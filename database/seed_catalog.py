"""Seed the DevSkyy database with SkyyRose product catalog.

Loads from the canonical CSV at data/product-catalog.csv.

Usage:
    python -m database.seed_catalog
"""

from __future__ import annotations

import asyncio
import csv
import json
import uuid
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CATALOG_CSV = _PROJECT_ROOT / "data" / "product-catalog.csv"


def _infer_category(name: str) -> str:
    n = name.lower()
    if "jogger" in n:
        return "Joggers"
    if "sweatpant" in n:
        return "Pants"
    if "windbreaker" in n or "jacket" in n:
        return "Jackets"
    if "hoodie" in n:
        return "Hoodies"
    if "crewneck" in n:
        return "Crewnecks"
    if "shorts" in n:
        return "Shorts"
    if "jersey" in n:
        return "Jerseys"
    if "tee" in n or "shirt" in n:
        return "Tees"
    if "beanie" in n or "fannie" in n:
        return "Accessories"
    if "set" in n:
        return "Sets"
    return "Apparel"


def _load_products() -> list[dict]:
    """Load canonical product list from data/product-catalog.csv.

    Skips render-only variants (rows where render_variant_of is set),
    which are not standalone WooCommerce products.
    """
    products = []
    with _CATALOG_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if not sku or row["render_variant_of"].strip():
                continue
            sizes = [s.strip() for s in row["sizes"].split("|") if s.strip()]
            products.append(
                {
                    "sku": sku,
                    "name": row["name"].strip(),
                    "price": float(row["price"]) if row["price"].strip() else 0.0,
                    "collection": row["collection_slug"].strip(),
                    "category": _infer_category(row["name"]),
                    "description": row["description"].strip(),
                    "quantity": int(row["edition_size"]) if row["edition_size"].strip() else 250,
                    "is_active": row["is_preorder"].strip() == "1",
                    "sizes": sizes,
                    "color": row["color"].strip(),
                }
            )
    return products


PRODUCTS = _load_products()


async def seed():
    """Seed all 28 SkyyRose products into the database."""
    from database.db import Product, db_manager

    await db_manager.initialize()

    async with db_manager.session() as session:
        # Check if products already exist
        from sqlalchemy import func, select

        count_result = await session.execute(select(func.count()).select_from(Product))
        existing = count_result.scalar() or 0

        if existing > 0:
            print(f"Database already has {existing} products. Skipping seed.")
            print("To re-seed, delete devskyy.db and run again.")
            return

        for p in PRODUCTS:
            product = Product(
                id=str(uuid.uuid4()),
                sku=p["sku"],
                name=p["name"],
                description=p["description"],
                price=p["price"],
                quantity=p["quantity"],
                category=p["category"],
                collection=p["collection"],
                is_active=p["is_active"],
                variants_json=json.dumps({"sizes": p["sizes"], "color": p["color"]}),
            )
            session.add(product)

        await session.commit()

    print(f"Seeded {len(PRODUCTS)} products:")
    collections = {}
    for p in PRODUCTS:
        c = p["collection"]
        collections[c] = collections.get(c, 0) + 1
    for c, n in collections.items():
        print(f"  {c}: {n} products")


if __name__ == "__main__":
    asyncio.run(seed())
