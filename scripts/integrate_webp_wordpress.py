#!/usr/bin/env python3
"""
WordPress WebP Integration Script

Uploads WebP-optimized product images to WordPress and configures
the theme to serve WebP with JPG fallback using <picture> tags.

Based on WordPress REST API documentation:
https://developer.wordpress.org/rest-api/reference/media/

Authentication:
    Requires Application Password (WordPress 5.6+)
    Generate: WordPress Admin → Users → Profile → Application Passwords

Troubleshooting:
    Run diagnostics first: python scripts/diagnose_wordpress_api.py

Usage:
    python scripts/integrate_webp_wordpress.py --webp-dir <dir> --fallback-dir <dir> [--limit N]

Example:
    python scripts/integrate_webp_wordpress.py \
        --webp-dir /tmp/webp_optimized/webp \
        --fallback-dir /tmp/webp_optimized/fallback \
        --limit 5
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# WordPress credentials
WP_URL = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
WP_USERNAME = os.getenv("WORDPRESS_USERNAME")
WP_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD")

if not all([WP_URL, WP_USERNAME, WP_APP_PASSWORD]):
    print("ERROR: WordPress credentials not found in environment")
    print("Required: WORDPRESS_URL, WORDPRESS_USERNAME, WORDPRESS_APP_PASSWORD")
    print("\nAdd to .env file:")
    print("  WORDPRESS_URL=https://skyyrose.co")
    print("  WORDPRESS_USERNAME=your_username")
    print("  WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx")
    print("\nGenerate Application Password:")
    print("  WordPress Admin → Users → Profile → Application Passwords → Add New")
    sys.exit(1)


class WordPressWebPIntegrator:
    """Handles WebP image upload and WordPress integration."""

    def __init__(self, webp_dir: Path, fallback_dir: Path):
        self.webp_dir = webp_dir
        self.fallback_dir = fallback_dir
        self.uploaded_webp: dict[str, dict] = {}
        self.uploaded_fallback: dict[str, dict] = {}

    async def upload_image(
        self, session: aiohttp.ClientSession, filepath: Path, alt_text: str = ""
    ) -> dict | None:
        """Upload single image to WordPress Media Library.

        Uses WordPress REST API media upload endpoint with Application Password authentication.
        Based on official WordPress REST API documentation:
        https://developer.wordpress.org/rest-api/reference/media/
        """
        try:
            with open(filepath, "rb") as f:
                file_data = f.read()

            # WordPress REST API media upload format (official docs)
            # Only Content-Disposition header required - WordPress detects MIME type automatically
            headers = {
                "Content-Disposition": f'attachment; filename="{filepath.name}"',
            }

            auth = aiohttp.BasicAuth(WP_USERNAME, WP_APP_PASSWORD)

            async with session.post(
                f"{WP_URL}/wp-json/wp/v2/media",
                data=file_data,
                headers=headers,
                auth=auth,
            ) as resp:
                # Check for HTML response (authentication redirect)
                content_type = resp.headers.get("Content-Type", "")

                if resp.status == 201:
                    result = await resp.json()
                    print(f"  ✓ Uploaded: {filepath.name} (ID: {result['id']})")
                    return result
                elif "text/html" in content_type:
                    # Got HTML instead of JSON - likely authentication issue
                    error_text = await resp.text()
                    print(
                        f"  ✗ Failed: {filepath.name} - Authentication error (got HTML, expected JSON)"
                    )
                    print(f"    Status: {resp.status}")
                    print("    Hint: Verify WordPress Application Password is correct")
                    print("    Run: python scripts/diagnose_wordpress_api.py")
                    return None
                else:
                    error_text = await resp.text()
                    print(f"  ✗ Failed: {filepath.name} ({resp.status})")
                    print(f"    Error: {error_text[:200]}")
                    return None

        except Exception as e:
            print(f"  ✗ Error uploading {filepath.name}: {e}")
            return None

    async def upload_image_pair(
        self, session: aiohttp.ClientSession, base_name: str
    ) -> tuple[dict | None, dict | None]:
        """Upload both WebP and fallback JPG for a single product."""
        webp_path = self.webp_dir / f"{base_name}.webp"
        fallback_path = self.fallback_dir / f"{base_name}.jpg"

        if not webp_path.exists():
            print(f"  ⚠ WebP not found: {webp_path}")
            return None, None

        if not fallback_path.exists():
            print(f"  ⚠ Fallback not found: {fallback_path}")
            return None, None

        print(f"\nProcessing: {base_name}")

        # Upload WebP
        webp_result = await self.upload_image(session, webp_path, f"{base_name} WebP")

        # Upload fallback
        fallback_result = await self.upload_image(session, fallback_path, f"{base_name} Fallback")

        return webp_result, fallback_result

    async def upload_batch(self, limit: int | None = None) -> None:
        """Upload all WebP + fallback pairs."""
        # Get list of base names from WebP directory
        webp_files = list(self.webp_dir.glob("*.webp"))

        if limit:
            webp_files = webp_files[:limit]

        base_names = [f.stem for f in webp_files]

        print(f"\n{'=' * 60}")
        print("WordPress WebP Integration")
        print(f"{'=' * 60}")
        print(f"WebP directory:     {self.webp_dir}")
        print(f"Fallback directory: {self.fallback_dir}")
        print(f"Images to process:  {len(base_names)}")
        print(f"WordPress URL:      {WP_URL}")
        print(f"{'=' * 60}\n")

        async with aiohttp.ClientSession() as session:
            for base_name in base_names:
                webp_result, fallback_result = await self.upload_image_pair(session, base_name)

                if webp_result:
                    self.uploaded_webp[base_name] = webp_result
                if fallback_result:
                    self.uploaded_fallback[base_name] = fallback_result

                # Rate limiting
                await asyncio.sleep(0.5)

        self.print_summary()

    def print_summary(self) -> None:
        """Print upload summary."""
        print(f"\n{'=' * 60}")
        print("Upload Summary")
        print(f"{'=' * 60}")
        print(f"WebP uploaded:     {len(self.uploaded_webp)}")
        print(f"Fallback uploaded: {len(self.uploaded_fallback)}")
        print("\nNext Steps:")
        print("1. Add WebP helper function to theme (see below)")
        print("2. Update product templates to use helper")
        print("3. Test on live site")
        print(f"{'=' * 60}\n")

        # Generate PHP helper function
        self.generate_php_helper()

    def generate_php_helper(self) -> None:
        """Generate PHP helper function for WordPress theme."""
        php_code = """
/**
 * SkyyRose WebP Image Helper
 *
 * Outputs <picture> tag with WebP + JPG fallback for optimal performance
 * Add this to wordpress/skyyrose-immersive/functions.php
 */
function skyyrose_webp_image($webp_id, $fallback_id, $alt = '', $class = '') {
    $webp_url = wp_get_attachment_url($webp_id);
    $fallback_url = wp_get_attachment_url($fallback_id);

    if (!$webp_url || !$fallback_url) {
        return '';
    }

    ob_start();
    ?>
    <picture class="<?php echo esc_attr($class); ?>">
        <source srcset="<?php echo esc_url($webp_url); ?>" type="image/webp">
        <img src="<?php echo esc_url($fallback_url); ?>"
             alt="<?php echo esc_attr($alt); ?>"
             loading="lazy"
             class="<?php echo esc_attr($class); ?>">
    </picture>
    <?php
    return ob_get_clean();
}

/**
 * Usage example in WooCommerce product template:
 *
 * <?php
 * echo skyyrose_webp_image(
 *     123,  // WebP attachment ID
 *     456,  // JPG fallback attachment ID
 *     'Product Name',
 *     'woocommerce-product-gallery__image'
 * );
 * ?>
 */
"""

        output_file = Path("wordpress/skyyrose-immersive/webp-helper.php")
        output_file.write_text(php_code)
        print(f"\n✓ Generated PHP helper: {output_file}")
        print("  Copy contents to wordpress/skyyrose-immersive/functions.php")

    def generate_image_mapping(self) -> None:
        """Generate JSON mapping of WebP IDs to fallback IDs."""
        mapping = {}

        for base_name in self.uploaded_webp:
            if base_name in self.uploaded_fallback:
                mapping[base_name] = {
                    "webp_id": self.uploaded_webp[base_name]["id"],
                    "webp_url": self.uploaded_webp[base_name]["source_url"],
                    "fallback_id": self.uploaded_fallback[base_name]["id"],
                    "fallback_url": self.uploaded_fallback[base_name]["source_url"],
                }

        import json

        output_file = Path("wordpress/webp_image_mapping.json")
        output_file.write_text(json.dumps(mapping, indent=2))
        print(f"✓ Generated mapping: {output_file}")
        print("  Use this to update product galleries programmatically")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Upload WebP-optimized images to WordPress")
    parser.add_argument("--webp-dir", type=Path, required=True, help="Directory with WebP images")
    parser.add_argument(
        "--fallback-dir",
        type=Path,
        required=True,
        help="Directory with JPG fallback images",
    )
    parser.add_argument("--limit", type=int, help="Limit number of images to upload (for testing)")

    args = parser.parse_args()

    if not args.webp_dir.exists():
        print(f"ERROR: WebP directory not found: {args.webp_dir}")
        sys.exit(1)

    if not args.fallback_dir.exists():
        print(f"ERROR: Fallback directory not found: {args.fallback_dir}")
        sys.exit(1)

    integrator = WordPressWebPIntegrator(args.webp_dir, args.fallback_dir)
    await integrator.upload_batch(limit=args.limit)
    integrator.generate_image_mapping()


if __name__ == "__main__":
    asyncio.run(main())
