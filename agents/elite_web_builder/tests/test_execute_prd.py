"""
Tests for execute_prd pipeline — PlanningError, ProjectReport,
_parse_planning_response, _build_breakdown, _plan_stories, execute_prd.

Mocking pattern: mock get_adapter to return a fake adapter that
returns LLMResponse with pre-defined JSON content.
"""

from __future__ import annotations

import json
import pytest
import time
from dataclasses import FrozenInstanceError
from unittest.mock import AsyncMock, MagicMock, patch

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
    _DIRECTOR_SPEC,
    _PLANNING_PROMPT_TEMPLATE,
)
from elite_web_builder.core.learning_journal import LearningJournal
from elite_web_builder.core.model_router import LLMResponse, ModelRouter


# =============================================================================
# Helpers
# =============================================================================


def _make_planning_json(
    num_stories: int = 3,
    roles: list[str] | None = None,
) -> str:
    """
    Create a planning JSON string containing a list of user stories and their dependency order.
    
    Parameters:
        num_stories (int): Number of user stories to generate.
        roles (list[str] | None): List of agent role names to assign to stories; roles are assigned cyclically. If None, defaults to ["design_system", "frontend_dev", "backend_dev"].
    
    Returns:
        str: JSON-formatted string with two keys:
            - "stories": list of story objects, each containing:
                - "id": story id in the form "US-###" (zero-padded).
                - "title": story title.
                - "description": story description.
                - "agent_role": assigned role name.
                - "depends_on": list of prerequisite story ids.
                - "acceptance_criteria": list of acceptance criteria strings.
            - "dependency_order": list of story ids in the generated order.
    """
    roles = roles or ["design_system", "frontend_dev", "backend_dev"]
    stories = []
    order = []
    for i in range(num_stories):
        sid = f"US-{i + 1:03d}"
        role = roles[i % len(roles)]
        deps = [f"US-{i:03d}"] if i > 0 else []
        stories.append({
            "id": sid,
            "title": f"Story {i + 1}",
            "description": f"Description for story {i + 1}",
            "agent_role": role,
            "depends_on": deps,
            "acceptance_criteria": [f"Criterion for story {i + 1}"],
        })
        order.append(sid)
    return json.dumps({"stories": stories, "dependency_order": order})


def _make_fake_adapter(content: str = "OK") -> AsyncMock:
    """
    Create an asynchronous mock adapter whose `generate` method returns an LLMResponse containing the provided content.
    
    Parameters:
    	content (str): The content to put in the mocked LLMResponse.
    
    Returns:
    	AsyncMock: An AsyncMock adapter with a `generate` coroutine that returns an LLMResponse whose `content` equals `content`.
    """
    adapter = AsyncMock()
    adapter.generate = AsyncMock(
        return_value=LLMResponse(
            content=content,
            provider="test",
            model="test-model",
            latency_ms=100.0,
        )
    )
    return adapter


def _make_director_with_mock(planning_response: str = "", story_response: str = "OK") -> Director:
    """
    Create a Director whose ModelRouter is populated with a single test adapter that returns controlled responses.
    
    The returned Director uses a router with route entries for the director and common agent roles all pointing to the "test" provider. The test adapter's generate method is mocked so that the first invocation returns the provided planning_response content and all subsequent invocations return the provided story_response content.
    
    Parameters:
        planning_response (str): JSON or text to return on the first generate call (planning phase).
        story_response (str): Text to return on subsequent generate calls (per-story responses).
    
    Returns:
        Director: A Director instance wired to the mocked ModelRouter and test adapter.
    """
    router = ModelRouter(
        routing={
            "director": {"provider": "test", "model": "test"},
            "design_system": {"provider": "test", "model": "test"},
            "frontend_dev": {"provider": "test", "model": "test"},
            "backend_dev": {"provider": "test", "model": "test"},
            "accessibility": {"provider": "test", "model": "test"},
            "performance": {"provider": "test", "model": "test"},
            "seo_content": {"provider": "test", "model": "test"},
            "qa": {"provider": "test", "model": "test"},
        },
        fallbacks={},
    )

    # First call returns planning response, subsequent calls return story response
    call_count = 0
    original_content = planning_response

    async def mock_generate(prompt, *, system_prompt="", model="", temperature=0.7, max_tokens=4096):
        """
        Mock async generate function that returns a planning response on the first call and story responses on subsequent calls.
        
        Parameters:
        	prompt (str): The prompt sent to the model.
        	system_prompt (str): Optional system prompt (accepted but not used by the mock).
        	model (str): Optional model identifier (accepted but not used by the mock).
        	temperature (float): Optional sampling temperature (accepted but not used by the mock).
        	max_tokens (int): Optional token limit (accepted but not used by the mock).
        
        Returns:
        	LLMResponse: An LLMResponse containing `original_content` on the first invocation and `story_response` on subsequent invocations.
        
        Notes:
        	Increments the enclosing `call_count` nonlocal variable on each invocation.
        """
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return LLMResponse(
                content=original_content,
                provider="test",
                model="test",
                latency_ms=50.0,
            )
        return LLMResponse(
            content=story_response,
            provider="test",
            model="test",
            latency_ms=50.0,
        )

    adapter = AsyncMock()
    adapter.generate = mock_generate
    router.register_adapter("test", adapter)

    return Director(router=router)


# =============================================================================
# TestPlanningError
# =============================================================================


class TestPlanningError:
    """Tests for PlanningError exception."""

    def test_inherits_runtime_error(self):
        err = PlanningError("test")
        assert isinstance(err, RuntimeError)

    def test_has_raw_response(self):
        err = PlanningError("test", raw_response="raw json here")
        assert err.raw_response == "raw json here"
        assert str(err) == "test"


# =============================================================================
# TestProjectReport
# =============================================================================


class TestProjectReport:
    """Tests for ProjectReport frozen dataclass."""

    def test_frozen(self):
        report = ProjectReport(
            stories=(),
            status_summary={},
            all_green=True,
            elapsed_ms=100.0,
            failures=(),
            instincts_learned=0,
        )
        with pytest.raises(FrozenInstanceError):
            report.all_green = False  # type: ignore[misc]

    def test_all_green_true(self):
        report = ProjectReport(
            stories=(),
            status_summary={"green": 3},
            all_green=True,
            elapsed_ms=100.0,
            failures=(),
            instincts_learned=0,
        )
        assert report.all_green is True

    def test_failures_tuple(self):
        report = ProjectReport(
            stories=(),
            status_summary={},
            all_green=False,
            elapsed_ms=100.0,
            failures=("US-001: Failed",),
            instincts_learned=0,
        )
        assert isinstance(report.failures, tuple)
        assert len(report.failures) == 1


# =============================================================================
# TestParsePlanningResponse
# =============================================================================


class TestParsePlanningResponse:
    """Tests for Director._parse_planning_response."""

    def test_valid_json(self):
        raw = '{"stories": [], "dependency_order": []}'
        result = Director._parse_planning_response(raw)
        assert result == {"stories": [], "dependency_order": []}

    def test_json_with_markdown_fences(self):
        raw = '```json\n{"stories": [], "dependency_order": []}\n```'
        result = Director._parse_planning_response(raw)
        assert result == {"stories": [], "dependency_order": []}

    def test_json_with_bare_fences(self):
        raw = '```\n{"stories": []}\n```'
        result = Director._parse_planning_response(raw)
        assert result == {"stories": []}

    def test_invalid_json_raises(self):
        with pytest.raises(PlanningError) as exc_info:
            Director._parse_planning_response("not json at all")
        assert "Invalid JSON" in str(exc_info.value)
        assert exc_info.value.raw_response == "not json at all"

    def test_empty_string_raises(self):
        with pytest.raises(PlanningError):
            Director._parse_planning_response("")


# =============================================================================
# TestBuildBreakdown
# =============================================================================


class TestBuildBreakdown:
    """Tests for Director._build_breakdown."""

    def test_happy_path(self):
        data = json.loads(_make_planning_json(3))
        breakdown = Director._build_breakdown(data)
        assert len(breakdown.stories) == 3
        assert breakdown.stories[0].id == "US-001"
        assert breakdown.stories[0].agent_role == AgentRole.DESIGN_SYSTEM

    def test_missing_stories_key(self):
        with pytest.raises(PlanningError, match="missing 'stories' key"):
            Director._build_breakdown({"no_stories": []})

    def test_unknown_role(self):
        data = {
            "stories": [{
                "id": "US-001",
                "title": "Test",
                "description": "Test",
                "agent_role": "nonexistent_role",
            }],
        }
        with pytest.raises(PlanningError, match="Unknown agent_role"):
            Director._build_breakdown(data)

    def test_missing_required_field(self):
        data = {
            "stories": [{
                "id": "US-001",
                "title": "Test",
                # missing description and agent_role
            }],
        }
        with pytest.raises(PlanningError, match="missing required field"):
            Director._build_breakdown(data)

    def test_max_stories_truncation(self):
        data = json.loads(_make_planning_json(10))
        breakdown = Director._build_breakdown(data, max_stories=5)
        assert len(breakdown.stories) == 5


# =============================================================================
# TestPlanStories
# =============================================================================


class TestPlanStories:
    """Tests for Director._plan_stories."""

    @pytest.mark.asyncio
    async def test_returns_breakdown(self):
        planning_json = _make_planning_json(3)
        director = _make_director_with_mock(planning_response=planning_json)
        breakdown = await director._plan_stories("Build a website")
        assert isinstance(breakdown, PRDBreakdown)
        assert len(breakdown.stories) == 3

    @pytest.mark.asyncio
    async def test_propagates_planning_error(self):
        director = _make_director_with_mock(planning_response="not json")
        with pytest.raises(PlanningError):
            await director._plan_stories("Build a website")

    @pytest.mark.asyncio
    async def test_max_stories_in_prompt(self):
        planning_json = _make_planning_json(2)
        config = DirectorConfig(max_stories=25)
        router = ModelRouter(
            routing={"director": {"provider": "test", "model": "test"}},
            fallbacks={},
        )

        captured_prompt = None

        async def capture_generate(prompt, **kwargs):
            """
            Capture the provided prompt into the enclosing scope and return a canned planning LLMResponse.
            
            Parameters:
                prompt (str): The prompt text passed to the model; stored into the outer-scope variable `captured_prompt`.
                **kwargs: Additional keyword arguments accepted by the call and ignored by this test helper.
            
            Returns:
                LLMResponse: A fabricated response with content set to `planning_json`, provider `"test"`, model `"test"`, and latency_ms `50`.
            """
            nonlocal captured_prompt
            captured_prompt = prompt
            return LLMResponse(content=planning_json, provider="test", model="test", latency_ms=50)

        adapter = AsyncMock()
        adapter.generate = capture_generate
        router.register_adapter("test", adapter)

        director = Director(config=config, router=router)
        await director._plan_stories("Build something")
        assert "25 stories" in captured_prompt

    @pytest.mark.asyncio
    async def test_uses_director_spec(self):
        planning_json = _make_planning_json(1, roles=["qa"])
        router = ModelRouter(
            routing={"director": {"provider": "test", "model": "test"}},
            fallbacks={},
        )

        captured_system_prompt = None

        async def capture_generate(prompt, *, system_prompt="", **kwargs):
            """
            Capture the provided system prompt and return a canned LLMResponse for testing.
            
            Parameters:
                prompt (str): The user prompt passed to the generator.
                system_prompt (str): The system-level prompt; its value is saved to the outer-scope variable `captured_system_prompt`.
                **kwargs: Additional keyword arguments are accepted and ignored.
            
            Returns:
                LLMResponse: A response with `content` set to the test planning JSON, `provider` and `model` set to "test", and `latency_ms` equal to 50.
            """
            nonlocal captured_system_prompt
            captured_system_prompt = system_prompt
            return LLMResponse(content=planning_json, provider="test", model="test", latency_ms=50)

        adapter = AsyncMock()
        adapter.generate = capture_generate
        router.register_adapter("test", adapter)

        director = Director(router=router)
        await director._plan_stories("PRD text")
        assert "Director" in captured_system_prompt
        assert "JSON" in captured_system_prompt


# =============================================================================
# TestExecutePrd
# =============================================================================


class TestExecutePrd:
    """Tests for Director.execute_prd."""

    @pytest.mark.asyncio
    async def test_planning_failure_returns_report(self):
        director = _make_director_with_mock(planning_response="not json")
        report = await director.execute_prd("Build a site")
        assert isinstance(report, ProjectReport)
        assert report.all_green is False
        assert len(report.failures) == 1
        assert "Planning failed" in report.failures[0]

    @pytest.mark.asyncio
    async def test_all_green(self):
        planning_json = _make_planning_json(2, roles=["design_system", "frontend_dev"])
        director = _make_director_with_mock(
            planning_response=planning_json,
            story_response="Story completed successfully",
        )
        report = await director.execute_prd("Build a website")
        assert report.all_green is True
        assert len(report.stories) == 2
        assert report.status_summary.get("green", 0) == 2

    @pytest.mark.asyncio
    async def test_failed_story_captured(self):
        planning_json = json.dumps({
            "stories": [{
                "id": "US-001",
                "title": "Failing story",
                "description": "This will fail",
                "agent_role": "design_system",
                "depends_on": [],
                "acceptance_criteria": [],
            }],
            "dependency_order": ["US-001"],
        })
        router = ModelRouter(
            routing={
                "director": {"provider": "test", "model": "test"},
                "design_system": {"provider": "fail", "model": "test"},
            },
            fallbacks={},
        )

        # Planning adapter succeeds
        call_count = 0

        async def mock_generate(prompt, **kwargs):
            """
            Return a canned LLMResponse that yields a planning JSON on the first invocation and "OK" on subsequent invocations.
            
            Parameters:
            	prompt (Any): The prompt passed to the mock; its value is not inspected by the mock.
            	**kwargs: Ignored; present for compatibility with the real adapter signature.
            
            Returns:
            	LLMResponse: On the first call, an LLMResponse whose `content` is the `planning_json` variable; on later calls, an LLMResponse whose `content` is "OK". In both cases `provider` is "test", `model` is "test", and `latency_ms` is 50.
            
            Side effects:
            	Increments the outer-scope `call_count` on each invocation to track call order.
            """
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return LLMResponse(content=planning_json, provider="test", model="test", latency_ms=50)
            return LLMResponse(content="OK", provider="test", model="test", latency_ms=50)

        adapter = AsyncMock()
        adapter.generate = mock_generate
        router.register_adapter("test", adapter)

        # Failing adapter
        fail_adapter = AsyncMock()
        fail_adapter.generate = AsyncMock(side_effect=RuntimeError("Provider down"))
        router.register_adapter("fail", fail_adapter)

        director = Director(router=router)
        report = await director.execute_prd("Build something")
        assert report.all_green is False
        assert len(report.failures) >= 1

    @pytest.mark.asyncio
    async def test_elapsed_ms(self):
        planning_json = _make_planning_json(1, roles=["qa"])
        director = _make_director_with_mock(
            planning_response=planning_json,
            story_response="Done",
        )
        report = await director.execute_prd("Quick PRD")
        assert report.elapsed_ms > 0

    @pytest.mark.asyncio
    async def test_stories_are_snapshot(self):
        planning_json = _make_planning_json(1, roles=["qa"])
        director = _make_director_with_mock(
            planning_response=planning_json,
            story_response="Done",
        )
        report = await director.execute_prd("PRD")
        assert isinstance(report.stories, tuple)
        # Modify director's internal state — report should not change
        original_count = len(report.stories)
        director._stories.clear()
        assert len(report.stories) == original_count

    @pytest.mark.asyncio
    async def test_instincts_count(self):
        planning_json = _make_planning_json(1, roles=["qa"])
        journal = LearningJournal()
        router = ModelRouter(
            routing={
                "director": {"provider": "test", "model": "test"},
                "qa": {"provider": "test", "model": "test"},
            },
            fallbacks={},
        )
        adapter = _make_fake_adapter(planning_json)

        call_count = 0
        original_generate = adapter.generate

        async def counting_generate(prompt, **kwargs):
            """
            Simulates an async model generate that returns a planning response on the first call and a generic "OK" response thereafter.
            
            Increments the surrounding `call_count` each time it is invoked to track number of calls.
            
            Parameters:
                prompt (str): The prompt passed to the model.
                **kwargs: Additional generation options (ignored by this mock).
            
            Returns:
                LLMResponse: On the first invocation, an LLMResponse whose `content` is the planning JSON; on subsequent invocations, an LLMResponse whose `content` is "OK". Both responses have `provider="test"`, `model="test"`, and `latency_ms=50`.
            """
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return LLMResponse(content=planning_json, provider="test", model="test", latency_ms=50)
            return LLMResponse(content="OK", provider="test", model="test", latency_ms=50)

        adapter.generate = counting_generate
        router.register_adapter("test", adapter)
        director = Director(router=router, journal=journal)

        report = await director.execute_prd("PRD text")
        assert report.instincts_learned == 0  # No learning in this test

    @pytest.mark.asyncio
    async def test_cycle_guard(self):
        """Stories with unresolvable circular deps should not loop forever."""
        planning_json = json.dumps({
            "stories": [
                {
                    "id": "US-001",
                    "title": "Story A",
                    "description": "Depends on B",
                    "agent_role": "design_system",
                    "depends_on": ["US-002"],
                },
                {
                    "id": "US-002",
                    "title": "Story B",
                    "description": "Depends on A",
                    "agent_role": "frontend_dev",
                    "depends_on": ["US-001"],
                },
            ],
            "dependency_order": ["US-001", "US-002"],
        })
        director = _make_director_with_mock(planning_response=planning_json)
        report = await director.execute_prd("Circular PRD")
        # Should complete without infinite loop
        # Stories remain PENDING (no ready stories due to cycle)
        assert report.all_green is False

    @pytest.mark.asyncio
    async def test_empty_prd(self):
        planning_json = json.dumps({"stories": [], "dependency_order": []})
        director = _make_director_with_mock(planning_response=planning_json)
        report = await director.execute_prd("")
        assert report.all_green is True  # No stories = vacuously all green
        assert len(report.stories) == 0


# =============================================================================
# TestDirectorConfigMaxStories
# =============================================================================


class TestDirectorConfigMaxStories:
    """Tests for DirectorConfig.max_stories field."""

    def test_default_50(self):
        config = DirectorConfig()
        assert config.max_stories == 50

    def test_custom_value(self):
        config = DirectorConfig(max_stories=25)
        assert config.max_stories == 25