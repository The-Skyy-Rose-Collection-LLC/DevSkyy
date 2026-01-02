# sync/woocommerce_sync.py
"""
WooCommerce Synchronization Client.

Handles direct communication with WooCommerce REST API for:
- Product CRUD operations
- Order synchronization
- Inventory updates
- 3D asset attachment
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx

from errors.production_errors import ConfigurationError, WordPressIntegrationError

logger = logging.getLogger(__name__)


@dataclass
class ProductSyncData:
    """Data structure for product synchronization."""

    sku: str
    name: str
    description: str = ""
    short_description: str = ""
    regular_price: str = ""
    sale_price: str = ""
    stock_quantity: int | None = None
    categories: list[int] | None = None
    images: list[dict[str, Any]] | None = None
    model_3d_url: str | None = None
    attributes: list[dict[str, Any]] | None = None
    meta_data: list[dict[str, Any]] | None = None


class WooCommerceSyncClient:
    """
    WooCommerce REST API client for synchronization.

    Provides methods for:
    - Product management
    - Media upload
    - 3D model attachment
    - Inventory sync

    Requires environment variables:
    - WOOCOMMERCE_URL
    - WOOCOMMERCE_KEY
    - WOOCOMMERCE_SECRET
    """

    def __init__(
        self,
        url: str | None = None,
        consumer_key: str | None = None,
        consumer_secret: str | None = None,
    ) -> None:
        """
        Initialize the WooCommerce client.

        Args:
            url: WooCommerce store URL
            consumer_key: API consumer key
            consumer_secret: API consumer secret
        """
        self.url = url or os.getenv("WOOCOMMERCE_URL", os.getenv("WORDPRESS_URL"))
        self.consumer_key = consumer_key or os.getenv("WOOCOMMERCE_KEY")
        self.consumer_secret = consumer_secret or os.getenv("WOOCOMMERCE_SECRET")

        if not all([self.url, self.consumer_key, self.consumer_secret]):
            raise ConfigurationError(
                "WooCommerce credentials required: WOOCOMMERCE_URL, "
                "WOOCOMMERCE_KEY, WOOCOMMERCE_SECRET",
            )

        self._client = httpx.AsyncClient(
            base_url=f"{self.url}/wp-json/wc/v3",
            auth=(self.consumer_key, self.consumer_secret),
            timeout=60.0,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def get_products(
        self,
        per_page: int = 100,
        page: int = 1,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Get products from WooCommerce.

        Args:
            per_page: Products per page
            page: Page number
            **kwargs: Additional query parameters

        Returns:
            List of product dictionaries
        """
        try:
            params = {"per_page": per_page, "page": page, **kwargs}
            response = await self._client.get("/products", params=params)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise WordPressIntegrationError(
                f"Failed to get products: {e.response.status_code}",
                endpoint="/products",
                status_code=e.response.status_code,
            )

    async def get_product(self, product_id: int) -> dict[str, Any]:
        """Get a single product by ID."""
        try:
            response = await self._client.get(f"/products/{product_id}")
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise WordPressIntegrationError(
                f"Failed to get product {product_id}",
                endpoint=f"/products/{product_id}",
                status_code=e.response.status_code,
            )

    async def get_product_by_sku(self, sku: str) -> dict[str, Any] | None:
        """Get a product by SKU."""
        products = await self.get_products(sku=sku)
        return products[0] if products else None

    async def create_product(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new product.

        Args:
            data: Product data

        Returns:
            Created product
        """
        try:
            response = await self._client.post("/products", json=data)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise WordPressIntegrationError(
                f"Failed to create product: {e.response.text}",
                endpoint="/products",
                status_code=e.response.status_code,
            )

    async def update_product(
        self,
        product_id: int,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Update an existing product.

        Args:
            product_id: Product ID
            data: Updated data

        Returns:
            Updated product
        """
        try:
            response = await self._client.put(f"/products/{product_id}", json=data)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise WordPressIntegrationError(
                f"Failed to update product {product_id}",
                endpoint=f"/products/{product_id}",
                status_code=e.response.status_code,
            )

    async def delete_product(
        self,
        product_id: int,
        force: bool = False,
    ) -> dict[str, Any]:
        """Delete a product."""
        try:
            response = await self._client.delete(
                f"/products/{product_id}",
                params={"force": force},
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise WordPressIntegrationError(
                f"Failed to delete product {product_id}",
                endpoint=f"/products/{product_id}",
                status_code=e.response.status_code,
            )

    async def sync_product(self, sync_data: ProductSyncData) -> dict[str, Any]:
        """
        Sync a product (create or update).

        Args:
            sync_data: Product data to sync

        Returns:
            Synced product
        """
        # Check if product exists
        existing = await self.get_product_by_sku(sync_data.sku)

        product_data = {
            "name": sync_data.name,
            "sku": sync_data.sku,
            "description": sync_data.description,
            "short_description": sync_data.short_description,
            "regular_price": sync_data.regular_price,
        }

        if sync_data.sale_price:
            product_data["sale_price"] = sync_data.sale_price

        if sync_data.stock_quantity is not None:
            product_data["stock_quantity"] = sync_data.stock_quantity
            product_data["manage_stock"] = True

        if sync_data.categories:
            product_data["categories"] = [{"id": cat} for cat in sync_data.categories]

        if sync_data.images:
            product_data["images"] = sync_data.images

        if sync_data.attributes:
            product_data["attributes"] = sync_data.attributes

        # Add 3D model as meta data
        meta_data = sync_data.meta_data or []
        if sync_data.model_3d_url:
            meta_data.append(
                {
                    "key": "_3d_model_url",
                    "value": sync_data.model_3d_url,
                }
            )
            meta_data.append(
                {
                    "key": "_has_3d_viewer",
                    "value": "yes",
                }
            )

        if meta_data:
            product_data["meta_data"] = meta_data

        if existing:
            return await self.update_product(existing["id"], product_data)
        else:
            return await self.create_product(product_data)

    async def attach_3d_model(
        self,
        product_id: int,
        model_url: str,
    ) -> dict[str, Any]:
        """
        Attach a 3D model URL to a product.

        Args:
            product_id: Product ID
            model_url: URL to the 3D model (.glb)

        Returns:
            Updated product
        """
        return await self.update_product(
            product_id,
            {
                "meta_data": [
                    {"key": "_3d_model_url", "value": model_url},
                    {"key": "_has_3d_viewer", "value": "yes"},
                ]
            },
        )

    async def update_inventory(
        self,
        product_id: int,
        stock_quantity: int,
        stock_status: str = "instock",
    ) -> dict[str, Any]:
        """
        Update product inventory.

        Args:
            product_id: Product ID
            stock_quantity: New stock quantity
            stock_status: Stock status (instock, outofstock, onbackorder)

        Returns:
            Updated product
        """
        return await self.update_product(
            product_id,
            {
                "stock_quantity": stock_quantity,
                "stock_status": stock_status,
                "manage_stock": True,
            },
        )

    async def get_orders(
        self,
        status: str | None = None,
        per_page: int = 100,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        """Get orders from WooCommerce."""
        try:
            params = {"per_page": per_page, "page": page}
            if status:
                params["status"] = status

            response = await self._client.get("/orders", params=params)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise WordPressIntegrationError(
                "Failed to get orders",
                endpoint="/orders",
                status_code=e.response.status_code,
            )

    async def get_categories(self) -> list[dict[str, Any]]:
        """Get product categories."""
        try:
            response = await self._client.get(
                "/products/categories",
                params={"per_page": 100},
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise WordPressIntegrationError(
                "Failed to get categories",
                endpoint="/products/categories",
                status_code=e.response.status_code,
            )

    async def health_check(self) -> bool:
        """Check WooCommerce API health."""
        try:
            response = await self._client.get("/system_status")
            return response.status_code == 200
        except Exception:
            return False
