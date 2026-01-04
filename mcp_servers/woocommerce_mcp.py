"""
WooCommerce MCP Client Integration
===================================

Client wrapper for the official WooCommerce MCP server (v10.3+).

This module provides:
- Type-safe WooCommerce operations via MCP
- Real-time inventory sync
- Order management
- Customer operations
- Coupon handling

Based on official WooCommerce MCP documentation:
https://developer.woocommerce.com/docs/features/mcp/

Requirements:
- WooCommerce 10.3+ with MCP beta enabled
- WordPress 6.9+ with Abilities API
- Valid WC REST API keys

Version: 1.0.0
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class WooCommerceMCPConfig:
    """WooCommerce MCP client configuration."""

    # WooCommerce store URL (falls back to WordPress URL)
    store_url: str = field(
        default_factory=lambda: os.getenv("WOOCOMMERCE_URL", "")
        or os.getenv("WORDPRESS_URL", "")
        or os.getenv("WP_SITE_URL", "")
    )

    # WC REST API credentials (supports both naming conventions)
    consumer_key: str = field(
        default_factory=lambda: os.getenv("WOOCOMMERCE_KEY", "") or os.getenv("WC_CONSUMER_KEY", "")
    )
    consumer_secret: str = field(
        default_factory=lambda: os.getenv("WOOCOMMERCE_SECRET", "")
        or os.getenv("WC_CONSUMER_SECRET", "")
    )

    # MCP server settings
    mcp_server_url: str = field(
        default_factory=lambda: os.getenv("WOOCOMMERCE_MCP_URL", "http://localhost:3100")
    )

    # Request settings
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


# =============================================================================
# Enums
# =============================================================================


class OrderStatus(str, Enum):
    """WooCommerce order statuses."""

    PENDING = "pending"
    PROCESSING = "processing"
    ON_HOLD = "on-hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    FAILED = "failed"


class StockStatus(str, Enum):
    """Product stock statuses."""

    IN_STOCK = "instock"
    OUT_OF_STOCK = "outofstock"
    ON_BACKORDER = "onbackorder"


class ProductType(str, Enum):
    """WooCommerce product types."""

    SIMPLE = "simple"
    VARIABLE = "variable"
    GROUPED = "grouped"
    EXTERNAL = "external"


# =============================================================================
# Data Models
# =============================================================================


class ProductVariation(BaseModel):
    """Product variation for variable products."""

    id: int | None = None
    sku: str | None = None
    price: str | None = None
    regular_price: str | None = None
    sale_price: str | None = None
    stock_quantity: int | None = None
    stock_status: StockStatus = StockStatus.IN_STOCK
    attributes: list[dict] = Field(default_factory=list)


class Product(BaseModel):
    """WooCommerce product model."""

    id: int | None = None
    name: str
    slug: str | None = None
    type: ProductType = ProductType.SIMPLE
    status: str = "publish"
    description: str = ""
    short_description: str = ""
    sku: str | None = None
    price: str | None = None
    regular_price: str | None = None
    sale_price: str | None = None
    stock_quantity: int | None = None
    stock_status: StockStatus = StockStatus.IN_STOCK
    manage_stock: bool = True
    categories: list[dict] = Field(default_factory=list)
    images: list[dict] = Field(default_factory=list)
    attributes: list[dict] = Field(default_factory=list)
    variations: list[ProductVariation] = Field(default_factory=list)
    meta_data: list[dict] = Field(default_factory=list)


class OrderItem(BaseModel):
    """Order line item."""

    id: int | None = None
    product_id: int
    variation_id: int | None = None
    quantity: int = 1
    subtotal: str | None = None
    total: str | None = None
    sku: str | None = None
    name: str | None = None


class Order(BaseModel):
    """WooCommerce order model."""

    id: int | None = None
    number: str | None = None
    status: OrderStatus = OrderStatus.PENDING
    currency: str = "USD"
    total: str | None = None
    subtotal: str | None = None
    customer_id: int | None = None
    billing: dict = Field(default_factory=dict)
    shipping: dict = Field(default_factory=dict)
    line_items: list[OrderItem] = Field(default_factory=list)
    payment_method: str | None = None
    transaction_id: str | None = None
    date_created: str | None = None
    date_modified: str | None = None
    meta_data: list[dict] = Field(default_factory=list)


class Customer(BaseModel):
    """WooCommerce customer model."""

    id: int | None = None
    email: str
    first_name: str = ""
    last_name: str = ""
    username: str | None = None
    billing: dict = Field(default_factory=dict)
    shipping: dict = Field(default_factory=dict)
    is_paying_customer: bool = False
    orders_count: int = 0
    total_spent: str = "0.00"
    meta_data: list[dict] = Field(default_factory=list)


class Coupon(BaseModel):
    """WooCommerce coupon model."""

    id: int | None = None
    code: str
    discount_type: str = "percent"  # percent, fixed_cart, fixed_product
    amount: str = "0"
    individual_use: bool = False
    usage_limit: int | None = None
    usage_count: int = 0
    date_expires: str | None = None
    product_ids: list[int] = Field(default_factory=list)
    excluded_product_ids: list[int] = Field(default_factory=list)
    minimum_amount: str | None = None
    maximum_amount: str | None = None


class InventoryUpdate(BaseModel):
    """Inventory update request."""

    product_id: int
    variation_id: int | None = None
    stock_quantity: int
    stock_status: StockStatus | None = None


# =============================================================================
# WooCommerce MCP Client
# =============================================================================


class WooCommerceMCPClient:
    """
    Client for WooCommerce MCP server operations.

    Provides async methods for all WooCommerce operations
    via the official MCP protocol.

    Example:
        client = WooCommerceMCPClient()
        await client.initialize()

        # Get product
        product = await client.get_product(123)

        # Update inventory
        await client.update_stock(123, quantity=50)

        # Create order
        order = await client.create_order(items=[...])
    """

    def __init__(self, config: WooCommerceMCPConfig | None = None):
        self.config = config or WooCommerceMCPConfig()
        self._session: aiohttp.ClientSession | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the client session."""
        if self._initialized:
            return

        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        self._initialized = True
        logger.info("WooCommerce MCP client initialized")

    async def close(self) -> None:
        """Close the client session."""
        if self._session:
            await self._session.close()
            self._session = None
            self._initialized = False

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    # -------------------------------------------------------------------------
    # Internal Methods
    # -------------------------------------------------------------------------

    async def _call_mcp(
        self,
        tool_name: str,
        params: dict[str, Any],
        retries: int = 0,
    ) -> dict[str, Any]:
        """Call WooCommerce MCP server tool."""
        if not self._session:
            await self.initialize()

        url = f"{self.config.mcp_server_url}/tools/{tool_name}"

        try:
            async with self._session.post(url, json=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429 and retries < self.config.max_retries:
                    # Rate limited, retry with backoff
                    await asyncio.sleep(self.config.retry_delay * (retries + 1))
                    return await self._call_mcp(tool_name, params, retries + 1)
                else:
                    error_text = await response.text()
                    logger.error(f"MCP call failed: {response.status} - {error_text}")
                    return {"error": f"HTTP {response.status}: {error_text}"}

        except aiohttp.ClientError as e:
            logger.error(f"MCP connection error: {e}")
            if retries < self.config.max_retries:
                await asyncio.sleep(self.config.retry_delay * (retries + 1))
                return await self._call_mcp(tool_name, params, retries + 1)
            return {"error": str(e)}

    async def _call_wc_rest(
        self,
        endpoint: str,
        method: str = "GET",
        data: dict | None = None,
    ) -> dict[str, Any]:
        """Direct WooCommerce REST API call (fallback)."""
        if not self._session:
            await self.initialize()

        url = f"{self.config.store_url}/wp-json/wc/v3/{endpoint}"
        auth = aiohttp.BasicAuth(self.config.consumer_key, self.config.consumer_secret)

        try:
            if method == "GET":
                async with self._session.get(url, auth=auth) as response:
                    return await response.json()
            elif method == "POST":
                async with self._session.post(url, auth=auth, json=data) as response:
                    return await response.json()
            elif method == "PUT":
                async with self._session.put(url, auth=auth, json=data) as response:
                    return await response.json()
            elif method == "DELETE":
                async with self._session.delete(url, auth=auth) as response:
                    return await response.json()

        except aiohttp.ClientError as e:
            logger.error(f"WC REST API error: {e}")
            return {"error": str(e)}

        return {"error": f"Unknown method: {method}"}

    # -------------------------------------------------------------------------
    # Product Operations
    # -------------------------------------------------------------------------

    async def get_product(self, product_id: int) -> Product | None:
        """Get product by ID."""
        result = await self._call_mcp("wc_get_product", {"id": product_id})

        if "error" in result:
            logger.error(f"Failed to get product {product_id}: {result['error']}")
            return None

        return Product(**result.get("product", result))

    async def search_products(
        self,
        query: str | None = None,
        category: int | None = None,
        sku: str | None = None,
        status: str = "publish",
        per_page: int = 20,
        page: int = 1,
    ) -> list[Product]:
        """Search products with filters."""
        params = {
            "status": status,
            "per_page": per_page,
            "page": page,
        }
        if query:
            params["search"] = query
        if category:
            params["category"] = category
        if sku:
            params["sku"] = sku

        result = await self._call_mcp("wc_list_products", params)

        if "error" in result:
            logger.error(f"Product search failed: {result['error']}")
            return []

        products = result.get("products", result if isinstance(result, list) else [])
        return [Product(**p) for p in products]

    async def create_product(self, product: Product) -> Product | None:
        """Create a new product."""
        data = product.model_dump(exclude_none=True, exclude={"id"})
        result = await self._call_mcp("wc_create_product", data)

        if "error" in result:
            logger.error(f"Failed to create product: {result['error']}")
            return None

        return Product(**result.get("product", result))

    async def update_product(self, product_id: int, updates: dict) -> Product | None:
        """Update product fields."""
        params = {"id": product_id, **updates}
        result = await self._call_mcp("wc_update_product", params)

        if "error" in result:
            logger.error(f"Failed to update product {product_id}: {result['error']}")
            return None

        return Product(**result.get("product", result))

    async def delete_product(self, product_id: int, force: bool = False) -> bool:
        """Delete a product."""
        result = await self._call_mcp("wc_delete_product", {"id": product_id, "force": force})
        return "error" not in result

    # -------------------------------------------------------------------------
    # Inventory Operations
    # -------------------------------------------------------------------------

    async def get_stock(self, product_id: int, variation_id: int | None = None) -> dict:
        """Get stock quantity for product or variation."""
        params = {"product_id": product_id}
        if variation_id:
            params["variation_id"] = variation_id

        result = await self._call_mcp("wc_get_stock", params)

        if "error" in result:
            # Fallback to REST API
            endpoint = f"products/{product_id}"
            if variation_id:
                endpoint += f"/variations/{variation_id}"
            result = await self._call_wc_rest(endpoint)

        return {
            "product_id": product_id,
            "variation_id": variation_id,
            "stock_quantity": result.get("stock_quantity", 0),
            "stock_status": result.get("stock_status", "instock"),
            "manage_stock": result.get("manage_stock", False),
        }

    async def update_stock(
        self,
        product_id: int,
        quantity: int,
        variation_id: int | None = None,
        stock_status: StockStatus | None = None,
    ) -> dict:
        """Update stock quantity."""
        params = {
            "product_id": product_id,
            "stock_quantity": quantity,
        }
        if variation_id:
            params["variation_id"] = variation_id
        if stock_status:
            params["stock_status"] = stock_status.value

        result = await self._call_mcp("wc_update_stock", params)

        if "error" in result:
            # Fallback to REST API
            endpoint = f"products/{product_id}"
            if variation_id:
                endpoint += f"/variations/{variation_id}"
            data = {"stock_quantity": quantity}
            if stock_status:
                data["stock_status"] = stock_status.value
            result = await self._call_wc_rest(endpoint, method="PUT", data=data)

        return result

    async def batch_update_stock(self, updates: list[InventoryUpdate]) -> dict:
        """Batch update multiple product stock levels."""
        batch_data = {
            "update": [
                {
                    "id": u.product_id,
                    "stock_quantity": u.stock_quantity,
                    **({"stock_status": u.stock_status.value} if u.stock_status else {}),
                }
                for u in updates
            ]
        }

        result = await self._call_mcp("wc_batch_products", batch_data)

        if "error" in result:
            # Fallback to REST API
            result = await self._call_wc_rest("products/batch", method="POST", data=batch_data)

        return result

    # -------------------------------------------------------------------------
    # Order Operations
    # -------------------------------------------------------------------------

    async def get_order(self, order_id: int) -> Order | None:
        """Get order by ID."""
        result = await self._call_mcp("wc_get_order", {"id": order_id})

        if "error" in result:
            logger.error(f"Failed to get order {order_id}: {result['error']}")
            return None

        return Order(**result.get("order", result))

    async def list_orders(
        self,
        status: OrderStatus | None = None,
        customer_id: int | None = None,
        per_page: int = 20,
        page: int = 1,
        after: str | None = None,
        before: str | None = None,
    ) -> list[Order]:
        """List orders with filters."""
        params = {"per_page": per_page, "page": page}
        if status:
            params["status"] = status.value
        if customer_id:
            params["customer"] = customer_id
        if after:
            params["after"] = after
        if before:
            params["before"] = before

        result = await self._call_mcp("wc_list_orders", params)

        if "error" in result:
            logger.error(f"Failed to list orders: {result['error']}")
            return []

        orders = result.get("orders", result if isinstance(result, list) else [])
        return [Order(**o) for o in orders]

    async def create_order(
        self,
        customer_id: int | None = None,
        line_items: list[OrderItem] | None = None,
        billing: dict | None = None,
        shipping: dict | None = None,
        payment_method: str | None = None,
        status: OrderStatus = OrderStatus.PENDING,
    ) -> Order | None:
        """Create a new order."""
        data = {"status": status.value}
        if customer_id:
            data["customer_id"] = customer_id
        if line_items:
            data["line_items"] = [item.model_dump(exclude_none=True) for item in line_items]
        if billing:
            data["billing"] = billing
        if shipping:
            data["shipping"] = shipping
        if payment_method:
            data["payment_method"] = payment_method

        result = await self._call_mcp("wc_create_order", data)

        if "error" in result:
            logger.error(f"Failed to create order: {result['error']}")
            return None

        return Order(**result.get("order", result))

    async def update_order_status(
        self,
        order_id: int,
        status: OrderStatus,
        note: str | None = None,
    ) -> Order | None:
        """Update order status."""
        params = {"id": order_id, "status": status.value}

        result = await self._call_mcp("wc_update_order", params)

        if "error" in result:
            logger.error(f"Failed to update order {order_id}: {result['error']}")
            return None

        # Add order note if provided
        if note:
            await self._call_mcp(
                "wc_create_order_note",
                {
                    "order_id": order_id,
                    "note": note,
                    "customer_note": False,
                },
            )

        return Order(**result.get("order", result))

    async def refund_order(
        self,
        order_id: int,
        amount: str | None = None,
        reason: str = "",
        restock_items: bool = True,
    ) -> dict:
        """Create refund for an order."""
        params = {
            "order_id": order_id,
            "reason": reason,
            "restock_items": restock_items,
        }
        if amount:
            params["amount"] = amount

        result = await self._call_mcp("wc_create_refund", params)

        if "error" in result:
            # Fallback to REST API
            result = await self._call_wc_rest(
                f"orders/{order_id}/refunds",
                method="POST",
                data=params,
            )

        return result

    # -------------------------------------------------------------------------
    # Customer Operations
    # -------------------------------------------------------------------------

    async def get_customer(self, customer_id: int) -> Customer | None:
        """Get customer by ID."""
        result = await self._call_mcp("wc_get_customer", {"id": customer_id})

        if "error" in result:
            logger.error(f"Failed to get customer {customer_id}: {result['error']}")
            return None

        return Customer(**result.get("customer", result))

    async def search_customers(
        self,
        email: str | None = None,
        search: str | None = None,
        per_page: int = 20,
        page: int = 1,
    ) -> list[Customer]:
        """Search customers."""
        params = {"per_page": per_page, "page": page}
        if email:
            params["email"] = email
        if search:
            params["search"] = search

        result = await self._call_mcp("wc_list_customers", params)

        if "error" in result:
            logger.error(f"Failed to search customers: {result['error']}")
            return []

        customers = result.get("customers", result if isinstance(result, list) else [])
        return [Customer(**c) for c in customers]

    async def create_customer(self, customer: Customer) -> Customer | None:
        """Create a new customer."""
        data = customer.model_dump(exclude_none=True, exclude={"id"})
        result = await self._call_mcp("wc_create_customer", data)

        if "error" in result:
            logger.error(f"Failed to create customer: {result['error']}")
            return None

        return Customer(**result.get("customer", result))

    # -------------------------------------------------------------------------
    # Coupon Operations
    # -------------------------------------------------------------------------

    async def get_coupon(self, coupon_id: int) -> Coupon | None:
        """Get coupon by ID."""
        result = await self._call_mcp("wc_get_coupon", {"id": coupon_id})

        if "error" in result:
            return None

        return Coupon(**result.get("coupon", result))

    async def validate_coupon(self, code: str, cart_total: str | None = None) -> dict:
        """Validate a coupon code."""
        params = {"code": code}
        if cart_total:
            params["cart_total"] = cart_total

        result = await self._call_mcp("wc_validate_coupon", params)

        if "error" in result:
            # Fallback: search coupon by code
            coupons = await self._call_wc_rest(f"coupons?code={code}")
            if isinstance(coupons, list) and coupons:
                coupon = coupons[0]
                return {
                    "valid": True,
                    "coupon": Coupon(**coupon).model_dump(),
                    "discount_type": coupon.get("discount_type"),
                    "amount": coupon.get("amount"),
                }
            return {"valid": False, "error": "Coupon not found"}

        return result

    async def create_coupon(self, coupon: Coupon) -> Coupon | None:
        """Create a new coupon."""
        data = coupon.model_dump(exclude_none=True, exclude={"id"})
        result = await self._call_mcp("wc_create_coupon", data)

        if "error" in result:
            logger.error(f"Failed to create coupon: {result['error']}")
            return None

        return Coupon(**result.get("coupon", result))

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    async def get_store_settings(self) -> dict:
        """Get WooCommerce store settings."""
        result = await self._call_mcp("wc_get_settings", {})
        return result

    async def get_shipping_zones(self) -> list[dict]:
        """Get configured shipping zones."""
        result = await self._call_mcp("wc_list_shipping_zones", {})

        if "error" in result:
            # Fallback to REST API
            result = await self._call_wc_rest("shipping/zones")

        return result if isinstance(result, list) else result.get("zones", [])

    async def get_payment_gateways(self) -> list[dict]:
        """Get available payment gateways."""
        result = await self._call_mcp("wc_list_payment_gateways", {})

        if "error" in result:
            result = await self._call_wc_rest("payment_gateways")

        return result if isinstance(result, list) else result.get("gateways", [])

    async def health_check(self) -> dict:
        """Check WooCommerce API health."""
        try:
            # Try MCP server first
            result = await self._call_mcp("wc_system_status", {})

            if "error" not in result:
                return {
                    "status": "healthy",
                    "mcp_available": True,
                    "wc_version": result.get("wc_version", "unknown"),
                    "wp_version": result.get("wp_version", "unknown"),
                }

            # Fallback to REST API
            result = await self._call_wc_rest("system_status")
            return {
                "status": "healthy",
                "mcp_available": False,
                "wc_version": result.get("environment", {}).get("wc_version", "unknown"),
                "wp_version": result.get("environment", {}).get("wp_version", "unknown"),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }


# =============================================================================
# Singleton Instance
# =============================================================================

_client: WooCommerceMCPClient | None = None


async def get_woocommerce_client() -> WooCommerceMCPClient:
    """Get or create the WooCommerce MCP client singleton."""
    global _client
    if _client is None:
        _client = WooCommerceMCPClient()
        await _client.initialize()
    return _client


# =============================================================================
# CLI Testing
# =============================================================================

if __name__ == "__main__":

    async def main():
        print("WooCommerce MCP Client Test")
        print("=" * 40)

        client = WooCommerceMCPClient()
        await client.initialize()

        # Health check
        health = await client.health_check()
        print(f"Health: {json.dumps(health, indent=2)}")

        # List products
        products = await client.search_products(per_page=5)
        print(f"\nProducts found: {len(products)}")
        for p in products[:3]:
            print(f"  - {p.name} (SKU: {p.sku}, Price: {p.price})")

        await client.close()

    asyncio.run(main())
