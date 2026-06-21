"""Resource tools: list_agents, health_check."""

import time

from utils.rate_limiting import get_rate_limit_stats
from utils.request_deduplication import get_deduplication_stats

from mcp_tools.api_client import _format_response, _make_api_request
from mcp_tools.security import secure_tool
from mcp_tools.server import API_BASE_URL, MCP_BACKEND, REQUEST_TIMEOUT, mcp
from mcp_tools.types import ResponseFormat


@mcp.tool(
    name="devskyy_list_agents",
    annotations={
        "title": "DevSkyy Agent Directory",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
        # Advanced Tool Use: Always loaded (core tool for discovery)
        "defer_loading": False,
    },
)
@secure_tool("list_agents")
async def list_agents(response_format: ResponseFormat = ResponseFormat.MARKDOWN) -> str:
    """List all DevSkyy AI agents with capabilities.

    Get a comprehensive directory of all available agents organized by category:
    - Infrastructure & System (Scanner, Fixer, Self-Healing, Security)
    - AI & Intelligence (NLP, Sentiment, Content Generation, Translation)
    - E-Commerce (Products, Pricing, Inventory, Orders)
    - Marketing (Brand, Social Media, Email, SMS, Campaigns)
    - Content (SEO, Copywriting, Image Generation, Video)
    - Integration (WordPress, Shopify, WooCommerce, Social Platforms)
    - Advanced (ML Models, Blockchain, Analytics, Reporting)
    - Frontend (UI Components, Theme Management, Analytics)

    Each agent listing includes:
    - Name and version
    - Primary capabilities
    - Status (active, maintenance, deprecated)
    - API endpoints

    Args:
        response_format: Output format (markdown or json)

    Returns:
        str: Complete agent directory of all available agents
    """
    # Canonical agents endpoint is GET /api/v1/agents (200, no auth). The old
    # "agents/list" path fell through to the JWT-gated /{agent_name} catch-all → 422.
    data = await _make_api_request("agents", method="GET")

    return _format_response(data, response_format, "DevSkyy Agent Directory")


@mcp.tool(
    name="devskyy_health_check",
    annotations={
        "title": "DevSkyy System Health Check",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,  # Internal diagnostic tool
        "defer_loading": False,  # Always available for monitoring
    },
)
@secure_tool("health_check")
async def health_check(response_format: ResponseFormat = ResponseFormat.MARKDOWN) -> str:
    """Comprehensive system health diagnostics and metrics.

    Monitors the DevSkyy MCP server health including:
    - API connectivity and response times
    - Rate limiting statistics (requests/second, utilization)
    - Request deduplication metrics (cache hits, pending requests)
    - Security subsystem status
    - Memory and performance indicators

    This tool is essential for:
    - Production monitoring and alerting
    - Debugging performance issues
    - Capacity planning
    - SLA compliance verification

    Args:
        response_format: Output format (markdown or json)

    Returns:
        str: Comprehensive health report with metrics and diagnostics

    Example:
        >>> health_check()
        # Returns detailed health metrics in markdown format
    """
    health_data = {}

    # API Connectivity Check
    try:
        start_time = time.time()
        api_response = await _make_api_request("health", method="GET")
        api_latency_ms = (time.time() - start_time) * 1000

        health_data["api_status"] = {
            "status": "healthy" if api_response.get("status") == "ok" else "degraded",
            "latency_ms": round(api_latency_ms, 2),
            "backend": api_response.get("backend", "unknown"),
        }
    except Exception as e:
        health_data["api_status"] = {
            "status": "unhealthy",
            "error": str(e),
        }

    # Rate Limiting Statistics
    try:
        rate_limit_stats = get_rate_limit_stats()
        health_data["rate_limiting"] = {
            "active_buckets": len(rate_limit_stats),
            "buckets": rate_limit_stats,
        }
    except Exception as e:
        health_data["rate_limiting"] = {
            "error": str(e),
        }

    # Request Deduplication Statistics
    try:
        dedup_stats = get_deduplication_stats()
        health_data["request_deduplication"] = dedup_stats
    except Exception as e:
        health_data["request_deduplication"] = {
            "error": str(e),
        }

    # Security Subsystems
    health_data["security"] = {
        "input_sanitization": "enabled",
        "path_traversal_protection": "enabled",
        "injection_protection": "enabled",
        "structured_logging": "enabled",
        "correlation_tracking": "enabled",
    }

    # MCP Server Info. Count tools dynamically from the registry so the value can never
    # drift out of sync with the actual @mcp.tool registrations (it repeatedly did).
    try:
        total_tools = len(mcp._tool_manager.list_tools())
    except Exception:  # registry shape changed — degrade gracefully rather than crash health
        total_tools = len(getattr(getattr(mcp, "_tool_manager", None), "_tools", {}) or {})
    health_data["mcp_server"] = {
        "backend": MCP_BACKEND,
        "api_base_url": API_BASE_URL,
        "request_timeout": REQUEST_TIMEOUT,
        "total_tools": total_tools,
    }

    # Overall Health Status
    api_healthy = health_data["api_status"]["status"] == "healthy"
    overall_status = "healthy" if api_healthy else "degraded"

    health_data["overall_status"] = overall_status
    health_data["timestamp"] = time.time()

    return _format_response(health_data, response_format, "DevSkyy System Health Check")


@mcp.tool(
    name="devskyy_fleet_health",
    annotations={
        "title": "DevSkyy Fleet Health",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,  # Internal diagnostic tool
        "defer_loading": False,  # Always available for monitoring
    },
)
@secure_tool("fleet_health")
async def fleet_health(window_seconds: int = 3600) -> str:
    """Per-agent LLM fleet health and alerts from in-process telemetry.

    Reads the token tracker (core.token_tracker) and reports, over the look-back window,
    fleet cost/requests plus any alerts: budget overrun, per-agent cost overrun, error
    rate, p95 latency, consecutive failures (retry-storm proxy), and stale/dead agents.

    Read-only and advisory — it never restarts an agent or mutates any state.

    Args:
        window_seconds: Look-back window for every check (default 3600 = 1 hour).

    Returns:
        str: Markdown fleet-health report.
    """
    from monitoring.fleet_observer import FleetObserver, format_health_report

    report = FleetObserver(window_seconds=window_seconds).evaluate()
    return format_health_report(report)


@mcp.tool(
    name="devskyy_fraud_assess",
    annotations={
        "title": "DevSkyy Fraud Risk Assessment",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,  # Pure local scoring — no external calls
        "defer_loading": False,
    },
)
@secure_tool("fraud_assess")
async def fraud_assess(order_json: str, history_json: str = "") -> str:
    """Score an order's fraud / chargeback risk from deterministic signals (advisory only).

    Reads industry-standard chargeback predictors — AVS/CVV mismatch, billing↔shipping
    country mismatch, order velocity, disposable email, new-customer high-value, recipient-
    name mismatch — and returns a 0-100 score, a risk level, and a recommended action
    ("approve" / "review" / "hold").

    This is READ-ONLY and ADVISORY. It never cancels, refunds, or writes to WooCommerce —
    a human (or a STOP-AND-SHOW gated action) acts on the recommendation.

    Args:
        order_json: A JSON object for the order (WooCommerce order shape: billing, shipping,
            total, customer_id, customer_ip_address, date_created, optional avs_result /
            cvv_result / meta_data).
        history_json: Optional JSON array of the customer's prior orders, used for velocity
            checks. Empty string disables velocity scoring.

    Returns:
        str: Markdown risk report followed by a compact JSON line for programmatic callers.
    """
    import json

    from services.risk.fraud import FraudScorer, format_assessment

    if len(order_json) > 1_000_000 or len(history_json) > 5_000_000:
        return "Payload too large — order_json must be <1MB and history_json <5MB."

    try:
        order = json.loads(order_json) if order_json else {}
    except (json.JSONDecodeError, TypeError):
        return "Could not parse order_json — expected a JSON object."

    history = None
    if history_json:
        try:
            parsed = json.loads(history_json)
            history = parsed if isinstance(parsed, list) else None
        except (json.JSONDecodeError, TypeError):
            history = None

    assessment = FraudScorer().assess(order if isinstance(order, dict) else {}, history=history)
    return f"{format_assessment(assessment)}\n\n```json\n{json.dumps(assessment.as_dict())}\n```"


@mcp.tool(
    name="devskyy_retention_assess",
    annotations={
        "title": "DevSkyy Retention / Lifecycle Assessment",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,  # Pure local scoring — no external calls
        "defer_loading": False,
    },
)
@secure_tool("retention_assess")
async def retention_assess(customer_json: str, as_of: str = "") -> str:
    """Score a customer's RFM, lifecycle stage, and churn risk (advisory only).

    Computes Recency / Frequency / Monetary from the customer's order history, assigns a
    lifecycle stage (NEW / ACTIVE / LOYAL / AT_RISK / DORMANT / CHURNED), a 0-100 churn-risk
    score, a recommended next action, and a SUGGESTED Klaviyo segment to enroll into.

    This is READ-ONLY and ADVISORY. It NEVER calls the Klaviyo API or enrolls anyone — a
    human (or a STOP-AND-SHOW gated action) performs the actual send.

    Args:
        customer_json: A JSON object for the customer. Either ``{"orders": [{"date_created",
            "total"}, ...]}`` or precomputed ``{"last_order_date", "order_count",
            "total_spent"}``. May include ``id``.
        as_of: Optional ISO-8601 timestamp to score against (default: now). Pass it for
            reproducible scoring.

    Returns:
        str: Markdown lifecycle report followed by a compact JSON line.
    """
    import json
    from datetime import datetime

    from services.lifecycle.retention import RetentionScorer, format_assessment

    if len(customer_json) > 5_000_000:
        return "Payload too large — customer_json must be <5MB."

    try:
        customer = json.loads(customer_json) if customer_json else {}
    except (json.JSONDecodeError, TypeError):
        return "Could not parse customer_json — expected a JSON object."

    when = None
    if as_of:
        try:
            when = datetime.fromisoformat(as_of.strip().replace("Z", "+00:00"))
        except ValueError:
            when = None

    assessment = RetentionScorer().assess(
        customer if isinstance(customer, dict) else {}, as_of=when
    )
    return f"{format_assessment(assessment)}\n\n```json\n{json.dumps(assessment.as_dict())}\n```"


@mcp.tool(
    name="devskyy_demand_forecast",
    annotations={
        "title": "DevSkyy Demand / Sellout Forecast",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,  # Pure local scoring — no external calls
        "defer_loading": False,
    },
)
@secure_tool("demand_forecast")
async def demand_forecast(product_json: str, horizon_days: int = 30) -> str:
    """Forecast a product's demand velocity, trend, and sellout risk (advisory only).

    Computes units/day over a trailing window, the trend vs the prior window
    (ACCELERATING / STEADY / DECLINING), days-to-sellout against inventory, and a reorder
    recommendation. The key signal for SkyyRose's pre-order / limited-run drops: will this
    sell out before production lead time?

    READ-ONLY and ADVISORY — it never changes inventory or places a reorder.

    Args:
        product_json: A JSON object: ``{"sku", "sales": [{"date", "units"}, ...],
            "inventory" (or "stock_quantity"), "is_preorder"}``.
        horizon_days: Projection horizon for the unit forecast (default 30).

    Returns:
        str: Markdown forecast followed by a compact JSON line.
    """
    import json

    from services.forecasting.demand import DemandForecaster, format_forecast

    if len(product_json) > 5_000_000:
        return "Payload too large — product_json must be <5MB."

    try:
        product = json.loads(product_json) if product_json else {}
    except (json.JSONDecodeError, TypeError):
        return "Could not parse product_json — expected a JSON object."

    forecast = DemandForecaster().forecast(product if isinstance(product, dict) else {})
    payload = forecast.as_dict()
    payload["forecast_units_horizon"] = forecast.forecast_units(horizon_days)
    return f"{format_forecast(forecast)}\n\n```json\n{json.dumps(payload)}\n```"


@mcp.tool(
    name="devskyy_recommend",
    annotations={
        "title": "DevSkyy Per-User Recommendations",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,  # Pure local scoring — no external calls
        "defer_loading": False,
    },
)
@secure_tool("recommend")
async def recommend(user_json: str, catalog_json: str, top_n: int = 10) -> str:
    """Rank the catalog for one user (content-based + co-purchase, advisory only).

    Personalizes ordering by the user's purchase profile (collection affinity, shared tags,
    price tier) and optional co-purchase data, falling back to global popularity for
    cold-start users. READ-ONLY — it suggests an order, it changes nothing.

    Args:
        user_json: A JSON object: ``{"id", "purchased": [item_id | {"id"/"sku", ...}, ...]}``.
        catalog_json: A JSON array of product dicts: ``{"id"/"sku", "collection", "price",
            "tags", "popularity"}``. May include a top-level ``co_purchase`` map if wrapped as
            ``{"catalog": [...], "co_purchase": {...}}``.
        top_n: Number of recommendations to return (default 10).

    Returns:
        str: Markdown recommendation table followed by a compact JSON line.
    """
    import json

    from services.personalization.recommender import Recommender, format_recommendations

    if len(user_json) > 1_000_000 or len(catalog_json) > 10_000_000:
        return "Payload too large — user_json <1MB, catalog_json <10MB."

    try:
        user = json.loads(user_json) if user_json else {}
        parsed = json.loads(catalog_json) if catalog_json else []
    except (json.JSONDecodeError, TypeError):
        return "Could not parse user_json/catalog_json."

    co_purchase = None
    if isinstance(parsed, dict):
        catalog = parsed.get("catalog", [])
        cp = parsed.get("co_purchase")
        co_purchase = cp if isinstance(cp, dict) else None
    else:
        catalog = parsed

    rs = Recommender(top_n=max(1, top_n)).recommend(
        user if isinstance(user, dict) else {},
        catalog if isinstance(catalog, list) else [],
        co_purchase=co_purchase,
    )
    return f"{format_recommendations(rs)}\n\n```json\n{json.dumps(rs.as_dict())}\n```"
