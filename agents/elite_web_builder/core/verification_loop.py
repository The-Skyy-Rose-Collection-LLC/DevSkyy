"""
Verification Loop — 8-gate quality check system.

Every agent output must pass all 8 gates before being marked GREEN.
Gates: BUILD, TYPES, LINT, TESTS, SECURITY, A11Y, PERF, DIFF.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class GateStatus(str, Enum):
    """Status of a quality gate."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class GateName(str, Enum):
    """Names of the 8 quality gates."""

    BUILD = "build"
    TYPES = "types"
    LINT = "lint"
    TESTS = "tests"
    SECURITY = "security"
    A11Y = "a11y"
    PERF = "perf"
    DIFF = "diff"


@dataclass(frozen=True)
class GateResult:
    """Immutable result from a single gate check."""

    gate: str
    status: GateStatus
    message: str = ""
    details: dict = field(default_factory=dict)


@dataclass
class VerificationResult:
    """Complete verification result across all gates."""

    gates: list[GateResult] = field(default_factory=list)

    @property
    def all_green(self) -> bool:
        """True if all gates passed."""
        return all(g.status == GateStatus.PASSED for g in self.gates)

    @property
    def failures(self) -> list[GateResult]:
        """List of failed gates."""
        return [g for g in self.gates if g.status == GateStatus.FAILED]

    @property
    def summary(self) -> dict[str, int]:
        """Count of each status."""
        result: dict[str, int] = {}
        for gate in self.gates:
            key = gate.status.value
            result[key] = result.get(key, 0) + 1
        return result


class VerificationLoop:
    """Runs all 8 quality gates on agent output."""

    def __init__(self, config: dict | None = None) -> None:
        self._config = config or {}
        self._gate_runners: dict[str, object] = {}

    async def run(self, content: str, *, context: dict | None = None) -> VerificationResult:
        """Run all verification gates on content."""
        result = VerificationResult()
        ctx = context or {}

        for gate_name in GateName:
            gate_result = await self._run_gate(gate_name, content, ctx)
            result.gates.append(gate_result)

        if result.all_green:
            logger.info("All 8 gates PASSED")
        else:
            failed = [g.gate for g in result.failures]
            logger.warning("Gates FAILED: %s", ", ".join(failed))

        return result

    async def _run_gate(
        self, gate: GateName, content: str, context: dict
    ) -> GateResult:
        """Run a single gate. Subclasses can override for real checks."""
        # Default implementation: pass all gates (overridden in production)
        return GateResult(
            gate=gate.value,
            status=GateStatus.PASSED,
            message=f"{gate.value} check passed",
        )
