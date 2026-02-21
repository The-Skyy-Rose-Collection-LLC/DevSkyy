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
        diagnosis = await healer.diagnose("Missing config env setting for provider")
        assert diagnosis.category == FailureCategory.CONFIG

    @pytest.mark.asyncio
    async def test_diagnose_external(self):
        healer = SelfHealer()
        diagnosis = await healer.diagnose("Connection timeout to server")
        assert diagnosis.category == FailureCategory.EXTERNAL
        assert diagnosis.fixable is False

    @pytest.mark.asyncio
    async def test_diagnose_wrong_approach(self):
        """
        Verifies that SelfHealer.diagnose classifies a message indicating an incorrect approach as WRONG_APPROACH.
        
        This test creates a SelfHealer instance, diagnoses the string "This approach does not work", and asserts the returned diagnosis category is FailureCategory.WRONG_APPROACH.
        """
        healer = SelfHealer()
        diagnosis = await healer.diagnose("This approach does not work")
        assert diagnosis.category == FailureCategory.WRONG_APPROACH

    @pytest.mark.asyncio
    async def test_diagnose_security(self):
        healer = SelfHealer()
        diagnosis = await healer.diagnose("SECRET: Possible API key found")
        assert diagnosis.category == FailureCategory.SECURITY

    @pytest.mark.asyncio
    async def test_diagnose_lint(self):
        healer = SelfHealer()
        diagnosis = await healer.diagnose("Lint: console.log found")
        assert diagnosis.category == FailureCategory.LINT

    @pytest.mark.asyncio
    async def test_diagnose_a11y(self):
        healer = SelfHealer()
        diagnosis = await healer.diagnose("a11y: img tag missing alt attribute")
        assert diagnosis.category == FailureCategory.A11Y

    @pytest.mark.asyncio
    async def test_history_tracked(self):
        healer = SelfHealer()
        await healer.diagnose("error 1")
        await healer.diagnose("error 2")
        assert len(healer.history) == 2

    @pytest.mark.asyncio
    async def test_heal_code_bug_unchanged(self):
        healer = SelfHealer()
        diagnosis = Diagnosis(
            category=FailureCategory.CODE_BUG,
            error_details="test",
            suggested_fix="fix it",
        )
        result = await healer.heal("original content", diagnosis)
        assert result == "original content"  # No auto-healer for code bugs

    @pytest.mark.asyncio
    async def test_heal_lint_removes_console_log(self):
        healer = SelfHealer()
        diagnosis = Diagnosis(
            category=FailureCategory.LINT,
            error_details="console.log found",
            suggested_fix="Remove console.log",
        )
        content = "const x = 1;\nconsole.log(x);\nreturn x;"
        result = await healer.heal(content, diagnosis)
        assert "console.log" not in result
        assert "const x = 1;" in result

    @pytest.mark.asyncio
    async def test_heal_security_replaces_innerhtml(self):
        healer = SelfHealer()
        diagnosis = Diagnosis(
            category=FailureCategory.SECURITY,
            error_details="innerHTML assignment",
            suggested_fix="Use textContent",
        )
        content = "el.innerHTML = userInput;"
        result = await healer.heal(content, diagnosis)
        assert "textContent" in result

    @pytest.mark.asyncio
    async def test_heal_a11y_adds_alt(self):
        healer = SelfHealer()
        diagnosis = Diagnosis(
            category=FailureCategory.A11Y,
            error_details="img missing alt",
            suggested_fix="Add alt attribute",
        )
        content = '<img src="photo.jpg">'
        result = await healer.heal(content, diagnosis)
        assert 'alt=""' in result

    @pytest.mark.asyncio
    async def test_heal_external_unchanged(self):
        healer = SelfHealer()
        diagnosis = Diagnosis(
            category=FailureCategory.EXTERNAL,
            error_details="timeout",
            suggested_fix="retry",
            fixable=False,
        )
        result = await healer.heal("original", diagnosis)
        assert result == "original"


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
    async def test_all_gates_pass_clean_content(self):
        vl = VerificationLoop()
        result = await vl.run("This is clean agent output with no code blocks at all.")
        assert result.all_green is True
        assert len(result.gates) == 8

    @pytest.mark.asyncio
    async def test_gate_names(self):
        vl = VerificationLoop()
        result = await vl.run("Enough content to pass the diff gate check easily.")
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

    # ── BUILD gate ──

    @pytest.mark.asyncio
    async def test_build_gate_valid_python(self):
        vl = VerificationLoop()
        content = "Here is code:\n```python\ndef hello():\n    return 42\n```\nDone."
        result = await vl.run(content)
        build = next(g for g in result.gates if g.gate == "build")
        assert build.status == GateStatus.PASSED

    @pytest.mark.asyncio
    async def test_build_gate_invalid_python(self):
        vl = VerificationLoop()
        content = "Code:\n```python\ndef hello(\n```\nDone with enough text here."
        result = await vl.run(content)
        build = next(g for g in result.gates if g.gate == "build")
        assert build.status == GateStatus.FAILED
        assert "syntax" in build.message.lower() or "build" in build.message.lower()

    @pytest.mark.asyncio
    async def test_build_gate_invalid_json(self):
        vl = VerificationLoop()
        content = "Config:\n```json\n{invalid json}\n```\nSome extra text padding."
        result = await vl.run(content)
        build = next(g for g in result.gates if g.gate == "build")
        assert build.status == GateStatus.FAILED

    # ── TYPES gate ──

    @pytest.mark.asyncio
    async def test_types_gate_any_in_typescript(self):
        vl = VerificationLoop()
        content = "TS:\n```typescript\nconst x: any = 5;\n```\nSome padding text here."
        result = await vl.run(content)
        types = next(g for g in result.gates if g.gate == "types")
        assert types.status == GateStatus.FAILED
        assert "any" in types.details.get("errors", [""])[0].lower()

    # ── LINT gate ──

    @pytest.mark.asyncio
    async def test_lint_gate_console_log(self):
        vl = VerificationLoop()
        content = "JS:\n```javascript\nconsole.log('debug');\n```\nSome extra text to pass."
        result = await vl.run(content)
        lint = next(g for g in result.gates if g.gate == "lint")
        assert lint.status == GateStatus.FAILED

    @pytest.mark.asyncio
    async def test_lint_gate_clean_code(self):
        vl = VerificationLoop()
        content = "JS:\n```javascript\nconst x = 5;\n```\nExtra text to pass diff gate."
        result = await vl.run(content)
        lint = next(g for g in result.gates if g.gate == "lint")
        assert lint.status == GateStatus.PASSED

    # ── SECURITY gate ──

    @pytest.mark.asyncio
    async def test_security_gate_detects_secret(self):
        vl = VerificationLoop()
        content = 'Config: api_key = "sk-proj-abcdef1234567890ABCDEF" plus padding.'
        result = await vl.run(content)
        sec = next(g for g in result.gates if g.gate == "security")
        assert sec.status == GateStatus.FAILED
        assert any("SECRET" in f for f in sec.details.get("findings", []))

    @pytest.mark.asyncio
    async def test_security_gate_detects_innerhtml(self):
        vl = VerificationLoop()
        content = "Code:\n```javascript\nel.innerHTML = userInput;\n```\nExtra text to pass."
        result = await vl.run(content)
        sec = next(g for g in result.gates if g.gate == "security")
        assert sec.status == GateStatus.FAILED

    # ── A11Y gate ──

    @pytest.mark.asyncio
    async def test_a11y_gate_missing_alt(self):
        vl = VerificationLoop()
        content = 'HTML:\n```html\n<h1>Page</h1>\n<img src="photo.jpg">\n```\nExtra text.'
        result = await vl.run(content)
        a11y = next(g for g in result.gates if g.gate == "a11y")
        assert a11y.status == GateStatus.FAILED
        assert any("alt" in v for v in a11y.details.get("violations", []))

    @pytest.mark.asyncio
    async def test_a11y_gate_with_alt(self):
        vl = VerificationLoop()
        content = 'HTML:\n```html\n<h1>Page</h1>\n<img src="photo.jpg" alt="A photo">\n```\nText.'
        result = await vl.run(content)
        a11y = next(g for g in result.gates if g.gate == "a11y")
        assert a11y.status == GateStatus.PASSED

    # ── PERF gate ──

    @pytest.mark.asyncio
    async def test_perf_gate_wildcard_import(self):
        vl = VerificationLoop()
        content = "JS:\n```javascript\nimport * as utils from 'utils';\n```\nExtra text here."
        result = await vl.run(content)
        perf = next(g for g in result.gates if g.gate == "perf")
        assert perf.status == GateStatus.FAILED

    # ── DIFF gate ──

    @pytest.mark.asyncio
    async def test_diff_gate_empty_content(self):
        vl = VerificationLoop()
        result = await vl.run("")
        diff = next(g for g in result.gates if g.gate == "diff")
        assert diff.status == GateStatus.FAILED

    @pytest.mark.asyncio
    async def test_diff_gate_too_short(self):
        vl = VerificationLoop()
        result = await vl.run("short")
        diff = next(g for g in result.gates if g.gate == "diff")
        assert diff.status == GateStatus.FAILED

    @pytest.mark.asyncio
    async def test_diff_gate_ground_truth_match(self):
        vl = VerificationLoop()
        result = await vl.run(
            "The design system uses #B76E79 as the primary color.",
            context={"ground_truth": ["#B76E79"]},
        )
        diff = next(g for g in result.gates if g.gate == "diff")
        assert diff.status == GateStatus.PASSED

    @pytest.mark.asyncio
    async def test_diff_gate_ground_truth_mismatch(self):
        vl = VerificationLoop()
        result = await vl.run(
            "The color is blue with some extra padding text.",
            context={"ground_truth": ["#B76E79"]},
        )
        diff = next(g for g in result.gates if g.gate == "diff")
        assert diff.status == GateStatus.FAILED

    # ── Gate config ──

    @pytest.mark.asyncio
    async def test_disabled_gate_skipped(self):
        vl = VerificationLoop(config={"gates": {"build": {"enabled": False}}})
        result = await vl.run("Agent output with enough content to pass.")
        build = next(g for g in result.gates if g.gate == "build")
        assert build.status == GateStatus.SKIPPED


# =============================================================================
# Ralph Integration
# =============================================================================


class TestRalphExecutor:
    @pytest.mark.asyncio
    async def test_success_first_try(self):
        executor = RalphExecutor()

        async def success():
            """
            Return a success indicator.
            
            Returns:
                str: The literal string 'result' indicating success.
            """
            return "result"

        result = await executor.execute(success)
        assert result == "result"

    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        executor = RalphExecutor(max_attempts=3, base_delay=0.01)
        call_count = 0

        async def flaky():
            """
            Simulate a flaky operation that fails twice before succeeding.
            
            Returns:
                str: "success" once the function has been called three or more times.
            
            Raises:
                RuntimeError: If invoked fewer than three times.
            """
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
            """
            Always raises a RuntimeError.
            
            Raises:
                RuntimeError: Always raised with the message "always fails".
            """
            raise RuntimeError("always fails")

        with pytest.raises(RuntimeError, match="All attempts exhausted"):
            await executor.execute(always_fail)

    @pytest.mark.asyncio
    async def test_fallback_used(self):
        executor = RalphExecutor(max_attempts=1, base_delay=0.01)

        async def primary():
            """
            Coroutine that always raises a RuntimeError.
            
            Raises:
                RuntimeError: Always raised with the message "primary fails".
            """
            raise RuntimeError("primary fails")

        async def fallback():
            """
            Provide a default fallback result string.
            
            Returns:
                The string "fallback result".
            """
            return "fallback result"

        result = await executor.execute(primary, fallbacks=[fallback])
        assert result == "fallback result"


# =============================================================================
# Model Router Health
# =============================================================================


class TestProviderHealth:
    def test_initial_healthy(self):
        """
        Verifies that a newly created ProviderHealth has status ProviderStatus.HEALTHY and zero consecutive failures.
        
        Asserts that:
        - `status` equals `ProviderStatus.HEALTHY`
        - `consecutive_failures` equals 0
        """
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