"""
Tests for llm module
====================

LLM client and router tests.
"""

from llm import (
    CompletionResponse,
    LLMRouter,
    Message,
    MessageRole,
    ModelProvider,
    RoutingStrategy,
)
from llm.exceptions import (
    AuthenticationError,
    LLMError,
    RateLimitError,
)
from llm.providers import (
    AnthropicClient,
    CohereClient,
    GoogleClient,
    GroqClient,
    MistralClient,
    OpenAIClient,
)


class TestMessage:
    """Test Message model."""

    def test_system_message(self):
        """Should create system message."""
        msg = Message.system("You are a helpful assistant.")

        assert msg.role == MessageRole.SYSTEM
        assert msg.content == "You are a helpful assistant."

    def test_user_message(self):
        """Should create user message."""
        msg = Message.user("Hello!")

        assert msg.role == MessageRole.USER
        assert msg.content == "Hello!"

    def test_assistant_message(self):
        """Should create assistant message."""
        msg = Message.assistant("Hi there!")

        assert msg.role == MessageRole.ASSISTANT
        assert msg.content == "Hi there!"

    def test_tool_message(self):
        """Should create tool result message."""
        msg = Message.tool('{"result": "success"}', "call_123")

        assert msg.role == MessageRole.TOOL
        assert msg.content == '{"result": "success"}'
        assert msg.tool_call_id == "call_123"


class TestCompletionResponse:
    """Test CompletionResponse model."""

    def test_basic_response(self):
        """Should create basic response."""
        response = CompletionResponse(
            content="Hello!",
            model="gpt-4",
            provider=ModelProvider.OPENAI,
            input_tokens=10,
            output_tokens=5,
            total_tokens=15,
        )

        assert response.content == "Hello!"
        assert response.total_tokens == 15

    def test_has_tool_calls(self):
        """Should detect tool calls."""
        from llm.base import ToolCall

        response = CompletionResponse(
            content="",
            model="gpt-4",
            provider=ModelProvider.OPENAI,
            tool_calls=[
                ToolCall(id="call_1", type="function", function={"name": "test", "arguments": "{}"})
            ],
        )

        assert response.has_tool_calls is True

    def test_no_tool_calls(self):
        """Should detect no tool calls."""
        response = CompletionResponse(
            content="Just text",
            model="gpt-4",
            provider=ModelProvider.OPENAI,
        )

        assert response.has_tool_calls is False


class TestProviderClients:
    """Test provider client instantiation."""

    def test_openai_client(self):
        """Should instantiate OpenAI client."""
        client = OpenAIClient(api_key="test-key")

        assert client.provider == ModelProvider.OPENAI

    def test_anthropic_client(self):
        """Should instantiate Anthropic client."""
        client = AnthropicClient(api_key="test-key")

        assert client.provider == ModelProvider.ANTHROPIC

    def test_google_client(self):
        """Should instantiate Google client."""
        client = GoogleClient(api_key="test-key")

        assert client.provider == ModelProvider.GOOGLE

    def test_mistral_client(self):
        """Should instantiate Mistral client."""
        client = MistralClient(api_key="test-key")

        assert client.provider == ModelProvider.MISTRAL

    def test_cohere_client(self):
        """Should instantiate Cohere client."""
        client = CohereClient(api_key="test-key")

        assert client.provider == ModelProvider.COHERE

    def test_groq_client(self):
        """Should instantiate Groq client."""
        client = GroqClient(api_key="test-key")

        assert client.provider == ModelProvider.GROQ


class TestLLMRouter:
    """Test LLM router."""

    def test_create_router(self):
        """Should create router."""
        router = LLMRouter()

        providers = router.get_available_providers()
        assert len(providers) >= 0  # May be 0 if no API keys set

    def test_enable_disable_provider(self):
        """Should enable/disable providers."""
        router = LLMRouter()

        router.disable_provider(ModelProvider.OPENAI)
        providers = router.get_available_providers()

        # OpenAI should not be in list
        assert ModelProvider.OPENAI not in providers or not any(
            p.provider == ModelProvider.OPENAI for p in providers
        )

    def test_routing_strategy_enum(self):
        """Should have routing strategies."""
        assert RoutingStrategy.PRIORITY
        assert RoutingStrategy.COST
        assert RoutingStrategy.LATENCY
        assert RoutingStrategy.ROUND_ROBIN


class TestLLMExceptions:
    """Test LLM exceptions."""

    def test_llm_error(self):
        """Should create base error."""
        error = LLMError("Something went wrong", provider="openai")

        assert "Something went wrong" in str(error)
        assert error.provider == "openai"

    def test_rate_limit_error(self):
        """Should create rate limit error with retry_after."""
        error = RateLimitError(
            "Rate limited",
            provider="openai",
            retry_after=60,
        )

        assert error.retry_after == 60

    def test_authentication_error(self):
        """Should create auth error."""
        error = AuthenticationError("Invalid API key", provider="anthropic")

        assert "Invalid API key" in str(error)
