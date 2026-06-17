import dataclasses

from evaluation.contracts import Severity, Verdict


def test_verdict_passed_and_score():
    v = Verdict(
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
    assert v.passed and v.score == 1.0
    try:
        v.passed = False
        assert False
    except dataclasses.FrozenInstanceError:
        pass


def test_severity_order():
    assert Severity.PAGE > Severity.TICKET > Severity.DASHBOARD
