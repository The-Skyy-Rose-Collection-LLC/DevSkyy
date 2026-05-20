"""Tests for per-FailureCategory retry policies."""

from __future__ import annotations

import pytest

from aos.cognition.reflector import FailureCategory
from aos.healing.policy import compute_delay, get_policy
from aos.healing.types import RetryConfig


def test_rate_limit_policy() -> None:
    cfg = get_policy(FailureCategory.RATE_LIMIT)
    assert cfg.max_retries == 3
    assert cfg.base_delay_seconds == 2.0
    assert cfg.exponential is True


def test_timeout_policy() -> None:
    cfg = get_policy(FailureCategory.TIMEOUT)
    assert cfg.max_retries == 2
    assert cfg.base_delay_seconds == 1.0
    assert cfg.exponential is False


def test_context_overflow_policy() -> None:
    cfg = get_policy(FailureCategory.CONTEXT_OVERFLOW)
    assert cfg.max_retries == 1
    assert cfg.base_delay_seconds == 0.5


def test_budget_exceeded_no_retries() -> None:
    cfg = get_policy(FailureCategory.BUDGET_EXCEEDED)
    assert cfg.max_retries == 0
    assert cfg.base_delay_seconds == 0.0


def test_policy_denial_no_retries() -> None:
    cfg = get_policy(FailureCategory.POLICY_DENIAL)
    assert cfg.max_retries == 0
    assert cfg.base_delay_seconds == 0.0


def test_tool_failure_policy() -> None:
    cfg = get_policy(FailureCategory.TOOL_FAILURE)
    assert cfg.max_retries == 1
    assert cfg.base_delay_seconds == 0.5


def test_unknown_policy() -> None:
    cfg = get_policy(FailureCategory.UNKNOWN)
    assert cfg.max_retries == 1
    assert cfg.base_delay_seconds == 1.0


def test_get_policy_returns_retry_config_for_all_categories() -> None:
    for category in FailureCategory:
        result = get_policy(category)
        assert isinstance(result, RetryConfig)


def test_compute_delay_flat_is_constant() -> None:
    cfg = RetryConfig(max_retries=2, base_delay_seconds=1.0, exponential=False)
    assert compute_delay(cfg, 0) == 1.0
    assert compute_delay(cfg, 1) == 1.0
    assert compute_delay(cfg, 5) == 1.0


def test_compute_delay_exponential_attempt0() -> None:
    cfg = RetryConfig(max_retries=3, base_delay_seconds=2.0, exponential=True)
    assert compute_delay(cfg, 0) == 2.0  # 2 * 2^0


def test_compute_delay_exponential_attempt1() -> None:
    cfg = RetryConfig(max_retries=3, base_delay_seconds=2.0, exponential=True)
    assert compute_delay(cfg, 1) == 4.0  # 2 * 2^1


def test_compute_delay_exponential_attempt2() -> None:
    cfg = RetryConfig(max_retries=3, base_delay_seconds=2.0, exponential=True)
    assert compute_delay(cfg, 2) == 8.0  # 2 * 2^2


def test_compute_delay_flat_zero() -> None:
    cfg = RetryConfig(max_retries=0, base_delay_seconds=0.0)
    assert compute_delay(cfg, 0) == 0.0
