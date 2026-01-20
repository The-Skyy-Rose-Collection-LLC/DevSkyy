"""
Unit Tests for Prompt Enhancer CLI (US-011)
===========================================

Comprehensive tests for PromptAnalyzer, TechniqueSelector, ContextScanner,
and PromptEnhancer with mocked Claude responses.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from cli.prompt_enhance import (
    ContextScanner,
    EnhancedPrompt,
    EnhancementError,
    PromptAnalysis,
    PromptAnalyzer,
    PromptEnhancer,
    PromptTechnique,
    TaskMode,
    TechniqueSelection,
    TechniqueSelector,
    main,
)

if TYPE_CHECKING:
    pass


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def analyzer() -> PromptAnalyzer:
    """Create a PromptAnalyzer instance."""
    return PromptAnalyzer()


@pytest.fixture
def selector() -> TechniqueSelector:
    """Create a TechniqueSelector instance."""
    return TechniqueSelector()


@pytest.fixture
def scanner() -> ContextScanner:
    """Create a ContextScanner instance."""
    return ContextScanner(token_budget=1000)


@pytest.fixture
def sample_analysis() -> PromptAnalysis:
    """Create a sample PromptAnalysis for testing."""
    return PromptAnalysis(
        original="Fix the bug in the login function",
        task_type=TaskMode.DEBUG,
        clarity_score=60,
        missing_elements=["context", "output_format"],
        detected_keywords=["fix", "bug"],
        confidence=0.6,
    )


@pytest.fixture
def temp_context_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with sample Python files."""
    # Create sample Python files
    (tmp_path / "main.py").write_text("def main():\n    print('hello')\n")
    (tmp_path / "utils.py").write_text("def helper():\n    return 42\n")
    (tmp_path / "login.py").write_text("def login(user, password):\n    pass\n")
    return tmp_path


# =============================================================================
# PromptAnalyzer Tests (US-002)
# =============================================================================


class TestPromptAnalyzer:
    """Tests for PromptAnalyzer class."""

    def test_analyze_returns_prompt_analysis(self, analyzer: PromptAnalyzer) -> None:
        """analyze() should return a PromptAnalysis instance."""
        result = analyzer.analyze("Fix the bug in the login function")
        assert isinstance(result, PromptAnalysis)
        assert result.original == "Fix the bug in the login function"

    def test_detect_code_task_type(self, analyzer: PromptAnalyzer) -> None:
        """Should detect code task type from keywords."""
        result = analyzer.analyze("Implement a new API endpoint for user registration")
        assert result.task_type == TaskMode.CODE
        assert result.confidence > 0

    def test_detect_debug_task_type(self, analyzer: PromptAnalyzer) -> None:
        """Should detect debug task type from keywords."""
        result = analyzer.analyze("Fix the bug causing the crash in production")
        assert result.task_type == TaskMode.DEBUG
        assert "bug" in result.detected_keywords or "crash" in result.detected_keywords

    def test_detect_refactor_task_type(self, analyzer: PromptAnalyzer) -> None:
        """Should detect refactor task type from keywords."""
        result = analyzer.analyze("Refactor the database module to improve performance")
        assert result.task_type == TaskMode.REFACTOR

    def test_detect_analysis_task_type(self, analyzer: PromptAnalyzer) -> None:
        """Should detect analysis task type from keywords."""
        result = analyzer.analyze("Analyze this code and explain what it does")
        assert result.task_type == TaskMode.ANALYSIS

    def test_detect_writing_task_type(self, analyzer: PromptAnalyzer) -> None:
        """Should detect writing task type from keywords."""
        result = analyzer.analyze("Write documentation for the API endpoints")
        # Note: 'write' appears in both CODE and WRITING - depends on other keywords
        assert result.task_type in (TaskMode.WRITING, TaskMode.CODE)

    def test_detect_creative_task_type(self, analyzer: PromptAnalyzer) -> None:
        """Should detect creative task type from keywords."""
        result = analyzer.analyze("Brainstorm innovative design ideas for the UI")
        assert result.task_type == TaskMode.CREATIVE

    def test_default_task_type_for_ambiguous_prompt(self, analyzer: PromptAnalyzer) -> None:
        """Should default to CODE for ambiguous prompts."""
        result = analyzer.analyze("hello world")
        assert result.task_type == TaskMode.CODE
        assert result.confidence < 0.5

    def test_clarity_score_short_prompt(self, analyzer: PromptAnalyzer) -> None:
        """Short prompts should have lower clarity scores."""
        result = analyzer.analyze("fix it")
        assert result.clarity_score < 50

    def test_clarity_score_detailed_prompt(self, analyzer: PromptAnalyzer) -> None:
        """Detailed prompts should have higher clarity scores."""
        detailed = """
        Please fix the authentication bug in src/auth/login.py.
        The function should return a proper error when credentials are invalid.
        Expected output: JSON response with error code and message.
        """
        result = analyzer.analyze(detailed)
        assert result.clarity_score >= 50

    def test_missing_elements_detection(self, analyzer: PromptAnalyzer) -> None:
        """Should detect missing elements like context, constraints, examples."""
        result = analyzer.analyze("do something")
        assert "context" in result.missing_elements
        assert "constraints" in result.missing_elements
        assert "output_format" in result.missing_elements
        assert "examples" in result.missing_elements

    def test_no_missing_context_when_file_mentioned(self, analyzer: PromptAnalyzer) -> None:
        """Should not report missing context when file is mentioned."""
        result = analyzer.analyze("Fix the bug in the auth.py file")
        assert "context" not in result.missing_elements

    def test_no_missing_constraints_when_requirements_present(
        self, analyzer: PromptAnalyzer
    ) -> None:
        """Should not report missing constraints when requirements are specified."""
        result = analyzer.analyze("The function must return a string and should handle errors")
        assert "constraints" not in result.missing_elements

    def test_keyword_extraction(self, analyzer: PromptAnalyzer) -> None:
        """Should extract relevant keywords from prompt."""
        result = analyzer.analyze("Debug and fix the broken API endpoint")
        assert len(result.detected_keywords) > 0
        assert any(
            kw in ["debug", "fix", "broken", "api", "endpoint"] for kw in result.detected_keywords
        )


# =============================================================================
# TechniqueSelector Tests (US-003)
# =============================================================================


class TestTechniqueSelector:
    """Tests for TechniqueSelector class."""

    def test_select_returns_technique_selection(
        self, selector: TechniqueSelector, sample_analysis: PromptAnalysis
    ) -> None:
        """select() should return a TechniqueSelection instance."""
        result = selector.select(sample_analysis)
        assert isinstance(result, TechniqueSelection)
        assert len(result.techniques) > 0
        assert len(result.techniques) <= 4

    def test_debug_task_gets_appropriate_techniques(self, selector: TechniqueSelector) -> None:
        """Debug tasks should get chain-of-thought and step-by-step techniques."""
        analysis = PromptAnalysis(
            original="Fix the bug",
            task_type=TaskMode.DEBUG,
            clarity_score=70,
            confidence=0.8,
        )
        result = selector.select(analysis)
        assert PromptTechnique.CHAIN_OF_THOUGHT in result.techniques
        assert PromptTechnique.STEP_BY_STEP in result.techniques

    def test_code_task_gets_appropriate_techniques(self, selector: TechniqueSelector) -> None:
        """Code tasks should get role-assignment and step-by-step techniques."""
        analysis = PromptAnalysis(
            original="Implement feature",
            task_type=TaskMode.CODE,
            clarity_score=70,
            confidence=0.8,
        )
        result = selector.select(analysis)
        assert PromptTechnique.ROLE_ASSIGNMENT in result.techniques
        assert PromptTechnique.STEP_BY_STEP in result.techniques

    def test_creative_task_gets_appropriate_techniques(self, selector: TechniqueSelector) -> None:
        """Creative tasks should get tree-of-thoughts technique."""
        analysis = PromptAnalysis(
            original="Design new UI",
            task_type=TaskMode.CREATIVE,
            clarity_score=70,
            confidence=0.8,
        )
        result = selector.select(analysis)
        assert PromptTechnique.TREE_OF_THOUGHTS in result.techniques

    def test_low_clarity_adds_metacognition(self, selector: TechniqueSelector) -> None:
        """Low clarity prompts should get metacognition added."""
        analysis = PromptAnalysis(
            original="fix",
            task_type=TaskMode.CODE,
            clarity_score=30,  # Low clarity
            confidence=0.3,
        )
        result = selector.select(analysis)
        assert PromptTechnique.METACOGNITION in result.techniques

    def test_missing_examples_adds_few_shot(self, selector: TechniqueSelector) -> None:
        """Missing examples should add few-shot technique."""
        analysis = PromptAnalysis(
            original="Write some code",
            task_type=TaskMode.CODE,
            clarity_score=50,
            missing_elements=["examples"],
            confidence=0.5,
        )
        result = selector.select(analysis)
        assert PromptTechnique.FEW_SHOT in result.techniques

    def test_reasoning_is_generated(
        self, selector: TechniqueSelector, sample_analysis: PromptAnalysis
    ) -> None:
        """Should generate reasoning for technique selection."""
        result = selector.select(sample_analysis)
        assert len(result.reasoning) > 0
        assert sample_analysis.task_type.value in result.reasoning


# =============================================================================
# ContextScanner Tests (US-004)
# =============================================================================


class TestContextScanner:
    """Tests for ContextScanner class."""

    def test_scan_with_no_context_flag(self, scanner: ContextScanner) -> None:
        """Should return empty context when no_context is True."""
        context, files = scanner.scan("Fix the bug", no_context=True)
        assert context == ""
        assert files == []

    def test_scan_with_explicit_files(
        self, scanner: ContextScanner, temp_context_dir: Path
    ) -> None:
        """Should read explicit files when provided."""
        file_path = str(temp_context_dir / "main.py")
        context, files = scanner.scan(
            "Fix the bug",
            explicit_files=[file_path],
            no_context=False,
        )
        assert file_path in files
        assert "def main():" in context

    def test_scan_with_nonexistent_file(self, scanner: ContextScanner) -> None:
        """Should skip nonexistent files gracefully."""
        context, files = scanner.scan(
            "Fix the bug",
            explicit_files=["/nonexistent/file.py"],
            no_context=False,
        )
        assert context == ""
        assert files == []

    def test_scan_respects_token_budget(self, temp_context_dir: Path) -> None:
        """Should respect token budget when scanning files."""
        scanner = ContextScanner(token_budget=50)  # Very small budget
        # Create a large file
        (temp_context_dir / "large.py").write_text("x = 1\n" * 1000)

        file_path = str(temp_context_dir / "large.py")
        context, files = scanner.scan(
            "Fix the bug",
            explicit_files=[file_path],
            no_context=False,
        )
        # Should truncate or limit content
        assert len(context) <= 50 * 4 + 200  # token_budget * 4 chars + overhead

    def test_extract_file_keywords(self, scanner: ContextScanner) -> None:
        """Should extract potential file keywords from prompt."""
        keywords = scanner._extract_file_keywords("Fix the login_handler function in auth_service")
        assert "login" in keywords or "auth" in keywords or "login_handler" in keywords

    def test_is_relevant_matches_keywords(self, scanner: ContextScanner) -> None:
        """Should match files based on keywords."""
        path = Path("/tmp/login.py")
        assert scanner._is_relevant(path, ["login", "auth"]) is True
        assert scanner._is_relevant(path, ["database", "model"]) is False


# =============================================================================
# PromptEnhancer Tests (US-005)
# =============================================================================


class TestPromptEnhancer:
    """Tests for PromptEnhancer class with mocked Claude responses."""

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""}, clear=False)
    def test_enhance_falls_back_without_api_key(self) -> None:
        """Should fall back to local enhancement without API key."""
        enhancer = PromptEnhancer()
        analysis = PromptAnalysis(
            original="Fix the bug",
            task_type=TaskMode.DEBUG,
            clarity_score=50,
            confidence=0.5,
        )
        techniques = TechniqueSelection(
            techniques=[PromptTechnique.CHAIN_OF_THOUGHT],
            reasoning="Testing",
            task_type=TaskMode.DEBUG,
        )

        result = enhancer.enhance("Fix the bug", analysis, techniques, "")

        assert len(result) > 0
        assert "Fix the bug" in result or "bug" in result.lower()

    @patch("cli.prompt_enhance.PromptEnhancer.client")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
    def test_enhance_calls_claude_api(self, mock_client: MagicMock) -> None:
        """Should call Claude API when key is available."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Enhanced prompt text here")]
        mock_client.messages.create.return_value = mock_response

        enhancer = PromptEnhancer()
        enhancer._client = mock_client

        analysis = PromptAnalysis(
            original="Fix the bug",
            task_type=TaskMode.DEBUG,
            clarity_score=50,
            confidence=0.5,
        )
        techniques = TechniqueSelection(
            techniques=[PromptTechnique.CHAIN_OF_THOUGHT],
            reasoning="Testing",
            task_type=TaskMode.DEBUG,
        )

        result = enhancer.enhance("Fix the bug", analysis, techniques, "")

        mock_client.messages.create.assert_called_once()
        assert result == "Enhanced prompt text here"

    @patch("cli.prompt_enhance.PromptEnhancer.client")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
    def test_enhance_falls_back_on_api_error(self, mock_client: MagicMock) -> None:
        """Should fall back to local enhancement on API error."""
        mock_client.messages.create.side_effect = Exception("API Error")

        enhancer = PromptEnhancer()
        enhancer._client = mock_client

        analysis = PromptAnalysis(
            original="Fix the bug",
            task_type=TaskMode.DEBUG,
            clarity_score=50,
            confidence=0.5,
        )
        techniques = TechniqueSelection(
            techniques=[PromptTechnique.CHAIN_OF_THOUGHT],
            reasoning="Testing",
            task_type=TaskMode.DEBUG,
        )

        # Should not raise, should fall back
        result = enhancer.enhance("Fix the bug", analysis, techniques, "")
        assert len(result) > 0

    def test_build_meta_prompt_includes_techniques(self) -> None:
        """Meta-prompt should include technique instructions."""
        enhancer = PromptEnhancer()
        analysis = PromptAnalysis(
            original="Test prompt",
            task_type=TaskMode.CODE,
            clarity_score=70,
            confidence=0.8,
        )
        techniques = TechniqueSelection(
            techniques=[PromptTechnique.ROLE_ASSIGNMENT, PromptTechnique.CHAIN_OF_THOUGHT],
            reasoning="Testing",
            task_type=TaskMode.CODE,
        )

        meta = enhancer._build_meta_prompt("Test prompt", analysis, techniques, "")

        assert "Role Assignment" in meta
        assert "Chain of Thought" in meta
        assert "Test prompt" in meta

    def test_enhance_locally_applies_role(self) -> None:
        """Local enhancement should apply role assignment."""
        enhancer = PromptEnhancer()
        analysis = PromptAnalysis(
            original="Debug the error",
            task_type=TaskMode.DEBUG,
            clarity_score=50,
            confidence=0.5,
        )
        techniques = TechniqueSelection(
            techniques=[PromptTechnique.ROLE_ASSIGNMENT],
            reasoning="Testing",
            task_type=TaskMode.DEBUG,
        )

        result = enhancer._enhance_locally("Debug the error", analysis, techniques, "")

        assert "debugging" in result.lower() or "expert" in result.lower()

    def test_enhance_locally_adds_chain_of_thought(self) -> None:
        """Local enhancement should add chain-of-thought when selected."""
        enhancer = PromptEnhancer()
        analysis = PromptAnalysis(
            original="Analyze this",
            task_type=TaskMode.ANALYSIS,
            clarity_score=50,
            confidence=0.5,
        )
        techniques = TechniqueSelection(
            techniques=[PromptTechnique.CHAIN_OF_THOUGHT],
            reasoning="Testing",
            task_type=TaskMode.ANALYSIS,
        )

        result = enhancer._enhance_locally("Analyze this", analysis, techniques, "")

        assert "step by step" in result.lower()


# =============================================================================
# EnhancedPrompt Tests
# =============================================================================


class TestEnhancedPrompt:
    """Tests for EnhancedPrompt data class."""

    def test_to_dict_serialization(self, sample_analysis: PromptAnalysis) -> None:
        """to_dict() should return a serializable dictionary."""
        techniques = TechniqueSelection(
            techniques=[PromptTechnique.CHAIN_OF_THOUGHT],
            reasoning="Testing",
            task_type=TaskMode.DEBUG,
        )
        result = EnhancedPrompt(
            original="Original prompt",
            enhanced="Enhanced prompt",
            analysis=sample_analysis,
            techniques=techniques,
            context_used=["file.py"],
            latency_ms=100.0,
        )

        data = result.to_dict()

        assert data["original"] == "Original prompt"
        assert data["enhanced"] == "Enhanced prompt"
        assert data["analysis"]["task_type"] == "debug"
        assert data["analysis"]["clarity_score"] == 60
        assert data["techniques"]["applied"] == ["chain-of-thought"]
        assert data["context_files"] == ["file.py"]
        assert data["latency_ms"] == 100.0

        # Verify it's JSON serializable
        json_str = json.dumps(data)
        assert len(json_str) > 0


# =============================================================================
# CLI Tests
# =============================================================================


class TestCLI:
    """Tests for CLI argument parsing and execution."""

    def test_help_option(self, runner: CliRunner) -> None:
        """--help should display usage information."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Transform natural language prompts" in result.output
        assert "--mode" in result.output
        assert "--format" in result.output

    def test_version_option(self, runner: CliRunner) -> None:
        """--version should display version information."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_basic_prompt_enhancement(self, runner: CliRunner) -> None:
        """Should enhance a basic prompt."""
        result = runner.invoke(main, ["Fix the login bug"])
        assert result.exit_code == 0
        assert len(result.output) > 0

    def test_mode_option(self, runner: CliRunner) -> None:
        """--mode should override auto-detection."""
        result = runner.invoke(main, ["--mode", "code", "do something"])
        assert result.exit_code == 0

    def test_format_json_option(self, runner: CliRunner) -> None:
        """--format json should output JSON."""
        result = runner.invoke(main, ["--format", "json", "Fix the bug"])
        assert result.exit_code == 0
        # Should be valid JSON
        data = json.loads(result.output)
        assert "original" in data
        assert "enhanced" in data
        assert "analysis" in data

    def test_format_markdown_option(self, runner: CliRunner) -> None:
        """--format md should output markdown."""
        result = runner.invoke(main, ["--format", "md", "Fix the bug"])
        assert result.exit_code == 0
        assert "# Enhanced Prompt" in result.output

    def test_preview_option(self, runner: CliRunner) -> None:
        """--preview should show side-by-side comparison."""
        result = runner.invoke(main, ["--preview", "Fix the bug"])
        assert result.exit_code == 0
        assert "ORIGINAL" in result.output
        assert "ENHANCED" in result.output

    def test_auto_option(self, runner: CliRunner) -> None:
        """--auto should output only enhanced prompt."""
        result = runner.invoke(main, ["--auto", "Fix the bug"])
        assert result.exit_code == 0
        # Should not contain metadata
        assert "ORIGINAL" not in result.output
        assert "Task:" not in result.output

    def test_verbose_option(self, runner: CliRunner) -> None:
        """--verbose should show processing details."""
        result = runner.invoke(main, ["--verbose", "Fix the bug"])
        assert result.exit_code == 0
        # Verbose output goes to stderr
        assert "Mode:" in result.output or "Detected task:" in result.output

    def test_no_context_option(self, runner: CliRunner) -> None:
        """--no-context should disable context scanning."""
        result = runner.invoke(main, ["--no-context", "Fix the bug"])
        assert result.exit_code == 0

    def test_no_log_option(self, runner: CliRunner) -> None:
        """--no-log should disable history logging."""
        result = runner.invoke(main, ["--no-log", "Fix the bug"])
        assert result.exit_code == 0

    def test_stats_option(self, runner: CliRunner) -> None:
        """--stats should show enhancement statistics."""
        result = runner.invoke(main, ["--stats"])
        assert result.exit_code == 0
        assert "history" in result.output.lower() or "stats" in result.output.lower()

    def test_init_option(self, runner: CliRunner) -> None:
        """--init should offer to create config file."""
        result = runner.invoke(main, ["--init"], input="n\n")
        assert result.exit_code == 0

    def test_empty_prompt_error(self, runner: CliRunner) -> None:
        """Empty prompt should raise error."""
        result = runner.invoke(main, [""])
        assert result.exit_code != 0
        assert "Empty prompt" in result.output

    def test_piped_input(self, runner: CliRunner) -> None:
        """Should accept piped input."""
        result = runner.invoke(main, input="Fix the bug in login\n")
        assert result.exit_code == 0
        assert len(result.output) > 0

    def test_context_option_with_file(self, runner: CliRunner, temp_context_dir: Path) -> None:
        """--context should include specified file."""
        file_path = str(temp_context_dir / "main.py")
        result = runner.invoke(
            main,
            ["--context", file_path, "--verbose", "Fix the bug"],
        )
        assert result.exit_code == 0


# =============================================================================
# Integration Tests (Light)
# =============================================================================


class TestIntegrationLight:
    """Light integration tests without real API calls."""

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""}, clear=False)
    def test_full_enhancement_flow_without_api(self, runner: CliRunner) -> None:
        """Full enhancement flow should work without API key."""
        result = runner.invoke(
            main,
            [
                "--format",
                "json",
                "--no-log",
                "Implement a REST API endpoint for user authentication",
            ],
        )
        assert result.exit_code == 0

        data = json.loads(result.output)

        # Verify all components worked
        assert data["original"] == "Implement a REST API endpoint for user authentication"
        assert len(data["enhanced"]) > len(data["original"])
        assert data["analysis"]["task_type"] == "code"
        assert data["analysis"]["clarity_score"] > 0
        assert len(data["techniques"]["applied"]) > 0

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""}, clear=False)
    def test_all_task_types_work(self, runner: CliRunner) -> None:
        """All task types should work without errors."""
        prompts = {
            "code": "Implement a new feature",
            "debug": "Fix the crash on startup",
            "refactor": "Refactor the database module",
            "analysis": "Analyze this algorithm's complexity",
            "writing": "Write documentation for the API",
            "creative": "Design a new UI concept",
        }

        for mode, prompt in prompts.items():
            result = runner.invoke(
                main,
                ["--mode", mode, "--format", "json", "--no-log", prompt],
            )
            assert result.exit_code == 0, f"Failed for mode: {mode}"
            data = json.loads(result.output)
            assert data["analysis"]["task_type"] == mode


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    def test_enhancement_error_is_raised_properly(self) -> None:
        """EnhancementError should be properly raised."""
        with pytest.raises(EnhancementError):
            raise EnhancementError("Test error")

    def test_api_initialization_error(self) -> None:
        """Should handle API initialization errors gracefully."""
        enhancer = PromptEnhancer()
        enhancer._client = None  # Force re-initialization

        # Mock Anthropic to raise an error during initialization
        with patch("anthropic.Anthropic", side_effect=Exception("Init failed")):
            with pytest.raises(EnhancementError) as exc_info:
                _ = enhancer.client
            assert "Failed to initialize" in str(exc_info.value)
