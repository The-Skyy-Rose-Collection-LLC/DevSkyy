#!/usr/bin/env python3
"""Batch Upload Enhanced Products to WordPress - Token-Efficient."""

import asyncio
import json
import os
import sys
from pathlib import Path

import aiohttp

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# WordPress credentials
WP_URL = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
WP_USERNAME = os.getenv("WORDPRESS_USERNAME", "skyyroseco")
WP_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD")

assert WP_APP_PASSWORD is not None, "WORDPRESS_APP_PASSWORD must be set"


async def upload_media_batch(session, media_files):
    """Upload media files sequentially with ralph-loop retry pattern."""

    results = []

    async def upload_one_with_retry(filepath, max_retries=3):
        """Upload with exponential backoff retry (ralph-loop pattern)."""
        for attempt in range(max_retries):
            try:
                # Read file as binary data
                with open(filepath, "rb") as f:
                    file_data = f.read()

                # WordPress requires binary upload with Content-Disposition header
                headers = {
                    "Content-Disposition": f"attachment; filename={filepath.name}",
                    "Content-Type": "image/jpeg",
                }

                async with session.post(
                    f"{WP_URL}/index.php?rest_route=/wp/v2/media",
                    data=file_data,
                    headers=headers,
                    auth=aiohttp.BasicAuth(WP_USERNAME, WP_APP_PASSWORD),  # type: ignore[arg-type]
                ) as resp:
                    if resp.status == 201:
                        result = await resp.json()
                        print(f"  ✓ {filepath.name}")
                        return {
                            "success": True,
                            "id": result["id"],
                            "title": result["title"]["rendered"],
                            "url": result["source_url"],
                            "file": str(filepath),
                        }
                    elif resp.status == 429:
                        # Rate limited - retry with exponential backoff
                        if attempt < max_retries - 1:
                            wait_time = 2**attempt  # 1s, 2s, 4s
                            print(
                                f"  ⏳ {filepath.name} rate limited, retry {attempt + 1}/{max_retries} in {wait_time}s"
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            error_text = await resp.text()
                            print(f"  ✗ {filepath.name} failed after {max_retries} retries (429)")
                            return {
                                "success": False,
                                "file": str(filepath),
                                "error": f"HTTP 429 after {max_retries} retries: {error_text[:100]}",
                            }
                    else:
                        error_text = await resp.text()
                        print(f"  ✗ {filepath.name} HTTP {resp.status}")
                        return {
                            "success": False,
                            "file": str(filepath),
                            "error": f"HTTP {resp.status}: {error_text[:200]}",
                        }
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    print(
                        f"  ⚠ {filepath.name} error, retry {attempt + 1}/{max_retries} in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    print(f"  ✗ {filepath.name} failed: {e}")
                    return {"success": False, "file": str(filepath), "error": str(e)}

        # Should not reach here
        return {"success": False, "file": str(filepath), "error": "Max retries exceeded"}

    # Upload sequentially to avoid rate limiting
    for filepath in media_files:
        result = await upload_one_with_retry(filepath)
        results.append(result)
        # Add small delay between uploads to be polite
        await asyncio.sleep(0.5)

    return results


async def main():
    # Load enhanced products
    enhanced_dir = project_root / "assets" / "enhanced_products" / "all"
    manifest_path = enhanced_dir / "manifest.json"

    with open(manifest_path) as f:
        products = json.load(f)

    # Get successful enhances only
    media_files = [Path(p["enhanced"]) for p in products if p["success"]]

    print(f"Uploading {len(media_files)} products to WordPress...")

    async with aiohttp.ClientSession() as session:
        results = await upload_media_batch(session, media_files)

    # Save results
    results_path = enhanced_dir / "wordpress_upload_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    # Summary
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful

    print("\n✅ Upload Complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Results: {results_path}")

    if failed > 0:
        print("\n❌ Failed uploads:")
        for r in results:
            if not r["success"]:
                print(f"  {Path(r['file']).name}: {r['error']}")


if __name__ == "__main__":
    asyncio.run(main())
