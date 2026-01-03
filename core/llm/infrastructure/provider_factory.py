"""
LLM Provider Factory
====================

Factory for creating and managing LLM provider instances.

This is the infrastructure layer component responsible for:
- Instantiating providers with proper configuration
- Managing provider capabilities
- Providing provider discovery

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
import os
from typing import Any

from core.llm.domain import (
    ILLMProvider,
    IProviderFactory,
    LLMCapabilities,
    ModelProvider,
)

# Import concrete provider implementations
from llm.providers.anthropic import AnthropicClient
from llm.providers.cohere import CohereClient
from llm.providers.google import GoogleClient
from llm.providers.groq import GroqClient
from llm.providers.mistral import MistralClient
from llm.providers.openai import OpenAIClient

logger = logging.getLogger(__name__)

__all__ = ["ProviderFactory"]


# =============================================================================
# Provider Capabilities Definitions
# =============================================================================

PROVIDER_CAPABILITIES: dict[ModelProvider, LLMCapabilities] = {
    ModelProvider.OPENAI: LLMCapabilities(
        supports_streaming=True,
        supports_tools=True,
        supports_vision=True,
        supports_json_mode=True,
        max_context_tokens=128_000,  # GPT-4
        max_output_tokens=4096,
    ),
    ModelProvider.ANTHROPIC: LLMCapabilities(
        supports_streaming=True,
        supports_tools=True,
        supports_vision=True,
        supports_json_mode=False,
        max_context_tokens=200_000,  # Claude 3.5 Sonnet
        max_output_tokens=4096,
    ),
    ModelProvider.GOOGLE: LLMCapabilities(
        supports_streaming=True,
        supports_tools=True,
        supports_vision=True,
        supports_json_mode=True,
        max_context_tokens=1_000_000,  # Gemini 1.5 Pro
        max_output_tokens=8192,
    ),
    ModelProvider.MISTRAL: LLMCapabilities(
        supports_streaming=True,
        supports_tools=True,
        supports_vision=False,
        supports_json_mode=True,
        max_context_tokens=32_000,
        max_output_tokens=4096,
    ),
    ModelProvider.COHERE: LLMCapabilities(
        supports_streaming=True,
        supports_tools=True,
        supports_vision=False,
        supports_json_mode=False,
        max_context_tokens=128_000,
        max_output_tokens=4096,
    ),
    ModelProvider.GROQ: LLMCapabilities(
        supports_streaming=True,
        supports_tools=True,
        supports_vision=False,
        supports_json_mode=True,
        max_context_tokens=32_000,
        max_output_tokens=4096,
    ),
}


# =============================================================================
# Provider Factory
# =============================================================================


class ProviderFactory(IProviderFactory):
    """
    Factory for creating LLM provider instances.

    Handles:
    - Provider instantiation with environment-based configuration
    - Capability discovery
    - Provider availability checks
    """

    def __init__(self) -> None:
        """Initialize provider factory."""
        self._provider_classes: dict[ModelProvider, type[ILLMProvider]] = {
            ModelProvider.OPENAI: OpenAIClient,
            ModelProvider.ANTHROPIC: AnthropicClient,
            ModelProvider.GOOGLE: GoogleClient,
            ModelProvider.MISTRAL: MistralClient,
            ModelProvider.COHERE: CohereClient,
            ModelProvider.GROQ: GroqClient,
        }
        self._provider_cache: dict[ModelProvider, ILLMProvider] = {}

    def create_provider(
        self,
        provider: ModelProvider,
        api_key: str | None = None,
        **kwargs: Any,
    ) -> ILLMProvider:
        """
        Create a provider instance.

        Args:
            provider: Provider type to create
            api_key: Optional API key (uses env var if not provided)
            **kwargs: Additional provider-specific configuration

        Returns:
            Provider instance implementing ILLMProvider

        Raises:
            ValueError: If provider is not supported
        """
        if provider not in self._provider_classes:
            available = ", ".join(p.value for p in self._provider_classes)
            raise ValueError(
                f"Unsupported provider: {provider}. " f"Available providers: {available}"
            )

        provider_class = self._provider_classes[provider]

        # Get API key from kwargs or environment
        if api_key is None:
            api_key = self._get_api_key_from_env(provider)

        # Create provider instance
        instance = provider_class(api_key=api_key, **kwargs)

        logger.info(
            f"Created {provider.value} provider",
            extra={"provider": provider.value, "model": instance.default_model},
        )

        return instance

    def get_or_create_provider(
        self,
        provider: ModelProvider,
        api_key: str | None = None,
        **kwargs: Any,
    ) -> ILLMProvider:
        """
        Get cached provider or create new one.

        Args:
            provider: Provider type
            api_key: Optional API key
            **kwargs: Additional configuration

        Returns:
            Provider instance (cached or new)
        """
        # Check cache
        if provider in self._provider_cache:
            return self._provider_cache[provider]

        # Create and cache
        instance = self.create_provider(provider, api_key=api_key, **kwargs)
        self._provider_cache[provider] = instance
        return instance

    def get_capabilities(self, provider: ModelProvider) -> LLMCapabilities:
        """
        Get provider capabilities.

        Args:
            provider: Provider to query

        Returns:
            Capabilities of the provider

        Raises:
            ValueError: If provider is not supported
        """
        if provider not in PROVIDER_CAPABILITIES:
            raise ValueError(f"Unknown provider: {provider}")

        return PROVIDER_CAPABILITIES[provider]

    def list_providers(self) -> list[ModelProvider]:
        """
        List all available providers.

        Returns:
            List of available provider types
        """
        return list(self._provider_classes.keys())

    def list_available_providers(self) -> list[ModelProvider]:
        """
        List providers with API keys configured.

        Returns:
            List of providers that have API keys available
        """
        available = []
        for provider in self.list_providers():
            try:
                api_key = self._get_api_key_from_env(provider)
                if api_key:
                    available.append(provider)
            except Exception:
                continue

        return available

    def _get_api_key_from_env(self, provider: ModelProvider) -> str | None:
        """
        Get API key from environment variables.

        Args:
            provider: Provider type

        Returns:
            API key from environment or None
        """
        env_var_map = {
            ModelProvider.OPENAI: "OPENAI_API_KEY",
            ModelProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            ModelProvider.GOOGLE: "GOOGLE_AI_API_KEY",
            ModelProvider.MISTRAL: "MISTRAL_API_KEY",
            ModelProvider.COHERE: "COHERE_API_KEY",
            ModelProvider.GROQ: "GROQ_API_KEY",
        }

        env_var = env_var_map.get(provider)
        if not env_var:
            return None

        return os.getenv(env_var)

    def clear_cache(self) -> None:
        """Clear provider cache."""
        self._provider_cache.clear()
        logger.debug("Cleared provider cache")
