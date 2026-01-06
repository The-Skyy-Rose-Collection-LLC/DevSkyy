#!/usr/bin/env python3
"""
Upload Product Images from Google Drive to WooCommerce
======================================================

Downloads images from Google Drive folders and uploads them to WooCommerce
with automatic product creation and categorization.

Usage:
    python3 scripts/upload_drive_to_woocommerce.py --drive-folder-id <ID> --collection BLACK_ROSE

Requirements:
    pip install gdown httpx pillow python-dotenv
"""

import argparse
import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Clothing item keywords for filtering
CLOTHING_KEYWORDS = [
    "hoodie",
    "tee",
    "t-shirt",
    "shirt",
    "shorts",
    "dress",
    "jacket",
    "sherpa",
    "bomber",
    "windbreaker",
    "joggers",
    "pants",
    "sweatshirt",
    "sweater",
    "cardigan",
    "blazer",
    "coat",
    "parka",
    "vest",
    "tank",
    "crop",
    "bodysuit",
    "romper",
    "jumpsuit",
    "skirt",
    "leggings",
]

# Exclude non-clothing items
EXCLUDE_KEYWORDS = [
    "beanie",
    "hat",
    "cap",
    "bag",
    "backpack",
    "wallet",
    "belt",
    "accessory",
    "jewelry",
    "necklace",
    "bracelet",
    "ring",
    "earring",
    "watch",
    "sunglasses",
    "scarf",
]


def is_clothing_item(filename: str, product_name: str = "") -> bool:
    """Check if item is clothing based on filename/name."""
    text = f"{filename} {product_name}".lower()

    # Exclude non-clothing items first
    if any(keyword in text for keyword in EXCLUDE_KEYWORDS):
        logger.debug(f"Excluded non-clothing: {filename}")
        return False

    # Check for clothing keywords
    is_clothing = any(keyword in text for keyword in CLOTHING_KEYWORDS)

    if is_clothing:
        logger.debug(f"Detected clothing: {filename}")
    else:
        logger.debug(f"Not recognized as clothing: {filename}")

    return is_clothing


def extract_product_info(filename: str) -> dict[str, str]:
    """Extract product information from filename.

    Expected format: SKU_ProductName_Variant.jpg
    Example: SRS-BR-001_Black_Rose_Hoodie_Front.jpg
    """
    # Remove extension
    name = Path(filename).stem

    # Try to extract SKU (format: XXX-XX-XXX or similar)
    sku_match = re.match(r"([A-Z]{2,4}-[A-Z]{2}-\d{3})", name)
    sku = sku_match.group(1) if sku_match else ""

    # Extract product name (everything after SKU or full name)
    product_name = name.replace(sku, "").strip("_- ") if sku else name

    # Clean up product name
    product_name = re.sub(r"[_-]+", " ", product_name)
    product_name = re.sub(r"\s+", " ", product_name).strip()

    # Capitalize words
    product_name = " ".join(word.capitalize() for word in product_name.split())

    return {
        "sku": sku or f"AUTO-{hash(filename) % 10000:04d}",
        "name": product_name,
    }


async def download_from_drive(folder_url: str, output_dir: Path) -> list[Path]:
    """Download images from Google Drive folder.

    Note: This requires the folder to be publicly accessible.
    For private folders, you'll need to download manually or use Drive API.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("📥 Attempting to download from Google Drive folder...")
    logger.info(f"📁 Output directory: {output_dir}")

    # Extract folder ID from URL
    folder_id_match = re.search(r"folders/([a-zA-Z0-9_-]+)", folder_url)
    if not folder_id_match:
        raise ValueError(f"Could not extract folder ID from URL: {folder_url}")

    folder_id = folder_id_match.group(1)
    logger.info(f"📋 Folder ID: {folder_id}")

    try:
        import gdown

        # Download entire folder
        logger.info("⏳ Downloading folder contents (this may take a while)...")
        gdown.download_folder(
            id=folder_id,
            output=str(output_dir),
            quiet=False,
            use_cookies=False,
        )

        # Find all image files
        image_files = []
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
            image_files.extend(output_dir.rglob(ext))

        logger.info(f"✅ Downloaded {len(image_files)} images")
        return image_files

    except ImportError:
        logger.error("❌ gdown not installed. Install with: pip install gdown")
        logger.info(
            "💡 Alternative: Download manually and provide local directory with --local-dir"
        )
        raise
    except Exception as e:
        logger.error(f"❌ Failed to download from Drive: {e}")
        logger.info("💡 Make sure the folder is publicly accessible (Anyone with link can view)")
        logger.info("💡 Or download manually and use --local-dir instead")
        raise


async def upload_to_woocommerce(
    images: list[Path],
    collection: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Upload images to WooCommerce as products."""

    # WooCommerce credentials
    wc_url = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
    wc_key = os.getenv("WOOCOMMERCE_KEY")
    wc_secret = os.getenv("WOOCOMMERCE_SECRET")

    if not wc_key or not wc_secret:
        raise ValueError("WOOCOMMERCE_KEY and WOOCOMMERCE_SECRET required in .env")

    # Group images by product (based on SKU/name)
    products: dict[str, list[Path]] = {}

    for image_path in images:
        filename = image_path.name

        # Filter: Only clothing items
        if not is_clothing_item(filename):
            continue

        info = extract_product_info(filename)
        sku = info["sku"]

        if sku not in products:
            products[sku] = []
        products[sku].append(image_path)

    logger.info(f"📦 Found {len(products)} unique products (clothing only)")

    if dry_run:
        logger.info("🔍 DRY RUN - No actual uploads will be performed")
        for sku, product_images in products.items():
            info = extract_product_info(product_images[0].name)
            logger.info(f"  • {sku}: {info['name']} ({len(product_images)} images)")
        return {"dry_run": True, "products": len(products)}

    # Get category ID for collection
    category_map = {
        "BLACK_ROSE": "black-rose",
        "LOVE_HURTS": "love-hurts",
        "SIGNATURE": "signature",
    }
    category_slug = category_map.get(collection, "uncategorized")

    async with httpx.AsyncClient(
        base_url=f"{wc_url}/wp-json/wc/v3",
        auth=(wc_key, wc_secret),
        timeout=60.0,
    ) as client:

        # Get category ID
        logger.info(f"🔍 Finding category: {category_slug}")
        response = await client.get("/products/categories", params={"slug": category_slug})
        categories = response.json()

        if not categories:
            logger.warning(f"⚠️  Category '{category_slug}' not found, creating it...")
            response = await client.post(
                "/products/categories",
                json={"name": collection.replace("_", " ").title(), "slug": category_slug},
            )
            category_id = response.json()["id"]
        else:
            category_id = categories[0]["id"]

        logger.info(f"✅ Using category ID: {category_id}")

        # Upload products
        uploaded = 0
        failed = 0

        for sku, product_images in products.items():
            try:
                info = extract_product_info(product_images[0].name)
                product_name = info["name"]

                logger.info(f"📤 Uploading: {product_name} (SKU: {sku})")

                # Check if product exists
                response = await client.get("/products", params={"sku": sku})
                existing_products = response.json()

                # Upload images to WordPress Media Library
                image_ids = []
                for img_path in product_images:
                    logger.info(f"  📸 Uploading image: {img_path.name}")

                    # Read image
                    with open(img_path, "rb") as f:
                        image_data = f.read()

                    # Upload to media library
                    media_response = await client.post(
                        f"{wc_url}/wp-json/wp/v2/media",
                        files={"file": (img_path.name, image_data, "image/jpeg")},
                        headers={"Content-Disposition": f'attachment; filename="{img_path.name}"'},
                    )

                    if media_response.status_code == 201:
                        media_id = media_response.json()["id"]
                        image_ids.append({"id": media_id})
                        logger.info(f"    ✅ Uploaded (ID: {media_id})")
                    else:
                        logger.error(f"    ❌ Failed: {media_response.status_code}")

                if not image_ids:
                    logger.error(f"  ❌ No images uploaded for {sku}")
                    failed += 1
                    continue

                # Create or update product
                product_data = {
                    "name": product_name,
                    "sku": sku,
                    "type": "simple",
                    "status": "draft",  # Start as draft for review
                    "categories": [{"id": category_id}],
                    "images": image_ids,
                    "description": f"SkyyRose {collection.replace('_', ' ')} Collection",
                }

                if existing_products:
                    # Update existing
                    product_id = existing_products[0]["id"]
                    logger.info(f"  🔄 Updating existing product ID: {product_id}")
                    response = await client.put(f"/products/{product_id}", json=product_data)
                else:
                    # Create new
                    logger.info("  ✨ Creating new product")
                    response = await client.post("/products", json=product_data)

                if response.status_code in [200, 201]:
                    product_id = response.json()["id"]
                    logger.info(f"  ✅ Success! Product ID: {product_id}")
                    logger.info(
                        f"     View at: {wc_url}/wp-admin/post.php?post={product_id}&action=edit"
                    )
                    uploaded += 1
                else:
                    logger.error(f"  ❌ Failed: {response.status_code} - {response.text}")
                    failed += 1

            except Exception as e:
                logger.error(f"❌ Error uploading {sku}: {e}")
                failed += 1
                continue

    logger.info("\n📊 Upload Summary:")
    logger.info(f"  ✅ Uploaded: {uploaded}")
    logger.info(f"  ❌ Failed: {failed}")
    logger.info(f"  📦 Total: {len(products)}")

    return {
        "uploaded": uploaded,
        "failed": failed,
        "total": len(products),
    }


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Upload product images from Google Drive to WooCommerce"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--drive-url",
        type=str,
        help="Google Drive folder URL",
    )
    group.add_argument(
        "--local-dir",
        type=Path,
        help="Local directory with images (alternative to Drive)",
    )

    parser.add_argument(
        "--collection",
        type=str,
        choices=["BLACK_ROSE", "LOVE_HURTS", "SIGNATURE"],
        required=True,
        help="Product collection",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be uploaded without actually uploading",
    )

    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("assets/drive-cache"),
        help="Directory for downloaded Drive files",
    )

    return parser.parse_args()


async def main() -> None:
    """Main execution."""
    args = parse_args()

    logger.info("🚀 SkyyRose Product Uploader")
    logger.info(f"📂 Collection: {args.collection}")

    # Get images
    if args.drive_url:
        logger.info("📥 Downloading from Google Drive...")
        cache_dir = args.cache_dir / args.collection.lower()
        images = await download_from_drive(args.drive_url, cache_dir)
    else:
        logger.info(f"📁 Using local directory: {args.local_dir}")
        images = []
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
            images.extend(args.local_dir.rglob(ext))
        logger.info(f"📷 Found {len(images)} images")

    if not images:
        logger.error("❌ No images found!")
        return

    # Upload to WooCommerce
    await upload_to_woocommerce(
        images=images,
        collection=args.collection,
        dry_run=args.dry_run,
    )

    if not args.dry_run:
        logger.info("\n✅ Upload complete!")
        logger.info("🔗 Visit WooCommerce to review products:")
        logger.info(f"   {os.getenv('WORDPRESS_URL')}/wp-admin/edit.php?post_type=product")


if __name__ == "__main__":
    asyncio.run(main())
