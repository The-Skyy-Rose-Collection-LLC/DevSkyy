#!/usr/bin/env python3
"""
WordPress Page Structure Deployment Script

Deploys the /experiences/ URL pattern for 3D collection pages:
- Creates "Experiences" parent page
- Updates SIGNATURE, BLACK ROSE, LOVE HURTS as child pages
- Sets proper slugs for /experiences/signature/, etc.

Usage:
    # Dry run (preview changes)
    python scripts/deploy_wordpress_pages.py --dry-run

    # Deploy to WordPress
    python scripts/deploy_wordpress_pages.py --deploy

    # Validate current state
    python scripts/deploy_wordpress_pages.py --validate

Requirements:
    Set environment variables:
    - WORDPRESS_URL (e.g., https://skyyrose.co)
    - WORDPRESS_USERNAME
    - WORDPRESS_APP_PASSWORD

Author: DevSkyy Platform Team
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "httpx", "-q"])
    import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class WordPressConfig:
    """WordPress API configuration."""
    url: str
    username: str
    app_password: str

    @classmethod
    def from_env(cls) -> "WordPressConfig":
        """Load from environment variables."""
        url = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
        username = os.getenv("WORDPRESS_USERNAME", "")
        password = os.getenv("WORDPRESS_APP_PASSWORD", "")

        if not username or not password:
            raise ValueError(
                "Missing WordPress credentials. Set WORDPRESS_USERNAME and "
                "WORDPRESS_APP_PASSWORD environment variables."
            )

        return cls(url=url, username=username, app_password=password)

    @property
    def auth_header(self) -> str:
        """Get Basic Auth header value."""
        credentials = f"{self.username}:{self.app_password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"


# Page configuration for /experiences/ pattern
EXPERIENCES_PARENT = {
    "title": "3D Experiences",
    "slug": "experiences",
    "content": "<p>Explore our immersive 3D collection experiences.</p>",
    "status": "publish",
}

COLLECTION_PAGES = [
    {
        "id": 152,  # SIGNATURE
        "title": "SIGNATURE Runway Experience",
        "slug": "signature",
        "parent_slug": "experiences",
        "meta_description": "Immersive 3D runway experience for the SIGNATURE collection.",
    },
    {
        "id": 153,  # BLACK ROSE
        "title": "BLACK ROSE Garden Experience",
        "slug": "black-rose",
        "parent_slug": "experiences",
        "meta_description": "Immersive 3D garden experience for the BLACK ROSE collection.",
    },
    {
        "id": 154,  # LOVE HURTS
        "title": "LOVE HURTS Castle Experience",
        "slug": "love-hurts",
        "parent_slug": "experiences",
        "meta_description": "Immersive 3D castle experience for the LOVE HURTS collection.",
    },
]


async def get_page_by_slug(client: httpx.AsyncClient, config: WordPressConfig, slug: str) -> dict | None:
    """Get page by slug."""
    # Use index.php?rest_route= format for WordPress.com hosted sites
    url = f"{config.url}/index.php"
    params = {"rest_route": "/wp/v2/pages", "slug": slug, "_fields": "id,slug,title,parent,status"}

    response = await client.get(
        url,
        params=params,
        headers={"Authorization": config.auth_header},
    )

    if response.status_code == 200:
        pages = response.json()
        return pages[0] if pages else None
    return None


async def create_page(
    client: httpx.AsyncClient,
    config: WordPressConfig,
    data: dict,
) -> dict | None:
    """Create a new page."""
    # Use index.php?rest_route= format for WordPress.com hosted sites
    url = f"{config.url}/index.php?rest_route=/wp/v2/pages"

    response = await client.post(
        url,
        json=data,
        headers={
            "Authorization": config.auth_header,
            "Content-Type": "application/json",
        },
    )

    if response.status_code == 201:
        result = response.json()
        logger.info(f"Created page: {result.get('slug')} (ID: {result.get('id')})")
        return result
    else:
        logger.error(f"Failed to create page: {response.status_code} - {response.text[:200]}")
        return None


async def update_page(
    client: httpx.AsyncClient,
    config: WordPressConfig,
    page_id: int,
    data: dict,
) -> dict | None:
    """Update an existing page."""
    # Use index.php?rest_route= format for WordPress.com hosted sites
    url = f"{config.url}/index.php?rest_route=/wp/v2/pages/{page_id}"

    response = await client.post(
        url,
        json=data,
        headers={
            "Authorization": config.auth_header,
            "Content-Type": "application/json",
        },
    )

    if response.status_code == 200:
        result = response.json()
        logger.info(f"Updated page: {result.get('slug')} (ID: {result.get('id')})")
        return result
    else:
        logger.error(f"Failed to update page {page_id}: {response.status_code} - {response.text[:200]}")
        return None


async def deploy_experiences_structure(config: WordPressConfig, dry_run: bool = False) -> dict:
    """Deploy the /experiences/ URL structure."""
    results = {
        "parent_created": False,
        "parent_id": None,
        "children_updated": [],
        "errors": [],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Check/create parent "Experiences" page
        logger.info("Checking for existing 'experiences' parent page...")
        parent = await get_page_by_slug(client, config, "experiences")

        if parent:
            logger.info(f"Parent 'experiences' page already exists (ID: {parent['id']})")
            results["parent_id"] = parent["id"]
        else:
            if dry_run:
                logger.info("[DRY RUN] Would create parent 'experiences' page")
                results["parent_id"] = "NEW"
            else:
                logger.info("Creating parent 'experiences' page...")
                parent = await create_page(client, config, EXPERIENCES_PARENT)
                if parent:
                    results["parent_created"] = True
                    results["parent_id"] = parent["id"]
                else:
                    results["errors"].append("Failed to create parent page")
                    return results

        parent_id = results["parent_id"] if results["parent_id"] != "NEW" else 0

        # Step 2: Update collection pages as children
        for page_config in COLLECTION_PAGES:
            # Rate limiting delay
            await asyncio.sleep(2.0)

            page_id = page_config["id"]
            update_data = {
                "title": page_config["title"],
                "slug": page_config["slug"],
                "parent": parent_id,
                "status": "publish",
            }

            if dry_run:
                logger.info(
                    f"[DRY RUN] Would update page {page_id} ({page_config['slug']}) "
                    f"with parent={parent_id}"
                )
                results["children_updated"].append({
                    "id": page_id,
                    "slug": page_config["slug"],
                    "status": "would_update",
                })
            else:
                updated = await update_page(client, config, page_id, update_data)
                if updated:
                    results["children_updated"].append({
                        "id": page_id,
                        "slug": updated.get("slug"),
                        "parent": updated.get("parent"),
                        "status": "updated",
                    })
                else:
                    results["errors"].append(f"Failed to update page {page_id}")

    return results


async def validate_structure(config: WordPressConfig) -> dict:
    """Validate current page structure."""
    results = {
        "parent_exists": False,
        "parent_id": None,
        "children": [],
        "issues": [],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check parent
        parent = await get_page_by_slug(client, config, "experiences")
        if parent:
            results["parent_exists"] = True
            results["parent_id"] = parent["id"]
        else:
            results["issues"].append("Parent 'experiences' page does not exist")

        # Check children
        for page_config in COLLECTION_PAGES:
            try:
                # Use index.php?rest_route= format for WordPress.com hosted sites
                url = f"{config.url}/index.php"
                params = {"rest_route": f"/wp/v2/pages/{page_config['id']}", "_fields": "id,slug,title,parent,status,link"}
                response = await client.get(
                    url,
                    params=params,
                    headers={"Authorization": config.auth_header},
                )

                if response.status_code == 200:
                    page = response.json()
                    child_info = {
                        "id": page["id"],
                        "slug": page.get("slug"),
                        "parent": page.get("parent"),
                        "link": page.get("link"),
                        "expected_slug": page_config["slug"],
                    }
                    results["children"].append(child_info)

                    # Check for issues
                    if page.get("slug") != page_config["slug"]:
                        results["issues"].append(
                            f"Page {page['id']} has slug '{page.get('slug')}' "
                            f"but expected '{page_config['slug']}'"
                        )
                    if parent and page.get("parent") != parent["id"]:
                        results["issues"].append(
                            f"Page {page['id']} has parent {page.get('parent')} "
                            f"but expected {parent['id']}"
                        )
                else:
                    results["issues"].append(
                        f"Page {page_config['id']} not found (HTTP {response.status_code})"
                    )
            except Exception as e:
                results["issues"].append(f"Error checking page {page_config['id']}: {e}")

    return results


def print_results(results: dict, mode: str) -> None:
    """Print results in a readable format."""
    print("\n" + "=" * 60)
    print(f"  {mode.upper()} RESULTS")
    print("=" * 60)

    if mode == "deploy":
        print(f"\nParent Page:")
        if results.get("parent_created"):
            print(f"  ✅ Created 'experiences' page (ID: {results['parent_id']})")
        elif results.get("parent_id"):
            print(f"  ✓ Already exists (ID: {results['parent_id']})")

        print(f"\nChild Pages:")
        for child in results.get("children_updated", []):
            status = "✅" if child["status"] == "updated" else "→"
            print(f"  {status} {child['slug']} (ID: {child['id']})")

        if results.get("errors"):
            print(f"\nErrors:")
            for error in results["errors"]:
                print(f"  ❌ {error}")

    elif mode == "validate":
        print(f"\nParent Page:")
        if results.get("parent_exists"):
            print(f"  ✅ 'experiences' page exists (ID: {results['parent_id']})")
        else:
            print(f"  ❌ 'experiences' page missing")

        print(f"\nChild Pages:")
        for child in results.get("children", []):
            parent_ok = child.get("parent") == results.get("parent_id")
            slug_ok = child.get("slug") == child.get("expected_slug")
            status = "✅" if (parent_ok and slug_ok) else "⚠️"
            print(f"  {status} ID {child['id']}: /{child.get('slug')}/ (parent={child.get('parent')})")
            if child.get("link"):
                print(f"      URL: {child['link']}")

        if results.get("issues"):
            print(f"\nIssues Found:")
            for issue in results["issues"]:
                print(f"  ⚠️ {issue}")
        else:
            print(f"\n✅ No issues found - structure is correct!")

    print("\n" + "=" * 60)


async def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Deploy WordPress /experiences/ URL structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--deploy", action="store_true", help="Deploy changes to WordPress")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without deploying")
    parser.add_argument("--validate", action="store_true", help="Validate current structure")

    args = parser.parse_args()

    try:
        config = WordPressConfig.from_env()
    except ValueError as e:
        logger.error(str(e))
        print("\nTo set credentials, run:")
        print("  export WORDPRESS_URL='https://example.com'")
        print("  export WORDPRESS_USERNAME='<your-username>'")
        print("  export WORDPRESS_APP_PASSWORD='<your-app-password>'")
        return 1

    print(f"\nWordPress URL: {config.url}")
    print(f"Username: {config.username}")

    if args.validate:
        results = await validate_structure(config)
        print_results(results, "validate")
        return 0 if not results.get("issues") else 1

    elif args.deploy or args.dry_run:
        results = await deploy_experiences_structure(config, dry_run=args.dry_run)
        print_results(results, "deploy" if not args.dry_run else "dry-run")
        return 0 if not results.get("errors") else 1

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
