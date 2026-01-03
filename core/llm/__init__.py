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
]

__version__ = "1.0.0"
