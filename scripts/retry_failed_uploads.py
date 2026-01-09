#!/usr/bin/env python3
"""
Retry Failed WordPress Uploads.

Retries only the files that failed during previous upload sessions.
Uses conservative delays (2s between uploads) to avoid rate limiting.
"""

import asyncio
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

# Failed files from previous attempts
FAILED_2D_25D_FILES = [
    "assets/2d-25d-assets/_Signature Collection_ Crop Hoodie back_depth.jpg",
    "assets/2d-25d-assets/_Signature Collection_ Crop Hoodie back_shadow.jpg",
    "assets/2d-25d-assets/Stay Golden Tee_shadow.jpg",
    "assets/2d-25d-assets/Stay Golden Tee_parallax.png",
    "assets/2d-25d-assets/_Signature Collection_ Cotton Candy Tee_shadow.jpg",
    "assets/2d-25d-assets/_Signature Collection_ Hoodie_shadow.jpg",
    "assets/2d-25d-assets/_Signature Collection_ Original Label Tee (Orchid)_depth.jpg",
    "assets/2d-25d-assets/Signature Collection Red Rose Beanie_depth.jpg",
    "assets/2d-25d-assets/_Signature Collection_ Cotton Candy Shorts_shadow.jpg",
    "assets/2d-25d-assets/_Signature Collection_ Cotton Candy Shorts_parallax.png",
]

FAILED_AI_MODEL_FILES = [
    "assets/ai-models-with-products/model_enhanced_The Yay Bridge Set.jpg",
]


async def upload_one_with_retry(
    session: aiohttp.ClientSession,
    filepath: Path,
    max_retries: int = 5,  # More retries for failed files
) -> dict:
    """Upload file with conservative ralph-loop retry pattern."""

    for attempt in range(max_retries):
        try:
            # Read file as binary
            with open(filepath, "rb") as f:
                file_data = f.read()

            # Determine MIME type
            mime_type = "image/png" if filepath.suffix == ".png" else "image/jpeg"

            # WordPress binary upload
            headers = {
                "Content-Disposition": f"attachment; filename={filepath.name}",
                "Content-Type": mime_type,
            }

            async with session.post(
                f"{WP_URL}/index.php?rest_route=/wp/v2/media",
                data=file_data,
                headers=headers,
                auth=aiohttp.BasicAuth(WP_USERNAME, WP_APP_PASSWORD),  # type: ignore[arg-type]
            ) as resp:
                if resp.status == 201:
                    result = await resp.json()

                    # Update metadata
                    product_name = filepath.stem.replace("model_enhanced_", "").replace("_", " ")
                    update_data = {
                        "alt_text": f"SkyyRose {product_name}",
                        "description": "SkyyRose premium visualization",
                    }

                    async with session.post(
                        f"{WP_URL}/index.php?rest_route=/wp/v2/media/{result['id']}",
                        json=update_data,
                        auth=aiohttp.BasicAuth(WP_USERNAME, WP_APP_PASSWORD),  # type: ignore[arg-type]
                    ) as update_resp:
                        if update_resp.status == 200:
                            print(f"  ✅ {filepath.name} (ID: {result['id']})")
                        else:
                            print(f"  ✅ {filepath.name} uploaded (metadata update failed)")

                    return {
                        "success": True,
                        "id": result["id"],
                        "url": result["source_url"],
                        "file": str(filepath),
                    }

                elif resp.status == 429:
                    # Rate limited - more aggressive backoff
                    if attempt < max_retries - 1:
                        wait_time = (2**attempt) * 2  # 2s, 4s, 8s, 16s, 32s
                        print(
                            f"  ⏳ {filepath.name} rate limited, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print(
                            f"  ❌ {filepath.name} still rate limited after {max_retries} attempts"
                        )
                        return {
                            "success": False,
                            "file": str(filepath),
                            "error": f"HTTP 429 after {max_retries} retries",
                        }
                else:
                    print(f"  ❌ {filepath.name} HTTP {resp.status}")
                    return {"success": False, "file": str(filepath), "error": f"HTTP {resp.status}"}

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (2**attempt) * 2  # Conservative backoff
                print(f"  ⚠️ {filepath.name} error, waiting {wait_time}s: {str(e)[:50]}")
                await asyncio.sleep(wait_time)
                continue
            else:
                print(f"  ❌ {filepath.name} failed: {e}")
                return {"success": False, "file": str(filepath), "error": str(e)}

    return {"success": False, "file": str(filepath), "error": "Max retries exceeded"}


async def main():
    """Retry all failed uploads with conservative delays."""

    print("=== Retrying Failed WordPress Uploads ===\n")

    # Combine all failed files
    all_failed_files = FAILED_2D_25D_FILES + FAILED_AI_MODEL_FILES

    # Convert to Path objects and verify they exist
    failed_paths = []
    for file_path in all_failed_files:
        full_path = project_root / file_path
        if full_path.exists():
            failed_paths.append(full_path)
        else:
            print(f"⚠️  File not found (skipping): {file_path}")

    if not failed_paths:
        print("❌ No failed files found to retry")
        return 1

    print(f"Found {len(failed_paths)} files to retry\n")
    print("Using conservative delays: 2s between uploads\n")

    # Upload sequentially with long delays
    results = []

    async with aiohttp.ClientSession() as session:
        for idx, filepath in enumerate(failed_paths, 1):
            print(f"[{idx}/{len(failed_paths)}] Retrying: {filepath.name}")

            result = await upload_one_with_retry(session, filepath, max_retries=5)
            results.append(result)

            # Long delay between uploads (2 seconds)
            if idx < len(failed_paths):
                await asyncio.sleep(2)

    # Summary
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful

    print(f"\n{'=' * 60}")
    print("✅ Retry Complete!")
    print(f"{'=' * 60}")
    print(f"Successful: {successful}/{len(results)}")
    print(f"Still Failed: {failed}")

    if failed > 0:
        print("\n❌ Still failing after retry:")
        for r in results:
            if not r["success"]:
                print(f"  {Path(r['file']).name}: {r.get('error', 'Unknown error')}")
        print("\n💡 Tip: Wait a few minutes and run this script again if rate limited")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
