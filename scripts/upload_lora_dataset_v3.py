#!/usr/bin/env python3
"""Upload SkyyRose LoRA Dataset v3 to HuggingFace Hub.

V3 contains 604 unique product images merged from all sources:
- V1 Dataset (82 images)
- V2 Dataset (249 images)
- Enhanced Products (107 images)
- 2D/2.5D Assets (166 images)
"""

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
    print("=" * 60)
    print("  UPLOADING SKYYROSE LORA DATASET V3 TO HUGGINGFACE HUB")
    print("=" * 60 + "\n")

    dataset_dir = project_root / "datasets" / "skyyrose_lora_v3"
    if not dataset_dir.exists():
        print(f"❌ Dataset not found: {dataset_dir}")
        print("Run: python scripts/merge_all_training_data.py first")
        return 1

    # Count images
    images_dir = dataset_dir / "images"
    image_count = len(list(images_dir.glob("*"))) if images_dir.exists() else 0
    print(f"📁 Dataset: {dataset_dir}")
    print(f"📷 Images: {image_count}")

    api = HfApi()
    repo_id = "damBruh/skyyrose-lora-dataset-v3"

    print(f"\n🔧 Creating repository: {repo_id}")
    try:
        create_repo(repo_id=repo_id, repo_type="dataset", exist_ok=True, private=False)
        print("✓ Repository ready\n")
    except Exception as e:
        print(f"⚠ {e}\n")

    print(f"📤 Uploading {image_count} images to HuggingFace...")
    print("This may take several minutes for 604 images...\n")

    # Upload entire folder at once (HuggingFace will handle chunking)
    api.upload_folder(
        folder_path=str(dataset_dir),
        repo_id=repo_id,
        repo_type="dataset",
        commit_message="feat: SkyyRose LoRA v3 - 604 product images (4 collections, full catalog)",
    )

    print(f"\n{'=' * 60}")
    print("✅ V3 DATASET UPLOADED SUCCESSFULLY!")
    print(f"{'=' * 60}")
    print(
        f"""
    URL: https://huggingface.co/datasets/{repo_id}

    Dataset Contents:
    - 604 unique product images
    - 4 collections (Signature, Love Hurts, Black Rose, SkyyRose)
    - metadata.jsonl with LoRA training captions
    - Brand trigger word: 'skyyrose'

    Next Steps:
    1. Train LoRA: python scripts/train_lora_from_products.py
    2. Test generation: python scripts/demo_image_generation.py
    """
    )
    return 0


if __name__ == "__main__":
    exit(main())
