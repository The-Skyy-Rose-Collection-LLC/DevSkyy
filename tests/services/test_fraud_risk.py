"""Tests for services.risk.fraud — deterministic fraud/chargeback risk scorer.

Contract: pure, deterministic, never-raises, advisory-only. No LLM, no network.
"""

from __future__ import annotations

import dataclasses

import pytest
from services.risk.fraud import (
    FraudAssessment,
    FraudScorer,
    RiskLevel,
    RiskSignal,
    format_assessment,
)

# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


def _clean_order(**overrides) -> dict:
    """A low-risk, fully-matched domestic order."""
    order = {
        "id": 1001,
        "total": "120.00",
        "currency": "USD",
        "customer_id": 42,
        "customer_ip_address": "73.15.4.9",
        "date_created": "2026-06-20T10:00:00",
        "billing": {
            "first_name": "Corey",
            "last_name": "Foster",
            "email": "corey@example.com",
            "country": "US",
            "city": "Oakland",
            "postcode": "94601",
            "address_1": "1 Telegraph Ave",
        },
        "shipping": {
            "first_name": "Corey",
            "last_name": "Foster",
            "country": "US",
            "city": "Oakland",
            "postcode": "94601",
            "address_1": "1 Telegraph Ave",
        },
        "line_items": [{"quantity": 1, "name": "Black Rose Bomber"}],
        "payment_method": "stripe",
    }
    order.update(overrides)
    return order


# --------------------------------------------------------------------------- #
# Clean baseline
# --------------------------------------------------------------------------- #


def test_clean_order_is_low_risk_approve():
    a = FraudScorer().assess(_clean_order())
    assert isinstance(a, FraudAssessment)
    assert a.score == 0
    assert a.level is RiskLevel.LOW
    assert a.recommended_action == "approve"
    assert a.signals == ()
    assert a.order_id == "1001"


# --------------------------------------------------------------------------- #
# Individual rules each fire
# --------------------------------------------------------------------------- #


def _rules(a: FraudAssessment) -> set[str]:
    return {s.rule for s in a.signals}


def test_country_mismatch_fires():
    order = _clean_order()
    order["shipping"] = {**order["shipping"], "country": "NG"}
    a = FraudScorer().assess(order)
    assert "billing_shipping_country_mismatch" in _rules(a)
    assert a.score > 0


def test_disposable_email_fires():
    order = _clean_order()
    order["billing"] = {**order["billing"], "email": "burner@mailinator.com"}
    a = FraudScorer().assess(order)
    assert "disposable_email" in _rules(a)


def test_avs_mismatch_fires():
    a = FraudScorer().assess(_clean_order(avs_result="N"))
    assert "avs_mismatch" in _rules(a)


def test_cvv_failure_fires():
    a = FraudScorer().assess(_clean_order(cvv_result="N"))
    assert "cvv_failure" in _rules(a)


def test_avs_cvv_read_from_meta_data():
    order = _clean_order(
        meta_data=[
            {"key": "_stripe_avs_result", "value": "N"},
            {"key": "cvv_check", "value": "fail"},
        ]
    )
    a = FraudScorer().assess(order)
    assert "avs_mismatch" in _rules(a)
    assert "cvv_failure" in _rules(a)


def test_high_value_order_fires():
    a = FraudScorer(high_value_threshold=100.0).assess(_clean_order(total="900.00"))
    assert "high_value_order" in _rules(a)


def test_guest_high_value_fires():
    order = _clean_order(customer_id=0, total="400.00")
    a = FraudScorer(mid_value_threshold=250.0).assess(order)
    assert "guest_high_value" in _rules(a)


def test_billing_name_mismatch_fires():
    order = _clean_order()
    order["shipping"] = {**order["shipping"], "first_name": "Someone", "last_name": "Else"}
    a = FraudScorer().assess(order)
    assert "mismatched_recipient_name" in _rules(a)


def test_velocity_email_fires_from_history():
    order = _clean_order()
    email = order["billing"]["email"]
    history = [
        {"billing": {"email": email}, "date_created": "2026-06-20T09:30:00"},
        {"billing": {"email": email}, "date_created": "2026-06-20T08:00:00"},
        {"billing": {"email": email}, "date_created": "2026-06-20T07:00:00"},
    ]
    a = FraudScorer(velocity_count=3).assess(order, history=history)
    assert "velocity_email" in _rules(a)


def test_velocity_ip_fires_from_history():
    order = _clean_order()
    ip = order["customer_ip_address"]
    history = [
        {"customer_ip_address": ip, "date_created": "2026-06-20T09:30:00"},
        {"customer_ip_address": ip, "date_created": "2026-06-20T08:00:00"},
        {"customer_ip_address": ip, "date_created": "2026-06-20T07:00:00"},
    ]
    a = FraudScorer(velocity_count=3).assess(order, history=history)
    assert "velocity_ip" in _rules(a)


def test_email_gibberish_fires():
    order = _clean_order()
    # 8-char local part, mostly digits → machine-generated heuristic.
    order["billing"] = {**order["billing"], "email": "8829471x@example.com"}
    a = FraudScorer().assess(order)
    assert "email_gibberish" in _rules(a)


def test_address_mismatch_same_country_fires():
    order = _clean_order()
    order["shipping"] = {
        **order["shipping"],
        "address_1": "999 Somewhere Else Blvd",
        "postcode": "10001",
        "city": "New York",
    }
    a = FraudScorer().assess(order)
    assert "address_mismatch" in _rules(a)
    assert "billing_shipping_country_mismatch" not in _rules(a)  # same country


def test_numeric_total_accepted():
    a = FraudScorer(high_value_threshold=100.0).assess(_clean_order(total=900.0))
    assert "high_value_order" in _rules(a)


def test_velocity_ignores_orders_outside_window():
    order = _clean_order()
    email = order["billing"]["email"]
    # All three are >24h before the order → must NOT trip a 24h window.
    history = [
        {"billing": {"email": email}, "date_created": "2026-06-18T09:30:00"},
        {"billing": {"email": email}, "date_created": "2026-06-17T08:00:00"},
        {"billing": {"email": email}, "date_created": "2026-06-16T07:00:00"},
    ]
    a = FraudScorer(velocity_count=3, velocity_window_hours=24).assess(order, history=history)
    assert "velocity_email" not in _rules(a)


# --------------------------------------------------------------------------- #
# Score / level / action mapping
# --------------------------------------------------------------------------- #


def test_score_is_clamped_to_100():
    order = _clean_order(customer_id=0, total="5000.00", avs_result="N", cvv_result="N")
    order["billing"] = {**order["billing"], "email": "x@guerrillamail.com"}
    order["shipping"] = {**order["shipping"], "country": "NG", "first_name": "Z", "last_name": "Q"}
    a = FraudScorer(high_value_threshold=100.0, mid_value_threshold=100.0).assess(order)
    assert a.score == 100
    assert a.level is RiskLevel.CRITICAL
    assert a.recommended_action == "hold"


@pytest.mark.parametrize(
    "score,level,action",
    [
        (0, RiskLevel.LOW, "approve"),
        (19, RiskLevel.LOW, "approve"),
        (20, RiskLevel.MEDIUM, "approve"),
        (49, RiskLevel.MEDIUM, "approve"),
        (50, RiskLevel.HIGH, "review"),
        (79, RiskLevel.HIGH, "review"),
        (80, RiskLevel.CRITICAL, "hold"),
        (100, RiskLevel.CRITICAL, "hold"),
    ],
)
def test_level_and_action_thresholds(score, level, action):
    assert FraudScorer.level_for(score) is level
    assert FraudScorer.action_for(level) == action


# --------------------------------------------------------------------------- #
# Robustness — never raises
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "bad",
    [
        {},
        {"billing": None, "shipping": None},
        {"total": "not-a-number"},
        {"total": None},
        {"billing": {"email": None}},
        {"date_created": "garbage"},
        {"line_items": "nope"},
        {"meta_data": "nope"},
    ],
)
def test_never_raises_on_garbage(bad):
    a = FraudScorer().assess(bad)  # must not raise
    assert isinstance(a, FraudAssessment)
    assert 0 <= a.score <= 100


def test_none_order_does_not_raise():
    a = FraudScorer().assess(None)  # type: ignore[arg-type]
    assert isinstance(a, FraudAssessment)
    assert a.score == 0


def test_none_history_is_fine():
    a = FraudScorer().assess(_clean_order(), history=None)
    assert a.signals == ()


# --------------------------------------------------------------------------- #
# Determinism + immutability
# --------------------------------------------------------------------------- #


def test_deterministic_same_input_same_output():
    order = _clean_order(total="900.00", avs_result="N")
    a1 = FraudScorer(high_value_threshold=100.0).assess(order)
    a2 = FraudScorer(high_value_threshold=100.0).assess(order)
    assert a1 == a2


def test_assessment_is_frozen():
    a = FraudScorer().assess(_clean_order())
    with pytest.raises(dataclasses.FrozenInstanceError):
        a.score = 99  # type: ignore[misc]


def test_signal_is_frozen():
    s = RiskSignal(rule="x", weight=1, detail="d")
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.weight = 2  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# Tunability
# --------------------------------------------------------------------------- #


def test_threshold_tunable_changes_outcome():
    order = _clean_order(total="300.00")
    assert "high_value_order" not in _rules(FraudScorer(high_value_threshold=500.0).assess(order))
    assert "high_value_order" in _rules(FraudScorer(high_value_threshold=200.0).assess(order))


def test_custom_disposable_domain():
    order = _clean_order()
    order["billing"] = {**order["billing"], "email": "a@evil.test"}
    scorer = FraudScorer(extra_disposable_domains=("evil.test",))
    assert "disposable_email" in _rules(scorer.assess(order))


# --------------------------------------------------------------------------- #
# Serialization / reporting
# --------------------------------------------------------------------------- #


def test_as_dict_is_json_safe():
    import json

    a = FraudScorer(high_value_threshold=100.0).assess(_clean_order(total="900.00"))
    payload = a.as_dict()
    json.dumps(payload)  # must not raise
    assert payload["score"] == a.score
    assert payload["level"] == a.level.name
    assert payload["recommended_action"] == a.recommended_action
    assert isinstance(payload["signals"], list)


def test_format_assessment_renders_markdown():
    a = FraudScorer(high_value_threshold=100.0).assess(_clean_order(total="900.00"))
    text = format_assessment(a)
    assert isinstance(text, str)
    assert "Fraud Risk" in text
    assert str(a.score) in text


def test_format_assessment_no_signals():
    a = FraudScorer().assess(_clean_order())
    text = format_assessment(a)
    assert "No risk signals" in text


# --------------------------------------------------------------------------- #
# Regression tests for the adversarial-review fixes
# --------------------------------------------------------------------------- #


def test_benign_international_gift_not_held():
    """A legit first-time guest sending a $500+ gift abroad must NOT be flagged to review.

    Country mismatch (15) + recipient-name mismatch (10) + high value (10) + guest high
    value (10) = 45 → MEDIUM/approve. Calibrated so only a gateway signal escalates.
    """
    order = _clean_order(customer_id=0, total="600.00")
    order["shipping"] = {
        **order["shipping"],
        "country": "GB",
        "first_name": "Gift",
        "last_name": "Recipient",
    }
    a = FraudScorer().assess(order)
    assert a.score == 45
    assert a.level is RiskLevel.MEDIUM
    assert a.recommended_action == "approve"


def test_gateway_signal_still_escalates_international():
    """But the same order with an AVS failure must escalate to review."""
    order = _clean_order(customer_id=0, total="600.00", avs_result="N")
    order["shipping"] = {**order["shipping"], "country": "GB"}
    a = FraudScorer().assess(order)
    assert a.recommended_action in ("review", "hold")


def test_bad_weight_value_does_not_raise():
    order = _clean_order(cvv_result="N")
    a = FraudScorer(weights={"cvv_failure": "thirty-five"}).assess(order)  # type: ignore[dict-item]
    assert isinstance(a, FraudAssessment)
    assert 0 <= a.score <= 100


def test_naive_aware_velocity_still_fires():
    order = _clean_order(date_created="2026-06-20T10:00:00+00:00")  # aware
    email = order["billing"]["email"]
    history = [  # naive timestamps (no offset) — must still count
        {"billing": {"email": email}, "date_created": "2026-06-20T09:30:00"},
        {"billing": {"email": email}, "date_created": "2026-06-20T08:00:00"},
        {"billing": {"email": email}, "date_created": "2026-06-20T07:00:00"},
    ]
    a = FraudScorer(velocity_count=3).assess(order, history=history)
    assert "velocity_email" in _rules(a)


def test_velocity_detail_masks_pii():
    order = _clean_order()
    email = order["billing"]["email"]
    history = [
        {"billing": {"email": email}, "date_created": "2026-06-20T09:30:00"},
        {"billing": {"email": email}, "date_created": "2026-06-20T08:00:00"},
        {"billing": {"email": email}, "date_created": "2026-06-20T07:00:00"},
    ]
    a = FraudScorer(velocity_count=3).assess(order, history=history)
    detail = next(s.detail for s in a.signals if s.rule == "velocity_email")
    assert email not in detail  # raw email must not leak
    assert "***@" in detail


def test_current_order_not_counted_in_velocity():
    order = _clean_order()  # id=1001
    email = order["billing"]["email"]
    # Two genuine priors + the current order echoed back in history → must count 2, not 3.
    history = [
        {"id": 1001, "billing": {"email": email}, "date_created": "2026-06-20T09:59:00"},
        {"billing": {"email": email}, "date_created": "2026-06-20T09:30:00"},
        {"billing": {"email": email}, "date_created": "2026-06-20T08:00:00"},
    ]
    a = FraudScorer(velocity_count=3).assess(order, history=history)
    assert "velocity_email" not in _rules(a)  # only 2 eligible priors


def test_nan_total_treated_as_unknown():
    a = FraudScorer(high_value_threshold=1.0).assess(_clean_order(total=float("nan")))
    assert "high_value_order" not in _rules(a)
    assert 0 <= a.score <= 100


def test_markdown_cells_escape_pipes():
    order = _clean_order()
    order["shipping"] = {**order["shipping"], "country": "N|G"}  # pipe in a field
    a = FraudScorer().assess(order)
    text = format_assessment(a)
    # No raw unescaped pipe from the country value should break the table.
    assert "N\\|G" in text


def test_package_reexports_importable():
    from services.risk import FraudAssessment as A
    from services.risk import FraudScorer as S
    from services.risk import RiskLevel as L
    from services.risk import RiskSignal as Sig
    from services.risk import format_assessment as f

    assert all(x is not None for x in (A, S, L, Sig, f))
