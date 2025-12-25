"""
DevSkyy LLM Module
==================

Unified LLM client library supporting multiple providers.

Providers:
- OpenAI (GPT-4o, o1)
- Anthropic (Claude 3.5)
- Google (Gemini)
- Mistral
- Cohere (Command R)
- Groq (Llama, Mixtral)

Features:
- Unified Message/Response format
- Async support with streaming
- Tool/function calling
- 2-LLM agreement architecture
- Automatic fallback routing
- Cost tracking

Usage:
    from llm import Message, LLMRouter, ModelProvider

    # Quick completion
    router = LLMRouter()
    response = await router.complete(
        messages=[Message.user("Hello!")],
        provider=ModelProvider.ANTHROPIC,
    )
    print(response.content)

    # With fallback
    response = await router.complete_with_fallback(
        messages=[Message.user("Hello!")],
    )

    # 2-LLM Agreement
    response, agreement = await router.complete_with_agreement(
        messages=[Message.user("Analyze this data...")],
        primary=ModelProvider.ANTHROPIC,
        secondary=ModelProvider.OPENAI,
    )
"""

from .base import (
    BaseLLMClient,  # Enums; Models; Base Client
    CompletionResponse,
    Message,
    MessageRole,
    ModelProvider,
    StreamChunk,
    ToolCall,
)
from .exceptions import (
    AuthenticationError,
    ContentFilterError,
    ContextLengthError,
    InvalidRequestError,
    LLMError,
    ModelNotFoundError,
    QuotaExceededError,
    RateLimitError,
    ServiceUnavailableError,
    StreamError,
    TimeoutError,
    ToolCallError,
)
from .providers import (
    AnthropicClient,
    CohereClient,
    GoogleClient,
    GroqClient,
    MistralClient,
    OpenAIClient,
)
from .round_table import (
    ABTestResult,
    CompetitionStatus,
    LLMResponse,
    LLMRoundTable,
    ResponseScorer,
    ResponseScores,
    RoundTableDatabase,
    RoundTableEntry,
    RoundTableResult,
    create_round_table,
)
from .round_table import LLMProvider as RoundTableProvider
from .router import (
    PROVIDER_CONFIGS,
    LLMRouter,
    ProviderConfig,
    RoutingStrategy,
    complete,
    get_router,
)

__version__ = "1.0.0"

__all__ = [
    # Version
    "__version__",
    # Enums
    "MessageRole",
    "ModelProvider",
    # Models
    "Message",
    "ToolCall",
    "CompletionResponse",
    "StreamChunk",
    # Base
    "BaseLLMClient",
    # Exceptions
    "LLMError",
    "AuthenticationError",
    "RateLimitError",
    "QuotaExceededError",
    "InvalidRequestError",
    "ModelNotFoundError",
    "ContentFilterError",
    "ContextLengthError",
    "TimeoutError",
    "ServiceUnavailableError",
    "StreamError",
    "ToolCallError",
    # Providers
    "OpenAIClient",
    "AnthropicClient",
    "GoogleClient",
    "MistralClient",
    "CohereClient",
    "GroqClient",
    # Router
    "ProviderConfig",
    "PROVIDER_CONFIGS",
    "RoutingStrategy",
    "LLMRouter",
    "get_router",
    "complete",
    # Round Table
    "RoundTableProvider",
    "CompetitionStatus",
    "LLMResponse",
    "ResponseScores",
    "RoundTableEntry",
    "ABTestResult",
    "RoundTableResult",
    "RoundTableDatabase",
    "ResponseScorer",
    "LLMRoundTable",
    "create_round_table",
]
