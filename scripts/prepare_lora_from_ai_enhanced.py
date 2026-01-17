#!/usr/bin/env python3
"""
Prepare LoRA Training Dataset from AI-Enhanced Images.

Converts AI_ENHANCEMENT_MANIFEST.json to diffusers-compatible format.

Usage:
    python3 scripts/prepare_lora_from_ai_enhanced.py
"""

import json
import shutil
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
MANIFEST_PATH = PROJECT_ROOT / "assets" / "ai-enhanced-images" / "AI_ENHANCEMENT_MANIFEST.json"
DATASET_DIR = PROJECT_ROOT / "datasets" / "skyyrose_lora_v2"

# SkyyRose Brand DNA
BRAND_DNA = {
    "trigger_word": "skyyrose",
    "collections": {
        "signature": {
            "trigger": "skyyrose signature collection",
            "theme": "understated luxury, confident elegance, everyday excellence",
            "mood": "confident, sophisticated, effortlessly premium, timeless",
            "colors": "rose, lavender, orchid, cotton candy pastels, premium whites",
            "keywords": ["luxury", "signature", "premium", "elegant", "timeless", "rose gold"],
        },
        "black-rose": {
            "trigger": "skyyrose black_rose collection",
            "theme": "gothic luxury, dark elegance, rebellious sophistication",
            "mood": "mysterious, powerful, unapologetically bold",
            "colors": "black, deep rose, charcoal, midnight tones",
            "keywords": ["gothic", "noir", "dark luxury", "rebellious", "dramatic", "black"],
        },
        "love-hurts": {
            "trigger": "skyyrose love_hurts collection",
            "theme": "emotional authenticity, vulnerable strength, artistic passion",
            "mood": "raw emotion, authentic, artistically refined, heartfelt",
            "colors": "deep rose, burgundy, warm earth tones, emotional reds",
            "keywords": ["emotional", "authentic", "passionate", "heartfelt", "artistic"],
        },
    },
}


def detect_garment_type(sku: str) -> dict:
    """Extract garment info from SKU."""
    sku_lower = sku.lower()

    garment_types = {
        "hoodie": ("Hoodie", ["hooded", "pullover", "warm", "cozy"]),
        "sherpa": ("Sherpa Jacket", ["fleece", "plush", "cozy", "warm", "textured"]),
        "shorts": ("Shorts", ["casual", "comfortable", "relaxed fit"]),
        "tee": ("T-Shirt", ["casual", "comfortable", "cotton"]),
        "t-shirt": ("T-Shirt", ["casual", "comfortable", "cotton"]),
        "shirt": ("Shirt", ["casual", "comfortable"]),
        "dress": ("Dress", ["elegant", "feminine", "stylish"]),
        "pants": ("Pants", ["comfortable", "casual"]),
        "jogger": ("Joggers", ["comfortable", "athletic", "relaxed"]),
        "sweater": ("Sweater", ["warm", "cozy", "knit"]),
        "jacket": ("Jacket", ["outerwear", "layering"]),
        "crop": ("Crop Top", ["trendy", "fitted", "stylish"]),
    }

    for key, (name, details) in garment_types.items():
        if key in sku_lower:
            return {"type": name, "details": details}

    return {"type": "Apparel", "details": ["premium", "stylish"]}


def generate_caption(sku: str, collection: str) -> str:
    """Generate detailed training caption."""
    collection_data = BRAND_DNA["collections"].get(
        collection, BRAND_DNA["collections"]["signature"]
    )
    garment = detect_garment_type(sku)

    # Build caption components
    parts = [
        collection_data["trigger"],  # skyyrose signature collection
        garment["type"],  # Hoodie
        sku.replace("_", " ").strip(),  # Clean product name
        collection_data["theme"],
        collection_data["mood"],
        ", ".join(garment["details"][:2]),
        "professional product photography",
        "studio lighting",
        "ultra detailed",
        "premium quality",
        "luxury streetwear",
        f"{collection_data['colors']}",
    ]

    return ", ".join(parts)


def main():
    """Prepare LoRA dataset from AI-enhanced images."""
    print("=" * 70)
    print("SkyyRose LoRA Dataset Preparation (v2 - AI Enhanced)")
    print("=" * 70)

    # Load manifest
    if not MANIFEST_PATH.exists():
        print(f"❌ Manifest not found: {MANIFEST_PATH}")
        return 1

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    print("\n📊 Manifest loaded:")
    print(f"   Pipeline: {manifest['pipeline']}")
    print(f"   Models: {', '.join(manifest['models_used'])}")

    # Create output directory
    images_dir = DATASET_DIR / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # Process each collection
    dataset_records = []
    stats = {"total": 0, "success": 0, "by_collection": {}}

    for collection_name, collection_data in manifest["collections"].items():
        print(f"\n🗂️  Processing {collection_name.upper()} collection...")
        stats["by_collection"][collection_name] = 0

        for item in collection_data["items"]:
            if not item["success"]:
                continue

            sku = item["sku"]

            # Get main image (highest quality for training)
            main_image = item["outputs"].get("main") or item["outputs"].get("retina")
            if not main_image:
                continue

            source_path = Path(main_image)
            if not source_path.exists():
                print(f"   ⚠ Missing: {source_path.name}")
                continue

            # Generate unique filename
            idx = len(dataset_records)
            ext = source_path.suffix
            dest_filename = f"{idx:04d}_{collection_name}_{sku[:30].replace(' ', '_')}{ext}"
            dest_path = images_dir / dest_filename

            # Copy image
            shutil.copy2(source_path, dest_path)

            # Generate caption
            caption = generate_caption(sku, collection_name)

            # Create record
            record = {
                "file_name": dest_filename,
                "text": caption,
            }
            dataset_records.append(record)
            stats["by_collection"][collection_name] += 1
            stats["success"] += 1

        print(f"   ✓ {stats['by_collection'][collection_name]} images prepared")

    stats["total"] = stats["success"]

    # Write metadata.jsonl (diffusers format)
    metadata_path = DATASET_DIR / "metadata.jsonl"
    with open(metadata_path, "w") as f:
        for record in dataset_records:
            f.write(json.dumps(record) + "\n")

    # Write dataset info
    dataset_info = {
        "name": "skyyrose-lora-dataset-v2",
        "description": "SkyyRose luxury streetwear product images for SDXL LoRA training",
        "version": "2.0.0",
        "trigger_word": BRAND_DNA["trigger_word"],
        "total_images": stats["total"],
        "collections": list(stats["by_collection"].keys()),
        "collection_counts": stats["by_collection"],
        "source": "AI-enhanced images (Gemini Nano + Real-ESRGAN)",
        "format": "diffusers-compatible",
    }

    info_path = DATASET_DIR / "dataset_info.json"
    with open(info_path, "w") as f:
        json.dump(dataset_info, f, indent=2)

    # Summary
    print(f"\n{'=' * 70}")
    print("✅ Dataset Preparation Complete!")
    print(f"{'=' * 70}")
    print(f"\n📁 Output: {DATASET_DIR}")
    print(f"📊 Total images: {stats['total']}")
    for col, count in stats["by_collection"].items():
        print(f"   • {col}: {count}")
    print("\n📝 Files created:")
    print(f"   • metadata.jsonl ({len(dataset_records)} records)")
    print("   • dataset_info.json")
    print(f"   • images/ ({stats['total']} files)")
    print("\n🚀 Next: python3 scripts/upload_lora_dataset_to_hf.py --version v2")

    return 0


if __name__ == "__main__":
    exit(main())
