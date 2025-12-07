#!/usr/bin/env python3
"""
Deploy Elementor Pages to WordPress

Deploys all 9 Elementor JSON templates to skyyrose.co:
- Global: header, footer
- Pages: homepage, about
- Collections: love-hurts, black-rose, signature
- WooCommerce: archive-product, single-product

Usage:
    python deploy_elementor_pages.py --mode=draft
    python deploy_elementor_pages.py --mode=publish
"""

import argparse
import asyncio
import base64
from dataclasses import dataclass
from datetime import datetime
from http import HTTPStatus
import json
import os
from pathlib import Path
import sys
from typing import Any, ClassVar

import httpx


# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


@dataclass
class DeploymentResult:
    """Result of a page deployment."""

    template_path: str
    page_title: str
    page_slug: str
    success: bool
    page_id: int | None = None
    page_url: str | None = None
    error: str | None = None


class ElementorPageDeployer:
    """Deploy Elementor JSON templates to WordPress."""

    # Template paths relative to elementor directory
    TEMPLATES: ClassVar[dict[str, dict[str, Any]]] = {
        # Global templates (Elementor Theme Builder)
        "header": {"path": "global/header.json", "type": "theme_builder", "location": "header"},
        "footer": {"path": "global/footer.json", "type": "theme_builder", "location": "footer"},
        # Standard pages
        "homepage": {"path": "pages/homepage.json", "type": "page", "slug": "home", "is_front_page": True},
        "about": {"path": "pages/about.json", "type": "page", "slug": "about"},
        # Collection pages
        "love-hurts": {"path": "collections/love-hurts.json", "type": "page", "slug": "love-hurts-collection"},
        "black-rose": {"path": "collections/black-rose.json", "type": "page", "slug": "black-rose-collection"},
        "signature": {"path": "collections/signature.json", "type": "page", "slug": "signature-collection"},
        # WooCommerce templates (Elementor Theme Builder)
        "archive-product": {
            "path": "woocommerce/archive-product.json",
            "type": "theme_builder",
            "location": "archive",
        },
        "single-product": {"path": "woocommerce/single-product.json", "type": "theme_builder", "location": "single"},
    }

    def __init__(self, site_url: str, username: str, password: str):
        """Initialize deployer with WordPress credentials."""
        self.site_url = site_url.rstrip("/")
        self.api_base = f"{self.site_url}/wp-json"
        self.username = username
        self.password = password

        # Create basic auth header
        credentials = f"{username}:{password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        self.auth_header = {"Authorization": f"Basic {encoded}"}

        # Get template directory
        self.template_dir = Path(__file__).parent.parent.parent / "mcp_servers" / "wordpress" / "elementor"

        # Track results
        self.results: list[DeploymentResult] = []

    async def verify_connection(self) -> bool:
        """Verify WordPress API connection."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(f"{self.api_base}/wp/v2/users/me", headers=self.auth_header)
                if response.status_code == HTTPStatus.OK:
                    user = response.json()
                    print(f"Connected as: {user.get('name', 'Unknown')} ({user.get('slug', 'unknown')})")
                    return True
                else:
                    print(f"Connection failed: {response.status_code} - {response.text}")
                    return False
            except Exception as e:
                print(f"Connection error: {e}")
                return False

    def load_template(self, template_path: str) -> dict | None:
        """Load Elementor template JSON."""
        full_path = self.template_dir / template_path
        if not full_path.exists():
            print(f"  Template not found: {full_path}")
            return None

        with open(full_path) as f:
            return json.load(f)

    async def deploy_page(self, template_key: str, template_config: dict, status: str = "draft") -> DeploymentResult:
        """Deploy a single page template."""
        template_path = template_config["path"]
        print(f"\nDeploying: {template_key}")
        print(f"  Template: {template_path}")

        # Load template
        template = self.load_template(template_path)
        if not template:
            return DeploymentResult(
                template_path=template_path,
                page_title=template_key,
                page_slug=template_config.get("slug", template_key),
                success=False,
                error="Template not found",
            )

        page_title = template.get("title", template_key.replace("-", " ").title())
        page_slug = template_config.get("slug", template_key)

        # Build page content
        # Note: WordPress REST API expects _elementor_page_settings as object, not JSON string
        # But _elementor_data must be a JSON string
        page_data = {
            "title": page_title,
            "slug": page_slug,
            "status": status,
            "template": template.get("settings", {}).get("template", "elementor_header_footer"),
            "content": "",  # Elementor pages have empty content, data in meta
            "meta": {
                "_elementor_edit_mode": "builder",
                "_elementor_template_type": "wp-page",
                "_elementor_version": template.get("version", "3.33.0"),
                "_elementor_data": json.dumps(template.get("content", [])),
                "_elementor_page_settings": template.get("settings", {}),  # Object, not string
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                # Check if page exists
                existing = await client.get(
                    f"{self.api_base}/wp/v2/pages", params={"slug": page_slug}, headers=self.auth_header
                )

                if existing.status_code == HTTPStatus.OK and existing.json():
                    # Update existing page
                    page_id = existing.json()[0]["id"]
                    print(f"  Updating existing page ID: {page_id}")
                    response = await client.post(
                        f"{self.api_base}/wp/v2/pages/{page_id}", json=page_data, headers=self.auth_header
                    )
                else:
                    # Create new page
                    print("  Creating new page")
                    response = await client.post(
                        f"{self.api_base}/wp/v2/pages", json=page_data, headers=self.auth_header
                    )

                if response.status_code in (HTTPStatus.OK, HTTPStatus.CREATED):
                    result = response.json()
                    page_id = result.get("id")
                    page_url = result.get("link")
                    print(f"  Success! Page ID: {page_id}")
                    print(f"  URL: {page_url}")

                    return DeploymentResult(
                        template_path=template_path,
                        page_title=page_title,
                        page_slug=page_slug,
                        success=True,
                        page_id=page_id,
                        page_url=page_url,
                    )
                else:
                    error = f"HTTP {response.status_code}: {response.text[:200]}"
                    print(f"  Failed: {error}")
                    return DeploymentResult(
                        template_path=template_path,
                        page_title=page_title,
                        page_slug=page_slug,
                        success=False,
                        error=error,
                    )

            except Exception as e:
                error = str(e)
                print(f"  Error: {error}")
                return DeploymentResult(
                    template_path=template_path, page_title=page_title, page_slug=page_slug, success=False, error=error
                )

    async def deploy_theme_template(
        self, template_key: str, template_config: dict, status: str = "draft"
    ) -> DeploymentResult:
        """Deploy a theme builder template (header/footer/archive/single)."""
        template_path = template_config["path"]
        location = template_config.get("location", "")
        print(f"\nDeploying Theme Template: {template_key}")
        print(f"  Template: {template_path}")
        print(f"  Location: {location}")

        # Load template
        template = self.load_template(template_path)
        if not template:
            return DeploymentResult(
                template_path=template_path,
                page_title=template_key,
                page_slug=template_key,
                success=False,
                error="Template not found",
            )

        page_title = template.get("title", template_key.replace("-", " ").title())

        # Elementor Theme Builder uses elementor_library post type
        # Map our type names to Elementor's allowed template types
        # Valid types: post, wp-post, wp-page, kit, not-supported, page, section, container
        type_map = {
            "header": "section",  # Headers are sections
            "footer": "section",  # Footers are sections
            "wc-archive-product": "section",  # Use section for WC templates
            "wc-single-product": "section",  # Use section for WC templates
        }
        template_type = type_map.get(template.get("type", "header"), "section")

        template_data = {
            "title": page_title,
            "slug": f"sr-{template_key}",
            "status": status,
            "meta": {
                "_elementor_edit_mode": "builder",
                "_elementor_template_type": template_type,
                "_elementor_version": template.get("version", "3.33.0"),
                "_elementor_data": json.dumps(template.get("content", [])),
                "_elementor_page_settings": template.get("settings", {}),  # Object, not string
                "_elementor_conditions": template.get("settings", {}).get("conditions", ["include/general"]),  # Object
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                # Elementor library templates use a different endpoint
                # Note: This requires Elementor Pro Theme Builder
                response = await client.post(
                    f"{self.api_base}/wp/v2/elementor_library", json=template_data, headers=self.auth_header
                )

                if response.status_code == HTTPStatus.NOT_FOUND:
                    # Elementor library endpoint not available, try regular pages
                    print("  Theme builder endpoint not available, using pages endpoint")
                    return await self.deploy_page(template_key, template_config, status)

                if response.status_code in (HTTPStatus.OK, HTTPStatus.CREATED):
                    result = response.json()
                    page_id = result.get("id")
                    page_url = result.get("link")
                    print(f"  Success! Template ID: {page_id}")
                    print(f"  Edit URL: {self.site_url}/wp-admin/post.php?post={page_id}&action=elementor")

                    return DeploymentResult(
                        template_path=template_path,
                        page_title=page_title,
                        page_slug=f"sr-{template_key}",
                        success=True,
                        page_id=page_id,
                        page_url=page_url,
                    )
                else:
                    error = f"HTTP {response.status_code}: {response.text[:200]}"
                    print(f"  Failed: {error}")
                    return DeploymentResult(
                        template_path=template_path,
                        page_title=page_title,
                        page_slug=f"sr-{template_key}",
                        success=False,
                        error=error,
                    )

            except Exception as e:
                error = str(e)
                print(f"  Error: {error}")
                return DeploymentResult(
                    template_path=template_path,
                    page_title=page_title,
                    page_slug=f"sr-{template_key}",
                    success=False,
                    error=error,
                )

    async def deploy_all(self, status: str = "draft") -> dict[str, Any]:
        """Deploy all templates in order."""
        print("=" * 60)
        print(f"Deploying Elementor Pages to {self.site_url}")
        print(f"Mode: {status.upper()}")
        print(f"Time: {datetime.now().isoformat()}")
        print("=" * 60)

        # Verify connection
        print("\nVerifying WordPress connection...")
        if not await self.verify_connection():
            return {"success": False, "error": "Failed to connect to WordPress", "results": []}

        # Deploy in order: theme builder first, then pages
        deployment_order = [
            # Global templates first
            "header",
            "footer",
            # Then pages
            "homepage",
            "about",
            "love-hurts",
            "black-rose",
            "signature",
            # WooCommerce templates last
            "archive-product",
            "single-product",
        ]

        for template_key in deployment_order:
            config = self.TEMPLATES.get(template_key)
            if not config:
                print(f"\nSkipping unknown template: {template_key}")
                continue

            if config["type"] == "theme_builder":
                result = await self.deploy_theme_template(template_key, config, status)
            else:
                result = await self.deploy_page(template_key, config, status)

            self.results.append(result)

        # Summary
        print("\n" + "=" * 60)
        print("DEPLOYMENT SUMMARY")
        print("=" * 60)

        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]

        print(f"\nSuccessful: {len(successful)}/{len(self.results)}")
        for r in successful:
            print(f"  [OK] {r.page_title} → {r.page_url or r.page_slug}")

        if failed:
            print(f"\nFailed: {len(failed)}/{len(self.results)}")
            for r in failed:
                print(f"  [FAIL] {r.page_title}: {r.error}")

        return {
            "success": len(failed) == 0,
            "total": len(self.results),
            "successful": len(successful),
            "failed": len(failed),
            "results": [
                {
                    "template": r.template_path,
                    "title": r.page_title,
                    "slug": r.page_slug,
                    "success": r.success,
                    "page_id": r.page_id,
                    "url": r.page_url,
                    "error": r.error,
                }
                for r in self.results
            ],
        }


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Deploy Elementor pages to WordPress")
    parser.add_argument(
        "--mode", choices=["draft", "publish"], default="draft", help="Deployment mode: draft (default) or publish"
    )
    parser.add_argument("--template", help="Deploy single template (e.g., 'homepage', 'header')")
    args = parser.parse_args()

    # Get credentials from environment
    site_url = os.getenv("SKYY_ROSE_SITE_URL")
    username = os.getenv("SKYY_ROSE_USERNAME")
    password = os.getenv("SKYY_ROSE_APP_PASSWORD") or os.getenv("SKYY_ROSE_PASSWORD")

    if not all([site_url, username, password]):
        print("ERROR: Missing WordPress credentials")
        print("Required environment variables:")
        print("  SKYY_ROSE_SITE_URL")
        print("  SKYY_ROSE_USERNAME")
        print("  SKYY_ROSE_APP_PASSWORD (or SKYY_ROSE_PASSWORD)")
        sys.exit(1)

    deployer = ElementorPageDeployer(site_url, username, password)

    if args.template:
        # Deploy single template
        config = deployer.TEMPLATES.get(args.template)
        if not config:
            print(f"Unknown template: {args.template}")
            print(f"Available: {', '.join(deployer.TEMPLATES.keys())}")
            sys.exit(1)

        if config["type"] == "theme_builder":
            result = await deployer.deploy_theme_template(args.template, config, args.mode)
        else:
            result = await deployer.deploy_page(args.template, config, args.mode)

        if not result.success:
            sys.exit(1)
    else:
        # Deploy all
        result = await deployer.deploy_all(args.mode)

        # Save results to file
        results_file = Path(__file__).parent / "deployment_results.json"
        with open(results_file, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nResults saved to: {results_file}")

        if not result["success"]:
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
