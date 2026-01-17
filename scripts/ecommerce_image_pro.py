#!/usr/bin/env python3
"""
Professional E-Commerce Image Enhancement Pipeline
===================================================

Top-tier cloud-based image processing using Replicate API:
- Real-ESRGAN 4x AI upscaling (nightmareai/real-esrgan)
- AI background removal (cjwbw/rembg)
- Professional e-commerce sizing & layouts
- White/transparent backgrounds
- Multi-format export for WooCommerce

E-Commerce Size Standards:
- Thumbnail: 300x300 (product grid)
- Gallery: 800x800 (product gallery)
- Main: 1200x1200 (product page hero)
- Retina: 2400x2400 (high-DPI displays)
- Zoom: 3000x3000 (hover zoom)

Usage:
    # Set API key first
    export REPLICATE_API_TOKEN="r8_..."

    # Process single image
    python scripts/ecommerce_image_pro.py --input image.jpg --output-dir enhanced/

    # Process collection
    python scripts/ecommerce_image_pro.py --collection signature

    # Process all collections
    python scripts/ecommerce_image_pro.py --all

    # Dry run (show what would be processed)
    python scripts/ecommerce_image_pro.py --all --dry-run

Author: DevSkyy Platform Team
Version: 2.0.0
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import shutil
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

# Add project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PIL import Image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# E-Commerce Size Standards
class EcomSize(NamedTuple):
    """E-commerce image size specification."""

    name: str
    width: int
    height: int
    suffix: str
    format: str
    quality: int
    use_case: str


ECOM_SIZES = [
    EcomSize("thumb", 300, 300, "thumb", "JPEG", 85, "Product grid thumbnails"),
    EcomSize("gallery", 800, 800, "gallery", "JPEG", 90, "Product gallery images"),
    EcomSize("main", 1200, 1200, "main", "JPEG", 92, "Product page hero"),
    EcomSize("retina", 2400, 2400, "retina", "JPEG", 95, "Retina/HiDPI displays"),
    EcomSize("zoom", 3000, 3000, "zoom", "JPEG", 95, "Hover zoom feature"),
    EcomSize("transparent", 1200, 1200, "trans", "PNG", 100, "Transparent background"),
]

# SkyyRose Brand Colors
BRAND = {
    "primary": "#B76E79",  # Rose Gold
    "secondary": "#1A1A1A",  # Black
    "accent": "#D4AF37",  # Gold
    "background": "#FFFFFF",  # White (e-commerce standard)
}


@dataclass
class ProcessingResult:
    """Result of processing a single image."""

    input_path: Path
    output_dir: Path
    success: bool = False
    upscaled: bool = False
    bg_removed: bool = False
    sizes_exported: list[str] = field(default_factory=list)
    error: str | None = None
    processing_time: float = 0.0


class EcommerceImageProcessor:
    """Professional e-commerce image processor using Replicate API."""

    # Replicate models
    UPSCALE_MODEL = (
        "nightmareai/real-esrgan:f121d640bd286e1fdc67f9799164c1d5be36ff74576ee11c803ae5b665dd46aa"
    )
    REMBG_MODEL = "cjwbw/rembg:fb8af171cfa1616ddcf1242c093f9c46bcada5ad4cf6f2fbe8b81b330ec5c003"

    def __init__(self, api_token: str | None = None):
        """Initialize processor with Replicate API token."""
        self.api_token = api_token or os.environ.get("REPLICATE_API_TOKEN")
        self.replicate_available = False

        if self.api_token:
            try:
                import replicate

                self.replicate = replicate
                self.replicate_available = True
                logger.info("Replicate API initialized successfully")
            except ImportError:
                logger.warning("replicate package not installed. Run: pip install replicate")
        else:
            logger.warning("REPLICATE_API_TOKEN not set. Cloud AI features disabled.")
            logger.info("Get your API key at: https://replicate.com/account/api-tokens")

    def upscale_image(self, image_path: Path, scale: int = 4) -> Path | None:
        """Upscale image using Real-ESRGAN via Replicate."""
        if not self.replicate_available:
            logger.warning("Replicate not available, skipping AI upscale")
            return None

        try:
            logger.info(f"  AI upscaling {image_path.name} ({scale}x)...")

            with open(image_path, "rb") as f:
                output = self.replicate.run(
                    self.UPSCALE_MODEL,
                    input={
                        "image": f,
                        "scale": scale,
                        "face_enhance": False,  # Clothing, not faces
                    },
                )

            # Download upscaled image
            upscaled_path = image_path.parent / f"{image_path.stem}_upscaled{image_path.suffix}"

            if hasattr(output, "read"):
                with open(upscaled_path, "wb") as f:
                    f.write(output.read())
            else:
                # URL output
                import urllib.request

                urllib.request.urlretrieve(str(output), upscaled_path)

            logger.info(f"  Upscaled: {upscaled_path.name}")
            return upscaled_path

        except Exception as e:
            logger.error(f"  Upscale failed: {e}")
            return None

    def remove_background(self, image_path: Path) -> Path | None:
        """Remove background using rembg via Replicate."""
        if not self.replicate_available:
            logger.warning("Replicate not available, skipping background removal")
            return None

        try:
            logger.info(f"  Removing background from {image_path.name}...")

            with open(image_path, "rb") as f:
                output = self.replicate.run(self.REMBG_MODEL, input={"image": f})

            # Download result
            nobg_path = image_path.parent / f"{image_path.stem}_nobg.png"

            if hasattr(output, "read"):
                with open(nobg_path, "wb") as f:
                    f.write(output.read())
            else:
                import urllib.request

                urllib.request.urlretrieve(str(output), nobg_path)

            logger.info(f"  Background removed: {nobg_path.name}")
            return nobg_path

        except Exception as e:
            logger.error(f"  Background removal failed: {e}")
            return None

    def create_white_background(self, image_path: Path) -> Image.Image:
        """Create image with white background (e-commerce standard)."""
        img = Image.open(image_path)

        if img.mode == "RGBA":
            # Create white background
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # Use alpha as mask
            return background
        elif img.mode != "RGB":
            return img.convert("RGB")
        return img

    def resize_contain(self, img: Image.Image, size: tuple[int, int]) -> Image.Image:
        """Resize image to fit within size while maintaining aspect ratio.

        Centers image on white background (e-commerce standard).
        """
        # Calculate aspect-ratio-preserving size
        img_ratio = img.width / img.height
        target_ratio = size[0] / size[1]

        if img_ratio > target_ratio:
            # Image is wider - fit to width
            new_width = size[0]
            new_height = int(size[0] / img_ratio)
        else:
            # Image is taller - fit to height
            new_height = size[1]
            new_width = int(size[1] * img_ratio)

        # Resize with high-quality resampling
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Create square canvas with white background
        canvas = Image.new("RGB", size, (255, 255, 255))

        # Center the image
        x = (size[0] - new_width) // 2
        y = (size[1] - new_height) // 2
        canvas.paste(resized, (x, y))

        return canvas

    def export_sizes(
        self,
        source_image: Path,
        output_dir: Path,
        sku: str,
    ) -> list[str]:
        """Export image in all e-commerce sizes."""
        exported = []
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load source image
        img = self.create_white_background(source_image)

        for size_spec in ECOM_SIZES:
            try:
                # Resize to target size
                resized = self.resize_contain(img, (size_spec.width, size_spec.height))

                # Determine output path
                ext = "png" if size_spec.format == "PNG" else "jpg"
                output_path = output_dir / f"{sku}_{size_spec.suffix}.{ext}"

                # Save with appropriate quality
                if size_spec.format == "PNG":
                    resized.save(output_path, "PNG", optimize=True)
                else:
                    # Convert to RGB if needed for JPEG
                    if resized.mode == "RGBA":
                        resized = resized.convert("RGB")
                    resized.save(
                        output_path,
                        "JPEG",
                        quality=size_spec.quality,
                        optimize=True,
                    )

                exported.append(size_spec.name)
                logger.debug(f"    Exported: {output_path.name}")

            except Exception as e:
                logger.error(f"    Failed to export {size_spec.name}: {e}")

        return exported

    def process_image(
        self,
        image_path: Path,
        output_dir: Path,
        collection: str = "general",
        enable_upscale: bool = True,
        enable_bg_removal: bool = True,
    ) -> ProcessingResult:
        """Process a single product image through the full pipeline."""
        start_time = time.time()
        result = ProcessingResult(input_path=image_path, output_dir=output_dir)

        try:
            # Generate SKU from filename
            sku = self._generate_sku(image_path, collection)
            logger.info(f"\nProcessing: {image_path.name} -> {sku}")

            # Create temp directory for processing
            temp_dir = output_dir / ".temp"
            temp_dir.mkdir(parents=True, exist_ok=True)

            # Copy source to temp
            working_image = temp_dir / image_path.name
            shutil.copy2(image_path, working_image)

            # Step 1: AI Upscale (if enabled and needed)
            if enable_upscale and self.replicate_available:
                img = Image.open(working_image)
                min_dim = min(img.width, img.height)

                if min_dim < 2400:  # Need upscaling for retina
                    upscaled = self.upscale_image(working_image, scale=4)
                    if upscaled:
                        working_image = upscaled
                        result.upscaled = True

            # Step 2: Background Removal (if enabled)
            if enable_bg_removal and self.replicate_available:
                nobg = self.remove_background(working_image)
                if nobg:
                    working_image = nobg
                    result.bg_removed = True

            # Step 3: Export all e-commerce sizes
            product_dir = output_dir / collection / sku
            exported = self.export_sizes(working_image, product_dir, sku)
            result.sizes_exported = exported

            # Cleanup temp
            shutil.rmtree(temp_dir, ignore_errors=True)

            result.success = len(exported) > 0
            result.processing_time = time.time() - start_time

            logger.info(f"  Success: {len(exported)} sizes exported to {product_dir.name}/")

        except Exception as e:
            result.error = str(e)
            result.processing_time = time.time() - start_time
            logger.error(f"  Failed: {e}")

        return result

    def _generate_sku(self, image_path: Path, collection: str) -> str:
        """Generate a clean SKU from image filename."""
        # Collection prefix mapping
        prefixes = {
            "signature": "SIG",
            "black-rose": "BR",
            "love-hurts": "LH",
            "general": "GEN",
        }
        prefix = prefixes.get(collection.lower(), "PROD")

        # Clean the filename
        name = image_path.stem
        # Remove common patterns
        for pattern in ["PhotoRoom_", "IMG_", "Photo ", "_enhanced", "_upscaled", "_nobg"]:
            name = name.replace(pattern, "")

        # Clean special chars
        clean = "".join(c if c.isalnum() else "_" for c in name)
        clean = "_".join(filter(None, clean.split("_")))  # Remove empty segments

        # Truncate and add hash for uniqueness
        if len(clean) > 25:
            hash_suffix = hashlib.md5(name.encode()).hexdigest()[:6].upper()
            clean = f"{clean[:20]}_{hash_suffix}"

        return f"{prefix}_{clean}".upper()

    def process_collection(
        self,
        collection: str,
        output_dir: Path,
        limit: int | None = None,
    ) -> list[ProcessingResult]:
        """Process all images in a collection."""
        # Collection source directories
        source_dirs = [
            PROJECT_ROOT / "assets" / "3d-models" / collection,
            PROJECT_ROOT
            / "generated_assets"
            / "product_images"
            / f"_{collection.replace('-', ' ').title()} Collection_",
        ]

        results = []
        image_extensions = {".jpg", ".jpeg", ".png", ".webp"}

        for source_dir in source_dirs:
            if not source_dir.exists():
                continue

            images = [
                f
                for f in source_dir.rglob("*")
                if f.is_file()
                and f.suffix.lower() in image_extensions
                and not f.name.startswith(".")
            ]

            if limit:
                images = images[:limit]

            logger.info(f"\n{'=' * 60}")
            logger.info(f"COLLECTION: {collection.upper()}")
            logger.info(f"Source: {source_dir}")
            logger.info(f"Images: {len(images)}")
            logger.info("=" * 60)

            for i, image_path in enumerate(images, 1):
                logger.info(f"\n[{i}/{len(images)}]")
                result = self.process_image(
                    image_path,
                    output_dir,
                    collection=collection,
                )
                results.append(result)

        return results


def main():
    """Run the e-commerce image processing pipeline."""
    parser = argparse.ArgumentParser(
        description="Professional E-Commerce Image Enhancement Pipeline"
    )
    parser.add_argument("--input", type=Path, help="Single image to process")
    parser.add_argument(
        "--collection",
        choices=["signature", "black-rose", "love-hurts"],
        help="Process specific collection",
    )
    parser.add_argument("--all", action="store_true", help="Process all collections")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "assets" / "ecommerce-images",
        help="Output directory",
    )
    parser.add_argument("--limit", type=int, help="Limit images per collection")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed")
    parser.add_argument("--no-upscale", action="store_true", help="Skip AI upscaling")
    parser.add_argument("--no-bg-removal", action="store_true", help="Skip background removal")

    args = parser.parse_args()

    if not any([args.input, args.collection, args.all]):
        parser.print_help()
        print("\n\nExamples:")
        print("  python scripts/ecommerce_image_pro.py --collection signature --limit 3")
        print("  python scripts/ecommerce_image_pro.py --all")
        print("  python scripts/ecommerce_image_pro.py --input product.jpg --output-dir enhanced/")
        sys.exit(1)

    # Check for API token
    if not os.environ.get("REPLICATE_API_TOKEN"):
        print("\n" + "=" * 70)
        print("REPLICATE API TOKEN REQUIRED")
        print("=" * 70)
        print("\nTo use cloud AI upscaling and background removal:")
        print("1. Get your API key at: https://replicate.com/account/api-tokens")
        print("2. Set it: export REPLICATE_API_TOKEN='r8_...'")
        print("3. Or add to .env: REPLICATE_API_TOKEN=r8_...")
        print("\nProceeding with local processing only (no AI enhancement)...\n")

    print("\n" + "=" * 70)
    print("SKYYROSE E-COMMERCE IMAGE PIPELINE")
    print("Professional Product Photo Enhancement")
    print("=" * 70)
    print(f"\nOutput: {args.output_dir}")
    print(f"AI Upscale: {'Disabled' if args.no_upscale else 'Enabled (Real-ESRGAN 4x)'}")
    print(f"Background Removal: {'Disabled' if args.no_bg_removal else 'Enabled (rembg)'}")
    print("\nE-Commerce Sizes:")
    for size in ECOM_SIZES:
        print(f"  - {size.name}: {size.width}x{size.height} ({size.use_case})")
    print("=" * 70)

    if args.dry_run:
        print("\n[DRY RUN - No files will be processed]\n")
        return

    # Initialize processor
    processor = EcommerceImageProcessor()

    all_results = []
    collections = []

    if args.all:
        collections = ["signature", "black-rose", "love-hurts"]
    elif args.collection:
        collections = [args.collection]

    if collections:
        for collection in collections:
            results = processor.process_collection(
                collection,
                args.output_dir,
                limit=args.limit,
            )
            all_results.extend(results)
    elif args.input:
        result = processor.process_image(
            args.input,
            args.output_dir,
            enable_upscale=not args.no_upscale,
            enable_bg_removal=not args.no_bg_removal,
        )
        all_results.append(result)

    # Summary
    success_count = sum(1 for r in all_results if r.success)
    fail_count = len(all_results) - success_count

    print("\n" + "=" * 70)
    print("PROCESSING COMPLETE")
    print("=" * 70)
    print(f"Total: {len(all_results)} images")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")

    if success_count > 0:
        print(f"\nOutput saved to: {args.output_dir}")
        print("\nNext steps:")
        print("  1. Review enhanced images in output directory")
        print("  2. Upload to WordPress: python scripts/upload_images_to_wordpress.py")
        print("  3. Import Elementor templates via wp-admin")

    # Save manifest
    manifest = {
        "generated_at": datetime.now().isoformat(),
        "total_images": len(all_results),
        "successful": success_count,
        "failed": fail_count,
        "output_dir": str(args.output_dir),
        "results": [
            {
                "input": str(r.input_path),
                "output": str(r.output_dir),
                "success": r.success,
                "upscaled": r.upscaled,
                "bg_removed": r.bg_removed,
                "sizes": r.sizes_exported,
                "error": r.error,
                "time_seconds": round(r.processing_time, 2),
            }
            for r in all_results
        ],
    }

    manifest_path = args.output_dir / "ECOMMERCE_MANIFEST.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest: {manifest_path}")


if __name__ == "__main__":
    main()
