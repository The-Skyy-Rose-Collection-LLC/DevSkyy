"""
Core LLM Module
===============

Hexagonal architecture for LLM operations.

Structure:
- domain/: Core models and port interfaces
- services/: Business logic (router, round_table, ab_testing)
- providers/: Concrete provider implementations
- infrastructure/: Provider factory and utilities

Usage:
    from core.llm.domain import LLMRequest, LLMResponse
    from core.llm.services import LLMRouter
    from core.llm.infrastructure import ProviderFactory

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from .domain import (
    CompletionResponse,
    ILLMProvider,
    ILLMRouter,
    IProviderFactory,
    LLMCapabilities,
    LLMRequest,
    LLMResponse,
    Message,
    MessageRole,
    ModelProvider,
    StreamChunk,
    ToolCall,
)
from .infrastructure import ProviderFactory
from .providers import (
    AnthropicClient,
    CohereClient,
    GoogleClient,
    GroqClient,
    MistralClient,
    OpenAIClient,
)
from .services import ab_testing, round_table, router

__all__ = [
    # Domain Models
    "Message",
    "MessageRole",
    "ModelProvider",
    "CompletionResponse",
    "StreamChunk",
    "ToolCall",
    "LLMRequest",
    "LLMResponse",
    "LLMCapabilities",
    # Domain Ports
    "ILLMProvider",
    "ILLMRouter",
    "IProviderFactory",
    # Infrastructure
    "ProviderFactory",
    # Providers
    "AnthropicClient",
    "OpenAIClient",
    "GoogleClient",
    "MistralClient",
    "CohereClient",
    "GroqClient",
    # Services
    "router",
    "round_table",
    "ab_testing",
]

__version__ = "1.0.0"
