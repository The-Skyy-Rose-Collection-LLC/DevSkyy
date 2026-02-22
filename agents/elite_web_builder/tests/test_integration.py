"""Integration test — end-to-end run with a minimal test PRD.

Tests the full Elite Web Builder pipeline:
PRD → Stories → Director → Agent Execution → Verification → Learning

Uses mocked agent functions (no real LLM calls) to verify the orchestration
logic works correctly end-to-end.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.base import AgentCapability, AgentOutput, AgentRole, AgentSpec
from agents.design_system import DESIGN_SYSTEM_SPEC
from agents.frontend_dev import FRONTEND_DEV_SPEC
from agents.backend_dev import BACKEND_DEV_SPEC
from agents.accessibility import ACCESSIBILITY_SPEC
from core.ground_truth import ClaimType, GroundTruthValidator
from core.learning_journal import JournalEntry, LearningJournal
from core.model_router import ModelRouter, RoutingConfig
from core.ralph_integration import RalphConfig, RalphExecutor
from core.self_healer import SelfHealer
from core.verification_loop import (
    Gate,
    GateResult,
    GateStatus,
    VerificationConfig,
    VerificationLoop,
)
from director import (
    Director,
    DirectorConfig,
    PRDBreakdown,
    StoryStatus,
    UserStory,
)
from tools.contrast_checker import check_contrast
from tools.type_scale import generate_type_scale
from tools.spacing_scale import generate_spacing_scale


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def director() -> Director:
    return Director.from_config()


@pytest.fixture
def mini_prd_stories() -> list[UserStory]:
    """A minimal 3-story PRD: design → frontend → QA."""
    return [
        UserStory(
            id="US-001",
            title="Create color palette",
            description="Generate rose gold palette with WCAG-compliant contrast",
            agent_role=AgentRole.DESIGN_SYSTEM,
            acceptance_criteria=[
                "Rose gold is #B76E79",
                "All text colors pass AA contrast on white",
            ],
        ),
        UserStory(
            id="US-002",
            title="Build homepage hero",
            description="Create responsive hero section with brand colors",
            agent_role=AgentRole.FRONTEND_DEV,
            depends_on=["US-001"],
            acceptance_criteria=[
                "Uses CSS custom properties from design system",
                "Responsive at 375px and 768px",
            ],
        ),
        UserStory(
            id="US-003",
            title="QA homepage",
            description="Verify homepage hero passes all quality gates",
            agent_role=AgentRole.QA,
            depends_on=["US-002"],
            acceptance_criteria=[
                "No accessibility violations",
                "Lighthouse performance > 80",
            ],
        ),
    ]


# ---------------------------------------------------------------------------
# E2E: Story lifecycle
# ---------------------------------------------------------------------------


class TestStoryLifecycle:
    """Test the full story lifecycle: pending → in_progress → green."""

    def test_dependency_order(
        self, director: Director, mini_prd_stories: list[UserStory]
    ) -> None:
        """Stories execute in dependency order."""
        director.add_stories(mini_prd_stories)

        # Only US-001 is ready (no deps)
        ready = director.get_ready_stories()
        assert len(ready) == 1
        assert ready[0].id == "US-001"

        # Mark US-001 green → US-002 becomes ready
        mini_prd_stories[0].status = StoryStatus.GREEN
        ready = director.get_ready_stories()
        assert len(ready) == 1
        assert ready[0].id == "US-002"

        # Mark US-002 green → US-003 becomes ready
        mini_prd_stories[1].status = StoryStatus.GREEN
        ready = director.get_ready_stories()
        assert len(ready) == 1
        assert ready[0].id == "US-003"

        # Mark US-003 green → no more stories
        mini_prd_stories[2].status = StoryStatus.GREEN
        ready = director.get_ready_stories()
        assert len(ready) == 0

    def test_status_summary(
        self, director: Director, mini_prd_stories: list[UserStory]
    ) -> None:
        director.add_stories(mini_prd_stories)
        mini_prd_stories[0].status = StoryStatus.GREEN
        mini_prd_stories[1].status = StoryStatus.IN_PROGRESS

        summary = director.get_status_summary()
        assert summary == {"green": 1, "in_progress": 1, "pending": 1}


# ---------------------------------------------------------------------------
# E2E: Agent execution pipeline
# ---------------------------------------------------------------------------


class TestAgentExecutionPipeline:
    @pytest.mark.asyncio
    async def test_design_system_story(self, director: Director) -> None:
        """Design system agent produces tokens, passes verification."""
        story = UserStory(
            id="US-001",
            title="Create color palette",
            description="Rose gold palette",
            agent_role=AgentRole.DESIGN_SYSTEM,
        )
        director.add_stories([story])

        async def design_agent() -> AgentOutput:
            # Simulated design system output
            palette = {
                "rose-gold": "#B76E79",
                "crimson": "#DC143C",
                "onyx": "#353839",
            }
            return AgentOutput(
                agent="design_system",
                story_id="US-001",
                content=json.dumps(palette),
                files_changed=("theme.json",),
                metadata={"colors_generated": 3},
            )

        async def color_checker() -> GateResult:
            # Verify rose gold contrast — passes AA-Large (3:1) but not AA-Normal (4.5:1)
            # Rose gold on white = 3.8:1 ratio
            result = check_contrast("#B76E79", "#FFFFFF")
            if result.aa_large:
                return GateResult(
                    gate=Gate.A11Y, status=GateStatus.PASSED,
                    message=f"Rose gold contrast {result.ratio}:1 passes AA-Large",
                )
            return GateResult(
                gate=Gate.A11Y,
                status=GateStatus.FAILED,
                message=f"Rose gold contrast {result.ratio}:1 fails AA-Large",
            )

        result = await director.execute_story(
            story, design_agent, gate_checkers={Gate.A11Y: color_checker}
        )
        assert result.status == StoryStatus.GREEN
        assert result.output is not None
        assert "B76E79" in result.output.content

    @pytest.mark.asyncio
    async def test_frontend_story_with_multiple_gates(
        self, director: Director
    ) -> None:
        """Frontend story passes build + lint + a11y gates."""
        story = UserStory(
            id="US-002",
            title="Build hero section",
            description="Responsive hero",
            agent_role=AgentRole.FRONTEND_DEV,
        )
        director.add_stories([story])

        async def frontend_agent() -> AgentOutput:
            return AgentOutput(
                agent="frontend_dev",
                story_id="US-002",
                content="<section class='hero'>...</section>",
                files_changed=("hero.html", "hero.css"),
            )

        gate_checkers = {
            Gate.BUILD: lambda: _make_gate_result(Gate.BUILD, True),
            Gate.LINT: lambda: _make_gate_result(Gate.LINT, True),
            Gate.A11Y: lambda: _make_gate_result(Gate.A11Y, True),
        }

        result = await director.execute_story(story, frontend_agent, gate_checkers)
        assert result.status == StoryStatus.GREEN

    @pytest.mark.asyncio
    async def test_failed_story_triggers_heal_attempt(
        self, director: Director
    ) -> None:
        """A failing gate triggers the self-heal cycle."""
        story = UserStory(
            id="US-003",
            title="Broken component",
            description="Will fail lint",
            agent_role=AgentRole.FRONTEND_DEV,
        )
        director.add_stories([story])

        async def broken_agent() -> AgentOutput:
            return AgentOutput(
                agent="frontend_dev",
                story_id="US-003",
                content="var x = 1; // eslint error",
            )

        async def failing_lint() -> GateResult:
            return GateResult(
                gate=Gate.LINT,
                status=GateStatus.FAILED,
                message="ESLint: 3 errors, 0 warnings",
                details=["no-var", "semi", "no-unused-vars"],
            )

        result = await director.execute_story(
            story, broken_agent, gate_checkers={Gate.LINT: failing_lint}
        )
        # Self-heal is triggered but no real fixer → stays FAILED
        assert result.status == StoryStatus.FAILED


# ---------------------------------------------------------------------------
# E2E: Multi-provider routing
# ---------------------------------------------------------------------------


class TestMultiProviderRouting:
    def test_all_agents_have_routes(self, director: Director) -> None:
        """Every agent role resolves to a valid provider/model pair."""
        for role in AgentRole:
            route = director.router.resolve(role.value)
            assert route.provider is not None
            assert route.model is not None

    def test_provider_diversity(self, director: Director) -> None:
        """The team uses at least 2 different providers (Anthropic + Google)."""
        providers = set()
        for role in AgentRole:
            route = director.router.resolve(role.value)
            providers.add(route.provider)
        assert len(providers) >= 2


# ---------------------------------------------------------------------------
# E2E: Ground truth + tools
# ---------------------------------------------------------------------------


class TestGroundTruthIntegration:
    def test_color_validation(self) -> None:
        """Ground truth validator catches invalid colors."""
        validator = GroundTruthValidator()
        # Valid hex
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "#B76E79")
        assert result.valid

        # Invalid hex
        result = validator.verify_claim(ClaimType.COLOR_VALUE, "#ZZZZZZ")
        assert not result.valid

    def test_contrast_tool_integration(self) -> None:
        """Contrast checker feeds into accessibility gate."""
        result = check_contrast("#B76E79", "#FFFFFF")
        # Rose gold on white = 3.8:1 — passes AA-Large but NOT AA-Normal
        assert result.ratio >= 3.0
        assert result.aa_large is True
        assert result.aa_normal is False

    def test_type_scale_integration(self) -> None:
        """Type scale generates valid sizes."""
        scale = generate_type_scale(base_size=16, ratio=1.25)
        assert scale["body"] == 16
        assert scale["h1"] > scale["h2"] > scale["h3"]

    def test_spacing_scale_integration(self) -> None:
        """Spacing scale generates consistent values."""
        scale = generate_spacing_scale(base=4)
        assert scale["xs"] < scale["sm"] < scale["md"] < scale["lg"]


# ---------------------------------------------------------------------------
# E2E: Learning journal
# ---------------------------------------------------------------------------


class TestLearningIntegration:
    def test_mistake_becomes_rule(self, tmp_path: Path) -> None:
        """A logged mistake can be extracted as a learning instinct."""
        journal = LearningJournal(storage_dir=tmp_path)

        # Log the same mistake 3 times (enough for instinct extraction)
        for i in range(3):
            journal.add_entry(
                JournalEntry(
                    mistake="Used #FFB6C1 for rose gold",
                    correct="Rose gold is #B76E79",
                    agent="design_system",
                    story_id=f"US-{i:03d}",
                    tags=["color", "brand"],
                )
            )

        instincts = journal.extract_instincts(min_occurrences=3)
        assert len(instincts) >= 1
        assert any("B76E79" in i.rule for i in instincts)

    def test_learning_context_injected(self, tmp_path: Path) -> None:
        """Learning context gets injected into agent prompts."""
        journal = LearningJournal(storage_dir=tmp_path)
        journal.add_entry(
            JournalEntry(
                mistake="Wrong color",
                correct="Use #B76E79",
                agent="design_system",
                story_id="US-001",
            )
        )

        context = journal.generate_context(agent="design_system")
        assert "#B76E79" in context

        # Inject into agent spec
        prompt = DESIGN_SYSTEM_SPEC.build_prompt(learning_context=context)
        assert "#B76E79" in prompt
        assert DESIGN_SYSTEM_SPEC.system_prompt in prompt


# ---------------------------------------------------------------------------
# E2E: Verification loop
# ---------------------------------------------------------------------------


class TestVerificationIntegration:
    @pytest.mark.asyncio
    async def test_all_gates_pass(self) -> None:
        """Full verification loop with all gates passing."""
        config = VerificationConfig()
        loop = VerificationLoop(config=config)

        checkers = {
            Gate.BUILD: lambda: _make_gate_result(Gate.BUILD, True),
            Gate.TYPES: lambda: _make_gate_result(Gate.TYPES, True),
            Gate.LINT: lambda: _make_gate_result(Gate.LINT, True),
            Gate.TESTS: lambda: _make_gate_result(Gate.TESTS, True),
            Gate.SECURITY: lambda: _make_gate_result(Gate.SECURITY, True),
            Gate.A11Y: lambda: _make_gate_result(Gate.A11Y, True),
            Gate.PERF: lambda: _make_gate_result(Gate.PERF, True),
            Gate.DIFF: lambda: _make_gate_result(Gate.DIFF, True),
        }

        report = await loop.run_all(checkers)
        assert report.all_green
        assert report.passed_count == 8
        assert report.failed_count == 0

    @pytest.mark.asyncio
    async def test_single_gate_failure(self) -> None:
        """One failing gate makes the report not all-green."""
        config = VerificationConfig()
        loop = VerificationLoop(config=config)

        checkers = {
            Gate.BUILD: lambda: _make_gate_result(Gate.BUILD, True),
            Gate.SECURITY: lambda: _make_gate_result(
                Gate.SECURITY, False, "Found hardcoded API key"
            ),
        }

        report = await loop.run_all(checkers)
        assert not report.all_green
        assert report.failed_count == 1


# ---------------------------------------------------------------------------
# E2E: Self-heal integration
# ---------------------------------------------------------------------------


class TestSelfHealIntegration:
    def test_diagnose_from_verification_report(self) -> None:
        """Self-healer can diagnose from a verification report."""
        healer = SelfHealer(max_attempts=3)
        config = VerificationConfig()
        loop = VerificationLoop(config=config)

        # Create a report with a failed gate
        from core.verification_loop import VerificationReport

        report = VerificationReport(
            results=[
                GateResult(
                    gate=Gate.BUILD,
                    status=GateStatus.PASSED,
                    message="OK",
                ),
                GateResult(
                    gate=Gate.LINT,
                    status=GateStatus.FAILED,
                    message="ruff: 5 violations found",
                    details=["E501 line too long", "F841 unused variable"],
                ),
            ]
        )

        diagnosis = healer.diagnose(report)
        assert diagnosis is not None
        assert Gate.LINT in diagnosis.failed_gates


# ---------------------------------------------------------------------------
# E2E: Ralph resilience
# ---------------------------------------------------------------------------


class TestRalphIntegration:
    @pytest.mark.asyncio
    async def test_successful_execution(self) -> None:
        """Ralph executor wraps successful operations."""
        executor = RalphExecutor(config=RalphConfig(max_attempts=2))

        async def ok_operation() -> str:
            return "success"

        result = await executor.execute(ok_operation)
        assert result.success
        assert result.value == "success"
        assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_retry_on_failure(self) -> None:
        """Ralph executor retries failed operations."""
        executor = RalphExecutor(config=RalphConfig(max_attempts=3, base_delay=0.01))
        call_count = 0

        async def flaky_operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("Temporary failure")
            return "recovered"

        result = await executor.execute(flaky_operation)
        assert result.success
        assert result.value == "recovered"
        assert result.attempts == 3


# ---------------------------------------------------------------------------
# E2E: Full pipeline simulation
# ---------------------------------------------------------------------------


class TestFullPipeline:
    @pytest.mark.asyncio
    async def test_three_story_pipeline(
        self, director: Director, mini_prd_stories: list[UserStory]
    ) -> None:
        """Execute 3 stories in dependency order through the full pipeline."""
        director.add_stories(mini_prd_stories)

        # Define mock agents for each story
        async def design_agent() -> AgentOutput:
            return AgentOutput(
                agent="design_system",
                story_id="US-001",
                content='{"rose-gold": "#B76E79"}',
            )

        async def frontend_agent() -> AgentOutput:
            return AgentOutput(
                agent="frontend_dev",
                story_id="US-002",
                content="<section class='hero'>Built</section>",
            )

        async def qa_agent() -> AgentOutput:
            return AgentOutput(
                agent="qa",
                story_id="US-003",
                content="All checks passed",
            )

        agents = {
            "US-001": design_agent,
            "US-002": frontend_agent,
            "US-003": qa_agent,
        }

        # Execute in dependency order
        execution_order = []
        for story_id in ["US-001", "US-002", "US-003"]:
            story = mini_prd_stories[
                next(i for i, s in enumerate(mini_prd_stories) if s.id == story_id)
            ]
            result = await director.execute_story(story, agents[story_id])
            execution_order.append(result.id)
            assert result.status == StoryStatus.GREEN

        assert execution_order == ["US-001", "US-002", "US-003"]

        # All stories green
        summary = director.get_status_summary()
        assert summary == {"green": 3}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_gate_result(
    gate: Gate, passed: bool, message: str = "OK"
) -> GateResult:
    return GateResult(
        gate=gate,
        status=GateStatus.PASSED if passed else GateStatus.FAILED,
        message=message,
    )
