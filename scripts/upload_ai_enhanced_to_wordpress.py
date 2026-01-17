#!/usr/bin/env python3
"""
Upload AI-Enhanced Images to WordPress & WooCommerce.

Uploads 252 AI-enhanced product images and updates WooCommerce galleries.

Usage:
    python3 scripts/upload_ai_enhanced_to_wordpress.py
"""

import asyncio
import base64
import json
import os
import sys
from pathlib import Path

import aiohttp

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

# Configuration
WORDPRESS_URL = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
WC_KEY = os.getenv("WOOCOMMERCE_KEY")
WC_SECRET = os.getenv("WOOCOMMERCE_SECRET")
WP_USER = os.getenv("WORDPRESS_USERNAME", "skyyroseco")
WP_PASS = os.getenv("WORDPRESS_APP_PASSWORD")

MANIFEST_PATH = Path("assets/ai-enhanced-images/AI_ENHANCEMENT_MANIFEST.json")
UPLOAD_RESULTS_PATH = Path("assets/ai-enhanced-images/WORDPRESS_UPLOAD_RESULTS.json")


async def upload_image(
    session: aiohttp.ClientSession,
    image_path: Path,
    title: str,
) -> dict:
    """Upload single image to WordPress media library."""
    endpoint = f"{WORDPRESS_URL}/wp-json/wp/v2/media"

    # Basic auth
    auth_string = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_string}",
        "Content-Disposition": f'attachment; filename="{image_path.name}"',
    }

    try:
        with open(image_path, "rb") as f:
            content_type = (
                "image/jpeg" if image_path.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
            )
            data = aiohttp.FormData()
            data.add_field(
                "file",
                f,
                filename=image_path.name,
                content_type=content_type,
            )

            async with session.post(
                endpoint,
                data=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status in (200, 201):
                    result = await resp.json()
                    return {
                        "success": True,
                        "id": result.get("id"),
                        "url": result.get("source_url"),
                        "title": title,
                    }
                else:
                    error = await resp.text()
                    return {
                        "success": False,
                        "error": f"{resp.status}: {error[:200]}",
                        "title": title,
                    }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "title": title,
        }


async def upload_collection(
    session: aiohttp.ClientSession,
    collection_name: str,
    items: list,
    semaphore: asyncio.Semaphore,
) -> list:
    """Upload all images for a collection."""
    results = []

    for idx, item in enumerate(items):
        if not item.get("success"):
            continue

        sku = item["sku"]
        outputs = item.get("outputs", {})

        # Upload main image (highest priority for product display)
        main_path = outputs.get("main")
        if main_path and Path(main_path).exists():
            async with semaphore:
                result = await upload_image(
                    session,
                    Path(main_path),
                    f"{sku} - Main",
                )
                result["sku"] = sku
                result["type"] = "main"
                result["collection"] = collection_name
                results.append(result)

                status = "✓" if result["success"] else "✗"
                print(f"  [{idx + 1}/{len(items)}] {status} {sku}")

        # Small delay to avoid overwhelming the server
        await asyncio.sleep(0.2)

    return results


async def main():
    """Main upload function."""
    print("=" * 70)
    print("Upload AI-Enhanced Images to WordPress")
    print("=" * 70)

    # Validate credentials
    if not all([WC_KEY, WC_SECRET, WP_PASS]):
        print("\n❌ Missing credentials. Check .env for:")
        print("   WOOCOMMERCE_KEY, WOOCOMMERCE_SECRET, WORDPRESS_APP_PASSWORD")
        return 1

    # Load manifest
    if not MANIFEST_PATH.exists():
        print(f"\n❌ Manifest not found: {MANIFEST_PATH}")
        return 1

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    print("\n📊 Manifest loaded:")
    print(f"   WordPress: {WORDPRESS_URL}")
    print(f"   Collections: {len(manifest['collections'])}")

    total_items = sum(c["total"] for c in manifest["collections"].values())
    print(f"   Total images: {total_items}")

    # Setup async session
    connector = aiohttp.TCPConnector(limit=5)  # Limit concurrent connections
    semaphore = asyncio.Semaphore(3)  # Max 3 concurrent uploads

    all_results = []

    async with aiohttp.ClientSession(connector=connector) as session:
        for collection_name, collection_data in manifest["collections"].items():
            print(
                f"\n🗂️  Uploading {collection_name.upper()} ({collection_data['total']} images)..."
            )

            results = await upload_collection(
                session,
                collection_name,
                collection_data["items"],
                semaphore,
            )
            all_results.extend(results)

    # Summary
    success_count = sum(1 for r in all_results if r.get("success"))
    failed_count = len(all_results) - success_count

    print(f"\n{'=' * 70}")
    print("✅ Upload Complete!")
    print(f"{'=' * 70}")
    print("\n📊 Results:")
    print(f"   Success: {success_count}")
    print(f"   Failed: {failed_count}")
    print(f"   Total: {len(all_results)}")

    # Save results
    upload_results = {
        "wordpress_url": WORDPRESS_URL,
        "total_uploaded": success_count,
        "total_failed": failed_count,
        "results": all_results,
    }

    with open(UPLOAD_RESULTS_PATH, "w") as f:
        json.dump(upload_results, f, indent=2)

    print(f"\n📁 Results saved to: {UPLOAD_RESULTS_PATH}")

    # Show any failures
    if failed_count > 0:
        print("\n⚠️  Failed uploads:")
        for r in all_results:
            if not r.get("success"):
                print(f"   - {r.get('sku')}: {r.get('error', 'Unknown')[:50]}")

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
