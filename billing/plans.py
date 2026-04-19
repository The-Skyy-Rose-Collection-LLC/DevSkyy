"""
Billing Plans — Tier Limits & Feature Gates
============================================

Defines the SkyyRose SaaS tier structure as frozen dataclasses.
All data is immutable at runtime; no mutation is permitted.

Tiers:
- free       — 10 renders / month
- starter    — $29/mo, 100 renders
- pro        — $99/mo, 1000 renders, all intents
- enterprise — unlimited, all intents

Usage::

    from billing.plans import get_limits, intent_allowed, quota_remaining

    limits = get_limits("starter")
    if intent_allowed("starter", "virtual-tryon"):
        remaining = quota_remaining("starter", "product-render", used=42)
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# TierLimits
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TierLimits:
    """
    Immutable limits for a subscription tier.

    All ``*_per_month`` fields use -1 to indicate unlimited.
    ``allowed_intents`` contains ``frozenset(["*"])`` when all intents are allowed.
    """

    renders_per_month: int  # -1 = unlimited
    models_3d_per_month: int
    social_packs_per_month: int
    characters: int
    api_requests_per_minute: int
    storage_gb: int
    allowed_intents: frozenset[str]  # frozenset(["*"]) = all intents allowed
    rag_queries_per_month: int = 0  # multimodal knowledge-base queries; -1 = unlimited
    rag_ingest_per_month: int = 0  # documents ingested per month; -1 = unlimited


# ---------------------------------------------------------------------------
# Canonical intent names
# ---------------------------------------------------------------------------

_ALL_INTENTS: frozenset[str] = frozenset(["*"])

_STARTER_INTENTS: frozenset[str] = frozenset(
    {
        "product-render",
        "product-copy",
        "social-pack",
        "scene-composite",
        "virtual-tryon",
        "moodboard",
        "rag-query",
        "rag-ingest",
    }
)

_FREE_INTENTS: frozenset[str] = frozenset({"product-render", "product-copy"})

# ---------------------------------------------------------------------------
# Tier catalogue
# ---------------------------------------------------------------------------

TIER_LIMITS: dict[str, TierLimits] = {
    "free": TierLimits(
        renders_per_month=10,
        models_3d_per_month=2,
        social_packs_per_month=5,
        characters=1,
        api_requests_per_minute=10,
        storage_gb=1,
        allowed_intents=_FREE_INTENTS,
        rag_queries_per_month=0,
        rag_ingest_per_month=0,
    ),
    "starter": TierLimits(
        renders_per_month=100,
        models_3d_per_month=20,
        social_packs_per_month=50,
        characters=5,
        api_requests_per_minute=60,
        storage_gb=10,
        allowed_intents=_STARTER_INTENTS,
        rag_queries_per_month=200,
        rag_ingest_per_month=20,
    ),
    "pro": TierLimits(
        renders_per_month=1000,
        models_3d_per_month=200,
        social_packs_per_month=500,
        characters=25,
        api_requests_per_minute=300,
        storage_gb=100,
        allowed_intents=_ALL_INTENTS,
        rag_queries_per_month=2000,
        rag_ingest_per_month=200,
    ),
    "enterprise": TierLimits(
        renders_per_month=-1,
        models_3d_per_month=-1,
        social_packs_per_month=-1,
        characters=-1,
        api_requests_per_minute=1000,
        storage_gb=1000,
        allowed_intents=_ALL_INTENTS,
        rag_queries_per_month=-1,
        rag_ingest_per_month=-1,
    ),
}

# ---------------------------------------------------------------------------
# Intent → quota field mapping
# ---------------------------------------------------------------------------

_INTENT_QUOTA_MAP: dict[str, str] = {
    "product-render": "renders_per_month",
    "scene-composite": "renders_per_month",
    "virtual-tryon": "renders_per_month",
    "moodboard": "renders_per_month",
    "3d-model": "models_3d_per_month",
    "social-pack": "social_packs_per_month",
    "product-copy": "api_requests_per_minute",  # text-only; track against API requests
    "rag-query": "rag_queries_per_month",
    "rag-ingest": "rag_ingest_per_month",
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def get_limits(tier: str) -> TierLimits:
    """
    Return the TierLimits for *tier*, defaulting to ``free`` if unknown.

    Args:
        tier: Tier name string (e.g. "pro").

    Returns:
        Corresponding TierLimits (frozen dataclass).
    """
    return TIER_LIMITS.get(tier, TIER_LIMITS["free"])


def intent_allowed(tier: str, intent: str) -> bool:
    """
    Check whether *intent* is permitted for *tier*.

    ``frozenset(["*"])`` in allowed_intents means all intents are allowed.

    Args:
        tier:   Subscription tier string.
        intent: Creative intent identifier (e.g. "virtual-tryon").

    Returns:
        True if the intent is allowed for this tier.
    """
    limits = get_limits(tier)
    if "*" in limits.allowed_intents:
        return True
    return intent in limits.allowed_intents


def quota_remaining(tier: str, intent: str, used: int) -> int:
    """
    Calculate how many units remain for *intent* this billing period.

    Args:
        tier:   Subscription tier string.
        intent: Creative intent identifier.
        used:   Units already consumed this period.

    Returns:
        Remaining units, or -1 if the quota is unlimited.
    """
    limits = get_limits(tier)
    quota_field = _INTENT_QUOTA_MAP.get(intent, "renders_per_month")
    quota_total: int = getattr(limits, quota_field, -1)

    if quota_total == -1:
        return -1

    remaining = quota_total - used
    return max(0, remaining)
