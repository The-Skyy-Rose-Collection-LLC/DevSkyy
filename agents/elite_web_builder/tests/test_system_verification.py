"""
System-level verification tests for Elite Web Builder.

Validates:
- File completeness (all expected files exist)
- Import integrity (all imports resolve)
- Interface contracts (public API correct)
- Config/Knowledge completeness
- End-to-end smoke test
"""

from __future__ import annotations

import asyncio
import inspect
import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest


# =============================================================================
# Constants
# =============================================================================

PACKAGE_ROOT = Path(__file__).parent.parent

EXPECTED_AGENT_FILES = [
    "agents/design_system.py",
    "agents/frontend_dev.py",
    "agents/backend_dev.py",
    "agents/accessibility.py",
    "agents/performance.py",
    "agents/seo_content.py",
    "agents/qa.py",
]

EXPECTED_CORE_FILES = [
    "core/model_router.py",
    "core/learning_journal.py",
    "core/verification_loop.py",
    "core/self_healer.py",
    "core/ground_truth.py",
    "core/ralph_integration.py",
]

EXPECTED_KNOWLEDGE_FILES = [
    "knowledge/wordpress.md",
    "knowledge/shopify.md",
    "knowledge/woocommerce.md",
    "knowledge/theme_json_schema.md",
    "knowledge/wcag_checklist.md",
    "knowledge/performance_budgets.md",
    "knowledge/security_checklist.md",
]

EXPECTED_CONFIG_FILES = [
    "config/provider_routing.json",
    "config/quality_gates.json",
]

MAX_FILE_LINES = 800


# =============================================================================
# 7a. File Completeness
# =============================================================================


class TestFileCompleteness:
    """All expected files exist and meet size constraints."""

    def test_director_exists(self):
        assert (PACKAGE_ROOT / "director.py").exists()

    def test_main_exists(self):
        assert (PACKAGE_ROOT / "__main__.py").exists()

    def test_init_exists(self):
        assert (PACKAGE_ROOT / "__init__.py").exists()

    @pytest.mark.parametrize("path", EXPECTED_AGENT_FILES)
    def test_agent_file_exists(self, path):
        assert (PACKAGE_ROOT / path).exists(), f"Missing agent file: {path}"

    @pytest.mark.parametrize("path", EXPECTED_CORE_FILES)
    def test_core_file_exists(self, path):
        assert (PACKAGE_ROOT / path).exists(), f"Missing core file: {path}"

    @pytest.mark.parametrize("path", EXPECTED_KNOWLEDGE_FILES)
    def test_knowledge_file_exists(self, path):
        assert (PACKAGE_ROOT / path).exists(), f"Missing knowledge file: {path}"

    @pytest.mark.parametrize("path", EXPECTED_CONFIG_FILES)
    def test_config_file_exists(self, path):
        """
        Assert that a configuration file exists at PACKAGE_ROOT for the given relative path.
        
        Parameters:
            path (str | pathlib.Path): Relative path (from PACKAGE_ROOT) to the expected config file.
        
        Raises:
            AssertionError: If the file does not exist.
        """
        assert (PACKAGE_ROOT / path).exists(), f"Missing config file: {path}"

    def test_no_file_exceeds_max_lines(self):
        """No Python file exceeds the 800-line limit."""
        violations = []
        for py_file in PACKAGE_ROOT.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            line_count = len(py_file.read_text().splitlines())
            if line_count > MAX_FILE_LINES:
                violations.append(f"{py_file.relative_to(PACKAGE_ROOT)}: {line_count} lines")
        assert not violations, f"Files exceeding {MAX_FILE_LINES} lines: {violations}"

    def test_no_legacy_imports(self):
        """
        Verify that no production Python files import from `base_legacy` or `operations_legacy`.
        
        Scans all .py files under PACKAGE_ROOT (excluding files in __pycache__ and test files) and fails the test if any file contains an `import base_legacy`, `import operations_legacy`, `from base_legacy`, or `from operations_legacy` statement.
        """
        for py_file in PACKAGE_ROOT.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            # Skip test files (they may reference legacy names in assertions)
            if "tests/" in str(py_file) or "test_" in py_file.name:
                continue
            content = py_file.read_text()
            assert "import base_legacy" not in content, f"{py_file} imports base_legacy"
            assert "import operations_legacy" not in content, f"{py_file} imports operations_legacy"
            assert "from base_legacy" not in content, f"{py_file} imports from base_legacy"
            assert "from operations_legacy" not in content, f"{py_file} imports from operations_legacy"


# =============================================================================
# 7b. Import Integrity
# =============================================================================


class TestImportIntegrity:
    """All imports resolve without errors."""

    def test_director_imports(self):
        """
        Ensure core Director-related symbols are importable from elite_web_builder.director.
        
        This test imports the public types, constants, templates, and registries expected to be exposed by the director module to verify import integrity and public API stability.
        """
        from elite_web_builder.director import (
            AgentRole,
            AgentRuntime,
            AgentSpec,
            Director,
            DirectorConfig,
            PlanningError,
            PRDBreakdown,
            ProjectReport,
            StoryStatus,
            UserStory,
            _DEFAULT_ROUTING,
            _DIRECTOR_SPEC,
            _PLANNING_PROMPT_TEMPLATE,
            spec_registry,
        )

    def test_main_imports(self):
        from elite_web_builder.__main__ import (
            _build_parser,
            _load_prd,
            _print_report,
            _run,
            main,
        )

    def test_core_imports(self):
        from elite_web_builder.core import (
            GroundTruthValidator,
            LearningEntry,
            LearningJournal,
            LLMResponse,
            ModelRouter,
            ProviderAdapter,
            RalphExecutor,
            FailureCategory,
            SelfHealer,
            GateConfig,
            GateName,
            GateResult,
            GateStatus,
            VerificationLoop,
        )

    def test_agents_imports(self):
        from elite_web_builder.agents import (
            ACCESSIBILITY_SPEC,
            BACKEND_DEV_SPEC,
            DESIGN_SYSTEM_SPEC,
            FRONTEND_DEV_SPEC,
            PERFORMANCE_SPEC,
            QA_SPEC,
            SEO_CONTENT_SPEC,
        )

    def test_package_init_imports(self):
        from agents.elite_web_builder import (
            AgentRole,
            AgentSpec,
            Director,
            DirectorConfig,
            PlanningError,
            PRDBreakdown,
            ProjectReport,
            StoryStatus,
            UserStory,
        )


# =============================================================================
# 7c. Interface Contracts
# =============================================================================


class TestInterfaceContracts:
    """Public API has correct signatures and types."""

    def test_execute_prd_is_async(self):
        from elite_web_builder.director import Director
        assert inspect.iscoroutinefunction(Director.execute_prd)

    def test_plan_stories_is_async(self):
        from elite_web_builder.director import Director
        assert inspect.iscoroutinefunction(Director._plan_stories)

    def test_run_story_is_async(self):
        from elite_web_builder.director import Director
        assert inspect.iscoroutinefunction(Director.run_story)

    def test_project_report_is_frozen(self):
        from elite_web_builder.director import ProjectReport
        report = ProjectReport(
            stories=(),
            status_summary={},
            all_green=True,
            elapsed_ms=0,
            failures=(),
            instincts_learned=0,
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            report.all_green = False  # type: ignore[misc]

    def test_project_report_has_all_fields(self):
        from elite_web_builder.director import ProjectReport
        import dataclasses
        fields = {f.name for f in dataclasses.fields(ProjectReport)}
        expected = {"stories", "status_summary", "all_green", "elapsed_ms", "failures", "instincts_learned"}
        assert fields == expected

    def test_planning_error_has_raw_response(self):
        from elite_web_builder.director import PlanningError
        err = PlanningError("test", raw_response="raw")
        assert hasattr(err, "raw_response")
        assert err.raw_response == "raw"

    def test_all_7_agents_in_spec_registry(self):
        """
        Verify that spec_registry contains exactly the seven expected AgentRole members: DESIGN_SYSTEM, FRONTEND_DEV, BACKEND_DEV, ACCESSIBILITY, PERFORMANCE, SEO_CONTENT, and QA.
        """
        from elite_web_builder.director import AgentRole, spec_registry
        expected_roles = {
            AgentRole.DESIGN_SYSTEM,
            AgentRole.FRONTEND_DEV,
            AgentRole.BACKEND_DEV,
            AgentRole.ACCESSIBILITY,
            AgentRole.PERFORMANCE,
            AgentRole.SEO_CONTENT,
            AgentRole.QA,
        }
        assert set(spec_registry.keys()) == expected_roles

    def test_default_routing_has_all_routes(self):
        from elite_web_builder.director import _DEFAULT_ROUTING
        routing = _DEFAULT_ROUTING["routing"]
        expected_roles = {
            "director", "design_system", "frontend_dev", "backend_dev",
            "accessibility", "performance", "seo_content", "qa",
        }
        assert set(routing.keys()) == expected_roles

    def test_default_routing_has_4_fallbacks(self):
        from elite_web_builder.director import _DEFAULT_ROUTING
        fallbacks = _DEFAULT_ROUTING["fallbacks"]
        assert len(fallbacks) == 4
        expected_providers = {"anthropic", "google", "openai", "xai"}
        assert set(fallbacks.keys()) == expected_providers


# =============================================================================
# 7d. Config/Knowledge Completeness
# =============================================================================


class TestConfigKnowledgeCompleteness:
    """Config and knowledge files are valid."""

    def test_provider_routing_is_valid_json(self):
        path = PACKAGE_ROOT / "config" / "provider_routing.json"
        data = json.loads(path.read_text())
        assert "routing" in data
        assert "fallbacks" in data

    def test_quality_gates_is_valid_json(self):
        path = PACKAGE_ROOT / "config" / "quality_gates.json"
        data = json.loads(path.read_text())
        assert "gates" in data
        assert len(data["gates"]) == 8  # 8 quality gates

    def test_knowledge_files_not_empty(self):
        for path_str in EXPECTED_KNOWLEDGE_FILES:
            path = PACKAGE_ROOT / path_str
            content = path.read_text()
            assert len(content) > 50, f"Knowledge file too short: {path_str}"


# =============================================================================
# 7e. End-to-End Smoke Test
# =============================================================================


class TestEndToEndSmoke:
    """Smoke test: create Director, feed minimal PRD, verify report."""

    @pytest.mark.asyncio
    async def test_minimal_3_story_prd(self):
        """
        Run an end-to-end smoke test using a mocked LLM to verify Director produces a successful 3-story report.
        
        Executes a minimal product requirements document (PRD) that defines three dependent stories via a ModelRouter backed by a mocked adapter. Asserts the produced ProjectReport contains exactly three stories, reports all_green as `True`, has a green count of 3, records a positive elapsed time, and contains no failures.
        """
        from elite_web_builder.director import Director, DirectorConfig
        from elite_web_builder.core.model_router import LLMResponse, ModelRouter

        planning_json = json.dumps({
            "stories": [
                {
                    "id": "US-001",
                    "title": "Design tokens",
                    "description": "Create design system tokens",
                    "agent_role": "design_system",
                    "depends_on": [],
                    "acceptance_criteria": ["Tokens created"],
                },
                {
                    "id": "US-002",
                    "title": "Homepage layout",
                    "description": "Build homepage HTML/CSS",
                    "agent_role": "frontend_dev",
                    "depends_on": ["US-001"],
                    "acceptance_criteria": ["Layout renders"],
                },
                {
                    "id": "US-003",
                    "title": "A11y audit",
                    "description": "Run accessibility audit",
                    "agent_role": "accessibility",
                    "depends_on": ["US-002"],
                    "acceptance_criteria": ["0 violations"],
                },
            ],
            "dependency_order": ["US-001", "US-002", "US-003"],
        })

        router = ModelRouter(
            routing={
                "director": {"provider": "mock", "model": "test"},
                "design_system": {"provider": "mock", "model": "test"},
                "frontend_dev": {"provider": "mock", "model": "test"},
                "accessibility": {"provider": "mock", "model": "test"},
                "performance": {"provider": "mock", "model": "test"},
                "seo_content": {"provider": "mock", "model": "test"},
                "backend_dev": {"provider": "mock", "model": "test"},
                "qa": {"provider": "mock", "model": "test"},
            },
            fallbacks={},
        )

        call_count = 0

        async def mock_generate(prompt, **kwargs):
            """
            Mock LLM generate function that returns a planning JSON on its first invocation and a success message on subsequent invocations.
            
            Parameters:
                prompt (str): The input prompt sent to the mock LLM.
            
            Returns:
                LLMResponse: An LLMResponse whose `content` is the planning JSON for the first call and a success message thereafter. The response uses provider "mock", model "test", and latency_ms 10.
            """
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return LLMResponse(content=planning_json, provider="mock", model="test", latency_ms=10)
            return LLMResponse(content="Story output completed successfully with all checks passing.", provider="mock", model="test", latency_ms=10)

        adapter = AsyncMock()
        adapter.generate = mock_generate
        router.register_adapter("mock", adapter)

        director = Director(router=router)
        report = await director.execute_prd("Build a luxury fashion homepage")

        assert len(report.stories) == 3
        assert report.all_green is True
        assert report.status_summary.get("green", 0) == 3
        assert report.elapsed_ms > 0
        assert len(report.failures) == 0

    @pytest.mark.asyncio
    async def test_director_default_config(self):
        """Create Director with default config and verify it initializes."""
        from elite_web_builder.director import Director, DirectorConfig
        config = DirectorConfig()
        director = Director(config=config)
        assert director._config.max_stories == 50
        assert director._config.max_heal_attempts == 3
        assert director._config.verification_enabled is True