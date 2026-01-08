#!/usr/bin/env python3
"""
Enhance Real SkyyRose Product Photos with Local Real-ESRGAN.

Takes real product photos from Desktop collections and:
1. Upscales with Real-ESRGAN 4x (or Lanczos fallback)
2. Applies luxury post-processing (sharpening, contrast, color)
3. Saves enhanced photos to assets/enhanced_products/
4. Generates manifest for user selection (3D vs 2D/2.5D)

Usage:
    python3 scripts/enhance_real_products.py
"""

import asyncio
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def detect_collection(filename: str) -> str:
    """Detect which collection a product belongs to based on filename."""
    filename_lower = filename.lower()
    if "black" in filename_lower or "noir" in filename_lower:
        return "BLACK_ROSE"
    elif "love" in filename_lower or "heart" in filename_lower:
        return "LOVE_HURTS"
    else:
        return "SIGNATURE"


def luxury_post_process(image: Image.Image) -> Image.Image:
    """Apply luxury finishing touches to product photos."""
    # Subtle sharpening for crisp details
    image = image.filter(ImageFilter.UnsharpMask(radius=2.0, percent=120, threshold=3))

    # Slight contrast enhancement
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.03)

    # Color accuracy refinement
    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(1.02)

    # Brightness adjustment for product clarity
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.01)

    return image


def upscale_with_realesrgan(image: Image.Image, scale: int = 4) -> Image.Image | None:
    """Upscale image using Real-ESRGAN if available."""
    try:
        import torch
        from basicsr.archs.rrdbnet_arch import RRDBNet
        from realesrgan import RealESRGANer

        print(f"    Using Real-ESRGAN {scale}x upscaling...")

        model = RRDBNet(
            num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=scale
        )

        upsampler = RealESRGANer(
            scale=scale,
            model_path="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
            dni_weight=None,
            model=model,
            tile=0,
            tile_pad=10,
            pre_pad=0,
            half=True,
            gpu_id=0 if torch.cuda.is_available() else None,
        )

        # Convert to numpy
        img_np = np.array(image)

        # Upscale
        output, _ = upsampler.enhance(img_np, outscale=scale)

        # Convert back to PIL
        return Image.fromarray(output)

    except Exception as e:
        print(f"    Real-ESRGAN failed ({e}), using Lanczos fallback...")
        return None


def upscale_with_lanczos(image: Image.Image, scale: int = 4) -> Image.Image:
    """Fallback: high-quality Lanczos resampling."""
    new_size = (image.width * scale, image.height * scale)
    return image.resize(new_size, Image.LANCZOS)


async def enhance_product_photo(
    input_path: Path, output_path: Path, collection: str, max_size: int = 4096
) -> dict:
    """Enhance a single product photo with upscaling + post-processing.

    Returns:
        Dict with enhancement metadata
    """
    print(f"\n{input_path.name}")

    # Load image
    image = Image.open(input_path)

    # Convert to RGB if needed
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Calculate scale factor
    current_max = max(image.width, image.height)
    if current_max < max_size:
        scale = max_size // current_max
        scale = min(scale, 4)  # Max 4x upscale

        # Try Real-ESRGAN first
        enhanced = upscale_with_realesrgan(image, scale=scale)

        if enhanced is None:
            # Fallback to Lanczos
            print(f"    Using Lanczos {scale}x upscaling...")
            enhanced = upscale_with_lanczos(image, scale=scale)
            method = f"Lanczos {scale}x"
        else:
            method = f"Real-ESRGAN {scale}x"

        print(f"    ✓ Upscaled {scale}x: {enhanced.width}x{enhanced.height}")
    else:
        enhanced = image
        method = "No upscaling (already high-res)"

    # Apply luxury post-processing
    enhanced = luxury_post_process(enhanced)
    print("    ✓ Applied luxury post-processing")

    # Save enhanced version
    output_path.parent.mkdir(parents=True, exist_ok=True)
    enhanced.save(output_path, "JPEG", quality=95, optimize=True)
    print(f"    ✓ Saved: {output_path}")

    return {
        "original": str(input_path),
        "enhanced": str(output_path),
        "collection": collection,
        "method": method,
        "original_size": f"{image.width}x{image.height}",
        "enhanced_size": f"{enhanced.width}x{enhanced.height}",
    }


async def main():
    """Enhance all real product photos with Real-ESRGAN + luxury post-processing."""

    # Source directories
    signature_dir = Path("/Users/coreyfoster/Desktop/_Signature Collection_")
    black_rose_dir = Path("/tmp")  # Extracted ZIP

    # Output directory
    enhanced_dir = project_root / "assets" / "enhanced_products"

    print("=== SkyyRose Product Photo Enhancement ===\n")
    print("Using Real-ESRGAN 4x upscaling + luxury post-processing\n")

    # Track all enhancements
    enhanced_products: list[dict] = []

    # SIGNATURE Collection
    print("=== SIGNATURE Collection ===")
    signature_output = enhanced_dir / "signature"

    signature_products = [
        "Cotton Candy Shorts.jpg",
        "Cotton Candy Tee.jpg",
        "Crop Hoodie front.jpg",
        "Crop Hoodie back.jpg",
        "Hoodie.jpg",
        "Lavender Rose Beanie.jpg",
        "Original Label Tee (Orchid).jpg",
        "Original Label Tee (White).jpg",
        "Signature Shorts.jpg",
        "_The Signature Collection_ The Sherpa 2.jpg",
    ]

    for product in signature_products:
        input_file = signature_dir / f"_Signature Collection_ {product}"
        if not input_file.exists():
            input_file = signature_dir / product

        if input_file.exists():
            output_file = signature_output / f"enhanced_{product}"
            result = await enhance_product_photo(input_file, output_file, "SIGNATURE")
            enhanced_products.append(result)

    # BLACK ROSE Collection
    print("\n=== BLACK ROSE Collection ===")
    black_rose_output = enhanced_dir / "black-rose"

    black_rose_products = [
        "The BLACK Rose Sherpa Back.jpg",
        "The BLACK Rose Sherpa Front.jpg",
        "Womens Black Rose Hooded Dress.jpeg",
        "BLACK is Beautiful Giants Front.jpg",
        "The BLACK Jersey (BLACK Rose Collection).jpg",
        "PhotoRoom_003_20230616_170635.jpg",
    ]

    for product in black_rose_products:
        input_file = black_rose_dir / product
        if input_file.exists():
            output_file = black_rose_output / f"enhanced_{product.replace('.jpeg', '.jpg')}"
            result = await enhance_product_photo(input_file, output_file, "BLACK_ROSE")
            enhanced_products.append(result)

    # Save enhancement manifest
    manifest_path = enhanced_dir / "enhancement_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(enhanced_products, f, indent=2)

    print(f"\n\n{'='*60}")
    print("✅ Enhancement Complete!")
    print(f"{'='*60}")
    print(f"\nEnhanced {len(enhanced_products)} products")
    print(f"Saved to: {enhanced_dir}")
    print(f"Manifest: {manifest_path}")

    print("\n📋 Next Steps:")
    print("  1. Review enhanced photos in assets/enhanced_products/")
    print("  2. SELECT which products to make into 3D models")
    print("  3. Remaining products → advanced 2D/2.5D visualizations")
    print("  4. Upload assets to WordPress/WooCommerce")

    print("\n🎨 Enhanced Products by Collection:")
    signature_count = sum(1 for p in enhanced_products if p["collection"] == "SIGNATURE")
    black_rose_count = sum(1 for p in enhanced_products if p["collection"] == "BLACK_ROSE")
    love_hurts_count = sum(1 for p in enhanced_products if p["collection"] == "LOVE_HURTS")

    print(f"  SIGNATURE: {signature_count} products")
    print(f"  BLACK_ROSE: {black_rose_count} products")
    print(f"  LOVE_HURTS: {love_hurts_count} products")


if __name__ == "__main__":
    asyncio.run(main())
