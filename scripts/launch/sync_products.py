"""Phase 2: Sync all 34 catalog products to WooCommerce.

Reads:
  - the canonical skyyrose-catalog.csv via skyyrose.core.catalog_loader (source of truth)
  - scripts/launch/sku_image_map.json (from Phase 1)

Uses WooCommerce REST API v3 with consumer key/secret auth.
Creates or updates products with images, prices, categories, and attributes.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import httpx

from skyyrose.core.catalog_loader import read_catalog_rows

ROOT = Path(__file__).resolve().parent.parent.parent
IMAGE_MAP_JSON = ROOT / "scripts" / "launch" / "sku_image_map.json"

# Load from .env or environment
SITE_URL = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
WC_KEY = os.getenv("WOOCOMMERCE_KEY", "")
WC_SECRET = os.getenv("WOOCOMMERCE_SECRET", "")

# WooCommerce category IDs (verified from API)
CATEGORY_MAP = {
    "signature": 19,
    "black-rose": 20,
    "love-hurts": 18,
}

# Will be created if missing
KIDS_CATEGORY_SLUG = "kids-capsule"


def load_env():
    """Load .env file if present."""
    env_path = ROOT / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())


def wc_request(
    method: str,
    endpoint: str,
    *,
    json_data: dict | None = None,
    params: dict | None = None,
) -> dict | list:
    """Make authenticated WooCommerce API request."""
    url = f"{SITE_URL}/wp-json/wc/v3/{endpoint}"
    auth = (WC_KEY, WC_SECRET)

    with httpx.Client(timeout=30.0) as client:
        response = client.request(
            method,
            url,
            auth=auth,
            json=json_data,
            params=params,
        )
        response.raise_for_status()
        return response.json()


def get_all_products() -> dict[str, dict]:
    """Get all existing WooCommerce products indexed by SKU."""
    products = {}
    page = 1
    while True:
        batch = wc_request("GET", "products", params={"per_page": 100, "page": page})
        if not batch:
            break
        for p in batch:
            if p.get("sku"):
                products[p["sku"]] = p
        page += 1
    return products


def ensure_kids_category() -> int:
    """Create Kids Capsule category if it doesn't exist. Return category ID."""
    categories = wc_request("GET", "products/categories", params={"per_page": 100})
    for cat in categories:
        if cat["slug"] == KIDS_CATEGORY_SLUG:
            return cat["id"]

    # Create it
    result = wc_request(
        "POST",
        "products/categories",
        json_data={
            "name": "Kids Capsule",
            "slug": KIDS_CATEGORY_SLUG,
            "description": "SkyyRose Kids — luxury starts young.",
        },
    )
    print(f"  Created Kids Capsule category (ID: {result['id']})")
    return result["id"]


def build_product_data(
    row: dict,
    image_info: dict | None,
    category_id: int,
) -> dict:
    """Build WooCommerce product payload from CSV row."""
    sku = row["sku"].strip().strip('"')
    name = row["name"].strip().strip('"')
    description = row.get("description", "").strip().strip('"')
    price = row["price"].strip().strip('"')
    sizes = (row.get("sizes") or "").strip().strip('"')
    color = (row.get("color") or "").strip().strip('"')
    is_preorder = (row.get("is_preorder") or "0").strip() == "1"
    edition_size = (row.get("edition_size") or "").strip().strip('"')

    data: dict = {
        "name": name,
        "slug": sku.lower(),
        "type": "simple",
        "status": "publish",
        "description": description,
        "short_description": description[:200] if description else f"{name} — SkyyRose Collection",
        "sku": sku,
        "regular_price": str(price),
        "manage_stock": False,
        "in_stock": True,
        "categories": [{"id": category_id}],
        "attributes": [],
    }

    # Add size attribute
    if sizes:
        size_list = [s.strip() for s in sizes.split("|") if s.strip()]
        if size_list:
            data["attributes"].append(
                {
                    "name": "Size",
                    "visible": True,
                    "options": size_list,
                }
            )

    # Add color attribute
    if color:
        data["attributes"].append(
            {
                "name": "Color",
                "visible": True,
                "options": [color],
            }
        )

    # Add image
    if image_info:
        data["images"] = [{"id": image_info["image_id"]}]

    # Add meta for preorder and edition size
    meta_data = []
    if is_preorder:
        meta_data.append({"key": "_skyyrose_preorder", "value": "yes"})
    if edition_size:
        meta_data.append({"key": "_skyyrose_edition_size", "value": edition_size})
    if meta_data:
        data["meta_data"] = meta_data

    return data


def sync_all():
    """Sync all catalog products to WooCommerce."""
    load_env()

    global WC_KEY, WC_SECRET, SITE_URL
    WC_KEY = os.getenv("WOOCOMMERCE_KEY", WC_KEY)
    WC_SECRET = os.getenv("WOOCOMMERCE_SECRET", WC_SECRET)
    SITE_URL = os.getenv("WORDPRESS_URL", SITE_URL)

    if not WC_KEY or not WC_SECRET:
        print("ERROR: WOOCOMMERCE_KEY and WOOCOMMERCE_SECRET required")
        sys.exit(1)

    # Load image mapping
    with open(IMAGE_MAP_JSON) as f:
        image_map: dict[str, dict] = json.load(f)

    # Load catalog (canonical CSV via the shared, memoized loader)
    products: list[dict] = list(read_catalog_rows())

    print(f"Catalog: {len(products)} products")
    print(f"Images:  {len(image_map)} mapped")
    print(f"Site:    {SITE_URL}")
    print()

    # Get existing products
    print("Fetching existing WooCommerce products...")
    existing = get_all_products()
    print(f"Found {len(existing)} existing products")
    print()

    # Ensure Kids Capsule category exists
    kids_cat_id = ensure_kids_category()
    CATEGORY_MAP["kids-capsule"] = kids_cat_id

    # Sync each product
    created = 0
    updated = 0
    failed = 0

    for row in products:
        sku = row["sku"].strip().strip('"')
        name = row["name"].strip().strip('"')
        collection_slug = row.get("collection", "").strip()
        category_id = CATEGORY_MAP.get(collection_slug, 19)  # Default to signature

        image_info = image_map.get(sku)
        product_data = build_product_data(row, image_info, category_id)

        try:
            if sku in existing:
                # Update existing
                wc_id = existing[sku]["id"]
                wc_request("PUT", f"products/{wc_id}", json_data=product_data)
                img_status = "✓ img" if image_info else "✗ no img"
                print(
                    f"  UPDATED  {sku:18s} | {name[:40]:40s} | ${product_data['regular_price']:>6s} | {img_status}"
                )
                updated += 1
            else:
                # Create new
                result = wc_request("POST", "products", json_data=product_data)
                img_status = "✓ img" if image_info else "✗ no img"
                print(
                    f"  CREATED  {sku:18s} | {name[:40]:40s} | ${product_data['regular_price']:>6s} | {img_status}"
                )
                created += 1

            # Rate limit: WooCommerce can throttle
            time.sleep(0.5)

        except httpx.HTTPStatusError as e:
            # If image ID is invalid, retry without image
            if "invalid_image_id" in e.response.text and image_info:
                try:
                    product_data.pop("images", None)
                    if sku in existing:
                        wc_request("PUT", f"products/{existing[sku]['id']}", json_data=product_data)
                        print(
                            f"  UPDATED  {sku:18s} | {name[:40]:40s} | ${product_data['regular_price']:>6s} | ✗ img invalid, synced without"
                        )
                        updated += 1
                    else:
                        wc_request("POST", "products", json_data=product_data)
                        print(
                            f"  CREATED  {sku:18s} | {name[:40]:40s} | ${product_data['regular_price']:>6s} | ✗ img invalid, synced without"
                        )
                        created += 1
                    time.sleep(0.5)
                    continue
                except Exception as retry_err:
                    print(f"  FAILED   {sku:18s} | {name[:40]:40s} | retry failed: {retry_err}")
                    failed += 1
            else:
                print(
                    f"  FAILED   {sku:18s} | {name[:40]:40s} | {e.response.status_code}: {e.response.text[:100]}"
                )
                failed += 1
        except Exception as e:
            print(f"  FAILED   {sku:18s} | {name[:40]:40s} | {e}")
            failed += 1

    # Summary
    print()
    print("=" * 60)
    print(f"CREATED:  {created}")
    print(f"UPDATED:  {updated}")
    print(f"FAILED:   {failed}")
    print(f"TOTAL:    {created + updated + failed}/{len(products)}")
    print("=" * 60)


if __name__ == "__main__":
    sync_all()
