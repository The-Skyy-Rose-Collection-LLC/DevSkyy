import dataclasses

import pytest

from evaluation.contracts import Severity, Verdict


def _make(**overrides) -> Verdict:
    defaults = dict(
        domain="imagery",
        passed=True,
        score=1.0,
        gate_results={"a": True},
        failure_tags=(),
        reason="pass",
        cost_usd=0.01,
        attempts=0,
        mode="hard_gate",
    )
    defaults.update(overrides)
    return Verdict(**defaults)


def test_verdict_passed_and_score():
    v = _make()
    assert v.passed and v.score == 1.0
    with pytest.raises(dataclasses.FrozenInstanceError):
        v.passed = False  # type: ignore[misc]


def test_verdict_defaults():
    v = Verdict(domain="copy", passed=False, score=0.0, gate_results={})
    assert v.failure_tags == ()
    assert v.reason == ""
    assert v.cost_usd == 0.0
    assert v.attempts == 0
    assert v.mode == "soft_signal"
    assert dict(v.detail) == {}


def test_gate_results_is_read_only():
    v = _make(gate_results={"sharpness": True})
    with pytest.raises(TypeError):
        v.gate_results["x"] = 1  # type: ignore[index]


def test_severity_order():
    assert Severity.PAGE > Severity.TICKET > Severity.DASHBOARD
