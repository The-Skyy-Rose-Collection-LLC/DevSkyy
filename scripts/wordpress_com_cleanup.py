#!/usr/bin/env python3
"""
WordPress.com Page Cleanup via OAuth

Deletes all existing WordPress.com pages and prepares for production.

Requirements in .env:
  - WORDPRESS_URL (e.g., https://skyyrose.co)
  - WORDPRESS_COM_ACCESS_TOKEN (OAuth bearer token from WordPress.com)

Setup OAuth Token:
  1. Go to https://developer.wordpress.com/apps/
  2. Create app → get Client ID & Secret
  3. Get authorization code from:
     https://public-api.wordpress.com/oauth2/authorize?client_id=ID&redirect_uri=YOUR_REDIRECT&response_type=code
  4. Exchange code for token:
     curl -X POST https://public-api.wordpress.com/oauth2/token \
       -d "client_id=ID" \
       -d "client_secret=SECRET" \
       -d "code=CODE" \
       -d "grant_type=authorization_code"
  5. Add access_token to .env as WORDPRESS_COM_ACCESS_TOKEN

Usage:
    python scripts/wordpress_com_cleanup.py [--list-only] [--dry-run]
"""

import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("Error: requests not installed. Try: python -m pip install requests")
    sys.exit(1)


class WordPressCOMClient:
    """WordPress.com REST API v1.1 client using OAuth."""

    BASE_URL = "https://public-api.wordpress.com/rest/v1.1"

    def __init__(self, site_url: str, access_token: str):
        """Initialize WordPress.com client.

        Args:
            site_url: Full site URL (e.g., https://skyyrose.co)
            access_token: OAuth access token from WordPress.com
        """
        # Extract domain from URL
        parsed = urlparse(site_url)
        self.site_url = site_url.rstrip("/")
        self.domain = parsed.netloc  # e.g., skyyrose.co
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def get_pages(self) -> list[dict]:
        """Fetch all pages from WordPress.com."""
        pages = []
        per_page = 100
        page_num = 1

        while True:
            url = f"{self.BASE_URL}/sites/{self.domain}/posts/"
            params = {
                "type": "page",
                "per_page": per_page,
                "page": page_num,
                "status": "publish,draft",
            }

            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                response.raise_for_status()
                result = response.json()

                if "posts" not in result:
                    print(f"Error: Unexpected response format: {result}")
                    break

                posts = result["posts"]
                if not posts:
                    break

                pages.extend(posts)
                if len(posts) < per_page:
                    break

                page_num += 1
            except requests.exceptions.RequestException as e:
                print(f"Error fetching pages: {e}")
                break

        return pages

    def delete_page(self, page_id: int, title: str, dry_run: bool = False) -> bool:
        """Delete a page from WordPress.com.

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

        url = f"{self.BASE_URL}/sites/{self.domain}/posts/{page_id}"
        params = {"status": "delete"}

        try:
            response = requests.post(url, headers=self.headers, params=params, timeout=10)
            if response.status_code in (200, 204):
                print(f"  ✓ Deleted: {title} (ID: {page_id})")
                return True
            else:
                error_msg = response.json().get("message", response.text)
                print(f"  ✗ Error deleting {title}: {error_msg}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error deleting {title}: {e}")
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
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()

    return env_vars


def main():
    parser = argparse.ArgumentParser(
        description="Clean up WordPress.com pages and prepare for production"
    )
    parser.add_argument("--list-only", action="store_true", help="List pages without deleting")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted")
    parser.add_argument(
        "--env-file",
        default="/Users/coreyfoster/DevSkyy/.env",
        help="Path to .env file",
    )
    args = parser.parse_args()

    # Load environment
    env = load_env(args.env_file)
    site_url = env.get("WORDPRESS_URL", "").strip("'\"")
    access_token = env.get("WORDPRESS_COM_ACCESS_TOKEN", "").strip("'\"")

    if not site_url:
        print("Error: WORDPRESS_URL not found in .env")
        sys.exit(1)

    if not access_token:
        print("Error: WORDPRESS_COM_ACCESS_TOKEN not found in .env")
        print("See wordpress/WORDPRESS_COM_CLEANUP_GUIDE.md for setup instructions.")
        sys.exit(1)

    client = WordPressCOMClient(site_url, access_token)

    print(f"\n📋 Fetching pages from {site_url}...\n")
    pages = client.get_pages()

    if not pages:
        print("✓ No pages found. WordPress is clean.\n")
        return

    print(f"Found {len(pages)} page(s):\n")
    for page in pages:
        status = "📌" if page.get("status") == "publish" else "📝"
        print(f"  {status} {page['status']:8} | {page['title']} (ID: {page['ID']})")

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
    deleted_count = 0
    for page in pages:
        if client.delete_page(page["ID"], page["title"], dry_run=args.dry_run):
            deleted_count += 1

    mode = "DRY-RUN" if args.dry_run else "COMPLETED"
    print(f"\n✓ {mode}: Deleted {deleted_count}/{len(pages)} pages.\n")

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
    main()
