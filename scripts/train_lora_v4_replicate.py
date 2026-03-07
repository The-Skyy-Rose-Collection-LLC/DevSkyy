#!/usr/bin/env python3
"""
Train SkyyRose LoRA v4 via Replicate's Flux Dev LoRA Trainer.

Key differences from v3:
  - Per-SKU trigger words (skyyrose_br001, skyyrose_lh002, etc.)
  - Tech flat images as ground truth training data
  - Detailed per-image captions describing exact graphics, colors, placement
  - Higher resolution (1024) and quality (95% JPEG)

Usage:
    source .venv-lora/bin/activate
    python scripts/train_lora_v4_replicate.py

    # Dry run (build zip only, don't train):
    python scripts/train_lora_v4_replicate.py --dry-run

    # Monitor existing training:
    python scripts/train_lora_v4_replicate.py --monitor <training_id>
"""

import argparse
import json
import os
import sys
import time
import zipfile
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).parent.parent
DATASET_DIR = PROJECT_ROOT / "datasets" / "skyyrose_lora_v4"

# Load env
for env_file in [PROJECT_ROOT / ".env", PROJECT_ROOT / ".env.hf"]:
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    value = value.strip().strip('"').strip("'")
                    if value:
                        os.environ.setdefault(key.strip(), value)


def create_training_zip() -> Path:
    """Create training zip with images + caption .txt files.

    Replicate's Flux trainer expects:
      image1.jpg + image1.txt (caption)
      image2.jpg + image2.txt (caption)
    """
    images_dir = DATASET_DIR / "images"
    captions_dir = DATASET_DIR / "captions"

    if not images_dir.exists():
        print("ERROR: Dataset not built. Run: python scripts/build_lora_v4_dataset.py")
        sys.exit(1)

    zip_path = PROJECT_ROOT / "skyyrose_v4_training.zip"

    image_count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for img_path in sorted(images_dir.glob("*.jpg")):
            # Add image
            zf.write(img_path, img_path.name)

            # Add matching caption
            caption_path = captions_dir / f"{img_path.stem}.txt"
            if caption_path.exists():
                zf.write(caption_path, caption_path.name)
            else:
                # Fallback caption
                fallback = "skyyrose luxury streetwear product by SkyyRose"
                zf.writestr(f"{img_path.stem}.txt", fallback)

            image_count += 1

    size_mb = zip_path.stat().st_size / 1024 / 1024
    print(f"  Created training zip: {zip_path.name} ({size_mb:.1f} MB, {image_count} images)")

    if size_mb > 95:
        print("  WARNING: Zip exceeds 95MB — may hit Replicate's 100MB limit")

    return zip_path


def upload_to_huggingface(zip_path: Path) -> str:
    """Upload training zip to HuggingFace and return download URL."""
    from huggingface_hub import HfApi

    hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_ACCESS_TOKEN")
    if not hf_token:
        # Try reading from HF cache
        hf_token_path = Path.home() / ".cache" / "huggingface" / "token"
        if hf_token_path.exists():
            hf_token = hf_token_path.read_text().strip()

    if not hf_token:
        print("ERROR: HF_TOKEN not found. Set in .env.hf or run `huggingface-cli login`")
        sys.exit(1)

    api = HfApi(token=hf_token)
    repo_id = "damBruh/skyyrose-lora-dataset-v4"

    # Create repo if needed
    try:
        api.create_repo(repo_id, repo_type="dataset", private=True, exist_ok=True)
    except Exception as e:
        print(f"  Note: {e}")

    print(f"  Uploading to HuggingFace: {repo_id}...")
    api.upload_file(
        path_or_fileobj=str(zip_path),
        path_in_repo="training/skyyrose_v4_training.zip",
        repo_id=repo_id,
        repo_type="dataset",
    )

    download_url = (
        f"https://huggingface.co/datasets/{repo_id}/resolve/main/training/skyyrose_v4_training.zip"
    )
    print(f"  Uploaded: {download_url}")
    return download_url


def start_training(data_url: str) -> dict:
    """Submit Flux LoRA training job to Replicate."""
    api_token = os.environ.get("REPLICATE_API_TOKEN")
    if not api_token:
        print("ERROR: REPLICATE_API_TOKEN not found in environment")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    # Flux Dev LoRA trainer config — optimized for product accuracy
    training_input = {
        "input_images": data_url,
        "trigger_word": "skyyrose",  # Global trigger; per-SKU triggers are in captions
        "steps": 1500,  # More steps for per-product learning (v3 used 1000)
        "lora_rank": 32,  # Higher rank for more detail capacity (v3 used 16)
        "optimizer": "adamw8bit",
        "batch_size": 1,
        "resolution": "512,768,1024",
        "autocaption": False,  # We provide our own per-SKU captions
        "autocaption_prefix": "",
        "lr_scheduler": "constant",
        "learning_rate": 0.0004,
    }

    # Use latest Flux Dev LoRA trainer
    trainer_owner = "ostris"
    trainer_model = "flux-dev-lora-trainer"

    # First, get the latest version
    print("  Fetching latest trainer version...")
    version_resp = httpx.get(
        f"https://api.replicate.com/v1/models/{trainer_owner}/{trainer_model}/versions",
        headers=headers,
        timeout=30.0,
    )

    if version_resp.status_code == 200:
        versions = version_resp.json().get("results", [])
        if versions:
            trainer_version = versions[0]["id"]
            print(f"  Using trainer version: {trainer_version[:16]}...")
        else:
            # Fallback to known working version from v3
            trainer_version = "26dce37af90b9d997eeb970d92e47de3064d46c300504ae376c75bef6a9022d2"
            print("  Using fallback trainer version")
    else:
        trainer_version = "26dce37af90b9d997eeb970d92e47de3064d46c300504ae376c75bef6a9022d2"
        print("  Using fallback trainer version")

    print("\n  Training configuration:")
    print(f"    Model:         {trainer_owner}/{trainer_model}")
    print("    Destination:   devskyy/skyyrose-lora-v4")
    print(f"    Steps:         {training_input['steps']}")
    print(f"    LoRA Rank:     {training_input['lora_rank']}")
    print(f"    Resolution:    {training_input['resolution']}")
    print(f"    Learning Rate: {training_input['learning_rate']}")
    print(f"    Autocaption:   {training_input['autocaption']}")
    print()

    response = httpx.post(
        f"https://api.replicate.com/v1/models/{trainer_owner}/{trainer_model}/versions/{trainer_version}/trainings",
        headers=headers,
        json={
            "destination": "devskyy/skyyrose-lora-v4",
            "input": training_input,
        },
        timeout=60.0,
    )

    if response.status_code not in (200, 201):
        print(f"ERROR: Failed to start training: {response.status_code}")
        print(f"  {response.text[:500]}")
        sys.exit(1)

    training = response.json()
    return training


def monitor_training(training_id: str, api_token: str | None = None):
    """Monitor a running training job."""
    if not api_token:
        api_token = os.environ.get("REPLICATE_API_TOKEN")
    if not api_token:
        print("ERROR: REPLICATE_API_TOKEN not found")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {api_token}"}
    url = f"https://api.replicate.com/v1/trainings/{training_id}"

    print(f"Monitoring training: {training_id}")
    print(f"Dashboard: https://replicate.com/p/{training_id}")
    print("-" * 70)

    last_log_len = 0
    try:
        while True:
            resp = httpx.get(url, headers=headers, timeout=30.0)
            if resp.status_code != 200:
                print(f"  Status check failed: {resp.status_code}")
                time.sleep(30)
                continue

            data = resp.json()
            status = data.get("status", "unknown")
            logs = data.get("logs", "") or ""

            # Print new log lines
            if len(logs) > last_log_len:
                new_lines = logs[last_log_len:].strip().split("\n")
                for line in new_lines:
                    if line.strip():
                        print(f"  {line}")
                last_log_len = len(logs)

            if status == "succeeded":
                return data
            elif status == "failed":
                print(f"\nFAILED: {data.get('error', 'Unknown error')}")
                return data
            elif status == "canceled":
                print("\nTraining was canceled.")
                return data

            time.sleep(30)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped. Training continues in background.")
        print(f"Resume: python scripts/train_lora_v4_replicate.py --monitor {training_id}")
        return None


def save_training_info(training: dict):
    """Save training result to models/ directory."""
    models_dir = PROJECT_ROOT / "models"
    models_dir.mkdir(exist_ok=True)

    info = {
        "model": "devskyy/skyyrose-lora-v4",
        "version": training.get("output", {}).get("version", ""),
        "training_id": training.get("id", ""),
        "status": training.get("status", ""),
        "weights_url": training.get("output", ""),
        "trigger_word": "skyyrose",
        "per_sku_triggers": True,
        "training_config": {
            "base_model": "ostris/flux-dev-lora-trainer",
            "steps": 1500,
            "lora_rank": 32,
            "optimizer": "adamw8bit",
            "batch_size": 1,
            "resolution": "512,768,1024",
            "learning_rate": 0.0004,
            "autocaption": False,
        },
        "dataset": {
            "source": "damBruh/skyyrose-lora-dataset-v4",
            "images": 73,
            "tech_flats": 24,
            "model_shots": 49,
            "unique_triggers": 23,
            "strategy": "per-SKU trigger words with detailed captions from tech flats",
        },
        "improvements_over_v3": [
            "Per-SKU trigger words instead of single 'skyyrose' trigger",
            "Tech flat images as ground truth training data",
            "Detailed per-image captions (not auto-captioned)",
            "Higher LoRA rank (32 vs 16) for more detail capacity",
            "More training steps (1500 vs 1000)",
            "Curated dataset (73 high-quality vs 390 noisy images)",
        ],
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    info_path = models_dir / "skyyrose-lora-v4-info.json"
    with open(info_path, "w") as f:
        json.dump(info, f, indent=2)
    print(f"  Training info saved: {info_path}")


def main():
    parser = argparse.ArgumentParser(description="Train SkyyRose LoRA v4 on Replicate")
    parser.add_argument("--dry-run", action="store_true", help="Build zip only, don't train")
    parser.add_argument("--monitor", type=str, help="Monitor existing training by ID")
    parser.add_argument(
        "--skip-upload", action="store_true", help="Skip HF upload, use existing URL"
    )
    args = parser.parse_args()

    print("=" * 70)
    print("  SKYYROSE LORA V4 TRAINING")
    print("  Per-SKU triggers | Tech flat ground truth | 73 curated images")
    print("=" * 70)

    # Monitor mode
    if args.monitor:
        result = monitor_training(args.monitor)
        if result and result.get("status") == "succeeded":
            save_training_info(result)
        return 0

    # Step 1: Build training zip
    print("\n[1/4] Building training zip...")
    zip_path = create_training_zip()

    if args.dry_run:
        print(f"\nDry run complete. Zip at: {zip_path}")
        print("Remove --dry-run to upload and train.")
        return 0

    # Step 2: Upload to HuggingFace
    print("\n[2/4] Uploading to HuggingFace Hub...")
    data_url = upload_to_huggingface(zip_path)

    # Step 3: Start training
    print("\n[3/4] Starting Flux LoRA training on Replicate...")
    training = start_training(data_url)

    training_id = training.get("id", "")
    print(f"\n  Training started: {training_id}")
    print(f"  Dashboard: https://replicate.com/p/{training_id}")

    # Step 4: Monitor
    print("\n[4/4] Monitoring progress (Ctrl+C to run in background)...")
    result = monitor_training(training_id)

    if result and result.get("status") == "succeeded":
        save_training_info(result)
        output = result.get("output", "")
        print("\n" + "=" * 70)
        print("  SUCCESS! LoRA v4 training complete")
        print("=" * 70)
        print(f"""
  Model:   https://replicate.com/devskyy/skyyrose-lora-v4
  Weights: {output}

  Usage examples:
    # Generate specific product:
    "skyyrose_br001 black crewneck on a fashion model, studio lighting"
    "skyyrose_brd02 red football jersey #80, urban photoshoot"
    "skyyrose_lh002 varsity jacket, model walking in rose garden"

  Next: python scripts/test_lora_v4.py
""")

    # Cleanup zip
    if zip_path.exists():
        zip_path.unlink()
        print(f"  Cleaned up: {zip_path.name}")

    return 0


if __name__ == "__main__":
    exit(main())
