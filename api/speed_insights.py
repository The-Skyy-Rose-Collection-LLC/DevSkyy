"""
Vercel Speed Insights Integration
==================================

This module provides integration with Vercel Speed Insights for monitoring
API performance metrics including response times, throughput, and error rates.

Speed Insights allows tracking of:
- Core Web Vitals (CLS, FID, LCP)
- API response times
- Error rates and types
- Resource utilization

Documentation: https://vercel.com/docs/speed-insights
"""

import logging
import time
from datetime import UTC, datetime
from typing import Any, Callable

from fastapi import Request, Response
from fastapi.routing import APIRouter

logger = logging.getLogger(__name__)


class SpeedInsightsMetrics:
    """Metrics container for Speed Insights tracking"""

    def __init__(self):
        self.metrics: dict[str, Any] = {
            "total_requests": 0,
            "total_errors": 0,
            "total_response_time": 0.0,
            "min_response_time": float("inf"),
            "max_response_time": 0.0,
            "endpoint_metrics": {},
        }

    def record_request(self, method: str, path: str, status_code: int, duration_ms: float):
        """Record metrics for a request"""
        self.metrics["total_requests"] += 1
        self.metrics["total_response_time"] += duration_ms

        # Update min/max
        if duration_ms < self.metrics["min_response_time"]:
            self.metrics["min_response_time"] = duration_ms
        if duration_ms > self.metrics["max_response_time"]:
            self.metrics["max_response_time"] = duration_ms

        # Track errors
        if status_code >= 400:
            self.metrics["total_errors"] += 1

        # Track per-endpoint metrics
        endpoint_key = f"{method} {path}"
        if endpoint_key not in self.metrics["endpoint_metrics"]:
            self.metrics["endpoint_metrics"][endpoint_key] = {
                "count": 0,
                "total_time": 0.0,
                "errors": 0,
                "avg_time": 0.0,
            }

        endpoint = self.metrics["endpoint_metrics"][endpoint_key]
        endpoint["count"] += 1
        endpoint["total_time"] += duration_ms
        endpoint["avg_time"] = endpoint["total_time"] / endpoint["count"]

        if status_code >= 400:
            endpoint["errors"] += 1

    def get_stats(self) -> dict[str, Any]:
        """Get current metrics statistics"""
        total_requests = self.metrics["total_requests"]
        if total_requests == 0:
            return {
                "status": "no_data",
                "total_requests": 0,
                "avg_response_time_ms": 0,
                "error_rate": 0,
            }

        avg_response_time = self.metrics["total_response_time"] / total_requests
        error_rate = (self.metrics["total_errors"] / total_requests) * 100 if total_requests > 0 else 0

        return {
            "status": "healthy" if error_rate < 5 else "degraded",
            "total_requests": total_requests,
            "total_errors": self.metrics["total_errors"],
            "error_rate_percent": round(error_rate, 2),
            "avg_response_time_ms": round(avg_response_time, 2),
            "min_response_time_ms": (
                round(self.metrics["min_response_time"], 2)
                if self.metrics["min_response_time"] != float("inf")
                else 0
            ),
            "max_response_time_ms": round(self.metrics["max_response_time"], 2),
            "endpoint_count": len(self.metrics["endpoint_metrics"]),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def get_endpoint_metrics(self) -> dict[str, Any]:
        """Get detailed per-endpoint metrics"""
        return {
            "endpoints": self.metrics["endpoint_metrics"],
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def reset(self):
        """Reset metrics (useful for periodic snapshots)"""
        self.__init__()


class SpeedInsightsMiddleware:
    """
    FastAPI middleware for tracking performance metrics compatible with Vercel Speed Insights.
    
    This middleware:
    - Records response times for all endpoints
    - Tracks error rates
    - Collects per-endpoint statistics
    - Makes metrics available via Speed Insights endpoint
    """

    def __init__(self, enabled: bool = True, verbose: bool = False):
        self.enabled = enabled
        self.verbose = verbose
        self.metrics = SpeedInsightsMetrics()

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request and track metrics"""
        if not self.enabled:
            return await call_next(request)

        # Skip metrics collection for health checks and Speed Insights endpoints
        if request.url.path in ["/health", "/ready", "/live"] or request.url.path.startswith(
            "/_vercel/speed-insights"
        ):
            return await call_next(request)

        # Record start time
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Record metrics
        self.metrics.record_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        if self.verbose:
            logger.debug(
                f"Speed Insights: {request.method} {request.url.path} - "
                f"{response.status_code} - {duration_ms:.2f}ms"
            )

        # Add performance header
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

        return response


# Global metrics instance
speed_insights_metrics = SpeedInsightsMetrics()

# Create router for Speed Insights endpoints
speed_insights_router = APIRouter(
    prefix="/_vercel/speed-insights", tags=["Speed Insights"], include_in_schema=False
)


@speed_insights_router.get("/metrics")
async def get_metrics():
    """
    Get current performance metrics for Speed Insights dashboard.
    
    This endpoint returns aggregated metrics about API performance,
    compatible with Vercel Speed Insights monitoring.
    """
    return speed_insights_metrics.get_stats()


@speed_insights_router.get("/endpoint-metrics")
async def get_endpoint_metrics():
    """
    Get detailed per-endpoint performance metrics.
    
    Returns breakdown of response times, error rates, and request counts
    for each API endpoint.
    """
    return speed_insights_metrics.get_endpoint_metrics()


@speed_insights_router.post("/events")
async def record_event(event: dict[str, Any]):
    """
    Record custom performance events for Speed Insights.
    
    Accepts custom events like Core Web Vitals, custom timings, etc.
    """
    logger.info(f"Speed Insights event recorded: {event}")
    return {"status": "recorded", "timestamp": datetime.now(UTC).isoformat()}


@speed_insights_router.get("/health")
async def speed_insights_health():
    """Health check for Speed Insights integration"""
    stats = speed_insights_metrics.get_stats()
    return {
        "status": "operational",
        "metrics_status": stats.get("status", "no_data"),
        "total_requests": stats.get("total_requests", 0),
        "timestamp": datetime.now(UTC).isoformat(),
    }


def create_speed_insights_middleware(
    enabled: bool = True, verbose: bool = False
) -> SpeedInsightsMiddleware:
    """
    Factory function to create Speed Insights middleware.
    
    Args:
        enabled: Whether to enable metric collection
        verbose: Whether to log all metric collection
    
    Returns:
        Configured SpeedInsightsMiddleware instance
    """
    return SpeedInsightsMiddleware(enabled=enabled, verbose=verbose)


__all__ = [
    "SpeedInsightsMetrics",
    "SpeedInsightsMiddleware",
    "speed_insights_metrics",
    "speed_insights_router",
    "create_speed_insights_middleware",
]
