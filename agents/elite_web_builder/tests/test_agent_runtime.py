"""Tests for AgentRuntime — the bridge from AgentSpec to LLM execution."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.base import AgentCapability, AgentOutput, AgentRole, AgentSpec
from agents.provider_adapters import LLMMessage, LLMResponse
from agents.runtime import AgentRuntime
from core.ground_truth import GroundTruthValidator
from core.learning_journal import LearningJournal
from core.model_router import ModelRouter, RoutingConfig


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def routing_config():
    return RoutingConfig.from_dict({
        "routes": {
            "frontend_dev": {"provider": "anthropic", "model": "claude-sonnet-4-6"},
            "design_system": {"provider": "google", "model": "gemini-3-pro-preview"},
        },
        "fallbacks": {
            "anthropic": {"provider": "google", "model": "gemini-3-pro-preview"},
            "google": {"provider": "anthropic", "model": "claude-sonnet-4-6"},
        },
    })


@pytest.fixture
def router(routing_config):
    return ModelRouter(config=routing_config)


@pytest.fixture
def validator():
    return GroundTruthValidator()


@pytest.fixture
def journal(tmp_path):
    return LearningJournal(storage_dir=tmp_path)


@pytest.fixture
def runtime(router, validator, journal):
    return AgentRuntime(router=router, validator=validator, journal=journal)


@pytest.fixture
def frontend_spec():
    return AgentSpec(
        role=AgentRole.FRONTEND_DEV,
        name="frontend_dev",
        system_prompt="You are a Frontend Development specialist.",
        capabilities=[
            AgentCapability(
                name="html_templates",
                description="Create HTML templates",
                tags=("frontend", "html"),
            ),
        ],
        knowledge_files=["knowledge/wordpress.md"],
    )


@pytest.fixture
def design_spec():
    return AgentSpec(
        role=AgentRole.DESIGN_SYSTEM,
        name="design_system",
        system_prompt="You are a Design System specialist.",
    )


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------


class TestBuildMessages:
    def test_basic_prompt(self, runtime, frontend_spec):
        messages = runtime._build_messages(frontend_spec, "Create a nav component")
        assert len(messages) >= 2
        # System message first
        assert messages[0].role == "system"
        assert "Frontend Development specialist" in messages[0].content
        # User message last
        assert messages[-1].role == "user"
        assert "nav component" in messages[-1].content

    def test_includes_learning_context(self, runtime, frontend_spec, journal):
        from core.learning_journal import JournalEntry

        journal.add_entry(JournalEntry(
            mistake="Used hardcoded colors",
            correct="Use CSS custom properties",
            agent="frontend_dev",
            story_id="US-001",
        ))

        messages = runtime._build_messages(frontend_spec, "Style the header")
        system_content = messages[0].content
        assert "hardcoded colors" in system_content
        assert "CSS custom properties" in system_content

    def test_no_learning_context_when_empty(self, runtime, design_spec):
        messages = runtime._build_messages(design_spec, "Generate palette")
        system_content = messages[0].content
        assert "Learning Rules" not in system_content

    def test_includes_knowledge_reference(self, runtime, frontend_spec):
        messages = runtime._build_messages(frontend_spec, "Create block pattern")
        system_content = messages[0].content
        assert "knowledge/wordpress.md" in system_content


# ---------------------------------------------------------------------------
# Execute
# ---------------------------------------------------------------------------


class TestExecute:
    @pytest.mark.asyncio
    async def test_success(self, runtime, frontend_spec):
        mock_response = LLMResponse(
            text="```html\n<nav>...</nav>\n```",
            provider="anthropic",
            model="claude-sonnet-4-6",
            usage={"input_tokens": 200, "output_tokens": 100},
        )

        mock_adapter = AsyncMock()
        mock_adapter.call.return_value = mock_response

        with patch("agents.runtime.get_adapter", return_value=mock_adapter):
            result = await runtime.execute(
                spec=frontend_spec,
                task="Create a navigation component",
                story_id="US-001",
            )

        assert isinstance(result, AgentOutput)
        assert result.agent == "frontend_dev"
        assert result.story_id == "US-001"
        assert "<nav>" in result.content
        assert result.metadata["provider"] == "anthropic"
        assert result.metadata["model"] == "claude-sonnet-4-6"

    @pytest.mark.asyncio
    async def test_routes_to_correct_provider(self, runtime, design_spec):
        mock_response = LLMResponse(
            text='{"colors": {}}',
            provider="google",
            model="gemini-3-pro-preview",
            usage={"input_tokens": 50, "output_tokens": 30},
        )

        mock_adapter = AsyncMock()
        mock_adapter.call.return_value = mock_response

        with patch("agents.runtime.get_adapter", return_value=mock_adapter) as mock_get:
            await runtime.execute(
                spec=design_spec,
                task="Generate color palette",
            )

        # Should have been called with the google adapter
        mock_get.assert_called_once_with("google")

    @pytest.mark.asyncio
    async def test_fallback_on_provider_failure(self, runtime, frontend_spec):
        """When primary provider fails, should try fallback."""
        mock_adapter_fail = AsyncMock()
        mock_adapter_fail.call.side_effect = Exception("API down")

        mock_adapter_ok = AsyncMock()
        mock_adapter_ok.call.return_value = LLMResponse(
            text="fallback response",
            provider="google",
            model="gemini-3-pro-preview",
            usage={"input_tokens": 50, "output_tokens": 30},
        )

        call_count = 0

        def side_effect_get_adapter(provider):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_adapter_fail
            return mock_adapter_ok

        with patch("agents.runtime.get_adapter", side_effect=side_effect_get_adapter):
            result = await runtime.execute(
                spec=frontend_spec,
                task="Build something",
                story_id="US-002",
            )

        assert result.content == "fallback response"
        assert result.metadata["is_fallback"] is True

    @pytest.mark.asyncio
    async def test_all_providers_fail(self, runtime, frontend_spec):
        mock_adapter = AsyncMock()
        mock_adapter.call.side_effect = Exception("All dead")

        with patch("agents.runtime.get_adapter", return_value=mock_adapter):
            with pytest.raises(RuntimeError, match="All providers exhausted"):
                await runtime.execute(
                    spec=frontend_spec,
                    task="Impossible task",
                )

    @pytest.mark.asyncio
    async def test_records_usage_metadata(self, runtime, frontend_spec):
        mock_response = LLMResponse(
            text="result",
            provider="anthropic",
            model="claude-sonnet-4-6",
            usage={"input_tokens": 500, "output_tokens": 250},
        )

        mock_adapter = AsyncMock()
        mock_adapter.call.return_value = mock_response

        with patch("agents.runtime.get_adapter", return_value=mock_adapter):
            result = await runtime.execute(
                spec=frontend_spec,
                task="Generate",
                story_id="US-003",
            )

        assert result.metadata["usage"]["input_tokens"] == 500
        assert result.metadata["usage"]["output_tokens"] == 250


# ---------------------------------------------------------------------------
# File extraction
# ---------------------------------------------------------------------------


class TestExtractFiles:
    def test_extracts_file_paths(self, runtime):
        content = (
            "I created the following files:\n"
            "- `theme.json`\n"
            "- `functions.php`\n"
            "```php\n// functions.php\n<?php\n```"
        )
        files = runtime._extract_files(content)
        assert "theme.json" in files
        assert "functions.php" in files

    def test_empty_content(self, runtime):
        files = runtime._extract_files("")
        assert files == ()

    def test_no_files_mentioned(self, runtime):
        files = runtime._extract_files("Just a general response about CSS.")
        assert files == ()


# ---------------------------------------------------------------------------
# Integration: Runtime + Router health tracking
# ---------------------------------------------------------------------------


class TestRuntimeRouterIntegration:
    @pytest.mark.asyncio
    async def test_unhealthy_primary_uses_fallback(self, runtime, frontend_spec):
        """If primary provider is marked unhealthy, runtime should use fallback."""
        # Mark anthropic as unhealthy
        runtime._router.mark_unhealthy("anthropic")

        mock_response = LLMResponse(
            text="from fallback",
            provider="google",
            model="gemini-3-pro-preview",
            usage={"input_tokens": 10, "output_tokens": 5},
        )

        mock_adapter = AsyncMock()
        mock_adapter.call.return_value = mock_response

        with patch("agents.runtime.get_adapter", return_value=mock_adapter) as mock_get:
            result = await runtime.execute(
                spec=frontend_spec,
                task="Quick task",
            )

        # Should route to google (fallback for anthropic)
        mock_get.assert_called_with("google")
        assert result.metadata["is_fallback"] is True
