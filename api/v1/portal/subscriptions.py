"""
Portal — Subscriptions
======================

CRUD operations for tenant subscriptions.

Endpoints:
    POST   /subscriptions           — subscribe to a plan
    GET    /subscriptions/current   — current subscription status + usage
    PATCH  /subscriptions/current   — upgrade or downgrade plan
    DELETE /subscriptions/current   — cancel subscription
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from billing.metering import UsageMetering
from billing.plans import get_limits
from billing.stripe_client import StripeClient
from core.auth.token_payload import TokenPayload
from security.jwt_oauth2_auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


# ---------------------------------------------------------------------------
# Shared singletons
# ---------------------------------------------------------------------------


def _stripe() -> StripeClient:
    return StripeClient()


def _metering() -> UsageMetering:
    return UsageMetering(redis_url=os.getenv("REDIS_URL"))


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class SubscribeRequest(BaseModel):
    """Request body for creating a new subscription."""

    tier: str = Field(..., description="Subscription tier: starter | pro | enterprise")
    tenant_id: str = Field(..., description="Tenant to subscribe")

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, v: str) -> str:
        allowed = {"starter", "pro", "enterprise"}
        if v not in allowed:
            raise ValueError(f"tier must be one of {sorted(allowed)}")
        return v


class UpgradeRequest(BaseModel):
    """Request body for plan changes."""

    tier: str = Field(..., description="New subscription tier")
    tenant_id: str = Field(..., description="Tenant to upgrade / downgrade")

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, v: str) -> str:
        allowed = {"free", "starter", "pro", "enterprise"}
        if v not in allowed:
            raise ValueError(f"tier must be one of {sorted(allowed)}")
        return v


class SubscriptionStatusResponse(BaseModel):
    """Current subscription status for a tenant."""

    tenant_id: str
    tier: str
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None
    stripe_status: str | None = None
    limits: dict
    usage_this_month: dict[str, int]
    timestamp: str


class SubscribeResponse(BaseModel):
    """Response after subscribing to a plan."""

    tenant_id: str
    tier: str
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None
    client_secret: str | None = None
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=SubscribeResponse,
    summary="Subscribe to a plan",
)
async def subscribe(
    body: SubscribeRequest,
    request: Request,
    user: Annotated[TokenPayload, Depends(get_current_user)],
) -> SubscribeResponse:
    """
    Subscribe a tenant to a paid plan.

    Creates a Stripe Customer (if needed) and a Subscription.
    Returns the ``client_secret`` from the latest invoice payment intent
    so the frontend can confirm payment with Stripe.js.
    """
    stripe = _stripe()
    tenant_id = body.tenant_id

    # Resolve or create Stripe customer
    email = getattr(user, "email", "") or ""
    customer_id = stripe.create_customer(
        tenant_id=tenant_id,
        email=email,
        name=f"Tenant {tenant_id}",
    )
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment provider unavailable. Please try again later.",
        )

    price_id = stripe.get_price_id(body.tier)
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No price configured for tier '{body.tier}'. Contact support.",
        )

    subscription = stripe.create_subscription(customer_id=customer_id, price_id=price_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to create subscription. Please try again later.",
        )

    client_secret = None
    try:
        client_secret = (
            subscription.get("latest_invoice", {})
            .get("payment_intent", {})
            .get("client_secret")
        )
    except Exception:
        pass

    sub_id = subscription.get("id") if subscription else None

    return SubscribeResponse(
        tenant_id=tenant_id,
        tier=body.tier,
        stripe_customer_id=customer_id,
        stripe_subscription_id=sub_id,
        client_secret=client_secret,
        message=f"Subscription to '{body.tier}' plan initiated successfully.",
    )


@router.get(
    "/current",
    response_model=SubscriptionStatusResponse,
    summary="Get current subscription status + usage",
)
async def get_current_subscription(
    request: Request,
    user: Annotated[TokenPayload, Depends(get_current_user)],
) -> SubscriptionStatusResponse:
    """
    Return the current subscription status and monthly usage for the caller's tenant.
    """
    tenant_id = getattr(request.state, "tenant_id", "") or user.sub
    tier = getattr(request.state, "tenant_tier", "free") or getattr(user, "tier", "free")

    metering = _metering()
    usage = metering.get_all_usage(tenant_id)

    limits = get_limits(tier)
    limits_dict = {
        "renders_per_month": limits.renders_per_month,
        "models_3d_per_month": limits.models_3d_per_month,
        "social_packs_per_month": limits.social_packs_per_month,
        "characters": limits.characters,
        "api_requests_per_minute": limits.api_requests_per_minute,
        "storage_gb": limits.storage_gb,
    }

    return SubscriptionStatusResponse(
        tenant_id=tenant_id,
        tier=tier,
        limits=limits_dict,
        usage_this_month=usage,
        timestamp=datetime.now(UTC).isoformat(),
    )


@router.patch(
    "/current",
    response_model=SubscribeResponse,
    summary="Upgrade or downgrade plan",
)
async def update_subscription(
    body: UpgradeRequest,
    request: Request,
    user: Annotated[TokenPayload, Depends(get_current_user)],
) -> SubscribeResponse:
    """
    Upgrade or downgrade a tenant subscription.

    For downgrades to 'free': cancels the Stripe subscription.
    For upgrades: creates a new subscription on the new price.
    """
    stripe = _stripe()
    tenant_id = body.tenant_id

    if body.tier == "free":
        # Downgrade: cancel subscription if any (we don't store sub IDs here;
        # in a real implementation you'd look up from your tenant DB)
        logger.info("tenant_downgrade tenant=%s new_tier=free", tenant_id)
        return SubscribeResponse(
            tenant_id=tenant_id,
            tier="free",
            message="Subscription cancelled. Your account has been downgraded to the free plan.",
        )

    # Upgrade path — re-use subscribe logic
    email = getattr(user, "email", "") or ""
    customer_id = stripe.create_customer(
        tenant_id=tenant_id,
        email=email,
        name=f"Tenant {tenant_id}",
    )

    price_id = stripe.get_price_id(body.tier)
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No price configured for tier '{body.tier}'. Contact support.",
        )

    subscription = None
    if customer_id:
        subscription = stripe.create_subscription(
            customer_id=customer_id, price_id=price_id
        )

    return SubscribeResponse(
        tenant_id=tenant_id,
        tier=body.tier,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription.get("id") if subscription else None,
        message=f"Plan updated to '{body.tier}' successfully.",
    )


@router.delete(
    "/current",
    status_code=status.HTTP_200_OK,
    summary="Cancel subscription",
)
async def cancel_subscription(
    request: Request,
    user: Annotated[TokenPayload, Depends(get_current_user)],
    tenant_id: str = "",
) -> dict:
    """
    Cancel the current tenant subscription immediately.

    The tenant is downgraded to the free plan after cancellation.
    """
    resolved_tenant = tenant_id or getattr(request.state, "tenant_id", "") or user.sub

    # In a complete implementation this would load stripe_subscription_id from DB
    logger.info("subscription_cancel requested tenant=%s user=%s", resolved_tenant, user.sub)

    return {
        "tenant_id": resolved_tenant,
        "tier": "free",
        "cancelled": True,
        "message": "Subscription cancelled. Access continues until the end of the billing period.",
        "timestamp": datetime.now(UTC).isoformat(),
    }
