"""Dashboard Summary API for DevSkyy Admin Dashboard.

Provides a unified endpoint for fetching aggregated dashboard data including:
- System health metrics
- ML pipeline status
- Business metrics overview
- Active alerts

Version: 1.0.0
"""

import hashlib
import json
import logging
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import Order, get_db
from security.jwt_oauth2_auth import TokenPayload, UserRole, get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/analytics/dashboard", tags=["Dashboard Analytics"])

# Cache TTL constants (in seconds)
CACHE_TTL_REALTIME = 60  # 1 minute for real-time sections
CACHE_TTL_BUSINESS = 300  # 5 minutes for business metrics


# =============================================================================
# Enums
# =============================================================================


class DashboardSection(str, Enum):
    """Available dashboard sections."""

    HEALTH = "health"
    ML = "ml"
    BUSINESS = "business"
    ALERTS = "alerts"


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class PipelineStatus(str, Enum):
    """ML Pipeline status values."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PENDING = "pending"


# =============================================================================
# Response Models
# =============================================================================


class ServiceHealth(BaseModel):
    """Individual service health status."""

    name: str
    status: Literal["healthy", "degraded", "unhealthy"]
    response_time_ms: float | None = None
    last_check: str


class SystemHealthSection(BaseModel):
    """System health section of dashboard."""

    overall_status: Literal["healthy", "degraded", "unhealthy"]
    services: list[ServiceHealth]
    uptime_pct: float
    cpu_usage_pct: float | None = None
    memory_usage_pct: float | None = None
    active_connections: int | None = None
    last_updated: str


class MLPipelineInfo(BaseModel):
    """Individual ML pipeline information."""

    pipeline_id: str
    name: str
    status: PipelineStatus
    progress_pct: float | None = None
    started_at: str | None = None
    completed_at: str | None = None
    error_message: str | None = None


class MLPipelinesSection(BaseModel):
    """ML Pipelines section of dashboard."""

    total_pipelines: int
    running: int
    completed: int
    failed: int
    pending: int
    pipelines: list[MLPipelineInfo]
    last_updated: str


class BusinessMetric(BaseModel):
    """Business metric with trend information."""

    value: float
    change_pct: float | None = None
    trend: Literal["up", "down", "flat"] | None = None


class BusinessSection(BaseModel):
    """Business metrics section of dashboard."""

    total_revenue: BusinessMetric
    order_count: BusinessMetric
    average_order_value: BusinessMetric
    active_customers: BusinessMetric
    conversion_rate: BusinessMetric | None = None
    period_days: int
    last_updated: str


class AlertInfo(BaseModel):
    """Individual alert information."""

    alert_id: str
    title: str
    message: str
    severity: AlertSeverity
    source: str
    created_at: str
    acknowledged: bool = False


class AlertsSection(BaseModel):
    """Active alerts section of dashboard."""

    total_alerts: int
    critical: int
    warning: int
    info: int
    alerts: list[AlertInfo]
    last_updated: str


class DashboardSummaryResponse(BaseModel):
    """Complete dashboard summary response."""

    status: str
    timestamp: str
    user_role: str
    requested_sections: list[str]
    system_health: SystemHealthSection | None = None
    ml_pipelines: MLPipelinesSection | None = None
    business: BusinessSection | None = None
    active_alerts: AlertsSection | None = None
    cache_hit: bool = False


# =============================================================================
# Cache Helper
# =============================================================================


class DashboardCache:
    """Simple in-memory cache for dashboard data with Redis fallback."""

    def __init__(self) -> None:
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self._redis: Any = None

    async def _get_redis(self) -> Any:
        """Get Redis client if available."""
        if self._redis is None:
            try:
                from core.redis_cache import RedisCache

                cache = RedisCache()
                connected = await cache.connect()
                if connected:
                    self._redis = cache
            except ImportError:
                logger.debug("Redis cache not available")
            except Exception as e:
                logger.debug(f"Redis connection failed: {e}")
        return self._redis

    def _generate_key(self, section: str, user_id: str, **kwargs: Any) -> str:
        """Generate cache key."""
        key_data = {"section": section, "user_id": user_id, **kwargs}
        key_hash = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()[:16]
        return f"dashboard:{section}:{key_hash}"

    async def get(self, section: str, user_id: str, **kwargs: Any) -> Any | None:
        """Get cached value."""
        key = self._generate_key(section, user_id, **kwargs)

        # Try Redis first
        redis = await self._get_redis()
        if redis:
            try:
                data = await redis._client.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.debug(f"Redis get error: {e}")

        # Fall back to in-memory cache
        if key in self._cache:
            value, expiry = self._cache[key]
            if datetime.now(UTC) < expiry:
                return value
            del self._cache[key]

        return None

    async def set(
        self, section: str, user_id: str, value: Any, ttl: int = CACHE_TTL_REALTIME, **kwargs: Any
    ) -> None:
        """Set cached value."""
        key = self._generate_key(section, user_id, **kwargs)

        # Try Redis first
        redis = await self._get_redis()
        if redis:
            try:
                await redis._client.setex(key, ttl, json.dumps(value))
                return
            except Exception as e:
                logger.debug(f"Redis set error: {e}")

        # Fall back to in-memory cache
        expiry = datetime.now(UTC) + timedelta(seconds=ttl)
        self._cache[key] = (value, expiry)


# Global cache instance
_dashboard_cache = DashboardCache()


# =============================================================================
# Data Fetchers
# =============================================================================


async def fetch_system_health() -> SystemHealthSection:
    """Fetch current system health metrics."""
    now = datetime.now(UTC)

    # Get service health (simulated for now - in production, ping actual services)
    services = [
        ServiceHealth(
            name="api",
            status="healthy",
            response_time_ms=12.5,
            last_check=now.isoformat(),
        ),
        ServiceHealth(
            name="database",
            status="healthy",
            response_time_ms=3.2,
            last_check=now.isoformat(),
        ),
        ServiceHealth(
            name="redis",
            status="healthy",
            response_time_ms=1.1,
            last_check=now.isoformat(),
        ),
        ServiceHealth(
            name="mcp_server",
            status="healthy",
            response_time_ms=8.4,
            last_check=now.isoformat(),
        ),
    ]

    # Calculate overall status
    unhealthy_count = sum(1 for s in services if s.status == "unhealthy")
    degraded_count = sum(1 for s in services if s.status == "degraded")

    if unhealthy_count > 0:
        overall_status = "unhealthy"
    elif degraded_count > 0:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return SystemHealthSection(
        overall_status=overall_status,
        services=services,
        uptime_pct=99.95,
        cpu_usage_pct=45.2,
        memory_usage_pct=62.8,
        active_connections=128,
        last_updated=now.isoformat(),
    )


async def fetch_ml_pipelines() -> MLPipelinesSection:
    """Fetch ML pipeline status information."""
    now = datetime.now(UTC)

    # Get pipeline information (simulated - in production, query pipeline registry)
    pipelines = [
        MLPipelineInfo(
            pipeline_id="pipe-001",
            name="Product Classification",
            status=PipelineStatus.RUNNING,
            progress_pct=67.5,
            started_at=(now - timedelta(hours=2)).isoformat(),
        ),
        MLPipelineInfo(
            pipeline_id="pipe-002",
            name="Price Optimization",
            status=PipelineStatus.COMPLETED,
            progress_pct=100.0,
            started_at=(now - timedelta(hours=5)).isoformat(),
            completed_at=(now - timedelta(hours=3)).isoformat(),
        ),
        MLPipelineInfo(
            pipeline_id="pipe-003",
            name="Demand Forecasting",
            status=PipelineStatus.PENDING,
        ),
    ]

    # Count by status
    running = sum(1 for p in pipelines if p.status == PipelineStatus.RUNNING)
    completed = sum(1 for p in pipelines if p.status == PipelineStatus.COMPLETED)
    failed = sum(1 for p in pipelines if p.status == PipelineStatus.FAILED)
    pending = sum(1 for p in pipelines if p.status == PipelineStatus.PENDING)

    return MLPipelinesSection(
        total_pipelines=len(pipelines),
        running=running,
        completed=completed,
        failed=failed,
        pending=pending,
        pipelines=pipelines,
        last_updated=now.isoformat(),
    )


async def fetch_business_metrics(db: AsyncSession, period_days: int = 30) -> BusinessSection:
    """Fetch business metrics from database."""
    now = datetime.now(UTC)
    period_start = now - timedelta(days=period_days)
    previous_period_start = period_start - timedelta(days=period_days)

    try:
        # Current period metrics
        current_query = select(
            func.count(Order.id).label("order_count"),
            func.sum(Order.total).label("total_revenue"),
            func.avg(Order.total).label("avg_order_value"),
            func.count(func.distinct(Order.user_id)).label("unique_customers"),
        ).where(
            Order.created_at >= period_start,
            Order.created_at < now,
            Order.status != "cancelled",
        )

        current_result = await db.execute(current_query)
        current_row = current_result.one()

        # Previous period metrics for comparison
        previous_query = select(
            func.count(Order.id).label("order_count"),
            func.sum(Order.total).label("total_revenue"),
            func.avg(Order.total).label("avg_order_value"),
            func.count(func.distinct(Order.user_id)).label("unique_customers"),
        ).where(
            Order.created_at >= previous_period_start,
            Order.created_at < period_start,
            Order.status != "cancelled",
        )

        previous_result = await db.execute(previous_query)
        previous_row = previous_result.one()

        def calculate_metric(current: float | None, previous: float | None) -> BusinessMetric:
            """Calculate metric with trend."""
            current_val = float(current or 0)
            previous_val = float(previous or 0)

            if previous_val == 0:
                change_pct = 100.0 if current_val > 0 else 0.0
                trend = "up" if current_val > 0 else "flat"
            else:
                change_pct = ((current_val - previous_val) / previous_val) * 100
                if change_pct > 1:
                    trend = "up"
                elif change_pct < -1:
                    trend = "down"
                else:
                    trend = "flat"

            return BusinessMetric(
                value=round(current_val, 2),
                change_pct=round(change_pct, 2),
                trend=trend,
            )

        return BusinessSection(
            total_revenue=calculate_metric(current_row.total_revenue, previous_row.total_revenue),
            order_count=calculate_metric(current_row.order_count, previous_row.order_count),
            average_order_value=calculate_metric(
                current_row.avg_order_value, previous_row.avg_order_value
            ),
            active_customers=calculate_metric(
                current_row.unique_customers, previous_row.unique_customers
            ),
            period_days=period_days,
            last_updated=now.isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to fetch business metrics: {e}")
        # Return empty metrics on error
        return BusinessSection(
            total_revenue=BusinessMetric(value=0),
            order_count=BusinessMetric(value=0),
            average_order_value=BusinessMetric(value=0),
            active_customers=BusinessMetric(value=0),
            period_days=period_days,
            last_updated=now.isoformat(),
        )


async def fetch_active_alerts() -> AlertsSection:
    """Fetch active alerts from alert system."""
    now = datetime.now(UTC)

    # Get alerts (simulated - in production, query alert database)
    alerts = [
        AlertInfo(
            alert_id="alert-001",
            title="High Memory Usage",
            message="Memory usage exceeded 80% threshold on production server",
            severity=AlertSeverity.WARNING,
            source="monitoring",
            created_at=(now - timedelta(hours=1)).isoformat(),
        ),
        AlertInfo(
            alert_id="alert-002",
            title="ML Pipeline Slow",
            message="Product classification pipeline taking longer than expected",
            severity=AlertSeverity.INFO,
            source="ml_pipelines",
            created_at=(now - timedelta(hours=2)).isoformat(),
        ),
    ]

    # Count by severity
    critical = sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL)
    warning = sum(1 for a in alerts if a.severity == AlertSeverity.WARNING)
    info = sum(1 for a in alerts if a.severity == AlertSeverity.INFO)

    return AlertsSection(
        total_alerts=len(alerts),
        critical=critical,
        warning=warning,
        info=info,
        alerts=alerts,
        last_updated=now.isoformat(),
    )


# =============================================================================
# Role-based filtering
# =============================================================================


def get_allowed_sections(user: TokenPayload) -> set[DashboardSection]:
    """Determine which sections a user can access based on their role."""
    admin_roles = {UserRole.SUPER_ADMIN, UserRole.ADMIN}
    developer_roles = {UserRole.DEVELOPER}
    business_roles = {UserRole.API_USER, UserRole.READ_ONLY}

    # Admins and developers see all sections
    if user.has_any_role(admin_roles) or user.has_any_role(developer_roles):
        return {
            DashboardSection.HEALTH,
            DashboardSection.ML,
            DashboardSection.BUSINESS,
            DashboardSection.ALERTS,
        }

    # Business users see only business metrics
    if user.has_any_role(business_roles):
        return {DashboardSection.BUSINESS}

    # Guests see nothing
    return set()


# =============================================================================
# Endpoints
# =============================================================================


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    status_code=status.HTTP_200_OK,
)
async def get_dashboard_summary(
    sections: str | None = Query(
        default=None,
        description="Comma-separated list of sections to include (health,ml,business,alerts). "
        "If not specified, returns all sections the user has access to.",
        examples=["health,ml,business,alerts", "business", "health,alerts"],
    ),
    period_days: int = Query(
        default=30,
        ge=1,
        le=365,
        description="Number of days for business metrics period",
    ),
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardSummaryResponse:
    """Get unified dashboard summary data.

    Returns aggregated data from multiple sources in a single response.
    Supports role-based filtering and section selection.

    **Role-based access:**
    - Admins/Developers: All sections (health, ml, business, alerts)
    - Business users (API_USER, READ_ONLY): Business metrics only
    - Guests: No access

    **Caching:**
    - Real-time sections (health, alerts): 1-minute TTL
    - Business metrics: 5-minute TTL

    Args:
        sections: Optional comma-separated list of sections to include
        period_days: Number of days for business metrics (1-365)
        user: Authenticated user from JWT token
        db: Database session

    Returns:
        DashboardSummaryResponse with requested sections
    """
    logger.info(f"Getting dashboard summary for user {user.sub}")
    now = datetime.now(UTC)

    # Determine allowed sections based on role
    allowed_sections = get_allowed_sections(user)

    if not allowed_sections:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access the dashboard",
        )

    # Parse requested sections
    if sections:
        requested = set()
        for s in sections.split(","):
            s = s.strip().lower()
            try:
                requested.add(DashboardSection(s))
            except ValueError:
                logger.warning(f"Unknown section requested: {s}")
        # Filter to only allowed sections
        requested_sections = requested & allowed_sections
    else:
        # Return all allowed sections if none specified
        requested_sections = allowed_sections

    if not requested_sections:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid sections requested or accessible",
        )

    # Determine user's highest role for display
    highest_role = user.get_highest_role()
    role_display = highest_role.value if highest_role else "unknown"

    # Build response
    response = DashboardSummaryResponse(
        status="success",
        timestamp=now.isoformat(),
        user_role=role_display,
        requested_sections=[s.value for s in requested_sections],
    )

    cache_hit = False

    # Fetch each requested section
    if DashboardSection.HEALTH in requested_sections:
        # Check cache first
        cached = await _dashboard_cache.get("health", user.sub)
        if cached:
            response.system_health = SystemHealthSection(**cached)
            cache_hit = True
        else:
            health_data = await fetch_system_health()
            response.system_health = health_data
            await _dashboard_cache.set(
                "health", user.sub, health_data.model_dump(), ttl=CACHE_TTL_REALTIME
            )

    if DashboardSection.ML in requested_sections:
        cached = await _dashboard_cache.get("ml", user.sub)
        if cached:
            response.ml_pipelines = MLPipelinesSection(**cached)
            cache_hit = True
        else:
            ml_data = await fetch_ml_pipelines()
            response.ml_pipelines = ml_data
            await _dashboard_cache.set("ml", user.sub, ml_data.model_dump(), ttl=CACHE_TTL_REALTIME)

    if DashboardSection.BUSINESS in requested_sections:
        cache_key_extra = {"period_days": period_days}
        cached = await _dashboard_cache.get("business", user.sub, **cache_key_extra)
        if cached:
            response.business = BusinessSection(**cached)
            cache_hit = True
        else:
            business_data = await fetch_business_metrics(db, period_days)
            response.business = business_data
            await _dashboard_cache.set(
                "business",
                user.sub,
                business_data.model_dump(),
                ttl=CACHE_TTL_BUSINESS,
                **cache_key_extra,
            )

    if DashboardSection.ALERTS in requested_sections:
        cached = await _dashboard_cache.get("alerts", user.sub)
        if cached:
            response.active_alerts = AlertsSection(**cached)
            cache_hit = True
        else:
            alerts_data = await fetch_active_alerts()
            response.active_alerts = alerts_data
            await _dashboard_cache.set(
                "alerts", user.sub, alerts_data.model_dump(), ttl=CACHE_TTL_REALTIME
            )

    response.cache_hit = cache_hit
    return response
