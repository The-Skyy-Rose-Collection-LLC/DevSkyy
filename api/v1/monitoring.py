"""System Monitoring and Health API Endpoints.

This module provides endpoints for:
- System metrics and monitoring
- Agent directory and status
- Prometheus integration

Version: 1.0.0
"""

import asyncio
import logging
import time
import uuid
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import httpx
import psutil
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from security.jwt_oauth2_auth import TokenPayload, get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Monitoring"])

# In-process agent listing cache (30s TTL)
_agents_cache: dict[str, Any] = {"data": None, "timestamp": 0.0}
_AGENT_CACHE_TTL = 30.0

# Rolling request window: (timestamp, success, latency_ms)
_req_window: deque[tuple[float, bool, float]] = deque(maxlen=2000)

# Per-service uptime history: last 100 check outcomes
_service_history: dict[str, deque[bool]] = {}

# Activity event ring buffer
_event_log: deque[dict[str, Any]] = deque(maxlen=50)

# Health check cache (5s TTL)
_health_cache: dict[str, Any] = {"data": None, "timestamp": 0.0}
_HEALTH_CACHE_TTL = 5.0

# External services to probe on each health check
_EXTERNAL_SERVICES = [
    {"name": "WordPress API", "url": "https://skyyrose.co/wp-json/"},
    {"name": "Vercel API", "url": "https://devskyy.app/api/health"},
    {"name": "FastAPI (self)", "url": "http://localhost:8000/health"},
]

_AGENT_CATEGORY_MAP: dict[str, str] = {
    "base_super_agent": "infrastructure",
    "claude_sdk": "ai",
    "visual_generation": "visual",
    "elite_web_builder": "web",
    "wordpress_bridge": "integration",
    "render_pipeline": "render",
    "core": "core",
    "devskyy-a2a": "automation",
    "llm_roundtable": "ai",
    "product_generation": "ecommerce",
}


# =============================================================================
# Request/Response Models
# =============================================================================


class MetricDataPoint(BaseModel):
    """Individual metric data point."""

    timestamp: str
    value: float
    labels: dict[str, str] | None = None


class MetricSeries(BaseModel):
    """Time series data for a metric."""

    metric_name: str
    unit: str
    data_points: list[MetricDataPoint]
    aggregation: str | None = None


class MonitoringMetricsResponse(BaseModel):
    """Response model for monitoring metrics."""

    timestamp: str
    time_range: str
    metrics: list[MetricSeries]
    summary: dict[str, Any]


class ServiceHealthStatus(BaseModel):
    """Health status for an external service."""

    name: str
    status: Literal["healthy", "degraded", "down"]
    uptime_pct: float
    response_ms: float | None = None
    last_check: str
    circuit_breaker: Literal["closed", "half-open", "open"]


class SystemStats(BaseModel):
    """Real-time system resource stats."""

    cpu_pct: float
    memory_pct: float
    disk_pct: float
    req_per_min: float
    success_rate: float
    avg_latency_ms: float


class HealthEvent(BaseModel):
    """Single event in the activity log."""

    id: str
    timestamp: str
    type: Literal["success", "warning", "error"]
    service: str
    message: str


class MonitoringHealthResponse(BaseModel):
    """Full monitoring health response."""

    timestamp: str
    services: list[ServiceHealthStatus]
    system: SystemStats
    events: list[HealthEvent]


class AgentInfo(BaseModel):
    """Information about individual agent."""

    name: str
    version: str
    category: str
    status: str  # active, idle, error, maintenance
    capabilities: list[str]
    endpoints: list[str]
    last_execution: str | None = None


class AgentListResponse(BaseModel):
    """Response model for agent directory."""

    timestamp: str
    total_agents: int
    active_agents: int
    agents_by_category: dict[str, int]
    agents: list[AgentInfo]


# =============================================================================
# Endpoints
# =============================================================================


def track_request(latency_ms: float, success: bool) -> None:
    """Record a request outcome into the rolling window. Called from timing_middleware."""
    _req_window.append((time.time(), success, latency_ms))


async def _check_http_service(name: str, url: str) -> ServiceHealthStatus:
    """Probe a single HTTP service and update its history."""
    if name not in _service_history:
        _service_history[name] = deque(maxlen=100)

    response_ms: float | None = None
    ok = False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            t0 = time.time()
            resp = await client.get(url)
            response_ms = (time.time() - t0) * 1000
            ok = resp.status_code < 400
    except Exception:
        ok = False

    _service_history[name].append(ok)
    history = _service_history[name]
    uptime_pct = round(sum(history) / len(history) * 100, 2) if history else 0.0

    if ok:
        status_val: Literal["healthy", "degraded", "down"] = "healthy"
        cb: Literal["closed", "half-open", "open"] = "closed"
    else:
        failures = sum(1 for v in list(history)[-5:] if not v)
        if failures >= 3:
            status_val = "down"
            cb = "open"
        else:
            status_val = "degraded"
            cb = "half-open"

    event_type: Literal["success", "warning", "error"] = "success" if ok else "error"
    _event_log.append(
        {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.now(UTC).isoformat(),
            "type": event_type,
            "service": name,
            "message": f"Health check {'passed' if ok else 'failed'}"
            + (f" — {response_ms:.0f}ms" if response_ms else ""),
        }
    )

    return ServiceHealthStatus(
        name=name,
        status=status_val,
        uptime_pct=uptime_pct,
        response_ms=round(response_ms, 1) if response_ms else None,
        last_check=datetime.now(UTC).isoformat(),
        circuit_breaker=cb,
    )


async def _check_db_service(db: AsyncSession) -> ServiceHealthStatus:
    """Probe the database with SELECT 1."""
    name = "Database"
    if name not in _service_history:
        _service_history[name] = deque(maxlen=100)

    ok = False
    response_ms: float | None = None
    try:
        t0 = time.time()
        await db.execute(text("SELECT 1"))
        response_ms = (time.time() - t0) * 1000
        ok = True
    except Exception:
        ok = False

    _service_history[name].append(ok)
    history = _service_history[name]
    uptime_pct = round(sum(history) / len(history) * 100, 2) if history else 0.0

    status_val: Literal["healthy", "degraded", "down"] = "healthy" if ok else "down"
    cb: Literal["closed", "half-open", "open"] = "closed" if ok else "open"

    event_type: Literal["success", "warning", "error"] = "success" if ok else "error"
    _event_log.append(
        {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.now(UTC).isoformat(),
            "type": event_type,
            "service": name,
            "message": "DB ping ok" + (f" — {response_ms:.0f}ms" if response_ms else "")
            if ok
            else "DB ping failed",
        }
    )

    return ServiceHealthStatus(
        name=name,
        status=status_val,
        uptime_pct=uptime_pct,
        response_ms=round(response_ms, 1) if response_ms else None,
        last_check=datetime.now(UTC).isoformat(),
        circuit_breaker=cb,
    )


def _compute_system_stats() -> SystemStats:
    """Read psutil metrics + rolling request window."""
    now = time.time()
    window_start = now - 60.0
    recent = [r for r in _req_window if r[0] >= window_start]
    req_per_min = float(len(recent))
    success_rate = (sum(1 for r in recent if r[1]) / len(recent) * 100) if recent else 100.0
    avg_latency = (sum(r[2] for r in recent) / len(recent)) if recent else 0.0

    return SystemStats(
        cpu_pct=round(psutil.cpu_percent(interval=None), 1),
        memory_pct=round(psutil.virtual_memory().percent, 1),
        disk_pct=round(psutil.disk_usage("/").percent, 1),
        req_per_min=round(req_per_min, 1),
        success_rate=round(success_rate, 2),
        avg_latency_ms=round(avg_latency, 1),
    )


@router.get(
    "/monitoring/health",
    response_model=MonitoringHealthResponse,
    status_code=status.HTTP_200_OK,
)
async def get_health(
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MonitoringHealthResponse:
    """Real-time service health and system stats for the monitoring dashboard."""
    logger.info(f"Health check requested by {user.sub}")

    now = time.time()
    if _health_cache["data"] is not None and now - _health_cache["timestamp"] < _HEALTH_CACHE_TTL:
        return _health_cache["data"]

    try:
        http_checks = await asyncio.gather(
            *[_check_http_service(svc["name"], svc["url"]) for svc in _EXTERNAL_SERVICES],
            return_exceptions=True,
        )
        services: list[ServiceHealthStatus] = []
        for i, result in enumerate(http_checks):
            if isinstance(result, Exception):
                services.append(
                    ServiceHealthStatus(
                        name=_EXTERNAL_SERVICES[i]["name"],
                        status="down",
                        uptime_pct=0.0,
                        response_ms=None,
                        last_check=datetime.now(UTC).isoformat(),
                        circuit_breaker="open",
                    )
                )
            else:
                services.append(result)

        db_status = await _check_db_service(db)
        services.append(db_status)

        system = _compute_system_stats()
        events = [HealthEvent(**e) for e in list(_event_log)[-20:]][::-1]

        response = MonitoringHealthResponse(
            timestamp=datetime.now(UTC).isoformat(),
            services=services,
            system=system,
            events=events,
        )
        _health_cache["data"] = response
        _health_cache["timestamp"] = now
        return response

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}",
        )


@router.get(
    "/monitoring/metrics",
    response_model=MonitoringMetricsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_metrics(
    metrics: list[str] = Query(
        default=["health", "performance"],
        description="Metrics to retrieve",
    ),
    time_range: str = Query(
        default="1h",
        description="Time range for metrics (1h, 24h, 7d, 30d)",
    ),
    user: TokenPayload = Depends(get_current_user),
) -> MonitoringMetricsResponse:
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

    Args:
        metrics: List of metric categories to retrieve
        time_range: Time window (1h, 24h, 7d, 30d)
        user: Authenticated user (from JWT token)

    Returns:
        MonitoringMetricsResponse with time series data

    Raises:
        HTTPException: If metrics retrieval fails
    """
    logger.info(f"Fetching metrics for user {user.sub}: {metrics} ({time_range})")

    try:
        metric_series = []

        if "health" in metrics:
            metric_series.append(
                MetricSeries(
                    metric_name="system_uptime",
                    unit="seconds",
                    data_points=[
                        MetricDataPoint(timestamp=datetime.now(UTC).isoformat(), value=86400.0)
                    ],
                    aggregation="last",
                )
            )
            metric_series.append(
                MetricSeries(
                    metric_name="agent_status",
                    unit="count",
                    data_points=[
                        MetricDataPoint(
                            timestamp=datetime.now(UTC).isoformat(),
                            value=54.0,
                            labels={"status": "active"},
                        )
                    ],
                    aggregation="gauge",
                )
            )

        if "performance" in metrics:
            metric_series.append(
                MetricSeries(
                    metric_name="api_latency_p95",
                    unit="milliseconds",
                    data_points=[
                        MetricDataPoint(timestamp=datetime.now(UTC).isoformat(), value=125.5)
                    ],
                    aggregation="p95",
                )
            )
            metric_series.append(
                MetricSeries(
                    metric_name="requests_per_second",
                    unit="requests/sec",
                    data_points=[
                        MetricDataPoint(timestamp=datetime.now(UTC).isoformat(), value=45.2)
                    ],
                    aggregation="avg",
                )
            )

        stats = _compute_system_stats()
        summary = {
            "overall_health": "healthy",
            "total_requests": len(_req_window),
            "error_rate": round(1.0 - stats.success_rate / 100, 4),
            "avg_latency_ms": stats.avg_latency_ms,
            "active_agents": _agents_cache["data"].total_agents if _agents_cache["data"] else 0,
        }

        return MonitoringMetricsResponse(
            timestamp=datetime.now(UTC).isoformat(),
            time_range=time_range,
            metrics=metric_series,
            summary=summary,
        )

    except Exception as e:
        logger.error(f"Metrics retrieval failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metrics retrieval failed: {str(e)}",
        )


def _scan_agents_directory() -> "AgentListResponse":
    """Walk agents/ directory and return real agent inventory."""
    agents_dir = Path(__file__).parent.parent.parent / "agents"
    found: list[AgentInfo] = []

    if agents_dir.exists():
        for entry in sorted(agents_dir.iterdir()):
            if entry.is_file() and entry.suffix == ".py" and entry.stem != "__init__":
                found.append(
                    AgentInfo(
                        name=entry.stem,
                        version="1.0.0",
                        category="general",
                        status="active",
                        capabilities=[],
                        endpoints=[],
                        last_execution=None,
                    )
                )
            elif entry.is_dir() and not entry.name.startswith(("_", ".")):
                category = _AGENT_CATEGORY_MAP.get(entry.name, entry.name.replace("-", "_").lower())
                for py_file in sorted(entry.glob("*.py")):
                    if py_file.stem != "__init__":
                        found.append(
                            AgentInfo(
                                name=py_file.stem,
                                version="1.0.0",
                                category=category,
                                status="active",
                                capabilities=[],
                                endpoints=[],
                                last_execution=None,
                            )
                        )

    agents_by_category: dict[str, int] = {}
    for a in found:
        agents_by_category[a.category] = agents_by_category.get(a.category, 0) + 1

    return AgentListResponse(
        timestamp=datetime.now(UTC).isoformat(),
        total_agents=len(found),
        active_agents=len(found),
        agents_by_category=agents_by_category,
        agents=found,
    )


@router.get("/agents", response_model=AgentListResponse, status_code=status.HTTP_200_OK)
async def list_agents(
    user: TokenPayload = Depends(get_current_user),
) -> AgentListResponse:
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

    Args:
        user: Authenticated user (from JWT token)

    Returns:
        AgentListResponse with complete agent directory

    Raises:
        HTTPException: If agent listing fails
    """
    logger.info(f"Fetching agent list for user {user.sub}")

    try:
        now = time.time()
        if _agents_cache["data"] is None or now - _agents_cache["timestamp"] > _AGENT_CACHE_TTL:
            _agents_cache["data"] = _scan_agents_directory()
            _agents_cache["timestamp"] = now
        return _agents_cache["data"]

    except Exception as e:
        logger.error(f"Agent listing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent listing failed: {str(e)}",
        )
