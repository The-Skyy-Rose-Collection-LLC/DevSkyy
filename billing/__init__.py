"""
Billing Package
===============

Multi-tier SaaS billing for the DevSkyy / SkyyRose platform.

Tiers:
- free      — 10 renders / month, limited intents
- starter   — $29/mo, 100 renders, most intents
- pro       — $99/mo, 1000 renders, all intents
- enterprise — custom pricing, unlimited

Public API:
    from billing import (
        TIER_LIMITS,
        get_limits,
        intent_allowed,
        quota_remaining,
        UsageMetering,
        EntitlementChecker,
        EntitlementResult,
        StripeClient,
        handle_stripe_webhook,
    )
"""

from .entitlements import EntitlementChecker, EntitlementResult
from .metering import UsageMetering
from .plans import TIER_LIMITS, TierLimits, get_limits, intent_allowed, quota_remaining
from .stripe_client import StripeClient
from .webhooks import handle_stripe_webhook

__all__ = [
    "TIER_LIMITS",
    "TierLimits",
    "get_limits",
    "intent_allowed",
    "quota_remaining",
    "UsageMetering",
    "EntitlementChecker",
    "EntitlementResult",
    "StripeClient",
    "handle_stripe_webhook",
]
