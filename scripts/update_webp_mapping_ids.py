#!/usr/bin/env python3
"""
Update WebP Image Mapping with WordPress Media IDs

Queries WordPress Media Library to fetch WebP and JPG attachment IDs
and updates the webp_image_mapping.json file with complete information.

Usage:
    python scripts/update_webp_mapping_ids.py

This script:
- Fetches all WebP and JPG media from WordPress
- Updates existing mapping entries with missing webp_id/fallback_id fields
- Adds complete URL information for all entries
"""

import asyncio
import json
import os
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

WP_URL = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
WP_USERNAME = os.getenv("WORDPRESS_USERNAME")
WP_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD")

# Colors
GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
YELLOW = "\033[1;33m"
NC = "\033[0m"


async def fetch_wordpress_media(
    session: aiohttp.ClientSession,
) -> tuple[dict[str, dict], dict[str, dict]]:
    """Fetch all WebP and JPG media from WordPress."""
    endpoint = f"{WP_URL}/wp-json/wp/v2/media"
    auth = aiohttp.BasicAuth(WP_USERNAME, WP_APP_PASSWORD)

    webp_items: dict[str, dict] = {}
    jpg_items: dict[str, dict] = {}

    try:
        page = 1
        while True:
            params = {"per_page": 100, "page": page}

            async with session.get(endpoint, params=params, auth=auth) as resp:
                if resp.status != 200:
                    break

                media = await resp.json()
                if not media:
                    break

                for item in media:
                    source_url = item.get("source_url", "")

                    if source_url.endswith("_main.webp"):
                        filename = Path(source_url).stem
                        webp_items[filename] = {
                            "id": item.get("id"),
                            "url": source_url,
                        }
                    elif source_url.endswith("_main.jpg"):
                        filename = Path(source_url).stem
                        jpg_items[filename] = {
                            "id": item.get("id"),
                            "url": source_url,
                        }

                page += 1

        print(f"  {GREEN}✓{NC} Found {len(webp_items)} WebP + {len(jpg_items)} JPG images")
        return webp_items, jpg_items

    except Exception as e:
        print(f"  {YELLOW}⚠{NC}  Warning: Failed to fetch media: {e}")
        return {}, {}


async def main():
    """Update mapping file with WordPress media IDs."""
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}Update WebP Image Mapping with WordPress IDs{NC}")
    print(f"{BLUE}{'=' * 60}{NC}\n")

    mapping_file = Path("wordpress/webp_image_mapping.json")

    # Load existing mapping
    with open(mapping_file) as f:
        mapping = json.load(f)

    print(f"Current mapping: {len(mapping)} entries")

    # Fetch WordPress media
    print(f"\n{BLUE}Fetching WordPress Media Library...{NC}")
    async with aiohttp.ClientSession() as session:
        webp_media, jpg_media = await fetch_wordpress_media(session)

    # Update mapping
    print(f"\n{BLUE}Updating mapping entries...{NC}")
    updated = 0

    for base_name in mapping:
        # Update WebP info
        if base_name in webp_media:
            mapping[base_name]["webp_id"] = webp_media[base_name]["id"]
            mapping[base_name]["webp_url"] = webp_media[base_name]["url"]
            updated += 1

        # Update fallback info
        if base_name in jpg_media:
            mapping[base_name]["fallback_id"] = jpg_media[base_name]["id"]
            mapping[base_name]["fallback_url"] = jpg_media[base_name]["url"]
            updated += 1

    # Count complete pairs
    complete = sum(
        1 for data in mapping.values() if data.get("webp_id") and data.get("fallback_id")
    )

    # Save updated mapping
    with open(mapping_file, "w") as f:
        json.dump(mapping, f, indent=2)

    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}Update Summary{NC}")
    print(f"{BLUE}{'=' * 60}{NC}")
    print(f"Total entries:      {len(mapping)}")
    print(f"Complete pairs:     {complete}")
    print(f"Fields updated:     {updated}")
    print(f"\n{GREEN}✓ Mapping updated: {mapping_file}{NC}")
    print(f"{BLUE}{'=' * 60}{NC}\n")


if __name__ == "__main__":
    asyncio.run(main())
