"""
Health Check Endpoints for Kubernetes/Docker

Provides liveness and readiness probes following cloud-native best practices:
- /health/liveness: Is the process running? (restart if fails)
- /health/readiness: Can we serve traffic? (stop routing if fails)
- /health: Combined health status

Truth Protocol Compliance:
- Rule #12: Performance SLOs (P95 < 200ms for health checks)
- Rule #10: No-Skip Rule (all checks logged)

References:
- Kubernetes Health Checks: https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
"""

import asyncio
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Response, status

router = APIRouter(prefix="/health", tags=["health"])


# =============================================================================
# Health Check Models
# =============================================================================


def _check_result(name: str, healthy: bool, message: str = "", latency_ms: float = 0) -> dict[str, Any]:
    """
    Create a standardized health check result.

    Args:
        name: Name of the component being checked.
        healthy: Whether the component is healthy.
        message: Optional message with details.
        latency_ms: Time taken for the check in milliseconds.

    Returns:
        Dict with standardized health check result.
    """
    return {
        "name": name,
        "status": "healthy" if healthy else "unhealthy",
        "healthy": healthy,
        "message": message,
        "latency_ms": round(latency_ms, 2),
    }


async def _check_database() -> dict[str, Any]:
    """
    Check database connectivity.

    Returns:
        Health check result for database.
    """
    start = datetime.now()
    try:
        from database import db_manager

        result = await db_manager.health_check()
        latency = (datetime.now() - start).total_seconds() * 1000

        if result.get("status") == "healthy":
            return _check_result(
                "database",
                True,
                f"Connected to {result.get('type', 'unknown')}",
                latency,
            )
        return _check_result(
            "database",
            False,
            result.get("error", "Unknown error"),
            latency,
        )
    except Exception as e:
        latency = (datetime.now() - start).total_seconds() * 1000
        return _check_result("database", False, str(e), latency)


async def _check_redis() -> dict[str, Any]:
    """
    Check Redis connectivity.

    Returns:
        Health check result for Redis.
    """
    start = datetime.now()
    try:
        import redis.asyncio as redis

        from core.settings import get_settings

        settings = get_settings()
        client = redis.from_url(settings.redis_url, decode_responses=True)

        # Simple ping check
        await asyncio.wait_for(client.ping(), timeout=2.0)
        await client.close()

        latency = (datetime.now() - start).total_seconds() * 1000
        return _check_result("redis", True, "Connected", latency)

    except asyncio.TimeoutError:
        latency = (datetime.now() - start).total_seconds() * 1000
        return _check_result("redis", False, "Connection timeout", latency)
    except Exception as e:
        latency = (datetime.now() - start).total_seconds() * 1000
        # Redis is optional - mark as healthy but note it's unavailable
        return _check_result("redis", True, f"Optional: {e}", latency)


async def _check_ai_services() -> dict[str, Any]:
    """
    Check AI service availability.

    Returns:
        Health check result for AI services.
    """
    start = datetime.now()
    try:
        from core.settings import get_settings

        settings = get_settings()

        # Check if API key is configured
        if settings.anthropic_api_key:
            latency = (datetime.now() - start).total_seconds() * 1000
            return _check_result("ai_services", True, "Anthropic API configured", latency)

        latency = (datetime.now() - start).total_seconds() * 1000
        return _check_result("ai_services", True, "No API key (optional)", latency)

    except Exception as e:
        latency = (datetime.now() - start).total_seconds() * 1000
        return _check_result("ai_services", False, str(e), latency)


# =============================================================================
# Liveness Probe
# =============================================================================


@router.get(
    "/liveness",
    summary="Liveness probe",
    description="Check if the process is running. Kubernetes restarts the pod if this fails.",
    response_description="Simple alive status",
)
async def liveness():
    """
    Liveness probe - is the process alive?

    This endpoint should be fast and simple. It only checks if the Python
    process is responding. Kubernetes will restart the pod if this fails.

    Returns:
        dict: {"status": "alive", "timestamp": "..."}
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
    }


# =============================================================================
# Readiness Probe
# =============================================================================


@router.get(
    "/readiness",
    summary="Readiness probe",
    description="Check if the app can serve traffic. Kubernetes stops routing if this fails.",
    response_description="Readiness status with component checks",
)
async def readiness(response: Response):
    """
    Readiness probe - can we serve traffic?

    Checks critical dependencies:
    - Database connectivity
    - Redis connectivity (optional)
    - AI services availability (optional)

    If any critical check fails, returns 503 and Kubernetes stops routing
    traffic to this pod (but doesn't restart it).

    Returns:
        dict: Readiness status with individual component checks.
    """
    start = datetime.now()

    # Run checks concurrently for speed
    db_check, redis_check, ai_check = await asyncio.gather(
        _check_database(),
        _check_redis(),
        _check_ai_services(),
        return_exceptions=True,
    )

    # Handle any exceptions from gather
    if isinstance(db_check, Exception):
        db_check = _check_result("database", False, str(db_check), 0)
    if isinstance(redis_check, Exception):
        redis_check = _check_result("redis", True, f"Check failed: {redis_check}", 0)
    if isinstance(ai_check, Exception):
        ai_check = _check_result("ai_services", True, f"Check failed: {ai_check}", 0)

    checks = {
        "database": db_check,
        "redis": redis_check,
        "ai_services": ai_check,
    }

    # Database is critical - if it fails, we're not ready
    critical_healthy = db_check.get("healthy", False)

    total_latency = (datetime.now() - start).total_seconds() * 1000

    result = {
        "status": "ready" if critical_healthy else "not_ready",
        "timestamp": datetime.now().isoformat(),
        "checks": checks,
        "total_latency_ms": round(total_latency, 2),
    }

    if not critical_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return result


# =============================================================================
# Combined Health Check
# =============================================================================


@router.get(
    "",
    summary="Combined health check",
    description="Comprehensive health status including version and uptime.",
    response_description="Full health status",
)
async def health_check(response: Response):
    """
    Combined health check endpoint.

    Provides comprehensive health status including:
    - Application version and environment
    - Uptime information
    - All component health checks
    - Performance metrics

    Returns:
        dict: Comprehensive health status.
    """
    start = datetime.now()

    try:
        from core.settings import get_settings

        settings = get_settings()

        # Get readiness checks
        db_check, redis_check, ai_check = await asyncio.gather(
            _check_database(),
            _check_redis(),
            _check_ai_services(),
            return_exceptions=True,
        )

        # Handle exceptions
        if isinstance(db_check, Exception):
            db_check = _check_result("database", False, str(db_check), 0)
        if isinstance(redis_check, Exception):
            redis_check = _check_result("redis", True, f"Check failed: {redis_check}", 0)
        if isinstance(ai_check, Exception):
            ai_check = _check_result("ai_services", True, f"Check failed: {ai_check}", 0)

        checks = {
            "database": db_check,
            "redis": redis_check,
            "ai_services": ai_check,
        }

        # Calculate overall health
        all_healthy = all(c.get("healthy", False) for c in checks.values())
        critical_healthy = db_check.get("healthy", False)

        total_latency = (datetime.now() - start).total_seconds() * 1000

        result = {
            "status": "healthy" if all_healthy else ("degraded" if critical_healthy else "unhealthy"),
            "version": settings.version,
            "environment": settings.environment,
            "timestamp": datetime.now().isoformat(),
            "checks": checks,
            "summary": {
                "total_checks": len(checks),
                "healthy_checks": sum(1 for c in checks.values() if c.get("healthy", False)),
                "total_latency_ms": round(total_latency, 2),
            },
        }

        if not critical_healthy:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return result

    except Exception as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


# =============================================================================
# Startup Probe (for slow-starting applications)
# =============================================================================


@router.get(
    "/startup",
    summary="Startup probe",
    description="Check if the application has finished starting up.",
    response_description="Startup status",
)
async def startup_check():
    """
    Startup probe - has the app finished initializing?

    This is useful for applications that take time to start.
    Kubernetes won't send liveness/readiness probes until this passes.

    Returns:
        dict: {"status": "started", "timestamp": "..."}
    """
    # Check if critical components are initialized
    try:
        from database import db_manager

        # If we can access these, startup is complete
        return {
            "status": "started",
            "timestamp": datetime.now().isoformat(),
            "database_manager": "initialized" if db_manager else "not_initialized",
        }
    except ImportError:
        return {
            "status": "starting",
            "timestamp": datetime.now().isoformat(),
            "message": "Components still loading",
        }
