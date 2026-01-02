#!/usr/bin/env python3
"""
WordPress Asset Upload Script

Uploads enhanced images and 3D models to WordPress media library
and updates WooCommerce product metadata.

Usage:
    python scripts/upload_assets_to_wordpress.py --images
    python scripts/upload_assets_to_wordpress.py --models
    python scripts/upload_assets_to_wordpress.py --all
    python scripts/upload_assets_to_wordpress.py --dry-run

Author: DevSkyy Platform Team
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import logging
import mimetypes
import os
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import httpx
except ImportError:
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "httpx", "-q"])
    import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class WordPressConfig:
    """WordPress API configuration."""

    url: str
    username: str
    app_password: str

    @classmethod
    def from_env(cls) -> WordPressConfig:
        """Load from environment variables."""
        url = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
        username = os.getenv("WORDPRESS_USERNAME", "")
        password = os.getenv("WORDPRESS_APP_PASSWORD", "")

        if not username or not password:
            raise ValueError(
                "Missing WordPress credentials. Set WORDPRESS_USERNAME and "
                "WORDPRESS_APP_PASSWORD environment variables."
            )

        return cls(url=url, username=username, app_password=password)

    @property
    def auth_header(self) -> str:
        """Get Basic Auth header value."""
        credentials = f"{self.username}:{self.app_password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"


async def upload_media(
    client: httpx.AsyncClient,
    config: WordPressConfig,
    file_path: Path,
    title: str | None = None,
    alt_text: str | None = None,
) -> dict | None:
    """Upload a file to WordPress media library."""
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None

    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type:
        mime_type = "application/octet-stream"

    filename = file_path.name
    title = title or file_path.stem.replace("_", " ").title()

    url = f"{config.url}/index.php?rest_route=/wp/v2/media"

    with open(file_path, "rb") as f:
        file_data = f.read()

    headers = {
        "Authorization": config.auth_header,
        "Content-Type": mime_type,
        "Content-Disposition": f'attachment; filename="{filename}"',
    }

    try:
        response = await client.post(
            url,
            content=file_data,
            headers=headers,
        )

        if response.status_code == 201:
            result = response.json()
            media_id = result.get("id")
            media_url = result.get("source_url", result.get("guid", {}).get("rendered"))
            logger.info(f"Uploaded: {filename} (ID: {media_id})")

            # Update alt text if provided
            if alt_text and media_id:
                await asyncio.sleep(1)
                await update_media_meta(client, config, media_id, alt_text=alt_text)

            return {
                "id": media_id,
                "url": media_url,
                "filename": filename,
            }
        else:
            logger.error(
                f"Failed to upload {filename}: {response.status_code} - {response.text[:200]}"
            )
            return None

    except Exception as e:
        logger.error(f"Error uploading {filename}: {e}")
        return None


async def update_media_meta(
    client: httpx.AsyncClient,
    config: WordPressConfig,
    media_id: int,
    alt_text: str | None = None,
    caption: str | None = None,
) -> bool:
    """Update media metadata."""
    url = f"{config.url}/index.php?rest_route=/wp/v2/media/{media_id}"

    data = {}
    if alt_text:
        data["alt_text"] = alt_text
    if caption:
        data["caption"] = caption

    if not data:
        return True

    try:
        response = await client.post(
            url,
            json=data,
            headers={
                "Authorization": config.auth_header,
                "Content-Type": "application/json",
            },
        )
        return response.status_code == 200
    except Exception:
        return False


async def update_product_3d_meta(
    client: httpx.AsyncClient,
    config: WordPressConfig,
    product_id: int,
    glb_url: str,
    usdz_url: str | None = None,
) -> bool:
    """Update WooCommerce product with 3D model URLs."""
    url = f"{config.url}/index.php?rest_route=/wc/v3/products/{product_id}"

    data = {
        "meta_data": [
            {"key": "_skyyrose_glb_url", "value": glb_url},
            {"key": "_skyyrose_ar_enabled", "value": "yes"},
        ]
    }

    if usdz_url:
        data["meta_data"].append({"key": "_skyyrose_usdz_url", "value": usdz_url})

    try:
        response = await client.put(
            url,
            json=data,
            headers={
                "Authorization": config.auth_header,
                "Content-Type": "application/json",
            },
        )
        if response.status_code == 200:
            logger.info(f"Updated product {product_id} with 3D model URL")
            return True
        else:
            logger.error(f"Failed to update product {product_id}: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error updating product {product_id}: {e}")
        return False


async def upload_enhanced_images(config: WordPressConfig, dry_run: bool = False) -> dict:
    """Upload all enhanced images."""
    results = {
        "uploaded": [],
        "failed": [],
        "skipped": [],
    }

    enhanced_dir = PROJECT_ROOT / "assets" / "enhanced-images"
    if not enhanced_dir.exists():
        logger.warning(f"Enhanced images directory not found: {enhanced_dir}")
        return results

    manifest_path = enhanced_dir / "ENHANCEMENT_MANIFEST.json"
    if not manifest_path.exists():
        logger.warning("Enhancement manifest not found")
        return results

    with open(manifest_path) as f:
        manifest = json.load(f)

    async with httpx.AsyncClient(timeout=60.0) as client:
        for collection, data in manifest.get("collections", {}).items():
            collection_dir = enhanced_dir / collection
            if not collection_dir.exists():
                continue

            for item in data.get("items", []):
                if not item.get("success"):
                    continue

                sku = item["sku"]
                outputs = item.get("outputs", {})

                # Upload main image
                main_file = outputs.get("main")
                if main_file:
                    file_path = collection_dir / sku / main_file
                    if file_path.exists():
                        if dry_run:
                            logger.info(f"[DRY RUN] Would upload: {file_path.name}")
                            results["skipped"].append(str(file_path))
                        else:
                            await asyncio.sleep(2)  # Rate limiting
                            result = await upload_media(
                                client,
                                config,
                                file_path,
                                title=f"{collection.title()} - {sku}",
                                alt_text=f"SkyyRose {collection.title()} Collection product image",
                            )
                            if result:
                                results["uploaded"].append(result)
                            else:
                                results["failed"].append(str(file_path))

    return results


async def upload_3d_models(config: WordPressConfig, dry_run: bool = False) -> dict:
    """Upload all 3D models."""
    results = {
        "uploaded": [],
        "failed": [],
        "skipped": [],
    }

    models_dir = PROJECT_ROOT / "assets" / "3d-models-generated"
    if not models_dir.exists():
        logger.warning(f"3D models directory not found: {models_dir}")
        return results

    async with httpx.AsyncClient(timeout=120.0) as client:
        for collection_dir in models_dir.iterdir():
            if not collection_dir.is_dir():
                continue

            collection = collection_dir.name

            for model_file in collection_dir.glob("*.glb"):
                if dry_run:
                    logger.info(f"[DRY RUN] Would upload: {model_file.name}")
                    results["skipped"].append(str(model_file))
                else:
                    await asyncio.sleep(3)  # Rate limiting (larger files)
                    result = await upload_media(
                        client,
                        config,
                        model_file,
                        title=f"3D Model - {model_file.stem}",
                        alt_text=f"3D model for {collection.title()} Collection",
                    )
                    if result:
                        results["uploaded"].append(result)
                    else:
                        results["failed"].append(str(model_file))

    return results


def print_results(results: dict, asset_type: str) -> None:
    """Print upload results."""
    print(f"\n{'=' * 60}")
    print(f"  {asset_type.upper()} UPLOAD RESULTS")
    print("=" * 60)

    print(f"\nUploaded: {len(results.get('uploaded', []))}")
    for item in results.get("uploaded", []):
        if isinstance(item, dict):
            print(f"  - {item.get('filename')} (ID: {item.get('id')})")
        else:
            print(f"  - {item}")

    if results.get("failed"):
        print(f"\nFailed: {len(results['failed'])}")
        for item in results["failed"]:
            print(f"  - {item}")

    if results.get("skipped"):
        print(f"\nSkipped (dry run): {len(results['skipped'])}")

    print("=" * 60)


async def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Upload assets to WordPress",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--images", action="store_true", help="Upload enhanced images")
    parser.add_argument("--models", action="store_true", help="Upload 3D models")
    parser.add_argument("--all", action="store_true", help="Upload all assets")
    parser.add_argument("--dry-run", action="store_true", help="Preview without uploading")

    args = parser.parse_args()

    try:
        config = WordPressConfig.from_env()
    except ValueError as e:
        logger.error(str(e))
        return 1

    print(f"\nWordPress URL: {config.url}")
    print(f"Username: {config.username}")

    if args.all or args.images:
        results = await upload_enhanced_images(config, dry_run=args.dry_run)
        print_results(results, "Enhanced Images")

    if args.all or args.models:
        results = await upload_3d_models(config, dry_run=args.dry_run)
        print_results(results, "3D Models")

    if not any([args.images, args.models, args.all]):
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
