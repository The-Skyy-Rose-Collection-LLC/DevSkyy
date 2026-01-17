#!/usr/bin/env python3
"""
Dataset Preparation for ResNet Fine-Tuning

Interactive tool for labeling product images into groups.
Creates training dataset for fine-tuning ResNet on SkyyRose catalog.

Usage:
    python scripts/training/prepare_dataset.py \
        --image-dir /tmp/full_catalog_processing/webp_optimized/webp \
        --output-dir data/product_dataset

Workflow:
    1. Displays product images one by one
    2. User assigns each image to a product group
    3. Exports labeled dataset in PyTorch format

Output Structure:
    data/product_dataset/
    ├── labels.json          # Image → product_group mapping
    ├── train/               # 80% of images
    │   ├── group_001/
    │   │   ├── image_001.webp
    │   │   └── image_002.webp
    │   └── group_002/
    └── val/                 # 20% of images
        └── group_001/
            └── image_003.webp

Requirements:
    - Minimum 2 images per product group
    - Recommended 100+ product groups for good accuracy
    - Balanced distribution (similar #images per group)
"""

import argparse
import json
import shutil
from collections import defaultdict
from pathlib import Path

# Colors
GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
YELLOW = "\033[1;33m"
NC = "\033[0m"


def interactive_labeling(image_paths: list[Path]) -> dict[str, str]:
    """
    Interactive CLI for labeling product images.

    Args:
        image_paths: List of image file paths

    Returns:
        Dictionary mapping image_path → product_group_id
    """
    labels: dict[str, str] = {}
    product_groups: dict[str, list[Path]] = defaultdict(list)

    print(f"\n{BLUE}Interactive Product Labeling{NC}")
    print("=" * 70)
    print("\nInstructions:")
    print("  - Enter product group ID for each image (e.g., 'BR_SHERPA_001')")
    print("  - Same group ID = images of same product")
    print("  - Press 's' to skip image")
    print("  - Press 'q' to quit and save")
    print("=" * 70 + "\n")

    for i, image_path in enumerate(image_paths):
        print(f"\n[{i + 1}/{len(image_paths)}] Image: {image_path.name}")

        # Show existing groups
        if product_groups:
            print("\nExisting groups:")
            for group_id, group_images in list(product_groups.items())[:5]:
                print(f"  {group_id}: {len(group_images)} images")
            if len(product_groups) > 5:
                print(f"  ... and {len(product_groups) - 5} more groups")

        # Get user input
        while True:
            group_id = input(f"\n{YELLOW}Product group ID:{NC} ").strip()

            if group_id.lower() == "q":
                print(f"\n{YELLOW}Quitting and saving progress...{NC}")
                return labels
            elif group_id.lower() == "s":
                print(f"{YELLOW}Skipped{NC}")
                break
            elif group_id:
                labels[str(image_path)] = group_id
                product_groups[group_id].append(image_path)
                print(f"{GREEN}✓ Assigned to group: {group_id}{NC}")
                break
            else:
                print(f"{YELLOW}Please enter a group ID{NC}")

    return labels


def split_dataset(
    labels: dict[str, str],
    output_dir: Path,
    train_ratio: float = 0.8,
) -> None:
    """
    Split labeled dataset into train/val sets.

    Args:
        labels: Image path → product group mapping
        output_dir: Output directory for dataset
        train_ratio: Ratio of images for training (0-1)
    """
    # Group images by product group
    groups: dict[str, list[Path]] = defaultdict(list)
    for image_path_str, group_id in labels.items():
        groups[group_id].append(Path(image_path_str))

    # Create directories
    train_dir = output_dir / "train"
    val_dir = output_dir / "val"
    train_dir.mkdir(parents=True, exist_ok=True)
    val_dir.mkdir(parents=True, exist_ok=True)

    # Split and copy images
    train_count = 0
    val_count = 0

    for group_id, group_images in groups.items():
        # Create group directories
        train_group_dir = train_dir / group_id
        val_group_dir = val_dir / group_id
        train_group_dir.mkdir(exist_ok=True)
        val_group_dir.mkdir(exist_ok=True)

        # Split images
        split_idx = int(len(group_images) * train_ratio)
        train_images = group_images[:split_idx]
        val_images = group_images[split_idx:]

        # Copy train images
        for img in train_images:
            dest = train_group_dir / img.name
            shutil.copy2(img, dest)
            train_count += 1

        # Copy val images
        for img in val_images:
            dest = val_group_dir / img.name
            shutil.copy2(img, dest)
            val_count += 1

    print(f"\n{GREEN}✓ Dataset split complete:{NC}")
    print(f"  Train: {train_count} images ({len([g for g in groups if train_dir / g])} groups)")
    print(f"  Val: {val_count} images ({len([g for g in groups if val_dir / g])} groups)")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Prepare labeled dataset for ResNet training")
    parser.add_argument(
        "--image-dir",
        type=Path,
        required=True,
        help="Directory containing product images",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/product_dataset"),
        help="Output directory for labeled dataset",
    )
    parser.add_argument(
        "--labels-file",
        type=Path,
        default=None,
        help="Existing labels file to resume from",
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.8,
        help="Ratio of images for training (0-1)",
    )

    args = parser.parse_args()

    print(f"\n{BLUE}{'=' * 70}{NC}")
    print(f"{BLUE}ResNet Dataset Preparation{NC}")
    print(f"{BLUE}{'=' * 70}{NC}\n")

    # Collect images
    image_extensions = {".webp", ".jpg", ".jpeg", ".png"}
    image_paths = []
    for ext in image_extensions:
        image_paths.extend(args.image_dir.glob(f"**/*{ext}"))
    image_paths = sorted(image_paths)

    print(f"Image directory: {args.image_dir}")
    print(f"Found {len(image_paths)} images\n")

    # Load existing labels (if any)
    if args.labels_file and args.labels_file.exists():
        with open(args.labels_file) as f:
            labels = json.load(f)
        print(f"Loaded {len(labels)} existing labels from {args.labels_file}")
    else:
        labels = {}

    # Interactive labeling
    labels = interactive_labeling(image_paths)

    if not labels:
        print(f"\n{YELLOW}No labels created. Exiting.{NC}")
        return

    # Save labels
    args.output_dir.mkdir(parents=True, exist_ok=True)
    labels_file = args.output_dir / "labels.json"
    with open(labels_file, "w") as f:
        json.dump(labels, f, indent=2)
    print(f"\n{GREEN}✓ Saved labels: {labels_file}{NC}")

    # Split dataset
    print(f"\n{BLUE}Splitting dataset...{NC}")
    split_dataset(labels, args.output_dir, args.train_ratio)

    # Summary
    groups = set(labels.values())
    print(f"\n{BLUE}{'=' * 70}{NC}")
    print(f"{BLUE}Dataset Summary{NC}")
    print(f"{BLUE}{'=' * 70}{NC}")
    print(f"Total images labeled: {len(labels)}")
    print(f"Product groups: {len(groups)}")
    print(f"Output directory: {args.output_dir}")
    print(f"\n{GREEN}✓ Ready for training!{NC}")
    print("\nNext step: python scripts/training/train_resnet.py\n")


if __name__ == "__main__":
    main()
