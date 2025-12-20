"""
WordPress 3D Media Sync Demo
============================

Demonstrates how to sync 3D assets with WooCommerce products.

Usage:
    python examples/wordpress_3d_sync_demo.py
"""

import asyncio
import os

from wordpress import WordPress3DMediaSync


async def demo_basic_sync():
    """Demo: Basic 3D model sync to a single product."""
    print("\n=== Demo: Basic 3D Model Sync ===\n")

    # Initialize sync client
    sync = WordPress3DMediaSync(
        wp_url=os.getenv("WP_SITE_URL", "https://skyyrose.com"),
        username=os.getenv("WP_USERNAME", "admin"),
        app_password=os.getenv("WP_APP_PASSWORD", ""),
    )

    async with sync:
        # Sync 3D model to product 123
        result = await sync.sync_3d_model(
            product_id=123,
            glb_url="https://cdn.skyyrose.com/models/black-rose-earrings.glb",
            usdz_url="https://cdn.skyyrose.com/models/black-rose-earrings.usdz",
            thumbnail_url="https://cdn.skyyrose.com/thumbnails/black-rose-earrings.jpg",
        )

        print(f"Synced product: {result['name']}")
        print(f"Product ID: {result['id']}")
        print(f"Status: {result['status']}")


async def demo_enable_ar():
    """Demo: Enable AR for a product."""
    print("\n=== Demo: Enable AR ===\n")

    sync = WordPress3DMediaSync(
        wp_url=os.getenv("WP_SITE_URL", "https://skyyrose.com"),
        username=os.getenv("WP_USERNAME", "admin"),
        app_password=os.getenv("WP_APP_PASSWORD", ""),
    )

    async with sync:
        # Enable AR for product
        result = await sync.enable_ar(product_id=123, enabled=True)
        print(f"AR enabled for product: {result['name']}")


async def demo_get_assets():
    """Demo: Get 3D assets for a product."""
    print("\n=== Demo: Get 3D Assets ===\n")

    sync = WordPress3DMediaSync(
        wp_url=os.getenv("WP_SITE_URL", "https://skyyrose.com"),
        username=os.getenv("WP_USERNAME", "admin"),
        app_password=os.getenv("WP_APP_PASSWORD", ""),
    )

    async with sync:
        # Get 3D assets
        assets = await sync.get_3d_assets(product_id=123)

        print(f"Product: {assets['product_name']}")
        print(f"GLB URL: {assets['glb_url']}")
        print(f"USDZ URL: {assets['usdz_url']}")
        print(f"AR Enabled: {assets['ar_enabled']}")
        print(f"Thumbnail: {assets['thumbnail_url']}")


async def demo_bulk_sync():
    """Demo: Bulk sync multiple products."""
    print("\n=== Demo: Bulk Sync ===\n")

    sync = WordPress3DMediaSync(
        wp_url=os.getenv("WP_SITE_URL", "https://skyyrose.com"),
        username=os.getenv("WP_USERNAME", "admin"),
        app_password=os.getenv("WP_APP_PASSWORD", ""),
    )

    # Prepare bulk sync data
    products = [
        {
            "product_id": 123,
            "glb_url": "https://cdn.skyyrose.com/models/black-rose-earrings.glb",
            "usdz_url": "https://cdn.skyyrose.com/models/black-rose-earrings.usdz",
            "thumbnail_url": "https://cdn.skyyrose.com/thumbnails/black-rose-earrings.jpg",
        },
        {
            "product_id": 124,
            "glb_url": "https://cdn.skyyrose.com/models/signature-necklace.glb",
            "usdz_url": "https://cdn.skyyrose.com/models/signature-necklace.usdz",
            "thumbnail_url": "https://cdn.skyyrose.com/thumbnails/signature-necklace.jpg",
        },
        {
            "product_id": 125,
            "glb_url": "https://cdn.skyyrose.com/models/love-hurts-ring.glb",
            "usdz_url": "https://cdn.skyyrose.com/models/love-hurts-ring.usdz",
            "thumbnail_url": "https://cdn.skyyrose.com/thumbnails/love-hurts-ring.jpg",
        },
    ]

    async with sync:
        results = await sync.bulk_sync(products)

        # Print summary
        success_count = sum(1 for r in results if r["status"] == "success")
        failed_count = sum(1 for r in results if r["status"] == "failed")

        print("\nBulk sync complete:")
        print(f"  Success: {success_count}/{len(results)}")
        print(f"  Failed: {failed_count}/{len(results)}")

        # Print details
        for result in results:
            status_icon = "✓" if result["status"] == "success" else "✗"
            print(f"  {status_icon} Product {result['product_id']}: {result['status']}")
            if result["status"] == "failed":
                print(f"    Error: {result.get('error', 'Unknown error')}")


async def demo_cleanup():
    """Demo: Cleanup orphaned 3D assets."""
    print("\n=== Demo: Cleanup Orphaned Assets ===\n")

    sync = WordPress3DMediaSync(
        wp_url=os.getenv("WP_SITE_URL", "https://skyyrose.com"),
        username=os.getenv("WP_USERNAME", "admin"),
        app_password=os.getenv("WP_APP_PASSWORD", ""),
    )

    async with sync:
        count = await sync.cleanup_orphaned_assets()
        print(f"Cleaned up {count} products with orphaned 3D assets")


async def demo_error_handling():
    """Demo: Error handling."""
    print("\n=== Demo: Error Handling ===\n")

    sync = WordPress3DMediaSync(
        wp_url=os.getenv("WP_SITE_URL", "https://skyyrose.com"),
        username=os.getenv("WP_USERNAME", "admin"),
        app_password=os.getenv("WP_APP_PASSWORD", ""),
    )

    async with sync:
        try:
            # Try to sync with invalid URL
            await sync.sync_3d_model(
                product_id=123,
                glb_url="invalid-url",  # Not a valid HTTP(S) URL
            )
        except Exception as e:
            print(f"Caught error: {type(e).__name__}: {e}")

        try:
            # Try to get assets for non-existent product
            await sync.get_3d_assets(product_id=999999)
        except Exception as e:
            print(f"Caught error: {type(e).__name__}: {e}")


async def main():
    """Run all demos."""
    print("WordPress 3D Media Sync Demo")
    print("=" * 50)

    # Check environment variables
    if not os.getenv("WP_SITE_URL") or not os.getenv("WP_APP_PASSWORD"):
        print("\n⚠️  Warning: Environment variables not set!")
        print("Please set WP_SITE_URL, WP_USERNAME, and WP_APP_PASSWORD")
        print("\nRunning in demo mode (will fail with actual API calls)")
        print("=" * 50)

    try:
        # Uncomment demos you want to run:

        # await demo_basic_sync()
        # await demo_enable_ar()
        # await demo_get_assets()
        # await demo_bulk_sync()
        # await demo_cleanup()
        await demo_error_handling()

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
