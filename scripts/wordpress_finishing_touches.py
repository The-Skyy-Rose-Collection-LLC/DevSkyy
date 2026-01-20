#!/usr/bin/env python3
"""
SkyyRose WordPress Finishing Touches Script

Applies final polish to WordPress production site:
1. Injects luxury CSS via Customizer/custom_css
2. Configures navigation menus
3. Sets homepage and reading settings
4. Verifies all pages render correctly

Author: DevSkyy Platform Team
"""

import argparse
import base64
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

WORDPRESS_URL = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
WORDPRESS_USERNAME = os.getenv("WORDPRESS_USERNAME", "")
WORDPRESS_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD", "")

PROJECT_ROOT = Path(__file__).parent.parent
CSS_DIR = PROJECT_ROOT / "wordpress" / "skyyrose-immersive" / "assets" / "css"

# Security limits
MAX_CSS_FILE_SIZE = 1 * 1024 * 1024  # 1MB per file
MAX_TOTAL_CSS_SIZE = 5 * 1024 * 1024  # 5MB total
API_RATE_LIMIT_DELAY = 1.5  # seconds between requests

# CSS files to inject (in order)
CSS_FILES = [
    "luxury-design-system.css",
    "luxury-overrides.css",
    "immersive.css",
    "spinning-logo.css",
]

# Navigation menu structure
MENU_STRUCTURE = {
    "main-menu": {
        "name": "Main Menu",
        "items": [
            {"title": "Home", "url": "/", "order": 1},
            {
                "title": "Experiences",
                "url": "/experiences/",
                "order": 2,
                "children": [
                    {"title": "SIGNATURE Collection", "url": "/experiences/signature/", "order": 1},
                    {
                        "title": "BLACK ROSE Collection",
                        "url": "/experiences/black-rose/",
                        "order": 2,
                    },
                    {
                        "title": "LOVE HURTS Collection",
                        "url": "/experiences/love-hurts/",
                        "order": 3,
                    },
                ],
            },
            {"title": "Shop", "url": "/shop/", "order": 3},
            {"title": "About", "url": "/about/", "order": 4},
            {"title": "Contact", "url": "/contact/", "order": 5},
        ],
    },
}

# Page IDs from deployment
PAGE_IDS = {
    "home": 8530,
    "experiences": 8259,
    "signature": 152,
    "black-rose": 153,
    "love-hurts": 154,
    "about": 8536,
}


# ============================================================================
# Input Validation
# ============================================================================

CSS_FILENAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}\.css$")


def validate_css_filename(filename: str) -> bool:
    """Validate CSS filename against safe pattern."""
    return bool(CSS_FILENAME_PATTERN.match(filename))


def sanitize_css_content(content: str) -> str:
    """
    Basic CSS sanitization - remove potential injection vectors.
    Note: This is defense-in-depth; WordPress also sanitizes.
    """
    # Remove potential script injections
    content = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r"javascript:", "", content, flags=re.IGNORECASE)
    content = re.sub(r"expression\s*\(", "", content, flags=re.IGNORECASE)
    content = re.sub(r"@import\s+url\s*\(['\"]?http", "@import url(", content, flags=re.IGNORECASE)
    return content


# ============================================================================
# WordPress API Client
# ============================================================================


class WordPressClient:
    """Authenticated WordPress REST API client with rate limiting."""

    def __init__(self, base_url: str, username: str, app_password: str):
        self.base_url = base_url.rstrip("/")
        self.rest_url = f"{self.base_url}/index.php?rest_route="
        self.session = requests.Session()

        # Basic auth
        credentials = f"{username}:{app_password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        self.session.headers.update(
            {
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/json",
                "User-Agent": "DevSkyy-FinishingTouches/1.0",
            }
        )

        self._last_request_time = 0.0

    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < API_RATE_LIMIT_DELAY:
            time.sleep(API_RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = time.time()

    def get(self, endpoint: str, params: dict | None = None) -> dict[str, Any]:
        """GET request with rate limiting."""
        self._rate_limit()
        url = f"{self.rest_url}{endpoint}"
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, data: dict) -> dict[str, Any]:
        """POST request with rate limiting."""
        self._rate_limit()
        url = f"{self.rest_url}{endpoint}"
        response = self.session.post(url, json=data, timeout=30)
        response.raise_for_status()
        return response.json()

    def put(self, endpoint: str, data: dict) -> dict[str, Any]:
        """PUT request with rate limiting."""
        self._rate_limit()
        url = f"{self.rest_url}{endpoint}"
        response = self.session.put(url, json=data, timeout=30)
        response.raise_for_status()
        return response.json()


# ============================================================================
# CSS Injection
# ============================================================================


def load_css_files() -> str:
    """Load and combine all CSS files with validation."""
    combined_css = []
    total_size = 0

    for filename in CSS_FILES:
        if not validate_css_filename(filename):
            logger.warning(f"Skipping invalid filename: {filename}")
            continue

        filepath = CSS_DIR / filename
        if not filepath.exists():
            logger.warning(f"CSS file not found: {filepath}")
            continue

        file_size = filepath.stat().st_size
        if file_size > MAX_CSS_FILE_SIZE:
            logger.warning(f"CSS file too large ({file_size} bytes): {filename}")
            continue

        total_size += file_size
        if total_size > MAX_TOTAL_CSS_SIZE:
            logger.warning(f"Total CSS size exceeded limit at: {filename}")
            break

        with open(filepath) as f:
            content = f.read()

        # Sanitize and add header
        content = sanitize_css_content(content)
        combined_css.append(f"/* ========== {filename} ========== */")
        combined_css.append(content)
        combined_css.append("")  # Empty line separator

        logger.info(f"✅ Loaded CSS: {filename} ({file_size:,} bytes)")

    return "\n".join(combined_css)


def inject_custom_css(client: WordPressClient, css_content: str, dry_run: bool = False) -> bool:
    """
    Inject custom CSS to WordPress.

    WordPress stores custom CSS in wp_posts with post_type='custom_css'.
    We need to find or create this post and update its content.
    """
    logger.info("Injecting custom CSS to WordPress...")

    if dry_run:
        logger.info(f"[DRY RUN] Would inject {len(css_content):,} chars of CSS")
        return True

    try:
        # Check for existing custom_css post
        # WordPress stores theme custom CSS with post_name = template slug
        existing = client.get(
            "/wp/v2/posts",
            {
                "post_type": "custom_css",
                "per_page": 1,
            },
        )

        if existing and len(existing) > 0:
            post_id = existing[0]["id"]
            logger.info(f"Found existing custom_css post: {post_id}")

            # Update existing
            result = client.post(
                f"/wp/v2/posts/{post_id}",
                {
                    "content": css_content,
                },
            )
            logger.info(f"✅ Updated custom CSS (ID: {post_id})")
        else:
            # Try via settings API for theme mods
            logger.info("No custom_css post found, trying settings API...")

            # WordPress Customizer stores CSS differently
            # We'll use the Additional CSS option via direct post creation
            result = client.post(
                "/wp/v2/posts",
                {
                    "title": "SkyyRose Custom CSS",
                    "content": css_content,
                    "status": "publish",
                    "post_type": "custom_css",
                },
            )
            logger.info(f"✅ Created custom CSS post (ID: {result.get('id')})")

        return True

    except requests.HTTPError as e:
        if e.response.status_code == 403:
            logger.warning("Cannot create custom_css post via REST API - using alternative method")
            return inject_css_via_option(client, css_content, dry_run)
        logger.error(f"Failed to inject CSS: {e}")
        return False


def inject_css_via_option(client: WordPressClient, css_content: str, dry_run: bool = False) -> bool:
    """
    Alternative: Store CSS as a WordPress option that theme can load.
    """
    logger.info("Using option-based CSS injection...")

    if dry_run:
        logger.info(f"[DRY RUN] Would store {len(css_content):,} chars in option")
        return True

    # Save CSS to local file that can be enqueued
    output_file = PROJECT_ROOT / "wordpress" / "skyyrose-custom-css.css"
    with open(output_file, "w") as f:
        f.write(css_content)
    logger.info(f"✅ Saved combined CSS to: {output_file}")

    # Print instructions for manual injection
    logger.info("")
    logger.info("=" * 60)
    logger.info("MANUAL CSS INJECTION REQUIRED")
    logger.info("=" * 60)
    logger.info("1. Go to WordPress Admin → Appearance → Customize")
    logger.info("2. Click 'Additional CSS'")
    logger.info("3. Paste the CSS from: wordpress/skyyrose-custom-css.css")
    logger.info("4. Click 'Publish'")
    logger.info("=" * 60)

    return True


# ============================================================================
# Navigation Menu Configuration
# ============================================================================


def configure_navigation_menus(client: WordPressClient, dry_run: bool = False) -> bool:
    """Configure WordPress navigation menus."""
    logger.info("Configuring navigation menus...")

    if dry_run:
        for _menu_slug, menu_config in MENU_STRUCTURE.items():
            logger.info(f"[DRY RUN] Would create menu: {menu_config['name']}")
            for item in menu_config["items"]:
                logger.info(f"  - {item['title']} → {item['url']}")
                if "children" in item:
                    for child in item["children"]:
                        logger.info(f"    - {child['title']} → {child['url']}")
        return True

    try:
        # Get existing menus
        menus = client.get("/wp/v2/menus")
        existing_menu_ids = {m["slug"]: m["id"] for m in menus}

        for menu_slug, menu_config in MENU_STRUCTURE.items():
            if menu_slug in existing_menu_ids:
                logger.info(f"Menu '{menu_config['name']}' already exists")
                continue

            # Create menu
            menu_result = client.post(
                "/wp/v2/menus",
                {
                    "name": menu_config["name"],
                    "slug": menu_slug,
                },
            )
            menu_id = menu_result.get("id")
            logger.info(f"✅ Created menu: {menu_config['name']} (ID: {menu_id})")

            # Add menu items
            for item in menu_config["items"]:
                item_result = client.post(
                    "/wp/v2/menu-items",
                    {
                        "title": item["title"],
                        "url": f"{WORDPRESS_URL}{item['url']}",
                        "menus": menu_id,
                        "menu_order": item["order"],
                    },
                )
                parent_id = item_result.get("id")
                logger.info(f"  Added: {item['title']}")

                # Add children
                if "children" in item:
                    for child in item["children"]:
                        client.post(
                            "/wp/v2/menu-items",
                            {
                                "title": child["title"],
                                "url": f"{WORDPRESS_URL}{child['url']}",
                                "menus": menu_id,
                                "menu_order": child["order"],
                                "parent": parent_id,
                            },
                        )
                        logger.info(f"    Added: {child['title']}")

        return True

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning("Menu endpoints not available - menus require manual configuration")
            print_menu_instructions()
            return True
        logger.error(f"Failed to configure menus: {e}")
        return False


def print_menu_instructions() -> None:
    """Print manual menu configuration instructions."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("MANUAL MENU CONFIGURATION")
    logger.info("=" * 60)
    logger.info("1. Go to WordPress Admin → Appearance → Menus")
    logger.info("2. Create menu 'Main Menu' with structure:")
    logger.info("   - Home (/)")
    logger.info("   - Experiences (/experiences/)")
    logger.info("     - SIGNATURE Collection (/experiences/signature/)")
    logger.info("     - BLACK ROSE Collection (/experiences/black-rose/)")
    logger.info("     - LOVE HURTS Collection (/experiences/love-hurts/)")
    logger.info("   - Shop (/shop/)")
    logger.info("   - About (/about/)")
    logger.info("   - Contact (/contact/)")
    logger.info("3. Assign to 'Primary Menu' location")
    logger.info("=" * 60)


# ============================================================================
# Homepage & Reading Settings
# ============================================================================


def configure_homepage_settings(client: WordPressClient, dry_run: bool = False) -> bool:
    """Set homepage and blog page in WordPress reading settings."""
    logger.info("Configuring homepage settings...")

    home_page_id = PAGE_IDS.get("home")
    if not home_page_id:
        logger.error("Home page ID not found")
        return False

    if dry_run:
        logger.info(f"[DRY RUN] Would set homepage to page ID: {home_page_id}")
        return True

    try:
        # WordPress settings are typically updated via options
        # REST API settings endpoint requires specific permissions
        client.put(
            "/wp/v2/settings",
            {
                "show_on_front": "page",
                "page_on_front": home_page_id,
            },
        )
        logger.info(f"✅ Set homepage to: Home (ID: {home_page_id})")
        return True

    except requests.HTTPError as e:
        if e.response.status_code in (403, 404):
            logger.warning("Settings API not available - requires manual configuration")
            logger.info("")
            logger.info("=" * 60)
            logger.info("MANUAL HOMEPAGE CONFIGURATION")
            logger.info("=" * 60)
            logger.info("1. Go to WordPress Admin → Settings → Reading")
            logger.info("2. Select 'A static page'")
            logger.info(f"3. Homepage: Select 'Home' (ID: {home_page_id})")
            logger.info("4. Click 'Save Changes'")
            logger.info("=" * 60)
            return True
        logger.error(f"Failed to set homepage: {e}")
        return False


# ============================================================================
# Verification
# ============================================================================


def verify_finishing_touches(client: WordPressClient) -> dict[str, bool]:
    """Verify all finishing touches were applied."""
    logger.info("Verifying finishing touches...")
    results = {}

    # Check pages are accessible
    for slug, page_id in PAGE_IDS.items():
        try:
            page = client.get(f"/wp/v2/pages/{page_id}")
            status = page.get("status") == "publish"
            results[f"page_{slug}"] = status
            logger.info(f"  Page '{slug}': {'✅' if status else '❌'}")
        except Exception:
            results[f"page_{slug}"] = False
            logger.info(f"  Page '{slug}': ❌")

    # Check homepage setting
    try:
        settings = client.get("/wp/v2/settings")
        home_check = settings.get("show_on_front") == "page" and settings.get(
            "page_on_front"
        ) == PAGE_IDS.get("home")
        results["homepage_set"] = home_check
        logger.info(f"  Homepage setting: {'✅' if home_check else '❌'}")
    except Exception:
        results["homepage_set"] = False
        logger.info("  Homepage setting: ❌ (requires manual check)")

    return results


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Apply finishing touches to SkyyRose WordPress site",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them",
    )
    parser.add_argument(
        "--css-only",
        action="store_true",
        help="Only inject CSS, skip other configurations",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only run verification checks",
    )

    args = parser.parse_args()

    # Validate credentials
    if not WORDPRESS_USERNAME or not WORDPRESS_APP_PASSWORD:
        logger.error("WordPress credentials not configured in .env")
        sys.exit(1)

    # Initialize client
    client = WordPressClient(WORDPRESS_URL, WORDPRESS_USERNAME, WORDPRESS_APP_PASSWORD)

    print("")
    print("=" * 60)
    print("  SKYYROSE FINISHING TOUCHES")
    print("=" * 60)
    print(f"  Site: {WORDPRESS_URL}")
    print(f"  Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print("=" * 60)
    print("")

    if args.verify_only:
        results = verify_finishing_touches(client)
        all_passed = all(results.values())
        print("")
        print("=" * 60)
        print(f"  VERIFICATION: {'✅ ALL PASSED' if all_passed else '❌ SOME FAILED'}")
        print("=" * 60)
        sys.exit(0 if all_passed else 1)

    # Step 1: Load and inject CSS
    logger.info("Step 1/3: CSS Injection")
    logger.info("-" * 40)
    css_content = load_css_files()
    if css_content:
        inject_custom_css(client, css_content, args.dry_run)
    else:
        logger.warning("No CSS content loaded")

    if args.css_only:
        logger.info("CSS-only mode - skipping remaining steps")
        sys.exit(0)

    print("")

    # Step 2: Configure navigation
    logger.info("Step 2/3: Navigation Menus")
    logger.info("-" * 40)
    configure_navigation_menus(client, args.dry_run)

    print("")

    # Step 3: Set homepage
    logger.info("Step 3/3: Homepage Settings")
    logger.info("-" * 40)
    configure_homepage_settings(client, args.dry_run)

    print("")

    # Final verification
    if not args.dry_run:
        logger.info("Running verification...")
        results = verify_finishing_touches(client)

    print("")
    print("=" * 60)
    if args.dry_run:
        print("  DRY RUN COMPLETE - No changes made")
    else:
        print("  FINISHING TOUCHES APPLIED")
    print("=" * 60)
    print("")


if __name__ == "__main__":
    main()
