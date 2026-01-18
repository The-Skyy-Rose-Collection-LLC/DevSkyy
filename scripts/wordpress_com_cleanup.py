#!/usr/bin/env python3
"""
WordPress Page Cleanup via REST API

Deletes/renames WordPress pages and prepares for production.

Requirements in .env:
  - WORDPRESS_URL (e.g., https://skyyrose.co)
  - WORDPRESS_USERNAME (e.g., skyyroseco)
  - WORDPRESS_APP_PASSWORD (Application password from WP Admin)

Usage:
    python scripts/wordpress_com_cleanup.py [--list-only] [--dry-run]
"""

import argparse
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests not installed. Try: python -m pip install requests")
    sys.exit(1)


class WordPressRESTClient:
    """WordPress REST API v2 client using Application Password."""

    def __init__(self, site_url: str, username: str, app_password: str):
        """Initialize WordPress REST API client.

        Args:
            site_url: Full site URL (e.g., https://skyyrose.co)
            username: WordPress username
            app_password: Application password from WP Admin
        """
        self.site_url = site_url.rstrip("/")
        self.api_base = f"{self.site_url}/wp-json/wp/v2"
        self.auth = (username, app_password)

    def get_pages(self) -> list[dict]:
        """Fetch all pages from WordPress."""
        pages = []
        per_page = 100
        page_num = 1

        while True:
            url = f"{self.api_base}/pages"
            params = {
                "per_page": per_page,
                "page": page_num,
                "status": "publish,draft,private",
            }

            try:
                response = requests.get(url, auth=self.auth, params=params, timeout=30)
                response.raise_for_status()
                result = response.json()

                if not result:
                    break

                pages.extend(result)
                if len(result) < per_page:
                    break

                page_num += 1
            except requests.exceptions.RequestException as e:
                print(f"Error fetching pages: {e}")
                if hasattr(e, "response") and e.response is not None:
                    print(f"Response: {e.response.text[:500]}")
                break

        return pages

    def delete_page(self, page_id: int, title: str, dry_run: bool = False) -> bool:
        """Delete a page from WordPress (move to trash).

        Args:
            page_id: WordPress page ID
            title: Page title (for logging)
            dry_run: If True, don't actually delete

        Returns:
            True if successful or dry-run
        """
        if dry_run:
            print(f"  [DRY-RUN] Would delete: {title} (ID: {page_id})")
            return True

        url = f"{self.api_base}/pages/{page_id}"

        try:
            # force=true permanently deletes, omit for trash
            response = requests.delete(url, auth=self.auth, timeout=30)
            if response.status_code in (200, 204):
                print(f"  ✓ Deleted: {title} (ID: {page_id})")
                return True
            else:
                error_msg = response.json().get("message", response.text[:200])
                print(f"  ✗ Error deleting {title}: {error_msg}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error deleting {title}: {e}")
            return False

    def update_page_slug(
        self, page_id: int, new_slug: str, title: str, dry_run: bool = False
    ) -> bool:
        """Update a page's slug.

        Args:
            page_id: WordPress page ID
            new_slug: New URL slug
            title: Page title (for logging)
            dry_run: If True, don't actually update

        Returns:
            True if successful or dry-run
        """
        if dry_run:
            print(f"  [DRY-RUN] Would rename: {title} → /{new_slug}/")
            return True

        url = f"{self.api_base}/pages/{page_id}"
        data = {"slug": new_slug}

        try:
            response = requests.post(url, auth=self.auth, json=data, timeout=30)
            if response.status_code == 200:
                print(f"  ✓ Renamed: {title} → /{new_slug}/")
                return True
            else:
                error_msg = response.json().get("message", response.text[:200])
                print(f"  ✗ Error renaming {title}: {error_msg}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error renaming {title}: {e}")
            return False


def load_env(env_file: str = ".env") -> dict[str, str]:
    """Load environment variables from .env file."""
    env_vars = {}
    env_path = Path(env_file)

    if not env_path.exists():
        return env_vars

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("export "):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                # Strip quotes
                value = value.strip().strip("'\"")
                env_vars[key.strip()] = value

    return env_vars


# Pages to rename (old-slug -> new-slug)
RENAME_MAP = {
    "home-2": "home",
    "about-2": "about",
}

# Pages to keep as-is
KEEP_PAGES = {
    "signature",
    "black-rose",
    "love-hurts",
    "collections",
    "shop",
    "cart",
    "checkout",
    "my-account",
    "experiences",
    "home",
    "about",
    "contact",
}


def main():
    parser = argparse.ArgumentParser(
        description="Clean up WordPress pages and prepare for production"
    )
    parser.add_argument("--list-only", action="store_true", help="List pages without modifying")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed")
    parser.add_argument("--delete-all", action="store_true", help="Delete ALL pages (dangerous)")
    parser.add_argument(
        "--env-file",
        default="/Users/coreyfoster/DevSkyy/.env",
        help="Path to .env file",
    )
    args = parser.parse_args()

    # Load environment
    env = load_env(args.env_file)
    site_url = env.get("WORDPRESS_URL", "").strip("'\"")
    username = env.get("WORDPRESS_USERNAME", "").strip("'\"")
    app_password = env.get("WORDPRESS_APP_PASSWORD", "").strip("'\"")

    if not site_url:
        print("Error: WORDPRESS_URL not found in .env")
        sys.exit(1)

    if not username:
        print("Error: WORDPRESS_USERNAME not found in .env")
        sys.exit(1)

    if not app_password:
        print("Error: WORDPRESS_APP_PASSWORD not found in .env")
        print("Generate one at: WP Admin → Users → Profile → Application Passwords")
        sys.exit(1)

    client = WordPressRESTClient(site_url, username, app_password)

    print(f"\n📋 Fetching pages from {site_url}...\n")
    pages = client.get_pages()

    if not pages:
        print("✓ No pages found. WordPress is clean.\n")
        return

    print(f"Found {len(pages)} page(s):\n")

    to_rename = []
    to_delete = []
    to_keep = []

    for page in pages:
        slug = page.get("slug", "")
        title = page.get("title", {}).get("rendered", "Untitled")
        page_id = page.get("id")
        status = page.get("status", "unknown")

        status_icon = "📌" if status == "publish" else "📝"

        if slug in RENAME_MAP:
            new_slug = RENAME_MAP[slug]
            print(f"  {status_icon} {status:8} | {title} (/{slug}/) → RENAME to /{new_slug}/")
            to_rename.append((page_id, title, slug, new_slug))
        elif slug in KEEP_PAGES:
            print(f"  {status_icon} {status:8} | {title} (/{slug}/) → KEEP")
            to_keep.append((page_id, title, slug))
        elif args.delete_all:
            print(f"  {status_icon} {status:8} | {title} (/{slug}/) → DELETE")
            to_delete.append((page_id, title, slug))
        else:
            print(f"  {status_icon} {status:8} | {title} (/{slug}/)")
            to_keep.append((page_id, title, slug))

    print("\n📊 Summary:")
    print(f"   Keep: {len(to_keep)}")
    print(f"   Rename: {len(to_rename)}")
    print(f"   Delete: {len(to_delete)}")

    if args.list_only:
        print("\n(Use without --list-only to make changes)\n")
        return

    if not to_rename and not to_delete:
        print("\n✓ No changes needed.\n")
        return

    # Confirm changes unless dry-run
    if not args.dry_run:
        changes = len(to_rename) + len(to_delete)
        print(f"\n⚠️  About to modify {changes} page(s). Type 'YES' to confirm: ", end="")
        confirm = input().strip()
        if confirm != "YES":
            print("Cancelled.\n")
            return

    print("\n🔄 Processing changes...\n")

    success_count = 0

    # Rename pages
    for page_id, title, _old_slug, new_slug in to_rename:
        if client.update_page_slug(page_id, new_slug, title, dry_run=args.dry_run):
            success_count += 1

    # Delete pages
    for page_id, title, slug in to_delete:
        if client.delete_page(page_id, title, dry_run=args.dry_run):
            success_count += 1

    total = len(to_rename) + len(to_delete)
    mode = "DRY-RUN" if args.dry_run else "COMPLETED"
    print(f"\n✓ {mode}: Modified {success_count}/{total} pages.\n")


if __name__ == "__main__":
    main()
