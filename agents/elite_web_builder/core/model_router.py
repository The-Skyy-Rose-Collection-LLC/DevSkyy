"""
Multi-provider model routing with fallback chains and health tracking.

Routes agent requests to the optimal provider (Anthropic, Google, OpenAI, xAI)
with automatic fallback when a provider is unhealthy. All operations use
ralph-wiggums resilience — no blocking, errors loop until pass.

Usage:
    router = ModelRouter(config=RoutingConfig.from_dict(json_data))
    result = router.resolve("director")  # → RouteResult(provider, model, is_fallback)
    response = await router.call_with_fallback("director", my_async_fn)
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Default fallback when all else fails
_ULTIMATE_FALLBACK = ("google", "gemini-2.0-flash")


# ---------------------------------------------------------------------------
# Data models (frozen / immutable)
# ---------------------------------------------------------------------------


class ProviderStatus(Enum):
    """Health status of a provider."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass(frozen=True)
class ProviderConfig:
    """Immutable provider + model pair."""

    provider: str
    model: str


@dataclass(frozen=True)
class RouteResult:
    """Result of resolving a route — includes fallback indicator."""

    provider: str
    model: str
    is_fallback: bool = False


@dataclass
class ProviderHealth:
    """Mutable health tracking for a single provider."""

    status: ProviderStatus = ProviderStatus.HEALTHY
    failure_count: int = 0
    success_count: int = 0
    consecutive_failures: int = 0
    latencies: deque = field(default_factory=lambda: deque(maxlen=50))
    last_failure_time: float = 0.0
    last_success_time: float = 0.0

    @property
    def avg_latency(self) -> float:
        if not self.latencies:
            return 0.0
        return sum(self.latencies) / len(self.latencies)


# ---------------------------------------------------------------------------
# Routing config
# ---------------------------------------------------------------------------

FAILURE_THRESHOLD = 5  # consecutive failures before marking unhealthy


@dataclass
class RoutingConfig:
    """Routing configuration: agent→provider mapping + fallback chain."""

    routes: dict[str, ProviderConfig] = field(default_factory=dict)
    fallbacks: dict[str, ProviderConfig] = field(default_factory=dict)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> RoutingConfig:
        """Build config from a dictionary (e.g., loaded from JSON)."""
        routes = {
            name: ProviderConfig(provider=cfg["provider"], model=cfg["model"])
            for name, cfg in data.get("routes", {}).items()
        }
        fallbacks = {
            provider: ProviderConfig(provider=cfg["provider"], model=cfg["model"])
            for provider, cfg in data.get("fallbacks", {}).items()
        }
        return RoutingConfig(routes=routes, fallbacks=fallbacks)

    @staticmethod
    def from_json_file(path: str) -> RoutingConfig:
        """Load config from a JSON file."""
        import json
        from pathlib import Path

        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return RoutingConfig.from_dict(data)


# ---------------------------------------------------------------------------
# Model Router
# ---------------------------------------------------------------------------


class ModelRouter:
    """
    Multi-provider routing engine with health tracking and fallback chains.

    Resolves agent names to (provider, model) pairs. Tracks provider health
    and automatically switches to fallback providers when the primary is down.
    All external calls use ralph-wiggums retry logic — no blocking.
    """

    def __init__(self, config: RoutingConfig) -> None:
        self._config = config
        self._health: dict[str, ProviderHealth] = {}

    # -- Health tracking --

    def _ensure_health(self, provider: str) -> ProviderHealth:
        """Get or create health record for a provider."""
        if provider not in self._health:
            self._health[provider] = ProviderHealth()
        return self._health[provider]

    def get_health(self, provider: str) -> ProviderHealth:
        """Return health state for a provider."""
        return self._ensure_health(provider)

    def mark_unhealthy(self, provider: str) -> None:
        """Mark a provider as unhealthy."""
        health = self._ensure_health(provider)
        health.status = ProviderStatus.UNHEALTHY
        logger.warning("Provider %s marked UNHEALTHY", provider)

    def mark_healthy(self, provider: str) -> None:
        """Mark a provider as healthy (recovered)."""
        health = self._ensure_health(provider)
        health.status = ProviderStatus.HEALTHY
        health.consecutive_failures = 0
        logger.info("Provider %s marked HEALTHY", provider)

    def record_latency(self, provider: str, latency_seconds: float) -> None:
        """Record a successful call latency."""
        health = self._ensure_health(provider)
        health.latencies.append(latency_seconds)

    def record_success(self, provider: str) -> None:
        """Record a successful call."""
        health = self._ensure_health(provider)
        health.success_count += 1
        health.consecutive_failures = 0
        health.last_success_time = time.time()
        # Auto-recover if was degraded
        if health.status == ProviderStatus.DEGRADED:
            health.status = ProviderStatus.HEALTHY

    def record_failure(self, provider: str) -> None:
        """Record a failed call. Auto-marks unhealthy after threshold."""
        health = self._ensure_health(provider)
        health.failure_count += 1
        health.consecutive_failures += 1
        health.last_failure_time = time.time()

        if health.consecutive_failures >= FAILURE_THRESHOLD:
            health.status = ProviderStatus.UNHEALTHY
            logger.error(
                "Provider %s auto-marked UNHEALTHY after %d consecutive failures",
                provider,
                health.consecutive_failures,
            )

    def _is_healthy(self, provider: str) -> bool:
        """Check if a provider is available for routing."""
        health = self._ensure_health(provider)
        return health.status != ProviderStatus.UNHEALTHY

    # -- Routing --

    def get_fallback(self, provider: str) -> ProviderConfig:
        """Get fallback config for a provider."""
        fb = self._config.fallbacks.get(provider)
        if fb is not None:
            return fb
        # Ultimate fallback
        return ProviderConfig(provider=_ULTIMATE_FALLBACK[0], model=_ULTIMATE_FALLBACK[1])

    def resolve(self, agent_name: str) -> RouteResult:
        """
        Resolve agent name → (provider, model) with health-aware fallback.

        If the primary provider is unhealthy, returns the fallback.
        If agent_name is unknown, returns a default route.
        """
        primary = self._config.routes.get(agent_name)

        if primary is None:
            # Unknown agent — use ultimate fallback
            logger.debug("Unknown agent '%s', using default route", agent_name)
            return RouteResult(
                provider=_ULTIMATE_FALLBACK[0],
                model=_ULTIMATE_FALLBACK[1],
                is_fallback=True,
            )

        # Check if primary provider is healthy
        if self._is_healthy(primary.provider):
            return RouteResult(
                provider=primary.provider,
                model=primary.model,
                is_fallback=False,
            )

        # Primary unhealthy — try fallback
        fallback = self.get_fallback(primary.provider)
        if self._is_healthy(fallback.provider):
            logger.info(
                "Agent '%s': primary %s unhealthy, falling back to %s",
                agent_name,
                primary.provider,
                fallback.provider,
            )
            return RouteResult(
                provider=fallback.provider,
                model=fallback.model,
                is_fallback=True,
            )

        # Both unhealthy — use ultimate fallback
        logger.warning(
            "Agent '%s': both %s and %s unhealthy, using ultimate fallback",
            agent_name,
            primary.provider,
            fallback.provider,
        )
        return RouteResult(
            provider=_ULTIMATE_FALLBACK[0],
            model=_ULTIMATE_FALLBACK[1],
            is_fallback=True,
        )

    # -- Async call with ralph-loop resilience --

    async def call_with_fallback(
        self,
        agent_name: str,
        operation: Callable[..., Any],
        max_attempts: int = 3,
        base_delay: float = 1.0,
    ) -> Any:
        """
        Call an async operation with automatic provider fallback.

        The operation receives (provider: str, model: str) and should use those
        to make the actual API call. On failure, the router tries fallback
        providers with exponential backoff. No blocking — ralph-loop resilience.

        Args:
            agent_name: Agent role name (e.g., "director")
            operation: Async callable(provider, model) → result
            max_attempts: Max retries per provider
            base_delay: Base delay for exponential backoff

        Returns:
            Result from the first successful call

        Raises:
            Exception: After all providers and retries exhausted
        """
        # Build provider chain: primary → fallback → ultimate
        route = self._config.routes.get(agent_name)
        providers_to_try: list[tuple[str, str]] = []

        if route:
            providers_to_try.append((route.provider, route.model))
            fb = self._config.fallbacks.get(route.provider)
            if fb:
                providers_to_try.append((fb.provider, fb.model))

        # Always add ultimate fallback
        if _ULTIMATE_FALLBACK not in providers_to_try:
            providers_to_try.append(_ULTIMATE_FALLBACK)

        last_error: Exception | None = None

        for provider, model in providers_to_try:
            for attempt in range(max_attempts):
                try:
                    start = time.time()
                    result = await operation(provider, model)
                    elapsed = time.time() - start

                    self.record_success(provider)
                    self.record_latency(provider, elapsed)
                    return result

                except Exception as exc:
                    last_error = exc
                    self.record_failure(provider)
                    logger.warning(
                        "call_with_fallback: %s/%s attempt %d/%d failed: %s",
                        provider,
                        model,
                        attempt + 1,
                        max_attempts,
                        exc,
                    )

                    if attempt < max_attempts - 1:
                        delay = base_delay * (2**attempt)
                        await asyncio.sleep(delay)

            logger.error(
                "call_with_fallback: %s exhausted %d attempts, trying next",
                provider,
                max_attempts,
            )

        # All exhausted
        raise RuntimeError(
            f"All providers exhausted for agent '{agent_name}'. "
            f"Last error: {last_error}"
        ) from last_error

    # -- Bulk operations --

    def list_routes(self) -> dict[str, RouteResult]:
        """Return all agent routes with current resolution (health-aware)."""
        return {name: self.resolve(name) for name in self._config.routes}

    def health_summary(self) -> dict[str, dict[str, Any]]:
        """Return health summary for all tracked providers."""
        return {
            provider: {
                "status": h.status.value,
                "failures": h.failure_count,
                "successes": h.success_count,
                "consecutive_failures": h.consecutive_failures,
                "avg_latency_ms": round(h.avg_latency * 1000, 1),
            }
            for provider, h in self._health.items()
        }
