"""Tests for HealingDirector.decide()."""

from __future__ import annotations

import pytest

from aos.cognition.reflector import FailureCategory
from aos.healing.director import HealingDirector
from aos.healing.types import HealAction


@pytest.fixture()
def director() -> HealingDirector:
    return HealingDirector()


def test_budget_exceeded_always_escalates(director: HealingDirector) -> None:
    for attempt in range(5):
        decision = director.decide(FailureCategory.BUDGET_EXCEEDED, attempt)
        assert decision.action == HealAction.ESCALATE
        assert decision.delay_seconds == 0.0


def test_policy_denial_always_aborts(director: HealingDirector) -> None:
    for attempt in range(5):
        decision = director.decide(FailureCategory.POLICY_DENIAL, attempt)
        assert decision.action == HealAction.ABORT
        assert decision.delay_seconds == 0.0


def test_rate_limit_retries_within_max(director: HealingDirector) -> None:
    for attempt in range(3):
        decision = director.decide(FailureCategory.RATE_LIMIT, attempt)
        assert decision.action == HealAction.RETRY


def test_rate_limit_escalates_at_max(director: HealingDirector) -> None:
    decision = director.decide(FailureCategory.RATE_LIMIT, 3)
    assert decision.action == HealAction.ESCALATE


def test_rate_limit_exponential_delay(director: HealingDirector) -> None:
    d0 = director.decide(FailureCategory.RATE_LIMIT, 0)
    d1 = director.decide(FailureCategory.RATE_LIMIT, 1)
    d2 = director.decide(FailureCategory.RATE_LIMIT, 2)
    assert d0.delay_seconds == 2.0
    assert d1.delay_seconds == 4.0
    assert d2.delay_seconds == 8.0


def test_timeout_retries_within_max(director: HealingDirector) -> None:
    for attempt in range(2):
        decision = director.decide(FailureCategory.TIMEOUT, attempt)
        assert decision.action == HealAction.RETRY


def test_timeout_escalates_at_max(director: HealingDirector) -> None:
    decision = director.decide(FailureCategory.TIMEOUT, 2)
    assert decision.action == HealAction.ESCALATE


def test_timeout_flat_delay(director: HealingDirector) -> None:
    d0 = director.decide(FailureCategory.TIMEOUT, 0)
    d1 = director.decide(FailureCategory.TIMEOUT, 1)
    assert d0.delay_seconds == d1.delay_seconds == 1.0


def test_context_overflow_retries_once(director: HealingDirector) -> None:
    decision = director.decide(FailureCategory.CONTEXT_OVERFLOW, 0)
    assert decision.action == HealAction.RETRY


def test_context_overflow_escalates_after(director: HealingDirector) -> None:
    decision = director.decide(FailureCategory.CONTEXT_OVERFLOW, 1)
    assert decision.action == HealAction.ESCALATE


def test_tool_failure_retries_once(director: HealingDirector) -> None:
    decision = director.decide(FailureCategory.TOOL_FAILURE, 0)
    assert decision.action == HealAction.RETRY


def test_tool_failure_escalates_after(director: HealingDirector) -> None:
    decision = director.decide(FailureCategory.TOOL_FAILURE, 1)
    assert decision.action == HealAction.ESCALATE


def test_unknown_retries_once(director: HealingDirector) -> None:
    decision = director.decide(FailureCategory.UNKNOWN, 0)
    assert decision.action == HealAction.RETRY


def test_unknown_aborts_after_max(director: HealingDirector) -> None:
    decision = director.decide(FailureCategory.UNKNOWN, 1)
    assert decision.action == HealAction.ABORT


def test_decision_reason_is_nonempty(director: HealingDirector) -> None:
    for category in FailureCategory:
        decision = director.decide(category, 0)
        assert isinstance(decision.reason, str)
        assert len(decision.reason) > 0
