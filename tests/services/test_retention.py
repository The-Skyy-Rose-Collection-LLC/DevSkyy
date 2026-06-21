"""Tests for services.lifecycle.retention — deterministic RFM + lifecycle scorer.

Contract: deterministic given ``as_of``, never-raises, advisory-only (suggests a Klaviyo
segment/flow; never sends).
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest
from services.lifecycle.retention import (
    LifecycleStage,
    RetentionAssessment,
    RetentionScorer,
    format_assessment,
)

AS_OF = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)


def _cust(orders=None, **fields):
    c = {"id": 7, "email": "buyer@example.com"}
    if orders is not None:
        c["orders"] = orders
    c.update(fields)
    return c


def _orders(*dates_and_totals):
    return [{"date_created": d, "total": t} for d, t in dates_and_totals]


# --------------------------------------------------------------------------- #
# Lifecycle stages
# --------------------------------------------------------------------------- #


def test_new_customer_single_recent_order():
    a = RetentionScorer().assess(_cust(_orders(("2026-06-15T10:00:00", "120.00"))), as_of=AS_OF)
    assert isinstance(a, RetentionAssessment)
    assert a.lifecycle_stage is LifecycleStage.NEW
    assert a.frequency == 1
    assert a.recency_days == 5
    assert a.churn_risk < 30


def test_active_customer_repeat_recent():
    orders = _orders(
        ("2026-06-10T10:00:00", "120.00"),
        ("2026-05-20T10:00:00", "90.00"),
        ("2026-05-01T10:00:00", "150.00"),
    )
    a = RetentionScorer().assess(_cust(orders), as_of=AS_OF)
    assert a.lifecycle_stage is LifecycleStage.ACTIVE
    assert a.frequency == 3


def test_loyal_customer_high_frequency_and_spend():
    orders = _orders(*[(f"2026-06-{d:02d}T10:00:00", "300.00") for d in range(1, 13)])
    a = RetentionScorer().assess(_cust(orders), as_of=AS_OF)
    assert a.lifecycle_stage is LifecycleStage.LOYAL
    assert a.rfm == "5-5-5"  # most recent, most frequent, top spend


def test_at_risk_customer():
    a = RetentionScorer().assess(_cust(_orders(("2026-03-01T10:00:00", "120.00"))), as_of=AS_OF)
    assert a.lifecycle_stage is LifecycleStage.AT_RISK


def test_dormant_customer():
    a = RetentionScorer().assess(_cust(_orders(("2025-12-15T10:00:00", "120.00"))), as_of=AS_OF)
    assert a.lifecycle_stage is LifecycleStage.DORMANT


def test_churned_customer_high_churn_risk():
    a = RetentionScorer().assess(_cust(_orders(("2025-04-01T10:00:00", "120.00"))), as_of=AS_OF)
    assert a.lifecycle_stage is LifecycleStage.CHURNED
    assert a.churn_risk >= 80


def test_zero_orders_is_new_no_recency():
    a = RetentionScorer().assess(_cust([]), as_of=AS_OF)
    assert a.lifecycle_stage is LifecycleStage.NEW
    assert a.recency_days is None
    assert a.frequency == 0
    assert a.monetary == 0.0
    assert a.churn_risk == 0


# --------------------------------------------------------------------------- #
# RFM computation
# --------------------------------------------------------------------------- #


def test_rfm_from_orders_list():
    orders = _orders(
        ("2026-06-18T10:00:00", "600.00"),
        ("2026-06-01T10:00:00", "600.00"),
        ("2026-05-15T10:00:00", "600.00"),
    )
    a = RetentionScorer().assess(_cust(orders), as_of=AS_OF)
    # recency 2d -> 5, freq 3 -> 3, monetary 1800 -> 5
    assert a.rfm == "5-3-5"
    assert a.monetary == 1800.0


def test_precomputed_fields_used_when_no_orders():
    cust = _cust(last_order_date="2026-06-15T00:00:00", order_count=4, total_spent=520.0)
    a = RetentionScorer().assess(cust, as_of=AS_OF)
    assert a.frequency == 4
    assert a.monetary == 520.0
    assert a.recency_days == 5


# --------------------------------------------------------------------------- #
# Action + Klaviyo segment (advisory only)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "stage",
    list(LifecycleStage),
)
def test_every_stage_has_action_and_segment(stage):
    assert RetentionScorer.action_for(stage)
    seg = RetentionScorer.klaviyo_segment_for(stage)
    assert isinstance(seg, str) and seg


def test_churned_recommends_winback():
    a = RetentionScorer().assess(_cust(_orders(("2025-04-01T10:00:00", "120.00"))), as_of=AS_OF)
    assert "winback" in a.recommended_action


# --------------------------------------------------------------------------- #
# Robustness — never raises
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "bad",
    [
        {},
        {"orders": None},
        {"orders": "nope"},
        {"orders": [None, "x", {"date_created": "garbage", "total": "x"}]},
        {"last_order_date": "garbage", "order_count": "x", "total_spent": None},
        {"orders": [{"total": "120.00"}]},  # order with no date
    ],
)
def test_never_raises_on_garbage(bad):
    a = RetentionScorer().assess(bad, as_of=AS_OF)
    assert isinstance(a, RetentionAssessment)
    assert 0 <= a.churn_risk <= 100


def test_none_customer_does_not_raise():
    a = RetentionScorer().assess(None, as_of=AS_OF)  # type: ignore[arg-type]
    assert a.lifecycle_stage is LifecycleStage.NEW
    assert a.churn_risk == 0


def test_default_as_of_does_not_raise():
    a = RetentionScorer().assess(_cust(_orders(("2026-06-15T10:00:00", "120.00"))))
    assert isinstance(a, RetentionAssessment)


# --------------------------------------------------------------------------- #
# Determinism + immutability + serialization
# --------------------------------------------------------------------------- #


def test_deterministic():
    cust = _cust(_orders(("2026-05-01T10:00:00", "300.00"), ("2026-04-01T10:00:00", "300.00")))
    assert RetentionScorer().assess(cust, as_of=AS_OF) == RetentionScorer().assess(
        cust, as_of=AS_OF
    )


def test_frozen():
    a = RetentionScorer().assess(_cust([]), as_of=AS_OF)
    with pytest.raises(dataclasses.FrozenInstanceError):
        a.churn_risk = 50  # type: ignore[misc]


def test_as_dict_json_safe():
    import json

    a = RetentionScorer().assess(_cust(_orders(("2026-03-01T10:00:00", "120.00"))), as_of=AS_OF)
    payload = a.as_dict()
    json.dumps(payload)
    assert payload["lifecycle_stage"] == a.lifecycle_stage.name
    assert payload["rfm"] == a.rfm
    assert payload["recommended_action"] == a.recommended_action
    assert payload["suggested_klaviyo_segment"]


# --------------------------------------------------------------------------- #
# Tunability
# --------------------------------------------------------------------------- #


def test_churned_window_tunable():
    cust = _cust(_orders(("2026-01-01T10:00:00", "120.00")))  # ~170 days before AS_OF
    assert RetentionScorer(churned_days=150).assess(cust, as_of=AS_OF).lifecycle_stage is (
        LifecycleStage.CHURNED
    )
    assert RetentionScorer(churned_days=400).assess(cust, as_of=AS_OF).lifecycle_stage is not (
        LifecycleStage.CHURNED
    )


def test_format_renders_markdown():
    a = RetentionScorer().assess(_cust(_orders(("2026-03-01T10:00:00", "120.00"))), as_of=AS_OF)
    text = format_assessment(a)
    assert "Retention" in text
    assert a.lifecycle_stage.name in text


# --------------------------------------------------------------------------- #
# Regression: adversarial-review fixes
# --------------------------------------------------------------------------- #


def test_loyal_buyer_in_drop_gap_stays_loyal():
    """A 5-order buyer whose last order was 96d ago (normal inter-drop gap) is LOYAL,
    not AT_RISK — the recency gate must not pre-empt the loyalty check."""
    orders = [
        {"date_created": f"2026-0{m}-15T10:00:00", "total": "300.00"} for m in (1, 2, 3)
    ] + _orders(("2026-03-16T10:00:00", "300.00"), ("2026-03-17T10:00:00", "300.00"))
    a = RetentionScorer().assess(_cust(orders), as_of=AS_OF)  # last order 2026-03-17 ≈ 95d
    assert a.frequency == 5
    assert a.recency_days > 90
    assert a.lifecycle_stage is LifecycleStage.LOYAL
    assert a.recommended_action == "vip_reward"


def test_loyal_buyer_past_dormant_window_degrades():
    orders = [{"date_created": "2025-12-01T10:00:00", "total": "300.00"} for _ in range(5)]
    a = RetentionScorer().assess(_cust(orders), as_of=AS_OF)  # ~201d > dormant_days
    assert a.frequency == 5
    assert a.lifecycle_stage is LifecycleStage.DORMANT


def test_new_with_last_order_but_no_count_has_zero_churn():
    # Precomputed path with last_order_date but no order_count → NEW with no contradictory churn.
    a = RetentionScorer().assess(_cust(last_order_date="2025-01-01T00:00:00"), as_of=AS_OF)
    assert a.frequency == 0
    assert a.lifecycle_stage is LifecycleStage.NEW
    assert a.churn_risk == 0


def test_parse_dt_accepts_datetime_objects():
    orders = [{"date_created": datetime(2026, 6, 15, tzinfo=UTC), "total": 120.0}]
    a = RetentionScorer().assess(_cust(orders), as_of=AS_OF)
    assert a.recency_days == 5
    assert a.frequency == 1
