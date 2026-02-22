"""Tests for core/self_healer.py — Diagnose → categorize → route → retry loop."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from core.self_healer import (
    Diagnosis,
    FailureCategory,
    HealAttempt,
    HealResult,
    SelfHealer,
)
from core.verification_loop import (
    Gate,
    GateResult,
    GateStatus,
    VerificationReport,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def healer() -> SelfHealer:
    return SelfHealer(max_attempts=3)


@pytest.fixture
def failing_report() -> VerificationReport:
    """A report where LINT and TESTS fail."""
    return VerificationReport(results=[
        GateResult(gate=Gate.BUILD, status=GateStatus.PASSED, message="ok"),
        GateResult(gate=Gate.TYPES, status=GateStatus.PASSED, message="ok"),
        GateResult(gate=Gate.LINT, status=GateStatus.FAILED, message="3 errors",
                   details=["E501", "W291", "E303"]),
        GateResult(gate=Gate.TESTS, status=GateStatus.FAILED, message="2 failures",
                   details=["test_foo FAILED", "test_bar FAILED"]),
        GateResult(gate=Gate.SECURITY, status=GateStatus.PASSED, message="ok"),
        GateResult(gate=Gate.A11Y, status=GateStatus.PASSED, message="ok"),
        GateResult(gate=Gate.PERF, status=GateStatus.PASSED, message="ok"),
        GateResult(gate=Gate.DIFF, status=GateStatus.PASSED, message="ok"),
    ])


# ---------------------------------------------------------------------------
# FailureCategory
# ---------------------------------------------------------------------------


class TestFailureCategory:
    def test_all_categories_exist(self) -> None:
        expected = {"CODE_BUG", "CONFIG", "WRONG_APPROACH", "EXTERNAL"}
        actual = {c.name for c in FailureCategory}
        assert expected == actual


# ---------------------------------------------------------------------------
# Diagnosis
# ---------------------------------------------------------------------------


class TestDiagnosis:
    def test_diagnose_lint_failure(self, healer: SelfHealer, failing_report: VerificationReport) -> None:
        diagnosis = healer.diagnose(failing_report)
        assert isinstance(diagnosis, Diagnosis)
        assert len(diagnosis.failed_gates) >= 1

    def test_diagnose_all_pass_returns_none(self, healer: SelfHealer) -> None:
        report = VerificationReport(results=[
            GateResult(gate=g, status=GateStatus.PASSED, message="ok")
            for g in Gate
        ])
        diagnosis = healer.diagnose(report)
        assert diagnosis is None  # Nothing to heal

    def test_diagnosis_categorizes_lint_as_code_bug(self, healer: SelfHealer, failing_report: VerificationReport) -> None:
        diagnosis = healer.diagnose(failing_report)
        assert diagnosis is not None
        # Lint failures are code bugs
        assert any(
            fc.category == FailureCategory.CODE_BUG
            for fc in diagnosis.failure_analyses
        )

    def test_diagnosis_has_suggested_actions(self, healer: SelfHealer, failing_report: VerificationReport) -> None:
        diagnosis = healer.diagnose(failing_report)
        assert diagnosis is not None
        assert len(diagnosis.suggested_actions) > 0


# ---------------------------------------------------------------------------
# Heal cycle
# ---------------------------------------------------------------------------


class TestHealCycle:
    @pytest.mark.asyncio
    async def test_heal_success_on_first_try(self, healer: SelfHealer) -> None:
        """Fixer succeeds on first attempt."""
        fixer = AsyncMock(return_value=HealResult(
            success=True,
            message="Fixed lint errors",
            changes=["formatted file.py"],
        ))
        verifier = AsyncMock(return_value=VerificationReport(results=[
            GateResult(gate=g, status=GateStatus.PASSED, message="ok")
            for g in Gate
        ]))

        diagnosis = Diagnosis(
            failed_gates={Gate.LINT},
            failure_analyses=[
                HealAttempt(
                    gate=Gate.LINT,
                    category=FailureCategory.CODE_BUG,
                    description="lint errors",
                )
            ],
            suggested_actions=["run formatter"],
        )

        result = await healer.heal(diagnosis, fixer=fixer, verifier=verifier)
        assert result.success is True
        assert result.attempts == 1
        fixer.assert_called_once()

    @pytest.mark.asyncio
    async def test_heal_retries_on_failure(self, healer: SelfHealer) -> None:
        """Fixer fails first, succeeds second."""
        call_count = 0

        async def fixer(diagnosis):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return HealResult(success=False, message="still broken")
            return HealResult(success=True, message="fixed")

        verifier = AsyncMock(return_value=VerificationReport(results=[
            GateResult(gate=g, status=GateStatus.PASSED, message="ok")
            for g in Gate
        ]))

        diagnosis = Diagnosis(
            failed_gates={Gate.TESTS},
            failure_analyses=[
                HealAttempt(gate=Gate.TESTS, category=FailureCategory.CODE_BUG, description="test failures"),
            ],
            suggested_actions=["fix tests"],
        )

        result = await healer.heal(diagnosis, fixer=fixer, verifier=verifier)
        assert result.success is True
        assert result.attempts == 2

    @pytest.mark.asyncio
    async def test_heal_exhausts_retries(self, healer: SelfHealer) -> None:
        """After max_attempts, returns failure."""
        fixer = AsyncMock(return_value=HealResult(success=False, message="can't fix"))
        verifier = AsyncMock(return_value=VerificationReport(results=[
            GateResult(gate=Gate.BUILD, status=GateStatus.FAILED, message="broken"),
        ]))

        diagnosis = Diagnosis(
            failed_gates={Gate.BUILD},
            failure_analyses=[
                HealAttempt(gate=Gate.BUILD, category=FailureCategory.WRONG_APPROACH, description="build broken"),
            ],
            suggested_actions=["rewrite"],
        )

        result = await healer.heal(diagnosis, fixer=fixer, verifier=verifier)
        assert result.success is False
        assert result.attempts == 3  # max_attempts
        assert result.escalation_needed is True

    @pytest.mark.asyncio
    async def test_heal_with_verifier_recheck(self, healer: SelfHealer) -> None:
        """After fix, verifier re-runs and confirms green."""
        fixer = AsyncMock(return_value=HealResult(success=True, message="patched"))

        # First verify: fail, second verify: pass
        verify_results = [
            VerificationReport(results=[
                GateResult(gate=Gate.SECURITY, status=GateStatus.FAILED, message="secret found"),
            ]),
            VerificationReport(results=[
                GateResult(gate=g, status=GateStatus.PASSED, message="ok")
                for g in Gate
            ]),
        ]
        verifier = AsyncMock(side_effect=verify_results)

        diagnosis = Diagnosis(
            failed_gates={Gate.SECURITY},
            failure_analyses=[
                HealAttempt(gate=Gate.SECURITY, category=FailureCategory.CODE_BUG, description="leaked secret"),
            ],
            suggested_actions=["remove secret"],
        )

        result = await healer.heal(diagnosis, fixer=fixer, verifier=verifier)
        assert result.success is True


# ---------------------------------------------------------------------------
# Category routing
# ---------------------------------------------------------------------------


class TestCategoryRouting:
    def test_categorize_build_failure(self, healer: SelfHealer) -> None:
        gate_result = GateResult(
            gate=Gate.BUILD, status=GateStatus.FAILED,
            message="SyntaxError in main.py",
        )
        category = healer.categorize(gate_result)
        assert category == FailureCategory.CODE_BUG

    def test_categorize_security_failure_secret(self, healer: SelfHealer) -> None:
        """API key in source → CONFIG (should be in env vars, not source)."""
        gate_result = GateResult(
            gate=Gate.SECURITY, status=GateStatus.FAILED,
            message="API key found in source",
        )
        category = healer.categorize(gate_result)
        assert category == FailureCategory.CONFIG

    def test_categorize_security_failure_xss(self, healer: SelfHealer) -> None:
        """XSS vulnerability → CODE_BUG (code needs fixing)."""
        gate_result = GateResult(
            gate=Gate.SECURITY, status=GateStatus.FAILED,
            message="Unsanitized user input in template",
        )
        category = healer.categorize(gate_result)
        assert category == FailureCategory.CODE_BUG

    def test_categorize_perf_failure(self, healer: SelfHealer) -> None:
        gate_result = GateResult(
            gate=Gate.PERF, status=GateStatus.FAILED,
            message="Lighthouse score 45 (threshold: 80)",
        )
        category = healer.categorize(gate_result)
        # Performance issues might need a different approach
        assert category in (FailureCategory.CODE_BUG, FailureCategory.WRONG_APPROACH)
