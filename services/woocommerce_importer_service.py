"""
WooCommerce Product Importer Service
Import products from WooCommerce into DevSkyy platform

Author: DevSkyy Enterprise Team
Date: 2025-11-10
"""

import logging
from typing import Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)


class WooCommerceImporter:
    """Service for importing products from WooCommerce"""

    def __init__(self, store_url: str, consumer_key: str, consumer_secret: str):
        """
        Initialize WooCommerce importer

        Args:
            store_url: WooCommerce store URL (e.g., https://shop.example.com)
            consumer_key: WooCommerce REST API consumer key
            consumer_secret: WooCommerce REST API consumer secret
        """
        self.store_url = store_url.rstrip("/")
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.api_url = f"{self.store_url}/wp-json/wc/v3"

    async def test_connection(self) -> bool:
        """
        Test WooCommerce API connection

        Returns:
            True if connection successful, False otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/system_status",
                    auth=(self.consumer_key, self.consumer_secret),
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"WooCommerce connection test failed: {e}")
            return False

    async def get_products(
        self,
        page: int = 1,
        per_page: int = 100,
        status: str = "publish"
    ) -> List[Dict]:
        """
        Get products from WooCommerce

        Args:
            page: Page number (default: 1)
            per_page: Products per page (default: 100, max: 100)
            status: Product status filter (publish, draft, pending)

        Returns:
            List of product dictionaries

        Raises:
            Exception: If API request fails
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/products",
                    auth=(self.consumer_key, self.consumer_secret),
                    params={
                        "page": page,
                        "per_page": min(per_page, 100),
                        "status": status
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"WooCommerce API error: {e.response.status_code}")
            raise Exception(f"Failed to fetch products: {e.response.text}")
        except Exception as e:
            logger.error(f"WooCommerce get_products error: {e}")
            raise

    async def import_product(self, wc_product: Dict) -> Dict:
        """
        Transform WooCommerce product to DevSkyy format

        Args:
            wc_product: WooCommerce product dictionary

        Returns:
            DevSkyy product dictionary ready for database insertion
        """
        try:
            # Extract product data
            product_data = {
                "name": wc_product.get("name", ""),
                "description": wc_product.get("description", ""),
                "sku": wc_product.get("sku", ""),
                "category": ", ".join([cat.get("name", "") for cat in wc_product.get("categories", [])]),
                "price": float(wc_product.get("price", 0)),
                "cost": 0.0,  # WooCommerce doesn't provide cost
                "stock_quantity": wc_product.get("stock_quantity", 0),
                "sizes": [attr.get("options", []) for attr in wc_product.get("attributes", []) if attr.get("name") == "Size"],
                "colors": [attr.get("options", []) for attr in wc_product.get("attributes", []) if attr.get("name") == "Color"],
                "images": [img.get("src") for img in wc_product.get("images", [])],
                "tags": [tag.get("name") for tag in wc_product.get("tags", [])],
                "seo_data": {
                    "meta_title": wc_product.get("meta_data", {}).get("_yoast_wpseo_title", ""),
                    "meta_description": wc_product.get("meta_data", {}).get("_yoast_wpseo_metadesc", ""),
                },
                "variants": [],  # Process variations separately
                "is_active": wc_product.get("status") == "publish",
            }

            return product_data

        except Exception as e:
            logger.error(f"Product import transformation error: {e}")
            raise

    async def import_all_products(self) -> Dict:
        """
        Import all products from WooCommerce

        Returns:
            Dict with import statistics (success_count, error_count, products)
        """
        stats = {
            "success_count": 0,
            "error_count": 0,
            "total_pages": 0,
            "products": []
        }

        try:
            page = 1
            has_more = True

            while has_more:
                wc_products = await self.get_products(page=page)

                if not wc_products:
                    has_more = False
                    break

                for wc_product in wc_products:
                    try:
                        product = await self.import_product(wc_product)
                        stats["products"].append(product)
                        stats["success_count"] += 1
                    except Exception as e:
                        logger.error(f"Failed to import product {wc_product.get('id')}: {e}")
                        stats["error_count"] += 1

                stats["total_pages"] = page
                page += 1

                # Check if there are more pages
                if len(wc_products) < 100:
                    has_more = False

            logger.info(f"WooCommerce import complete: {stats['success_count']} success, {stats['error_count']} errors")
            return stats

        except Exception as e:
            logger.error(f"Import all products error: {e}")
            raise


def get_woocommerce_importer(store_url: str, consumer_key: str, consumer_secret: str) -> WooCommerceImporter:
    """
    Factory function to create WooCommerce importer instance

    Args:
        store_url: WooCommerce store URL
        consumer_key: WooCommerce REST API consumer key
        consumer_secret: WooCommerce REST API consumer secret

    Returns:
        WooCommerceImporter instance
    """
    return WooCommerceImporter(store_url, consumer_key, consumer_secret)
