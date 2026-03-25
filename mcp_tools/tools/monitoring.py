"""System monitoring tool."""

from pydantic import Field

from mcp_tools.api_client import _format_response, _make_api_request
from mcp_tools.security import secure_tool
from mcp_tools.server import mcp
from mcp_tools.types import BaseAgentInput


class MonitoringInput(BaseAgentInput):
    """Input for system monitoring."""

    metrics: list[str] | None = Field(
        default=["health", "performance", "errors"],
        description="Metrics to retrieve: health, performance, errors, ml_accuracy, api_latency",
        max_length=20,
    )
    time_range: str | None = Field(
        default="1h",
        description="Time range for metrics (e.g., '1h', '24h', '7d')",
        max_length=10,
    )


@mcp.tool(
    name="devskyy_system_monitoring",
    annotations={
        "title": "DevSkyy System Monitoring",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
        # Advanced Tool Use: Always loaded (core health monitoring)
        "defer_loading": False,
    },
)
@secure_tool("system_monitoring")
async def system_monitoring(params: MonitoringInput) -> str:
    """Monitor DevSkyy platform health and performance metrics.

    Real-time monitoring across all system components:

    **Health Metrics:**
    - System uptime and availability
    - Agent status (active, idle, error)
    - Database connection pool
    - Cache hit rates
    - Queue depths

    **Performance Metrics:**
    - API latency (p50, p95, p99)
    - Request throughput
    - Error rates
    - CPU and memory usage
    - Network I/O

    **ML Metrics:**
    - Model accuracy scores
    - Prediction latency
    - Training status
    - Data drift detection

    **Business Metrics:**
    - Products created/updated
    - Campaigns sent
    - Orders processed
    - Revenue tracked

    Supports time ranges from 1 hour to 30 days.

    Args:
        params (MonitoringInput): Monitoring configuration containing:
            - metrics: List of metric categories to retrieve
            - time_range: Time window (1h, 24h, 7d, 30d)
            - response_format: Output format (markdown/json)

    Returns:
        str: Comprehensive system metrics and health status

    Example:
        >>> system_monitoring({
        ...     "metrics": ["health", "performance", "ml_accuracy"],
        ...     "time_range": "24h"
        ... })
    """
    data = await _make_api_request(
        "monitoring/metrics",
        method="GET",
        params={
            "metrics": (",".join(params.metrics) if params.metrics else "health,performance"),
            "time_range": params.time_range,
        },
    )

    return _format_response(data, params.response_format, "System Monitoring")
