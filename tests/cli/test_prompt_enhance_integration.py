"""
Integration Tests for Prompt Enhancer CLI (US-012)
==================================================

Integration tests that verify real Claude API enhancement.
These tests require ANTHROPIC_API_KEY to be set.

Run with: pytest tests/cli/test_prompt_enhance_integration.py -v -m integration
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

import pytest
from click.testing import CliRunner

from cli.prompt_enhance import (
    PromptAnalyzer,
    PromptEnhancer,
    PromptTechnique,
    TechniqueSelector,
    main,
)

if TYPE_CHECKING:
    pass


# Skip all tests in this module if ANTHROPIC_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set - skipping integration tests",
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.integration
class TestClaudeAPIIntegration:
    """Integration tests with real Claude API calls."""

    def test_enhance_with_real_api(self) -> None:
        """Test enhancement with real Claude API."""
        # Setup
        analyzer = PromptAnalyzer()
        selector = TechniqueSelector()
        enhancer = PromptEnhancer()

        prompt = "Fix the login bug"
        analysis = analyzer.analyze(prompt)
        techniques = selector.select(analysis)

        # Execute
        enhanced = enhancer.enhance(prompt, analysis, techniques, "")

        # Verify
        assert len(enhanced) > len(prompt)
        assert isinstance(enhanced, str)
        # Enhanced prompt should have more structure
        assert any(
            marker in enhanced.lower()
            for marker in ["step", "task", "context", "output", "requirement", "#", "-"]
        )

    def test_code_task_enhancement(self) -> None:
        """Test that code tasks produce appropriate enhancements."""
        analyzer = PromptAnalyzer()
        selector = TechniqueSelector()
        enhancer = PromptEnhancer()

        prompt = "Implement a REST API endpoint for user authentication"
        analysis = analyzer.analyze(prompt)
        techniques = selector.select(analysis)

        enhanced = enhancer.enhance(prompt, analysis, techniques, "")

        assert len(enhanced) > len(prompt)
        # Should contain code-related structure
        assert any(
            word in enhanced.lower()
            for word in [
                "implement",
                "api",
                "authentication",
                "endpoint",
                "code",
                "function",
                "class",
            ]
        )

    def test_debug_task_enhancement(self) -> None:
        """Test that debug tasks produce appropriate enhancements."""
        analyzer = PromptAnalyzer()
        selector = TechniqueSelector()
        enhancer = PromptEnhancer()

        prompt = "Debug the crash that happens when users submit empty forms"
        analysis = analyzer.analyze(prompt)
        techniques = selector.select(analysis)

        enhanced = enhancer.enhance(prompt, analysis, techniques, "")

        assert len(enhanced) > len(prompt)
        # Should maintain debug context
        assert any(
            word in enhanced.lower() for word in ["debug", "crash", "error", "fix", "issue", "form"]
        )

    def test_refactor_task_enhancement(self) -> None:
        """Test that refactor tasks produce appropriate enhancements."""
        analyzer = PromptAnalyzer()
        selector = TechniqueSelector()
        enhancer = PromptEnhancer()

        prompt = "Refactor the database module to use async/await"
        analysis = analyzer.analyze(prompt)
        techniques = selector.select(analysis)

        enhanced = enhancer.enhance(prompt, analysis, techniques, "")

        assert len(enhanced) > len(prompt)
        assert any(word in enhanced.lower() for word in ["refactor", "database", "async", "module"])


@pytest.mark.integration
class TestCLIIntegration:
    """CLI integration tests with real API calls."""

    def test_cli_enhancement_plain_format(self, runner: CliRunner) -> None:
        """Test CLI enhancement with plain output format."""
        result = runner.invoke(
            main,
            ["--no-log", "Explain how to implement binary search"],
        )

        assert result.exit_code == 0
        assert len(result.output) > 0
        # Should produce a non-trivial enhanced prompt
        assert len(result.output) > 50

    def test_cli_enhancement_json_format(self, runner: CliRunner) -> None:
        """Test CLI enhancement with JSON output format."""
        result = runner.invoke(
            main,
            ["--format", "json", "--no-log", "Optimize this database query"],
        )

        assert result.exit_code == 0

        # Should be valid JSON
        data = json.loads(result.output)

        # Verify structure
        assert "original" in data
        assert "enhanced" in data
        assert "analysis" in data
        assert "techniques" in data

        # Enhanced should be longer
        assert len(data["enhanced"]) > len(data["original"])

        # Analysis should have proper fields
        assert "task_type" in data["analysis"]
        assert "clarity_score" in data["analysis"]

        # Techniques should be applied
        assert "applied" in data["techniques"]
        assert len(data["techniques"]["applied"]) > 0

    def test_cli_enhancement_markdown_format(self, runner: CliRunner) -> None:
        """Test CLI enhancement with markdown output format."""
        result = runner.invoke(
            main,
            ["--format", "md", "--no-log", "Add logging to the application"],
        )

        assert result.exit_code == 0
        assert "# Enhanced Prompt" in result.output
        assert "**Task Type:**" in result.output
        assert "**Techniques:**" in result.output

    def test_cli_preview_mode(self, runner: CliRunner) -> None:
        """Test CLI preview mode shows comparison."""
        result = runner.invoke(
            main,
            ["--preview", "--no-log", "Fix the memory leak"],
        )

        assert result.exit_code == 0
        assert "ORIGINAL" in result.output
        assert "ENHANCED" in result.output

    def test_cli_auto_mode(self, runner: CliRunner) -> None:
        """Test CLI auto mode outputs only enhanced prompt."""
        result = runner.invoke(
            main,
            ["--auto", "--no-log", "Write unit tests for the API"],
        )

        assert result.exit_code == 0
        # Should not contain metadata markers
        assert "ORIGINAL" not in result.output
        assert "Task:" not in result.output
        # Should have substantial output
        assert len(result.output.strip()) > 50

    def test_cli_with_explicit_mode(self, runner: CliRunner) -> None:
        """Test CLI with explicit mode override."""
        result = runner.invoke(
            main,
            ["--mode", "creative", "--format", "json", "--no-log", "design something"],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)

        # Mode should be overridden
        assert data["analysis"]["task_type"] == "creative"


@pytest.mark.integration
class TestEnhancementQuality:
    """Tests for enhancement quality verification."""

    def test_enhanced_prompt_is_structurally_valid(self) -> None:
        """Verify enhanced prompts have good structure."""
        analyzer = PromptAnalyzer()
        selector = TechniqueSelector()
        enhancer = PromptEnhancer()

        prompt = "help me write code"
        analysis = analyzer.analyze(prompt)
        techniques = selector.select(analysis)

        enhanced = enhancer.enhance(prompt, analysis, techniques, "")

        # Should be substantially longer
        assert len(enhanced) > len(prompt) * 2

        # Should have some structure (headers, lists, etc.)
        structural_markers = ["#", "-", "*", "1.", ":", "**", "```", "\n\n"]
        has_structure = any(marker in enhanced for marker in structural_markers)
        assert has_structure, "Enhanced prompt should have structural markers"

    def test_enhanced_prompt_preserves_intent(self) -> None:
        """Verify enhanced prompts preserve the original intent."""
        analyzer = PromptAnalyzer()
        selector = TechniqueSelector()
        enhancer = PromptEnhancer()

        # Test various prompts
        test_cases = [
            ("implement user authentication", ["authentication", "user"]),
            ("fix the database connection bug", ["database", "bug"]),
            ("refactor to use dependency injection", ["refactor", "dependency"]),
        ]

        for prompt, expected_keywords in test_cases:
            analysis = analyzer.analyze(prompt)
            techniques = selector.select(analysis)
            enhanced = enhancer.enhance(prompt, analysis, techniques, "")

            # At least one expected keyword should be preserved
            enhanced_lower = enhanced.lower()
            has_keyword = any(kw in enhanced_lower for kw in expected_keywords)
            assert has_keyword, f"Enhanced prompt lost intent from: {prompt}"

    def test_technique_application_visible(self) -> None:
        """Verify that selected techniques are applied in the enhancement."""
        analyzer = PromptAnalyzer()
        selector = TechniqueSelector()
        enhancer = PromptEnhancer()

        # Debug task should use chain-of-thought
        prompt = "Debug the crash"
        analysis = analyzer.analyze(prompt)
        techniques = selector.select(analysis)

        # Verify chain-of-thought was selected
        assert PromptTechnique.CHAIN_OF_THOUGHT in techniques.techniques

        enhanced = enhancer.enhance(prompt, analysis, techniques, "")

        # Chain-of-thought indicators
        cot_indicators = [
            "step by step",
            "step-by-step",
            "think through",
            "systematically",
            "first",
            "then",
            "next",
            "finally",
            "reasoning",
            "1.",
            "2.",
        ]

        enhanced_lower = enhanced.lower()
        has_cot = any(indicator in enhanced_lower for indicator in cot_indicators)
        assert has_cot, "Chain-of-thought technique should be visible in enhancement"


@pytest.mark.integration
class TestContextInjection:
    """Tests for context injection with real API."""

    def test_enhancement_with_context(self, runner: CliRunner, tmp_path) -> None:
        """Test enhancement includes injected context."""
        # Create a context file
        context_file = tmp_path / "example.py"
        context_file.write_text(
            '''
def authenticate(username: str, password: str) -> bool:
    """Authenticate a user."""
    if not username or not password:
        return False
    # TODO: implement actual authentication
    return True
'''
        )

        result = runner.invoke(
            main,
            [
                "--format",
                "json",
                "--no-log",
                "--context",
                str(context_file),
                "Fix the authentication function",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)

        # Context should be used
        assert (
            str(context_file) in data.get("context_files", [])
            or len(data.get("context_files", [])) > 0
        )


@pytest.mark.integration
class TestErrorRecovery:
    """Tests for error recovery during integration."""

    def test_handles_large_prompt(self, runner: CliRunner) -> None:
        """Test handling of large prompts."""
        large_prompt = "Fix the bug. " * 100  # Repeat to make it large

        result = runner.invoke(
            main,
            ["--format", "json", "--no-log", large_prompt],
        )

        # Should still work
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "enhanced" in data

    def test_handles_special_characters(self, runner: CliRunner) -> None:
        """Test handling of special characters in prompts."""
        prompt = 'Fix the bug in function: def test() -> str: return "hello"'

        result = runner.invoke(
            main,
            ["--format", "json", "--no-log", prompt],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "enhanced" in data
