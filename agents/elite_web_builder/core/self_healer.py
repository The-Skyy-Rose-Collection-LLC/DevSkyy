"""
Self-healing cycle — diagnose, categorize, route, retry.

When verification fails, the healer doesn't just retry blindly. It:
1. Diagnoses what specifically failed
2. Categorizes the failure (CODE_BUG, CONFIG, WRONG_APPROACH, EXTERNAL)
3. Routes to the appropriate fix strategy
4. Retries with verification after each fix
5. Escalates if max attempts exceeded

No blocking — ralph-loop resilience on every step.

Usage:
    healer = SelfHealer(max_attempts=3)
    diagnosis = healer.diagnose(failing_report)
    result = await healer.heal(diagnosis, fixer=my_fixer, verifier=my_verifier)
    if result.escalation_needed:
        await learning_journal.log_failure(...)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable

from core.verification_loop import (
    Gate,
    GateResult,
    GateStatus,
    VerificationReport,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums and data models
# ---------------------------------------------------------------------------


class FailureCategory(Enum):
    """How a failure should be routed for healing."""

    CODE_BUG = "code_bug"           # Syntax error, logic error, wrong value
    CONFIG = "config"               # Missing env var, wrong path, bad setting
    WRONG_APPROACH = "wrong_approach"  # Need to replan entirely
    EXTERNAL = "external"           # API down, rate limit, network issue


@dataclass(frozen=True)
class HealAttempt:
    """Analysis of a single gate failure."""

    gate: Gate
    category: FailureCategory
    description: str


@dataclass(frozen=True)
class Diagnosis:
    """Full diagnosis of a failing verification report."""

    failed_gates: set[Gate]
    failure_analyses: list[HealAttempt]
    suggested_actions: list[str]


@dataclass
class HealResult:
    """Result of a single fix attempt."""

    success: bool
    message: str
    changes: list[str] = field(default_factory=list)


@dataclass
class HealCycleResult:
    """Result of the entire heal cycle (possibly multiple attempts)."""

    success: bool
    attempts: int
    escalation_needed: bool = False
    history: list[HealResult] = field(default_factory=list)
    final_report: VerificationReport | None = None


# ---------------------------------------------------------------------------
# Category routing rules
# ---------------------------------------------------------------------------

# Maps (gate, keyword patterns in message) → category
# Default is CODE_BUG for most failures
_CATEGORY_RULES: dict[Gate, FailureCategory] = {
    Gate.BUILD: FailureCategory.CODE_BUG,
    Gate.TYPES: FailureCategory.CODE_BUG,
    Gate.LINT: FailureCategory.CODE_BUG,
    Gate.TESTS: FailureCategory.CODE_BUG,
    Gate.SECURITY: FailureCategory.CODE_BUG,
    Gate.A11Y: FailureCategory.CODE_BUG,
    Gate.PERF: FailureCategory.CODE_BUG,
    Gate.DIFF: FailureCategory.CODE_BUG,
}

# Override patterns — if message contains these keywords, override category
_CATEGORY_OVERRIDES: list[tuple[str, FailureCategory]] = [
    ("env var", FailureCategory.CONFIG),
    ("missing config", FailureCategory.CONFIG),
    ("file not found", FailureCategory.CONFIG),
    ("connection refused", FailureCategory.EXTERNAL),
    ("rate limit", FailureCategory.EXTERNAL),
    ("timeout", FailureCategory.EXTERNAL),
    ("api key", FailureCategory.CONFIG),
    ("approach", FailureCategory.WRONG_APPROACH),
    ("architectural", FailureCategory.WRONG_APPROACH),
    ("redesign", FailureCategory.WRONG_APPROACH),
    ("lighthouse score", FailureCategory.CODE_BUG),  # perf issues are fixable
]


# ---------------------------------------------------------------------------
# Self Healer
# ---------------------------------------------------------------------------


class SelfHealer:
    """
    Diagnoses verification failures and runs fix→verify→retry loops.

    The healer doesn't fix code itself — it categorizes failures and delegates
    to a fixer function (provided by the caller, typically an agent). After
    each fix, it runs verification again. Escalates after max_attempts.
    """

    def __init__(self, max_attempts: int = 3) -> None:
        self._max_attempts = max_attempts

    def categorize(self, gate_result: GateResult) -> FailureCategory:
        """
        Categorize a gate failure for routing to the right fix strategy.

        Checks message keywords first (overrides), then falls back to
        gate-based defaults.
        """
        msg_lower = gate_result.message.lower()

        for keyword, category in _CATEGORY_OVERRIDES:
            if keyword in msg_lower:
                return category

        return _CATEGORY_RULES.get(gate_result.gate, FailureCategory.CODE_BUG)

    def diagnose(self, report: VerificationReport) -> Diagnosis | None:
        """
        Analyze a failing verification report.

        Returns None if all gates passed (nothing to heal).
        """
        failed_results = [
            r for r in report.results
            if r.status == GateStatus.FAILED
        ]

        if not failed_results:
            return None

        analyses = [
            HealAttempt(
                gate=r.gate,
                category=self.categorize(r),
                description=r.message,
            )
            for r in failed_results
        ]

        # Generate suggested actions based on categories
        actions = []
        categories = {a.category for a in analyses}

        if FailureCategory.CODE_BUG in categories:
            actions.append("Fix code errors in the affected files")
        if FailureCategory.CONFIG in categories:
            actions.append("Check configuration files and environment variables")
        if FailureCategory.WRONG_APPROACH in categories:
            actions.append("Replan the story with a different implementation strategy")
        if FailureCategory.EXTERNAL in categories:
            actions.append("Retry with exponential backoff (external service issue)")

        # Add gate-specific suggestions
        gates = {r.gate for r in failed_results}
        if Gate.LINT in gates:
            actions.append("Run auto-formatter (ruff format / eslint --fix)")
        if Gate.TESTS in gates:
            actions.append("Review and fix failing test cases")
        if Gate.SECURITY in gates:
            actions.append("Remove secrets and security vulnerabilities")
        if Gate.A11Y in gates:
            actions.append("Fix accessibility violations (contrast, ARIA, keyboard)")
        if Gate.PERF in gates:
            actions.append("Optimize performance (lazy load, compress, defer)")

        return Diagnosis(
            failed_gates=gates,
            failure_analyses=analyses,
            suggested_actions=actions,
        )

    async def heal(
        self,
        diagnosis: Diagnosis,
        fixer: Callable[..., Awaitable[HealResult]],
        verifier: Callable[..., Awaitable[VerificationReport]],
    ) -> HealCycleResult:
        """
        Run the heal cycle: fix → verify → retry.

        Args:
            diagnosis: What needs fixing
            fixer: Async function that attempts to fix the issues.
                   Receives the diagnosis and returns HealResult.
            verifier: Async function that re-runs verification.
                      Returns a fresh VerificationReport.

        Returns:
            HealCycleResult with success status and attempt history
        """
        history: list[HealResult] = []

        for attempt in range(1, self._max_attempts + 1):
            logger.info(
                "Heal attempt %d/%d for gates: %s",
                attempt,
                self._max_attempts,
                [g.name for g in diagnosis.failed_gates],
            )

            # Step 1: Try to fix
            fix_result = await fixer(diagnosis)
            history.append(fix_result)

            if not fix_result.success:
                logger.warning(
                    "Heal attempt %d: fixer reported failure — %s",
                    attempt,
                    fix_result.message,
                )
                continue  # Try again

            # Step 2: Verify the fix
            new_report = await verifier()

            if new_report.all_green:
                logger.info("Heal succeeded on attempt %d", attempt)
                return HealCycleResult(
                    success=True,
                    attempts=attempt,
                    history=history,
                    final_report=new_report,
                )

            # Fix was applied but verification still fails
            logger.warning(
                "Heal attempt %d: fix applied but verification still failing — %s",
                attempt,
                [g.name for g in new_report.failed_gates],
            )

            # Update diagnosis for next attempt
            new_diagnosis = self.diagnose(new_report)
            if new_diagnosis is not None:
                diagnosis = new_diagnosis

        # Exhausted all attempts
        logger.error(
            "Heal cycle exhausted %d attempts — escalation needed",
            self._max_attempts,
        )
        return HealCycleResult(
            success=False,
            attempts=self._max_attempts,
            escalation_needed=True,
            history=history,
        )
