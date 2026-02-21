"""
Self Healer — Diagnose-fix-retry cycle for failed verifications.

When verification fails, the system diagnoses the root cause,
categorizes it, routes to the correct fixer, and retries.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FailureCategory(str, Enum):
    """Categories of failures for routing to correct healer."""

    CODE_BUG = "code_bug"
    CONFIG = "config"
    WRONG_APPROACH = "wrong_approach"
    EXTERNAL = "external"
    SECURITY = "security"
    LINT = "lint"
    A11Y = "a11y"


@dataclass
class Diagnosis:
    """Diagnosis of a verification failure."""

    category: FailureCategory
    error_details: str
    suggested_fix: str
    confidence: float = 0.8
    gate_name: str = ""
    fixable: bool = True


class SelfHealer:
    """Self-healing cycle: diagnose → categorize → fix → re-verify."""

    def __init__(self, max_attempts: int = 3) -> None:
        """
        Initialize the SelfHealer with its attempt limit.
        
        Parameters:
            max_attempts (int): Maximum number of diagnose–heal attempts the instance will perform before giving up.
        """
        self._max_attempts = max_attempts
        self._history: list[Diagnosis] = []

    @property
    def history(self) -> list[Diagnosis]:
        """
        Get a shallow copy of the recorded diagnosis history.
        
        Returns:
            list[Diagnosis]: A shallow copy of past Diagnosis entries in chronological order.
        """
        return list(self._history)

    async def diagnose(self, failure_report: str) -> Diagnosis:
        """
        Produce a Diagnosis for a given failure report using gate-aware categorization.
        
        Analyzes the provided failure_report to determine a failure category (security, lint, a11y, code bug, config, external, or wrong approach), selects a suggested fix and fixable flag, extracts an associated gate name, appends the resulting Diagnosis to the healer's history, and logs a brief summary.
        
        Parameters:
            failure_report (str): Raw failure message or output to analyze.
        
        Returns:
            Diagnosis: Contains the determined category, original error details, a suggested fix, the extracted gate name, confidence, and whether the issue is considered fixable.
        """
        lower = failure_report.lower()

        # Gate-aware categorization
        if "secret" in lower or "injection" in lower or "xss" in lower:
            category = FailureCategory.SECURITY
            fix = _suggest_security_fix(failure_report)
            fixable = True
        elif "lint" in lower or "console.log" in lower or "debugger" in lower:
            category = FailureCategory.LINT
            fix = _suggest_lint_fix(failure_report)
            fixable = True
        elif "a11y" in lower or "alt" in lower or "aria" in lower:
            category = FailureCategory.A11Y
            fix = _suggest_a11y_fix(failure_report)
            fixable = True
        elif "syntax" in lower or "parse" in lower or "typeerror" in lower:
            category = FailureCategory.CODE_BUG
            fix = f"Fix syntax/parse error: {failure_report[:200]}"
            fixable = True
        elif "config" in lower or "env" in lower or "setting" in lower:
            category = FailureCategory.CONFIG
            fix = f"Fix configuration: {failure_report[:200]}"
            fixable = True
        elif "timeout" in lower or "connection" in lower:
            category = FailureCategory.EXTERNAL
            fix = "Retry after external service recovery"
            fixable = False
        else:
            category = FailureCategory.WRONG_APPROACH
            fix = f"Revise approach: {failure_report[:200]}"
            fixable = True

        gate_name = _extract_gate_name(failure_report)
        diagnosis = Diagnosis(
            category=category,
            error_details=failure_report,
            suggested_fix=fix,
            gate_name=gate_name,
            fixable=fixable,
        )
        self._history.append(diagnosis)
        logger.info("Diagnosis: %s — %s", category.value, failure_report[:100])
        return diagnosis

    async def heal(self, content: str, diagnosis: Diagnosis) -> str:
        """
        Apply a diagnosis-guided repair to the given content.
        
        Parameters:
            content (str): The source content to modify (e.g., code or markup).
            diagnosis (Diagnosis): Diagnosis that determines which healer to apply.
        
        Returns:
            healed_content (str): The content after applying the appropriate healer; returns the original `content` if the diagnosis is not fixable or no matching healer is available.
        """
        logger.info(
            "Healing attempt for %s (gate=%s): %s",
            diagnosis.category.value,
            diagnosis.gate_name,
            diagnosis.error_details[:100],
        )

        if not diagnosis.fixable:
            return content

        healers = {
            FailureCategory.LINT: _heal_lint,
            FailureCategory.SECURITY: _heal_security,
            FailureCategory.A11Y: _heal_a11y,
        }
        healer = healers.get(diagnosis.category)
        if healer:
            return healer(content, diagnosis)

        return content


# ─── Fix Suggesters ───────────────────────────────────────────────────


def _suggest_security_fix(report: str) -> str:
    """
    Suggest a concise security remediation based on keywords found in a failure report.
    
    Parameters:
        report (str): Text of the failure report to scan for security indicators.
    
    Returns:
        str: A suggested security fix message tailored to the detected issue.
    """
    if "innerhtml" in report.lower():
        return "Replace innerHTML with textContent or sanitized insertion"
    if "secret" in report.lower() or "key" in report.lower():
        return "Move secrets to environment variables"
    return "Review and fix security finding"


def _suggest_lint_fix(report: str) -> str:
    """
    Suggests a lint remediation message by inspecting a failure report for common lint-related keywords.
    
    Parameters:
        report (str): The failure report text to check for lint indicators such as `console.log`, `debugger`, or `var`.
    
    Returns:
        str: A suggested lint fix message (e.g., "Remove console.log statements", "Remove debugger statements", "Replace var with const or let", or a generic "Fix lint warnings").
    """
    if "console.log" in report.lower():
        return "Remove console.log statements"
    if "debugger" in report.lower():
        return "Remove debugger statements"
    if "var " in report.lower():
        return "Replace var with const or let"
    return "Fix lint warnings"


def _suggest_a11y_fix(report: str) -> str:
    """
    Suggests an accessibility-focused fix message based on keywords found in a failure report.
    
    Parameters:
    	report (str): Failure report text to analyze for accessibility hints.
    
    Returns:
    	suggestion (str): A suggested fix message:
    	- "Add descriptive alt attributes to all img tags" if the report mentions "alt".
    	- "Add appropriate aria-label attributes" if the report mentions "aria".
    	- "Fix accessibility violations" otherwise.
    """
    if "alt" in report.lower():
        return "Add descriptive alt attributes to all img tags"
    if "aria" in report.lower():
        return "Add appropriate aria-label attributes"
    return "Fix accessibility violations"


def _extract_gate_name(report: str) -> str:
    """
    Identify the first pipeline gate keyword mentioned in a failure report.
    
    Searches the provided report text for known gate names and returns the first match found.
    
    Parameters:
        report (str): The failure report text to search.
    
    Returns:
        str: The matching gate name (one of "build", "types", "lint", "tests", "security", "a11y", "perf", "diff") if present, otherwise an empty string.
    """
    lower = report.lower()
    for name in ("build", "types", "lint", "tests", "security", "a11y", "perf", "diff"):
        if name in lower:
            return name
    return ""


# ─── Content Healers ──────────────────────────────────────────────────


def _heal_lint(content: str, diagnosis: Diagnosis) -> str:
    """
    Remove common lint issues from the given source content.
    
    Returns:
        The input content with `console.log` and `debugger` statements removed and `var` declarations replaced with `const`.
    """
    result = re.sub(r"^\s*console\.log\([^)]*\);?\s*\n?", "", content, flags=re.MULTILINE)
    result = re.sub(r"^\s*debugger;?\s*\n?", "", result, flags=re.MULTILINE)
    result = re.sub(r"\bvar\s+", "const ", result)
    return result


def _heal_security(content: str, diagnosis: Diagnosis) -> str:
    """
    Replace insecure `.innerHTML` assignments with `.textContent` assignments in the provided content.
    
    Parameters:
    	content (str): The source text or code to be healed.
    	diagnosis (Diagnosis): The diagnosis that motivated this healing attempt; may provide context for the transformation.
    
    Returns:
    	str: The transformed content with `.innerHTML =` replaced by `.textContent =`.
    """
    result = re.sub(
        r"\.innerHTML\s*=\s*",
        ".textContent = ",
        content,
    )
    return result


def _heal_a11y(content: str, diagnosis: Diagnosis) -> str:
    """
    Ensure all <img> tags include an `alt` attribute by injecting `alt=""` when missing.
    
    Parameters:
        content (str): HTML or template text to process.
        diagnosis (Diagnosis): Diagnosis metadata associated with the issue (may be used by healers).
    
    Returns:
        str: The input content with any <img> tags that lacked an `alt` attribute updated to include `alt=""`; existing `alt` attributes are preserved.
    """
    result = re.sub(
        r"<img\b((?![^>]*\balt\s*=)[^>]*)>",
        r'<img\1 alt="">',
        content,
    )
    return result