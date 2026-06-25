"""HealingDirector — maps FailureCategory + attempt number to a HealDecision."""

from __future__ import annotations

from aos.cognition.reflector import FailureCategory
from aos.healing.policy import compute_delay, get_policy
from aos.healing.types import HealAction, HealDecision


class HealingDirector:
    """Stateless decision engine: given a failure category and attempt index, returns a HealDecision."""

    def decide(self, category: FailureCategory, attempt: int) -> HealDecision:
        if category == FailureCategory.BUDGET_EXCEEDED:
            return HealDecision(
                action=HealAction.ESCALATE,
                delay_seconds=0.0,
                reason="budget exceeded — escalate for human review",
            )
        if category == FailureCategory.POLICY_DENIAL:
            return HealDecision(
                action=HealAction.ABORT,
                delay_seconds=0.0,
                reason="policy denied — abort to prevent unauthorized re-attempts",
            )

        config = get_policy(category)
        if attempt >= config.max_retries:
            if category == FailureCategory.UNKNOWN:
                return HealDecision(
                    action=HealAction.ABORT,
                    delay_seconds=0.0,
                    reason=f"unknown failure exhausted {config.max_retries} retries — abort",
                )
            return HealDecision(
                action=HealAction.ESCALATE,
                delay_seconds=0.0,
                reason=f"{category} exhausted {config.max_retries} retries — escalate",
            )

        delay = compute_delay(config, attempt)
        return HealDecision(
            action=HealAction.RETRY,
            delay_seconds=delay,
            reason=f"{category} attempt {attempt + 1} of {config.max_retries}",
        )
