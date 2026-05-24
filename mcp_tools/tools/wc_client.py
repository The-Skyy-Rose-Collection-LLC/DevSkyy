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
