#!/usr/bin/env python3
"""
Deploy Elementor templates to WordPress.
Uses WordPress REST API + Elementor plugin.
"""

import json
import os
from pathlib import Path

import requests


class ElementorDeployer:
    """Deploy Elementor JSON templates to WordPress."""

    def __init__(self, base_url: str, username: str, app_password: str):
        self.base_url = base_url.rstrip("/")
        self.auth = (username, app_password)
        self.headers = {"Content-Type": "application/json"}

    def get_page_by_slug(self, slug: str) -> dict | None:
        """Get existing page by slug."""
        url = f"{self.base_url}/wp-json/wp/v2/pages"
        params = {"slug": slug, "per_page": 1}
        response = requests.get(url, auth=self.auth, params=params, timeout=30)
        response.raise_for_status()
        pages = response.json()
        return pages[0] if pages else None

    def deploy_template(self, template_path: Path) -> dict:
        """Deploy single Elementor template."""
        print(f"\n{'=' * 70}")
        print(f"📄 Deploying: {template_path.name}")
        print(f"{'=' * 70}")

        # Load template
        with open(template_path) as f:
            template_data = json.load(f)

        # Extract metadata
        page_settings = template_data.get("page_settings", {})
        title = page_settings.get("post_title", template_path.stem.replace("_", " ").title())
        slug = template_path.stem.replace("_", "-")
        meta_desc = page_settings.get("meta_description", "")

        print(f"   Title: {title}")
        print(f"   Slug: {slug}")

        # Check if page exists
        existing_page = self.get_page_by_slug(slug)

        # Prepare Elementor data (stored in post meta)
        elementor_data = json.dumps(template_data.get("content", []))
        page_data = {
            "title": title,
            "slug": slug,
            "status": "publish",
            "template": page_settings.get("template", "elementor_canvas"),
            "meta": {
                "_elementor_data": elementor_data,
                "_elementor_edit_mode": "builder",
                "_elementor_template_type": "wp-page",
                "_wp_page_template": page_settings.get("template", "elementor_canvas"),
            },
        }

        if meta_desc:
            page_data["meta"]["_yoast_wpseo_metadesc"] = meta_desc

        # Create or update
        if existing_page:
            page_id = existing_page["id"]
            print(f"   ✓ Found existing page (ID: {page_id})")
            url = f"{self.base_url}/wp-json/wp/v2/pages/{page_id}"
            response = requests.post(
                url, auth=self.auth, json=page_data, headers=self.headers, timeout=30
            )
            action = "Updated"
        else:
            print("   ✓ Creating new page")
            url = f"{self.base_url}/wp-json/wp/v2/pages"
            response = requests.post(
                url, auth=self.auth, json=page_data, headers=self.headers, timeout=30
            )
            action = "Created"

        response.raise_for_status()
        result = response.json()
        page_id = result["id"]
        page_url = result["link"]

        print(f"   ✅ {action} (ID: {page_id})")
        print(f"   🔗 {page_url}")

        return {
            "success": True,
            "page_id": page_id,
            "title": title,
            "slug": slug,
            "url": page_url,
            "action": action.lower(),
        }

    def deploy_all(self, templates_dir: Path) -> list[dict]:
        """Deploy all Elementor templates."""
        results = []
        template_files = sorted(templates_dir.glob("*.json"))

        print(f"\n{'#' * 70}")
        print("# ELEMENTOR TEMPLATE DEPLOYMENT")
        print(f"# Templates: {len(template_files)}")
        print(f"# WordPress: {self.base_url}")
        print(f"{'#' * 70}")

        for template_path in template_files:
            try:
                result = self.deploy_template(template_path)
                results.append(result)
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                results.append(
                    {
                        "success": False,
                        "template": template_path.name,
                        "error": str(e),
                    }
                )

        # Summary
        successful = sum(1 for r in results if r.get("success"))
        created = sum(1 for r in results if r.get("action") == "created")
        updated = sum(1 for r in results if r.get("action") == "updated")
        failed = len(results) - successful

        print(f"\n{'=' * 70}")
        print("DEPLOYMENT COMPLETE")
        print(f"{'=' * 70}")
        print(f"✅ Successful: {successful}/{len(results)}")
        print(f"   📝 Created: {created}")
        print(f"   🔄 Updated: {updated}")
        print(f"❌ Failed: {failed}")
        print(f"{'=' * 70}\n")

        return results


def main():
    """Deploy Elementor templates to WordPress."""
    # Get credentials
    wp_url = os.getenv("WORDPRESS_URL")
    wp_user = os.getenv("WORDPRESS_USER", "admin")
    wp_pass = os.getenv("WORDPRESS_APP_PASSWORD")

    if not wp_url or not wp_pass:
        print("❌ ERROR: WordPress credentials required")
        print("   Set environment variables:")
        print("   - WORDPRESS_URL=https://your-site.com")
        print("   - WORDPRESS_USER=admin (optional)")
        print("   - WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx")
        return

    # Initialize deployer
    deployer = ElementorDeployer(wp_url, wp_user, wp_pass)

    # Deploy all templates
    templates_dir = Path(__file__).parent.parent / "wordpress" / "elementor_templates"
    results = deployer.deploy_all(templates_dir)

    # Save results
    results_file = templates_dir / "deployment_results.json"
    with open(results_file, "w") as f:
        json.dump(
            {
                "wordpress_url": wp_url,
                "total": len(results),
                "successful": sum(1 for r in results if r.get("success")),
                "results": results,
            },
            f,
            indent=2,
        )

    print(f"💾 Results saved: {results_file}\n")


if __name__ == "__main__":
    main()
