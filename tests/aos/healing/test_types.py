"""Tests for AOS healing types — HealAction, RetryConfig, HealDecision."""

from __future__ import annotations

import pytest

from aos.healing.types import HealAction, HealDecision, RetryConfig


def test_heal_action_string_values() -> None:
    assert HealAction.RETRY == "retry"
    assert HealAction.ABORT == "abort"
    assert HealAction.ESCALATE == "escalate"


def test_retry_config_defaults() -> None:
    cfg = RetryConfig(max_retries=2, base_delay_seconds=1.0)
    assert cfg.exponential is False


def test_retry_config_exponential_flag() -> None:
    cfg = RetryConfig(max_retries=3, base_delay_seconds=2.0, exponential=True)
    assert cfg.exponential is True


def test_retry_config_is_frozen() -> None:
    cfg = RetryConfig(max_retries=1, base_delay_seconds=0.5)
    with pytest.raises((AttributeError, TypeError)):
        cfg.max_retries = 5  # type: ignore[misc]


def test_retry_config_zero_retries() -> None:
    cfg = RetryConfig(max_retries=0, base_delay_seconds=0.0)
    assert cfg.max_retries == 0
    assert cfg.base_delay_seconds == 0.0


def test_heal_decision_fields() -> None:
    decision = HealDecision(action=HealAction.RETRY, delay_seconds=1.5, reason="test retry")
    assert decision.action == HealAction.RETRY
    assert decision.delay_seconds == 1.5
    assert decision.reason == "test retry"


def test_heal_decision_is_frozen() -> None:
    decision = HealDecision(action=HealAction.ABORT, delay_seconds=0.0, reason="abort")
    with pytest.raises((AttributeError, TypeError)):
        decision.action = HealAction.RETRY  # type: ignore[misc]


def test_heal_decision_all_actions() -> None:
    for action in HealAction:
        d = HealDecision(action=action, delay_seconds=0.0, reason="x")
        assert d.action == action
