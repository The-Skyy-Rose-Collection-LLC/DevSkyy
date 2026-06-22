"""Deterministic customer-lifecycle / retention scorer (advisory only).

Closes agent gap #5 (Customer Lifecycle / Retention), which was fragmented across thin
LLM wrappers: ``agents/claude_sdk/domain_agents/customer_intelligence.py`` (``churn_predict``
capability string), ``community.py`` (retention/win-back prose), ``analytics_agent`` segment
stub, and an ``mcp_tools/tools/advanced.py`` re-engagement workflow. None computed anything.

This is the missing deterministic core they can all call. It scores a customer with the
canonical **RFM** model (Recency, Frequency, Monetary), assigns a lifecycle stage, computes a
churn-risk score, and recommends a next action + a Klaviyo segment to enroll into.

Design (mirrors ``services/risk/fraud.py`` and ``monitoring/fleet_observer.py``):
- **Deterministic** given ``as_of`` (defaults to now only when the caller omits it).
- **Never raises.** Every field read is defensive; a malformed customer yields a safe
  ``NEW`` / ``churn_risk == 0`` assessment.
- **Advisory.** It returns a *suggested* Klaviyo segment/flow name. It NEVER calls the Klaviyo
  API or enrolls anyone — a human (or a STOP-AND-SHOW gated action) does the actual send.
- **Founder-tunable.** Every window and threshold is a constructor argument.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

# --------------------------------------------------------------------------- #
# Public types
# --------------------------------------------------------------------------- #


class LifecycleStage(StrEnum):
    """Where a customer sits in their relationship with the brand."""

    NEW = "new"
    ACTIVE = "active"
    LOYAL = "loyal"
    AT_RISK = "at_risk"
    DORMANT = "dormant"
    CHURNED = "churned"


@dataclass(frozen=True)
class RetentionAssessment:
    """RFM + lifecycle verdict for one customer. Immutable, JSON-serializable."""

    customer_id: str | None
    recency_days: int | None  # None when the customer has never ordered
    frequency: int
    monetary: float
    rfm: str  # "R-F-M", each 1-5, e.g. "5-3-4"
    lifecycle_stage: LifecycleStage
    churn_risk: int  # 0-100
    recommended_action: str
    suggested_klaviyo_segment: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "recency_days": self.recency_days,
            "frequency": self.frequency,
            "monetary": self.monetary,
            "rfm": self.rfm,
            "lifecycle_stage": self.lifecycle_stage.name,
            "churn_risk": self.churn_risk,
            "recommended_action": self.recommended_action,
            "suggested_klaviyo_segment": self.suggested_klaviyo_segment,
        }


# --------------------------------------------------------------------------- #
# Defaults (founder-tunable via the constructor)
# --------------------------------------------------------------------------- #

# Recency days -> R score. Each tuple is (max_days_inclusive, score). First match wins.
_RECENCY_BANDS: tuple[tuple[int, int], ...] = ((30, 5), (60, 4), (120, 3), (240, 2))
# Frequency (order count) -> F score. (min_orders_inclusive, score). First match wins.
_FREQUENCY_BANDS: tuple[tuple[int, int], ...] = ((10, 5), (6, 4), (3, 3), (2, 2))
# Monetary (total spent) -> M score. (min_spend_inclusive, score). First match wins.
_MONETARY_BANDS: tuple[tuple[float, int], ...] = ((1000.0, 5), (500.0, 4), (250.0, 3), (100.0, 2))

_ACTION_BY_STAGE: dict[LifecycleStage, str] = {
    LifecycleStage.NEW: "welcome_nurture",
    LifecycleStage.ACTIVE: "cross_sell",
    LifecycleStage.LOYAL: "vip_reward",
    LifecycleStage.AT_RISK: "reengagement_offer",
    LifecycleStage.DORMANT: "winback_offer",
    LifecycleStage.CHURNED: "winback_last_attempt",
}

_KLAVIYO_SEGMENT_BY_STAGE: dict[LifecycleStage, str] = {
    LifecycleStage.NEW: "New / Welcome",
    LifecycleStage.ACTIVE: "Active Buyers",
    LifecycleStage.LOYAL: "VIP / Loyal",
    LifecycleStage.AT_RISK: "At-Risk (re-engage)",
    LifecycleStage.DORMANT: "Dormant (win-back)",
    LifecycleStage.CHURNED: "Churned (last-touch)",
}


# --------------------------------------------------------------------------- #
# Defensive helpers (never raise)
# --------------------------------------------------------------------------- #


def _to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        result = float(value)
    elif isinstance(value, str):
        try:
            result = float(value.strip())
        except (ValueError, AttributeError):
            return None
    else:
        return None
    return result if math.isfinite(result) else None


def _parse_dt(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if not isinstance(value, str):
        return None
    raw = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _band(value: float, bands: tuple[tuple[float, int], ...], *, ascending: bool) -> int:
    """Map a value to a 1-5 score. ``ascending`` bands are 'value >= edge'; otherwise '<='."""
    for edge, score in bands:
        if (value >= edge) if ascending else (value <= edge):
            return score
    return 1


# --------------------------------------------------------------------------- #
# Scorer
# --------------------------------------------------------------------------- #


class RetentionScorer:
    """Score a customer's RFM, lifecycle stage, and churn risk (read-only, advisory)."""

    def __init__(
        self,
        *,
        at_risk_days: int = 90,
        dormant_days: int = 180,
        churned_days: int = 365,
        loyal_min_orders: int = 4,
        loyalty_weight: int = 4,  # churn-risk discount per repeat order (capped at 5 orders)
    ) -> None:
        self.at_risk_days = at_risk_days
        self.dormant_days = dormant_days
        self.churned_days = churned_days
        self.loyal_min_orders = loyal_min_orders
        self.loyalty_weight = loyalty_weight

    # -- pure mappings ----------------------------------------------------- #

    @staticmethod
    def action_for(stage: LifecycleStage) -> str:
        return _ACTION_BY_STAGE.get(stage, "reengagement_offer")

    @staticmethod
    def klaviyo_segment_for(stage: LifecycleStage) -> str:
        return _KLAVIYO_SEGMENT_BY_STAGE.get(stage, "At-Risk (re-engage)")

    # -- entry point ------------------------------------------------------- #

    def assess(
        self, customer: dict[str, Any], *, as_of: datetime | None = None
    ) -> RetentionAssessment:
        """Return a :class:`RetentionAssessment` for ``customer``. Never raises."""
        now = as_of or datetime.now(UTC)
        if not isinstance(customer, dict):
            return self._empty(None)

        cid = customer.get("id")
        cid_str = str(cid) if cid is not None else None

        try:
            recency_days, frequency, monetary = self._rfm_inputs(customer, now)
        except Exception:  # defense-in-depth — never break a marketing batch
            return self._empty(cid_str)

        r_score = (
            _band(recency_days, _RECENCY_BANDS, ascending=False) if recency_days is not None else 1
        )
        f_score = _band(float(frequency), _FREQUENCY_BANDS, ascending=True)
        m_score = _band(monetary, _MONETARY_BANDS, ascending=True)
        rfm = f"{r_score}-{f_score}-{m_score}"

        stage = self._stage(frequency, recency_days)
        churn = self._churn_risk(recency_days, frequency)

        return RetentionAssessment(
            customer_id=cid_str,
            recency_days=recency_days,
            frequency=frequency,
            monetary=round(monetary, 2),
            rfm=rfm,
            lifecycle_stage=stage,
            churn_risk=churn,
            recommended_action=self.action_for(stage),
            suggested_klaviyo_segment=self.klaviyo_segment_for(stage),
        )

    def _empty(self, cid: str | None) -> RetentionAssessment:
        return RetentionAssessment(
            customer_id=cid,
            recency_days=None,
            frequency=0,
            monetary=0.0,
            rfm="1-1-1",
            lifecycle_stage=LifecycleStage.NEW,
            churn_risk=0,
            recommended_action=self.action_for(LifecycleStage.NEW),
            suggested_klaviyo_segment=self.klaviyo_segment_for(LifecycleStage.NEW),
        )

    # -- RFM extraction ---------------------------------------------------- #

    def _rfm_inputs(self, customer: dict, now: datetime) -> tuple[int | None, int, float]:
        """Return (recency_days, frequency, monetary) from an orders list or precomputed fields."""
        orders = customer.get("orders")
        if isinstance(orders, list):
            dicts = [o for o in orders if isinstance(o, dict)]
            frequency = len(dicts)
            monetary = sum(v for v in (_to_float(o.get("total")) for o in dicts) if v is not None)
            dates = [d for d in (_parse_dt(o.get("date_created")) for o in dicts) if d is not None]
            recency = self._recency(max(dates), now) if dates else None
            return recency, frequency, monetary

        # Precomputed-field fallback.
        frequency = int(_to_float(customer.get("order_count")) or 0)
        monetary = _to_float(customer.get("total_spent")) or 0.0
        last = _parse_dt(customer.get("last_order_date"))
        recency = self._recency(last, now) if last else None
        return recency, frequency, monetary

    @staticmethod
    def _recency(last: datetime, now: datetime) -> int:
        # Day-granularity diff via .date() avoids naive/aware subtraction errors.
        return max(0, (now.date() - last.date()).days)

    # -- stage + churn ----------------------------------------------------- #

    def _stage(self, frequency: int, recency_days: int | None) -> LifecycleStage:
        if frequency <= 0 or recency_days is None:
            return LifecycleStage.NEW
        if recency_days > self.churned_days:
            return LifecycleStage.CHURNED
        if recency_days > self.dormant_days:
            return LifecycleStage.DORMANT
        # Loyalty protects against the at-risk gate through the normal inter-drop window:
        # a repeat buyer (>= loyal_min_orders) in a 91-180d quiet period between drops is
        # LOYAL, not AT_RISK. churn_risk still rises with recency as the secondary signal.
        if frequency >= self.loyal_min_orders:
            return LifecycleStage.LOYAL
        if recency_days > self.at_risk_days:
            return LifecycleStage.AT_RISK
        if frequency >= 2:
            return LifecycleStage.ACTIVE
        return LifecycleStage.NEW

    def _churn_risk(self, recency_days: int | None, frequency: int) -> int:
        if recency_days is None or self.churned_days <= 0 or frequency <= 0:
            return 0
        ratio = min(recency_days / self.churned_days, 1.0)
        base = round(100 * ratio)
        discount = min(frequency, 5) * self.loyalty_weight
        return max(0, min(100, base - discount))


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #


def format_assessment(assessment: RetentionAssessment) -> str:
    """Render a :class:`RetentionAssessment` as a markdown summary."""
    recency = "never" if assessment.recency_days is None else f"{assessment.recency_days}d ago"
    return "\n".join(
        [
            f"## Retention — customer {assessment.customer_id or 'n/a'}",
            f"Stage: **{assessment.lifecycle_stage.name}** | Churn risk: "
            f"**{assessment.churn_risk}/100** | RFM: **{assessment.rfm}**",
            f"Last order: {recency} | Orders: {assessment.frequency} | "
            f"Spent: ${assessment.monetary:.2f}",
            f"Action: **{assessment.recommended_action}** | Klaviyo segment: "
            f"**{assessment.suggested_klaviyo_segment}**",
        ]
    )


__all__ = [
    "LifecycleStage",
    "RetentionAssessment",
    "RetentionScorer",
    "format_assessment",
]
