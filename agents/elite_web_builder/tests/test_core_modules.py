"""
Tests for core modules: ground_truth, self_healer, learning_journal,
verification_loop, ralph_integration.
"""

from __future__ import annotations

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

from elite_web_builder.core.ground_truth import GroundTruthValidator
from elite_web_builder.core.self_healer import (
    Diagnosis,
    FailureCategory,
    SelfHealer,
)
from elite_web_builder.core.learning_journal import (
    LearningEntry,
    LearningJournal,
)
from elite_web_builder.core.verification_loop import (
    GateName,
    GateResult,
    GateStatus,
    VerificationLoop,
    VerificationResult,
)
from elite_web_builder.core.ralph_integration import RalphExecutor
from elite_web_builder.core.model_router import (
    LLMResponse,
    ModelRouter,
    ProviderHealth,
    ProviderStatus,
)


# =============================================================================
# Ground Truth Validator
# =============================================================================


class TestGroundTruthValidator:
    def test_validate_valid_json(self):
        v = GroundTruthValidator()
        assert v.validate_json('{"key": "value"}') is True

    def test_validate_invalid_json(self):
        v = GroundTruthValidator()
        assert v.validate_json("not json") is False

    def test_validate_color_hex_valid(self):
        v = GroundTruthValidator()
        assert v.validate_color_hex("#B76E79") is True
        assert v.validate_color_hex("#fff") is True
        assert v.validate_color_hex("#FF0000FF") is True

    def test_validate_color_hex_invalid(self):
        v = GroundTruthValidator()
        assert v.validate_color_hex("B76E79") is False  # Missing #
        assert v.validate_color_hex("#GGG") is False  # Invalid chars

    def test_validate_theme_json_valid(self):
        v = GroundTruthValidator()
        theme = json.dumps({
            "$schema": "https://schemas.wp.org/trunk/theme.json",
            "version": 2,
            "settings": {
                "color": {
                    "palette": [
                        {"slug": "primary", "name": "Primary", "color": "#B76E79"}
                    ]
                }
            },
        })
        valid, errors = v.validate_theme_json(theme)
        assert valid is True
        assert errors == []

    def test_validate_theme_json_missing_version(self):
        v = GroundTruthValidator()
        theme = json.dumps({"$schema": "test"})
        valid, errors = v.validate_theme_json(theme)
        assert valid is False
        assert any("version" in e for e in errors)

    def test_validate_theme_json_duplicate_slugs(self):
        v = GroundTruthValidator()
        theme = json.dumps({
            "version": 2,
            "$schema": "test",
            "settings": {
                "color": {
                    "palette": [
                        {"slug": "primary", "name": "A", "color": "#000"},
                        {"slug": "primary", "name": "B", "color": "#fff"},
                    ]
                }
            },
        })
        valid, errors = v.validate_theme_json(theme)
        assert valid is False
        assert any("Duplicate" in e for e in errors)

    def test_validate_liquid_syntax_balanced(self):
        v = GroundTruthValidator()
        content = "{% if true %}{{ product.title }}{% endif %}"
        valid, errors = v.validate_liquid_syntax(content)
        assert valid is True

    def test_validate_liquid_syntax_unbalanced(self):
        v = GroundTruthValidator()
        content = "{% if true %}{{ product.title }"
        valid, errors = v.validate_liquid_syntax(content)
        assert valid is False

    def test_validate_file_reference(self):
        v = GroundTruthValidator(project_root=Path(__file__).parent.parent)
        assert v.validate_file_reference("director.py") is True
        assert v.validate_file_reference("nonexistent.py") is False


# =============================================================================
# Self Healer
# =============================================================================


class TestSelfHealer:
    @pytest.mark.asyncio
    async def test_diagnose_code_bug(self):
        healer = SelfHealer()
        diagnosis = await healer.diagnose("SyntaxError: unexpected indent")
        assert diagnosis.category == FailureCategory.CODE_BUG

    @pytest.mark.asyncio
    async def test_diagnose_config(self):
        healer = SelfHealer()
        diagnosis = await healer.diagnose("Missing config variable: API_KEY")
        assert diagnosis.category == FailureCategory.CONFIG

    @pytest.mark.asyncio
    async def test_diagnose_external(self):
        healer = SelfHealer()
        diagnosis = await healer.diagnose("Connection timeout to API server")
        assert diagnosis.category == FailureCategory.EXTERNAL

    @pytest.mark.asyncio
    async def test_diagnose_wrong_approach(self):
        healer = SelfHealer()
        diagnosis = await healer.diagnose("This approach does not work")
        assert diagnosis.category == FailureCategory.WRONG_APPROACH

    @pytest.mark.asyncio
    async def test_history_tracked(self):
        healer = SelfHealer()
        await healer.diagnose("error 1")
        await healer.diagnose("error 2")
        assert len(healer.history) == 2

    @pytest.mark.asyncio
    async def test_heal_returns_content(self):
        healer = SelfHealer()
        diagnosis = Diagnosis(
            category=FailureCategory.CODE_BUG,
            error_details="test",
            suggested_fix="fix it",
        )
        result = await healer.heal("original", diagnosis)
        assert result == "original"  # Default implementation returns unchanged


# =============================================================================
# Learning Journal
# =============================================================================


class TestLearningJournal:
    def test_add_entry(self):
        journal = LearningJournal()
        entry = LearningEntry(
            mistake="Used wrong color",
            correct="Use #B76E79",
            agent="design_system",
            story_id="US-001",
        )
        journal.add_entry(entry)
        assert len(journal.entries) == 1

    def test_get_rules_for_agent(self):
        journal = LearningJournal()
        journal.add_entry(LearningEntry(
            mistake="bad practice",
            correct="good practice",
            agent="design_system",
            story_id="US-001",
        ))
        journal.add_entry(LearningEntry(
            mistake="other issue",
            correct="other fix",
            agent="frontend_dev",
            story_id="US-002",
        ))
        rules = journal.get_rules_for_agent("design_system")
        assert len(rules) == 1
        assert "bad practice" in rules[0]

    def test_persistence(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = Path(f.name)

        try:
            # Write
            journal = LearningJournal(path=path)
            journal.add_entry(LearningEntry(
                mistake="test",
                correct="test fix",
                agent="qa",
                story_id="US-001",
            ))

            # Read back
            journal2 = LearningJournal(path=path)
            assert len(journal2.entries) == 1
        finally:
            path.unlink(missing_ok=True)

    def test_entry_to_rule(self):
        entry = LearningEntry(
            mistake="bad",
            correct="good",
            agent="qa",
            story_id="US-001",
        )
        rule = entry.to_rule()
        assert "bad" in rule
        assert "good" in rule


# =============================================================================
# Verification Loop
# =============================================================================


class TestVerificationLoop:
    @pytest.mark.asyncio
    async def test_all_gates_pass(self):
        vl = VerificationLoop()
        result = await vl.run("test content")
        assert result.all_green is True
        assert len(result.gates) == 8

    @pytest.mark.asyncio
    async def test_gate_names(self):
        vl = VerificationLoop()
        result = await vl.run("content")
        gate_names = {g.gate for g in result.gates}
        expected = {"build", "types", "lint", "tests", "security", "a11y", "perf", "diff"}
        assert gate_names == expected

    def test_verification_result_summary(self):
        result = VerificationResult(gates=[
            GateResult(gate="build", status=GateStatus.PASSED),
            GateResult(gate="tests", status=GateStatus.FAILED),
        ])
        assert result.all_green is False
        assert len(result.failures) == 1
        assert result.summary == {"passed": 1, "failed": 1}


# =============================================================================
# Ralph Integration
# =============================================================================


class TestRalphExecutor:
    @pytest.mark.asyncio
    async def test_success_first_try(self):
        executor = RalphExecutor()

        async def success():
            return "result"

        result = await executor.execute(success)
        assert result == "result"

    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        executor = RalphExecutor(max_attempts=3, base_delay=0.01)
        call_count = 0

        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("flaky")
            return "success"

        result = await executor.execute(flaky)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_all_attempts_fail(self):
        executor = RalphExecutor(max_attempts=2, base_delay=0.01)

        async def always_fail():
            raise RuntimeError("always fails")

        with pytest.raises(RuntimeError, match="All attempts exhausted"):
            await executor.execute(always_fail)

    @pytest.mark.asyncio
    async def test_fallback_used(self):
        executor = RalphExecutor(max_attempts=1, base_delay=0.01)

        async def primary():
            raise RuntimeError("primary fails")

        async def fallback():
            return "fallback result"

        result = await executor.execute(primary, fallbacks=[fallback])
        assert result == "fallback result"


# =============================================================================
# Model Router Health
# =============================================================================


class TestProviderHealth:
    def test_initial_healthy(self):
        health = ProviderHealth(provider="test")
        assert health.status == ProviderStatus.HEALTHY
        assert health.consecutive_failures == 0

    def test_record_success(self):
        health = ProviderHealth(provider="test")
        health.record_failure()
        health.record_success()
        assert health.status == ProviderStatus.HEALTHY
        assert health.consecutive_failures == 0

    def test_degraded_after_one_failure(self):
        health = ProviderHealth(provider="test")
        health.record_failure()
        assert health.status == ProviderStatus.DEGRADED

    def test_down_after_three_failures(self):
        health = ProviderHealth(provider="test")
        health.record_failure()
        health.record_failure()
        health.record_failure()
        assert health.status == ProviderStatus.DOWN
