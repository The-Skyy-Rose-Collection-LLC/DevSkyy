"""
Self Healer — Diagnose-fix-retry cycle for failed verifications.

When verification fails, the system diagnoses the root cause,
categorizes it, routes to the correct fixer, and retries.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FailureCategory(str, Enum):
    """Categories of failures for routing to correct healer."""

    CODE_BUG = "code_bug"
    CONFIG = "config"
    WRONG_APPROACH = "wrong_approach"
    EXTERNAL = "external"


@dataclass
class Diagnosis:
    """Diagnosis of a verification failure."""

    category: FailureCategory
    error_details: str
    suggested_fix: str
    confidence: float = 0.8


class SelfHealer:
    """Self-healing cycle: diagnose → categorize → fix → re-verify."""

    def __init__(self, max_attempts: int = 3) -> None:
        self._max_attempts = max_attempts
        self._history: list[Diagnosis] = []

    @property
    def history(self) -> list[Diagnosis]:
        return list(self._history)

    async def diagnose(self, failure_report: str) -> Diagnosis:
        """Analyze a failure and produce a diagnosis."""
        # Heuristic categorization
        lower = failure_report.lower()
        if "syntax" in lower or "undefined" in lower or "typeerror" in lower:
            category = FailureCategory.CODE_BUG
        elif "config" in lower or "env" in lower or "setting" in lower:
            category = FailureCategory.CONFIG
        elif "timeout" in lower or "connection" in lower or "api" in lower:
            category = FailureCategory.EXTERNAL
        else:
            category = FailureCategory.WRONG_APPROACH

        diagnosis = Diagnosis(
            category=category,
            error_details=failure_report,
            suggested_fix=f"Fix {category.value}: {failure_report[:200]}",
        )
        self._history.append(diagnosis)
        logger.info("Diagnosis: %s — %s", category.value, failure_report[:100])
        return diagnosis

    async def heal(
        self, content: str, diagnosis: Diagnosis
    ) -> str:
        """Attempt to heal content based on diagnosis. Returns fixed content."""
        # In production, this routes to the appropriate agent for fixing.
        # Default: return content unchanged (agents override this).
        logger.info(
            "Healing attempt for %s: %s",
            diagnosis.category.value,
            diagnosis.error_details[:100],
        )
        return content
