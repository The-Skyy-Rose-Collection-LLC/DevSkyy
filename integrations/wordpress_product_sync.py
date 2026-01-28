"""WordPress Product Sync for SkyyRose Collections.

Syncs SkyyRose product catalog to WooCommerce.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from integrations.wordpress_com_client import (
    WordPressComClient,
    WordPressProduct,
)


class SkyyRoseProduct(BaseModel):
    """SkyyRose product model."""

    sku: str = Field(..., description="Product SKU")
    name: str = Field(..., description="Product name")
    collection: Literal["signature", "black-rose", "love-hurts"] = Field(
        ..., description="SkyyRose collection"
    )
    description: str = Field(..., description="Full product description")
    short_description: str = Field(..., description="Short description")
    price: str = Field(..., description="Price (e.g., '299.00')")
    regular_price: str | None = Field(None, description="Regular price before discount")
    images: list[str] = Field(default_factory=list, description="Image URLs")
    stock_quantity: int | None = Field(None, description="Stock quantity")
    limited_edition: bool = Field(default=True, description="Is limited edition")
    metal_type: str | None = Field(None, description="Metal type (18k gold, silver, rose gold)")


class ProductSyncResult(BaseModel):
    """Product sync result."""

    sku: str
    woo_id: int
    action: Literal["created", "updated", "skipped"]
    error: str | None = None


class WordPressProductSync:
    """Sync SkyyRose products to WooCommerce."""

    # Collection metadata
    COLLECTION_META = {
        "signature": {
            "slug": "signature-collection",
            "name": "Signature Collection",
            "description": "Our most celebrated pieces that define a generation of discerning taste.",
            "color": "#C9A962",  # Gold
        },
        "black-rose": {
            "slug": "black-rose-collection",
            "name": "Black Rose Collection",
            "description": "A gothic journey through midnight gardens where shadow dances with silver.",
            "color": "#C0C0C0",  # Silver
        },
        "love-hurts": {
            "slug": "love-hurts-collection",
            "name": "Love Hurts Collection",
            "description": "Where passion meets fragility in a castle of whispered confessions.",
            "color": "#B76E79",  # Rose gold
        },
    }

    def __init__(self, client: WordPressComClient) -> None:
        """Initialize product sync.

        Args:
            client: WordPress.com client with WooCommerce config
        """
        if not client.woo_client:
            raise ValueError("WooCommerce must be configured")
        self.client = client

    async def sync_product(
        self,
        product: SkyyRoseProduct,
        *,
        force_update: bool = False,
    ) -> ProductSyncResult:
        """Sync single product to WooCommerce.

        Args:
            product: SkyyRose product
            force_update: Force update even if product exists

        Returns:
            Sync result
        """
        try:
            # Check if product exists by SKU
            existing = await self._find_by_sku(product.sku)

            if existing and not force_update:
                return ProductSyncResult(
                    sku=product.sku,
                    woo_id=existing["id"],
                    action="skipped",
                )

            # Build WooCommerce product data
            woo_product = self._build_woo_product(product)

            if existing:
                # Update existing product
                result = await self.client.update_product(existing["id"], woo_product)
                return ProductSyncResult(
                    sku=product.sku,
                    woo_id=result["id"],
                    action="updated",
                )
            else:
                # Create new product
                result = await self.client.create_product(woo_product)
                return ProductSyncResult(
                    sku=product.sku,
                    woo_id=result["id"],
                    action="created",
                )

        except Exception as e:
            return ProductSyncResult(
                sku=product.sku,
                woo_id=0,
                action="skipped",
                error=str(e),
            )

    async def sync_collection(
        self,
        collection: Literal["signature", "black-rose", "love-hurts"],
        products: list[SkyyRoseProduct],
    ) -> list[ProductSyncResult]:
        """Sync all products in a collection.

        Args:
            collection: Collection name
            products: Products to sync

        Returns:
            List of sync results
        """
        results: list[ProductSyncResult] = []

        for product in products:
            if product.collection != collection:
                continue
            result = await self.sync_product(product)
            results.append(result)

        return results

    def _build_woo_product(self, product: SkyyRoseProduct) -> WordPressProduct:
        """Build WooCommerce product data from SkyyRose product.

        Args:
            product: SkyyRose product

        Returns:
            WooCommerce product data
        """
        collection_meta = self.COLLECTION_META[product.collection]

        # Build product data
        woo_product: WordPressProduct = {
            "name": product.name,
            "slug": product.sku.lower(),
            "type": "simple",
            "status": "publish",
            "description": product.description,
            "short_description": product.short_description,
            "sku": product.sku,
            "price": product.price,
            "regular_price": product.regular_price or product.price,
            "manage_stock": product.stock_quantity is not None,
            "stock_quantity": product.stock_quantity,
            "categories": [{"name": collection_meta["name"]}],
            "tags": [{"name": "Limited Edition"}] if product.limited_edition else [],
        }

        # Add images
        if product.images:
            woo_product["images"] = [{"src": url} for url in product.images]

        # Add metal type attribute
        if product.metal_type:
            woo_product["attributes"] = [
                {
                    "name": "Metal Type",
                    "options": [product.metal_type],
                    "visible": True,
                }
            ]

        return woo_product

    async def _find_by_sku(self, sku: str) -> dict[str, Any] | None:
        """Find product by SKU.

        Args:
            sku: Product SKU

        Returns:
            Product data or None if not found
        """
        products = await self.client.list_products(sku=sku, per_page=1)
        return products[0] if products else None
