#!/usr/bin/env python3
"""
Upload enhanced clothing images to WordPress media library.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import aiohttp

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()


async def upload_image_to_wordpress(
    session: aiohttp.ClientSession,
    image_path: Path,
    title: str,
    wordpress_url: str,
) -> dict:
    """Upload a single image to WordPress."""
    endpoint = f"{wordpress_url}/wp-json/wp/v2/media"

    with open(image_path, "rb") as f:
        data = aiohttp.FormData()
        data.add_field("file", f, filename=image_path.name, content_type="image/png")

        async with session.post(
            endpoint,
            data=data,
            headers={"Content-Disposition": f'attachment; filename="{image_path.name}"'},
            timeout=aiohttp.ClientTimeout(total=60),
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
                    "error": f"{resp.status}: {error[:100]}",
                    "title": title,
                }


async def main():
    # Config - use production URL
    wordpress_url = "https://skyyrose.co"
    wc_key = os.getenv("WOOCOMMERCE_KEY")
    wc_secret = os.getenv("WOOCOMMERCE_SECRET")

    if not wc_key or not wc_secret:
        print("ERROR: WOOCOMMERCE_KEY and WOOCOMMERCE_SECRET required")
        sys.exit(1)

    # Get enhanced images
    images_dir = Path(__file__).parent.parent / "assets/visual-generated/enhanced_clothing"
    manifest_path = images_dir / "MANIFEST.json"

    if not manifest_path.exists():
        print("ERROR: No manifest found. Run batch_enhance_clothing.py first.")
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)

    print(f"WordPress: {wordpress_url}")
    print(f"Images to upload: {len(manifest)}")
    print("=" * 50)

    # Auth
    auth = aiohttp.BasicAuth(wc_key, wc_secret)

    async with aiohttp.ClientSession(auth=auth) as session:
        results = []

        for item in manifest:
            image_path = Path(item["path"])
            if not image_path.exists():
                print(f"✗ Missing: {item['name']}")
                continue

            result = await upload_image_to_wordpress(
                session,
                image_path,
                item["name"],
                wordpress_url,
            )

            if result["success"]:
                print(f"✓ {item['name'][:40]}: ID {result['id']}")
            else:
                print(f"✗ {item['name'][:40]}: {result['error']}")

            results.append(result)

            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)

        # Summary
        successful = sum(1 for r in results if r.get("success"))
        print("=" * 50)
        print(f"Uploaded: {successful}/{len(results)}")

        # Save results
        results_path = images_dir / "WORDPRESS_UPLOAD_RESULTS.json"
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results: {results_path}")


if __name__ == "__main__":
    asyncio.run(main())
