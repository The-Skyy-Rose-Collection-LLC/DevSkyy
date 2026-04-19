"""
Customer Portal API
===================

FastAPI routers for tenant self-service:
- /api/v1/portal/subscriptions — subscribe / upgrade / cancel
- /api/v1/portal/usage         — usage summary
- /api/v1/portal/billing       — invoices and Stripe portal
- /api/v1/portal/team          — team member management
"""

from fastapi import APIRouter

from .billing import router as billing_router
from .subscriptions import router as subscriptions_router
from .team import router as team_router
from .usage import router as usage_router

portal_router = APIRouter(prefix="/portal", tags=["Portal"])
portal_router.include_router(subscriptions_router)
portal_router.include_router(usage_router)
portal_router.include_router(billing_router)
portal_router.include_router(team_router)

__all__ = ["portal_router"]
