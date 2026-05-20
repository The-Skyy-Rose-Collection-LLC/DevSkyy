"""Per-FailureCategory retry policies for the AOS healing layer."""

from __future__ import annotations

from aos.cognition.reflector import FailureCategory
from aos.healing.types import RetryConfig

_POLICY: dict[FailureCategory, RetryConfig] = {
    FailureCategory.RATE_LIMIT: RetryConfig(
        max_retries=3, base_delay_seconds=2.0, exponential=True
    ),
    FailureCategory.TIMEOUT: RetryConfig(max_retries=2, base_delay_seconds=1.0),
    FailureCategory.CONTEXT_OVERFLOW: RetryConfig(max_retries=1, base_delay_seconds=0.5),
    FailureCategory.BUDGET_EXCEEDED: RetryConfig(max_retries=0, base_delay_seconds=0.0),
    FailureCategory.POLICY_DENIAL: RetryConfig(max_retries=0, base_delay_seconds=0.0),
    FailureCategory.TOOL_FAILURE: RetryConfig(max_retries=1, base_delay_seconds=0.5),
    FailureCategory.UNKNOWN: RetryConfig(max_retries=1, base_delay_seconds=1.0),
}


def get_policy(category: FailureCategory) -> RetryConfig:
    return _POLICY.get(category, _POLICY[FailureCategory.UNKNOWN])


def compute_delay(config: RetryConfig, attempt: int) -> float:
    if config.exponential:
        return config.base_delay_seconds * (2**attempt)
    return config.base_delay_seconds
