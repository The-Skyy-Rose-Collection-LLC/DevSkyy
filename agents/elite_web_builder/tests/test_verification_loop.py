"""Tests for core/verification_loop.py — 8-gate quality check.

Every story passes through 8 gates: build, types, lint, tests,
security, a11y, performance, diff. ALL must pass for GREEN.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.verification_loop import (
    Gate,
    GateResult,
    GateStatus,
    VerificationConfig,
    VerificationLoop,
    VerificationReport,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def default_config() -> VerificationConfig:
    """Standard 8-gate config."""
    return VerificationConfig()


@pytest.fixture
def loop(default_config: VerificationConfig) -> VerificationLoop:
    return VerificationLoop(config=default_config)


# ---------------------------------------------------------------------------
# Gate enum and GateResult
# ---------------------------------------------------------------------------


class TestGateEnum:
    def test_all_eight_gates_exist(self) -> None:
        expected = {"BUILD", "TYPES", "LINT", "TESTS", "SECURITY", "A11Y", "PERF", "DIFF"}
        actual = {g.name for g in Gate}
        assert expected == actual

    def test_gate_ordering(self) -> None:
        """Gates run in a specific order (build first, diff last)."""
        gates = list(Gate)
        assert gates[0] == Gate.BUILD
        assert gates[-1] == Gate.DIFF


class TestGateResult:
    def test_passed_result(self) -> None:
        result = GateResult(
            gate=Gate.BUILD,
            status=GateStatus.PASSED,
            message="Build successful",
        )
        assert result.passed is True
        assert result.gate == Gate.BUILD

    def test_failed_result(self) -> None:
        result = GateResult(
            gate=Gate.LINT,
            status=GateStatus.FAILED,
            message="3 lint errors",
            details=["E501: line too long", "W291: trailing whitespace"],
        )
        assert result.passed is False
        assert len(result.details) == 2

    def test_skipped_result(self) -> None:
        result = GateResult(
            gate=Gate.PERF,
            status=GateStatus.SKIPPED,
            message="No perf config",
        )
        assert result.passed is True  # skipped counts as pass


# ---------------------------------------------------------------------------
# VerificationConfig
# ---------------------------------------------------------------------------


class TestVerificationConfig:
    def test_default_config_has_all_gates_enabled(self, default_config: VerificationConfig) -> None:
        for gate in Gate:
            assert default_config.is_enabled(gate) is True

    def test_disable_gate(self) -> None:
        config = VerificationConfig(disabled_gates={Gate.PERF, Gate.A11Y})
        assert config.is_enabled(Gate.BUILD) is True
        assert config.is_enabled(Gate.PERF) is False
        assert config.is_enabled(Gate.A11Y) is False

    def test_max_retries_default(self, default_config: VerificationConfig) -> None:
        assert default_config.max_retries == 3

    def test_custom_thresholds(self) -> None:
        config = VerificationConfig(
            thresholds={"test_coverage": 90.0, "lighthouse_score": 80.0}
        )
        assert config.thresholds["test_coverage"] == 90.0


# ---------------------------------------------------------------------------
# Verification Loop — run_gate
# ---------------------------------------------------------------------------


class TestRunGate:
    @pytest.mark.asyncio
    async def test_run_single_gate_pass(self, loop: VerificationLoop) -> None:
        checker = AsyncMock(return_value=GateResult(
            gate=Gate.BUILD,
            status=GateStatus.PASSED,
            message="ok",
        ))
        result = await loop.run_gate(Gate.BUILD, checker)
        assert result.passed is True
        checker.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_single_gate_fail(self, loop: VerificationLoop) -> None:
        checker = AsyncMock(return_value=GateResult(
            gate=Gate.TESTS,
            status=GateStatus.FAILED,
            message="2 tests failed",
        ))
        result = await loop.run_gate(Gate.TESTS, checker)
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_run_disabled_gate_skips(self) -> None:
        config = VerificationConfig(disabled_gates={Gate.PERF})
        loop = VerificationLoop(config=config)
        checker = AsyncMock()
        result = await loop.run_gate(Gate.PERF, checker)
        assert result.status == GateStatus.SKIPPED
        checker.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_gate_exception_becomes_failure(self, loop: VerificationLoop) -> None:
        checker = AsyncMock(side_effect=RuntimeError("checker crashed"))
        result = await loop.run_gate(Gate.SECURITY, checker)
        assert result.passed is False
        assert "crashed" in result.message.lower() or "error" in result.message.lower()


# ---------------------------------------------------------------------------
# Verification Loop — full run
# ---------------------------------------------------------------------------


class TestFullRun:
    @pytest.mark.asyncio
    async def test_all_gates_pass(self, loop: VerificationLoop) -> None:
        """Mock all 8 checkers to pass."""
        checkers = {}
        for gate in Gate:
            checkers[gate] = AsyncMock(return_value=GateResult(
                gate=gate,
                status=GateStatus.PASSED,
                message=f"{gate.name} ok",
            ))

        report = await loop.run_all(checkers)
        assert report.all_green is True
        assert report.passed_count == 8
        assert report.failed_count == 0

    @pytest.mark.asyncio
    async def test_one_gate_fails(self, loop: VerificationLoop) -> None:
        """One failure means not green."""
        checkers = {}
        for gate in Gate:
            if gate == Gate.LINT:
                checkers[gate] = AsyncMock(return_value=GateResult(
                    gate=gate,
                    status=GateStatus.FAILED,
                    message="lint errors",
                ))
            else:
                checkers[gate] = AsyncMock(return_value=GateResult(
                    gate=gate,
                    status=GateStatus.PASSED,
                    message="ok",
                ))

        report = await loop.run_all(checkers)
        assert report.all_green is False
        assert report.failed_count == 1
        assert Gate.LINT in report.failed_gates

    @pytest.mark.asyncio
    async def test_missing_checker_skips(self, loop: VerificationLoop) -> None:
        """Gates without a checker are skipped, not failed."""
        # Only provide BUILD checker
        checkers = {
            Gate.BUILD: AsyncMock(return_value=GateResult(
                gate=Gate.BUILD,
                status=GateStatus.PASSED,
                message="ok",
            ))
        }
        report = await loop.run_all(checkers)
        # BUILD passed, rest skipped → all green (skipped = pass)
        assert report.all_green is True
        assert report.skipped_count == 7


# ---------------------------------------------------------------------------
# VerificationReport
# ---------------------------------------------------------------------------


class TestVerificationReport:
    def test_report_summary(self) -> None:
        results = [
            GateResult(gate=Gate.BUILD, status=GateStatus.PASSED, message="ok"),
            GateResult(gate=Gate.TYPES, status=GateStatus.PASSED, message="ok"),
            GateResult(gate=Gate.LINT, status=GateStatus.FAILED, message="bad"),
            GateResult(gate=Gate.TESTS, status=GateStatus.PASSED, message="ok"),
            GateResult(gate=Gate.SECURITY, status=GateStatus.SKIPPED, message="n/a"),
            GateResult(gate=Gate.A11Y, status=GateStatus.PASSED, message="ok"),
            GateResult(gate=Gate.PERF, status=GateStatus.PASSED, message="ok"),
            GateResult(gate=Gate.DIFF, status=GateStatus.PASSED, message="ok"),
        ]
        report = VerificationReport(results=results)
        assert report.all_green is False
        assert report.passed_count == 6
        assert report.failed_count == 1
        assert report.skipped_count == 1
        assert report.failed_gates == {Gate.LINT}

    def test_all_green_report(self) -> None:
        results = [
            GateResult(gate=g, status=GateStatus.PASSED, message="ok")
            for g in Gate
        ]
        report = VerificationReport(results=results)
        assert report.all_green is True

    def test_to_dict(self) -> None:
        results = [
            GateResult(gate=Gate.BUILD, status=GateStatus.PASSED, message="ok"),
        ]
        report = VerificationReport(results=results)
        d = report.to_dict()
        assert "all_green" in d
        assert "gates" in d
        assert isinstance(d["gates"], list)
