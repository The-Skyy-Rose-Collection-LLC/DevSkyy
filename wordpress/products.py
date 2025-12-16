"""
WooCommerce Products
====================

WooCommerce product CRUD operations.

Reference: https://woocommerce.github.io/woocommerce-rest-api-docs/

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import builtins
import logging
import os
from dataclasses import dataclass, field
from typing import Any

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Models
# =============================================================================


class ProductImage(BaseModel):
    """Product image."""

    id: int | None = None
    src: str = ""
    name: str = ""
    alt: str = ""
    position: int = 0


class ProductAttribute(BaseModel):
    """Product attribute."""

    id: int = 0
    name: str = ""
    position: int = 0
    visible: bool = True
    variation: bool = False
    options: list[str] = Field(default_factory=list)


class ProductCategory(BaseModel):
    """Product category."""

    id: int
    name: str = ""
    slug: str = ""


class ProductCreate(BaseModel):
    """Product creation data."""

    name: str
    type: str = "simple"
    status: str = "draft"
    description: str = ""
    short_description: str = ""
    sku: str = ""
    regular_price: str = ""
    sale_price: str = ""
    manage_stock: bool = False
    stock_quantity: int | None = None
    categories: list[dict[str, int]] = Field(default_factory=list)
    images: list[dict[str, Any]] = Field(default_factory=list)
    attributes: list[dict[str, Any]] = Field(default_factory=list)
    meta_data: list[dict[str, Any]] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    """Product update data."""

    name: str | None = None
    status: str | None = None
    description: str | None = None
    short_description: str | None = None
    regular_price: str | None = None
    sale_price: str | None = None
    manage_stock: bool | None = None
    stock_quantity: int | None = None
    images: list[dict[str, Any]] | None = None
    categories: list[dict[str, int]] | None = None


class ProductVariation(BaseModel):
    """Product variation."""

    id: int | None = None
    sku: str = ""
    regular_price: str = ""
    sale_price: str = ""
    manage_stock: bool = False
    stock_quantity: int | None = None
    attributes: list[dict[str, str]] = Field(default_factory=list)
    image: dict[str, Any] | None = None


class Product(BaseModel):
    """WooCommerce product."""

    id: int
    name: str = ""
    slug: str = ""
    type: str = "simple"
    status: str = "publish"
    description: str = ""
    short_description: str = ""
    sku: str = ""
    price: str = ""
    regular_price: str = ""
    sale_price: str = ""
    on_sale: bool = False
    stock_status: str = "instock"
    stock_quantity: int | None = None
    categories: list[ProductCategory] = Field(default_factory=list)
    images: list[ProductImage] = Field(default_factory=list)
    attributes: list[ProductAttribute] = Field(default_factory=list)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class WooCommerceConfig:
    """WooCommerce API configuration."""

    site_url: str = field(default_factory=lambda: os.getenv("WP_SITE_URL", ""))
    consumer_key: str = field(
        default_factory=lambda: os.getenv("WC_CONSUMER_KEY", "")
        or os.getenv("WOOCOMMERCE_KEY", "")
        or os.getenv("WOOCOMMERCE_CONSUMER_KEY", "")
    )
    consumer_secret: str = field(
        default_factory=lambda: os.getenv("WC_CONSUMER_SECRET", "")
        or os.getenv("WOOCOMMERCE_SECRET", "")
        or os.getenv("WOOCOMMERCE_CONSUMER_SECRET", "")
    )
    api_version: str = "wc/v3"
    timeout: float = 30.0
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> WooCommerceConfig:
        return cls()

    @property
    def base_url(self) -> str:
        return f"{self.site_url}/wp-json/{self.api_version}"


# =============================================================================
# WooCommerce Products Client
# =============================================================================


class WooCommerceProducts:
    """
    WooCommerce Products API client.

    Usage:
        async with WooCommerceProducts() as wc:
            # List products
            products = await wc.list(per_page=20)

            # Create product
            product = await wc.create(ProductCreate(
                name="Test Product",
                regular_price="99.99",
            ))

            # Update product
            await wc.update(product["id"], ProductUpdate(status="publish"))
    """

    def __init__(self, config: WooCommerceConfig | None = None) -> None:
        self.config = config or WooCommerceConfig.from_env()
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> WooCommerceProducts:
        await self.connect()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def connect(self) -> None:
        """Initialize HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                auth=aiohttp.BasicAuth(
                    self.config.consumer_key,
                    self.config.consumer_secret,
                ),
            )

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """Make API request."""
        await self.connect()
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"

        async with self._session.request(method, url, params=params, json=json) as response:
            if response.status >= 400:
                text = await response.text()
                raise Exception(f"WooCommerce API error ({response.status}): {text}")
            return await response.json()

    # -------------------------------------------------------------------------
    # Products CRUD
    # -------------------------------------------------------------------------

    async def list(
        self,
        per_page: int = 10,
        page: int = 1,
        status: str = "any",
        category: int | None = None,
        search: str | None = None,
        **kwargs: Any,
    ) -> builtins.list[dict[str, Any]]:
        """List products."""
        params = {
            "per_page": per_page,
            "page": page,
            "status": status,
            **kwargs,
        }
        if category:
            params["category"] = category
        if search:
            params["search"] = search

        return await self._request("GET", "/products", params=params)

    async def get(self, product_id: int) -> dict[str, Any]:
        """Get single product."""
        return await self._request("GET", f"/products/{product_id}")

    async def create(self, data: ProductCreate) -> dict[str, Any]:
        """Create product."""
        return await self._request("POST", "/products", json=data.model_dump(exclude_none=True))

    async def update(self, product_id: int, data: ProductUpdate) -> dict[str, Any]:
        """Update product."""
        return await self._request(
            "PUT",
            f"/products/{product_id}",
            json=data.model_dump(exclude_none=True),
        )

    async def delete(self, product_id: int, force: bool = False) -> dict[str, Any]:
        """Delete product."""
        params = {"force": force}
        return await self._request("DELETE", f"/products/{product_id}", params=params)

    # -------------------------------------------------------------------------
    # Batch Operations
    # -------------------------------------------------------------------------

    async def batch(
        self,
        create: builtins.list[ProductCreate] | None = None,
        update: builtins.list[dict[str, Any]] | None = None,
        delete: builtins.list[int] | None = None,
    ) -> dict[str, Any]:
        """Batch create/update/delete products."""
        data: dict[str, Any] = {}

        if create:
            data["create"] = [p.model_dump(exclude_none=True) for p in create]
        if update:
            data["update"] = update
        if delete:
            data["delete"] = delete

        return await self._request("POST", "/products/batch", json=data)

    # -------------------------------------------------------------------------
    # Variations
    # -------------------------------------------------------------------------

    async def list_variations(
        self,
        product_id: int,
        per_page: int = 10,
    ) -> builtins.list[dict[str, Any]]:
        """List product variations."""
        return await self._request(
            "GET",
            f"/products/{product_id}/variations",
            params={"per_page": per_page},
        )

    async def create_variation(
        self,
        product_id: int,
        data: ProductVariation,
    ) -> dict[str, Any]:
        """Create product variation."""
        return await self._request(
            "POST",
            f"/products/{product_id}/variations",
            json=data.model_dump(exclude_none=True),
        )

    async def update_variation(
        self,
        product_id: int,
        variation_id: int,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Update product variation."""
        return await self._request(
            "PUT",
            f"/products/{product_id}/variations/{variation_id}",
            json=data,
        )

    # -------------------------------------------------------------------------
    # Categories
    # -------------------------------------------------------------------------

    async def list_categories(
        self,
        per_page: int = 100,
        **kwargs: Any,
    ) -> builtins.list[dict[str, Any]]:
        """List product categories."""
        return await self._request(
            "GET",
            "/products/categories",
            params={"per_page": per_page, **kwargs},
        )

    async def create_category(
        self,
        name: str,
        slug: str = "",
        parent: int = 0,
        description: str = "",
        image: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create product category."""
        data = {
            "name": name,
            "parent": parent,
            "description": description,
        }
        if slug:
            data["slug"] = slug
        if image:
            data["image"] = image

        return await self._request("POST", "/products/categories", json=data)

    # -------------------------------------------------------------------------
    # Attributes
    # -------------------------------------------------------------------------

    async def list_attributes(self) -> builtins.list[dict[str, Any]]:
        """List product attributes."""
        return await self._request("GET", "/products/attributes")

    async def create_attribute(
        self,
        name: str,
        slug: str = "",
        type: str = "select",
        order_by: str = "menu_order",
    ) -> dict[str, Any]:
        """Create product attribute."""
        data = {
            "name": name,
            "type": type,
            "order_by": order_by,
        }
        if slug:
            data["slug"] = slug

        return await self._request("POST", "/products/attributes", json=data)


__all__ = [
    "WooCommerceProducts",
    "WooCommerceConfig",
    "Product",
    "ProductCreate",
    "ProductUpdate",
    "ProductVariation",
    "ProductImage",
    "ProductAttribute",
    "ProductCategory",
]
