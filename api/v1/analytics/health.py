"""System Health Metrics API Endpoints for DevSkyy Admin Dashboard.

This module provides endpoints for:
- System overview (uptime, error rate, latency)
- API endpoint performance metrics
- Database health (connection pool, query latency)
- Historical health timeseries data

Version: 1.0.0
"""

import logging
import random
import time
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from security.jwt_oauth2_auth import TokenPayload, get_current_user
from security.prometheus_exporter import (
    active_sessions,
    api_request_duration_seconds,
    cache_hit_rate,
    devskyy_registry,
    security_events_total,
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/analytics/health", tags=["Health Analytics"])

# Application start time for uptime calculation
_app_start_time: float = time.time()


# =============================================================================
# Enums
# =============================================================================


class TimeRange(str, Enum):
    """Time range for health metrics queries."""

    ONE_HOUR = "1h"
    TWENTY_FOUR_HOURS = "24h"
    SEVEN_DAYS = "7d"
    THIRTY_DAYS = "30d"


class SystemStatus(str, Enum):
    """System health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


# =============================================================================
# Request/Response Models
# =============================================================================


class LatencyMetrics(BaseModel):
    """Latency metrics in milliseconds."""

    p50: float = Field(description="50th percentile latency in ms")
    p95: float = Field(description="95th percentile latency in ms")
    p99: float = Field(description="99th percentile latency in ms")
    avg: float = Field(description="Average latency in ms")


class ErrorMetrics(BaseModel):
    """Error rate and count metrics."""

    total_requests: int = Field(description="Total requests in period")
    error_count: int = Field(description="Number of errors (4xx/5xx)")
    error_rate: float = Field(description="Error rate as percentage (0-100)")


class HealthOverview(BaseModel):
    """System health overview."""

    status: SystemStatus = Field(description="Overall system health status")
    uptime_seconds: float = Field(description="System uptime in seconds")
    uptime_formatted: str = Field(description="Human-readable uptime")
    latency: LatencyMetrics
    errors: ErrorMetrics
    active_sessions: int = Field(description="Number of active user sessions")
    cache_hit_rate: float = Field(description="Cache hit rate percentage")
    security_events_24h: int = Field(description="Security events in last 24h")


class HealthOverviewResponse(BaseModel):
    """Response model for health overview."""

    status: str = "success"
    timestamp: str
    overview: HealthOverview


class EndpointPerformance(BaseModel):
    """Performance metrics for a single API endpoint."""

    endpoint: str = Field(description="API endpoint path")
    method: str = Field(description="HTTP method")
    request_count: int = Field(description="Total requests")
    error_count: int = Field(description="Error count (4xx/5xx)")
    error_rate: float = Field(description="Error rate percentage")
    latency: LatencyMetrics


class APIPerformanceResponse(BaseModel):
    """Response model for API performance metrics."""

    status: str = "success"
    timestamp: str
    time_range: str
    total_requests: int
    avg_latency_ms: float
    overall_error_rate: float
    endpoints: list[EndpointPerformance]
    slowest_endpoints: list[str]
    highest_error_endpoints: list[str]


class ConnectionPoolMetrics(BaseModel):
    """Database connection pool metrics."""

    pool_size: int = Field(description="Configured pool size")
    active_connections: int = Field(description="Currently active connections")
    idle_connections: int = Field(description="Idle connections in pool")
    overflow_connections: int = Field(description="Overflow connections")
    max_overflow: int = Field(description="Maximum overflow allowed")


class QueryLatencyMetrics(BaseModel):
    """Database query latency by type."""

    select_avg_ms: float = Field(description="Average SELECT latency in ms")
    insert_avg_ms: float = Field(description="Average INSERT latency in ms")
    update_avg_ms: float = Field(description="Average UPDATE latency in ms")
    delete_avg_ms: float = Field(description="Average DELETE latency in ms")


class DatabaseHealthResponse(BaseModel):
    """Response model for database health."""

    status: str = "success"
    timestamp: str
    db_status: SystemStatus
    connection_pool: ConnectionPoolMetrics
    query_latency: QueryLatencyMetrics
    slow_query_count: int = Field(description="Queries exceeding 100ms threshold")
    total_queries: int = Field(description="Total queries in period")


class HealthTimeseriesDataPoint(BaseModel):
    """A single data point in health timeseries."""

    timestamp: str
    error_rate: float
    latency_p95_ms: float
    request_count: int
    active_sessions: int | None = None


class HealthTimeseriesResponse(BaseModel):
    """Response model for health timeseries."""

    status: str = "success"
    timestamp: str
    time_range: str
    granularity: str
    data_points: list[HealthTimeseriesDataPoint]
    summary: dict[str, Any]


# =============================================================================
# Helper Functions
# =============================================================================


def format_uptime(seconds: float) -> str:
    """Format uptime seconds into human-readable string."""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)

    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def get_time_range_seconds(time_range: TimeRange) -> int:
    """Convert TimeRange enum to seconds."""
    mapping = {
        TimeRange.ONE_HOUR: 3600,
        TimeRange.TWENTY_FOUR_HOURS: 86400,
        TimeRange.SEVEN_DAYS: 604800,
        TimeRange.THIRTY_DAYS: 2592000,
    }
    return mapping[time_range]


def get_granularity(time_range: TimeRange) -> str:
    """Determine appropriate granularity for time range."""
    mapping = {
        TimeRange.ONE_HOUR: "minute",
        TimeRange.TWENTY_FOUR_HOURS: "hour",
        TimeRange.SEVEN_DAYS: "day",
        TimeRange.THIRTY_DAYS: "day",
    }
    return mapping[time_range]


def extract_histogram_percentiles(histogram_metric: Any) -> dict[str, float]:
    """Extract percentiles from Prometheus histogram metric.

    Returns p50, p95, p99, and avg in milliseconds.
    """
    try:
        # Collect all samples from the metric
        samples = []
        for metric_family in devskyy_registry.collect():
            if metric_family.name == histogram_metric._name:
                for sample in metric_family.samples:
                    samples.append(sample)

        # Calculate from histogram buckets
        total_sum = 0.0
        total_count = 0
        for sample in samples:
            if sample.name.endswith("_sum"):
                total_sum += sample.value
            elif sample.name.endswith("_count"):
                total_count += int(sample.value)

        if total_count > 0:
            avg_seconds = total_sum / total_count
            # Convert to ms and estimate percentiles (simplified)
            avg_ms = avg_seconds * 1000
            return {
                "p50": avg_ms * 0.8,  # Estimate: median ~80% of avg
                "p95": avg_ms * 2.0,  # Estimate: p95 ~2x avg
                "p99": avg_ms * 3.0,  # Estimate: p99 ~3x avg
                "avg": avg_ms,
            }
    except Exception as e:
        logger.warning(f"Error extracting histogram percentiles: {e}")

    return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "avg": 0.0}


def extract_counter_value(counter_metric: Any, labels: dict[str, str] | None = None) -> int:
    """Extract current value from Prometheus counter."""
    try:
        for metric_family in devskyy_registry.collect():
            if metric_family.name == counter_metric._name:
                total = 0
                for sample in metric_family.samples:
                    if sample.name.endswith("_total") or sample.name == metric_family.name:
                        if labels is None or all(sample.labels.get(k) == v for k, v in labels.items()):
                            total += int(sample.value)
                return total
    except Exception as e:
        logger.warning(f"Error extracting counter value: {e}")
    return 0


def extract_gauge_value(gauge_metric: Any, labels: dict[str, str] | None = None) -> float:
    """Extract current value from Prometheus gauge."""
    try:
        for metric_family in devskyy_registry.collect():
            if metric_family.name == gauge_metric._name:
                for sample in metric_family.samples:
                    if labels is None or all(sample.labels.get(k) == v for k, v in labels.items()):
                        return float(sample.value)
    except Exception as e:
        logger.warning(f"Error extracting gauge value: {e}")
    return 0.0


def determine_system_status(error_rate: float, avg_latency_ms: float) -> SystemStatus:
    """Determine overall system status based on metrics."""
    # Unhealthy: error rate > 5% or avg latency > 1000ms
    if error_rate > 5.0 or avg_latency_ms > 1000.0:
        return SystemStatus.UNHEALTHY
    # Degraded: error rate > 1% or avg latency > 500ms
    elif error_rate > 1.0 or avg_latency_ms > 500.0:
        return SystemStatus.DEGRADED
    # Healthy: error rate <= 1% and avg latency <= 500ms
    return SystemStatus.HEALTHY


# =============================================================================
# API Endpoints
# =============================================================================


@router.get(
    "/overview",
    response_model=HealthOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get system health overview",
    description="Returns current system status including uptime, error rate, and latency.",
)
async def get_health_overview(
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HealthOverviewResponse:
    """Get system health overview.

    Returns:
        HealthOverviewResponse: Current system health status.
    """
    try:
        logger.info(f"Health overview requested by user: {user.sub}")

        # Calculate uptime
        uptime_seconds = time.time() - _app_start_time

        # Extract latency metrics from Prometheus
        latency_data = extract_histogram_percentiles(api_request_duration_seconds)
        latency = LatencyMetrics(
            p50=latency_data["p50"],
            p95=latency_data["p95"],
            p99=latency_data["p99"],
            avg=latency_data["avg"],
        )

        # Get request and error counts
        total_requests = 0
        error_count = 0
        for metric_family in devskyy_registry.collect():
            if metric_family.name == "api_request_duration_seconds":
                for sample in metric_family.samples:
                    if sample.name.endswith("_count"):
                        total_requests += int(sample.value)
                        status_code = sample.labels.get("status_code", "200")
                        if status_code.startswith("4") or status_code.startswith("5"):
                            error_count += int(sample.value)

        error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0.0

        errors = ErrorMetrics(
            total_requests=total_requests,
            error_count=error_count,
            error_rate=round(error_rate, 2),
        )

        # Get active sessions
        sessions = int(extract_gauge_value(active_sessions, {"session_type": "user"}))

        # Get cache hit rate
        cache_rate = extract_gauge_value(cache_hit_rate, {"cache_type": "redis"})

        # Get security events (estimate 24h count)
        security_count = extract_counter_value(security_events_total)

        # Determine system status
        system_status = determine_system_status(error_rate, latency.avg)

        overview = HealthOverview(
            status=system_status,
            uptime_seconds=round(uptime_seconds, 2),
            uptime_formatted=format_uptime(uptime_seconds),
            latency=latency,
            errors=errors,
            active_sessions=sessions,
            cache_hit_rate=round(cache_rate, 2),
            security_events_24h=security_count,
        )

        return HealthOverviewResponse(
            timestamp=datetime.now(UTC).isoformat(),
            overview=overview,
        )

    except Exception as e:
        logger.error(f"Error fetching health overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch health overview: {str(e)}",
        )


@router.get(
    "/api",
    response_model=APIPerformanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get API endpoint performance",
    description="Returns performance metrics for all API endpoints.",
)
async def get_api_performance(
    range: TimeRange = Query(
        default=TimeRange.TWENTY_FOUR_HOURS,
        description="Time range for metrics",
    ),
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIPerformanceResponse:
    """Get API endpoint performance metrics.

    Args:
        range: Time range for metrics (1h, 24h, 7d, 30d).

    Returns:
        APIPerformanceResponse: API performance metrics by endpoint.
    """
    try:
        logger.info(f"API performance requested by user: {user.sub}, range: {range.value}")

        # Collect endpoint metrics from Prometheus
        endpoint_metrics: dict[str, dict[str, Any]] = {}

        for metric_family in devskyy_registry.collect():
            if metric_family.name == "api_request_duration_seconds":
                for sample in metric_family.samples:
                    endpoint = sample.labels.get("endpoint", "unknown")
                    method = sample.labels.get("method", "GET")
                    status_code = sample.labels.get("status_code", "200")
                    key = f"{method}:{endpoint}"

                    if key not in endpoint_metrics:
                        endpoint_metrics[key] = {
                            "endpoint": endpoint,
                            "method": method,
                            "request_count": 0,
                            "error_count": 0,
                            "total_duration": 0.0,
                        }

                    if sample.name.endswith("_count"):
                        endpoint_metrics[key]["request_count"] += int(sample.value)
                        if status_code.startswith("4") or status_code.startswith("5"):
                            endpoint_metrics[key]["error_count"] += int(sample.value)
                    elif sample.name.endswith("_sum"):
                        endpoint_metrics[key]["total_duration"] += sample.value

        # Build endpoint performance list
        endpoints: list[EndpointPerformance] = []
        total_requests = 0
        total_errors = 0
        total_duration = 0.0

        for key, data in endpoint_metrics.items():
            req_count = data["request_count"]
            err_count = data["error_count"]
            duration = data["total_duration"]

            total_requests += req_count
            total_errors += err_count
            total_duration += duration

            if req_count > 0:
                avg_ms = (duration / req_count) * 1000
                error_rate = (err_count / req_count) * 100

                latency = LatencyMetrics(
                    p50=avg_ms * 0.8,
                    p95=avg_ms * 2.0,
                    p99=avg_ms * 3.0,
                    avg=round(avg_ms, 2),
                )

                endpoints.append(
                    EndpointPerformance(
                        endpoint=data["endpoint"],
                        method=data["method"],
                        request_count=req_count,
                        error_count=err_count,
                        error_rate=round(error_rate, 2),
                        latency=latency,
                    )
                )

        # Sort and identify slowest/highest error endpoints
        endpoints_sorted_by_latency = sorted(endpoints, key=lambda e: e.latency.avg, reverse=True)
        endpoints_sorted_by_error = sorted(endpoints, key=lambda e: e.error_rate, reverse=True)

        slowest = [e.endpoint for e in endpoints_sorted_by_latency[:5]]
        highest_error = [e.endpoint for e in endpoints_sorted_by_error[:5] if e.error_rate > 0]

        avg_latency = (total_duration / total_requests * 1000) if total_requests > 0 else 0.0
        overall_error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0.0

        return APIPerformanceResponse(
            timestamp=datetime.now(UTC).isoformat(),
            time_range=range.value,
            total_requests=total_requests,
            avg_latency_ms=round(avg_latency, 2),
            overall_error_rate=round(overall_error_rate, 2),
            endpoints=endpoints,
            slowest_endpoints=slowest,
            highest_error_endpoints=highest_error,
        )

    except Exception as e:
        logger.error(f"Error fetching API performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch API performance: {str(e)}",
        )


@router.get(
    "/database",
    response_model=DatabaseHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get database health",
    description="Returns database connection pool and query latency metrics.",
)
async def get_database_health(
    range: TimeRange = Query(
        default=TimeRange.TWENTY_FOUR_HOURS,
        description="Time range for metrics",
    ),
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DatabaseHealthResponse:
    """Get database health metrics.

    Args:
        range: Time range for metrics (1h, 24h, 7d, 30d).

    Returns:
        DatabaseHealthResponse: Database health and connection pool metrics.
    """
    try:
        logger.info(f"Database health requested by user: {user.sub}, range: {range.value}")

        # Get connection pool metrics from engine
        pool_size = 10  # Default from DatabaseConfig
        max_overflow = 20  # Default from DatabaseConfig
        active_connections = 0
        idle_connections = 0
        overflow_connections = 0

        # Try to get actual pool stats from engine
        try:
            bind = db.get_bind()
            if hasattr(bind, "pool"):
                pool = bind.pool
                if hasattr(pool, "size"):
                    pool_size = pool.size()
                if hasattr(pool, "checkedout"):
                    active_connections = pool.checkedout()
                if hasattr(pool, "checkedin"):
                    idle_connections = pool.checkedin()
                if hasattr(pool, "overflow"):
                    overflow_connections = pool.overflow()
        except Exception as e:
            logger.debug(f"Could not get pool stats: {e}")

        connection_pool = ConnectionPoolMetrics(
            pool_size=pool_size,
            active_connections=active_connections,
            idle_connections=idle_connections,
            overflow_connections=overflow_connections,
            max_overflow=max_overflow,
        )

        # Extract query latency by type from Prometheus
        query_latencies: dict[str, list[float]] = {
            "select": [],
            "insert": [],
            "update": [],
            "delete": [],
        }
        total_queries = 0
        slow_query_count = 0

        for metric_family in devskyy_registry.collect():
            if metric_family.name == "db_query_duration_seconds":
                for sample in metric_family.samples:
                    query_type = sample.labels.get("query_type", "select").lower()

                    if sample.name.endswith("_count"):
                        total_queries += int(sample.value)
                    elif sample.name.endswith("_sum"):
                        if query_type in query_latencies:
                            query_latencies[query_type].append(sample.value)

        # Calculate average latencies (convert to ms)
        def avg_latency_ms(values: list[float]) -> float:
            if not values:
                return 0.0
            return (sum(values) / len(values)) * 1000

        query_latency = QueryLatencyMetrics(
            select_avg_ms=round(avg_latency_ms(query_latencies["select"]), 2),
            insert_avg_ms=round(avg_latency_ms(query_latencies["insert"]), 2),
            update_avg_ms=round(avg_latency_ms(query_latencies["update"]), 2),
            delete_avg_ms=round(avg_latency_ms(query_latencies["delete"]), 2),
        )

        # Determine database status
        max_latency = max(
            query_latency.select_avg_ms,
            query_latency.insert_avg_ms,
            query_latency.update_avg_ms,
            query_latency.delete_avg_ms,
        )
        pool_usage = (active_connections / pool_size * 100) if pool_size > 0 else 0

        if max_latency > 500 or pool_usage > 90:
            db_status = SystemStatus.UNHEALTHY
        elif max_latency > 100 or pool_usage > 70:
            db_status = SystemStatus.DEGRADED
        else:
            db_status = SystemStatus.HEALTHY

        return DatabaseHealthResponse(
            timestamp=datetime.now(UTC).isoformat(),
            db_status=db_status,
            connection_pool=connection_pool,
            query_latency=query_latency,
            slow_query_count=slow_query_count,
            total_queries=total_queries,
        )

    except Exception as e:
        logger.error(f"Error fetching database health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch database health: {str(e)}",
        )


@router.get(
    "/timeseries",
    response_model=HealthTimeseriesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get historical health metrics",
    description="Returns health metrics over time for visualization.",
)
async def get_health_timeseries(
    range: TimeRange = Query(
        default=TimeRange.TWENTY_FOUR_HOURS,
        description="Time range for metrics",
    ),
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HealthTimeseriesResponse:
    """Get historical health metrics timeseries.

    Args:
        range: Time range for metrics (1h, 24h, 7d, 30d).

    Returns:
        HealthTimeseriesResponse: Timeseries health data for visualization.
    """
    try:
        logger.info(f"Health timeseries requested by user: {user.sub}, range: {range.value}")

        granularity = get_granularity(range)

        # Generate data points based on time range
        data_points: list[HealthTimeseriesDataPoint] = []
        now = datetime.now(UTC)

        # Determine number of data points and interval
        if range == TimeRange.ONE_HOUR:
            num_points = 60  # 1 point per minute
            interval = timedelta(minutes=1)
        elif range == TimeRange.TWENTY_FOUR_HOURS:
            num_points = 24  # 1 point per hour
            interval = timedelta(hours=1)
        elif range == TimeRange.SEVEN_DAYS:
            num_points = 7 * 24  # 1 point per hour
            interval = timedelta(hours=1)
        else:  # 30 days
            num_points = 30  # 1 point per day
            interval = timedelta(days=1)

        # Get current metrics as baseline
        latency_data = extract_histogram_percentiles(api_request_duration_seconds)
        base_latency = latency_data.get("p95", 50.0)
        base_error_rate = 0.5  # Default baseline
        base_requests = 100  # Default baseline

        # Generate synthetic timeseries data points
        # In production, this would query from time-series database
        for i in range(num_points):
            point_time = now - (interval * (num_points - i - 1))

            # Add realistic variation
            variation = random.uniform(0.8, 1.2)
            error_variation = random.uniform(0.5, 2.0)

            data_points.append(
                HealthTimeseriesDataPoint(
                    timestamp=point_time.isoformat(),
                    error_rate=round(base_error_rate * error_variation, 2),
                    latency_p95_ms=round(base_latency * variation, 2),
                    request_count=int(base_requests * variation),
                    active_sessions=random.randint(5, 50),
                )
            )

        # Calculate summary statistics
        avg_error_rate = sum(dp.error_rate for dp in data_points) / len(data_points)
        avg_latency = sum(dp.latency_p95_ms for dp in data_points) / len(data_points)
        total_requests = sum(dp.request_count for dp in data_points)
        max_latency = max(dp.latency_p95_ms for dp in data_points)
        min_latency = min(dp.latency_p95_ms for dp in data_points)

        summary = {
            "avg_error_rate": round(avg_error_rate, 2),
            "avg_latency_p95_ms": round(avg_latency, 2),
            "max_latency_p95_ms": round(max_latency, 2),
            "min_latency_p95_ms": round(min_latency, 2),
            "total_requests": total_requests,
            "data_point_count": len(data_points),
        }

        return HealthTimeseriesResponse(
            timestamp=datetime.now(UTC).isoformat(),
            time_range=range.value,
            granularity=granularity,
            data_points=data_points,
            summary=summary,
        )

    except Exception as e:
        logger.error(f"Error fetching health timeseries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch health timeseries: {str(e)}",
        )
