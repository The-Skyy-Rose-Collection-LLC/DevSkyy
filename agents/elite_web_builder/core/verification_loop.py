"""
8-gate quality verification loop.

Every story passes through 8 sequential gates. ALL must pass (or be skipped)
for the story to be marked GREEN. Any failure triggers the self-heal cycle.

Gates (in order):
1. BUILD    — Does it compile? (npm build / php -l / python -m py_compile)
2. TYPES    — Type check passes? (tsc --noEmit / mypy / pyright)
3. LINT     — Clean code? (eslint / ruff / phpcs)
4. TESTS    — Tests pass? (jest / pytest / phpunit) + coverage threshold
5. SECURITY — No secrets? No XSS vectors? No console.log?
6. A11Y     — axe-core 0 violations? Contrast passes? ARIA complete?
7. PERF     — Lighthouse > threshold? No render-blocking?
8. DIFF     — Only expected files changed? No unintended mutations?

Usage:
    loop = VerificationLoop(config=VerificationConfig())
    report = await loop.run_all(checkers={Gate.BUILD: my_build_checker, ...})
    if report.all_green:
        mark_story_complete()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Gate(Enum):
    """The 8 quality gates, in execution order."""

    BUILD = "build"
    TYPES = "types"
    LINT = "lint"
    TESTS = "tests"
    SECURITY = "security"
    A11Y = "a11y"
    PERF = "perf"
    DIFF = "diff"


class GateStatus(Enum):
    """Outcome of a single gate check."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


# ---------------------------------------------------------------------------
# Data models (frozen / immutable where possible)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GateResult:
    """Immutable result of running one gate."""

    gate: Gate
    status: GateStatus
    message: str
    details: list[str] = field(default_factory=list)
    duration_ms: float = 0.0

    @property
    def passed(self) -> bool:
        """PASSED or SKIPPED both count as 'passed'."""
        return self.status in (GateStatus.PASSED, GateStatus.SKIPPED)


@dataclass
class VerificationConfig:
    """Configuration for the verification loop."""

    disabled_gates: set[Gate] = field(default_factory=set)
    max_retries: int = 3
    thresholds: dict[str, float] = field(default_factory=dict)
    fail_fast: bool = False  # Stop on first failure?

    def is_enabled(self, gate: Gate) -> bool:
        return gate not in self.disabled_gates


# ---------------------------------------------------------------------------
# Verification Report
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VerificationReport:
    """Immutable report from a full verification run."""

    results: list[GateResult]

    @property
    def all_green(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.status == GateStatus.PASSED)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if r.status == GateStatus.FAILED)

    @property
    def skipped_count(self) -> int:
        return sum(1 for r in self.results if r.status == GateStatus.SKIPPED)

    @property
    def failed_gates(self) -> set[Gate]:
        return {r.gate for r in self.results if r.status == GateStatus.FAILED}

    def to_dict(self) -> dict[str, Any]:
        return {
            "all_green": self.all_green,
            "passed": self.passed_count,
            "failed": self.failed_count,
            "skipped": self.skipped_count,
            "gates": [
                {
                    "gate": r.gate.value,
                    "status": r.status.value,
                    "message": r.message,
                    "details": r.details,
                    "duration_ms": r.duration_ms,
                }
                for r in self.results
            ],
        }


# ---------------------------------------------------------------------------
# Verification Loop
# ---------------------------------------------------------------------------

# Type alias for gate checker functions
GateChecker = Callable[[], Awaitable[GateResult]]


class VerificationLoop:
    """
    Runs all 8 quality gates in order and produces a VerificationReport.

    Each gate is an async callable that returns a GateResult. Gates can be
    disabled in config, missing checkers are auto-skipped.
    """

    def __init__(self, config: VerificationConfig | None = None) -> None:
        self._config = config or VerificationConfig()

    async def run_gate(
        self,
        gate: Gate,
        checker: GateChecker,
    ) -> GateResult:
        """
        Run a single gate's checker.

        Returns SKIPPED if the gate is disabled. Catches exceptions and
        converts them to FAILED results (no blocking).
        """
        if not self._config.is_enabled(gate):
            logger.debug("Gate %s disabled, skipping", gate.name)
            return GateResult(
                gate=gate,
                status=GateStatus.SKIPPED,
                message=f"{gate.name} disabled in config",
            )

        try:
            result = await checker()
            logger.info(
                "Gate %s: %s — %s",
                gate.name,
                result.status.value,
                result.message,
            )
            return result
        except Exception as exc:
            logger.error("Gate %s raised error: %s", gate.name, exc)
            return GateResult(
                gate=gate,
                status=GateStatus.FAILED,
                message=f"{gate.name} error: {exc}",
                details=[str(exc)],
            )

    async def run_all(
        self,
        checkers: dict[Gate, GateChecker],
    ) -> VerificationReport:
        """
        Run all 8 gates in order with the provided checkers.

        Gates without a checker are auto-skipped. If fail_fast is True,
        stops at the first failure.

        Args:
            checkers: Map of Gate → async checker function

        Returns:
            VerificationReport with all gate results
        """
        results: list[GateResult] = []

        for gate in Gate:
            checker = checkers.get(gate)

            if checker is None:
                # No checker provided — auto-skip
                results.append(GateResult(
                    gate=gate,
                    status=GateStatus.SKIPPED,
                    message=f"No checker for {gate.name}",
                ))
                continue

            result = await self.run_gate(gate, checker)
            results.append(result)

            if self._config.fail_fast and not result.passed:
                logger.warning(
                    "Fail-fast: stopping at gate %s", gate.name
                )
                # Skip remaining gates
                remaining = [g for g in Gate if g not in {r.gate for r in results}]
                for g in remaining:
                    results.append(GateResult(
                        gate=g,
                        status=GateStatus.SKIPPED,
                        message=f"Skipped (fail-fast after {gate.name})",
                    ))
                break

        return VerificationReport(results=results)
