"""
Prometheus Metrics for DevSkyy MCP Server

Provides comprehensive monitoring and observability for all MCP servers,
tools, and system health metrics.

Metrics Categories:
1. Request Metrics - Tool calls, latency, throughput
2. Error Metrics - Failures by type, tool, and cause
3. System Metrics - Memory, CPU, connections
4. Business Metrics - Agent utilization, cost tracking
5. Security Metrics - Auth failures, rate limit hits

Usage:
    from monitoring.prometheus_metrics import (
        mcp_tool_calls,
        mcp_request_duration,
        record_tool_call,
        record_error
    )

    # Record tool call
    with record_tool_call("devskyy_generate_3d"):
        result = await generate_3d(...)

    # Record error
    record_error("tool_execution", "devskyy_generate_3d", "timeout")

Version: 1.0.0
"""

import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Optional

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Info,
    Summary,
    generate_latest,
)

# ============================================================================
# REQUEST METRICS
# ============================================================================

# Tool call counter by tool name and status
mcp_tool_calls = Counter(
    "mcp_tool_calls_total",
    "Total number of MCP tool calls",
    ["tool_name", "status"],  # status: success, error, timeout
)

# Request duration histogram with reasonable buckets for MCP tools
mcp_request_duration = Histogram(
    "mcp_request_duration_seconds",
    "MCP tool request duration in seconds",
    ["tool_name"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0),
)

# Request size tracking
mcp_request_size_bytes = Summary(
    "mcp_request_size_bytes",
    "MCP request payload size in bytes",
    ["tool_name"],
)

mcp_response_size_bytes = Summary(
    "mcp_response_size_bytes",
    "MCP response payload size in bytes",
    ["tool_name"],
)

# ============================================================================
# ERROR METRICS
# ============================================================================

# Error counter by type, tool, and reason
mcp_errors_total = Counter(
    "mcp_errors_total",
    "Total number of MCP errors",
    ["error_type", "tool_name", "reason"],  # error_type: tool_error, api_error, validation_error
)

# Rate limit hits
mcp_rate_limit_hits = Counter(
    "mcp_rate_limit_hits_total",
    "Number of rate limit hits",
    ["tool_name", "limit_type"],  # limit_type: per_second, per_minute, per_hour
)

# Timeout counter
mcp_timeouts_total = Counter(
    "mcp_timeouts_total",
    "Number of request timeouts",
    ["tool_name"],
)

# ============================================================================
# SYSTEM METRICS
# ============================================================================

# Active connections
mcp_active_connections = Gauge(
    "mcp_active_connections",
    "Number of active MCP connections",
)

# Tool execution queue depth
mcp_queue_depth = Gauge(
    "mcp_queue_depth",
    "Number of pending tool executions",
    ["tool_name"],
)

# System info (labels only, no value)
mcp_server_info = Info(
    "mcp_server",
    "MCP Server information",
)

# Server uptime
mcp_server_uptime_seconds = Gauge(
    "mcp_server_uptime_seconds",
    "MCP Server uptime in seconds",
)

# Tool availability (1 = available, 0 = unavailable)
mcp_tool_availability = Gauge(
    "mcp_tool_availability",
    "Tool availability status (1=available, 0=unavailable)",
    ["tool_name"],
)

# ============================================================================
# BUSINESS METRICS
# ============================================================================

# Agent usage by category
mcp_agent_usage = Counter(
    "mcp_agent_usage_total",
    "Agent usage by category",
    ["agent_name", "category"],
)

# LLM token usage (approximate cost tracking)
mcp_llm_tokens = Counter(
    "mcp_llm_tokens_total",
    "LLM token usage",
    ["provider", "model", "type"],  # type: input, output
)

# 3D generation requests (high-cost operation)
mcp_3d_generations = Counter(
    "mcp_3d_generations_total",
    "Number of 3D model generations",
    ["status"],  # status: success, failed, pending
)

# ============================================================================
# SECURITY METRICS
# ============================================================================

# Authentication failures
mcp_auth_failures = Counter(
    "mcp_auth_failures_total",
    "Authentication failures",
    ["reason"],  # reason: invalid_token, expired_token, missing_token
)

# Input validation failures
mcp_validation_failures = Counter(
    "mcp_validation_failures_total",
    "Input validation failures",
    ["tool_name", "validation_type"],  # validation_type: sanitization, schema, business_rule
)

# Security events
mcp_security_events = Counter(
    "mcp_security_events_total",
    "Security-related events",
    ["event_type"],  # event_type: path_traversal, injection_attempt, suspicious_input
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


@contextmanager
def record_tool_call(tool_name: str, track_size: bool = False):
    """
    Context manager to automatically record tool call metrics.

    Args:
        tool_name: Name of the MCP tool being called
        track_size: Whether to track request/response sizes

    Usage:
        with record_tool_call("devskyy_generate_3d"):
            result = await generate_3d(...)
    """
    start_time = time.time()
    status = "success"

    try:
        yield
    except TimeoutError:
        status = "timeout"
        mcp_timeouts_total.labels(tool_name=tool_name).inc()
        raise
    except Exception:
        status = "error"
        raise
    finally:
        duration = time.time() - start_time
        mcp_request_duration.labels(tool_name=tool_name).observe(duration)
        mcp_tool_calls.labels(tool_name=tool_name, status=status).inc()


def record_error(
    error_type: str,
    tool_name: str,
    reason: str,
    correlation_id: Optional[str] = None,
):
    """
    Record an error with detailed context.

    Args:
        error_type: Category of error (tool_error, api_error, validation_error)
        tool_name: Name of the tool that encountered the error
        reason: Specific reason for the error
        correlation_id: Optional correlation ID for tracing
    """
    mcp_errors_total.labels(
        error_type=error_type,
        tool_name=tool_name,
        reason=reason,
    ).inc()


def record_rate_limit_hit(tool_name: str, limit_type: str = "per_second"):
    """
    Record a rate limit hit.

    Args:
        tool_name: Name of the tool that hit rate limit
        limit_type: Type of rate limit (per_second, per_minute, per_hour)
    """
    mcp_rate_limit_hits.labels(tool_name=tool_name, limit_type=limit_type).inc()


def record_llm_tokens(
    provider: str,
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
):
    """
    Record LLM token usage for cost tracking.

    Args:
        provider: LLM provider (anthropic, openai, gemini, etc.)
        model: Model name (claude-3-7-sonnet, gpt-4, etc.)
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
    """
    if input_tokens > 0:
        mcp_llm_tokens.labels(
            provider=provider,
            model=model,
            type="input"
        ).inc(input_tokens)

    if output_tokens > 0:
        mcp_llm_tokens.labels(
            provider=provider,
            model=model,
            type="output"
        ).inc(output_tokens)


def record_3d_generation(status: str = "success"):
    """
    Record a 3D generation attempt.

    Args:
        status: Generation status (success, failed, pending)
    """
    mcp_3d_generations.labels(status=status).inc()


def record_security_event(event_type: str):
    """
    Record a security-related event.

    Args:
        event_type: Type of security event (path_traversal, injection_attempt, etc.)
    """
    mcp_security_events.labels(event_type=event_type).inc()


def record_validation_failure(tool_name: str, validation_type: str):
    """
    Record an input validation failure.

    Args:
        tool_name: Name of the tool with validation failure
        validation_type: Type of validation that failed
    """
    mcp_validation_failures.labels(
        tool_name=tool_name,
        validation_type=validation_type,
    ).inc()


def set_tool_availability(tool_name: str, available: bool):
    """
    Update tool availability status.

    Args:
        tool_name: Name of the tool
        available: Whether the tool is currently available
    """
    mcp_tool_availability.labels(tool_name=tool_name).set(1 if available else 0)


def update_queue_depth(tool_name: str, depth: int):
    """
    Update tool execution queue depth.

    Args:
        tool_name: Name of the tool
        depth: Current queue depth
    """
    mcp_queue_depth.labels(tool_name=tool_name).set(depth)


def set_server_info(version: str, backend: str, python_version: str):
    """
    Set static server information.

    Args:
        version: Server version
        backend: Backend type (fastmcp, mcp)
        python_version: Python version string
    """
    mcp_server_info.info({
        "version": version,
        "backend": backend,
        "python_version": python_version,
    })


def update_server_uptime(uptime_seconds: float):
    """
    Update server uptime metric.

    Args:
        uptime_seconds: Server uptime in seconds
    """
    mcp_server_uptime_seconds.set(uptime_seconds)


def get_metrics_text() -> bytes:
    """
    Get current metrics in Prometheus text format.

    Returns:
        bytes: Metrics in Prometheus exposition format
    """
    return generate_latest()


# ============================================================================
# DECORATOR FOR AUTOMATIC METRICS
# ============================================================================


def monitored_tool(func: Callable) -> Callable:
    """
    Decorator to automatically add monitoring to MCP tool functions.

    Usage:
        @mcp.tool()
        @monitored_tool
        async def my_tool(...):
            ...
    """
    tool_name = func.__name__

    @wraps(func)
    async def wrapper(*args, **kwargs):
        with record_tool_call(tool_name):
            return await func(*args, **kwargs)

    return wrapper


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_metrics():
    """
    Initialize metrics with default values and server info.
    Should be called on server startup.
    """
    import sys

    # Set server info
    set_server_info(
        version="2.0.0",
        backend="fastmcp",
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    )

    # Initialize tool availability (all tools start as available)
    tools = [
        "devskyy_scan_code",
        "devskyy_fix_code",
        "devskyy_generate_wordpress_theme",
        "devskyy_ml_prediction",
        "devskyy_manage_products",
        "devskyy_dynamic_pricing",
        "devskyy_generate_3d_from_description",
        "devskyy_generate_3d_from_image",
        "devskyy_marketing_campaign",
        "devskyy_multi_agent_workflow",
        "devskyy_system_monitoring",
        "devskyy_list_agents",
        "devskyy_health_check",
    ]

    for tool in tools:
        set_tool_availability(tool, True)

    # Initialize active connections
    mcp_active_connections.set(0)


# Initialize on module import
initialize_metrics()
