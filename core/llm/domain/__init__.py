"""LLM Domain Layer.

Core domain models and ports for the LLM layer.

This package defines the domain logic independent of infrastructure:
- models.py: Domain models (LLMRequest, LLMResponse, etc.)
- ports.py: Port interfaces (ILLMProvider, ILLMRouter, etc.)

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from .models import (
    CompletionResponse,
    LLMCapabilities,
    LLMRequest,
    LLMResponse,
    Message,
    MessageRole,
    ModelProvider,
    StreamChunk,
    ToolCall,
)
from .ports import ILLMProvider, ILLMRouter, IProviderFactory

__all__ = [
    # Models
    "Message",
    "MessageRole",
    "ModelProvider",
    "CompletionResponse",
    "StreamChunk",
    "ToolCall",
    "LLMRequest",
    "LLMResponse",
    "LLMCapabilities",
    # Ports
    "ILLMProvider",
    "ILLMRouter",
    "IProviderFactory",
]

__version__ = "1.0.0"
