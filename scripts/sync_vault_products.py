#!/usr/bin/env python3
"""
Sync Vault Pre-Order Products to WooCommerce
Creates and updates products with custom Vault meta fields
"""

import asyncio
import base64
import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

# WordPress Configuration
WP_URL = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
WP_CONSUMER_KEY = os.getenv("WOO_CONSUMER_KEY")
WP_CONSUMER_SECRET = os.getenv("WOO_CONSUMER_SECRET")

# Vault Products Data
VAULT_PRODUCTS = [
    {
        "name": "The Prototype",
        "price": "500.00",
        "sku": "VAULT-PROTO-001",
        "description": "Limited edition prototype design. First of its kind.",
        "short_description": "Exclusive prototype - Only 50 available",
        "vault_badge": "ENCRYPTED",
        "vault_quantity_limit": "50",
        "vault_icon": "🔐",
        "stock_quantity": 50,
        "categories": ["Pre-Order", "Vault"],
        "tags": ["exclusive", "limited-edition", "prototype"],
        "manage_stock": True,
        "status": "publish",
    },
    {
        "name": "Mystery Box",
        "price": "250.00",
        "sku": "VAULT-MYSTERY-001",
        "description": "Curated selection of SkyyRose items. Contents unknown until delivery.",
        "short_description": "Surprise yourself with exclusive SkyyRose items",
        "vault_badge": "ARCHIVE",
        "vault_quantity_limit": "",  # Unlimited
        "vault_icon": "📦",
        "stock_quantity": 9999,
        "categories": ["Pre-Order", "Vault"],
        "tags": ["mystery-box", "surprise"],
        "manage_stock": False,
        "status": "publish",
    },
    {
        "name": "Crystal Rose",
        "price": "1200.00",
        "sku": "VAULT-CRYSTAL-001",
        "description": "Hand-crafted crystal rose sculpture. Luxury collector's item.",
        "short_description": "Ultra-rare crystal rose - Only 10 made",
        "vault_badge": "LIMITED",
        "vault_quantity_limit": "10",
        "vault_icon": "💎",
        "stock_quantity": 10,
        "categories": ["Pre-Order", "Vault", "Luxury"],
        "tags": ["luxury", "crystal", "collectors-item"],
        "manage_stock": True,
        "status": "publish",
    },
]


class WooCommerceVaultSync:
    """Sync Vault products to WooCommerce"""

    def __init__(self, base_url: str, consumer_key: str, consumer_secret: str):
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/wp-json/wc/v3"

        # Basic Auth for WooCommerce
        auth_str = f"{consumer_key}:{consumer_secret}"
        self.auth = base64.b64encode(auth_str.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {self.auth}",
            "Content-Type": "application/json",
        }

    async def create_category(self, name: str) -> int:
        """Create or get category ID"""
        async with httpx.AsyncClient() as client:
            # Check if exists
            response = await client.get(
                f"{self.api_url}/products/categories",
                headers=self.headers,
                params={"search": name},
            )
            categories = response.json()

            if categories:
                print(f"Category '{name}' already exists (ID: {categories[0]['id']})")
                return categories[0]["id"]

            # Create new
            response = await client.post(
                f"{self.api_url}/products/categories",
                headers=self.headers,
                json={"name": name, "slug": name.lower().replace(" ", "-")},
            )
            category = response.json()
            print(f"Created category '{name}' (ID: {category['id']})")
            return category["id"]

    async def create_tag(self, name: str) -> int:
        """Create or get tag ID"""
        async with httpx.AsyncClient() as client:
            # Check if exists
            response = await client.get(
                f"{self.api_url}/products/tags",
                headers=self.headers,
                params={"search": name},
            )
            tags = response.json()

            if tags:
                return tags[0]["id"]

            # Create new
            response = await client.post(
                f"{self.api_url}/products/tags",
                headers=self.headers,
                json={"name": name, "slug": name.lower().replace(" ", "-")},
            )
            tag = response.json()
            return tag["id"]

    async def find_product_by_sku(self, sku: str) -> dict[str, Any] | None:
        """Find existing product by SKU"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/products",
                headers=self.headers,
                params={"sku": sku},
            )
            products = response.json()
            return products[0] if products else None

    async def create_or_update_product(self, product_data: dict[str, Any]) -> dict[str, Any]:
        """Create or update a WooCommerce product"""
        # Get category IDs
        category_ids = []
        for cat_name in product_data.get("categories", []):
            cat_id = await self.create_category(cat_name)
            category_ids.append({"id": cat_id})

        # Get tag IDs
        tag_ids = []
        for tag_name in product_data.get("tags", []):
            tag_id = await self.create_tag(tag_name)
            tag_ids.append({"id": tag_id})

        # Build product payload
        payload = {
            "name": product_data["name"],
            "type": "simple",
            "regular_price": product_data["price"],
            "description": product_data["description"],
            "short_description": product_data["short_description"],
            "sku": product_data["sku"],
            "manage_stock": product_data.get("manage_stock", True),
            "stock_quantity": product_data.get("stock_quantity", 0),
            "status": product_data.get("status", "draft"),
            "categories": category_ids,
            "tags": tag_ids,
            "meta_data": [
                {"key": "_vault_preorder", "value": "1"},
                {"key": "_vault_badge", "value": product_data.get("vault_badge", "ENCRYPTED")},
                {
                    "key": "_vault_quantity_limit",
                    "value": product_data.get("vault_quantity_limit", ""),
                },
                {"key": "_vault_icon", "value": product_data.get("vault_icon", "🔐")},
                {"key": "_vault_quantity_sold", "value": "0"},
                {"key": "_skyyrose_collection", "value": "vault"},
            ],
        }

        # Check if product exists
        existing = await self.find_product_by_sku(product_data["sku"])

        async with httpx.AsyncClient(timeout=30.0) as client:
            if existing:
                # Update existing product
                response = await client.put(
                    f"{self.api_url}/products/{existing['id']}",
                    headers=self.headers,
                    json=payload,
                )
                print(f"✓ Updated: {product_data['name']} (ID: {existing['id']})")
            else:
                # Create new product
                response = await client.post(
                    f"{self.api_url}/products", headers=self.headers, json=payload
                )
                print(f"✓ Created: {product_data['name']} (ID: {response.json()['id']})")

            response.raise_for_status()
            return response.json()

    async def sync_all_products(self):
        """Sync all Vault products"""
        print(f"\n🔐 Syncing {len(VAULT_PRODUCTS)} Vault products to WooCommerce...")
        print(f"Target: {self.base_url}\n")

        for product_data in VAULT_PRODUCTS:
            try:
                await self.create_or_update_product(product_data)
            except Exception as e:
                print(f"✗ Error syncing {product_data['name']}: {e}")

        print("\n✓ Sync complete!")


async def main():
    """Main entry point"""
    if not WP_CONSUMER_KEY or not WP_CONSUMER_SECRET:
        print("❌ Error: WooCommerce credentials not found in .env")
        print("Required: WOO_CONSUMER_KEY, WOO_CONSUMER_SECRET")
        return

    syncer = WooCommerceVaultSync(WP_URL, WP_CONSUMER_KEY, WP_CONSUMER_SECRET)
    await syncer.sync_all_products()


if __name__ == "__main__":
    asyncio.run(main())
