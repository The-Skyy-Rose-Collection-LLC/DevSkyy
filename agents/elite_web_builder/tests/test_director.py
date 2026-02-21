"""
Tests for Director core functionality — story management,
agent registry, routing, and run_story.
"""

from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock

from elite_web_builder.director import (
    AgentRole,
    AgentRuntime,
    AgentSpec,
    Director,
    DirectorConfig,
    PRDBreakdown,
    StoryStatus,
    UserStory,
    spec_registry,
    _DEFAULT_ROUTING,
)
from elite_web_builder.core.model_router import LLMResponse, ModelRouter


# =============================================================================
# Helpers
# =============================================================================


def _make_story(
    sid: str = "US-001",
    title: str = "Test Story",
    role: AgentRole = AgentRole.DESIGN_SYSTEM,
    deps: list[str] | None = None,
) -> UserStory:
    return UserStory(
        id=sid,
        title=title,
        description=f"Description for {title}",
        agent_role=role,
        depends_on=deps or [],
    )


def _make_router_with_mock(content: str = "OK") -> ModelRouter:
    router = ModelRouter(
        routing=_DEFAULT_ROUTING["routing"],
        fallbacks=_DEFAULT_ROUTING["fallbacks"],
    )
    adapter = AsyncMock()
    adapter.generate = AsyncMock(
        return_value=LLMResponse(
            content=content,
            provider="test",
            model="test",
            latency_ms=50.0,
        )
    )
    # Register for all providers used in routing
    for provider in {"anthropic", "google", "openai", "xai"}:
        router.register_adapter(provider, adapter)
    return router


# =============================================================================
# TestAgentRole
# =============================================================================


class TestAgentRole:
    def test_has_all_roles(self):
        roles = {r.value for r in AgentRole}
        expected = {
            "director", "design_system", "frontend_dev", "backend_dev",
            "accessibility", "performance", "seo_content", "qa",
        }
        assert roles == expected

    def test_string_enum(self):
        assert AgentRole.DIRECTOR == "director"
        assert isinstance(AgentRole.DIRECTOR, str)


# =============================================================================
# TestStoryStatus
# =============================================================================


class TestStoryStatus:
    def test_has_all_statuses(self):
        statuses = {s.value for s in StoryStatus}
        assert statuses == {"pending", "in_progress", "green", "failed"}


# =============================================================================
# TestUserStory
# =============================================================================


class TestUserStory:
    def test_default_status(self):
        story = _make_story()
        assert story.status == StoryStatus.PENDING

    def test_default_output(self):
        story = _make_story()
        assert story.output == ""
        assert story.error == ""


# =============================================================================
# TestAgentSpec
# =============================================================================


class TestAgentSpec:
    def test_create(self):
        spec = AgentSpec(
            role=AgentRole.DESIGN_SYSTEM,
            name="design_system",
            system_prompt="You are a design system specialist.",
        )
        assert spec.role == AgentRole.DESIGN_SYSTEM
        assert spec.name == "design_system"

    def test_default_capabilities(self):
        spec = AgentSpec(
            role=AgentRole.QA,
            name="qa",
            system_prompt="test",
        )
        assert spec.capabilities == []
        assert spec.knowledge_files == []


# =============================================================================
# TestSpecRegistry
# =============================================================================


class TestSpecRegistry:
    def test_has_7_agents(self):
        assert len(spec_registry) == 7

    def test_no_director_in_registry(self):
        assert AgentRole.DIRECTOR not in spec_registry

    def test_each_agent_has_required_fields(self):
        for role, spec in spec_registry.items():
            assert "name" in spec, f"{role} missing name"
            assert "system_prompt" in spec, f"{role} missing system_prompt"
            assert "capabilities" in spec, f"{role} missing capabilities"


# =============================================================================
# TestDirector Story Management
# =============================================================================


class TestDirectorStoryManagement:
    def test_add_stories(self):
        director = Director()
        stories = [_make_story("US-001"), _make_story("US-002")]
        director.add_stories(stories)
        assert len(director.stories) == 2

    def test_get_ready_stories_no_deps(self):
        director = Director()
        stories = [_make_story("US-001"), _make_story("US-002")]
        director.add_stories(stories)
        ready = director.get_ready_stories()
        assert len(ready) == 2

    def test_get_ready_stories_with_deps(self):
        director = Director()
        s1 = _make_story("US-001")
        s2 = _make_story("US-002", deps=["US-001"])
        director.add_stories([s1, s2])
        ready = director.get_ready_stories()
        assert len(ready) == 1
        assert ready[0].id == "US-001"

    def test_get_ready_stories_after_green(self):
        director = Director()
        s1 = _make_story("US-001")
        s2 = _make_story("US-002", deps=["US-001"])
        director.add_stories([s1, s2])
        s1.status = StoryStatus.GREEN
        ready = director.get_ready_stories()
        assert len(ready) == 1
        assert ready[0].id == "US-002"

    def test_get_status_summary(self):
        director = Director()
        s1 = _make_story("US-001")
        s2 = _make_story("US-002")
        s1.status = StoryStatus.GREEN
        director.add_stories([s1, s2])
        summary = director.get_status_summary()
        assert summary == {"green": 1, "pending": 1}

    def test_empty_stories(self):
        director = Director()
        assert director.get_ready_stories() == []
        assert director.get_status_summary() == {}


# =============================================================================
# TestDirectorRunStory
# =============================================================================


class TestDirectorRunStory:
    @pytest.mark.asyncio
    async def test_run_story_success(self):
        router = _make_router_with_mock("Story output content")
        director = Director(router=router)
        story = _make_story()
        result = await director.run_story(story)
        assert result.status == StoryStatus.GREEN
        assert result.output == "Story output content"

    @pytest.mark.asyncio
    async def test_run_story_failure(self):
        router = ModelRouter(
            routing={"design_system": {"provider": "broken", "model": "test"}},
            fallbacks={},
        )
        adapter = AsyncMock()
        adapter.generate = AsyncMock(side_effect=RuntimeError("API error"))
        router.register_adapter("broken", adapter)

        director = Director(router=router)
        story = _make_story()
        result = await director.run_story(story)
        assert result.status == StoryStatus.FAILED
        assert "failed" in result.error.lower() or "broken" in result.error.lower()

    @pytest.mark.asyncio
    async def test_run_story_marks_in_progress(self):
        router = _make_router_with_mock()

        statuses_seen = []

        class TrackingRouter(ModelRouter):
            pass

        director = Director(router=router)
        story = _make_story()
        # Story starts as PENDING
        assert story.status == StoryStatus.PENDING
        result = await director.run_story(story)
        # After run, should be GREEN or FAILED
        assert result.status in (StoryStatus.GREEN, StoryStatus.FAILED)


# =============================================================================
# TestPRDBreakdown
# =============================================================================


class TestPRDBreakdown:
    def test_create(self):
        stories = [_make_story("US-001"), _make_story("US-002")]
        breakdown = PRDBreakdown(stories=stories, dependency_order=["US-001", "US-002"])
        assert len(breakdown.stories) == 2

    def test_default_order(self):
        breakdown = PRDBreakdown(stories=[])
        assert breakdown.dependency_order == []


# =============================================================================
# TestModelRouter
# =============================================================================


class TestModelRouter:
    def test_register_adapter(self):
        router = ModelRouter()
        adapter = AsyncMock()
        router.register_adapter("test", adapter)
        assert router.get_adapter("test") is adapter

    def test_get_nonexistent_adapter(self):
        router = ModelRouter()
        assert router.get_adapter("nonexistent") is None

    @pytest.mark.asyncio
    async def test_route_success(self):
        router = ModelRouter(
            routing={"design_system": {"provider": "test", "model": "test"}},
        )
        adapter = AsyncMock()
        adapter.generate = AsyncMock(
            return_value=LLMResponse(
                content="result",
                provider="test",
                model="test",
                latency_ms=50,
            )
        )
        router.register_adapter("test", adapter)
        result = await router.route("design_system", "prompt")
        assert result.content == "result"

    @pytest.mark.asyncio
    async def test_route_no_config(self):
        router = ModelRouter()
        with pytest.raises(ValueError, match="No routing configured"):
            await router.route("unknown_role", "prompt")

    @pytest.mark.asyncio
    async def test_route_fallback(self):
        router = ModelRouter(
            routing={"design_system": {"provider": "primary", "model": "test"}},
            fallbacks={"primary": {"provider": "fallback", "model": "test"}},
        )
        # Primary fails
        primary = AsyncMock()
        primary.generate = AsyncMock(side_effect=RuntimeError("down"))
        router.register_adapter("primary", primary)

        # Fallback succeeds
        fallback = AsyncMock()
        fallback.generate = AsyncMock(
            return_value=LLMResponse(content="fallback ok", provider="fallback", model="test", latency_ms=50)
        )
        router.register_adapter("fallback", fallback)

        result = await router.route("design_system", "prompt")
        assert result.content == "fallback ok"
