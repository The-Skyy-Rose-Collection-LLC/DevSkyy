#!/usr/bin/env python3
"""
Retry Fallback JPG Uploads to WordPress

Uploads the remaining fallback JPG images that failed during full catalog upload
due to WordPress.com rate limiting (HTTP 429).

This script:
- Reads existing webp_image_mapping.json to identify missing fallbacks
- Uploads only the fallback JPGs for products that have WebP but no fallback
- Updates webp_image_mapping.json with new fallback IDs
- Implements conservative rate limiting (1.5s delay) to avoid HTTP 429

Usage:
    python scripts/retry_fallback_uploads.py \
        --fallback-dir /tmp/wordpress_integration/webp_optimized/fallback \
        [--batch-size 20] \
        [--delay 1.5]

Requirements:
    - .env file with WORDPRESS_URL, WORDPRESS_USERNAME, WORDPRESS_APP_PASSWORD
    - webp_image_mapping.json with existing WebP uploads
    - Processed fallback JPG directory

Features:
    - Idempotent: skips products that already have both WebP + fallback
    - Conservative rate limiting (default 1.5s delay)
    - Batch processing (default 20 images at a time)
    - Automatic mapping file updates
    - Resume-friendly (can stop/restart safely)
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

WP_URL = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
WP_USERNAME = os.getenv("WORDPRESS_USERNAME")
WP_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD")

# Colors for output
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"


class FallbackRetryUploader:
    """Retry uploader for fallback JPGs that were rate-limited."""

    def __init__(
        self,
        fallback_dir: Path,
        mapping_file: Path,
        batch_size: int = 20,
        delay: float = 1.5,
    ):
        self.fallback_dir = fallback_dir
        self.mapping_file = mapping_file
        self.batch_size = batch_size
        self.delay = delay

        # Load existing mapping
        self.mapping: dict[str, dict[str, Any]] = {}
        if mapping_file.exists():
            with open(mapping_file) as f:
                self.mapping = json.load(f)

        # Track stats
        self.uploaded = 0
        self.skipped = 0
        self.failed = 0

    def identify_missing_fallbacks(self) -> list[str]:
        """Identify products that have WebP but no fallback."""
        # Get all fallback files available
        fallback_files = sorted(self.fallback_dir.glob("*.jpg"))
        all_products = {f.stem for f in fallback_files}

        # Get products already in mapping with fallback
        products_with_fallback = {
            name for name, data in self.mapping.items() if data.get("fallback_id")
        }

        # Missing = all products - products with fallback
        missing = sorted(all_products - products_with_fallback)

        return missing

    async def fetch_wordpress_media(self, session: aiohttp.ClientSession) -> dict[str, int]:
        """Fetch all WebP media from WordPress to find existing upload IDs."""
        endpoint = f"{WP_URL}/wp-json/wp/v2/media"
        auth = aiohttp.BasicAuth(WP_USERNAME, WP_APP_PASSWORD)

        webp_ids: dict[str, int] = {}

        try:
            # Fetch media in pages (100 per page)
            page = 1
            while True:
                params = {"per_page": 100, "page": page, "mime_type": "image/webp"}

                async with session.get(endpoint, params=params, auth=auth) as resp:
                    if resp.status != 200:
                        print(f"  {YELLOW}⚠{NC}  Warning: Failed to fetch media (page {page})")
                        break

                    media = await resp.json()
                    if not media:
                        break

                    # Extract base names and IDs
                    for item in media:
                        # source_url example: "https://skyyrose.co/.../LH_FANNIE_2_main.webp"
                        source_url = item.get("source_url", "")
                        media_id = item.get("id")

                        if source_url.endswith("_main.webp"):
                            # Extract base name (keep _main suffix for consistency)
                            filename = Path(source_url).stem  # "LH_FANNIE_2_main"
                            webp_ids[filename] = media_id

                    page += 1

            print(f"  {GREEN}✓{NC} Found {len(webp_ids)} WebP images in WordPress Media Library")
            return webp_ids

        except Exception as e:
            print(f"  {YELLOW}⚠{NC}  Warning: Failed to fetch WordPress media: {e}")
            return {}

    async def upload_image(
        self, session: aiohttp.ClientSession, filepath: Path
    ) -> dict[str, Any] | None:
        """Upload single image to WordPress Media Library."""
        endpoint = f"{WP_URL}/wp-json/wp/v2/media"

        # WordPress REST API media upload format (official docs)
        # Only Content-Disposition header required - WordPress detects MIME type automatically
        headers = {
            "Content-Disposition": f'attachment; filename="{filepath.name}"',
        }

        auth = aiohttp.BasicAuth(WP_USERNAME, WP_APP_PASSWORD)

        try:
            with open(filepath, "rb") as f:
                data = f.read()

            async with session.post(endpoint, headers=headers, data=data, auth=auth) as resp:
                # Check for HTML response (authentication redirect)
                content_type = resp.headers.get("Content-Type", "")

                if resp.status == 201:
                    result = await resp.json()
                    print(f"  {GREEN}✓{NC} Uploaded: {filepath.name} (ID: {result['id']})")
                    return result
                elif resp.status == 429:
                    # Rate limited - return None to signal retry later
                    print(
                        f"  {YELLOW}⏸{NC}  Rate limited: {filepath.name} - will retry after cooldown"
                    )
                    return None
                elif "text/html" in content_type:
                    # Got HTML instead of JSON - likely authentication issue
                    print(
                        f"  {RED}✗{NC} Failed: {filepath.name} - Authentication error (got HTML, expected JSON)"
                    )
                    print(f"    Status: {resp.status}")
                    print("    Hint: Verify WordPress Application Password is correct")
                    print("    Run: python scripts/diagnose_wordpress_api.py")
                    return None
                else:
                    text = await resp.text()
                    print(f"  {RED}✗{NC} Failed: {filepath.name} - HTTP {resp.status}")
                    print(f"    Response: {text[:200]}")
                    return None

        except Exception as e:
            print(f"  {RED}✗{NC} Error: {filepath.name} - {e}")
            return None

    async def upload_batch(self, base_names: list[str], webp_ids: dict[str, int]) -> None:
        """Upload a batch of fallback JPGs."""
        async with aiohttp.ClientSession() as session:
            for i, base_name in enumerate(base_names):
                fallback_path = self.fallback_dir / f"{base_name}.jpg"

                print(f"\n[{i + 1}/{len(base_names)}] Processing: {base_name}")

                # Upload fallback JPG
                result = await self.upload_image(session, fallback_path)

                if result:
                    # Get WebP ID from WordPress query (if available)
                    webp_id = webp_ids.get(base_name)
                    webp_url = None

                    # If we have the webp_id, get the URL too
                    if webp_id:
                        # Construct WebP URL (assuming WordPress naming convention)
                        webp_url = f"{WP_URL}/wp-content/uploads/2026/01/{base_name}_main.webp"

                    # Create or update mapping entry
                    if base_name not in self.mapping:
                        self.mapping[base_name] = {}

                    self.mapping[base_name]["fallback_id"] = result["id"]
                    self.mapping[base_name]["fallback_url"] = result["source_url"]

                    if webp_id:
                        self.mapping[base_name]["webp_id"] = webp_id
                        self.mapping[base_name]["webp_url"] = webp_url

                    self.uploaded += 1

                    # Save mapping after each successful upload (resume-friendly)
                    with open(self.mapping_file, "w") as f:
                        json.dump(self.mapping, f, indent=2)

                elif result is None:
                    # Rate limited or other error
                    self.failed += 1

                # Rate limiting delay
                if i < len(base_names) - 1:
                    await asyncio.sleep(self.delay)

    async def run(self) -> None:
        """Run the retry upload process."""
        print(f"\n{BLUE}{'=' * 60}{NC}")
        print(f"{BLUE}WordPress Fallback JPG Retry Upload{NC}")
        print(f"{BLUE}{'=' * 60}{NC}")

        # Fetch existing WebP media from WordPress
        print(f"\n{BLUE}Step 1: Fetching WordPress Media Library...{NC}")
        async with aiohttp.ClientSession() as session:
            webp_ids = await self.fetch_wordpress_media(session)

        if not webp_ids:
            print(
                f"\n{YELLOW}⚠  Warning: Could not fetch WordPress media. Continuing without WebP IDs.{NC}"
            )
            print(
                "   (Mapping will be created with fallback IDs only, WebP IDs can be added manually)"
            )

        # Identify missing fallbacks
        print(f"\n{BLUE}Step 2: Identifying missing fallbacks...{NC}")
        missing = self.identify_missing_fallbacks()

        print(f"\nFallback directory: {self.fallback_dir}")
        print(f"Mapping file:       {self.mapping_file}")
        print(f"WebP found in WP:   {len(webp_ids)}")
        print(f"Missing fallbacks:  {len(missing)}")
        print(f"Batch size:         {self.batch_size}")
        print(f"Delay between:      {self.delay}s")
        print(f"WordPress URL:      {WP_URL}")
        print(f"{BLUE}{'=' * 60}{NC}\n")

        if not missing:
            print(f"{GREEN}✓ All products already have fallback JPGs uploaded!{NC}")
            return

        print(f"{BLUE}Step 3: Uploading fallback JPGs...{NC}\n")

        # Process in batches
        for batch_num in range(0, len(missing), self.batch_size):
            batch = missing[batch_num : batch_num + self.batch_size]
            batch_index = batch_num // self.batch_size + 1
            total_batches = (len(missing) + self.batch_size - 1) // self.batch_size

            print(
                f"\n{BLUE}═══ Batch {batch_index}/{total_batches} ({len(batch)} images) ═══{NC}\n"
            )

            await self.upload_batch(batch, webp_ids)

            # Longer delay between batches to avoid rate limit
            if batch_num + self.batch_size < len(missing):
                print(f"\n{YELLOW}⏸  Waiting 5s before next batch...{NC}")
                await asyncio.sleep(5)

        # Summary
        print(f"\n{BLUE}{'=' * 60}{NC}")
        print(f"{BLUE}Upload Summary{NC}")
        print(f"{BLUE}{'=' * 60}{NC}")
        print(f"Fallback uploaded:  {self.uploaded}")
        print(f"Failed/Rate limit:  {self.failed}")
        print(f"Total processed:    {self.uploaded + self.failed}")

        # Updated mapping stats
        complete_pairs = sum(
            1 for data in self.mapping.values() if data.get("webp_id") and data.get("fallback_id")
        )
        print(f"\nComplete pairs:     {complete_pairs}/{len(self.mapping)}")

        print(f"\n{GREEN}✓ Mapping updated: {self.mapping_file}{NC}")
        print(f"\n{BLUE}{'=' * 60}{NC}\n")


async def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Retry fallback JPG uploads to WordPress")
    parser.add_argument(
        "--fallback-dir",
        type=Path,
        default=Path("/tmp/wordpress_integration/webp_optimized/fallback"),
        help="Directory containing fallback JPG files",
    )
    parser.add_argument(
        "--mapping-file",
        type=Path,
        default=Path("wordpress/webp_image_mapping.json"),
        help="WebP image mapping file",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Number of images to upload per batch",
    )
    parser.add_argument("--delay", type=float, default=1.5, help="Delay between uploads (seconds)")

    args = parser.parse_args()

    # Validate credentials
    if not WP_USERNAME or not WP_APP_PASSWORD:
        print(f"{RED}Error: WordPress credentials not configured{NC}", file=sys.stderr)
        print(
            "\nAdd to .env file:",
            """
WORDPRESS_URL=https://skyyrose.co
WORDPRESS_USERNAME=your_username
WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx  # pragma: allowlist secret
""",
        )
        print(
            "\nGenerate Application Password:",
            """
1. Log in to WordPress Admin
2. Users → Profile → Application Passwords
3. Name: "DevSkyy Fallback Upload Script"
4. Generate and copy password
""",
        )
        sys.exit(1)

    # Validate directories
    if not args.fallback_dir.exists():
        print(
            f"{RED}Error: Fallback directory not found: {args.fallback_dir}{NC}",
            file=sys.stderr,
        )
        sys.exit(1)

    if not args.mapping_file.exists():
        print(
            f"{RED}Error: Mapping file not found: {args.mapping_file}{NC}",
            file=sys.stderr,
        )
        print(
            "\nRun full upload first: python scripts/integrate_webp_wordpress.py",
            file=sys.stderr,
        )
        sys.exit(1)

    # Run uploader
    uploader = FallbackRetryUploader(
        args.fallback_dir, args.mapping_file, args.batch_size, args.delay
    )
    await uploader.run()


if __name__ == "__main__":
    asyncio.run(main())
