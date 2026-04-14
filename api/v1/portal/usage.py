"""
Portal — Usage
==============

Usage reporting endpoints for tenants.

Endpoints:
    GET /usage         — current period usage summary per intent
    GET /usage/history — last 6 months usage
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from billing.metering import UsageMetering
from billing.plans import get_limits, quota_remaining
from core.auth.token_payload import TokenPayload
from security.jwt_oauth2_auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/usage", tags=["Usage"])


# ---------------------------------------------------------------------------
# Shared singleton
# ---------------------------------------------------------------------------


def _metering() -> UsageMetering:
    return UsageMetering(redis_url=os.getenv("REDIS_URL"))


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class IntentUsageSummary(BaseModel):
    """Per-intent usage breakdown."""

    intent: str
    used: int
    quota: int  # -1 = unlimited
    remaining: int  # -1 = unlimited


class UsageSummaryResponse(BaseModel):
    """Current period usage summary."""

    tenant_id: str
    tier: str
    period: str
    intents: list[IntentUsageSummary]
    timestamp: str


class MonthlyUsageRecord(BaseModel):
    """Usage for a single month."""

    period: str
    total_operations: int
    intents: dict[str, int]


class UsageHistoryResponse(BaseModel):
    """Usage over the last 6 months."""

    tenant_id: str
    tier: str
    months: list[MonthlyUsageRecord]
    timestamp: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=UsageSummaryResponse,
    summary="Current period usage summary",
)
async def get_current_usage(
    request: Request,
    user: Annotated[TokenPayload, Depends(get_current_user)],
) -> UsageSummaryResponse:
    """
    Return usage breakdown for each creative intent for the current billing month.
    """
    tenant_id = getattr(request.state, "tenant_id", "") or user.sub
    tier = getattr(request.state, "tenant_tier", "free") or getattr(user, "tier", "free")

    metering = _metering()
    period = _current_period()
    all_usage = metering.get_all_usage(tenant_id=tenant_id, period=period)

    limits = get_limits(tier)
    intent_summaries: list[IntentUsageSummary] = []

    # Report on all known intents, not just those with recorded usage
    known_intents = [
        "product-render",
        "scene-composite",
        "virtual-tryon",
        "moodboard",
        "3d-model",
        "social-pack",
        "product-copy",
    ]

    for intent in known_intents:
        used = all_usage.get(intent, 0)
        remaining = quota_remaining(tier=tier, intent=intent, used=used)
        quota_field = _intent_to_quota_field(intent)
        quota_total: int = getattr(limits, quota_field, -1)

        intent_summaries.append(
            IntentUsageSummary(
                intent=intent,
                used=used,
                quota=quota_total,
                remaining=remaining,
            )
        )

    return UsageSummaryResponse(
        tenant_id=tenant_id,
        tier=tier,
        period=period,
        intents=intent_summaries,
        timestamp=datetime.now(UTC).isoformat(),
    )


@router.get(
    "/history",
    response_model=UsageHistoryResponse,
    summary="Last 6 months usage history",
)
async def get_usage_history(
    request: Request,
    user: Annotated[TokenPayload, Depends(get_current_user)],
) -> UsageHistoryResponse:
    """
    Return aggregated usage for each of the last 6 billing months.
    """
    tenant_id = getattr(request.state, "tenant_id", "") or user.sub
    tier = getattr(request.state, "tenant_tier", "free") or getattr(user, "tier", "free")

    metering = _metering()
    monthly_records: list[MonthlyUsageRecord] = []

    for period in _last_n_periods(6):
        intents_usage = metering.get_all_usage(tenant_id=tenant_id, period=period)
        total = sum(intents_usage.values())
        monthly_records.append(
            MonthlyUsageRecord(
                period=period,
                total_operations=total,
                intents=intents_usage,
            )
        )

    return UsageHistoryResponse(
        tenant_id=tenant_id,
        tier=tier,
        months=monthly_records,
        timestamp=datetime.now(UTC).isoformat(),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _current_period() -> str:
    return datetime.now(UTC).strftime("%Y-%m")


def _last_n_periods(n: int) -> list[str]:
    """Return the last *n* YYYY-MM strings in reverse chronological order."""
    from datetime import date
    from dateutil.relativedelta import relativedelta  # type: ignore[import]

    periods: list[str] = []
    current = date.today().replace(day=1)
    for _ in range(n):
        periods.append(current.strftime("%Y-%m"))
        current = current - relativedelta(months=1)
    return periods


def _intent_to_quota_field(intent: str) -> str:
    _map = {
        "product-render": "renders_per_month",
        "scene-composite": "renders_per_month",
        "virtual-tryon": "renders_per_month",
        "moodboard": "renders_per_month",
        "3d-model": "models_3d_per_month",
        "social-pack": "social_packs_per_month",
        "product-copy": "api_requests_per_minute",
    }
    return _map.get(intent, "renders_per_month")
