"""Tests for director.py — Director, UserStory, StoryStatus, PRDBreakdown."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from agents.base import AgentOutput, AgentRole
from agents.provider_adapters import LLMResponse
from agents.runtime import AgentRuntime
from director import (
    Director,
    DirectorConfig,
    PRDBreakdown,
    StoryStatus,
    UserStory,
)
from core.model_router import RoutingConfig
from core.verification_loop import Gate, GateResult, GateStatus


# ---------------------------------------------------------------------------
# StoryStatus
# ---------------------------------------------------------------------------


class TestStoryStatus:
    def test_all_statuses(self) -> None:
        statuses = [s.value for s in StoryStatus]
        assert "pending" in statuses
        assert "in_progress" in statuses
        assert "green" in statuses
        assert "failed" in statuses
        assert "escalated" in statuses


# ---------------------------------------------------------------------------
# UserStory
# ---------------------------------------------------------------------------


class TestUserStory:
    def test_create_story(self) -> None:
        story = UserStory(
            id="US-001",
            title="Fix rose gold color",
            description="Change #FFB6C1 to #B76E79",
            agent_role=AgentRole.DESIGN_SYSTEM,
        )
        assert story.id == "US-001"
        assert story.status == StoryStatus.PENDING
        assert story.depends_on == []
        assert story.acceptance_criteria == []
        assert story.output is None

    def test_story_with_dependencies(self) -> None:
        story = UserStory(
            id="US-003",
            title="Build product page",
            description="Create product page template",
            agent_role=AgentRole.FRONTEND_DEV,
            depends_on=["US-001", "US-002"],
        )
        assert len(story.depends_on) == 2
        assert "US-001" in story.depends_on

    def test_story_with_acceptance_criteria(self) -> None:
        story = UserStory(
            id="US-004",
            title="Add contrast checker",
            description="WCAG contrast",
            agent_role=AgentRole.ACCESSIBILITY,
            acceptance_criteria=["4.5:1 for normal text", "3:1 for large text"],
        )
        assert len(story.acceptance_criteria) == 2


# ---------------------------------------------------------------------------
# PRDBreakdown
# ---------------------------------------------------------------------------


class TestPRDBreakdown:
    def test_create_breakdown(self) -> None:
        stories = [
            UserStory(
                id="US-001",
                title="Design system",
                description="Create tokens",
                agent_role=AgentRole.DESIGN_SYSTEM,
            ),
            UserStory(
                id="US-002",
                title="Build frontend",
                description="Create pages",
                agent_role=AgentRole.FRONTEND_DEV,
                depends_on=["US-001"],
            ),
        ]
        breakdown = PRDBreakdown(
            stories=stories,
            dependency_order=["US-001", "US-002"],
        )
        assert len(breakdown.stories) == 2
        assert breakdown.dependency_order == ["US-001", "US-002"]


# ---------------------------------------------------------------------------
# Director — Creation
# ---------------------------------------------------------------------------


class TestDirectorCreation:
    def test_from_config_default(self) -> None:
        director = Director.from_config()
        assert director.router is not None
        assert director.validator is not None
        assert director.journal is not None
        assert director.healer is not None
        assert director.verifier is not None
        assert director.executor is not None

    def test_from_config_custom_routing(self) -> None:
        custom_routing = {
            "routes": {
                "director": {"provider": "anthropic", "model": "claude-opus-4-6"},
            },
            "fallbacks": {
                "anthropic": {"provider": "google", "model": "gemini-3-pro-preview"},
            },
        }
        director = Director.from_config(routing_config=custom_routing)
        route = director.router.resolve("director")
        assert route.provider == "anthropic"
        assert route.model == "claude-opus-4-6"

    def test_from_config_custom_learning_dir(self) -> None:
        director = Director.from_config(learning_dir="custom_instincts")
        # The journal should exist (we can't easily check dir without I/O)
        assert director.journal is not None


# ---------------------------------------------------------------------------
# Director — Story Management
# ---------------------------------------------------------------------------


class TestDirectorStoryManagement:
    def _make_director(self) -> Director:
        return Director.from_config()

    def test_add_stories(self) -> None:
        director = self._make_director()
        stories = [
            UserStory(
                id="US-001",
                title="Story 1",
                description="Desc 1",
                agent_role=AgentRole.DESIGN_SYSTEM,
            ),
            UserStory(
                id="US-002",
                title="Story 2",
                description="Desc 2",
                agent_role=AgentRole.FRONTEND_DEV,
            ),
        ]
        director.add_stories(stories)
        summary = director.get_status_summary()
        assert summary["pending"] == 2

    def test_get_ready_stories_no_deps(self) -> None:
        director = self._make_director()
        stories = [
            UserStory(
                id="US-001",
                title="Independent",
                description="No deps",
                agent_role=AgentRole.QA,
            ),
        ]
        director.add_stories(stories)
        ready = director.get_ready_stories()
        assert len(ready) == 1
        assert ready[0].id == "US-001"

    def test_get_ready_stories_with_unmet_deps(self) -> None:
        director = self._make_director()
        stories = [
            UserStory(
                id="US-001",
                title="First",
                description="Must go first",
                agent_role=AgentRole.DESIGN_SYSTEM,
            ),
            UserStory(
                id="US-002",
                title="Second",
                description="Depends on first",
                agent_role=AgentRole.FRONTEND_DEV,
                depends_on=["US-001"],
            ),
        ]
        director.add_stories(stories)
        ready = director.get_ready_stories()
        # Only US-001 is ready (US-002 blocked by US-001)
        assert len(ready) == 1
        assert ready[0].id == "US-001"

    def test_get_ready_stories_after_dep_green(self) -> None:
        director = self._make_director()
        s1 = UserStory(
            id="US-001",
            title="First",
            description="First",
            agent_role=AgentRole.DESIGN_SYSTEM,
        )
        s2 = UserStory(
            id="US-002",
            title="Second",
            description="Depends on first",
            agent_role=AgentRole.FRONTEND_DEV,
            depends_on=["US-001"],
        )
        director.add_stories([s1, s2])

        # Mark first story as GREEN
        s1.status = StoryStatus.GREEN
        ready = director.get_ready_stories()
        # Now US-002 should be ready
        assert len(ready) == 1
        assert ready[0].id == "US-002"

    def test_get_status_summary(self) -> None:
        director = self._make_director()
        s1 = UserStory(
            id="US-001", title="A", description="A", agent_role=AgentRole.QA
        )
        s2 = UserStory(
            id="US-002", title="B", description="B", agent_role=AgentRole.QA
        )
        s3 = UserStory(
            id="US-003", title="C", description="C", agent_role=AgentRole.QA
        )
        s1.status = StoryStatus.GREEN
        s2.status = StoryStatus.FAILED
        director.add_stories([s1, s2, s3])

        summary = director.get_status_summary()
        assert summary["green"] == 1
        assert summary["failed"] == 1
        assert summary["pending"] == 1

    def test_in_progress_not_ready(self) -> None:
        director = self._make_director()
        s = UserStory(
            id="US-001", title="A", description="A", agent_role=AgentRole.QA
        )
        s.status = StoryStatus.IN_PROGRESS
        director.add_stories([s])
        ready = director.get_ready_stories()
        assert len(ready) == 0


# ---------------------------------------------------------------------------
# Director — Story Execution
# ---------------------------------------------------------------------------


class TestDirectorExecution:
    @pytest.mark.asyncio
    async def test_execute_story_success_no_gates(self) -> None:
        director = Director.from_config()
        story = UserStory(
            id="US-001",
            title="Simple task",
            description="Just do it",
            agent_role=AgentRole.DESIGN_SYSTEM,
        )
        director.add_stories([story])

        output = AgentOutput(
            agent="design_system",
            story_id="US-001",
            content="Done",
        )

        async def agent_fn() -> AgentOutput:
            return output

        result = await director.execute_story(story, agent_fn)
        assert result.status == StoryStatus.GREEN
        assert result.output == output

    @pytest.mark.asyncio
    async def test_execute_story_marks_in_progress(self) -> None:
        director = Director.from_config()
        story = UserStory(
            id="US-001",
            title="Task",
            description="Check status flow",
            agent_role=AgentRole.QA,
        )
        director.add_stories([story])

        captured_status = []

        async def agent_fn() -> AgentOutput:
            # Capture the status during execution
            captured_status.append(story.status)
            return AgentOutput(agent="qa", story_id="US-001", content="OK")

        await director.execute_story(story, agent_fn)
        assert captured_status[0] == StoryStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_execute_story_failure(self) -> None:
        director = Director.from_config()
        story = UserStory(
            id="US-001",
            title="Failing task",
            description="Will fail",
            agent_role=AgentRole.BACKEND_DEV,
        )
        director.add_stories([story])

        async def agent_fn() -> AgentOutput:
            raise RuntimeError("API connection failed")

        result = await director.execute_story(story, agent_fn)
        assert result.status == StoryStatus.FAILED

    @pytest.mark.asyncio
    async def test_execute_story_with_passing_gates(self) -> None:
        director = Director.from_config()
        story = UserStory(
            id="US-001",
            title="Gated task",
            description="With verification",
            agent_role=AgentRole.FRONTEND_DEV,
        )
        director.add_stories([story])

        async def agent_fn() -> AgentOutput:
            return AgentOutput(
                agent="frontend_dev", story_id="US-001", content="<div>OK</div>"
            )

        async def build_checker() -> GateResult:
            return GateResult(gate=Gate.BUILD, status=GateStatus.PASSED, message="OK")

        result = await director.execute_story(
            story, agent_fn, gate_checkers={Gate.BUILD: build_checker}
        )
        assert result.status == StoryStatus.GREEN

    @pytest.mark.asyncio
    async def test_execute_story_with_failing_gate(self) -> None:
        director = Director.from_config()
        story = UserStory(
            id="US-001",
            title="Gated fail",
            description="Gate will fail",
            agent_role=AgentRole.FRONTEND_DEV,
        )
        director.add_stories([story])

        async def agent_fn() -> AgentOutput:
            return AgentOutput(
                agent="frontend_dev", story_id="US-001", content="bad code"
            )

        async def lint_checker() -> GateResult:
            return GateResult(
                gate=Gate.LINT,
                status=GateStatus.FAILED,
                message="ESLint found 5 errors",
            )

        result = await director.execute_story(
            story, agent_fn, gate_checkers={Gate.LINT: lint_checker}
        )
        # Should be FAILED because self-heal returns diagnosis but no actual fixer wired
        assert result.status == StoryStatus.FAILED


# ---------------------------------------------------------------------------
# Director — Default Routing
# ---------------------------------------------------------------------------


class TestDefaultRouting:
    def test_default_routing_has_all_agents(self) -> None:
        director = Director.from_config()
        expected_agents = [
            "director",
            "design_system",
            "frontend_dev",
            "backend_dev",
            "accessibility",
            "performance",
            "seo_content",
            "qa",
        ]
        for agent_name in expected_agents:
            route = director.router.resolve(agent_name)
            assert route.provider is not None
            assert route.model is not None

    def test_director_uses_opus(self) -> None:
        director = Director.from_config()
        route = director.router.resolve("director")
        assert route.provider == "anthropic"
        assert "opus" in route.model

    def test_design_system_uses_gemini(self) -> None:
        director = Director.from_config()
        route = director.router.resolve("design_system")
        assert route.provider == "google"

    def test_qa_uses_haiku(self) -> None:
        director = Director.from_config()
        route = director.router.resolve("qa")
        assert route.provider == "anthropic"
        assert "haiku" in route.model


# ---------------------------------------------------------------------------
# Director — Runtime Integration
# ---------------------------------------------------------------------------


class TestDirectorRuntimeIntegration:
    """Tests for the Director's integrated AgentRuntime support."""

    def test_director_has_runtime(self) -> None:
        """Director should create an AgentRuntime internally."""
        director = Director.from_config()
        assert director.runtime is not None
        assert isinstance(director.runtime, AgentRuntime)

    def test_director_has_spec_registry(self) -> None:
        """Director should have a mapping from AgentRole to AgentSpec."""
        director = Director.from_config()
        specs = director.spec_registry
        assert isinstance(specs, dict)
        # Should have specs for all 7 specialist roles (not director itself)
        assert AgentRole.DESIGN_SYSTEM in specs
        assert AgentRole.FRONTEND_DEV in specs
        assert AgentRole.BACKEND_DEV in specs
        assert AgentRole.ACCESSIBILITY in specs
        assert AgentRole.PERFORMANCE in specs
        assert AgentRole.SEO_CONTENT in specs
        assert AgentRole.QA in specs

    def test_spec_registry_names_match_roles(self) -> None:
        """Each spec's name should match its role value (used by ModelRouter)."""
        director = Director.from_config()
        for role, spec in director.spec_registry.items():
            assert spec.role == role
            assert spec.name == role.value

    @pytest.mark.asyncio
    async def test_run_story_success(self) -> None:
        """run_story() should auto-resolve spec and call runtime."""
        director = Director.from_config()

        story = UserStory(
            id="US-001",
            title="Fix color palette",
            description="Change rose gold from #FFB6C1 to #B76E79",
            agent_role=AgentRole.DESIGN_SYSTEM,
        )
        director.add_stories([story])

        mock_response = LLMResponse(
            text='{"rose_gold": "#B76E79"}',
            provider="google",
            model="gemini-3-pro-preview",
            usage={"input_tokens": 100, "output_tokens": 50},
        )

        mock_adapter = AsyncMock()
        mock_adapter.call.return_value = mock_response

        with patch("agents.runtime.get_adapter", return_value=mock_adapter):
            result = await director.run_story(story)

        assert result.status == StoryStatus.GREEN
        assert result.output is not None
        assert result.output.agent == "design_system"
        assert result.output.story_id == "US-001"
        assert "#B76E79" in result.output.content

    @pytest.mark.asyncio
    async def test_run_story_uses_correct_provider(self) -> None:
        """run_story() should route to the spec's configured provider."""
        director = Director.from_config()

        story = UserStory(
            id="US-002",
            title="Build nav component",
            description="Create responsive navigation",
            agent_role=AgentRole.FRONTEND_DEV,
        )
        director.add_stories([story])

        mock_response = LLMResponse(
            text="<nav>...</nav>",
            provider="anthropic",
            model="claude-sonnet-4-6",
            usage={"input_tokens": 200, "output_tokens": 100},
        )

        mock_adapter = AsyncMock()
        mock_adapter.call.return_value = mock_response

        with patch("agents.runtime.get_adapter", return_value=mock_adapter) as mock_get:
            await director.run_story(story)

        # frontend_dev routes to anthropic
        mock_get.assert_called_with("anthropic")

    @pytest.mark.asyncio
    async def test_run_story_unknown_role_raises(self) -> None:
        """run_story() should raise if the story's role has no registered spec."""
        director = Director.from_config()

        # Director role has no spec in the registry (it IS the director)
        story = UserStory(
            id="US-099",
            title="Director task",
            description="Self-referential",
            agent_role=AgentRole.DIRECTOR,
        )
        director.add_stories([story])

        with pytest.raises(ValueError, match="No agent spec registered"):
            await director.run_story(story)

    @pytest.mark.asyncio
    async def test_run_story_with_gates(self) -> None:
        """run_story() should pass gate_checkers through to execute_story."""
        director = Director.from_config()

        story = UserStory(
            id="US-003",
            title="Accessible nav",
            description="Build WCAG-compliant nav",
            agent_role=AgentRole.ACCESSIBILITY,
        )
        director.add_stories([story])

        mock_response = LLMResponse(
            text="ARIA labels added",
            provider="anthropic",
            model="claude-haiku-4-5",
            usage={"input_tokens": 50, "output_tokens": 25},
        )

        mock_adapter = AsyncMock()
        mock_adapter.call.return_value = mock_response

        async def a11y_checker() -> GateResult:
            return GateResult(
                gate=Gate.A11Y,
                status=GateStatus.PASSED,
                message="0 violations",
            )

        with patch("agents.runtime.get_adapter", return_value=mock_adapter):
            result = await director.run_story(
                story, gate_checkers={Gate.A11Y: a11y_checker}
            )

        assert result.status == StoryStatus.GREEN

    @pytest.mark.asyncio
    async def test_run_story_passes_task_as_description(self) -> None:
        """The story description should be used as the LLM task."""
        director = Director.from_config()

        story = UserStory(
            id="US-004",
            title="SEO meta tags",
            description="Generate Open Graph meta tags for the homepage",
            agent_role=AgentRole.SEO_CONTENT,
        )
        director.add_stories([story])

        mock_response = LLMResponse(
            text="<meta property='og:title'...",
            provider="openai",
            model="gpt-4o",
            usage={"input_tokens": 80, "output_tokens": 40},
        )

        mock_adapter = AsyncMock()
        mock_adapter.call.return_value = mock_response

        with patch("agents.runtime.get_adapter", return_value=mock_adapter):
            await director.run_story(story)

        # The user message should contain the story description
        call_args = mock_adapter.call.call_args
        messages = call_args[1]["messages"] if "messages" in call_args[1] else call_args[0][1]
        user_msg = [m for m in messages if m.role == "user"][0]
        assert "Open Graph meta tags" in user_msg.content
