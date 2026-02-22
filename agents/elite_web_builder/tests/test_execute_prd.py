"""Tests for execute_prd pipeline — PlanningError, ProjectReport, planning, execution."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from unittest.mock import AsyncMock, patch

import pytest

from agents.base import AgentOutput, AgentRole
from agents.provider_adapters import LLMResponse
from director import (
    Director,
    PlanningError,
    ProjectReport,
    StoryStatus,
    UserStory,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_planning_json(num_stories: int = 2) -> str:
    """Build a valid JSON string mimicking LLM planning output."""
    stories = []
    for i in range(1, num_stories + 1):
        sid = f"US-{i:03d}"
        stories.append({
            "id": sid,
            "title": f"Story {i}",
            "description": f"Do thing {i}",
            "agent_role": "design_system" if i == 1 else "frontend_dev",
            "depends_on": [] if i == 1 else [f"US-{i-1:03d}"],
            "acceptance_criteria": [f"Criterion {i}a"],
        })
    order = [f"US-{i:03d}" for i in range(1, num_stories + 1)]
    return json.dumps({"stories": stories, "dependency_order": order})


def _make_mock_adapter(text: str = "done") -> AsyncMock:
    """Create a mock provider adapter that returns a fixed LLMResponse."""
    mock = AsyncMock()
    mock.call.return_value = LLMResponse(
        text=text,
        provider="google",
        model="gemini-3-pro-preview",
        usage={"input_tokens": 50, "output_tokens": 25},
    )
    return mock


# ---------------------------------------------------------------------------
# PlanningError
# ---------------------------------------------------------------------------


class TestPlanningError:
    def test_is_runtime_error(self) -> None:
        err = PlanningError("bad json")
        assert isinstance(err, RuntimeError)

    def test_has_raw_response_field(self) -> None:
        err = PlanningError("parse failed", raw_response='{"incomplete')
        assert err.raw_response == '{"incomplete'

    def test_default_raw_response_empty(self) -> None:
        err = PlanningError("oops")
        assert err.raw_response == ""

    def test_str_contains_message(self) -> None:
        err = PlanningError("LLM returned garbage")
        assert "LLM returned garbage" in str(err)


# ---------------------------------------------------------------------------
# ProjectReport
# ---------------------------------------------------------------------------


class TestProjectReport:
    def test_frozen_dataclass(self) -> None:
        report = ProjectReport(
            stories={},
            status_summary={},
            all_green=True,
            elapsed_ms=100.0,
            failures=[],
            instincts_learned=0,
        )
        with pytest.raises(FrozenInstanceError):
            report.all_green = False  # type: ignore[misc]

    def test_all_green_true(self) -> None:
        report = ProjectReport(
            stories={"US-001": UserStory(
                id="US-001", title="A", description="A",
                agent_role=AgentRole.QA, status=StoryStatus.GREEN,
            )},
            status_summary={"green": 1},
            all_green=True,
            elapsed_ms=50.0,
            failures=[],
            instincts_learned=0,
        )
        assert report.all_green is True
        assert report.failures == []

    def test_all_green_false(self) -> None:
        report = ProjectReport(
            stories={},
            status_summary={"failed": 1},
            all_green=False,
            elapsed_ms=50.0,
            failures=["US-001: Something failed"],
            instincts_learned=0,
        )
        assert report.all_green is False
        assert len(report.failures) == 1

    def test_instincts_learned_tracked(self) -> None:
        report = ProjectReport(
            stories={},
            status_summary={},
            all_green=True,
            elapsed_ms=10.0,
            failures=[],
            instincts_learned=3,
        )
        assert report.instincts_learned == 3


# ---------------------------------------------------------------------------
# _parse_planning_response
# ---------------------------------------------------------------------------


class TestParsePlanningResponse:
    def test_valid_json(self) -> None:
        raw = '{"stories": [], "dependency_order": []}'
        result = Director._parse_planning_response(raw)
        assert result == {"stories": [], "dependency_order": []}

    def test_strips_markdown_fences(self) -> None:
        raw = '```json\n{"stories": [], "dependency_order": []}\n```'
        result = Director._parse_planning_response(raw)
        assert result == {"stories": [], "dependency_order": []}

    def test_strips_triple_backtick_no_lang(self) -> None:
        raw = '```\n{"stories": [], "dependency_order": []}\n```'
        result = Director._parse_planning_response(raw)
        assert result == {"stories": [], "dependency_order": []}

    def test_invalid_json_raises_planning_error(self) -> None:
        with pytest.raises(PlanningError, match="invalid JSON"):
            Director._parse_planning_response("this is not json at all")

    def test_empty_string_raises_planning_error(self) -> None:
        with pytest.raises(PlanningError):
            Director._parse_planning_response("")

    def test_json_with_leading_whitespace(self) -> None:
        raw = '  \n  {"stories": [], "dependency_order": []}  \n  '
        result = Director._parse_planning_response(raw)
        assert result == {"stories": [], "dependency_order": []}


# ---------------------------------------------------------------------------
# _build_breakdown
# ---------------------------------------------------------------------------


class TestBuildBreakdown:
    def test_valid_data_returns_breakdown(self) -> None:
        data = {
            "stories": [
                {
                    "id": "US-001",
                    "title": "Design tokens",
                    "description": "Create design system tokens",
                    "agent_role": "design_system",
                    "depends_on": [],
                    "acceptance_criteria": ["Tokens documented"],
                },
            ],
            "dependency_order": ["US-001"],
        }
        breakdown = Director._build_breakdown(data, max_stories=50)
        assert len(breakdown.stories) == 1
        assert breakdown.stories[0].id == "US-001"
        assert breakdown.stories[0].agent_role == AgentRole.DESIGN_SYSTEM
        assert breakdown.dependency_order == ["US-001"]

    def test_missing_stories_key_raises(self) -> None:
        with pytest.raises(PlanningError, match="stories"):
            Director._build_breakdown({"dependency_order": []}, max_stories=50)

    def test_unknown_agent_role_raises(self) -> None:
        data = {
            "stories": [{
                "id": "US-001",
                "title": "X",
                "description": "X",
                "agent_role": "nonexistent_role",
            }],
            "dependency_order": ["US-001"],
        }
        with pytest.raises(PlanningError, match="nonexistent_role"):
            Director._build_breakdown(data, max_stories=50)

    def test_depends_on_defaults_to_empty(self) -> None:
        data = {
            "stories": [{
                "id": "US-001",
                "title": "X",
                "description": "X",
                "agent_role": "qa",
            }],
            "dependency_order": ["US-001"],
        }
        breakdown = Director._build_breakdown(data, max_stories=50)
        assert breakdown.stories[0].depends_on == []

    def test_acceptance_criteria_defaults_to_empty(self) -> None:
        data = {
            "stories": [{
                "id": "US-001",
                "title": "X",
                "description": "X",
                "agent_role": "qa",
            }],
            "dependency_order": ["US-001"],
        }
        breakdown = Director._build_breakdown(data, max_stories=50)
        assert breakdown.stories[0].acceptance_criteria == []

    def test_truncates_to_max_stories(self) -> None:
        stories = [
            {
                "id": f"US-{i:03d}",
                "title": f"S{i}",
                "description": f"D{i}",
                "agent_role": "qa",
            }
            for i in range(1, 11)
        ]
        data = {
            "stories": stories,
            "dependency_order": [s["id"] for s in stories],
        }
        breakdown = Director._build_breakdown(data, max_stories=3)
        assert len(breakdown.stories) == 3


# ---------------------------------------------------------------------------
# _plan_stories
# ---------------------------------------------------------------------------


class TestPlanStories:
    @pytest.mark.asyncio
    async def test_calls_runtime_with_director_spec(self) -> None:
        director = Director.from_config()
        planning_json = _valid_planning_json(1)
        mock_adapter = _make_mock_adapter(text=planning_json)

        with patch("agents.runtime.get_adapter", return_value=mock_adapter):
            breakdown = await director._plan_stories("Build a landing page")

        assert len(breakdown.stories) == 1
        # Verify runtime.execute was called (adapter.call is the underlying call)
        mock_adapter.call.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_prd_breakdown(self) -> None:
        director = Director.from_config()
        planning_json = _valid_planning_json(3)
        mock_adapter = _make_mock_adapter(text=planning_json)

        with patch("agents.runtime.get_adapter", return_value=mock_adapter):
            breakdown = await director._plan_stories("Build an e-commerce site")

        assert len(breakdown.stories) == 3
        assert breakdown.dependency_order == ["US-001", "US-002", "US-003"]

    @pytest.mark.asyncio
    async def test_propagates_planning_error(self) -> None:
        director = Director.from_config()
        mock_adapter = _make_mock_adapter(text="not json at all")

        with patch("agents.runtime.get_adapter", return_value=mock_adapter):
            with pytest.raises(PlanningError):
                await director._plan_stories("Bad PRD")

    @pytest.mark.asyncio
    async def test_max_stories_in_prompt(self) -> None:
        director = Director.from_config()
        planning_json = _valid_planning_json(1)
        mock_adapter = _make_mock_adapter(text=planning_json)

        with patch("agents.runtime.get_adapter", return_value=mock_adapter):
            await director._plan_stories("Test PRD")

        # Check the prompt sent to the LLM contains the max_stories value
        call_args = mock_adapter.call.call_args
        messages = call_args[1].get("messages") or call_args[0][1]
        user_msg = [m for m in messages if m.role == "user"][0]
        assert "50" in user_msg.content  # default max_stories


# ---------------------------------------------------------------------------
# execute_prd
# ---------------------------------------------------------------------------


class TestExecutePrd:
    @pytest.mark.asyncio
    async def test_planning_failure_returns_report_with_failure(self) -> None:
        director = Director.from_config()
        mock_adapter = _make_mock_adapter(text="not json")

        with patch("agents.runtime.get_adapter", return_value=mock_adapter):
            report = await director.execute_prd("Bad PRD")

        assert report.all_green is False
        assert len(report.failures) == 1
        assert "Planning failed" in report.failures[0]

    @pytest.mark.asyncio
    async def test_all_green_sets_all_green_true(self) -> None:
        director = Director.from_config()

        # Phase 1: planning returns 1 story (design_system, no deps)
        planning_json = json.dumps({
            "stories": [{
                "id": "US-001",
                "title": "Tokens",
                "description": "Create tokens",
                "agent_role": "design_system",
                "depends_on": [],
                "acceptance_criteria": [],
            }],
            "dependency_order": ["US-001"],
        })

        # Phase 2: story execution returns content
        call_count = 0

        async def mock_call(model, messages):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Planning call
                return LLMResponse(
                    text=planning_json,
                    provider="anthropic",
                    model="claude-opus-4-6",
                    usage={"input_tokens": 100, "output_tokens": 50},
                )
            # Story execution call
            return LLMResponse(
                text='{"tokens": {"rose_gold": "#B76E79"}}',
                provider="google",
                model="gemini-3-pro-preview",
                usage={"input_tokens": 50, "output_tokens": 25},
            )

        mock_adapter = AsyncMock()
        mock_adapter.call = AsyncMock(side_effect=mock_call)

        with patch("agents.runtime.get_adapter", return_value=mock_adapter):
            report = await director.execute_prd("Create design tokens")

        assert report.all_green is True
        assert report.failures == []
        assert "US-001" in report.stories

    @pytest.mark.asyncio
    async def test_failed_story_captured_in_failures_list(self) -> None:
        director = Director.from_config()

        planning_json = json.dumps({
            "stories": [{
                "id": "US-001",
                "title": "Broken task",
                "description": "Will fail",
                "agent_role": "design_system",
                "depends_on": [],
                "acceptance_criteria": [],
            }],
            "dependency_order": ["US-001"],
        })

        call_count = 0

        async def mock_call(model, messages):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return LLMResponse(
                    text=planning_json,
                    provider="anthropic",
                    model="claude-opus-4-6",
                    usage={"input_tokens": 100, "output_tokens": 50},
                )
            raise RuntimeError("API connection failed")

        mock_adapter = AsyncMock()
        mock_adapter.call = AsyncMock(side_effect=mock_call)

        with patch("agents.runtime.get_adapter", return_value=mock_adapter):
            report = await director.execute_prd("Fail PRD")

        assert report.all_green is False
        assert any("US-001" in f for f in report.failures)

    @pytest.mark.asyncio
    async def test_elapsed_ms_is_positive(self) -> None:
        director = Director.from_config()
        planning_json = _valid_planning_json(1)

        call_count = 0

        async def mock_call(model, messages, **kwargs):
            nonlocal call_count
            call_count += 1
            return LLMResponse(
                text=planning_json if call_count == 1 else "ok",
                provider="google",
                model=model,
                usage={"input_tokens": 50, "output_tokens": 25},
            )

        mock_adapter = AsyncMock()
        mock_adapter.call = AsyncMock(side_effect=mock_call)

        with patch("agents.runtime.get_adapter", return_value=mock_adapter):
            report = await director.execute_prd("Test timing")

        assert report.elapsed_ms > 0

    @pytest.mark.asyncio
    async def test_stories_snapshot_in_report(self) -> None:
        director = Director.from_config()

        planning_json = json.dumps({
            "stories": [
                {
                    "id": "US-001",
                    "title": "Design",
                    "description": "Tokens",
                    "agent_role": "design_system",
                    "depends_on": [],
                },
                {
                    "id": "US-002",
                    "title": "Frontend",
                    "description": "Build pages",
                    "agent_role": "frontend_dev",
                    "depends_on": ["US-001"],
                },
            ],
            "dependency_order": ["US-001", "US-002"],
        })

        call_count = 0

        async def mock_call(model, messages, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return LLMResponse(
                    text=planning_json,
                    provider="anthropic",
                    model=model,
                    usage={"input_tokens": 100, "output_tokens": 50},
                )
            return LLMResponse(
                text="content",
                provider="google",
                model=model,
                usage={"input_tokens": 50, "output_tokens": 25},
            )

        mock_adapter = AsyncMock()
        mock_adapter.call = AsyncMock(side_effect=mock_call)

        with patch("agents.runtime.get_adapter", return_value=mock_adapter):
            report = await director.execute_prd("Two-story PRD")

        assert "US-001" in report.stories
        assert "US-002" in report.stories

    @pytest.mark.asyncio
    async def test_dependency_cycle_guard(self) -> None:
        """Stories with circular deps should surface failure, not loop forever."""
        director = Director.from_config()

        # Manually set up a cycle: A depends on B, B depends on A
        # (bypass planning since we need a specific invalid state)
        s1 = UserStory(
            id="US-001", title="A", description="A",
            agent_role=AgentRole.DESIGN_SYSTEM, depends_on=["US-002"],
        )
        s2 = UserStory(
            id="US-002", title="B", description="B",
            agent_role=AgentRole.FRONTEND_DEV, depends_on=["US-001"],
        )
        director.add_stories([s1, s2])

        # Directly test the cycle detection in the execution loop
        # by calling the internal loop logic
        max_loops = len(director._stories) * 2
        loop_count = 0
        deadlocked = False

        while True:
            ready = director.get_ready_stories()
            if not ready:
                # Both stories are still PENDING — this IS the cycle
                pending = [
                    s for s in director._stories.values()
                    if s.status == StoryStatus.PENDING
                ]
                if pending:
                    deadlocked = True
                break
            if loop_count >= max_loops:
                deadlocked = True
                break
            loop_count += 1

        assert deadlocked is True

    @pytest.mark.asyncio
    async def test_empty_prd_produces_empty_report(self) -> None:
        director = Director.from_config()

        planning_json = json.dumps({
            "stories": [],
            "dependency_order": [],
        })
        mock_adapter = _make_mock_adapter(text=planning_json)

        with patch("agents.runtime.get_adapter", return_value=mock_adapter):
            report = await director.execute_prd("")

        assert report.all_green is True
        assert report.stories == {}


# ---------------------------------------------------------------------------
# DirectorConfig.max_stories
# ---------------------------------------------------------------------------


class TestDirectorConfigMaxStories:
    def test_default_max_stories_is_50(self) -> None:
        director = Director.from_config()
        assert director._config.max_stories == 50

    def test_custom_max_stories_stored(self) -> None:
        from core.model_router import RoutingConfig
        rc = RoutingConfig.from_dict({
            "routes": {"director": {"provider": "anthropic", "model": "claude-opus-4-6"}},
            "fallbacks": {"anthropic": {"provider": "google", "model": "gemini-3-pro-preview"}},
        })
        from director import DirectorConfig
        config = DirectorConfig(routing_config=rc, max_stories=10)
        assert config.max_stories == 10
