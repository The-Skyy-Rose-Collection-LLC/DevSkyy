#!/usr/bin/env python3
"""
Generate advanced 2D/2.5D visualizations for ALL SkyyRose products.

Creates 4 variations per product (104 total):
- Drop Shadow: Professional depth with offset shadows
- Depth Effect: Simulated depth of field with edge detection
- Parallax Layers: Multi-layer 2.5D effect for web animations
- Enhanced Detail: Sharpened with enhanced textures

Uses Context7-researched Pillow and OpenCV techniques.
"""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file
from dotenv import load_dotenv  # noqa: E402

load_dotenv(project_root / ".env")

print("=== SkyyRose 2D/2.5D Visualization Generator ===\n")

try:
    import numpy as np
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
except ImportError:
    print("Installing required packages...")
    import subprocess

    subprocess.run(
        [sys.executable, "-m", "pip", "install", "pillow", "numpy", "opencv-python"], check=True
    )
    import numpy as np
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps

try:
    import cv2
except ImportError:
    print("Installing OpenCV...")
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "opencv-python"], check=True)
    import cv2


# Directories
ENHANCED_DIR = project_root / "assets" / "enhanced_products" / "all"
OUTPUT_DIR = project_root / "assets" / "2d-25d-assets"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_drop_shadow(
    image: Image.Image,
    offset: tuple[int, int] = (15, 15),
    blur_radius: int = 25,
    opacity: int = 180,
) -> Image.Image:
    """
    Create professional drop shadow effect.

    Uses Context7 Pillow filter techniques for depth.

    Args:
        image: Input PIL Image
        offset: Shadow offset (x, y) in pixels
        blur_radius: Gaussian blur radius for shadow softness
        opacity: Shadow opacity (0-255)

    Returns:
        Image with drop shadow
    """
    # Create new image with space for shadow
    shadow_size = (
        image.width + abs(offset[0]) + blur_radius * 2,
        image.height + abs(offset[1]) + blur_radius * 2,
    )

    # Create shadow layer
    shadow = Image.new("RGBA", shadow_size, (0, 0, 0, 0))

    # Position for shadow
    shadow_pos = (blur_radius + max(0, offset[0]), blur_radius + max(0, offset[1]))

    # Create shadow mask from image alpha
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # Extract alpha channel as shadow
    shadow_mask = Image.new("RGBA", image.size, (0, 0, 0, opacity))
    shadow_mask.putalpha(image.split()[3])  # Use original alpha

    # Paste shadow and blur (Context7 GaussianBlur technique)
    shadow.paste(shadow_mask, shadow_pos)
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))

    # Position for original image (on top of shadow)
    image_pos = (blur_radius + max(0, -offset[0]), blur_radius + max(0, -offset[1]))

    # Composite original image over shadow
    shadow.paste(image, image_pos, image)

    return shadow


def create_depth_effect(image: Image.Image, focal_strength: float = 0.7) -> Image.Image:
    """
    Create depth of field effect using edge detection.

    Uses Context7 OpenCV Canny edge detection + Pillow blur.

    Args:
        image: Input PIL Image
        focal_strength: Strength of blur on non-focal areas (0.0-1.0)

    Returns:
        Image with depth effect
    """
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Convert to numpy for OpenCV (Context7 technique)
    img_array = np.array(image)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

    # Detect edges (Context7 Canny technique)
    edges = cv2.Canny(gray, 50, 150)

    # Create depth mask (edges = in focus, far from edges = blurred)
    # Dilate edges to create focus region
    kernel = np.ones((21, 21), np.uint8)
    focus_mask = cv2.dilate(edges, kernel, iterations=1)
    focus_mask = cv2.GaussianBlur(focus_mask, (51, 51), 0)

    # Convert back to PIL
    focus_pil = Image.fromarray(focus_mask).convert("L")

    # Create blurred version (Context7 GaussianBlur)
    blurred = image.filter(ImageFilter.GaussianBlur(radius=8 * focal_strength))

    # Composite focused and blurred based on mask
    result = Image.composite(image, blurred, ImageOps.invert(focus_pil))

    return result


def create_parallax_layers(image: Image.Image) -> Image.Image:
    """
    Create parallax-ready layered image for 2.5D web effects.

    Separates foreground from background with offset for animation.

    Args:
        image: Input PIL Image

    Returns:
        Layered image with parallax separation
    """
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # Convert to numpy for OpenCV edge detection
    img_array = np.array(image)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGBA2GRAY)

    # Detect edges to find product boundaries
    edges = cv2.Canny(gray, 30, 100)

    # Find largest contour (product)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        # Get largest contour
        largest_contour = max(contours, key=cv2.contourArea)

        # Create mask for foreground
        mask = np.zeros(gray.shape, np.uint8)
        cv2.drawContours(mask, [largest_contour], -1, 255, -1)

        # Blur mask edges for smooth transition
        mask = cv2.GaussianBlur(mask, (21, 21), 0)  # type: ignore[assignment]
        mask_pil = Image.fromarray(mask).convert("L")

        # Create foreground and background layers
        # Foreground: product with slight offset
        foreground = image.copy()

        # Background: blurred copy with offset
        background = image.filter(ImageFilter.GaussianBlur(5))
        background = ImageEnhance.Brightness(background).enhance(0.9)

        # Create canvas with space for parallax offset
        canvas = Image.new("RGBA", (image.width + 20, image.height + 20), (0, 0, 0, 0))

        # Paste background (offset)
        canvas.paste(background, (10, 10), background)

        # Paste foreground (centered, using mask)
        canvas.paste(foreground, (5, 5), mask_pil)

        return canvas
    else:
        # No contours found, return enhanced original
        return image


def create_enhanced_detail(image: Image.Image, sharpness: float = 2.0) -> Image.Image:
    """
    Enhance details with sharpening and texture enhancement.

    Uses Context7 DETAIL filter + sharpening.

    Args:
        image: Input PIL Image
        sharpness: Sharpening strength (1.0 = normal, 2.0 = enhanced)

    Returns:
        Detail-enhanced image
    """
    # Apply DETAIL filter (Context7 technique)
    enhanced = image.filter(ImageFilter.DETAIL)

    # Apply SHARPEN filter
    enhanced = enhanced.filter(ImageFilter.SHARPEN)

    # Enhance sharpness programmatically
    enhancer = ImageEnhance.Sharpness(enhanced)
    enhanced = enhancer.enhance(sharpness)

    # Enhance contrast slightly
    contrast = ImageEnhance.Contrast(enhanced)
    enhanced = contrast.enhance(1.1)

    return enhanced


def generate_all_variations(product_path: Path, output_dir: Path) -> dict[str, Path | None]:
    """Generate all 4 variations for a product."""

    results: dict[str, Path | None] = {
        "drop_shadow": None,
        "depth_effect": None,
        "parallax_layers": None,
        "enhanced_detail": None,
    }

    # Load image
    image = Image.open(product_path)
    base_name = product_path.stem.replace("enhanced_", "")

    print(f"  Generating variations for: {base_name}")

    # 1. Drop Shadow
    try:
        shadow_img = create_drop_shadow(image)
        shadow_path = output_dir / f"{base_name}_shadow.jpg"
        # Convert RGBA to RGB for JPEG
        if shadow_img.mode == "RGBA":
            # Create white background
            bg = Image.new("RGB", shadow_img.size, (255, 255, 255))
            bg.paste(shadow_img, mask=shadow_img.split()[3])
            shadow_img = bg
        shadow_img.save(shadow_path, quality=95)
        results["drop_shadow"] = shadow_path
        print(f"    ✓ Drop Shadow: {shadow_path.name}")
    except Exception as e:
        print(f"    ✗ Drop Shadow failed: {e}")

    # 2. Depth Effect
    try:
        depth_img = create_depth_effect(image)
        depth_path = output_dir / f"{base_name}_depth.jpg"
        depth_img.save(depth_path, quality=95)
        results["depth_effect"] = depth_path
        print(f"    ✓ Depth Effect: {depth_path.name}")
    except Exception as e:
        print(f"    ✗ Depth Effect failed: {e}")

    # 3. Parallax Layers
    try:
        parallax_img = create_parallax_layers(image)
        parallax_path = output_dir / f"{base_name}_parallax.png"
        parallax_img.save(parallax_path)
        results["parallax_layers"] = parallax_path
        print(f"    ✓ Parallax Layers: {parallax_path.name}")
    except Exception as e:
        print(f"    ✗ Parallax Layers failed: {e}")

    # 4. Enhanced Detail
    try:
        detail_img = create_enhanced_detail(image)
        detail_path = output_dir / f"{base_name}_detail.jpg"
        detail_img.save(detail_path, quality=95)
        results["enhanced_detail"] = detail_path
        print(f"    ✓ Enhanced Detail: {detail_path.name}")
    except Exception as e:
        print(f"    ✗ Enhanced Detail failed: {e}")

    return results


def main():
    """Generate 2D/2.5D visualizations for all products."""

    # Check if enhanced products exist
    if not ENHANCED_DIR.exists():
        print(f"❌ Enhanced products directory not found: {ENHANCED_DIR}")
        return 1

    # Get all enhanced product images (all supported formats)
    product_images: list[Path] = []
    for ext in ["*.jpg", "*.jpeg", "*.JPG", "*.JPEG", "*.png", "*.PNG"]:
        product_images.extend(ENHANCED_DIR.glob(ext))

    print(f"Found {len(product_images)} total images")

    # Filter to only clothing items (exclude accessories, logos, packaging)
    # User specified: "those folders are not all clothing"
    non_clothing_keywords = [
        "logo",
        "tag",
        "label",
        "package",
        "box",
        "bag",
        "hanger",
        "receipt",
        "card",
        "sticker",
        "icon",
        "banner",
        "button",
    ]

    def is_clothing_item(path: Path) -> bool:
        name_lower = path.stem.lower()
        # Exclude obvious non-clothing items (return True if no keywords match)
        return not any(kw in name_lower for kw in non_clothing_keywords)

    product_images = [p for p in product_images if is_clothing_item(p)]

    if not product_images:
        print(f"❌ No product images found in: {ENHANCED_DIR}")
        return 1

    print(f"Filtered to {len(product_images)} clothing items")
    print(f"Generating 4 variations each = {len(product_images) * 4} total images\n")

    # Try to use tqdm for progress bar
    try:
        from tqdm import tqdm

        product_iter = tqdm(product_images, desc="Generating 2D/2.5D", unit="product")
    except ImportError:
        print("Note: Install tqdm for progress bars (pip install tqdm)\n")
        product_iter = product_images

    total_generated = 0

    for product_path in product_iter:
        results = generate_all_variations(product_path, OUTPUT_DIR)

        # Count successful generations
        total_generated += sum(1 for v in results.values() if v is not None)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"✅ Generated {total_generated}/{len(product_images) * 4} visualizations")
    print(f"{'=' * 60}")
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("\nVariation types:")
    print("  1. Drop Shadow (_shadow.jpg) - Professional depth")
    print("  2. Depth Effect (_depth.jpg) - Simulated depth of field")
    print("  3. Parallax Layers (_parallax.png) - 2.5D web animation ready")
    print("  4. Enhanced Detail (_detail.jpg) - Sharpened textures")

    if total_generated == len(product_images) * 4:
        print("\n📋 Next Steps:")
        print("  1. Review generated visualizations")
        print("  2. Upload to WooCommerce product galleries")
        print("  3. Configure parallax effects on product pages")
        return 0
    else:
        print(f"\n⚠️  {len(product_images) * 4 - total_generated} variations failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
