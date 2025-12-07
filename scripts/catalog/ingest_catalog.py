#!/usr/bin/env python3
"""
SkyyRose Catalog Ingestion Pipeline

Ingests the SkyyRose product catalog into:
1. ChromaDB (RAG) - For semantic search
2. WooCommerce - For e-commerce

Usage:
    python ingest_catalog.py --rag          # Ingest to ChromaDB only
    python ingest_catalog.py --woocommerce  # Sync to WooCommerce only
    python ingest_catalog.py --all          # Both
"""

import argparse
import asyncio
import base64
import csv
from dataclasses import dataclass, field
from http import HTTPStatus
import os
from pathlib import Path
import sys

import httpx


env_file = Path(__file__).parent.parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip())


@dataclass
class Product:
    """SkyyRose product data."""

    token: str
    name: str
    variation: str
    sku: str
    description: str
    categories: str
    seo_title: str
    seo_description: str
    permalink: str
    price: float
    color: str = ""
    size: str = ""
    quantity: int = 0
    visibility: str = "visible"

    @property
    def full_name(self) -> str:
        if self.variation:
            return f"{self.name} - {self.variation}"
        return self.name

    @property
    def searchable_text(self) -> str:
        """Text for semantic search embedding."""
        parts = [
            self.name,
            self.description,
            self.seo_description,
            self.categories,
            self.color,
        ]
        return " ".join(p for p in parts if p)


@dataclass
class ProductGroup:
    """Group of product variations (same parent product)."""

    name: str
    description: str
    seo_title: str
    seo_description: str
    permalink: str
    categories: str
    base_price: float
    variations: list[Product] = field(default_factory=list)

    @property
    def colors(self) -> list[str]:
        return list({v.color for v in self.variations if v.color})

    @property
    def sizes(self) -> list[str]:
        size_order = ["Small", "Medium", "Large", "X-Large", "XX-Large", "XXX-Large", "Regular"]
        sizes = list({v.size for v in self.variations if v.size})
        default_sort_order = 99
        return sorted(sizes, key=lambda s: size_order.index(s) if s in size_order else default_sort_order)


def load_catalog(csv_path: str) -> tuple[list[Product], list[ProductGroup]]:
    """Load catalog from CSV file."""
    products = []
    groups: dict[str, ProductGroup] = {}

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse price
            try:
                price = float(row.get("Price", "0").replace("$", "").replace(",", "") or "0")
            except ValueError:
                price = 0.0

            # Parse quantity
            try:
                qty = int(row.get("Current Quantity The Skyy Rose Collection", "0") or "0")
            except ValueError:
                qty = 0

            product = Product(
                token=row.get("Token", ""),
                name=row.get("Item Name", ""),
                variation=row.get("Variation Name", ""),
                sku=row.get("SKU", ""),
                description=row.get("Description", ""),
                categories=row.get("Categories", ""),
                seo_title=row.get("SEO Title", ""),
                seo_description=row.get("SEO Description", ""),
                permalink=row.get("Permalink", ""),
                price=price,
                color=row.get("Option Value 1", ""),
                size=row.get("Option Value 2", ""),
                quantity=qty,
                visibility=row.get("Square Online Item Visibility", "visible"),
            )
            products.append(product)

            # Group by parent product
            if product.name not in groups:
                groups[product.name] = ProductGroup(
                    name=product.name,
                    description=product.description or "",
                    seo_title=product.seo_title or "",
                    seo_description=product.seo_description or "",
                    permalink=product.permalink or "",
                    categories=product.categories or "",
                    base_price=price,
                )
            groups[product.name].variations.append(product)

            # Update group with non-empty values
            if product.description and not groups[product.name].description:
                groups[product.name].description = product.description
            if product.seo_title and not groups[product.name].seo_title:
                groups[product.name].seo_title = product.seo_title

    return products, list(groups.values())


class ChromaDBIngester:
    """Ingest products into ChromaDB for RAG."""

    def __init__(self, collection_name: str = "skyyrose_products"):
        self.collection_name = collection_name
        self.client = None
        self.collection = None

    async def connect(self) -> bool:
        """Connect to ChromaDB.

        Returns:
            bool: True if connection successful, False otherwise.

        Note:
            ChromaDB is imported dynamically to allow graceful degradation
            when the package is not installed (optional dependency).
        """
        try:
            import chromadb  # noqa: PLC0415 - Dynamic import for optional dependency

            # Use persistent storage
            persist_dir = Path(__file__).parent.parent.parent / "data" / "chromadb"
            persist_dir.mkdir(parents=True, exist_ok=True)

            self.client = chromadb.PersistentClient(path=str(persist_dir))
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name, metadata={"description": "SkyyRose product catalog for semantic search"}
            )
            print(f"  Connected to ChromaDB: {self.collection_name}")
            return True
        except ImportError:
            print("  ChromaDB not installed. Run: pip install chromadb")
            return False
        except Exception as e:
            print(f"  ChromaDB connection failed: {e}")
            return False

    async def ingest(self, groups: list[ProductGroup]) -> dict:
        """Ingest product groups into ChromaDB."""
        if not self.collection:
            return {"success": False, "error": "Not connected"}

        documents = []
        metadatas = []
        ids = []

        for group in groups:
            # Create searchable document
            doc = f"""
Product: {group.name}
Description: {group.description}
Categories: {group.categories}
Colors: {', '.join(group.colors)}
Sizes: {', '.join(group.sizes)}
Price: ${group.base_price}
SEO: {group.seo_description}
            """.strip()

            documents.append(doc)
            metadatas.append(
                {
                    "name": group.name,
                    "categories": group.categories,
                    "price": group.base_price,
                    "colors": ",".join(group.colors),
                    "sizes": ",".join(group.sizes),
                    "permalink": group.permalink,
                    "variation_count": len(group.variations),
                }
            )
            ids.append(group.permalink or group.name.lower().replace(" ", "-"))

        # Upsert to ChromaDB
        self.collection.upsert(documents=documents, metadatas=metadatas, ids=ids)

        return {"success": True, "products_ingested": len(groups), "collection": self.collection_name}


class WooCommerceSync:
    """Sync products to WooCommerce."""

    def __init__(self):
        self.site_url = os.getenv("SKYY_ROSE_SITE_URL", "")
        self.consumer_key = os.getenv("WOOCOMMERCE_CONSUMER_KEY", "")
        self.consumer_secret = os.getenv("WOOCOMMERCE_CONSUMER_SECRET", "")

        # Fallback to WordPress credentials for basic operations
        self.wp_username = os.getenv("SKYY_ROSE_USERNAME", "skyyroseco")
        self.wp_password = os.getenv("SKYY_ROSE_APP_PASSWORD", "")

    async def connect(self) -> bool:
        """Test WooCommerce connection."""
        if not self.site_url:
            print("  SKYY_ROSE_SITE_URL not set")
            return False

        # Try WooCommerce API first
        if self.consumer_key and self.consumer_secret:
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    r = await client.get(
                        f"{self.site_url}/wp-json/wc/v3/products",
                        params={"per_page": 1},
                        auth=(self.consumer_key, self.consumer_secret),
                    )
                    if r.status_code == HTTPStatus.OK:
                        print("  Connected to WooCommerce API")
                        return True
                except Exception as e:
                    print(f"  WooCommerce API error: {e}")

        # Fall back to REST API
        if self.wp_password:
            creds = base64.b64encode(f"{self.wp_username}:{self.wp_password}".encode()).decode()
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    r = await client.get(
                        f"{self.site_url}/wp-json/wc/v3/products",
                        params={"per_page": 1},
                        headers={"Authorization": f"Basic {creds}"},
                    )
                    if r.status_code == HTTPStatus.OK:
                        print("  Connected to WooCommerce via WordPress auth")
                        return True
                    else:
                        print(f"  WooCommerce response: {r.status_code}")
                except Exception as e:
                    print(f"  Connection error: {e}")

        print("  WooCommerce credentials not configured")
        print("  Set WOOCOMMERCE_CONSUMER_KEY and WOOCOMMERCE_CONSUMER_SECRET")
        return False

    def _get_auth(self):
        """Get authentication for requests."""
        if self.consumer_key and self.consumer_secret:
            return (self.consumer_key, self.consumer_secret)
        return None

    def _get_headers(self):
        """Get headers for requests."""
        if not self.consumer_key and self.wp_password:
            creds = base64.b64encode(f"{self.wp_username}:{self.wp_password}".encode()).decode()
            return {"Authorization": f"Basic {creds}"}
        return {}

    async def sync(self, groups: list[ProductGroup]) -> dict:
        """Sync products to WooCommerce."""
        results = {"created": 0, "updated": 0, "failed": 0, "errors": []}

        async with httpx.AsyncClient(timeout=60.0) as client:
            for group in groups:
                try:
                    # Check if product exists
                    r = await client.get(
                        f"{self.site_url}/wp-json/wc/v3/products",
                        params={"slug": group.permalink or group.name.lower().replace(" ", "-")},
                        auth=self._get_auth(),
                        headers=self._get_headers(),
                    )

                    existing = r.json() if r.status_code == HTTPStatus.OK else []

                    # Build product data
                    product_data = {
                        "name": group.name,
                        "slug": group.permalink or group.name.lower().replace(" ", "-"),
                        "type": "variable" if len(group.variations) > 1 else "simple",
                        "description": group.description,
                        "short_description": group.seo_description,
                        "categories": [{"name": group.categories}] if group.categories else [],
                        "regular_price": str(group.base_price) if len(group.variations) == 1 else "",
                        "status": "publish",
                        "attributes": [],
                    }

                    # Add attributes for variable products
                    if group.colors:
                        product_data["attributes"].append(
                            {"name": "Color", "options": group.colors, "visible": True, "variation": True}
                        )
                    if group.sizes:
                        product_data["attributes"].append(
                            {"name": "Size", "options": group.sizes, "visible": True, "variation": True}
                        )

                    if existing:
                        # Update existing
                        product_id = existing[0]["id"]
                        r = await client.put(
                            f"{self.site_url}/wp-json/wc/v3/products/{product_id}",
                            json=product_data,
                            auth=self._get_auth(),
                            headers=self._get_headers(),
                        )
                        if r.status_code == HTTPStatus.OK:
                            results["updated"] += 1
                            print(f"    [UPDATE] {group.name}")
                        else:
                            results["failed"] += 1
                            results["errors"].append(f"{group.name}: {r.status_code}")
                    else:
                        # Create new
                        r = await client.post(
                            f"{self.site_url}/wp-json/wc/v3/products",
                            json=product_data,
                            auth=self._get_auth(),
                            headers=self._get_headers(),
                        )
                        if r.status_code == HTTPStatus.CREATED:
                            results["created"] += 1
                            print(f"    [CREATE] {group.name}")
                        else:
                            results["failed"] += 1
                            results["errors"].append(f"{group.name}: {r.status_code} - {r.text[:100]}")

                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"{group.name}: {e!s}")

        return results


async def main():
    parser = argparse.ArgumentParser(description="Ingest SkyyRose catalog")
    parser.add_argument("--rag", action="store_true", help="Ingest to ChromaDB")
    parser.add_argument("--woocommerce", action="store_true", help="Sync to WooCommerce")
    parser.add_argument("--all", action="store_true", help="Both RAG and WooCommerce")
    parser.add_argument(
        "--catalog",
        default="/Users/coreyfoster/Downloads/files 3/skyyrose-catalog-updated.csv",
        help="Path to catalog CSV",
    )
    args = parser.parse_args()

    if not any([args.rag, args.woocommerce, args.all]):
        args.all = True  # Default to all

    print("=" * 60)
    print("SkyyRose Catalog Ingestion Pipeline")
    print("=" * 60)

    # Load catalog
    print(f"\nLoading catalog from: {args.catalog}")
    if not Path(args.catalog).exists():
        print(f"ERROR: Catalog file not found: {args.catalog}")
        sys.exit(1)

    products, groups = load_catalog(args.catalog)
    print(f"  Loaded {len(products)} product variations")
    print(f"  Found {len(groups)} unique products")

    # Show product summary
    print("\nProducts:")
    for g in groups:
        print(f"  - {g.name}: ${g.base_price} ({len(g.variations)} variations)")

    # Ingest to ChromaDB
    if args.rag or args.all:
        print("\n" + "-" * 40)
        print("RAG Ingestion (ChromaDB)")
        print("-" * 40)

        ingester = ChromaDBIngester()
        if await ingester.connect():
            result = await ingester.ingest(groups)
            if result["success"]:
                print(f"  Ingested {result['products_ingested']} products to {result['collection']}")
            else:
                print(f"  Failed: {result.get('error')}")

    # Sync to WooCommerce
    if args.woocommerce or args.all:
        print("\n" + "-" * 40)
        print("WooCommerce Sync")
        print("-" * 40)

        woo = WooCommerceSync()
        if await woo.connect():
            result = await woo.sync(groups)
            print(f"\n  Created: {result['created']}")
            print(f"  Updated: {result['updated']}")
            print(f"  Failed: {result['failed']}")
            if result["errors"]:
                print("  Errors:")
                for err in result["errors"][:5]:
                    print(f"    - {err}")

    print("\n" + "=" * 60)
    print("Ingestion Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
