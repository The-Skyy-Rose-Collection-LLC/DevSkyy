"""WooCommerce MCP tools — 429-safe client exposed as 5 tools.

Closes archive Pattern #2: the existing tooling crashed on first GET 429
because retry logic was only on write paths. These tools route through
`skyyrose.integrations.wc_safe_client.WCSafeClient`, which retries on EVERY
verb (GET, POST, PUT, PATCH, DELETE).

Tools:
    wc_get_products    — paginated product list
    wc_get_product     — single product by ID
    wc_get_orders      — paginated order list
    wc_update_product  — mutation (gated by confirm + paid-api-stopgate)
    wc_smoketest       — single-call session preflight (replaces archive Pattern #8)
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from mcp_tools.api_client import _format_response
from mcp_tools.security import secure_tool
from mcp_tools.server import mcp
from mcp_tools.types import BaseAgentInput


def _extract_error(response: Any) -> str:
    """Pull a clean error string from a WC response.

    Prefer the JSON `{code, message}` shape that WC errors normally return.
    Fall back to truncated text only if JSON parse fails — and even then,
    keep it short and never include raw HTML/PHP error pages that could
    contain server paths, SQL fragments, or echoed query strings.
    """
    try:
        body = response.json()
    except Exception:
        body = None
    if isinstance(body, dict):
        code = body.get("code", "")
        message = body.get("message", "")
        if code or message:
            return f"{code}: {message}".strip(": ")
    # Last-resort fallback — keep short, strip HTML-ish content.
    text = response.text
    if "<" in text:
        text = "error page returned (HTML, redacted to avoid leaking server detail)"
    return text[:200]


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class GetProductsInput(BaseAgentInput):
    per_page: int = Field(default=100, ge=1, le=100)
    page: int = Field(default=1, ge=1)
    status: Literal["any", "draft", "pending", "private", "publish"] = Field(default="any")
    sku: str | None = Field(default=None, max_length=64)


class GetProductInput(BaseAgentInput):
    product_id: int = Field(..., gt=0)


class GetOrdersInput(BaseAgentInput):
    per_page: int = Field(default=50, ge=1, le=100)
    page: int = Field(default=1, ge=1)
    status: Literal[
        "any", "pending", "processing", "on-hold", "completed", "cancelled", "refunded", "failed"
    ] = Field(default="any")


class UpdateProductInput(BaseAgentInput):
    product_id: int = Field(..., gt=0)
    fields: dict[str, Any] = Field(..., description="Fields to update (per WC REST API schema).")
    confirm: bool = Field(
        default=False,
        description="Must be True. Production WC writes are gated by paid-api-stopgate.",
    )


class SmoketestInput(BaseAgentInput):
    pass  # No params — single ping with retry.


# ---------------------------------------------------------------------------
# Input models — 6 new tools
# ---------------------------------------------------------------------------


class UpdateStockInput(BaseAgentInput):
    product_id: int = Field(..., gt=0, description="WooCommerce product ID.")
    stock_quantity: int = Field(..., description="Absolute stock quantity to set.")
    variation_id: int | None = Field(
        default=None, gt=0, description="Variation ID for variable products."
    )
    stock_status: Literal["instock", "outofstock", "onbackorder"] | None = Field(
        default=None, description="Explicit stock status override (optional)."
    )
    confirm: bool = Field(
        default=False,
        description="Must be True. Production WC write gated by paid-api-stopgate.",
    )


class UpdateOrderStatusInput(BaseAgentInput):
    order_id: int = Field(..., gt=0, description="WooCommerce order ID.")
    status: Literal[
        "pending", "processing", "on-hold", "completed", "cancelled", "refunded", "failed"
    ] = Field(..., description="Target order status.")
    note: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional order note appended alongside the status change.",
    )
    confirm: bool = Field(
        default=False,
        description="Must be True. Production WC write gated by paid-api-stopgate.",
    )


class SearchCustomersInput(BaseAgentInput):
    email: str | None = Field(default=None, max_length=254, description="Exact email match.")
    search: str | None = Field(
        default=None, max_length=200, description="Search term for name or email (partial)."
    )
    per_page: int = Field(default=20, ge=1, le=100)
    page: int = Field(default=1, ge=1)


class ValidateCouponInput(BaseAgentInput):
    code: str = Field(..., min_length=1, max_length=200, description="Coupon code to validate.")
    cart_total: str | None = Field(
        default=None,
        max_length=32,
        description="Optional cart total (decimal string) to check minimum/maximum amount constraints.",
    )


class GetStoreSettingsInput(BaseAgentInput):
    pass  # No params beyond response_format.


class ListOrdersInput(BaseAgentInput):
    status: Literal[
        "any", "pending", "processing", "on-hold", "completed", "cancelled", "refunded", "failed"
    ] = Field(default="any", description="Filter by WooCommerce order status.")
    customer_id: int | None = Field(default=None, gt=0, description="Filter orders by customer ID.")
    after: str | None = Field(
        default=None,
        max_length=32,
        description="ISO 8601 datetime — return orders created after this date.",
    )
    before: str | None = Field(
        default=None,
        max_length=32,
        description="ISO 8601 datetime — return orders created before this date.",
    )
    per_page: int = Field(default=20, ge=1, le=100)
    page: int = Field(default=1, ge=1)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="wc_get_products",
    annotations={
        "title": "WooCommerce — paginated product list (429-safe)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@secure_tool("wc_get_products")
async def wc_get_products(params: GetProductsInput) -> str:
    """List products with automatic 429/503 retry.

    Returns a slim summary (id, sku, name, status, stock_status, price) — full
    product payloads from WC v3 are ~30KB each and would exceed CHARACTER_LIMIT
    on the first page.
    """
    from skyyrose.integrations.wc_safe_client import WCSafeClient

    query: dict[str, Any] = {"per_page": params.per_page, "page": params.page}
    if params.status != "any":
        query["status"] = params.status
    if params.sku:
        query["sku"] = params.sku

    async with WCSafeClient.from_env() as client:
        response = await client.get("products", params=query)

    if response.status_code != 200:
        report = {
            "ok": False,
            "status_code": response.status_code,
            "error": _extract_error(response),
        }
        return _format_response(report, params.response_format, "WC error")

    raw = response.json()
    slim = [
        {
            "id": p.get("id"),
            "sku": p.get("sku"),
            "name": p.get("name"),
            "status": p.get("status"),
            "stock_status": p.get("stock_status"),
            "price": p.get("price"),
        }
        for p in raw
    ]
    report = {
        "ok": True,
        "page": params.page,
        "per_page": params.per_page,
        "count": len(slim),
        "products": slim,
    }
    return _format_response(report, params.response_format, "WC products")


@mcp.tool(
    name="wc_get_product",
    annotations={
        "title": "WooCommerce — single product (429-safe)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@secure_tool("wc_get_product")
async def wc_get_product(params: GetProductInput) -> str:
    """Fetch a single product by ID with automatic 429/503 retry."""
    from skyyrose.integrations.wc_safe_client import WCSafeClient

    async with WCSafeClient.from_env() as client:
        response = await client.get(f"products/{params.product_id}")

    if response.status_code == 404:
        report = {"ok": False, "error": f"product {params.product_id} not found"}
        return _format_response(report, params.response_format, "Not found")
    if response.status_code != 200:
        report = {
            "ok": False,
            "status_code": response.status_code,
            "error": _extract_error(response),
        }
        return _format_response(report, params.response_format, "WC error")

    return _format_response(
        {"ok": True, "product": response.json()}, params.response_format, "WC product"
    )


@mcp.tool(
    name="wc_get_orders",
    annotations={
        "title": "WooCommerce — paginated order list (429-safe)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@secure_tool("wc_get_orders")
async def wc_get_orders(params: GetOrdersInput) -> str:
    """List orders with automatic 429/503 retry."""
    from skyyrose.integrations.wc_safe_client import WCSafeClient

    query: dict[str, Any] = {"per_page": params.per_page, "page": params.page}
    if params.status != "any":
        query["status"] = params.status

    async with WCSafeClient.from_env() as client:
        response = await client.get("orders", params=query)

    if response.status_code != 200:
        report = {
            "ok": False,
            "status_code": response.status_code,
            "error": _extract_error(response),
        }
        return _format_response(report, params.response_format, "WC error")

    raw = response.json()
    slim = [
        {
            "id": o.get("id"),
            "status": o.get("status"),
            "total": o.get("total"),
            "currency": o.get("currency"),
            "date_created": o.get("date_created"),
            "customer_id": o.get("customer_id"),
            "line_items_count": len(o.get("line_items", [])),
        }
        for o in raw
    ]
    return _format_response(
        {"ok": True, "page": params.page, "count": len(slim), "orders": slim},
        params.response_format,
        "WC orders",
    )


@mcp.tool(
    name="wc_update_product",
    annotations={
        "title": "WooCommerce — update product (gated, 429-safe)",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
@secure_tool("wc_update_product")
async def wc_update_product(params: UpdateProductInput) -> str:
    """Update a WooCommerce product (production mutation).

    Refuses unless `confirm=True`. Even with confirm, the paid-api-stopgate
    hook will intercept `wp post update` shell invocations elsewhere.
    """
    if not params.confirm:
        return _format_response(
            {
                "dry_run": True,
                "product_id": params.product_id,
                "fields_to_update": list(params.fields.keys()),
                "note": "production write — set confirm=True to dispatch",
            },
            params.response_format,
            "WC update plan (dry-run)",
        )

    from skyyrose.integrations.wc_safe_client import WCSafeClient

    async with WCSafeClient.from_env() as client:
        response = await client.put(f"products/{params.product_id}", json=params.fields)

    if response.status_code not in (200, 201):
        report = {
            "ok": False,
            "status_code": response.status_code,
            "error": _extract_error(response),
        }
        return _format_response(report, params.response_format, "WC update FAILED")

    return _format_response(
        {"ok": True, "product_id": params.product_id, "updated": response.json()},
        params.response_format,
        "WC update OK",
    )


@mcp.tool(
    name="wc_smoketest",
    annotations={
        "title": "WC session preflight — single retrying GET",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@secure_tool("wc_smoketest")
async def wc_smoketest(params: SmoketestInput) -> str:
    """Single-call session preflight. Returns ok/fail in one shot.

    Replaces archive Pattern #8 ritual: locate .env.wordpress, verify creds
    populated, ping WC API. One MCP call does all 3 with proper 429 retry.
    """
    from skyyrose.integrations.wc_safe_client import WCCredentials, WCSafeClient

    # Stage 1: credentials present + non-placeholder
    try:
        creds = WCCredentials.from_env()
    except KeyError as exc:
        return _format_response(
            {"ok": False, "stage": "env", "error": f"missing env var: {exc}"},
            params.response_format,
            "Smoketest FAILED",
        )

    placeholder_markers = ("YOUR_", "PLACEHOLDER", "CHANGE_ME", "xxx")
    for field_name, value in [
        ("consumer_key", creds.consumer_key),
        ("consumer_secret", creds.consumer_secret),
    ]:
        if any(marker.lower() in value.lower() for marker in placeholder_markers):
            return _format_response(
                {"ok": False, "stage": "env", "error": f"{field_name} appears to be a placeholder"},
                params.response_format,
                "Smoketest FAILED",
            )

    # Stage 2: ping WC (1 product fetch — cheap)
    async with WCSafeClient(creds) as client:
        response = await client.get("products", params={"per_page": 1})

    return _format_response(
        {
            "ok": response.status_code == 200,
            "stage": "api_ping",
            "status_code": response.status_code,
            "base_url": creds.base_url,
            "note": "All retries on 429/503 are applied transparently.",
        },
        params.response_format,
        "Smoketest OK" if response.status_code == 200 else "Smoketest FAILED",
    )


# ---------------------------------------------------------------------------
# 6 new tools ported from mcp_servers/woocommerce_mcp.py
# ---------------------------------------------------------------------------


@mcp.tool(
    name="wc_update_stock",
    annotations={
        "title": "WooCommerce — update product stock (gated, 429-safe)",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
@secure_tool("wc_update_stock")
async def wc_update_stock(params: UpdateStockInput) -> str:
    """Set absolute stock quantity for a product or variation (production mutation).

    Refuses unless ``confirm=True``.  Supports both simple products and
    individual variations of variable products.

    Args:
        params.product_id: WooCommerce product ID.
        params.stock_quantity: New absolute stock quantity.
        params.variation_id: Optional variation ID (variable products only).
        params.stock_status: Optional override for stock status
            (instock | outofstock | onbackorder).  When omitted WooCommerce
            derives the status from the quantity automatically.
        params.confirm: Must be True to dispatch the live write.

    Returns:
        JSON/markdown with updated product stock fields or a dry-run manifest.
    """
    if not params.confirm:
        return _format_response(
            {
                "dry_run": True,
                "product_id": params.product_id,
                "variation_id": params.variation_id,
                "stock_quantity": params.stock_quantity,
                "stock_status": params.stock_status,
                "note": "production write — set confirm=True to dispatch",
            },
            params.response_format,
            "wc_update_stock (dry-run)",
        )

    from skyyrose.integrations.wc_safe_client import WCSafeClient

    payload: dict[str, Any] = {
        "manage_stock": True,
        "stock_quantity": params.stock_quantity,
    }
    if params.stock_status is not None:
        payload["stock_status"] = params.stock_status

    endpoint = f"products/{params.product_id}"
    if params.variation_id is not None:
        endpoint = f"products/{params.product_id}/variations/{params.variation_id}"

    try:
        async with WCSafeClient.from_env() as client:
            response = await client.put(endpoint, json=payload)
    except Exception as exc:
        return _format_response(
            {"ok": False, "error": str(exc)},
            params.response_format,
            "wc_update_stock FAILED",
        )

    if response.status_code not in (200, 201):
        return _format_response(
            {
                "ok": False,
                "status_code": response.status_code,
                "error": _extract_error(response),
            },
            params.response_format,
            "wc_update_stock FAILED",
        )

    body = response.json()
    return _format_response(
        {
            "ok": True,
            "product_id": params.product_id,
            "variation_id": params.variation_id,
            "stock_quantity": body.get("stock_quantity"),
            "stock_status": body.get("stock_status"),
        },
        params.response_format,
        "wc_update_stock OK",
    )


@mcp.tool(
    name="wc_update_order_status",
    annotations={
        "title": "WooCommerce — update order status (gated, 429-safe)",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
@secure_tool("wc_update_order_status")
async def wc_update_order_status(params: UpdateOrderStatusInput) -> str:
    """Transition a WooCommerce order to a new status (production mutation).

    Refuses unless ``confirm=True``.  An optional order note is appended via a
    second PUT to ``orders/{id}/notes`` only when the status update succeeds.

    Args:
        params.order_id: WooCommerce order ID.
        params.status: Target status (pending | processing | on-hold | completed
            | cancelled | refunded | failed).
        params.note: Optional private order note.
        params.confirm: Must be True to dispatch the live write.

    Returns:
        JSON/markdown with slim order fields (id, number, status, total) or dry-run plan.
    """
    if not params.confirm:
        return _format_response(
            {
                "dry_run": True,
                "order_id": params.order_id,
                "new_status": params.status,
                "note": params.note,
                "message": "production write — set confirm=True to dispatch",
            },
            params.response_format,
            "wc_update_order_status (dry-run)",
        )

    from skyyrose.integrations.wc_safe_client import WCSafeClient

    try:
        async with WCSafeClient.from_env() as client:
            response = await client.put(
                f"orders/{params.order_id}",
                json={"status": params.status},
            )
    except Exception as exc:
        return _format_response(
            {"ok": False, "error": str(exc)},
            params.response_format,
            "wc_update_order_status FAILED",
        )

    if response.status_code not in (200, 201):
        return _format_response(
            {
                "ok": False,
                "status_code": response.status_code,
                "error": _extract_error(response),
            },
            params.response_format,
            "wc_update_order_status FAILED",
        )

    body = response.json()

    # Append order note when supplied — non-fatal if this secondary call fails.
    if params.note:
        try:
            async with WCSafeClient.from_env() as client:
                await client.post(
                    f"orders/{params.order_id}/notes",
                    json={"note": params.note, "customer_note": False},
                )
        except Exception:
            pass  # Note is advisory; status update already succeeded.

    return _format_response(
        {
            "ok": True,
            "order_id": body.get("id"),
            "order_number": body.get("number"),
            "status": body.get("status"),
            "total": body.get("total"),
            "note_appended": bool(params.note),
        },
        params.response_format,
        "wc_update_order_status OK",
    )


@mcp.tool(
    name="wc_search_customers",
    annotations={
        "title": "WooCommerce — search customers (429-safe)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@secure_tool("wc_search_customers")
async def wc_search_customers(params: SearchCustomersInput) -> str:
    """Search WooCommerce customers by email or name.

    At least one of ``email`` or ``search`` should be supplied for a useful
    result; passing neither returns the first page of all customers.

    Args:
        params.email: Exact email address match.
        params.search: Partial name or email search term.
        params.per_page: Page size (1–100, default 20).
        params.page: Page number (default 1).

    Returns:
        JSON/markdown with slim customer list (id, email, first_name,
        last_name, orders_count, total_spent).
    """
    from skyyrose.integrations.wc_safe_client import WCSafeClient

    query: dict[str, Any] = {"per_page": params.per_page, "page": params.page}
    if params.email:
        query["email"] = params.email
    if params.search:
        query["search"] = params.search

    try:
        async with WCSafeClient.from_env() as client:
            response = await client.get("customers", params=query)
    except Exception as exc:
        return _format_response(
            {"ok": False, "error": str(exc)},
            params.response_format,
            "wc_search_customers FAILED",
        )

    if response.status_code != 200:
        return _format_response(
            {
                "ok": False,
                "status_code": response.status_code,
                "error": _extract_error(response),
            },
            params.response_format,
            "wc_search_customers FAILED",
        )

    raw = response.json()
    slim = [
        {
            "id": c.get("id"),
            "email": c.get("email"),
            "first_name": c.get("first_name"),
            "last_name": c.get("last_name"),
            "username": c.get("username"),
            "orders_count": c.get("orders_count"),
            "total_spent": c.get("total_spent"),
        }
        for c in raw
    ]
    return _format_response(
        {"ok": True, "page": params.page, "count": len(slim), "customers": slim},
        params.response_format,
        "WC customers",
    )


@mcp.tool(
    name="wc_validate_coupon",
    annotations={
        "title": "WooCommerce — validate coupon code (429-safe)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@secure_tool("wc_validate_coupon")
async def wc_validate_coupon(params: ValidateCouponInput) -> str:
    """Validate a WooCommerce coupon code.

    Looks up the coupon by code via ``GET /coupons?code=…``.  Validates
    expiry, usage limits, and — when ``cart_total`` is supplied — checks
    minimum/maximum cart amount constraints.

    Args:
        params.code: Coupon code to validate.
        params.cart_total: Optional cart total (decimal string, e.g. ``"49.99"``)
            used to validate minimum/maximum amount rules.

    Returns:
        JSON/markdown with ``valid`` flag, discount type, amount, and any
        constraint violations.
    """
    from skyyrose.integrations.wc_safe_client import WCSafeClient

    try:
        async with WCSafeClient.from_env() as client:
            response = await client.get("coupons", params={"code": params.code})
    except Exception as exc:
        return _format_response(
            {"ok": False, "valid": False, "error": str(exc)},
            params.response_format,
            "wc_validate_coupon FAILED",
        )

    if response.status_code != 200:
        return _format_response(
            {
                "ok": False,
                "valid": False,
                "status_code": response.status_code,
                "error": _extract_error(response),
            },
            params.response_format,
            "wc_validate_coupon FAILED",
        )

    coupons = response.json()
    if not isinstance(coupons, list) or not coupons:
        return _format_response(
            {"ok": True, "valid": False, "reason": "coupon code not found"},
            params.response_format,
            "wc_validate_coupon",
        )

    coupon = coupons[0]

    # Check expiry.
    from datetime import UTC, datetime

    date_expires = coupon.get("date_expires")
    if date_expires:
        try:
            expires_dt = datetime.fromisoformat(date_expires.replace("Z", "+00:00"))
            if datetime.now(UTC) > expires_dt:
                return _format_response(
                    {
                        "ok": True,
                        "valid": False,
                        "reason": f"coupon expired on {date_expires}",
                        "code": params.code,
                    },
                    params.response_format,
                    "wc_validate_coupon",
                )
        except ValueError:
            pass  # Unparseable expiry — treat as non-expiring.

    # Check usage limit.
    usage_limit = coupon.get("usage_limit")
    usage_count = coupon.get("usage_count", 0)
    if usage_limit is not None and usage_count >= usage_limit:
        return _format_response(
            {
                "ok": True,
                "valid": False,
                "reason": f"usage limit reached ({usage_count}/{usage_limit})",
                "code": params.code,
            },
            params.response_format,
            "wc_validate_coupon",
        )

    # Check minimum/maximum cart amount when cart_total provided.
    if params.cart_total is not None:
        try:
            total_f = float(params.cart_total)
            minimum = coupon.get("minimum_amount")
            maximum = coupon.get("maximum_amount")
            if minimum and float(minimum) > total_f:
                return _format_response(
                    {
                        "ok": True,
                        "valid": False,
                        "reason": f"cart total {params.cart_total} is below minimum {minimum}",
                        "code": params.code,
                    },
                    params.response_format,
                    "wc_validate_coupon",
                )
            if maximum and float(maximum) < total_f:
                return _format_response(
                    {
                        "ok": True,
                        "valid": False,
                        "reason": f"cart total {params.cart_total} exceeds maximum {maximum}",
                        "code": params.code,
                    },
                    params.response_format,
                    "wc_validate_coupon",
                )
        except ValueError:
            pass  # Non-numeric cart_total or coupon amounts — skip constraint checks.

    return _format_response(
        {
            "ok": True,
            "valid": True,
            "code": params.code,
            "discount_type": coupon.get("discount_type"),
            "amount": coupon.get("amount"),
            "usage_count": usage_count,
            "usage_limit": usage_limit,
            "date_expires": date_expires,
            "minimum_amount": coupon.get("minimum_amount"),
            "maximum_amount": coupon.get("maximum_amount"),
        },
        params.response_format,
        "wc_validate_coupon",
    )


@mcp.tool(
    name="wc_get_store_settings",
    annotations={
        "title": "WooCommerce — store settings (429-safe)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@secure_tool("wc_get_store_settings")
async def wc_get_store_settings(params: GetStoreSettingsInput) -> str:
    """Retrieve WooCommerce store configuration.

    Fetches the ``general`` settings group from ``GET /settings/general``,
    which includes currency, store address, weight/dimension units, and
    tax settings.

    Returns:
        JSON/markdown key-value map of store configuration options.
    """
    from skyyrose.integrations.wc_safe_client import WCSafeClient

    try:
        async with WCSafeClient.from_env() as client:
            response = await client.get("settings/general")
    except Exception as exc:
        return _format_response(
            {"ok": False, "error": str(exc)},
            params.response_format,
            "wc_get_store_settings FAILED",
        )

    if response.status_code != 200:
        return _format_response(
            {
                "ok": False,
                "status_code": response.status_code,
                "error": _extract_error(response),
            },
            params.response_format,
            "wc_get_store_settings FAILED",
        )

    raw = response.json()
    # WC returns a list of setting objects: [{id, label, value, ...}, ...]
    # Flatten to {id: value} for a compact, usable payload.
    if isinstance(raw, list):
        settings: dict[str, Any] = {
            item.get("id", f"setting_{i}"): item.get("value") for i, item in enumerate(raw)
        }
    else:
        settings = raw  # Already a dict on some WC versions.

    return _format_response(
        {"ok": True, "settings": settings},
        params.response_format,
        "WC store settings",
    )


@mcp.tool(
    name="wc_list_orders",
    annotations={
        "title": "WooCommerce — filtered order list (429-safe)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@secure_tool("wc_list_orders")
async def wc_list_orders(params: ListOrdersInput) -> str:
    """List WooCommerce orders with status, customer, and date filters.

    Extends ``wc_get_orders`` with additional filter parameters:
    ``customer_id``, ``after`` (ISO 8601), and ``before`` (ISO 8601).
    All filters are optional and combinable.

    Args:
        params.status: Order status filter (any | pending | processing |
            on-hold | completed | cancelled | refunded | failed).
        params.customer_id: Restrict to orders placed by this customer ID.
        params.after: ISO 8601 datetime — orders created after this timestamp.
        params.before: ISO 8601 datetime — orders created before this timestamp.
        params.per_page: Page size (1–100, default 20).
        params.page: Page number (default 1).

    Returns:
        JSON/markdown with slim order list (id, status, total, currency,
        date_created, customer_id, line_items_count).
    """
    from skyyrose.integrations.wc_safe_client import WCSafeClient

    query: dict[str, Any] = {"per_page": params.per_page, "page": params.page}
    if params.status != "any":
        query["status"] = params.status
    if params.customer_id is not None:
        query["customer"] = params.customer_id
    if params.after is not None:
        query["after"] = params.after
    if params.before is not None:
        query["before"] = params.before

    try:
        async with WCSafeClient.from_env() as client:
            response = await client.get("orders", params=query)
    except Exception as exc:
        return _format_response(
            {"ok": False, "error": str(exc)},
            params.response_format,
            "wc_list_orders FAILED",
        )

    if response.status_code != 200:
        return _format_response(
            {
                "ok": False,
                "status_code": response.status_code,
                "error": _extract_error(response),
            },
            params.response_format,
            "wc_list_orders FAILED",
        )

    raw = response.json()
    slim = [
        {
            "id": o.get("id"),
            "status": o.get("status"),
            "total": o.get("total"),
            "currency": o.get("currency"),
            "date_created": o.get("date_created"),
            "customer_id": o.get("customer_id"),
            "line_items_count": len(o.get("line_items", [])),
        }
        for o in raw
    ]
    return _format_response(
        {
            "ok": True,
            "page": params.page,
            "per_page": params.per_page,
            "count": len(slim),
            "orders": slim,
        },
        params.response_format,
        "WC orders",
    )
