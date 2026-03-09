#!/usr/bin/env python3
"""
Enhance product image colors for accurate 3D generation.
Boosts saturation, contrast, and vibrancy while preserving alpha channel.
"""

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance


def enhance_for_3d(
    input_path: str,
    output_path: str,
    saturation_boost: float = 1.8,
    contrast_boost: float = 1.3,
    brightness_boost: float = 1.1,
) -> dict:
    """Enhance product image colors for 3D extraction."""

    print(f"\n🎨 Enhancing: {Path(input_path).name}")

    # Load image with alpha
    img = Image.open(input_path).convert("RGBA")
    rgb = img.convert("RGB")
    alpha = img.split()[3]

    # Original stats
    orig_array = np.array(rgb)
    orig_mean = orig_array.mean(axis=(0, 1))

    # Enhance saturation
    enhancer = ImageEnhance.Color(rgb)
    rgb = enhancer.enhance(saturation_boost)

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(rgb)
    rgb = enhancer.enhance(contrast_boost)

    # Slight brightness boost
    enhancer = ImageEnhance.Brightness(rgb)
    rgb = enhancer.enhance(brightness_boost)

    # Recombine with alpha
    rgb = rgb.convert("RGB")
    enhanced = Image.merge("RGBA", (*rgb.split(), alpha))

    # Enhanced stats
    enh_array = np.array(rgb)
    enh_mean = enh_array.mean(axis=(0, 1))

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    enhanced.save(output_path, "PNG", optimize=True)

    print(f"   Original RGB: [{orig_mean[0]:.1f}, {orig_mean[1]:.1f}, {orig_mean[2]:.1f}]")
    print(f"   Enhanced RGB: [{enh_mean[0]:.1f}, {enh_mean[1]:.1f}, {enh_mean[2]:.1f}]")
    print(f"   Boost: +{((enh_mean - orig_mean).mean()):.1f} intensity")
    print(f"   ✓ Saved: {output_path.name}")

    return {
        "success": True,
        "input": str(input_path),
        "output": str(output_path),
        "original_mean_rgb": orig_mean.tolist(),
        "enhanced_mean_rgb": enh_mean.tolist(),
    }


def process_collection(collection: str, output_base: str = "assets/3d-ready-images") -> list:
    """Process all products in a collection."""

    collection_dir = Path(f"assets/enhanced-images/{collection}")
    output_dir = Path(output_base) / collection

    results = []

    for product_dir in sorted(collection_dir.iterdir()):
        if not product_dir.is_dir():
            continue

        # Find transparent PNG
        img_path = product_dir / f"{product_dir.name}_transparent.png"
        if not img_path.exists():
            continue

        # Output path
        output_path = output_dir / f"{product_dir.name}_3d_ready.png"

        result = enhance_for_3d(
            input_path=str(img_path),
            output_path=str(output_path),
            saturation_boost=1.8,  # 80% more color
            contrast_boost=1.3,  # 30% more contrast
            brightness_boost=1.1,  # 10% brighter
        )
        result["product_name"] = product_dir.name
        result["collection"] = collection
        results.append(result)

    return results


def main():
    """Enhance all collection images for 3D generation."""

    print("=" * 70)
    print("SKYYROSE COLOR ENHANCEMENT FOR 3D GENERATION")
    print("Boost saturation, contrast, vibrancy for EXACT color replication")
    print("=" * 70)

    collections = ["signature", "love-hurts", "black-rose"]
    all_results = []

    for collection in collections:
        print(f"\n📦 Processing {collection.upper()}...")
        results = process_collection(collection)
        all_results.extend(results)
        print(f"   ✓ {len(results)} images enhanced")

    # Save manifest
    manifest = {
        "total": len(all_results),
        "collections": {
            col: len([r for r in all_results if r["collection"] == col]) for col in collections
        },
        "enhancements": {
            "saturation": 1.8,
            "contrast": 1.3,
            "brightness": 1.1,
        },
        "results": all_results,
    }

    manifest_path = Path("assets/3d-ready-images/ENHANCEMENT_MANIFEST.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n{'=' * 70}")
    print("✅ COLOR ENHANCEMENT COMPLETE")
    print(f"{'=' * 70}")
    print(f"\n📊 Total: {len(all_results)} images")
    for col, count in manifest["collections"].items():
        print(f"   • {col}: {count}")
    print("\n📁 Output: assets/3d-ready-images/")
    print(f"💾 Manifest: {manifest_path}")
    print("\n🚀 Next: Run 3D generation with enhanced images")


if __name__ == "__main__":
    main()
