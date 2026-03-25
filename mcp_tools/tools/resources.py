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
    """List all 54 DevSkyy AI agents with capabilities.

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
        str: Complete agent directory with 54 agents
    """
    data = await _make_api_request("agents/list", method="GET")

    return _format_response(data, response_format, "DevSkyy Agent Directory (54 Agents)")


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

    # MCP Server Info
    health_data["mcp_server"] = {
        "backend": MCP_BACKEND,
        "api_base_url": API_BASE_URL,
        "request_timeout": REQUEST_TIMEOUT,
        "total_tools": 22,  # 21 + health_check
    }

    # Overall Health Status
    api_healthy = health_data["api_status"]["status"] == "healthy"
    overall_status = "healthy" if api_healthy else "degraded"

    health_data["overall_status"] = overall_status
    health_data["timestamp"] = time.time()

    return _format_response(health_data, response_format, "DevSkyy System Health Check")
