#!/usr/bin/env python3
"""
Upload AI Model Images to WordPress Media Library.

Uploads 26 AI-generated model images wearing exact SkyyRose merchandise.
Uses ralph-loop retry pattern with sequential uploads to avoid rate limiting.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import aiohttp

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file
from dotenv import load_dotenv  # noqa: E402

load_dotenv(project_root / ".env")

# WordPress credentials
WP_URL = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
WP_USERNAME = os.getenv("WORDPRESS_USERNAME", "skyyroseco")
WP_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD")

if not WP_APP_PASSWORD:
    print("❌ WORDPRESS_APP_PASSWORD not set in .env")
    sys.exit(1)

assert WP_APP_PASSWORD is not None

# Directories
AI_MODELS_DIR = project_root / "assets" / "ai-models-with-products"


async def upload_one_with_retry(
    session: aiohttp.ClientSession,
    filepath: Path,
    max_retries: int = 3,
) -> dict:
    """Upload AI model image with ralph-loop retry pattern."""

    for attempt in range(max_retries):
        try:
            # Read file as binary
            with open(filepath, "rb") as f:
                file_data = f.read()

            # WordPress binary upload
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

                    # Update media metadata
                    product_name = filepath.stem.replace("model_enhanced_", "").replace("_", " ")
                    update_data = {
                        "alt_text": f"AI model wearing {product_name}",
                        "description": "AI-generated fashion model wearing exact SkyyRose product",
                        "caption": f"Model wearing {product_name}",
                    }

                    async with session.post(
                        f"{WP_URL}/index.php?rest_route=/wp/v2/media/{result['id']}",
                        json=update_data,
                        auth=aiohttp.BasicAuth(WP_USERNAME, WP_APP_PASSWORD),  # type: ignore[arg-type]
                    ) as update_resp:
                        if update_resp.status == 200:
                            print(f"  ✓ {filepath.name} (ID: {result['id']})")
                        else:
                            print(f"  ⚠ {filepath.name} uploaded but metadata update failed")

                    return {
                        "success": True,
                        "id": result["id"],
                        "url": result["source_url"],
                        "file": str(filepath),
                    }

                elif resp.status == 429:
                    # Rate limited - retry with exponential backoff (ralph-loop)
                    if attempt < max_retries - 1:
                        wait_time = 2**attempt  # 1s, 2s, 4s
                        print(
                            f"  ⏳ {filepath.name} rate limited, retry {attempt + 1}/{max_retries} in {wait_time}s"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print(f"  ✗ {filepath.name} failed after {max_retries} retries (429)")
                        return {
                            "success": False,
                            "file": str(filepath),
                            "error": f"HTTP 429 after {max_retries} retries",
                        }
                else:
                    print(f"  ✗ {filepath.name} HTTP {resp.status}")
                    return {"success": False, "file": str(filepath), "error": f"HTTP {resp.status}"}

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2**attempt  # Ralph-loop: 1s, 2s, 4s
                print(
                    f"  ⚠ {filepath.name} error, retry {attempt + 1}/{max_retries} in {wait_time}s"
                )
                await asyncio.sleep(wait_time)
                continue
            else:
                print(f"  ✗ {filepath.name} failed: {e}")
                return {"success": False, "file": str(filepath), "error": str(e)}

    return {"success": False, "file": str(filepath), "error": "Max retries exceeded"}


async def main():
    """Upload all AI model images to WordPress."""

    print("=== AI Model Images Upload to WordPress ===\n")

    # Validate directory
    if not AI_MODELS_DIR.exists():
        print(f"❌ AI models directory not found: {AI_MODELS_DIR}")
        return 1

    # Get all AI model images
    model_images = list(AI_MODELS_DIR.glob("*.jpg"))

    if not model_images:
        print(f"❌ No AI model images found in: {AI_MODELS_DIR}")
        return 1

    print(f"Found {len(model_images)} AI model images\n")

    # Upload sequentially to avoid rate limiting
    results = []

    async with aiohttp.ClientSession() as session:
        for idx, filepath in enumerate(model_images, 1):
            print(f"[{idx}/{len(model_images)}] Uploading: {filepath.name}")

            result = await upload_one_with_retry(session, filepath)
            results.append(result)

            # Polite delay between uploads
            if idx < len(model_images):
                await asyncio.sleep(0.5)

    # Save results
    results_path = AI_MODELS_DIR / "wordpress_upload_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    # Summary
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful

    print(f"\n{'=' * 60}")
    print("✅ Upload Complete!")
    print(f"{'=' * 60}")
    print(f"Successful: {successful}/{len(results)}")
    print(f"Failed: {failed}")
    print(f"Results saved: {results_path}")

    if failed > 0:
        print("\n❌ Failed uploads:")
        for r in results:
            if not r["success"]:
                print(f"  {Path(r['file']).name}: {r.get('error', 'Unknown error')}")

    print("\n📋 Next Steps:")
    print("  1. Review uploaded images in WordPress Media Library")
    print("  2. Use AI model images in product marketing and ads")
    print("  3. Embed in email campaigns and social media")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
