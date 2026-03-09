#!/usr/bin/env python3
"""
Train SkyyRose LoRA via Replicate's SDXL trainer.

Uses the V3 dataset (604 images) from HuggingFace to create
a custom LoRA for exact product generation.

Usage:
    python3 scripts/train_lora_replicate.py
"""

import json
import os
import sys
import time
from pathlib import Path

import httpx

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load env manually (avoid dotenv parsing issues)
for env_file in [project_root / ".env", project_root / ".env.hf"]:
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    value = value.strip().strip('"').strip("'")
                    if value:
                        os.environ.setdefault(key.strip(), value)


def create_training_zip(max_size_mb: int = 90) -> str:
    """Create optimized zip file for Replicate (under 100MB limit).

    Replicate expects a zip with images and optional .txt caption files.
    Images are resized to 512x512 and compressed as JPEG.
    """
    import shutil
    import zipfile

    from PIL import Image

    dataset_dir = project_root / "datasets" / "skyyrose_lora_v3"
    images_dir = dataset_dir / "images"
    metadata_path = dataset_dir / "metadata.jsonl"

    if not images_dir.exists():
        raise FileNotFoundError(f"Dataset not found: {images_dir}")

    # Load metadata for captions
    captions = {}
    if metadata_path.exists():
        with open(metadata_path) as f:
            for line in f:
                entry = json.loads(line.strip())
                captions[entry["file_name"]] = entry["text"]

    # Create temp directory with optimized images + caption files
    temp_dir = project_root / "temp_training_data"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()

    image_count = 0
    target_size = 512  # Replicate trainer default resolution
    jpeg_quality = 85  # Good balance of quality/size

    for img_path in sorted(images_dir.glob("*")):
        if img_path.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
            try:
                # Open, resize, and save as optimized JPEG
                img = Image.open(img_path).convert("RGB")

                # Resize to 512x512 (or aspect-preserving if needed)
                img.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)

                # Pad to square if needed
                if img.size != (target_size, target_size):
                    new_img = Image.new("RGB", (target_size, target_size), (255, 255, 255))
                    offset = ((target_size - img.size[0]) // 2, (target_size - img.size[1]) // 2)
                    new_img.paste(img, offset)
                    img = new_img

                # Save as optimized JPEG
                output_name = f"{img_path.stem}.jpg"
                img.save(temp_dir / output_name, "JPEG", quality=jpeg_quality, optimize=True)

                # Create caption file
                caption = captions.get(img_path.name, "skyyrose luxury streetwear product")
                caption_path = temp_dir / f"{img_path.stem}.txt"
                with open(caption_path, "w") as f:
                    f.write(caption)

                image_count += 1
            except Exception as e:
                print(f"   Warning: Skipped {img_path.name}: {e}")

    print(f"   Prepared {image_count} optimized images (512x512 JPEG)")

    # Create zip
    zip_path = project_root / "skyyrose_training_data.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in temp_dir.iterdir():
            zf.write(file, file.name)

    # Cleanup
    shutil.rmtree(temp_dir)

    size_mb = zip_path.stat().st_size / 1024 / 1024
    print(f"   Created {zip_path} ({size_mb:.1f} MB)")

    if size_mb > max_size_mb:
        print(f"   WARNING: Zip is {size_mb:.1f}MB, exceeds {max_size_mb}MB limit")
        print("   Reducing quality or image count may be needed")

    return str(zip_path)


def upload_to_huggingface(zip_path: str) -> str:
    """Upload training zip to HuggingFace Hub and return download URL."""
    from huggingface_hub import HfApi

    hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_ACCESS_TOKEN")
    if not hf_token:
        raise ValueError("HF_TOKEN not found in environment")

    api = HfApi(token=hf_token)
    repo_id = "damBruh/skyyrose-lora-dataset-v3"
    filename = Path(zip_path).name

    print(f"   Uploading to HuggingFace Hub: {repo_id}...")

    # Upload the zip file to the existing dataset repo
    api.upload_file(
        path_or_fileobj=zip_path,
        path_in_repo=f"training/{filename}",
        repo_id=repo_id,
        repo_type="dataset",
    )

    # Get the direct download URL
    download_url = f"https://huggingface.co/datasets/{repo_id}/resolve/main/training/{filename}"
    print(f"   Uploaded: {download_url}")
    return download_url


def main():
    print("=" * 70)
    print("  SKYYROSE LORA TRAINING VIA REPLICATE")
    print("  Training on 604 exact product images")
    print("=" * 70 + "\n")

    # Verify API token
    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        print("ERROR: REPLICATE_API_TOKEN not found in environment")
        return 1

    print("Preparing training data...")
    zip_path = create_training_zip()

    print("\nUploading to HuggingFace Hub...")
    data_url = upload_to_huggingface(zip_path)

    print("\nStarting Flux LoRA training...")
    print("   Model: ostris/flux-dev-lora-trainer")
    print("   Trigger: skyyrose")
    print("   Steps: 1000")
    print("   Learning Rate: 4e-4")
    print()

    # Use Flux Dev LoRA trainer via direct HTTP API (no SDK required)
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    training_input = {
        "input_images": data_url,
        "trigger_word": "skyyrose",
        "steps": 1000,
        "lora_rank": 16,
        "optimizer": "adamw8bit",
        "batch_size": 1,
        "resolution": "512,768,1024",
        "autocaption": False,
        "autocaption_prefix": "skyyrose",
        "lr_scheduler": "constant",
        "learning_rate": 0.0004,
    }

    # Create training via HTTP API - use correct model/version endpoint
    # Format: POST /v1/models/{owner}/{model}/versions/{version_id}/trainings
    trainer_owner = "ostris"
    trainer_model = "flux-dev-lora-trainer"
    trainer_version = "26dce37af90b9d997eeb970d92e47de3064d46c300504ae376c75bef6a9022d2"  # pragma: allowlist secret

    response = httpx.post(
        f"https://api.replicate.com/v1/models/{trainer_owner}/{trainer_model}/versions/{trainer_version}/trainings",
        headers=headers,
        json={
            "destination": "dambruh/skyyrose-lora-v3",
            "input": training_input,
        },
        timeout=60.0,
    )

    if response.status_code not in (200, 201):
        print(f"ERROR: Failed to start training: {response.text}")
        return 1

    training = response.json()
    training_id = training.get("id")
    training_url = training.get("urls", {}).get("get", "")

    print(f"Training started: {training_id}")
    print(f"Status URL: https://replicate.com/p/{training_id}")
    print()

    # Monitor progress
    print("Monitoring progress (Ctrl+C to continue in background)...")
    print("-" * 70)

    try:
        status = training.get("status", "starting")
        while status in ("starting", "processing"):
            time.sleep(30)

            # Fetch latest status
            status_response = httpx.get(
                training_url or f"https://api.replicate.com/v1/trainings/{training_id}",
                headers=headers,
                timeout=30.0,
            )
            if status_response.status_code == 200:
                training = status_response.json()
                status = training.get("status", "unknown")
                logs = training.get("logs", "") or ""

                # Extract last few lines of logs
                log_lines = logs.strip().split("\n")[-5:]
                for line in log_lines:
                    if line.strip():
                        print(f"  {line}")

            if status == "succeeded":
                break
            elif status == "failed":
                print(f"\nERROR: Training failed - {training.get('error')}")
                return 1

        if status == "succeeded":
            output = training.get("output")
            print("\n" + "=" * 70)
            print("SUCCESS! LoRA training complete")
            print("=" * 70)
            print(f"""
Model: https://replicate.com/dambruh/skyyrose-lora-v3
Weights: {output}

Next Steps:
1. Test generation: python scripts/demo_image_generation.py
2. Use prompt: "skyyrose luxury streetwear, [product description]"
3. Deploy to production image pipeline
""")

            # Save training info
            info_path = project_root / "models" / "skyyrose-lora-v3-info.json"
            info_path.parent.mkdir(exist_ok=True)
            with open(info_path, "w") as f:
                json.dump(
                    {
                        "training_id": training_id,
                        "status": status,
                        "output": output,
                        "model_url": "https://replicate.com/dambruh/skyyrose-lora-v3",
                        "trigger_word": "skyyrose",
                        "dataset": "damBruh/skyyrose-lora-dataset-v3",
                        "images": 604,
                    },
                    f,
                    indent=2,
                )

            print(f"Training info saved: {info_path}")

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped. Training continues in background.")
        print(f"Check status: https://replicate.com/p/{training_id}")

    return 0


if __name__ == "__main__":
    exit(main())
