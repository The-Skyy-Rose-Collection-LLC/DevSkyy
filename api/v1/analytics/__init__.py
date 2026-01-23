"""Analytics API module for DevSkyy admin dashboard."""

from api.v1.analytics.business import router as business_router
from api.v1.analytics.dashboard import router as analytics_dashboard_router
from api.v1.analytics.health import router as health_analytics_router

__all__ = ["business_router", "analytics_dashboard_router", "health_analytics_router"]
