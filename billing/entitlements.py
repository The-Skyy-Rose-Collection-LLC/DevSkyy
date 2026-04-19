"""
Entitlements
============

Fast feature-gating layer that combines plan limits and live quota data
to produce a single ``EntitlementResult`` for a creative operation request.

Usage::

    from billing.entitlements import EntitlementChecker

    checker = EntitlementChecker(metering)
    result = checker.check(tenant_id="t1", tier="starter", intent="virtual-tryon")
    if not result.allowed:
        raise HTTPException(402, result.reason)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from billing.metering import UsageMetering
from billing.plans import intent_allowed

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Upgrade path: which tier unlocks each intent group
# ---------------------------------------------------------------------------

_UPGRADE_MAP: dict[str, str] = {
    "3d-model": "starter",
    "social-pack": "starter",
    "scene-composite": "starter",
    "virtual-tryon": "starter",
    "moodboard": "starter",
    "rag-query": "starter",
    "rag-ingest": "starter",
    "editorial": "pro",
    "batch-render": "pro",
    "custom-training": "enterprise",
}

_DEFAULT_UPGRADE = "pro"


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EntitlementResult:
    """
    Immutable result of an entitlement check.

    Attributes:
        allowed:    Whether the operation is permitted.
        tier:       The tenant's current subscription tier.
        intent:     The requested creative intent.
        reason:     Human-readable reason when *allowed* is False.
        upgrade_to: Tier that would unlock this intent (empty if already allowed).
        remaining:  Quota remaining for this intent (-1 = unlimited, 0 = exhausted).
    """

    allowed: bool
    tier: str
    intent: str
    reason: str = ""
    upgrade_to: str = ""
    remaining: int = field(default=-1)


# ---------------------------------------------------------------------------
# Checker
# ---------------------------------------------------------------------------


class EntitlementChecker:
    """
    Evaluates whether a tenant may perform a creative operation.

    Checks in order:
    1. Is the intent allowed for the tenant's tier?
    2. Is there quota remaining this billing period?

    Args:
        metering: Optional ``UsageMetering`` instance.  When None a new
                  in-process instance is created (no Redis).
    """

    def __init__(self, metering: UsageMetering | None = None) -> None:
        self._metering = metering or UsageMetering()

    def check(self, tenant_id: str, tier: str, intent: str) -> EntitlementResult:
        """
        Evaluate entitlement for *tenant_id* requesting *intent*.

        Args:
            tenant_id: Tenant identifier.
            tier:      Subscription tier string.
            intent:    Creative intent (e.g. "virtual-tryon").

        Returns:
            EntitlementResult with allowed status and contextual metadata.
        """
        # 1. Plan-level feature gate
        if not intent_allowed(tier, intent):
            upgrade_to = _UPGRADE_MAP.get(intent, _DEFAULT_UPGRADE)
            reason = (
                f"Intent '{intent}' is not available on the '{tier}' plan. "
                f"Upgrade to {upgrade_to} to unlock this feature."
            )
            return EntitlementResult(
                allowed=False,
                tier=tier,
                intent=intent,
                reason=reason,
                upgrade_to=upgrade_to,
                remaining=0,
            )

        # 2. Quota check
        allowed, remaining = self._metering.check_quota(tenant_id, tier, intent)

        if not allowed:
            upgrade_to = _UPGRADE_MAP.get(intent, _DEFAULT_UPGRADE)
            reason = (
                f"Monthly quota for '{intent}' exhausted on the '{tier}' plan. "
                f"Upgrade to {upgrade_to} for more capacity."
            )
            return EntitlementResult(
                allowed=False,
                tier=tier,
                intent=intent,
                reason=reason,
                upgrade_to=upgrade_to,
                remaining=0,
            )

        return EntitlementResult(
            allowed=True,
            tier=tier,
            intent=intent,
            remaining=remaining,
        )

    def get_upgrade_message(self, tier: str, intent: str) -> str:
        """
        Return a friendly upgrade prompt for a blocked intent.

        Args:
            tier:   Current tier string.
            intent: Blocked creative intent.

        Returns:
            Human-readable upgrade message.
        """
        upgrade_to = _UPGRADE_MAP.get(intent, _DEFAULT_UPGRADE)
        tier_prices = {
            "starter": "$29/month",
            "pro": "$99/month",
            "enterprise": "custom pricing",
        }
        price_info = tier_prices.get(upgrade_to, "")
        price_str = f" ({price_info})" if price_info else ""
        return (
            f"'{intent}' requires the {upgrade_to.capitalize()} plan{price_str}. "
            "Visit /portal/subscriptions to upgrade and unlock this feature."
        )
