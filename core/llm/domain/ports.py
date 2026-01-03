"""
LLM Domain Ports
================

Port interfaces for hexagonal architecture.

Defines the contracts that LLM providers must implement.
This allows the core domain to depend on abstractions, not concrete implementations.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any, Protocol

from .models import (
    CompletionResponse,
    LLMCapabilities,
    LLMRequest,
    LLMResponse,
    Message,
    ModelProvider,
    StreamChunk,
)

__all__ = [
    "ILLMProvider",
    "ILLMRouter",
    "IProviderFactory",
]


# =============================================================================
# Provider Port
# =============================================================================


class ILLMProvider(Protocol):
    """
    LLM Provider interface (Port).

    All LLM providers must implement this interface.
    This is a Protocol (structural subtyping) not an ABC,
    so existing BaseLLMClient implementations automatically conform.
    """

    provider: str
    default_model: str

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
        """Generate a completion."""
        ...

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a completion."""
        ...

    @abstractmethod
    async def connect(self) -> None:
        """Initialize the provider."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close the provider."""
        ...


# =============================================================================
# Router Port
# =============================================================================


class ILLMRouter(ABC):
    """
    LLM Router interface (Port).

    Routes requests to appropriate providers based on task type,
    requirements, or other criteria.
    """

    @abstractmethod
    async def route_request(self, request: LLMRequest) -> LLMResponse:
        """
        Route request to appropriate provider.

        Args:
            request: LLM request to route

        Returns:
            LLM response from selected provider
        """
        pass

    @abstractmethod
    def select_provider(self, request: LLMRequest) -> tuple[ModelProvider, str]:
        """
        Select best provider and model for request.

        Args:
            request: LLM request

        Returns:
            Tuple of (provider, model_name)
        """
        pass


# =============================================================================
# Factory Port
# =============================================================================


class IProviderFactory(ABC):
    """
    Provider factory interface (Port).

    Creates and manages provider instances.
    """

    @abstractmethod
    def create_provider(self, provider: ModelProvider) -> ILLMProvider:
        """
        Create a provider instance.

        Args:
            provider: Provider type to create

        Returns:
            Provider instance implementing ILLMProvider
        """
        pass

    @abstractmethod
    def get_capabilities(self, provider: ModelProvider) -> LLMCapabilities:
        """
        Get provider capabilities.

        Args:
            provider: Provider to query

        Returns:
            Capabilities of the provider
        """
        pass

    @abstractmethod
    def list_providers(self) -> list[ModelProvider]:
        """
        List all available providers.

        Returns:
            List of available provider types
        """
        pass
