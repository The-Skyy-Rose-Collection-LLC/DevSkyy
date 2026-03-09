#!/usr/bin/env python3
"""Upload SkyyRose LoRA Dataset v2 to HuggingFace Hub."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from huggingface_hub import HfApi, create_repo
except ImportError:
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub"], check=True)
    from huggingface_hub import HfApi, create_repo


def main():
    print("=== Uploading SkyyRose LoRA Dataset v2 to HuggingFace Hub ===\n")

    dataset_dir = project_root / "datasets" / "skyyrose_lora_v2"
    if not dataset_dir.exists():
        print(f"❌ Dataset not found: {dataset_dir}")
        return 1

    api = HfApi()
    repo_id = "damBruh/skyyrose-lora-dataset-v2"

    print(f"Creating repository: {repo_id}")
    try:
        create_repo(repo_id=repo_id, repo_type="dataset", exist_ok=True, private=False)
        print("✓ Repository ready\n")
    except Exception as e:
        print(f"⚠ {e}\n")

    print(f"Uploading 252 images from: {dataset_dir}")
    print("This will take a few minutes...\n")

    api.upload_folder(
        folder_path=str(dataset_dir),
        repo_id=repo_id,
        repo_type="dataset",
        commit_message="feat: SkyyRose LoRA v2 - 252 AI-enhanced images (3 collections)",
    )

    print(f"\n{'=' * 60}")
    print("✅ Dataset Uploaded!")
    print(f"{'=' * 60}")
    print(f"\nURL: https://huggingface.co/datasets/{repo_id}")
    return 0


if __name__ == "__main__":
    exit(main())
