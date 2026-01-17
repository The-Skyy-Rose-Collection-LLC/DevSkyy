#!/usr/bin/env python3
"""
WordPress Page Cleanup & Production Prep
==========================================

Deletes all existing WordPress pages and prepares scaffolding for
production pages (home, shop, collection experiences, etc).

Usage:
    python scripts/wordpress_cleanup.py [--list-only] [--dry-run]

Options:
    --list-only    Show pages without deleting
    --dry-run      Show what would be deleted without actually deleting
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wordpress.client import WordPressClient, WordPressConfig


async def list_pages(client: WordPressClient) -> list[dict]:
    """Fetch all pages from WordPress."""
    pages = []
    per_page = 100
    page_num = 1

    while True:
        result = await client.get_pages(per_page=per_page, page=page_num)
        if not result:
            break
        pages.extend(result)
        if len(result) < per_page:
            break
        page_num += 1

    return pages


async def delete_page(client: WordPressClient, page_id: int, title: str, dry_run: bool = False):
    """Delete a page with logging."""
    if dry_run:
        print(f"  [DRY-RUN] Would delete: {title} (ID: {page_id})")
        return

    try:
        await client.delete_page(page_id, force=True)
        print(f"  ✓ Deleted: {title} (ID: {page_id})")
    except Exception as e:
        print(f"  ✗ Error deleting {title}: {e}")


async def main():
    parser = argparse.ArgumentParser(
        description="Clean up WordPress pages and prepare for production"
    )
    parser.add_argument("--list-only", action="store_true", help="List pages without deleting")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted")
    args = parser.parse_args()

    config = WordPressConfig.from_env()
    async with WordPressClient(config) as client:
        print(f"\n📋 Fetching pages from {config.site_url}...\n")
        pages = await list_pages(client)

        if not pages:
            print("✓ No pages found. WordPress is clean.\n")
            return

        print(f"Found {len(pages)} page(s):\n")
        for page in pages:
            status = "📌 PUBLISH" if page.get("status") == "publish" else "📝 DRAFT"
            print(f"  {status} | {page['title']['rendered']} (ID: {page['id']})")

        if args.list_only:
            print("\n(Use without --list-only to delete these pages)\n")
            return

        # Confirm deletion unless dry-run
        if not args.dry_run:
            print(f"\n⚠️  About to delete {len(pages)} page(s). Type 'DELETE' to confirm: ", end="")
            confirm = input().strip()
            if confirm != "DELETE":
                print("Cancelled.\n")
                return

        print("\nDeleting pages...\n")
        for page in pages:
            await delete_page(client, page["id"], page["title"]["rendered"], dry_run=args.dry_run)

        mode = "DRY-RUN" if args.dry_run else "COMPLETED"
        print(f"\n✓ {mode}: WordPress cleanup finished.\n")

        print("📝 Production Pages Ready to Create:")
        print("  - / (Home)")
        print("  - /shop (Product Archive)")
        print("  - /experiences/signature (Signature Collection)")
        print("  - /experiences/black-rose (Black Rose Collection)")
        print("  - /experiences/love-hurts (Love Hurts Collection)")
        print("  - /about (About SkyyRose)")
        print("  - /contact (Contact)")
        print()


if __name__ == "__main__":
    asyncio.run(main())
