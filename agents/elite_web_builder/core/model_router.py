"""
Model Router — Multi-provider LLM routing with health-aware fallback.

Routes requests to the best available provider based on agent role,
provider health, and configured fallback chains.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class ProviderStatus(str, Enum):
    """Health status of an LLM provider."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


@dataclass(frozen=True)
class LLMResponse:
    """Immutable response from an LLM provider."""

    content: str
    provider: str
    model: str
    latency_ms: float
    tokens_used: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderHealth:
    """Tracks health of a single provider."""

    provider: str
    status: ProviderStatus = ProviderStatus.HEALTHY
    consecutive_failures: int = 0
    last_success: float = 0.0
    last_failure: float = 0.0
    total_requests: int = 0
    total_failures: int = 0

    def record_success(self) -> None:
        """
        Mark the provider health as a successful request and reset failure tracking.
        
        Updates the provider's last success timestamp, clears consecutive failure count, increments the total request counter, and sets the provider status to HEALTHY.
        """
        self.consecutive_failures = 0
        self.last_success = time.time()
        self.total_requests += 1
        self.status = ProviderStatus.HEALTHY

    def record_failure(self) -> None:
        """
        Record a failure occurrence for this provider and update its health metrics.
        
        Increments consecutive failure and total request/failure counters, updates the last failure timestamp, and sets the provider status to `DEGRADED` when there is at least one consecutive failure or to `DOWN` when there are three or more consecutive failures.
        """
        self.consecutive_failures += 1
        self.last_failure = time.time()
        self.total_requests += 1
        self.total_failures += 1
        if self.consecutive_failures >= 3:
            self.status = ProviderStatus.DOWN
        elif self.consecutive_failures >= 1:
            self.status = ProviderStatus.DEGRADED


class ProviderAdapter(Protocol):
    """Protocol for LLM provider adapters."""

    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str = "",
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse: """
        Generate a response from the adapter's provider for the given prompt.
        
        Parameters:
            prompt (str): User-facing input text to generate a response for.
            system_prompt (str): Optional system-level prompt or instructions to influence the response.
            model (str): Provider-specific model identifier to use for generation.
            temperature (float): Sampling temperature controlling randomness (higher is more random).
            max_tokens (int): Maximum number of tokens the provider should generate.
        
        Returns:
            LLMResponse: The provider's response including content, provider identifier, model used, latency_ms, tokens_used, and optional metadata.
        """
        ...


class ModelRouter:
    """Routes LLM requests to providers with health-aware fallback."""

    def __init__(
        self,
        routing: dict[str, dict[str, str]] | None = None,
        fallbacks: dict[str, dict[str, str]] | None = None,
    ) -> None:
        """
        Initialize the router with optional routing and fallback configurations and create internal registries.
        
        Parameters:
            routing (dict[str, dict[str, str]] | None): Mapping from agent role to routing info (e.g., {'provider': 'openai', 'model': 'gpt-4'}). If None, an empty routing map is used.
            fallbacks (dict[str, dict[str, str]] | None): Mapping from a primary provider to its fallback info (e.g., {'provider': 'anthropic', 'model': 'claude'}). If None, an empty fallback map is used.
        
        Side effects:
            Creates empty internal registries:
              - _adapters: maps provider names to their registered ProviderAdapter
              - _health: maps provider names to their ProviderHealth trackers
        """
        self._routing = routing or {}
        self._fallbacks = fallbacks or {}
        self._adapters: dict[str, ProviderAdapter] = {}
        self._health: dict[str, ProviderHealth] = {}

    def register_adapter(self, provider: str, adapter: ProviderAdapter) -> None:
        """
        Register an adapter for a provider and initialize its health tracking.
        
        Parameters:
            provider (str): Provider identifier to register.
            adapter (ProviderAdapter): Adapter instance that implements the provider's generate interface.
        """
        self._adapters[provider] = adapter
        self._health[provider] = ProviderHealth(provider=provider)

    def get_adapter(self, provider: str) -> ProviderAdapter | None:
        """
        Retrieve the registered adapter for the given provider.
        
        Parameters:
            provider (str): Provider identifier to look up.
        
        Returns:
            adapter (ProviderAdapter | None): The registered adapter for the provider, or `None` if no adapter is registered.
        """
        return self._adapters.get(provider)

    def get_route(self, role: str) -> dict[str, str]:
        """
        Retrieve the routing configuration for the given agent role.
        
        Parameters:
            role (str): Agent role identifier to look up in the router configuration.
        
        Returns:
            dict[str, str]: Mapping with routing keys (e.g., "provider", "model") for the role, or an empty dict if no route is configured.
        """
        return self._routing.get(role, {})

    def get_fallback(self, provider: str) -> dict[str, str]:
        """
        Retrieve the configured fallback mapping for a provider.
        
        Parameters:
            provider (str): Provider identifier to look up.
        
        Returns:
            dict: Fallback mapping containing keys 'provider' and 'model' when configured, or an empty dict if no fallback is defined.
        """
        return self._fallbacks.get(provider, {})

    def get_health(self, provider: str) -> ProviderHealth:
        """
        Retrieve the health tracker for the named provider, creating and storing one if it does not exist.
        
        If the provider has no existing health entry, a new ProviderHealth is initialized, stored in the router's registry, and returned.
        
        Parameters:
            provider (str): Provider identifier.
        
        Returns:
            ProviderHealth: The health record for the specified provider.
        """
        if provider not in self._health:
            self._health[provider] = ProviderHealth(provider=provider)
        return self._health[provider]

    async def route(
        self,
        role: str,
        prompt: str,
        *,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """
        Route a request for the given agent role to the best available LLM provider, using the configured primary provider and an optional fallback.
        
        Parameters:
            role (str): Agent role used to look up routing configuration.
            prompt (str): Prompt to send to the provider.
            system_prompt (str): System prompt to include with the request.
            temperature (float): Sampling temperature for the model.
            max_tokens (int): Maximum number of tokens to generate.
        
        Returns:
            LLMResponse: Response returned by the selected provider, including content, provider id, model, latency, and metadata.
        
        Raises:
            ValueError: If no routing is configured for the given role.
            RuntimeError: If both the primary provider and its configured fallback fail or are unavailable.
        """
        route = self.get_route(role)
        if not route:
            raise ValueError(f"No routing configured for role: {role}")

        provider = route.get("provider", "")
        model = route.get("model", "")

        # Try primary provider
        adapter = self.get_adapter(provider)
        health = self.get_health(provider)

        if adapter and health.status != ProviderStatus.DOWN:
            try:
                start = time.time()
                response = await adapter.generate(
                    prompt,
                    system_prompt=system_prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                health.record_success()
                latency = (time.time() - start) * 1000
                logger.info(
                    "Routed to %s/%s for %s (%.0fms)",
                    provider,
                    model,
                    role,
                    latency,
                )
                return response
            except Exception as exc:
                health.record_failure()
                logger.warning(
                    "Primary provider %s failed for %s: %s",
                    provider,
                    role,
                    exc,
                )

        # Try fallback
        fallback = self.get_fallback(provider)
        if fallback:
            fb_provider = fallback.get("provider", "")
            fb_model = fallback.get("model", "")
            fb_adapter = self.get_adapter(fb_provider)
            if fb_adapter:
                try:
                    response = await fb_adapter.generate(
                        prompt,
                        system_prompt=system_prompt,
                        model=fb_model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    self.get_health(fb_provider).record_success()
                    logger.info(
                        "Fallback to %s/%s for %s",
                        fb_provider,
                        fb_model,
                        role,
                    )
                    return response
                except Exception as exc:
                    self.get_health(fb_provider).record_failure()
                    logger.error(
                        "Fallback provider %s also failed for %s: %s",
                        fb_provider,
                        role,
                        exc,
                    )

        raise RuntimeError(
            f"All providers failed for role '{role}'. "
            f"Primary: {provider}, Fallback: {fallback.get('provider', 'none')}"
        )