"""
Unit tests for LiteLLM universal provider.
============================================
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from llm.base import Message, ModelProvider
from llm.providers.litellm_provider import _PROVIDER_MODEL_MAP, LiteLLMClient


class TestModelStringMapping:
    def test_provider_model_map_completeness(self):
        """All non-LITELLM providers should have a model mapping."""
        for provider in ModelProvider:
            if provider != ModelProvider.LITELLM:
                assert provider in _PROVIDER_MODEL_MAP, f"Missing mapping for {provider}"

    def test_get_model_string_with_provider(self):
        """Should return mapped model string for known providers."""
        result = LiteLLMClient.get_model_string(ModelProvider.ANTHROPIC)
        assert result == "anthropic/claude-sonnet-4-20250514"

    def test_get_model_string_with_override(self):
        """Should use override model with provider prefix."""
        result = LiteLLMClient.get_model_string(ModelProvider.OPENAI, "gpt-4o")
        assert result == "openai/gpt-4o"

    def test_get_model_string_with_full_model(self):
        """Should pass through model strings that already have provider prefix."""
        result = LiteLLMClient.get_model_string(ModelProvider.OPENAI, "openai/gpt-4o")
        assert result == "openai/gpt-4o"


class TestLiteLLMClient:
    def test_init_defaults(self):
        """Should initialize with default model."""
        client = LiteLLMClient()
        assert client.provider == "litellm"
        assert client._default_model == "anthropic/claude-sonnet-4-20250514"

    def test_init_custom_model(self):
        """Should accept custom default model."""
        client = LiteLLMClient(model="openai/gpt-4o")
        assert client._default_model == "openai/gpt-4o"

    def test_get_headers_empty(self):
        """Headers should be empty -- LiteLLM handles auth via env vars."""
        client = LiteLLMClient()
        assert client._get_headers() == {}

    @pytest.mark.asyncio
    async def test_complete_calls_litellm(self):
        """Should call litellm.acompletion with correct params."""
        client = LiteLLMClient()

        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20

        mock_choice = MagicMock()
        mock_choice.message.content = "Hello world"
        mock_choice.finish_reason = "stop"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        mock_litellm = MagicMock()
        mock_litellm.acompletion = AsyncMock(return_value=mock_response)
        mock_litellm.completion_cost = MagicMock(return_value=0.001)
        mock_litellm.suppress_debug_info = False
        mock_litellm.set_verbose = False

        client._litellm = mock_litellm

        messages = [Message.user("Hello")]
        response = await client.complete(messages, model="openai/gpt-4o")

        assert response.content == "Hello world"
        assert response.input_tokens == 10
        assert response.output_tokens == 20
        assert response.provider == "litellm"
        mock_litellm.acompletion.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_raises_on_auth_error(self):
        """Should raise AuthenticationError for 401 errors."""
        from llm.exceptions import AuthenticationError

        client = LiteLLMClient()
        mock_litellm = MagicMock()
        mock_litellm.acompletion = AsyncMock(side_effect=Exception("401 authentication failed"))
        mock_litellm.suppress_debug_info = False
        mock_litellm.set_verbose = False
        client._litellm = mock_litellm

        with pytest.raises(AuthenticationError):
            await client.complete([Message.user("test")])

    @pytest.mark.asyncio
    async def test_complete_raises_on_rate_limit(self):
        """Should raise RateLimitError for 429 errors."""
        from llm.exceptions import RateLimitError

        client = LiteLLMClient()
        mock_litellm = MagicMock()
        mock_litellm.acompletion = AsyncMock(side_effect=Exception("429 rate limit exceeded"))
        mock_litellm.suppress_debug_info = False
        mock_litellm.set_verbose = False
        client._litellm = mock_litellm

        with pytest.raises(RateLimitError):
            await client.complete([Message.user("test")])

    @pytest.mark.asyncio
    async def test_complete_raises_on_service_unavailable(self):
        """Should raise ServiceUnavailableError for 503 errors."""
        from llm.exceptions import ServiceUnavailableError

        client = LiteLLMClient()
        mock_litellm = MagicMock()
        mock_litellm.acompletion = AsyncMock(side_effect=Exception("503 service unavailable"))
        mock_litellm.suppress_debug_info = False
        mock_litellm.set_verbose = False
        client._litellm = mock_litellm

        with pytest.raises(ServiceUnavailableError):
            await client.complete([Message.user("test")])

    @pytest.mark.asyncio
    async def test_complete_raises_generic_llm_error(self):
        """Should raise LLMError for unknown errors."""
        from llm.exceptions import LLMError

        client = LiteLLMClient()
        mock_litellm = MagicMock()
        mock_litellm.acompletion = AsyncMock(side_effect=Exception("something unknown went wrong"))
        mock_litellm.suppress_debug_info = False
        mock_litellm.set_verbose = False
        client._litellm = mock_litellm

        with pytest.raises(LLMError):
            await client.complete([Message.user("test")])

    @pytest.mark.asyncio
    async def test_complete_with_tools(self):
        """Should pass tools through to litellm.acompletion."""
        client = LiteLLMClient()

        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 5
        mock_usage.completion_tokens = 10

        mock_choice = MagicMock()
        mock_choice.message.content = "Using tool"
        mock_choice.finish_reason = "tool_calls"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        mock_litellm = MagicMock()
        mock_litellm.acompletion = AsyncMock(return_value=mock_response)
        mock_litellm.completion_cost = MagicMock(return_value=0.0005)
        client._litellm = mock_litellm

        tools = [{"type": "function", "function": {"name": "get_weather"}}]
        await client.complete([Message.user("weather?")], tools=tools)

        call_kwargs = mock_litellm.acompletion.call_args
        assert "tools" in call_kwargs.kwargs or "tools" in (
            call_kwargs[1] if len(call_kwargs) > 1 else {}
        )

    @pytest.mark.asyncio
    async def test_complete_cost_tracking_failure_graceful(self):
        """Should handle cost tracking failure gracefully."""
        client = LiteLLMClient()

        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20

        mock_choice = MagicMock()
        mock_choice.message.content = "response"
        mock_choice.finish_reason = "stop"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        mock_litellm = MagicMock()
        mock_litellm.acompletion = AsyncMock(return_value=mock_response)
        mock_litellm.completion_cost = MagicMock(side_effect=Exception("cost tracking failed"))
        client._litellm = mock_litellm

        response = await client.complete([Message.user("test")])
        assert response.content == "response"
        assert response.cost_usd is None

    def test_ensure_litellm_import_error(self):
        """Should raise LLMError when litellm is not installed."""
        from llm.exceptions import LLMError

        client = LiteLLMClient()
        client._litellm = None

        with patch.dict("sys.modules", {"litellm": None}):
            with patch("builtins.__import__", side_effect=ImportError("no litellm")):
                with pytest.raises(LLMError, match="litellm is not installed"):
                    client._ensure_litellm()


class TestRouterIntegration:
    def test_litellm_in_provider_configs(self):
        """LiteLLM should be registered in PROVIDER_CONFIGS if available."""
        from llm.router import PROVIDER_CONFIGS

        # If litellm provider module is importable, it should be in configs
        if ModelProvider.LITELLM in PROVIDER_CONFIGS:
            config = PROVIDER_CONFIGS[ModelProvider.LITELLM]
            assert config.priority == 99  # Lowest priority
            assert config.client_class == LiteLLMClient

    def test_litellm_priority_is_lowest(self):
        """LiteLLM should have the lowest priority (highest number)."""
        from llm.router import PROVIDER_CONFIGS

        if ModelProvider.LITELLM in PROVIDER_CONFIGS:
            litellm_priority = PROVIDER_CONFIGS[ModelProvider.LITELLM].priority
            for provider, config in PROVIDER_CONFIGS.items():
                if provider != ModelProvider.LITELLM:
                    assert config.priority < litellm_priority, (
                        f"{provider.value} priority ({config.priority}) should be "
                        f"lower than LiteLLM ({litellm_priority})"
                    )
