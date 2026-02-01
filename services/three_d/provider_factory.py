# services/three_d/provider_factory.py
"""3D Provider Factory with Failover Support.

Implements US-017: Provider selection, caching, and automatic failover.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from services.three_d.provider_interface import (
    I3DProvider,
    ProviderHealth,
    ProviderStatus,
    ThreeDCapability,
    ThreeDProviderError,
    ThreeDRequest,
    ThreeDResponse,
    ThreeDTimeoutError,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


class ProviderPriority(str, Enum):
    """Provider priority levels."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    FALLBACK = "fallback"


@dataclass
class ProviderConfig:
    """Configuration for a provider in the factory."""

    provider_type: str
    priority: ProviderPriority
    enabled: bool = True
    weight: int = 100  # For weighted selection
    max_retries: int = 2
    circuit_breaker_threshold: int = 5  # Failures before circuit opens
    circuit_breaker_reset_seconds: int = 60


@dataclass
class FactoryConfig:
    """Factory configuration."""

    # Provider priority order
    text_to_3d_order: list[str] = field(
        default_factory=lambda: ["tripo", "replicate", "huggingface"]
    )
    image_to_3d_order: list[str] = field(
        default_factory=lambda: ["tripo", "huggingface", "replicate"]
    )
    # Image generation order (Gemini Nano Banana Pro is primary - no rate limits)
    image_generation_order: list[str] = field(
        default_factory=lambda: ["gemini", "replicate", "huggingface"]
    )

    # Failover settings
    enable_failover: bool = True
    max_failover_attempts: int = 3

    # Health check settings
    health_check_interval_seconds: int = 60
    enable_periodic_health_checks: bool = False

    # Caching
    cache_provider_health: bool = True
    health_cache_ttl_seconds: int = 30

    @classmethod
    def from_env(cls) -> FactoryConfig:
        """Create config from environment."""
        return cls(
            enable_failover=os.getenv("THREE_D_ENABLE_FAILOVER", "true").lower() == "true",
            max_failover_attempts=int(os.getenv("THREE_D_MAX_FAILOVER", "3")),
        )


# =============================================================================
# Circuit Breaker
# =============================================================================


@dataclass
class CircuitBreakerState:
    """State for a circuit breaker."""

    failures: int = 0
    last_failure: datetime | None = None
    is_open: bool = False
    opened_at: datetime | None = None


# =============================================================================
# Factory Implementation
# =============================================================================


class ThreeDProviderFactory:
    """Factory for 3D generation providers with failover.

    Manages multiple 3D providers and handles:
    - Provider selection based on capabilities and priority
    - Automatic failover on provider failure
    - Circuit breaker pattern to avoid cascading failures
    - Health monitoring and caching

    Usage:
        factory = get_provider_factory()

        # Use best available provider
        response = await factory.generate(
            ThreeDRequest(prompt="luxury hoodie")
        )

        # Use specific provider
        response = await factory.generate(
            ThreeDRequest(image_path="/path/to/image.jpg"),
            provider_name="trellis"
        )
    """

    def __init__(self, config: FactoryConfig | None = None) -> None:
        self.config = config or FactoryConfig.from_env()
        self._providers: dict[str, I3DProvider] = {}
        self._provider_configs: dict[str, ProviderConfig] = {}
        self._circuit_breakers: dict[str, CircuitBreakerState] = {}
        self._health_cache: dict[str, tuple[ProviderHealth, datetime]] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all providers."""
        if self._initialized:
            return

        # Import providers here to avoid circular imports
        from services.three_d.huggingface_provider import HuggingFaceProvider
        from services.three_d.replicate_provider import ReplicateProvider
        from services.three_d.tripo_provider import TripoProvider

        # Register providers
        self._register_provider(
            "tripo",
            TripoProvider(),
            ProviderConfig(
                provider_type="tripo",
                priority=ProviderPriority.PRIMARY,
                weight=100,
            ),
        )

        self._register_provider(
            "replicate",
            ReplicateProvider(),
            ProviderConfig(
                provider_type="replicate",
                priority=ProviderPriority.SECONDARY,
                weight=80,
            ),
        )

        self._register_provider(
            "huggingface",
            HuggingFaceProvider(),
            ProviderConfig(
                provider_type="huggingface",
                priority=ProviderPriority.FALLBACK,
                weight=60,
            ),
        )

        # Register Gemini provider (Nano Banana Pro) - no rate limits
        try:
            from services.three_d.gemini_provider import GeminiImageProvider

            self._register_provider(
                "gemini",
                GeminiImageProvider(),
                ProviderConfig(
                    provider_type="gemini",
                    priority=ProviderPriority.PRIMARY,  # Primary for image gen
                    weight=120,  # Higher weight - no rate limits
                ),
            )
            logger.info("Gemini Nano Banana Pro provider registered")
        except ImportError:
            logger.warning("Gemini provider not available")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini provider: {e}")

        self._initialized = True
        logger.info(f"ThreeDProviderFactory initialized with {len(self._providers)} providers")

    def _register_provider(
        self,
        name: str,
        provider: I3DProvider,
        config: ProviderConfig,
    ) -> None:
        """Register a provider."""
        self._providers[name] = provider
        self._provider_configs[name] = config
        self._circuit_breakers[name] = CircuitBreakerState()

    def _generate_correlation_id(self) -> str:
        """Generate correlation ID."""
        return str(uuid.uuid4())

    def _is_circuit_open(self, provider_name: str) -> bool:
        """Check if circuit breaker is open for provider."""
        state = self._circuit_breakers.get(provider_name)
        if not state or not state.is_open:
            return False

        # Check if reset period has passed
        config = self._provider_configs.get(provider_name)
        if config and state.opened_at:
            reset_time = state.opened_at + timedelta(seconds=config.circuit_breaker_reset_seconds)
            if datetime.now(UTC) > reset_time:
                # Reset circuit breaker
                state.is_open = False
                state.failures = 0
                state.opened_at = None
                logger.info(f"Circuit breaker reset for provider {provider_name}")
                return False

        return True

    def _record_failure(self, provider_name: str, error: Exception) -> None:
        """Record a provider failure."""
        state = self._circuit_breakers.get(provider_name)
        config = self._provider_configs.get(provider_name)

        if state and config:
            state.failures += 1
            state.last_failure = datetime.now(UTC)

            if state.failures >= config.circuit_breaker_threshold:
                state.is_open = True
                state.opened_at = datetime.now(UTC)
                logger.warning(
                    f"Circuit breaker opened for provider {provider_name} "
                    f"after {state.failures} failures"
                )

    def _record_success(self, provider_name: str) -> None:
        """Record a provider success."""
        state = self._circuit_breakers.get(provider_name)
        if state:
            state.failures = 0
            state.is_open = False
            state.opened_at = None

    async def _get_health_cached(self, provider_name: str) -> ProviderHealth | None:
        """Get cached health status."""
        if not self.config.cache_provider_health:
            return None

        cached = self._health_cache.get(provider_name)
        if cached:
            health, timestamp = cached
            if datetime.now(UTC) - timestamp < timedelta(
                seconds=self.config.health_cache_ttl_seconds
            ):
                return health

        return None

    async def _cache_health(self, provider_name: str, health: ProviderHealth) -> None:
        """Cache health status."""
        if self.config.cache_provider_health:
            self._health_cache[provider_name] = (health, datetime.now(UTC))

    def _select_providers(
        self,
        request: ThreeDRequest,
        provider_name: str | None = None,
    ) -> list[str]:
        """Select providers in order of preference."""
        # If specific provider requested, use only that
        if provider_name:
            if provider_name not in self._providers:
                raise ThreeDProviderError(
                    f"Unknown provider: {provider_name}",
                    provider=provider_name,
                )
            return [provider_name]

        # Select based on request type
        if request.is_text_request():
            order = self.config.text_to_3d_order
            required_cap = ThreeDCapability.TEXT_TO_3D
        else:
            order = self.config.image_to_3d_order
            required_cap = ThreeDCapability.IMAGE_TO_3D

        # Filter to available providers with required capability
        available = []
        for name in order:
            provider = self._providers.get(name)
            config = self._provider_configs.get(name)

            if not provider or not config or not config.enabled:
                continue

            if required_cap not in provider.capabilities:
                continue

            if self._is_circuit_open(name):
                logger.debug(f"Skipping provider {name}: circuit breaker open")
                continue

            available.append(name)

        return available

    async def generate(
        self,
        request: ThreeDRequest,
        *,
        provider_name: str | None = None,
        correlation_id: str | None = None,
    ) -> ThreeDResponse:
        """Generate 3D model using best available provider.

        Handles automatic failover if primary provider fails.

        Args:
            request: ThreeDRequest with generation parameters
            provider_name: Optional specific provider to use
            correlation_id: Optional correlation ID for tracing

        Returns:
            ThreeDResponse with generation result

        Raises:
            ThreeDProviderError: If all providers fail
        """
        await self.initialize()

        correlation_id = correlation_id or request.correlation_id or self._generate_correlation_id()
        request.correlation_id = correlation_id

        providers = self._select_providers(request, provider_name)

        if not providers:
            raise ThreeDProviderError(
                "No available providers for request",
                correlation_id=correlation_id,
            )

        # Limit to max failover attempts
        providers = providers[: self.config.max_failover_attempts]

        errors: list[tuple[str, Exception]] = []

        for provider_name in providers:
            provider = self._providers[provider_name]
            config = self._provider_configs[provider_name]

            logger.info(
                f"Attempting 3D generation with provider {provider_name}",
                extra={"correlation_id": correlation_id},
            )

            retries = 0
            while retries <= config.max_retries:
                try:
                    # Generate based on request type
                    if request.is_text_request():
                        response = await provider.generate_from_text(request)
                    else:
                        response = await provider.generate_from_image(request)

                    # Success
                    self._record_success(provider_name)

                    logger.info(
                        f"3D generation completed with provider {provider_name}",
                        extra={
                            "correlation_id": correlation_id,
                            "task_id": response.task_id,
                            "duration_seconds": response.duration_seconds,
                        },
                    )

                    return response

                except ThreeDTimeoutError as e:
                    retries += 1
                    if retries <= config.max_retries:
                        logger.warning(
                            f"Provider {provider_name} timed out, retry {retries}/{config.max_retries}",
                            extra={"correlation_id": correlation_id},
                        )
                    else:
                        errors.append((provider_name, e))
                        self._record_failure(provider_name, e)
                        break

                except ThreeDProviderError as e:
                    if e.retryable and retries < config.max_retries:
                        retries += 1
                        logger.warning(
                            f"Provider {provider_name} failed (retryable), retry {retries}/{config.max_retries}",
                            extra={"correlation_id": correlation_id},
                        )
                    else:
                        errors.append((provider_name, e))
                        self._record_failure(provider_name, e)
                        break

                except Exception as e:
                    errors.append((provider_name, e))
                    self._record_failure(provider_name, e)
                    break

            # Check if failover is enabled
            if not self.config.enable_failover:
                break

        # All providers failed
        error_summary = "; ".join(f"{name}: {str(err)}" for name, err in errors)
        raise ThreeDProviderError(
            f"All providers failed: {error_summary}",
            correlation_id=correlation_id,
        )

    async def health_check(
        self,
        provider_name: str | None = None,
    ) -> dict[str, ProviderHealth]:
        """Check health of providers.

        Args:
            provider_name: Optional specific provider to check

        Returns:
            Dict of provider name to ProviderHealth
        """
        await self.initialize()

        results: dict[str, ProviderHealth] = {}
        providers = [provider_name] if provider_name else list(self._providers.keys())

        for name in providers:
            provider = self._providers.get(name)
            if not provider:
                continue

            # Check cache first
            cached = await self._get_health_cached(name)
            if cached:
                results[name] = cached
                continue

            # Run health check
            health = await provider.health_check()

            # Add circuit breaker status
            if self._is_circuit_open(name):
                health.status = ProviderStatus.UNAVAILABLE
                health.error_message = "Circuit breaker open"

            await self._cache_health(name, health)
            results[name] = health

        return results

    async def list_providers(self) -> list[dict[str, Any]]:
        """List all registered providers with status."""
        await self.initialize()

        health_results = await self.health_check()

        providers = []
        for name, provider in self._providers.items():
            config = self._provider_configs.get(name)
            health = health_results.get(name)

            providers.append(
                {
                    "name": name,
                    "capabilities": [c.value for c in provider.capabilities],
                    "priority": config.priority.value if config else "unknown",
                    "enabled": config.enabled if config else False,
                    "status": health.status.value if health else "unknown",
                    "latency_ms": health.latency_ms if health else None,
                    "circuit_breaker_open": self._is_circuit_open(name),
                }
            )

        return providers

    async def close(self) -> None:
        """Close all provider resources."""
        for provider in self._providers.values():
            await provider.close()
        self._providers.clear()
        self._initialized = False


# =============================================================================
# Singleton Factory
# =============================================================================

_factory_instance: ThreeDProviderFactory | None = None


def get_provider_factory() -> ThreeDProviderFactory:
    """Get the singleton provider factory instance."""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = ThreeDProviderFactory()
    return _factory_instance


async def reset_provider_factory() -> None:
    """Reset the factory instance (for testing)."""
    global _factory_instance
    if _factory_instance:
        await _factory_instance.close()
        _factory_instance = None


__all__ = [
    "ThreeDProviderFactory",
    "FactoryConfig",
    "ProviderConfig",
    "ProviderPriority",
    "get_provider_factory",
    "reset_provider_factory",
]
