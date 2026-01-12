#!/usr/bin/env python3
"""
Product Image Processor for SkyyRose WordPress
================================================

Automatically processes product images for WordPress Media Library:
- Resizes to standard ecommerce dimensions (1200x1200, 600x600, 300x300)
- Crops to center square (1:1 aspect ratio)
- Converts to WebP format (90% quality)
- Organizes by collection and product
- Generates SEO-friendly filenames

Usage:
    python3 process_product_images.py

Requirements:
    pip install Pillow

Author: Claude (Principal Engineer)
Created: 2026-01-11
"""

import re
from pathlib import Path

from PIL import Image

# ==================== Configuration ====================

SOURCE_DIR = Path("/Users/coreyfoster/DevSkyy/assets/3d-models")
OUTPUT_DIR = Path("/Users/coreyfoster/DevSkyy/wordpress/product-images-processed")

# Image sizes (width, height)
SIZES: dict[str, tuple[int, int]] = {
    "main": (1200, 1200),  # Product page hero
    "gallery": (1200, 1200),  # Lightbox images
    "thumb": (300, 300),  # Product grid thumbnails
    "mobile": (600, 600),  # Mobile optimized
}

WEBP_QUALITY = 90  # 90% quality for sharp product photos
MAX_FILE_SIZE_KB = 150  # Target file size in KB

# Collections to process
COLLECTIONS = {
    "love-hurts": "_Love Hurts Collection_",
    "black-rose": "_BLACK Rose Collection_",
}

# ==================== Helper Functions ====================


def sanitize_filename(name: str) -> str:
    """
    Convert filename to SEO-friendly format.

    Examples:
        "Men windbreaker jacket (1).png" → "men-windbreaker-jacket"
        "PhotoRoom_002_20221110_201626.png" → "photoroom-002"
    """
    # Remove file extension
    name = Path(name).stem

    # Remove PhotoRoom timestamps
    name = re.sub(r"_\d{8}_\d{6}", "", name)

    # Convert to lowercase, replace spaces with hyphens
    name = name.lower().replace(" ", "-")

    # Remove special characters (keep only alphanumeric and hyphens)
    name = re.sub(r"[^a-z0-9-]", "", name)

    # Remove multiple consecutive hyphens
    name = re.sub(r"-+", "-", name)

    # Truncate to 50 characters (SEO best practice)
    if len(name) > 50:
        name = name[:50].rstrip("-")

    return name


def determine_view_type(filename: str) -> str:
    """
    Infer image view type from filename.

    Returns:
        'main', 'front', 'back', 'detail', or 'lifestyle'
    """
    filename_lower = filename.lower()

    if "front" in filename_lower:
        return "front"
    elif "back" in filename_lower:
        return "back"
    elif any(word in filename_lower for word in ["detail", "close", "zoom", "texture"]):
        return "detail"
    elif any(word in filename_lower for word in ["lifestyle", "photoroom", "model", "worn"]):
        return "lifestyle"
    else:
        return "main"


def crop_to_square(img: Image.Image) -> Image.Image:
    """
    Crop image to center square (1:1 aspect ratio).

    Args:
        img: PIL Image object

    Returns:
        Cropped square image
    """
    width, height = img.size
    min_dim = min(width, height)

    # Calculate crop coordinates (center crop)
    left = (width - min_dim) // 2
    top = (height - min_dim) // 2
    right = left + min_dim
    bottom = top + min_dim

    return img.crop((left, top, right, bottom))


def remove_background_if_transparent(img: Image.Image) -> Image.Image:
    """
    Convert images with alpha channel to RGB with white background.

    Args:
        img: PIL Image object

    Returns:
        RGB image (alpha channel removed)
    """
    if img.mode in ("RGBA", "LA", "P"):
        # Create white background
        background = Image.new("RGB", img.size, (255, 255, 255))

        # Paste original image on white background
        if img.mode == "RGBA":
            background.paste(img, mask=img.split()[-1])  # Use alpha as mask
        else:
            background.paste(img)

        return background

    # Already RGB or other mode without transparency
    return img.convert("RGB") if img.mode != "RGB" else img


def process_image(
    input_path: Path, collection: str, product_name: str, view_type: str = "main"
) -> None:
    """
    Process a single product image: resize, crop, convert to WebP.

    Args:
        input_path: Path to source image
        collection: Collection name (e.g., 'love-hurts')
        product_name: Sanitized product name
        view_type: Image view type (main, front, back, lifestyle)
    """
    try:
        # Open image
        img = Image.open(input_path)

        # Remove transparency
        img = remove_background_if_transparent(img)

        # Crop to square
        img = crop_to_square(img)

        # Create output directory
        product_dir = OUTPUT_DIR / collection / product_name
        product_dir.mkdir(parents=True, exist_ok=True)

        # Generate images at all sizes
        for size_name, dimensions in SIZES.items():
            # Resize with high-quality Lanczos resampling
            resized = img.resize(dimensions, Image.Resampling.LANCZOS)

            # Generate filename: {collection}-{product}-{view}-{size}.webp
            filename = f"{collection}-{product_name}-{view_type}-{size_name}.webp"
            output_path = product_dir / filename

            # Save as WebP
            resized.save(
                output_path,
                "WEBP",
                quality=WEBP_QUALITY,
                method=6,  # Slowest but best compression
            )

            # Get file size
            file_size_kb = output_path.stat().st_size / 1024

            # Log result
            status = "✓" if file_size_kb <= MAX_FILE_SIZE_KB else "⚠"
            print(f"  {status} {filename} ({file_size_kb:.1f} KB)")

    except Exception as e:
        print(f"  ✗ Error processing {input_path.name}: {e}")


def process_collection(collection: str, folder_name: str) -> int:
    """
    Process all images in a collection folder.

    Args:
        collection: Collection slug (e.g., 'love-hurts')
        folder_name: Source folder name (e.g., '_Love Hurts Collection_')

    Returns:
        Number of images processed
    """
    source_path = SOURCE_DIR / folder_name

    if not source_path.exists():
        print(f"⚠ Skipping {collection}: Folder not found at {source_path}")
        return 0

    print(f"\n{'=' * 60}")
    print(f"Processing {collection.upper().replace('-', ' ')} Collection")
    print(f"{'=' * 60}")

    # Supported image formats
    image_extensions = ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG")
    image_files = []
    for ext in image_extensions:
        image_files.extend(source_path.glob(ext))

    if not image_files:
        print(f"  No images found in {source_path}")
        return 0

    print(f"Found {len(image_files)} images\n")

    processed_count = 0

    for image_file in sorted(image_files):
        # Sanitize filename for product name
        product_name = sanitize_filename(image_file.name)

        # Determine view type
        view_type = determine_view_type(image_file.name)

        # Log processing
        print(f"Processing: {image_file.name}")
        print(f"  Product: {product_name}")
        print(f"  View: {view_type}")

        # Process image
        process_image(image_file, collection, product_name, view_type)

        processed_count += 1
        print()  # Blank line between products

    return processed_count


def main():
    """
    Main execution: process all collections.
    """
    print("\n" + "=" * 60)
    print("SkyyRose Product Image Processor")
    print("=" * 60)
    print(f"Source: {SOURCE_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Sizes: {', '.join(f'{k}={v[0]}×{v[1]}' for k, v in SIZES.items())}")
    print(f"Format: WebP (quality {WEBP_QUALITY}%)")
    print("=" * 60)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total_processed = 0

    # Process each collection
    for collection, folder_name in COLLECTIONS.items():
        count = process_collection(collection, folder_name)
        total_processed += count

    # Summary
    print("\n" + "=" * 60)
    print("✅ Processing Complete!")
    print("=" * 60)
    print(f"Total images processed: {total_processed}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("\nNext steps:")
    print("1. Review processed images in output directory")
    print("2. Upload to WordPress Media Library")
    print("3. Assign images to WooCommerce products")
    print("4. Add alt text and captions for SEO")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
