"""Tests for Reflector quality scoring and failure classification."""

from __future__ import annotations

import pytest

from aos.cognition.reflector import FailureCategory, Reflector
from aos.observability.learning_hook import LearningTrace


def _trace(
    agent_type: str = "test",
    prompt: str = "do something",
    result: str | None = "ok",
    success: bool = True,
    error: str | None = None,
    retry_count: int = 0,
    heal_categories: tuple[str, ...] = (),
    cost_usd: float = 0.0,
    latency_ms: float = 0.0,
) -> LearningTrace:
    return LearningTrace(
        agent_type=agent_type,
        prompt=prompt,
        result=result,
        success=success,
        error=error,
        retry_count=retry_count,
        heal_categories=heal_categories,
        cost_usd=cost_usd,
        latency_ms=latency_ms,
    )


class _FakeOutcome:
    """Minimal duck-type of ExecutionOutcome for reflector tests."""

    def __init__(
        self,
        pid: int = 1,
        success: bool = True,
        error: str | None = None,
        heal_entries: tuple = (),
    ) -> None:
        self.pid = pid
        self.success = success
        self.error = error
        self.heal_entries = heal_entries


class TestQualityScoring:
    def setup_method(self):
        self.reflector = Reflector()

    def test_perfect_score(self):
        outcome = _FakeOutcome(success=True)
        reflection = self.reflector.reflect(outcome, _trace(success=True))
        assert reflection.quality_score == pytest.approx(1.0)

    def test_failure_deducts_half(self):
        outcome = _FakeOutcome(success=False, error="unknown")
        reflection = self.reflector.reflect(outcome, _trace(success=False))
        assert reflection.quality_score == pytest.approx(0.5)

    def test_one_heal_entry_deducts_005(self):
        from tests.aos._mocks import MockHealEntry

        outcome = _FakeOutcome(success=True, heal_entries=(MockHealEntry(category="timeout"),))
        reflection = self.reflector.reflect(outcome, _trace())
        assert reflection.quality_score == pytest.approx(0.95)

    def test_heal_penalty_caps_at_020(self):
        from tests.aos._mocks import MockHealEntry

        entries = tuple(MockHealEntry(category="rate_limit") for _ in range(10))
        outcome = _FakeOutcome(success=True, heal_entries=entries)
        reflection = self.reflector.reflect(outcome, _trace())
        assert reflection.quality_score == pytest.approx(0.80)

    def test_high_cost_deducts_010(self):
        outcome = _FakeOutcome(success=True)
        reflection = self.reflector.reflect(outcome, _trace(cost_usd=0.6))
        assert reflection.quality_score == pytest.approx(0.9)

    def test_high_latency_deducts_010(self):
        outcome = _FakeOutcome(success=True)
        reflection = self.reflector.reflect(outcome, _trace(latency_ms=6000.0))
        assert reflection.quality_score == pytest.approx(0.9)

    def test_all_penalties_applied(self):
        from tests.aos._mocks import MockHealEntry

        entries = tuple(MockHealEntry(category="rate_limit") for _ in range(10))
        outcome = _FakeOutcome(success=False, error="budget exceeded", heal_entries=entries)
        reflection = self.reflector.reflect(
            outcome, _trace(success=False, cost_usd=1.0, latency_ms=10000.0)
        )
        # 1.0 - 0.5(failure) - 0.20(heal cap) - 0.10(cost) - 0.10(latency) = 0.10
        assert reflection.quality_score == pytest.approx(0.1)

    def test_score_clamped_to_1(self):
        outcome = _FakeOutcome(success=True)
        reflection = self.reflector.reflect(outcome, _trace())
        assert reflection.quality_score <= 1.0


class TestFailureClassification:
    def setup_method(self):
        self.reflector = Reflector()

    def _reflect_error(self, error: str) -> FailureCategory | None:
        outcome = _FakeOutcome(success=False, error=error)
        ref = self.reflector.reflect(outcome, _trace(success=False, error=error))
        return ref.failure_category

    def test_rate_limit(self):
        assert self._reflect_error("429 rate limit exceeded") == FailureCategory.RATE_LIMIT

    def test_timeout(self):
        assert self._reflect_error("operation timed out") == FailureCategory.TIMEOUT

    def test_context_overflow(self):
        assert self._reflect_error("context length exceeded") == FailureCategory.CONTEXT_OVERFLOW

    def test_tool_failure(self):
        assert self._reflect_error("tool error: bad params") == FailureCategory.TOOL_FAILURE

    def test_policy_denial(self):
        assert self._reflect_error("policy denied: forbidden") == FailureCategory.POLICY_DENIAL

    def test_budget_exceeded_takes_priority(self):
        assert self._reflect_error("budget exceeded the limit") == FailureCategory.BUDGET_EXCEEDED

    def test_unknown_fallback(self):
        assert self._reflect_error("some weird error") == FailureCategory.UNKNOWN

    def test_no_failure_category_when_success(self):
        outcome = _FakeOutcome(success=True)
        ref = self.reflector.reflect(outcome, _trace(success=True))
        assert ref.failure_category is None
        assert ref.remediation is None

    def test_remediation_set_on_failure(self):
        outcome = _FakeOutcome(success=False, error="429 too many requests")
        ref = self.reflector.reflect(outcome, _trace(success=False))
        assert ref.remediation is not None
        assert len(ref.remediation) > 0
