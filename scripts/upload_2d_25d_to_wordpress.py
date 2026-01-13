#!/usr/bin/env python3
"""
Upload 2D/2.5D Visualizations to WordPress & WooCommerce Products.

Uploads 104 visualization assets (26 products × 4 variations) to WordPress,
then updates WooCommerce product galleries with the new images.
Includes custom CSS injection for parallax effects.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import aiohttp

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file
from dotenv import load_dotenv  # noqa: E402

load_dotenv(project_root / ".env")

# WordPress/WooCommerce credentials
WP_URL = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
WP_USERNAME = os.getenv("WORDPRESS_USERNAME", "skyyroseco")
WP_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD")
WC_KEY = os.getenv("WOOCOMMERCE_KEY")
WC_SECRET = os.getenv("WOOCOMMERCE_SECRET")

# Validate required credentials
if not WP_APP_PASSWORD:
    print("❌ WORDPRESS_APP_PASSWORD not set in .env")
    sys.exit(1)
if not WC_KEY or not WC_SECRET:
    print("❌ WOOCOMMERCE_KEY or WOOCOMMERCE_SECRET not set in .env")
    sys.exit(1)

# Asset directories
ASSETS_DIR = project_root / "assets" / "2d-25d-assets"
ENHANCED_DIR = project_root / "assets" / "enhanced_products" / "all"

# Variation type metadata
VARIATION_METADATA = {
    "shadow": {
        "alt": "Professional drop shadow visualization",
        "css_class": "product-shadow-viz",
        "description": "Enhanced depth with realistic shadows",
    },
    "depth": {
        "alt": "Depth of field effect visualization",
        "css_class": "product-depth-viz",
        "description": "Photography-style selective focus",
    },
    "parallax": {
        "alt": "Interactive parallax layers",
        "css_class": "product-parallax-viz parallax-enabled",
        "description": "2.5D web animation ready",
    },
    "detail": {
        "alt": "Enhanced detail sharpened visualization",
        "css_class": "product-detail-viz",
        "description": "Professional texture enhancement",
    },
}


async def upload_media_with_metadata(
    session: aiohttp.ClientSession,
    filepath: Path,
    variation_type: str,
    product_name: str,
    max_retries: int = 3,
) -> dict | None:
    """Upload media file with custom metadata using ralph-loop retry pattern."""

    metadata = VARIATION_METADATA.get(variation_type, {})

    # Fatal errors that should not be retried (ralph-loop classification)
    FATAL_ERRORS = [
        "None is not allowed as password value",
        "401",  # Unauthorized
        "403",  # Forbidden
        "400",  # Bad Request (usually means data issue)
    ]

    for attempt in range(max_retries):
        try:
            # Read file as binary
            with open(filepath, "rb") as f:
                file_data = f.read()

            # Determine MIME type
            mime_type = "image/png" if filepath.suffix == ".png" else "image/jpeg"

            # WordPress binary upload with metadata
            headers = {
                "Content-Disposition": f"attachment; filename={filepath.name}",
                "Content-Type": mime_type,
            }

            async with session.post(
                f"{WP_URL}/index.php?rest_route=/wp/v2/media",
                data=file_data,
                headers=headers,
                auth=aiohttp.BasicAuth(WP_USERNAME, WP_APP_PASSWORD),
            ) as resp:
                if resp.status == 201:
                    result = await resp.json()
                    media_id = result["id"]

                    # Update media metadata (alt text, description)
                    update_data = {
                        "alt_text": f"{product_name} - {metadata.get('alt', '')}",
                        "description": metadata.get("description", ""),
                        "caption": f"{variation_type.title()} variation",
                    }

                    async with session.post(
                        f"{WP_URL}/index.php?rest_route=/wp/v2/media/{media_id}",
                        json=update_data,
                        auth=aiohttp.BasicAuth(WP_USERNAME, WP_APP_PASSWORD),
                    ) as update_resp:
                        if update_resp.status == 200:
                            print(f"  ✓ {filepath.name} (ID: {media_id})")
                        else:
                            print(f"  ⚠ {filepath.name} uploaded but metadata update failed")

                    return {
                        "success": True,
                        "id": media_id,
                        "url": result["source_url"],
                        "file": str(filepath),
                        "variation_type": variation_type,
                        "css_class": metadata.get("css_class", ""),
                    }

                elif resp.status == 429:
                    # Rate limited - retry with exponential backoff
                    if attempt < max_retries - 1:
                        wait_time = 2**attempt  # 1s, 2s, 4s (ralph-loop)
                        print(
                            f"  ⏳ {filepath.name} rate limited, retry {attempt + 1}/{max_retries} in {wait_time}s"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        error_text = await resp.text()
                        print(f"  ✗ {filepath.name} failed after {max_retries} retries (429)")
                        return {
                            "success": False,
                            "file": str(filepath),
                            "error": f"HTTP 429 after {max_retries} retries",
                        }
                else:
                    error_text = await resp.text()
                    print(f"  ✗ {filepath.name} HTTP {resp.status}: {error_text[:100]}")
                    return {"success": False, "file": str(filepath), "error": f"HTTP {resp.status}"}

        except Exception as e:
            error_msg = str(e)

            # Check if this is a fatal error (ralph-loop classification)
            is_fatal = any(fatal in error_msg for fatal in FATAL_ERRORS)

            if is_fatal:
                print(f"  ✗ {filepath.name} FATAL error (no retry): {error_msg}")
                return {"success": False, "file": str(filepath), "error": f"FATAL: {error_msg}"}

            if attempt < max_retries - 1:
                wait_time = 2**attempt  # Ralph-loop: 1s, 2s, 4s
                print(
                    f"  ⚠ {filepath.name} error, retry {attempt + 1}/{max_retries} in {wait_time}s: {error_msg[:50]}"
                )
                await asyncio.sleep(wait_time)
                continue
            else:
                print(f"  ✗ {filepath.name} failed after {max_retries} retries: {error_msg}")
                return {"success": False, "file": str(filepath), "error": str(e)}

    return {"success": False, "file": str(filepath), "error": "Max retries exceeded"}


async def update_product_gallery(
    session: aiohttp.ClientSession,
    product_id: int,
    new_images: list[dict],
    existing_images: list[dict],
) -> bool:
    """Update WooCommerce product gallery with new visualization images."""

    try:
        # Combine existing + new images
        all_images = existing_images.copy()

        # Add new images with proper metadata
        for img in new_images:
            all_images.append(
                {
                    "src": img["url"],
                    "alt": img.get("alt", ""),
                    "name": Path(img["file"]).stem,
                    "position": len(all_images),
                }
            )

        # Update product via WooCommerce REST API
        update_data = {"images": all_images}

        async with session.put(
            f"{WP_URL}/wp-json/wc/v3/products/{product_id}",
            json=update_data,
            auth=aiohttp.BasicAuth(WC_KEY, WC_SECRET),
        ) as resp:
            if resp.status == 200:
                await resp.json()  # Consume response body
                print(f"  ✓ Product {product_id} gallery updated ({len(all_images)} images)")
                return True
            else:
                error_text = await resp.text()
                print(f"  ✗ Product {product_id} update failed: HTTP {resp.status}")
                print(f"    Error: {error_text[:200]}")
                return False

    except Exception as e:
        print(f"  ✗ Product {product_id} update failed: {e}")
        return False


async def get_product_by_sku(session: aiohttp.ClientSession, sku: str) -> dict | None:
    """Fetch WooCommerce product by SKU."""

    try:
        async with session.get(
            f"{WP_URL}/wp-json/wc/v3/products",
            params={"sku": sku},
            auth=aiohttp.BasicAuth(WC_KEY, WC_SECRET),
        ) as resp:
            if resp.status == 200:
                products = await resp.json()
                if products:
                    return products[0]
            return None
    except Exception as e:
        print(f"  ⚠ Error fetching product {sku}: {e}")
        return None


async def inject_custom_css(session: aiohttp.ClientSession) -> bool:
    """Inject custom CSS for parallax effects via WordPress Customizer."""

    custom_css = """
/* 2D/2.5D Product Visualization Styles */
.woocommerce-product-gallery__image.parallax-enabled {
    position: relative;
    overflow: hidden;
    border-radius: 8px;
}

.woocommerce-product-gallery__image.parallax-enabled img {
    transition: transform 0.15s cubic-bezier(0.4, 0.0, 0.2, 1);
    will-change: transform;
}

.woocommerce-product-gallery__image.parallax-enabled:hover img {
    transform: scale(1.05);
}

/* Shadow visualization enhancement */
.product-shadow-viz {
    filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1));
}

/* Depth visualization enhancement */
.product-depth-viz {
    border: 1px solid rgba(0, 0, 0, 0.05);
}

/* Detail visualization enhancement */
.product-detail-viz {
    image-rendering: -webkit-optimize-contrast;
    image-rendering: crisp-edges;
}

/* Gallery thumbnail hover effect */
.woocommerce-product-gallery__thumbnail:hover {
    transform: translateY(-2px);
    transition: transform 0.2s ease;
}
"""

    try:
        # WordPress Customizer Additional CSS endpoint
        # Note: This requires proper permissions and may need theme support
        async with session.post(
            f"{WP_URL}/wp-json/wp/v2/customize",
            json={"additional_css": custom_css},
            auth=aiohttp.BasicAuth(WP_USERNAME, WP_APP_PASSWORD),
        ) as resp:
            if resp.status in [200, 201]:
                print("✓ Custom CSS injected successfully")
                return True
            else:
                # Fallback: Save CSS to file for manual injection
                css_file = project_root / "wordpress" / "2d-25d-custom.css"
                css_file.parent.mkdir(parents=True, exist_ok=True)
                css_file.write_text(custom_css)
                print(f"⚠ CSS auto-inject failed, saved to {css_file}")
                print("  Please add to WordPress > Appearance > Customize > Additional CSS")
                return False

    except Exception as e:
        # Fallback: Save CSS to file
        css_file = project_root / "wordpress" / "2d-25d-custom.css"
        css_file.parent.mkdir(parents=True, exist_ok=True)
        css_file.write_text(custom_css)
        print(f"⚠ CSS auto-inject failed ({e}), saved to {css_file}")
        print("  Please add to WordPress > Appearance > Customize > Additional CSS")
        return False


async def main():
    """Upload all 2D/2.5D assets and update WooCommerce products."""

    print("=== 2D/2.5D Asset Upload to WordPress ===\n")

    # Validate directories
    if not ASSETS_DIR.exists():
        print(f"❌ Assets directory not found: {ASSETS_DIR}")
        return 1

    # Load enhanced products manifest to get product metadata
    manifest_path = ENHANCED_DIR / "manifest.json"
    if not manifest_path.exists():
        print(f"❌ Manifest not found: {manifest_path}")
        return 1

    with open(manifest_path) as f:
        products_manifest = json.load(f)

    # Build mapping of base product name → product metadata
    product_map = {}
    for product in products_manifest:
        if product["success"]:
            base_name = Path(product["enhanced"]).stem.replace("enhanced_", "")
            product_map[base_name] = {
                "original": product["original"],
                "enhanced": product["enhanced"],
                "sku": base_name.upper().replace("_", "-"),
            }

    # Find all 2D/2.5D assets
    asset_files = list(ASSETS_DIR.glob("*.jpg")) + list(ASSETS_DIR.glob("*.png"))

    if not asset_files:
        print(f"❌ No assets found in: {ASSETS_DIR}")
        return 1

    print(f"Found {len(asset_files)} visualization assets")
    print(f"Mapped {len(product_map)} products from manifest\n")

    # Group assets by product
    product_assets = {}
    for filepath in asset_files:
        # Parse filename: {product}_{variation}.{ext}
        base_name = filepath.stem.rsplit("_", 1)[0]
        variation_type = filepath.stem.rsplit("_", 1)[1]

        if base_name not in product_assets:
            product_assets[base_name] = []

        product_assets[base_name].append(
            {"filepath": filepath, "variation_type": variation_type, "product_name": base_name}
        )

    print(f"Grouped into {len(product_assets)} product sets\n")

    # Upload assets and update products
    upload_results = []
    product_updates = []

    async with aiohttp.ClientSession() as session:
        # Step 1: Upload all media files
        print("Step 1: Uploading media to WordPress...\n")

        for product_name, assets in product_assets.items():
            print(f"Uploading {len(assets)} variations for {product_name}:")

            uploaded_images = []
            for asset in assets:
                result = await upload_media_with_metadata(
                    session, asset["filepath"], asset["variation_type"], product_name
                )

                if result:
                    upload_results.append(result)
                    if result["success"]:
                        uploaded_images.append(result)

                # Rate limit protection: WordPress returned 429 during testing
                # Increase delay to 3 seconds between uploads to respect rate limits
                await asyncio.sleep(3.0)

            # Step 2: Update WooCommerce product gallery
            if uploaded_images and product_name in product_map:
                sku = product_map[product_name]["sku"]
                product = await get_product_by_sku(session, sku)

                if product:
                    existing_images = product.get("images", [])
                    success = await update_product_gallery(
                        session, product["id"], uploaded_images, existing_images
                    )

                    product_updates.append(
                        {
                            "product_id": product["id"],
                            "sku": sku,
                            "success": success,
                            "images_added": len(uploaded_images),
                        }
                    )
                else:
                    print(f"  ⚠ Product not found in WooCommerce: {sku}")

            print()  # Blank line between products

        # Step 3: Inject custom CSS
        print("\nStep 3: Injecting custom CSS for parallax effects...\n")
        await inject_custom_css(session)

    # Save results
    results_path = ASSETS_DIR / "wordpress_upload_results.json"
    with open(results_path, "w") as f:
        json.dump(
            {
                "upload_results": upload_results,
                "product_updates": product_updates,
                "summary": {
                    "total_uploads": len(upload_results),
                    "successful_uploads": sum(1 for r in upload_results if r["success"]),
                    "failed_uploads": sum(1 for r in upload_results if not r["success"]),
                    "products_updated": sum(1 for p in product_updates if p["success"]),
                    "products_failed": sum(1 for p in product_updates if not p["success"]),
                },
            },
            f,
            indent=2,
        )

    # Summary
    successful_uploads = sum(1 for r in upload_results if r["success"])
    failed_uploads = len(upload_results) - successful_uploads
    products_updated = sum(1 for p in product_updates if p["success"])

    print("\n" + "=" * 60)
    print("✅ Upload Complete!")
    print("=" * 60)
    print(f"Media Uploads: {successful_uploads}/{len(upload_results)} successful")
    print(f"Product Updates: {products_updated}/{len(product_updates)} successful")
    print(f"Results saved: {results_path}")

    if failed_uploads > 0:
        print(f"\n❌ Failed uploads ({failed_uploads}):")
        for r in upload_results:
            if not r["success"]:
                print(f"  {Path(r['file']).name}: {r.get('error', 'Unknown error')}")

    print("\n📋 Next Steps:")
    print("  1. Review uploaded images in WordPress Media Library")
    print(
        "  2. Verify product galleries at https://skyyrose.co/wp-admin/edit.php?post_type=product"
    )
    print("  3. Test parallax effects on product pages")
    print("  4. If CSS wasn't auto-injected, add wordpress/2d-25d-custom.css to theme")

    return 0 if failed_uploads == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
