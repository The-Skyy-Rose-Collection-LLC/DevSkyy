#!/usr/bin/env python3
"""
Import products from CSV to WooCommerce.

Revenue-critical script for SkyyRose product setup.
"""

import asyncio
import csv
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from sync.woocommerce_sync import WooCommerceSyncClient


# Category IDs from WordPress (verified)
CATEGORY_IDS = {
    "signature": 19,
    "black rose": 20,
    "love hurts": 18,
}


def parse_category(category_str: str) -> list[dict]:
    """Parse category string to WooCommerce format."""
    categories = []
    cat_lower = category_str.lower()

    if "signature" in cat_lower:
        categories.append({"id": CATEGORY_IDS["signature"]})
    elif "black rose" in cat_lower or "black_rose" in cat_lower:
        categories.append({"id": CATEGORY_IDS["black rose"]})
    elif "love hurts" in cat_lower or "love_hurts" in cat_lower:
        categories.append({"id": CATEGORY_IDS["love hurts"]})

    return categories


def parse_attributes(row: dict) -> list[dict]:
    """Parse size and color attributes."""
    attributes = []

    # Size attribute
    if row.get("Attribute 1 name") == "Size" and row.get("Attribute 1 value(s)"):
        sizes = [s.strip() for s in row["Attribute 1 value(s)"].split(",")]
        attributes.append({
            "name": "Size",
            "options": sizes,
            "visible": True,
            "variation": True,
        })

    # Color attribute
    if row.get("Attribute 2 name") == "Color" and row.get("Attribute 2 value(s)"):
        colors = [c.strip() for c in row["Attribute 2 value(s)"].split(",")]
        attributes.append({
            "name": "Color",
            "options": colors,
            "visible": True,
            "variation": True,
        })

    return attributes


def parse_tags(tags_str: str) -> list[dict]:
    """Parse tags string to WooCommerce format."""
    if not tags_str:
        return []
    return [{"name": tag.strip()} for tag in tags_str.split(",")]


async def import_products():
    """Import products from CSV to WooCommerce."""
    csv_path = Path(__file__).parent.parent / "wordpress" / "woocommerce-products-import.csv"

    if not csv_path.exists():
        print(f"CSV not found: {csv_path}")
        return

    print(f"Reading products from: {csv_path}")

    client = WooCommerceSyncClient()
    created = 0
    updated = 0
    errors = 0

    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                sku = row.get("SKU", "").strip()
                name = row.get("Name", "").strip()

                if not name or not sku:
                    continue

                print(f"\nProcessing: {name} ({sku})")

                # Build product data
                product_data = {
                    "name": name,
                    "type": row.get("Type", "simple"),
                    "status": "publish",  # Publish immediately for revenue
                    "featured": row.get("Is featured?") == "1",
                    "catalog_visibility": row.get("Visibility in catalog", "visible"),
                    "description": row.get("Description", ""),
                    "short_description": row.get("Short description", ""),
                    "sku": sku,
                    "regular_price": row.get("Regular price", "0"),
                    "sale_price": row.get("Sale price", ""),
                    "manage_stock": row.get("In stock?") == "1",
                    "stock_quantity": int(row.get("Stock", 0)) if row.get("Stock") else None,
                    "categories": parse_category(row.get("Categories", "")),
                    "tags": parse_tags(row.get("Tags", "")),
                    "attributes": parse_attributes(row),
                    "meta_data": [
                        {"key": "_skyyrose_collection", "value": row.get("Categories", "").split(">")[-1].strip() if row.get("Categories") else ""},
                        {"key": "_skyyrose_3d_enabled", "value": "yes"},
                    ],
                }

                # Remove empty values
                product_data = {k: v for k, v in product_data.items() if v not in [None, "", []]}

                try:
                    # Check if product exists
                    existing = await client.get_product_by_sku(sku)

                    if existing:
                        # Update existing product
                        result = await client.update_product(existing["id"], product_data)
                        print(f"  Updated: {result['permalink']}")
                        updated += 1
                    else:
                        # Create new product
                        result = await client.create_product(product_data)
                        print(f"  Created: {result['permalink']}")
                        created += 1

                except Exception as e:
                    print(f"  ERROR: {e}")
                    errors += 1

    finally:
        await client.close()

    print(f"\n{'='*50}")
    print(f"Import Complete!")
    print(f"  Created: {created}")
    print(f"  Updated: {updated}")
    print(f"  Errors: {errors}")
    print(f"{'='*50}")

    # Verify products are live
    print(f"\nView products: https://skyyrose.co/shop/")


if __name__ == "__main__":
    asyncio.run(import_products())
