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
        self.consecutive_failures = 0
        self.last_success = time.time()
        self.total_requests += 1
        self.status = ProviderStatus.HEALTHY

    def record_failure(self) -> None:
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
    ) -> LLMResponse: ...


class ModelRouter:
    """Routes LLM requests to providers with health-aware fallback."""

    def __init__(
        self,
        routing: dict[str, dict[str, str]] | None = None,
        fallbacks: dict[str, dict[str, str]] | None = None,
    ) -> None:
        self._routing = routing or {}
        self._fallbacks = fallbacks or {}
        self._adapters: dict[str, ProviderAdapter] = {}
        self._health: dict[str, ProviderHealth] = {}

    def register_adapter(self, provider: str, adapter: ProviderAdapter) -> None:
        """Register a provider adapter."""
        self._adapters[provider] = adapter
        self._health[provider] = ProviderHealth(provider=provider)

    def get_adapter(self, provider: str) -> ProviderAdapter | None:
        """Get adapter for a provider, or None if not registered."""
        return self._adapters.get(provider)

    def get_route(self, role: str) -> dict[str, str]:
        """Get routing config for an agent role."""
        return self._routing.get(role, {})

    def get_fallback(self, provider: str) -> dict[str, str]:
        """Get fallback config for a provider."""
        return self._fallbacks.get(provider, {})

    def get_health(self, provider: str) -> ProviderHealth:
        """Get health status for a provider."""
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
        """Route a request to the best available provider for the given role."""
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
