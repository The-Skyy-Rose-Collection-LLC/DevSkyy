#!/usr/bin/env python3
"""
Merge All Training Data for SkyyRose LoRA V3
=============================================

Combines all product images from:
- V1 Dataset (95 images)
- V2 Dataset (252 images)
- Enhanced Products (203 images)
- 2D/2.5D Assets (primary images only)

Creates proper LoRA training captions with:
- Collection name
- Product type
- Brand DNA (skyyrose trigger word)
- Style descriptors

Usage:
    python scripts/merge_all_training_data.py
"""

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
V1_DATASET = PROJECT_ROOT / "datasets" / "skyyrose_lora_v1"
V2_DATASET = PROJECT_ROOT / "datasets" / "skyyrose_lora_v2"
ENHANCED_PRODUCTS = PROJECT_ROOT / "assets" / "enhanced_products" / "all"
ASSETS_2D_25D = PROJECT_ROOT / "assets" / "2d-25d-assets"
PRODUCT_INVENTORY = PROJECT_ROOT / "datasets" / "product_inventory.json"
OUTPUT_DIR = PROJECT_ROOT / "datasets" / "skyyrose_lora_v3"

# Brand DNA for captions
BRAND_TRIGGER = "skyyrose"
BRAND_STYLE = "luxury urban fashion, Oakland streetwear, bold design, premium quality"

# Collection mapping (clean names)
COLLECTION_MAP = {
    "_signature collection_": "signature_collection",
    "_the signature collection_": "signature_collection",
    "signature collection": "signature_collection",
    "signature": "signature_collection",
    "black rose": "black_rose",
    "black_rose": "black_rose",
    "love hurts": "love_hurts",
    "love_hurts": "love_hurts",
    "heartbreak season": "heartbreak_season",
    "heartbreak_season": "heartbreak_season",
}


def get_collection_from_path(path: str) -> str:
    """Extract collection name from file path."""
    path_lower = path.lower()

    for key, value in COLLECTION_MAP.items():
        if key in path_lower:
            return value

    # Try to extract from directory structure
    parts = Path(path).parts
    for part in parts:
        part_lower = part.lower()
        for key, value in COLLECTION_MAP.items():
            if key in part_lower:
                return value

    return "skyyrose"  # Default collection


def get_product_type(filename: str) -> str:
    """Extract product type from filename."""
    filename_lower = filename.lower()

    product_types = {
        "hoodie": "hoodie",
        "tee": "t-shirt",
        "shirt": "shirt",
        "shorts": "shorts",
        "jacket": "jacket",
        "sherpa": "sherpa jacket",
        "beanie": "beanie",
        "windbreaker": "windbreaker",
        "crop": "crop top",
        "dress": "dress",
        "pants": "pants",
        "jogger": "joggers",
        "sweater": "sweater",
        "cardigan": "cardigan",
    }

    for key, value in product_types.items():
        if key in filename_lower:
            return value

    return "apparel"


def create_caption(filepath: str, filename: str) -> str:
    """Create LoRA training caption for an image."""
    collection = get_collection_from_path(filepath)
    product_type = get_product_type(filename)

    # Clean collection name for caption
    collection_display = collection.replace("_", " ").title()

    caption = (
        f"{BRAND_TRIGGER} {collection_display}, {product_type}, "
        f"{BRAND_STYLE}, professional product photography, "
        f"high quality, detailed texture"
    )

    return caption


def file_hash(filepath: Path) -> str:
    """Get MD5 hash of file for deduplication."""
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def is_primary_image(filename: str) -> bool:
    """Check if this is a primary image (not depth, shadow, etc.)."""
    skip_patterns = [
        "_depth",
        "_shadow",
        "_parallax",
        "_mask",
        "_normal",
        "_ao",
        "_specular",
    ]
    filename_lower = filename.lower()
    return not any(pattern in filename_lower for pattern in skip_patterns)


def gather_images():
    """Gather all images from all sources."""
    images = []
    seen_hashes = set()

    print("\n" + "=" * 60)
    print("GATHERING IMAGES FROM ALL SOURCES")
    print("=" * 60)

    # 1. V1 Dataset - root images
    v1_root_images = list(V1_DATASET.glob("*.jpg")) + list(V1_DATASET.glob("*.png"))
    print(f"\n📁 V1 Dataset (root): {len(v1_root_images)} images")
    for img in v1_root_images:
        if img.is_file():
            h = file_hash(img)
            if h not in seen_hashes:
                seen_hashes.add(h)
                images.append({"path": img, "source": "v1_root"})

    # V1 Dataset - images subdirectory
    v1_images_dir = V1_DATASET / "images"
    if v1_images_dir.exists():
        v1_subdir_images = list(v1_images_dir.glob("*.jpg")) + list(v1_images_dir.glob("*.png"))
        print(f"📁 V1 Dataset (images/): {len(v1_subdir_images)} images")
        for img in v1_subdir_images:
            if img.is_file():
                h = file_hash(img)
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    images.append({"path": img, "source": "v1_images"})

    # 2. V2 Dataset
    v2_images_dir = V2_DATASET / "images"
    if v2_images_dir.exists():
        v2_images = list(v2_images_dir.glob("*.jpg")) + list(v2_images_dir.glob("*.png"))
        print(f"\n📁 V2 Dataset: {len(v2_images)} images")
        for img in v2_images:
            if img.is_file():
                h = file_hash(img)
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    images.append({"path": img, "source": "v2"})

    # 3. Enhanced Products
    if ENHANCED_PRODUCTS.exists():
        enhanced_images = list(ENHANCED_PRODUCTS.glob("*.jpg")) + list(
            ENHANCED_PRODUCTS.glob("*.png")
        )
        print(f"\n📁 Enhanced Products: {len(enhanced_images)} images")
        for img in enhanced_images:
            if img.is_file():
                h = file_hash(img)
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    images.append({"path": img, "source": "enhanced"})

    # 4. 2D/2.5D Assets (primary images only)
    if ASSETS_2D_25D.exists():
        all_2d_images = list(ASSETS_2D_25D.glob("*.jpg")) + list(ASSETS_2D_25D.glob("*.png"))
        primary_2d_images = [img for img in all_2d_images if is_primary_image(img.name)]
        print(
            f"\n📁 2D/2.5D Assets (primary only): {len(primary_2d_images)}/{len(all_2d_images)} images"
        )
        for img in primary_2d_images:
            if img.is_file():
                h = file_hash(img)
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    images.append({"path": img, "source": "2d_25d"})

    print(f"\n✅ Total unique images: {len(images)}")
    return images


def create_v3_dataset(images: list):
    """Create the V3 dataset with images and metadata."""
    print("\n" + "=" * 60)
    print("CREATING V3 DATASET")
    print("=" * 60)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    images_dir = OUTPUT_DIR / "images"
    images_dir.mkdir(exist_ok=True)

    metadata = []

    for i, img_data in enumerate(images):
        src_path = img_data["path"]
        source = img_data["source"]

        # New filename with index
        ext = src_path.suffix.lower()
        new_filename = f"skyyrose_{i:04d}{ext}"
        dst_path = images_dir / new_filename

        # Copy image
        shutil.copy2(src_path, dst_path)

        # Create caption
        caption = create_caption(str(src_path), src_path.stem)

        # Add to metadata
        metadata.append(
            {
                "file_name": f"images/{new_filename}",
                "text": caption,
                "source": source,
                "original_name": src_path.name,
                "collection": get_collection_from_path(str(src_path)),
                "product_type": get_product_type(src_path.stem),
            }
        )

        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(images)} images...")

    # Write metadata.jsonl (HuggingFace format)
    metadata_path = OUTPUT_DIR / "metadata.jsonl"
    with open(metadata_path, "w") as f:
        for item in metadata:
            f.write(json.dumps(item) + "\n")

    # Write dataset info
    dataset_info = {
        "name": "skyyrose-lora-v3",
        "version": "3.0.0",
        "description": "SkyyRose luxury fashion product images for LoRA training",
        "created": datetime.now().isoformat(),
        "total_images": len(images),
        "sources": {
            "v1_root": sum(1 for m in metadata if m["source"] == "v1_root"),
            "v1_images": sum(1 for m in metadata if m["source"] == "v1_images"),
            "v2": sum(1 for m in metadata if m["source"] == "v2"),
            "enhanced": sum(1 for m in metadata if m["source"] == "enhanced"),
            "2d_25d": sum(1 for m in metadata if m["source"] == "2d_25d"),
        },
        "collections": list({m["collection"] for m in metadata}),
        "product_types": list({m["product_type"] for m in metadata}),
        "brand_trigger": BRAND_TRIGGER,
    }

    info_path = OUTPUT_DIR / "dataset_info.json"
    with open(info_path, "w") as f:
        json.dump(dataset_info, f, indent=2)

    print(f"\n✅ V3 Dataset created at: {OUTPUT_DIR}")
    print(f"   Total images: {len(images)}")
    print(f"   Metadata: {metadata_path}")
    print(f"   Info: {info_path}")

    return dataset_info


def print_summary(info: dict):
    """Print dataset summary."""
    print("\n" + "=" * 60)
    print("V3 DATASET SUMMARY")
    print("=" * 60)
    print(f"""
    Name: {info["name"]}
    Version: {info["version"]}
    Total Images: {info["total_images"]}

    Sources:
    ├── V1 Root: {info["sources"]["v1_root"]}
    ├── V1 Images: {info["sources"]["v1_images"]}
    ├── V2: {info["sources"]["v2"]}
    ├── Enhanced: {info["sources"]["enhanced"]}
    └── 2D/2.5D: {info["sources"]["2d_25d"]}

    Collections: {", ".join(info["collections"])}
    Product Types: {", ".join(info["product_types"])}
    Brand Trigger: {info["brand_trigger"]}
    """)


def main():
    """Main entry point."""
    print("\n" + "🌹" * 30)
    print("  SKYYROSE LORA V3 DATASET BUILDER")
    print("🌹" * 30)

    # Gather images from all sources
    images = gather_images()

    if not images:
        print("\n❌ No images found!")
        return

    # Create V3 dataset
    info = create_v3_dataset(images)

    # Print summary
    print_summary(info)

    print("\n🚀 NEXT STEPS:")
    print("   1. Upload to HuggingFace: python scripts/upload_lora_dataset_v2.py --version v3")
    print("   2. Start training: python scripts/train_lora_from_products.py")
    print("   3. Validate model: python scripts/demo_image_generation.py")


if __name__ == "__main__":
    main()
