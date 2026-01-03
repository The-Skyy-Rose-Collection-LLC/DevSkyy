"""
LLM Domain Models
=================

Core domain models for LLM operations.

This module defines the domain models used throughout the LLM layer:
- Re-exports from llm.base for backward compatibility
- New request/response models for hexagonal architecture

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# Re-export existing models from llm.base
from llm.base import (
    CompletionResponse,
    Message,
    MessageRole,
    ModelProvider,
    StreamChunk,
    ToolCall,
)

__all__ = [
    # Re-exported base models
    "Message",
    "MessageRole",
    "ModelProvider",
    "CompletionResponse",
    "StreamChunk",
    "ToolCall",
    # New domain models
    "LLMRequest",
    "LLMResponse",
    "LLMCapabilities",
]


# =============================================================================
# Domain Models
# =============================================================================


class LLMCapabilities(BaseModel):
    """Provider capabilities."""

    model_config = ConfigDict(extra="forbid")

    supports_streaming: bool = True
    supports_tools: bool = True
    supports_vision: bool = False
    supports_json_mode: bool = False
    max_context_tokens: int = 4096
    max_output_tokens: int = 4096


class LLMRequest(BaseModel):
    """
    High-level LLM request.

    Used by services to make provider-agnostic requests.
    """

    model_config = ConfigDict(extra="forbid")

    # Core fields
    messages: list[Message]
    provider: ModelProvider | None = None
    model: str | None = None

    # Generation params
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, gt=0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)

    # Advanced features
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | dict[str, Any] | None = None
    response_format: dict[str, Any] | None = None  # For JSON mode
    stop_sequences: list[str] | None = None
    stream: bool = False

    # Metadata
    user_id: str | None = None
    request_id: str | None = None
    timeout_seconds: float = 60.0


class LLMResponse(BaseModel):
    """
    High-level LLM response.

    Wraps CompletionResponse with additional metadata for hexagonal architecture.
    """

    model_config = ConfigDict(extra="forbid")

    # Core completion
    completion: CompletionResponse

    # Request metadata
    request_id: str | None = None
    provider_used: ModelProvider
    model_used: str
    request_latency_ms: float = 0

    # Cost tracking
    estimated_cost_usd: float = 0.0

    # Timestamps
    requested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def content(self) -> str:
        """Get response content."""
        return self.completion.content

    @property
    def tool_calls(self) -> list[ToolCall]:
        """Get tool calls from response."""
        return self.completion.tool_calls

    @property
    def has_tool_calls(self) -> bool:
        """Check if response has tool calls."""
        return self.completion.has_tool_calls

    @property
    def total_tokens(self) -> int:
        """Get total tokens used."""
        return self.completion.total_tokens
