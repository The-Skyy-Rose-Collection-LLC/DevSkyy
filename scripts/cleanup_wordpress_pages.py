#!/usr/bin/env python3
"""WordPress Page Cleanup Script.

Deletes obsolete pages and organizes the page structure for SkyyRose launch.

Usage:
    python scripts/cleanup_wordpress_pages.py --dry-run
    python scripts/cleanup_wordpress_pages.py --execute
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root to path (must be before local imports)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()


# Pages to delete (obsolete/duplicate)
PAGES_TO_DELETE = [
    {"id": 151, "slug": "collections", "reason": "Not needed - categories replace this"},
    {"id": 238, "slug": "signature-3d", "reason": "Duplicate test page"},
    {"id": 236, "slug": "3d-demo-working", "reason": "Development test page"},
]


async def delete_pages(dry_run: bool = True) -> None:
    """Delete obsolete WordPress pages."""
    from wordpress.client import WordPressClient

    print("\n" + "=" * 60)
    print("WordPress Page Cleanup")
    print("=" * 60)

    if dry_run:
        print("\n[DRY RUN] No changes will be made\n")
    else:
        print("\n[EXECUTE] Pages will be permanently deleted\n")

    async with WordPressClient() as client:
        for page in PAGES_TO_DELETE:
            page_id = page["id"]
            slug = page["slug"]
            reason = page["reason"]

            print(f"Page {page_id} ({slug})")
            print(f"  Reason: {reason}")

            if dry_run:
                print(f"  [SKIP] Would delete page {page_id}")
            else:
                try:
                    await client.delete_page(int(page_id), force=True)
                    print(f"  [OK] Deleted page {page_id}")
                except Exception as e:
                    error_msg = str(e)
                    if "rest_post_invalid_id" in error_msg or "404" in error_msg:
                        print(f"  [SKIP] Page {page_id} not found (already deleted?)")
                    else:
                        print(f"  [ERROR] Failed to delete: {e}")

            print()

    print("=" * 60)
    if dry_run:
        print("Dry run complete. Use --execute to delete pages.")
    else:
        print("Cleanup complete.")
    print("=" * 60 + "\n")


def main() -> None:
    """Run WordPress page cleanup CLI."""
    parser = argparse.ArgumentParser(description="WordPress Page Cleanup")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without making them",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete the pages",
    )

    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("Please specify --dry-run or --execute")
        sys.exit(1)

    if args.dry_run and args.execute:
        print("Cannot specify both --dry-run and --execute")
        sys.exit(1)

    # Check WordPress credentials
    wp_url = os.getenv("WORDPRESS_URL")
    wp_user = os.getenv("WORDPRESS_USERNAME")
    wp_pass = os.getenv("WORDPRESS_APP_PASSWORD") or os.getenv("WORDPRESS_PASSWORD")

    if not all([wp_url, wp_user, wp_pass]):
        print("ERROR: Missing WordPress credentials in .env")
        print("Required: WORDPRESS_URL, WORDPRESS_USERNAME, WORDPRESS_APP_PASSWORD")
        sys.exit(1)

    print(f"\nConnecting to: {wp_url}")

    asyncio.run(delete_pages(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
