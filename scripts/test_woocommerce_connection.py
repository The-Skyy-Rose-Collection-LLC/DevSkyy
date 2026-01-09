#!/usr/bin/env python3
"""
Test WooCommerce API Connection
================================

Simple script to test connection to WooCommerce API using real credentials.

Usage:
    python scripts/test_woocommerce_connection.py

Environment Variables Required:
- WORDPRESS_URL
- WOOCOMMERCE_KEY
- WOOCOMMERCE_SECRET
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from integrations.wordpress_client import WordPressWooCommerceClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_connection():
    """Test WooCommerce API connection."""
    print("\n" + "=" * 80)
    print("WooCommerce API Connection Test")
    print("=" * 80 + "\n")

    # Check environment variables
    required_vars = ["WORDPRESS_URL", "WOOCOMMERCE_KEY", "WOOCOMMERCE_SECRET"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set the following in your .env file:")
        print("  WORDPRESS_URL=https://skyyrose.co")
        print("  WOOCOMMERCE_KEY=your_consumer_key")
        print("  WOOCOMMERCE_SECRET=your_consumer_secret")
        return False

    print("Configuration:")
    print(f"  Site URL: {os.getenv('WORDPRESS_URL')}")
    print(f"  Consumer Key: {os.getenv('WOOCOMMERCE_KEY')[:10]}...")
    print(f"  Consumer Secret: {'*' * 20}")
    print()

    try:
        # Create client
        print("Creating WordPress/WooCommerce client...")
        async with WordPressWooCommerceClient() as client:
            print("  ✓ Client created\n")

            # Test connection
            print("Testing API connection...")
            result = await client.test_connection()

            if result.get("success"):
                print("  ✓ Connection successful!\n")
                print("Connection Details:")
                print(f"  Site URL: {result.get('site_url')}")
                print(f"  WooCommerce API: {'✓' if result.get('woocommerce_connected') else '✗'}")
                print(f"  Products Count: {result.get('products_count', 'N/A')}")
                print()
            else:
                print("  ✗ Connection failed\n")
                print(f"Error: {result.get('error')}")
                return False

            # Test listing products
            print("Testing product listing...")
            products = await client.list_products(per_page=5)
            print(f"  ✓ Found {len(products)} products\n")

            if products:
                print("Sample Products:")
                for i, product in enumerate(products[:3], 1):
                    print(f"  {i}. {product.name}")
                    print(f"     SKU: {product.sku or 'N/A'}")
                    print(f"     Price: ${product.regular_price}")
                    print(f"     Status: {product.status}")
                    print(f"     Stock: {product.stock_quantity or 'N/A'}")
                    print()

            # Test listing orders
            print("Testing order listing...")
            orders = await client.list_orders(per_page=5)
            print(f"  ✓ Found {len(orders)} recent orders\n")

            if orders:
                print("Recent Orders:")
                for i, order in enumerate(orders[:3], 1):
                    print(f"  {i}. Order #{order.id}")
                    print(f"     Status: {order.status}")
                    print(f"     Total: ${order.total} {order.currency}")
                    print(f"     Date: {order.date_created}")
                    print()

            # Test listing customers
            print("Testing customer listing...")
            customers = await client.list_customers(per_page=5)
            print(f"  ✓ Found {len(customers)} customers\n")

            print("=" * 80)
            print("SUCCESS: All tests passed!")
            print("=" * 80 + "\n")
            return True

    except Exception as e:
        print(f"\n✗ ERROR: {e}\n")
        logger.exception("Connection test failed")
        return False


async def test_product_creation():
    """Test creating a test product."""
    print("\n" + "=" * 80)
    print("Test Product Creation (Optional)")
    print("=" * 80 + "\n")

    response = input("Do you want to create a test product? (y/N): ")
    if response.lower() != "y":
        print("Skipping product creation")
        return

    from integrations.wordpress_client import ProductStatus, WooCommerceProduct

    async with WordPressWooCommerceClient() as client:
        print("\nCreating test product...")

        product = WooCommerceProduct(
            name="DevSkyy Test Product",
            regular_price="99.99",
            description="<p>This is a test product created by the DevSkyy integration test.</p>",
            short_description="Test product for API integration",
            sku=f"TEST-DEVSKYY-{os.getpid()}",
            status=ProductStatus.DRAFT,
            stock_quantity=100,
            categories=[{"name": "Test"}],
            tags=[{"name": "test"}, {"name": "devskyy"}],
        )

        created = await client.create_product(product)

        print("  ✓ Product created successfully!\n")
        print("Product Details:")
        print(f"  ID: {created.id}")
        print(f"  Name: {created.name}")
        print(f"  SKU: {created.sku}")
        print(f"  Price: ${created.regular_price}")
        print(f"  Status: {created.status}")
        print(f"  Permalink: {created.permalink}")
        print()

        # Ask if should delete
        response = input("Delete test product? (Y/n): ")
        if response.lower() != "n":
            print("\nDeleting test product...")
            await client.delete_product(created.id, force=True)
            print("  ✓ Product deleted\n")


def main():
    """Main entry point."""
    try:
        # Run connection test
        success = asyncio.run(test_connection())

        if success:
            # Optionally test product creation
            asyncio.run(test_product_creation())

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        logger.exception("Test failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
