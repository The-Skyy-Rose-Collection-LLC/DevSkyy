#!/usr/bin/env python3
"""
Upload SkyyRose LoRA Dataset to HuggingFace Hub.

Uploads the complete 95-image dataset with:
- All 3 collections (SIGNATURE, BLACK_ROSE, LOVE_HURTS)
- Brand logos
- Training metadata and config

Usage:
    python3 scripts/upload_lora_dataset_to_hf.py
"""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from huggingface_hub import HfApi, create_repo
except ImportError:
    print("Installing huggingface_hub...")
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub"], check=True)
    from huggingface_hub import HfApi, create_repo


def main():
    """Upload LoRA dataset to HuggingFace Hub."""

    print("=== Uploading SkyyRose LoRA Dataset to HuggingFace Hub ===\n")

    # Dataset directory
    dataset_dir = project_root / "datasets" / "skyyrose_lora_v1"

    if not dataset_dir.exists():
        print(f"❌ Dataset not found at: {dataset_dir}")
        return 1

    # Initialize HuggingFace API
    api = HfApi()

    # Dataset repository
    repo_id = "damBruh/skyyrose-lora-dataset-v1"

    print(f"Creating dataset repository: {repo_id}")

    try:
        create_repo(
            repo_id=repo_id,
            repo_type="dataset",
            exist_ok=True,
            private=False,  # Public dataset
        )
        print("✓ Repository created/verified\n")
    except Exception as e:
        print(f"⚠ Repository may already exist: {e}\n")

    # Upload dataset folder
    print(f"Uploading dataset from: {dataset_dir}")
    print("This may take a few minutes for 95 images...\n")

    api.upload_folder(
        folder_path=str(dataset_dir),
        repo_id=repo_id,
        repo_type="dataset",
        commit_message="feat: SkyyRose LoRA dataset v1 - 95 images (SIGNATURE, BLACK_ROSE, LOVE_HURTS + logos)",
    )

    print(f"\n{'='*60}")
    print("✅ Dataset Uploaded Successfully!")
    print(f"{'='*60}")
    print(f"\nDataset URL: https://huggingface.co/datasets/{repo_id}")
    print("\n📋 Next Steps:")
    print("  1. Visit lora-training-monitor Space")
    print("  2. Configure training with this dataset")
    print("  3. Start LoRA training")
    print("\nSpace URL: https://huggingface.co/spaces/damBruh/skyyrose-lora-training-monitor")

    return 0


if __name__ == "__main__":
    sys.exit(main())
