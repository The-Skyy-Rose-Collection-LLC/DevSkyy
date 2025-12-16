"""
LLM Base Classes
================

Base classes and models for LLM provider clients.

Features:
- Unified Message format
- CompletionResponse with token tracking
- StreamChunk for streaming
- Abstract BaseLLMClient

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field

from .exceptions import (
    AuthenticationError,
    LLMError,
    RateLimitError,
    ServiceUnavailableError,
    TimeoutError,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================


class MessageRole(str, Enum):
    """Message roles in conversations."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ModelProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    MISTRAL = "mistral"
    COHERE = "cohere"
    GROQ = "groq"


# =============================================================================
# Message Models
# =============================================================================


class Message(BaseModel):
    """
    Unified chat message format.

    Compatible with all providers.
    """

    model_config = ConfigDict(extra="forbid")

    role: MessageRole
    content: str
    name: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None

    @classmethod
    def system(cls, content: str) -> Message:
        """Create a system message."""
        return cls(role=MessageRole.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str, name: str | None = None) -> Message:
        """Create a user message."""
        return cls(role=MessageRole.USER, content=content, name=name)

    @classmethod
    def assistant(
        cls,
        content: str,
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> Message:
        """Create an assistant message."""
        return cls(role=MessageRole.ASSISTANT, content=content, tool_calls=tool_calls)

    @classmethod
    def tool(cls, content: str, tool_call_id: str) -> Message:
        """Create a tool result message."""
        return cls(role=MessageRole.TOOL, content=content, tool_call_id=tool_call_id)


class ToolCall(BaseModel):
    """Tool/function call request from LLM."""

    model_config = ConfigDict(extra="forbid")

    id: str
    type: str = "function"
    function: dict[str, Any]

    @property
    def name(self) -> str:
        """Get function name."""
        return self.function.get("name", "")

    @property
    def arguments(self) -> Any:
        """Get function arguments."""
        return self.function.get("arguments", {})


# =============================================================================
# Response Models
# =============================================================================


class CompletionResponse(BaseModel):
    """
    Unified completion response from any provider.

    Includes content, usage stats, and metadata.
    """

    model_config = ConfigDict(extra="forbid")

    # Content
    content: str
    model: str
    provider: str

    # Usage
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    # Metadata
    finish_reason: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    latency_ms: float = 0

    # Raw response (for debugging)
    raw: dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def has_tool_calls(self) -> bool:
        """Check if response includes tool calls."""
        return len(self.tool_calls) > 0

    def get_cost_estimate(self, input_price_per_1k: float, output_price_per_1k: float) -> float:
        """
        Estimate cost based on token pricing.

        Args:
            input_price_per_1k: Price per 1000 input tokens
            output_price_per_1k: Price per 1000 output tokens

        Returns:
            Estimated cost in dollars
        """
        input_cost = (self.input_tokens / 1000) * input_price_per_1k
        output_cost = (self.output_tokens / 1000) * output_price_per_1k
        return input_cost + output_cost


class StreamChunk(BaseModel):
    """Streaming response chunk."""

    model_config = ConfigDict(extra="forbid")

    content: str = ""
    finish_reason: str | None = None
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)

    # Delta tracking
    delta_content: str = ""
    index: int = 0


# =============================================================================
# Base Client
# =============================================================================


class BaseLLMClient(ABC):
    """
    Abstract base class for LLM provider clients.

    Provides:
    - Async HTTP client management
    - Retry logic with exponential backoff
    - Error handling and classification
    - Common interface for all providers

    Subclasses must implement:
    - _get_headers(): Return auth headers
    - complete(): Generate completion
    - stream(): Stream completion
    """

    provider: str = "base"
    default_model: str = ""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 3,
    ) -> None:
        self.api_key = api_key or ""
        self.base_url = base_url or ""
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> BaseLLMClient:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def connect(self) -> None:
        """Initialize HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers=self._get_headers(),
            )

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @abstractmethod
    def _get_headers(self) -> dict[str, str]:
        """Get authentication headers."""
        pass

    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> CompletionResponse:
        """
        Generate a completion.

        Args:
            messages: Conversation messages
            model: Model to use (provider-specific)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            tools: Tool/function definitions
            **kwargs: Provider-specific options

        Returns:
            CompletionResponse with generated content
        """
        pass

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream a completion.

        Args:
            messages: Conversation messages
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Provider-specific options

        Yields:
            StreamChunk objects with incremental content
        """
        pass
        yield  # Make this a generator

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _messages_to_list(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert Message objects to dict list for API."""
        return [{"role": m.role.value, "content": m.content} for m in messages]

    async def _make_request(
        self,
        method: str,
        url: str,
        json: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic.

        Handles common errors and retries appropriately.
        """
        await self.connect()

        last_error: Exception | None = None
        retry_delays = [1, 2, 4]  # Exponential backoff

        for attempt in range(self.max_retries):
            try:
                response = await self._client.request(  # type: ignore
                    method=method,
                    url=url,
                    json=json,
                    **kwargs,
                )

                # Check for errors
                if response.status_code == 401:
                    raise AuthenticationError(
                        "Invalid API key",
                        provider=self.provider,
                    )
                elif response.status_code == 429:
                    retry_after = response.headers.get("retry-after")
                    raise RateLimitError(
                        "Rate limit exceeded",
                        provider=self.provider,
                        retry_after=float(retry_after) if retry_after else None,
                    )
                elif response.status_code >= 500:
                    raise ServiceUnavailableError(
                        f"Service error: {response.status_code}",
                        provider=self.provider,
                    )
                elif response.status_code >= 400:
                    raise LLMError(
                        f"Request failed: {response.text}",
                        provider=self.provider,
                        details={"status_code": response.status_code},
                    )

                return response

            except httpx.TimeoutException:
                last_error = TimeoutError(
                    f"Request timed out after {self.timeout}s",
                    provider=self.provider,
                )
            except (RateLimitError, ServiceUnavailableError) as e:
                last_error = e
                # Retry these errors
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(retry_delays[min(attempt, len(retry_delays) - 1)])
            except (AuthenticationError, LLMError):
                raise  # Don't retry auth or validation errors

        raise last_error or LLMError("Request failed after retries", provider=self.provider)

    def _calculate_latency(self, start_time: datetime) -> float:
        """Calculate latency in milliseconds."""
        return (datetime.now(UTC) - start_time).total_seconds() * 1000


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "MessageRole",
    "ModelProvider",
    # Models
    "Message",
    "ToolCall",
    "CompletionResponse",
    "StreamChunk",
    # Base Client
    "BaseLLMClient",
]
