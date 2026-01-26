"""
DevSkyy Commerce Tools
======================

Commerce tool implementations with proper specs, permissions, and rate limiting.

Example tools:
- commerce_create_product: Create WooCommerce product
- commerce_update_pricing: Update product pricing
- commerce_get_inventory: Get inventory levels
- commerce_process_order: Process order
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any

import httpx

from core.runtime.tool_registry import (
    ParameterType,
    ToolCategory,
    ToolParameter,
    ToolRegistry,
    ToolSeverity,
    ToolSpec,
)

logger = logging.getLogger(__name__)


# =============================================================================
# WooCommerce Client Configuration
# =============================================================================


class WooCommerceClientError(Exception):
    """WooCommerce API error with status code."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _get_wc_config() -> tuple[str, str, str]:
    """
    Get WooCommerce configuration from environment variables.

    Returns:
        Tuple of (base_url, consumer_key, consumer_secret)

    Raises:
        WooCommerceClientError: If required environment variables are missing
    """
    base_url = os.getenv("WORDPRESS_URL") or os.getenv("WP_URL") or os.getenv("WOOCOMMERCE_URL")
    consumer_key = os.getenv("WC_CONSUMER_KEY") or os.getenv("WOOCOMMERCE_KEY")
    consumer_secret = os.getenv("WC_CONSUMER_SECRET") or os.getenv("WOOCOMMERCE_SECRET")

    if not base_url:
        raise WooCommerceClientError(
            "Missing WooCommerce URL. Set WORDPRESS_URL, WP_URL, or WOOCOMMERCE_URL"
        )
    if not consumer_key:
        raise WooCommerceClientError(
            "Missing WooCommerce consumer key. Set WC_CONSUMER_KEY or WOOCOMMERCE_KEY"
        )
    if not consumer_secret:
        raise WooCommerceClientError(
            "Missing WooCommerce consumer secret. Set WC_CONSUMER_SECRET or WOOCOMMERCE_SECRET"
        )

    # Ensure base URL doesn't have trailing slash
    base_url = base_url.rstrip("/")

    return base_url, consumer_key, consumer_secret


async def _wc_request(
    method: str,
    endpoint: str,
    *,
    json_data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """
    Make an authenticated request to the WooCommerce REST API.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: API endpoint (e.g., "products", "orders/123")
        json_data: JSON body for POST/PUT requests
        params: Query parameters
        timeout: Request timeout in seconds

    Returns:
        API response as dictionary

    Raises:
        WooCommerceClientError: If the request fails
    """
    base_url, consumer_key, consumer_secret = _get_wc_config()

    url = f"{base_url}/wp-json/wc/v3/{endpoint.lstrip('/')}"

    async with httpx.AsyncClient(
        auth=(consumer_key, consumer_secret),
        timeout=timeout,
    ) as client:
        try:
            response = await client.request(
                method=method,
                url=url,
                json=json_data,
                params=params,
            )
            response.raise_for_status()

            if response.status_code == 204:
                return {}

            return response.json()

        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_body = e.response.json()
                error_detail = error_body.get("message", str(error_body))
            except Exception:
                error_detail = e.response.text[:500] if e.response.text else "Unknown error"

            logger.error(
                f"WooCommerce API error: {method} {endpoint} -> {e.response.status_code}: {error_detail}"
            )
            raise WooCommerceClientError(
                f"WooCommerce API error: {error_detail}",
                status_code=e.response.status_code,
            ) from e

        except httpx.RequestError as e:
            logger.error(f"WooCommerce request failed: {method} {endpoint} -> {e}")
            raise WooCommerceClientError(f"Request failed: {e}") from e


# =============================================================================
# Tool Handlers
# =============================================================================


async def commerce_create_product(
    name: str,
    price: float,
    description: str,
    collection: str | None = None,
    sizes: list[str] | None = None,
    images: list[str] | None = None,
) -> dict[str, Any]:
    """
    Create a new product in WooCommerce.

    Args:
        name: Product name
        price: Product price
        description: Product description
        collection: Product collection (BLACK_ROSE, LOVE_HURTS, SIGNATURE)
        sizes: Available sizes
        images: Image URLs

    Returns:
        Created product data with ID
    """
    logger.info(f"Creating product: {name} at ${price}")

    try:
        # Build product data for WooCommerce API
        product_data: dict[str, Any] = {
            "name": name,
            "regular_price": str(price),
            "description": description,
            "status": "draft",
        }

        # Add collection as a category tag in meta_data
        meta_data: list[dict[str, Any]] = []
        if collection:
            meta_data.append({"key": "_skyyrose_collection", "value": collection})

        # Add size attributes if provided
        if sizes:
            product_data["attributes"] = [
                {
                    "name": "Size",
                    "visible": True,
                    "variation": True,
                    "options": sizes,
                }
            ]

        # Add images if provided
        if images:
            product_data["images"] = [{"src": img_url} for img_url in images]

        if meta_data:
            product_data["meta_data"] = meta_data

        # Make API call to create product
        result = await _wc_request("POST", "products", json_data=product_data)

        return {
            "id": result.get("id"),
            "name": result.get("name"),
            "price": float(result.get("regular_price", 0)),
            "description": result.get("description", ""),
            "collection": collection,
            "sizes": sizes or [],
            "images": [img.get("src", "") for img in result.get("images", [])],
            "status": result.get("status", "draft"),
            "created_at": result.get("date_created", datetime.now(UTC).isoformat()),
        }

    except WooCommerceClientError as e:
        logger.error(f"Failed to create product '{name}': {e}")
        return {
            "id": None,
            "name": name,
            "price": price,
            "description": description,
            "collection": collection,
            "sizes": sizes or [],
            "images": images or [],
            "status": "error",
            "error": str(e),
            "created_at": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.exception(f"Unexpected error creating product '{name}': {e}")
        return {
            "id": None,
            "name": name,
            "price": price,
            "description": description,
            "collection": collection,
            "sizes": sizes or [],
            "images": images or [],
            "status": "error",
            "error": f"Unexpected error: {e}",
            "created_at": datetime.now(UTC).isoformat(),
        }


async def commerce_update_pricing(
    product_id: int,
    regular_price: float | None = None,
    sale_price: float | None = None,
) -> dict[str, Any]:
    """
    Update product pricing.

    Args:
        product_id: Product ID
        regular_price: New regular price
        sale_price: New sale price

    Returns:
        Updated product pricing data
    """
    logger.info(f"Updating pricing for product {product_id}")

    try:
        # Build update data - only include prices that are provided
        update_data: dict[str, Any] = {}

        if regular_price is not None:
            update_data["regular_price"] = str(regular_price)

        if sale_price is not None:
            update_data["sale_price"] = str(sale_price)

        if not update_data:
            logger.warning(f"No pricing updates provided for product {product_id}")
            return {
                "product_id": product_id,
                "regular_price": regular_price,
                "sale_price": sale_price,
                "updated_at": datetime.now(UTC).isoformat(),
                "status": "no_changes",
            }

        # Make API call to update product
        result = await _wc_request("PUT", f"products/{product_id}", json_data=update_data)

        return {
            "product_id": result.get("id"),
            "regular_price": (
                float(result.get("regular_price", 0)) if result.get("regular_price") else None
            ),
            "sale_price": float(result.get("sale_price", 0)) if result.get("sale_price") else None,
            "updated_at": result.get("date_modified", datetime.now(UTC).isoformat()),
            "status": "updated",
        }

    except WooCommerceClientError as e:
        logger.error(f"Failed to update pricing for product {product_id}: {e}")
        return {
            "product_id": product_id,
            "regular_price": regular_price,
            "sale_price": sale_price,
            "updated_at": datetime.now(UTC).isoformat(),
            "status": "error",
            "error": str(e),
        }
    except Exception as e:
        logger.exception(f"Unexpected error updating pricing for product {product_id}: {e}")
        return {
            "product_id": product_id,
            "regular_price": regular_price,
            "sale_price": sale_price,
            "updated_at": datetime.now(UTC).isoformat(),
            "status": "error",
            "error": f"Unexpected error: {e}",
        }


async def commerce_get_inventory(
    product_id: int | None = None,
    sku: str | None = None,
    low_stock_only: bool = False,
) -> dict[str, Any]:
    """
    Get inventory levels.

    Args:
        product_id: Product ID (optional)
        sku: Product SKU (optional)
        low_stock_only: Return only low stock items

    Returns:
        Inventory data
    """
    logger.info(f"Getting inventory for product_id={product_id}, sku={sku}")

    # Default low stock threshold (WooCommerce default)
    low_stock_threshold = 10

    try:
        items: list[dict[str, Any]] = []

        if product_id:
            # Get single product by ID
            result = await _wc_request("GET", f"products/{product_id}")

            stock_quantity = result.get("stock_quantity")
            is_low_stock = stock_quantity is not None and stock_quantity <= low_stock_threshold

            if not low_stock_only or is_low_stock:
                items.append(
                    {
                        "product_id": result.get("id"),
                        "sku": result.get("sku", ""),
                        "name": result.get("name", ""),
                        "stock": stock_quantity,
                        "stock_status": result.get("stock_status", ""),
                        "manage_stock": result.get("manage_stock", False),
                        "low_stock": is_low_stock,
                    }
                )

        elif sku:
            # Search by SKU
            result = await _wc_request("GET", "products", params={"sku": sku})

            if isinstance(result, list) and result:
                product = result[0]
                stock_quantity = product.get("stock_quantity")
                is_low_stock = stock_quantity is not None and stock_quantity <= low_stock_threshold

                if not low_stock_only or is_low_stock:
                    items.append(
                        {
                            "product_id": product.get("id"),
                            "sku": product.get("sku", ""),
                            "name": product.get("name", ""),
                            "stock": stock_quantity,
                            "stock_status": product.get("stock_status", ""),
                            "manage_stock": product.get("manage_stock", False),
                            "low_stock": is_low_stock,
                        }
                    )

        else:
            # Get all products with managed stock
            params: dict[str, Any] = {
                "per_page": 100,
                "stock_status": "instock,outofstock,onbackorder",
            }

            result = await _wc_request("GET", "products", params=params)

            if isinstance(result, list):
                for product in result:
                    stock_quantity = product.get("stock_quantity")
                    is_low_stock = (
                        stock_quantity is not None and stock_quantity <= low_stock_threshold
                    )

                    if not low_stock_only or is_low_stock:
                        items.append(
                            {
                                "product_id": product.get("id"),
                                "sku": product.get("sku", ""),
                                "name": product.get("name", ""),
                                "stock": stock_quantity,
                                "stock_status": product.get("stock_status", ""),
                                "manage_stock": product.get("manage_stock", False),
                                "low_stock": is_low_stock,
                            }
                        )

        return {
            "items": items,
            "count": len(items),
            "low_stock_threshold": low_stock_threshold,
            "low_stock_only": low_stock_only,
            "retrieved_at": datetime.now(UTC).isoformat(),
        }

    except WooCommerceClientError as e:
        logger.error(f"Failed to get inventory: {e}")
        return {
            "items": [],
            "count": 0,
            "low_stock_threshold": low_stock_threshold,
            "error": str(e),
            "retrieved_at": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.exception(f"Unexpected error getting inventory: {e}")
        return {
            "items": [],
            "count": 0,
            "low_stock_threshold": low_stock_threshold,
            "error": f"Unexpected error: {e}",
            "retrieved_at": datetime.now(UTC).isoformat(),
        }


async def commerce_process_order(
    order_id: int,
    action: str,
    notes: str | None = None,
) -> dict[str, Any]:
    """
    Process order (fulfill, cancel, refund, etc).

    Args:
        order_id: Order ID
        action: Action to perform (fulfill, cancel, refund, hold)
        notes: Optional notes

    Returns:
        Order processing result
    """
    logger.info(f"Processing order {order_id}: {action}")

    # Map action to WooCommerce order status
    action_to_status: dict[str, str] = {
        "fulfill": "completed",
        "cancel": "cancelled",
        "refund": "refunded",
        "hold": "on-hold",
    }

    if action not in action_to_status:
        logger.error(f"Invalid action '{action}' for order {order_id}")
        return {
            "order_id": order_id,
            "action": action,
            "notes": notes,
            "status": "error",
            "error": f"Invalid action: {action}. Valid actions: {list(action_to_status.keys())}",
            "processed_at": datetime.now(UTC).isoformat(),
        }

    try:
        new_status = action_to_status[action]

        # Handle refund separately - requires creating a refund object
        if action == "refund":
            # First get the order to get the total
            order = await _wc_request("GET", f"orders/{order_id}")
            order_total = order.get("total", "0")

            # Create refund
            refund_data: dict[str, Any] = {
                "amount": order_total,
                "reason": notes or "Refund requested",
            }

            refund_result = await _wc_request(
                "POST",
                f"orders/{order_id}/refunds",
                json_data=refund_data,
            )

            return {
                "order_id": order_id,
                "action": action,
                "notes": notes,
                "status": "refunded",
                "refund_id": refund_result.get("id"),
                "refund_amount": refund_result.get("amount"),
                "processed_at": refund_result.get("date_created", datetime.now(UTC).isoformat()),
            }

        # For other actions, update order status
        update_data: dict[str, Any] = {"status": new_status}

        result = await _wc_request("PUT", f"orders/{order_id}", json_data=update_data)

        # Add order note if provided
        if notes:
            note_data = {
                "note": notes,
                "customer_note": False,
            }
            await _wc_request("POST", f"orders/{order_id}/notes", json_data=note_data)

        return {
            "order_id": result.get("id"),
            "action": action,
            "notes": notes,
            "status": result.get("status"),
            "previous_status": order.get("status") if "order" in dir() else None,
            "processed_at": result.get("date_modified", datetime.now(UTC).isoformat()),
        }

    except WooCommerceClientError as e:
        logger.error(f"Failed to process order {order_id} ({action}): {e}")
        return {
            "order_id": order_id,
            "action": action,
            "notes": notes,
            "status": "error",
            "error": str(e),
            "processed_at": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.exception(f"Unexpected error processing order {order_id} ({action}): {e}")
        return {
            "order_id": order_id,
            "action": action,
            "notes": notes,
            "status": "error",
            "error": f"Unexpected error: {e}",
            "processed_at": datetime.now(UTC).isoformat(),
        }


# =============================================================================
# Tool Registration
# =============================================================================


def register_commerce_tools(registry: ToolRegistry) -> None:
    """
    Register all commerce tools with the registry.

    Args:
        registry: ToolRegistry instance to register tools with
    """
    # Create Product Tool
    create_product_spec = ToolSpec(
        name="commerce_create_product",
        description="Create a new product in WooCommerce with full details",
        category=ToolCategory.COMMERCE,
        severity=ToolSeverity.MEDIUM,  # Creates data
        parameters=[
            ToolParameter(
                name="name",
                type=ParameterType.STRING,
                description="Product name",
                required=True,
                min_length=3,
                max_length=200,
            ),
            ToolParameter(
                name="price",
                type=ParameterType.NUMBER,
                description="Product price in USD",
                required=True,
                min_value=0.01,
            ),
            ToolParameter(
                name="description",
                type=ParameterType.STRING,
                description="Product description",
                required=True,
                min_length=10,
            ),
            ToolParameter(
                name="collection",
                type=ParameterType.STRING,
                description="Product collection",
                enum=["BLACK_ROSE", "LOVE_HURTS", "SIGNATURE"],
            ),
            ToolParameter(
                name="sizes",
                type=ParameterType.ARRAY,
                description="Available sizes",
                items={"type": "string"},
            ),
            ToolParameter(
                name="images",
                type=ParameterType.ARRAY,
                description="Image URLs",
                items={"type": "string"},
            ),
        ],
        permissions={"commerce:write", "products:create"},
        requires_auth=True,
        rate_limit=20,  # 20 requests per minute
        timeout_seconds=30.0,
        idempotent=False,
        cacheable=False,
        tags={"commerce", "products"},
        # Advanced Tool Use
        defer_loading=True,
        allowed_callers=["code_execution_20250825"],  # Enable PTC for batch creation
        input_examples=[
            {
                "name": "Heart aRose Bomber Jacket",
                "price": 299.99,
                "description": "Premium bomber with rose gold accents",
                "collection": "BLACK_ROSE",
                "sizes": ["S", "M", "L", "XL"],
            },
            {
                "name": "Love Hurts Hoodie",
                "price": 149.99,
                "description": "Oversized hoodie with signature thorns",
                "collection": "LOVE_HURTS",
            },
        ],
    )
    registry.register(create_product_spec, commerce_create_product)

    # Update Pricing Tool
    update_pricing_spec = ToolSpec(
        name="commerce_update_pricing",
        description="Update product pricing (regular and sale prices)",
        category=ToolCategory.COMMERCE,
        severity=ToolSeverity.HIGH,  # Affects pricing
        parameters=[
            ToolParameter(
                name="product_id",
                type=ParameterType.INTEGER,
                description="Product ID",
                required=True,
                min_value=1,
            ),
            ToolParameter(
                name="regular_price",
                type=ParameterType.NUMBER,
                description="New regular price",
                min_value=0.01,
            ),
            ToolParameter(
                name="sale_price",
                type=ParameterType.NUMBER,
                description="New sale price",
                min_value=0.01,
            ),
        ],
        permissions={"commerce:write", "pricing:update"},
        requires_auth=True,
        rate_limit=10,  # 10 requests per minute (more sensitive)
        timeout_seconds=30.0,
        idempotent=True,  # Same price update = same result
        cacheable=False,
        tags={"commerce", "pricing"},
        # Advanced Tool Use
        defer_loading=True,
        allowed_callers=["code_execution_20250825"],  # Enable PTC for batch updates
        input_examples=[
            {"product_id": 123, "regular_price": 199.99, "sale_price": 149.99},
            {"product_id": 456, "regular_price": 299.99},
        ],
    )
    registry.register(update_pricing_spec, commerce_update_pricing)

    # Get Inventory Tool
    get_inventory_spec = ToolSpec(
        name="commerce_get_inventory",
        description="Get current inventory levels for products",
        category=ToolCategory.COMMERCE,
        severity=ToolSeverity.READ_ONLY,  # Read-only
        parameters=[
            ToolParameter(
                name="product_id",
                type=ParameterType.INTEGER,
                description="Product ID to check",
                min_value=1,
            ),
            ToolParameter(
                name="sku",
                type=ParameterType.STRING,
                description="Product SKU to check",
            ),
            ToolParameter(
                name="low_stock_only",
                type=ParameterType.BOOLEAN,
                description="Return only low stock items",
                default=False,
            ),
        ],
        permissions={"commerce:read", "inventory:read"},
        requires_auth=True,
        rate_limit=100,  # 100 requests per minute (read-only, higher limit)
        timeout_seconds=15.0,
        idempotent=True,
        cacheable=True,
        cache_ttl_seconds=60,  # Cache for 1 minute
        tags={"commerce", "inventory", "read-only"},
        # Advanced Tool Use - READ_ONLY auto-enables PTC
    )
    registry.register(get_inventory_spec, commerce_get_inventory)

    # Process Order Tool
    process_order_spec = ToolSpec(
        name="commerce_process_order",
        description="Process order actions (fulfill, cancel, refund)",
        category=ToolCategory.COMMERCE,
        severity=ToolSeverity.DESTRUCTIVE,  # Can cancel/refund
        parameters=[
            ToolParameter(
                name="order_id",
                type=ParameterType.INTEGER,
                description="Order ID",
                required=True,
                min_value=1,
            ),
            ToolParameter(
                name="action",
                type=ParameterType.STRING,
                description="Action to perform",
                required=True,
                enum=["fulfill", "cancel", "refund", "hold"],
            ),
            ToolParameter(
                name="notes",
                type=ParameterType.STRING,
                description="Optional processing notes",
                max_length=500,
            ),
        ],
        permissions={"commerce:write", "orders:process"},
        requires_auth=True,
        rate_limit=5,  # 5 requests per minute (very sensitive)
        timeout_seconds=60.0,  # Longer timeout for order processing
        idempotent=False,  # Order actions have side effects
        cacheable=False,
        tags={"commerce", "orders", "destructive"},
        # Advanced Tool Use
        input_examples=[
            {"order_id": 789, "action": "fulfill", "notes": "Shipped via UPS"},
            {"order_id": 790, "action": "refund", "notes": "Customer requested refund"},
        ],
    )
    registry.register(process_order_spec, commerce_process_order)

    logger.info("Registered 4 commerce tools with ToolRegistry")
