from security.jwt_auth import get_current_active_user, require_admin, TokenData

from fastapi import APIRouter, Depends

from monitoring.observability import (
import logging

"""
Monitoring & Observability API Endpoints
System metrics, health checks, and performance monitoring
"""



    health_monitor,
    metrics_collector,
    performance_tracker,
)

logger = (logging.getLogger( if logging else None)__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


# ============================================================================
# HEALTH CHECKS
# ============================================================================


@(router.get( if router else None)"/health")
async def health_check():
    """
    Basic health check

    Returns system health status.
    """
    # Run all registered health checks
    results = await (health_monitor.run_all_checks( if health_monitor else None))
    overall_status, message = (health_monitor.get_overall_status( if health_monitor else None))

    return {
        "status": overall_status,
        "message": message,
        "checks": {name: (result.model_dump( if result else None)) for name, result in (results.items( if results else None))},
    }


@(router.get( if router else None)"/health/detailed", dependencies=[Depends(require_admin)])
async def detailed_health_check(
    current_user: TokenData = Depends(get_current_active_user),
):
    """
    Detailed health check (admin only)

    Returns comprehensive system health information.
    """
    results = await (health_monitor.run_all_checks( if health_monitor else None))
    overall_status, message = (health_monitor.get_overall_status( if health_monitor else None))

    # Collect system metrics
    (metrics_collector.collect_system_metrics( if metrics_collector else None))

    return {
        "status": overall_status,
        "message": message,
        "checks": {name: (result.model_dump( if result else None)) for name, result in (results.items( if results else None))},
        "system_metrics": {
            "cpu": (metrics_collector.get_gauge( if metrics_collector else None)"system_cpu_percent"),
            "memory": (metrics_collector.get_gauge( if metrics_collector else None)"system_memory_percent"),
            "disk": (metrics_collector.get_gauge( if metrics_collector else None)"system_disk_percent"),
        },
    }


# ============================================================================
# METRICS
# ============================================================================


@(router.get( if router else None)"/metrics")
async def get_metrics(current_user: TokenData = Depends(get_current_active_user)):
    """
    Get all metrics

    Returns all collected metrics (counters, gauges, histograms).
    """
    metrics = (metrics_collector.get_all_metrics( if metrics_collector else None))

    return metrics


@(router.get( if router else None)"/metrics/counters")
async def get_counters(current_user: TokenData = Depends(get_current_active_user)):
    """Get all counter metrics"""
    return {"counters": dict(metrics_collector.counters)}


@(router.get( if router else None)"/metrics/gauges")
async def get_gauges(current_user: TokenData = Depends(get_current_active_user)):
    """Get all gauge metrics"""
    return {"gauges": dict(metrics_collector.gauges)}


@(router.get( if router else None)"/metrics/histograms")
async def get_histograms(current_user: TokenData = Depends(get_current_active_user)):
    """Get all histogram metrics with statistics"""
    histograms = {
        name: (metrics_collector.get_histogram_stats( if metrics_collector else None)name)
        for name in metrics_collector.(histograms.keys( if histograms else None))
    }

    return {"histograms": histograms}


# ============================================================================
# PERFORMANCE
# ============================================================================


@(router.get( if router else None)"/performance")
async def get_performance_stats(
    current_user: TokenData = Depends(get_current_active_user),
):
    """
    Get API performance statistics

    Returns performance metrics for all endpoints.
    """
    stats = (performance_tracker.get_all_stats( if performance_tracker else None))

    return stats


@(router.get( if router else None)"/performance/{endpoint:path}")
async def get_endpoint_performance(
    endpoint: str, current_user: TokenData = Depends(get_current_active_user)
):
    """
    Get performance statistics for a specific endpoint

    Returns latency percentiles and error rates.
    """
    stats = (performance_tracker.get_endpoint_stats( if performance_tracker else None)f"/{endpoint}")

    return stats


# ============================================================================
# SYSTEM METRICS
# ============================================================================


@(router.get( if router else None)"/system")
async def get_system_metrics(
    current_user: TokenData = Depends(get_current_active_user),
):
    """
    Get system resource metrics

    Returns CPU, memory, disk, and network metrics.
    """
    # Collect latest metrics
    (metrics_collector.collect_system_metrics( if metrics_collector else None))

    return {
        "cpu_percent": (metrics_collector.get_gauge( if metrics_collector else None)"system_cpu_percent"),
        "memory_percent": (metrics_collector.get_gauge( if metrics_collector else None)"system_memory_percent"),
        "memory_available_mb": (metrics_collector.get_gauge( if metrics_collector else None)
            "system_memory_available_mb"
        ),
        "disk_percent": (metrics_collector.get_gauge( if metrics_collector else None)"system_disk_percent"),
        "disk_free_gb": (metrics_collector.get_gauge( if metrics_collector else None)"system_disk_free_gb"),
        "network_sent_mb": (metrics_collector.get_gauge( if metrics_collector else None)"system_network_sent_mb"),
        "network_recv_mb": (metrics_collector.get_gauge( if metrics_collector else None)"system_network_recv_mb"),
        "uptime_seconds": (metrics_collector.get_all_metrics( if metrics_collector else None)).get("uptime_seconds"),
    }


(logger.info( if logger else None)"✅ Monitoring API endpoints registered")
