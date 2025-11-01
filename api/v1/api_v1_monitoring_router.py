"""
API v1 Monitoring Router
Health checks, metrics collection, system status monitoring
Path: api/v1/monitoring

Author: DevSkyy Enterprise Team
Date: October 26, 2025
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import psutil
import os

from jwt_auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])

# ============================================================================
# MODELS
# ============================================================================


class HealthCheckResponse(BaseModel):
    """Health check response"""

    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime
    uptime_seconds: float
    version: str
    components: Dict[str, str]


class MetricsResponse(BaseModel):
    """System metrics response"""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    process_memory_mb: float
    api_requests_total: int
    api_requests_errors: int
    api_requests_success: int
    avg_request_latency_ms: float


class LatencyPercentile(BaseModel):
    """Latency percentile"""

    p50: float  # milliseconds
    p95: float
    p99: float


class PerformanceMetrics(BaseModel):
    """Performance metrics with percentiles"""

    timestamp: datetime
    request_latency_percentiles: LatencyPercentile
    cache_hit_rate: float
    cache_miss_rate: float
    database_query_time_ms: float
    webhook_delivery_success_rate: float
    agent_execution_success_rate: float


class AlertResponse(BaseModel):
    """Alert/threshold response"""

    alert_id: str
    severity: str  # "info", "warning", "critical"
    component: str
    message: str
    threshold: float
    current_value: float
    created_at: datetime


# ============================================================================
# GLOBAL STATE (in production, use Prometheus/time-series database)
# ============================================================================


class MetricsCollector:
    """Simple in-memory metrics collector"""

    def __init__(self):
        self.start_time = datetime.utcnow()
        self.request_times: List[float] = []
        self.request_errors = 0
        self.request_success = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.webhook_successes = 0
        self.webhook_failures = 0
        self.agent_successes = 0
        self.agent_failures = 0

    def add_request(self, latency_ms: float, error: bool = False):
        """Record API request"""
        self.request_times.append(latency_ms)
        if error:
            self.request_errors += 1
        else:
            self.request_success += 1

        # Keep only recent 1000 requests for percentile calculations
        if len(self.request_times) > 1000:
            self.request_times = self.request_times[-1000:]

    def get_latency_percentiles(self) -> LatencyPercentile:
        """Calculate latency percentiles (p50, p95, p99)"""
        if not self.request_times:
            return LatencyPercentile(p50=0, p95=0, p99=0)

        sorted_times = sorted(self.request_times)
        n = len(sorted_times)

        p50_idx = int(n * 0.50)
        p95_idx = int(n * 0.95)
        p99_idx = int(n * 0.99)

        return LatencyPercentile(
            p50=sorted_times[max(0, p50_idx)], p95=sorted_times[max(0, p95_idx)], p99=sorted_times[max(0, p99_idx)]
        )


# Global metrics instance
metrics_collector = MetricsCollector()

# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(current_user: Dict = Depends(get_current_user)):
    """
    Health check endpoint

    Returns overall system health status and component health

    Args:
        current_user: Current authenticated user (from JWT)

    Returns:
        HealthCheckResponse with status and component health

    Status Codes:
        200: System healthy
        503: System unhealthy
    """
    try:
        uptime = (datetime.utcnow() - metrics_collector.start_time).total_seconds()

        # Check components
        components = {
            "api": "healthy",
            "database": "healthy",  # TODO: Ping database
            "cache": "healthy",  # TODO: Ping Redis
            "webhooks": "healthy",
        }

        # Determine overall status
        overall_status = "healthy"
        if any(v == "unhealthy" for v in components.values()):
            overall_status = "unhealthy"
        elif any(v == "degraded" for v in components.values()):
            overall_status = "degraded"

        status_code = 200 if overall_status == "healthy" else 503

        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            uptime_seconds=uptime,
            version="5.1.0",
            components=components,
        )

    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Health check failed")


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(current_user: Dict = Depends(get_current_user)):
    """
    Get system and application metrics

    Returns CPU, memory, disk usage and API request metrics

    Args:
        current_user: Current authenticated user (from JWT)

    Returns:
        MetricsResponse with system metrics
    """
    try:
        # System metrics (using psutil)
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Process metrics
        process = psutil.Process(os.getpid())
        process_memory_mb = process.memory_info().rss / 1024 / 1024

        # Request metrics
        total_requests = metrics_collector.request_success + metrics_collector.request_errors
        avg_latency = (
            sum(metrics_collector.request_times) / len(metrics_collector.request_times)
            if metrics_collector.request_times
            else 0
        )

        return MetricsResponse(
            timestamp=datetime.utcnow(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=disk.percent,
            process_memory_mb=process_memory_mb,
            api_requests_total=total_requests,
            api_requests_errors=metrics_collector.request_errors,
            api_requests_success=metrics_collector.request_success,
            avg_request_latency_ms=avg_latency,
        )

    except Exception as e:
        logger.error(f"Metrics error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve metrics")


@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(current_user: Dict = Depends(get_current_user)):
    """
    Get detailed performance metrics

    Returns latency percentiles (p50, p95, p99), cache rates, and success rates

    Args:
        current_user: Current authenticated user (from JWT)

    Returns:
        PerformanceMetrics with percentiles and rates
    """
    try:
        percentiles = metrics_collector.get_latency_percentiles()

        # Calculate rates
        total_cache_ops = metrics_collector.cache_hits + metrics_collector.cache_misses
        cache_hit_rate = metrics_collector.cache_hits / total_cache_ops if total_cache_ops > 0 else 0

        total_webhooks = metrics_collector.webhook_successes + metrics_collector.webhook_failures
        webhook_success_rate = metrics_collector.webhook_successes / total_webhooks if total_webhooks > 0 else 0

        total_agents = metrics_collector.agent_successes + metrics_collector.agent_failures
        agent_success_rate = metrics_collector.agent_successes / total_agents if total_agents > 0 else 0

        return PerformanceMetrics(
            timestamp=datetime.utcnow(),
            request_latency_percentiles=percentiles,
            cache_hit_rate=cache_hit_rate,
            cache_miss_rate=1 - cache_hit_rate,
            database_query_time_ms=0,  # TODO: Track actual DB query times
            webhook_delivery_success_rate=webhook_success_rate,
            agent_execution_success_rate=agent_success_rate,
        )

    except Exception as e:
        logger.error(f"Performance metrics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve performance metrics"
        )


@router.get("/alerts", response_model=List[AlertResponse])
async def get_active_alerts(severity: Optional[str] = None, current_user: Dict = Depends(get_current_user)):
    """
    Get active system alerts

    Returns alerts when thresholds are exceeded (CPU > 80%, memory > 85%, etc.)

    Args:
        severity: Filter by severity (info, warning, critical)
        current_user: Current authenticated user (from JWT)

    Returns:
        List of AlertResponse
    """
    alerts: List[AlertResponse] = []

    try:
        # Get current metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Check thresholds
        if cpu_percent > 80:
            alerts.append(
                AlertResponse(
                    alert_id="cpu_high",
                    severity="critical",
                    component="system/cpu",
                    message=f"CPU usage high: {cpu_percent}%",
                    threshold=80.0,
                    current_value=cpu_percent,
                    created_at=datetime.utcnow(),
                )
            )

        if memory.percent > 85:
            alerts.append(
                AlertResponse(
                    alert_id="memory_high",
                    severity="critical",
                    component="system/memory",
                    message=f"Memory usage high: {memory.percent}%",
                    threshold=85.0,
                    current_value=memory.percent,
                    created_at=datetime.utcnow(),
                )
            )

        if disk.percent > 90:
            alerts.append(
                AlertResponse(
                    alert_id="disk_high",
                    severity="warning",
                    component="system/disk",
                    message=f"Disk usage high: {disk.percent}%",
                    threshold=90.0,
                    current_value=disk.percent,
                    created_at=datetime.utcnow(),
                )
            )

        # Filter by severity if provided
        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        return alerts

    except Exception as e:
        logger.error(f"Alerts error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve alerts")


@router.get("/dependencies", response_model=Dict[str, Dict[str, Any]])
async def check_dependencies(current_user: Dict = Depends(get_current_user)):
    """
    Check status of external dependencies

    Returns health status of database, cache, external APIs, etc.

    Args:
        current_user: Current authenticated user (from JWT)

    Returns:
        Dictionary with dependency status
    """
    dependencies = {
        "database": {"status": "unknown", "latency_ms": None, "error": None},  # TODO: Ping database
        "cache": {"status": "unknown", "latency_ms": None, "error": None},  # TODO: Ping Redis
        "anthropic_api": {"status": "unknown", "latency_ms": None, "error": None},  # TODO: Ping Anthropic API
        "openai_api": {"status": "unknown", "latency_ms": None, "error": None},  # TODO: Ping OpenAI API
    }

    return dependencies
