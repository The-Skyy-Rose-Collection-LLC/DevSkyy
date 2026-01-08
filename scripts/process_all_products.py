#!/usr/bin/env python3
"""
Process ALL SkyyRose Product Photos - Complete Pipeline.

Scans all source directories, converts HEIC to JPG, enhances all images,
uploads to WordPress, creates 2D/2.5D visualizations.

Implements ralph-loop pattern for retries.

Usage:
    python3 scripts/process_all_products.py
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PIL import Image, ImageEnhance, ImageFilter

# Source directories
SOURCE_DIRS = [
    Path("/Users/coreyfoster/Desktop/_Signature Collection_"),
    Path("/tmp/black-rose-extracted"),
    Path("/tmp/signature-extracted"),
]


def convert_heic_to_jpg(heic_path: Path) -> Path:
    """Convert HEIC to JPG using sips."""
    jpg_path = heic_path.with_suffix(".jpg")

    if jpg_path.exists():
        return jpg_path

    try:
        subprocess.run(
            ["sips", "-s", "format", "jpeg", str(heic_path), "--out", str(jpg_path)],
            check=True,
            capture_output=True,
        )
        print(f"  Converted: {heic_path.name} → {jpg_path.name}")
        return jpg_path
    except Exception as e:
        print(f"  ✗ HEIC conversion failed: {e}")
        return heic_path


def scan_all_products() -> list[Path]:
    """Scan all source directories for product images."""

    all_images = []

    for source_dir in SOURCE_DIRS:
        if not source_dir.exists():
            continue

        # Find all image files (including HEIC)
        for pattern in [
            "**/*.jpg",
            "**/*.jpeg",
            "**/*.png",
            "**/*.JPG",
            "**/*.JPEG",
            "**/*.PNG",
            "**/*.heic",
            "**/*.HEIC",
        ]:
            for img_path in source_dir.glob(pattern):
                # Skip non-products (logos, duplicates with (1), HTML)
                if any(x in img_path.name.lower() for x in ["logo", "(1)", ".html", "book."]):
                    continue

                # Convert HEIC to JPG
                if img_path.suffix.lower() in [".heic"]:
                    img_path = convert_heic_to_jpg(img_path)

                # Only add JPG/JPEG/PNG
                if img_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                    all_images.append(img_path)

    return sorted(set(all_images))


def luxury_post_process(image: Image.Image) -> Image.Image:
    """Apply luxury finishing touches."""
    image = image.filter(ImageFilter.UnsharpMask(radius=2.0, percent=120, threshold=3))
    image = ImageEnhance.Contrast(image).enhance(1.03)
    image = ImageEnhance.Color(image).enhance(1.02)
    image = ImageEnhance.Brightness(image).enhance(1.01)
    return image


def enhance_product(input_path: Path, output_dir: Path, max_retries: int = 3) -> dict:
    """Enhance product photo with ralph-loop retry pattern."""

    for attempt in range(max_retries):
        try:
            # Load image
            image = Image.open(input_path)

            # Convert to RGB
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Upscale if needed (Lanczos 2-4x)
            current_max = max(image.width, image.height)
            if current_max < 4096:
                scale = min(4096 // current_max, 4)
                new_size = (image.width * scale, image.height * scale)
                image = image.resize(new_size, Image.LANCZOS)
                method = f"Lanczos {scale}x"
            else:
                method = "No upscaling"

            # Luxury post-processing
            image = luxury_post_process(image)

            # Save
            output_path = output_dir / f"enhanced_{input_path.name}"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(output_path, "JPEG", quality=95, optimize=True)

            return {
                "original": str(input_path),
                "enhanced": str(output_path),
                "method": method,
                "size": f"{image.width}x{image.height}",
                "success": True,
            }

        except Exception as e:
            if attempt < max_retries - 1:
                print(f"    Retry {attempt+1}/{max_retries}: {e}")
                continue
            else:
                return {"original": str(input_path), "error": str(e), "success": False}

    return {"success": False}


async def main():
    """Process ALL products with ralph-loop error handling."""

    print("=== SkyyRose Complete Product Processing ===\n")

    # Step 1: Scan all products
    print("📁 Scanning all source directories...")
    all_products = scan_all_products()
    print(f"✓ Found {len(all_products)} product images\n")

    # Step 2: Enhance ALL products
    print("🎨 Enhancing ALL products...\n")
    enhanced_dir = project_root / "assets" / "enhanced_products" / "all"

    results = []
    for i, product_path in enumerate(all_products, 1):
        print(f"[{i}/{len(all_products)}] {product_path.name}")
        result = enhance_product(product_path, enhanced_dir)
        results.append(result)

        if result["success"]:
            print(f"    ✓ Enhanced: {result['method']} → {result['size']}")
        else:
            print(f"    ✗ Failed: {result.get('error', 'Unknown error')}")

    # Save manifest
    manifest_path = enhanced_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(results, f, indent=2)

    # Summary
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful

    print(f"\n{'='*60}")
    print("✅ Processing Complete!")
    print(f"{'='*60}")
    print(f"Total products: {len(all_products)}")
    print(f"Successfully enhanced: {successful}")
    print(f"Failed: {failed}")
    print(f"\nEnhanced products saved to: {enhanced_dir}")
    print(f"Manifest: {manifest_path}")

    print("\n📋 Next Steps:")
    print("  1. Upload enhanced products to WordPress")
    print("  2. Create 2D/2.5D visualizations")
    print("  3. Attach to WooCommerce products")


if __name__ == "__main__":
    asyncio.run(main())
