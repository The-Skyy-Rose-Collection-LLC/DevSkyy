"""Reflector — converts ExecutionOutcome + LearningTrace into a quality-scored Reflection.

Quality scoring formula:
    start 1.0
    -0.50  if not success
    -0.05 per heal entry, capped at -0.20 total
    -0.10  if cost_usd > 0.5
    -0.10  if latency_ms > 5000
    clamp to [0.0, 1.0]

Failure categories are classified by tokenising the error string against
keyword lists — no LLM required for the rule-based path.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from aos.observability.learning_hook import LearningTrace

if TYPE_CHECKING:
    from aos.runtime.executor import ExecutionOutcome

_HIGH_COST_THRESHOLD_USD = 0.5
_HIGH_LATENCY_THRESHOLD_MS = 5_000.0
_HEAL_PENALTY_PER_ENTRY = 0.05
_HEAL_PENALTY_CAP = 0.20


class FailureCategory(StrEnum):
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    CONTEXT_OVERFLOW = "context_overflow"
    TOOL_FAILURE = "tool_failure"
    POLICY_DENIAL = "policy_denial"
    BUDGET_EXCEEDED = "budget_exceeded"
    UNKNOWN = "unknown"


_REMEDIATION: dict[FailureCategory, str] = {
    FailureCategory.RATE_LIMIT: "Add exponential backoff and retry delay",
    FailureCategory.TIMEOUT: "Increase timeout or reduce prompt complexity",
    FailureCategory.CONTEXT_OVERFLOW: "Truncate context or split into smaller tasks",
    FailureCategory.TOOL_FAILURE: "Validate tool call parameters before execution",
    FailureCategory.POLICY_DENIAL: "Review agent policy rules for this agent_type",
    FailureCategory.BUDGET_EXCEEDED: "Increase budget_usd or optimise for cost",
    FailureCategory.UNKNOWN: "Investigate error logs for root cause",
}

# Ordered by specificity — first match wins
_CATEGORY_SIGNALS: list[tuple[FailureCategory, tuple[str, ...]]] = [
    (FailureCategory.BUDGET_EXCEEDED, ("budget exceeded", "budget_exceeded", "cost limit")),
    (FailureCategory.RATE_LIMIT, ("429", "rate limit", "too many requests", "ratelimit")),
    (FailureCategory.TIMEOUT, ("timeout", "timed out", "timedout")),
    (
        FailureCategory.CONTEXT_OVERFLOW,
        ("context length", "token limit", "max tokens", "context window"),
    ),
    (FailureCategory.TOOL_FAILURE, ("tool error", "function call failed", "tool_call")),
    (FailureCategory.POLICY_DENIAL, ("policy denied", "permission denied", "denied by policy")),
]


class Reflection(BaseModel):
    """Quality-scored reflection on a completed ExecutionOutcome."""

    model_config = {"frozen": True}

    outcome_pid: int
    agent_type: str
    success: bool
    failure_category: FailureCategory | None = None
    remediation: str | None = None
    quality_score: float = Field(ge=0.0, le=1.0)
    trace: LearningTrace


class Reflector:
    """Converts an ExecutionOutcome into a Reflection with quality scoring."""

    def reflect(self, outcome: ExecutionOutcome, trace: LearningTrace) -> Reflection:
        """Produce a Reflection from a completed outcome and its learning trace."""
        failure_cat: FailureCategory | None = None
        remediation: str | None = None

        if not outcome.success and outcome.error:
            failure_cat = classify_failure(outcome.error)
            remediation = _REMEDIATION[failure_cat]

        quality = _compute_quality(outcome, trace)
        return Reflection(
            outcome_pid=outcome.pid,
            agent_type=trace.agent_type,
            success=outcome.success,
            failure_category=failure_cat,
            remediation=remediation,
            quality_score=quality,
            trace=trace,
        )


def classify_failure(error: str) -> FailureCategory:
    lower = error.lower()
    for category, signals in _CATEGORY_SIGNALS:
        if any(sig in lower for sig in signals):
            return category
    return FailureCategory.UNKNOWN


def _compute_quality(outcome: ExecutionOutcome, trace: LearningTrace) -> float:
    score = 1.0
    if not outcome.success:
        score -= 0.5
    heal_penalty = min(_HEAL_PENALTY_CAP, _HEAL_PENALTY_PER_ENTRY * len(outcome.heal_entries))
    score -= heal_penalty
    if trace.cost_usd > _HIGH_COST_THRESHOLD_USD:
        score -= 0.1
    if trace.latency_ms > _HIGH_LATENCY_THRESHOLD_MS:
        score -= 0.1
    return max(0.0, min(1.0, score))
