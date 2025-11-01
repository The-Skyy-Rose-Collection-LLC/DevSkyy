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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

# ============================================================================
# HEALTH CHECKS
# ============================================================================

@router.get("/health")
async def health_check():
    """
    Basic health check

    Returns system health status.
    """
    # Run all registered health checks
    results = await health_monitor.run_all_checks()
    overall_status, message = health_monitor.get_overall_status()

    return {
        "status": overall_status,
        "message": message,
        "checks": {name: result.model_dump() for name, result in results.items()},
    }

@router.get("/health/detailed", dependencies=[Depends(require_admin)])
async def detailed_health_check(
    current_user: TokenData = Depends(get_current_active_user),
):
    """
    Detailed health check (admin only)

    Returns comprehensive system health information.
    """
    results = await health_monitor.run_all_checks()
    overall_status, message = health_monitor.get_overall_status()

    # Collect system metrics
    metrics_collector.collect_system_metrics()

    return {
        "status": overall_status,
        "message": message,
        "checks": {name: result.model_dump() for name, result in results.items()},
        "system_metrics": {
            "cpu": metrics_collector.get_gauge("system_cpu_percent"),
            "memory": metrics_collector.get_gauge("system_memory_percent"),
            "disk": metrics_collector.get_gauge("system_disk_percent"),
        },
    }

# ============================================================================
# METRICS
# ============================================================================

@router.get("/metrics")
async def get_metrics(current_user: TokenData = Depends(get_current_active_user)):
    """
    Get all metrics

    Returns all collected metrics (counters, gauges, histograms).
    """
    metrics = metrics_collector.get_all_metrics()

    return metrics

@router.get("/metrics/counters")
async def get_counters(current_user: TokenData = Depends(get_current_active_user)):
    """Get all counter metrics"""
    return {"counters": dict(metrics_collector.counters)}

@router.get("/metrics/gauges")
async def get_gauges(current_user: TokenData = Depends(get_current_active_user)):
    """Get all gauge metrics"""
    return {"gauges": dict(metrics_collector.gauges)}

@router.get("/metrics/histograms")
async def get_histograms(current_user: TokenData = Depends(get_current_active_user)):
    """Get all histogram metrics with statistics"""
    histograms = {
        name: metrics_collector.get_histogram_stats(name)
        for name in metrics_collector.histograms.keys()
    }

    return {"histograms": histograms}

# ============================================================================
# PERFORMANCE
# ============================================================================

@router.get("/performance")
async def get_performance_stats(
    current_user: TokenData = Depends(get_current_active_user),
):
    """
    Get API performance statistics

    Returns performance metrics for all endpoints.
    """
    stats = performance_tracker.get_all_stats()

    return stats

@router.get("/performance/{endpoint:path}")
async def get_endpoint_performance(
    endpoint: str, current_user: TokenData = Depends(get_current_active_user)
):
    """
    Get performance statistics for a specific endpoint

    Returns latency percentiles and error rates.
    """
    stats = performance_tracker.get_endpoint_stats(f"/{endpoint}")

    return stats

# ============================================================================
# SYSTEM METRICS
# ============================================================================

@router.get("/system")
async def get_system_metrics(
    current_user: TokenData = Depends(get_current_active_user),
):
    """
    Get system resource metrics

    Returns CPU, memory, disk, and network metrics.
    """
    # Collect latest metrics
    metrics_collector.collect_system_metrics()

    return {
        "cpu_percent": metrics_collector.get_gauge("system_cpu_percent"),
        "memory_percent": metrics_collector.get_gauge("system_memory_percent"),
        "memory_available_mb": metrics_collector.get_gauge(
            "system_memory_available_mb"
        ),
        "disk_percent": metrics_collector.get_gauge("system_disk_percent"),
        "disk_free_gb": metrics_collector.get_gauge("system_disk_free_gb"),
        "network_sent_mb": metrics_collector.get_gauge("system_network_sent_mb"),
        "network_recv_mb": metrics_collector.get_gauge("system_network_recv_mb"),
        "uptime_seconds": metrics_collector.get_all_metrics().get("uptime_seconds"),
    }

logger.info("✅ Monitoring API endpoints registered")
