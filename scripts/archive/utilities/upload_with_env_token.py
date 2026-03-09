#!/usr/bin/env python3
"""Upload LoRA dataset using token from .env file."""

import os
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file
from dotenv import load_dotenv  # noqa: E402

load_dotenv(project_root / ".env")

# Get token
token = os.getenv("HF_TOKEN")
if not token:
    print("❌ HF_TOKEN not found in .env")
    sys.exit(1)

print("✓ Token loaded from .env")

# Set token for huggingface_hub
os.environ["HF_TOKEN"] = token

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

    # Initialize HuggingFace API with token
    api = HfApi(token=token)

    # Dataset repository
    repo_id = "damBruh/skyyrose-lora-dataset-v1"

    print(f"Creating dataset repository: {repo_id}")

    try:
        create_repo(
            repo_id=repo_id,
            repo_type="dataset",
            exist_ok=True,
            private=False,
            token=token,
        )
        print("✓ Repository created/verified\n")
    except Exception as e:
        print(f"⚠ Repository may already exist: {e}\n")

    # Upload dataset folder
    print(f"Uploading dataset from: {dataset_dir}")
    print("Uploading 95 images + metadata...\n")

    try:
        api.upload_folder(
            folder_path=str(dataset_dir),
            repo_id=repo_id,
            repo_type="dataset",
            commit_message="feat: SkyyRose LoRA dataset v1 - 95 images (SIGNATURE, BLACK_ROSE, LOVE_HURTS + logos)",
            token=token,
        )

        print(f"\n{'=' * 60}")
        print("✅ Dataset Uploaded Successfully!")
        print(f"{'=' * 60}")
        print(f"\nDataset URL: https://huggingface.co/datasets/{repo_id}")
        print("\n📋 Next Steps:")
        print("  1. Visit lora-training-monitor Space")
        print("  2. Configure training with this dataset")
        print("  3. Start LoRA training")
        print("\nSpace URL: https://huggingface.co/spaces/damBruh/skyyrose-lora-training-monitor")

        return 0

    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
