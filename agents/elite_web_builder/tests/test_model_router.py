"""Tests for core/model_router.py — Multi-provider routing + fallback chain."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.model_router import (
    ModelRouter,
    ProviderConfig,
    ProviderHealth,
    ProviderStatus,
    RouteResult,
    RoutingConfig,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def routing_config() -> RoutingConfig:
    """Standard routing config matching the spec."""
    return RoutingConfig(
        routes={
            "director": ProviderConfig(
                provider="anthropic", model="claude-opus-4-6"
            ),
            "design_system": ProviderConfig(
                provider="google", model="gemini-3-pro-preview"
            ),
            "frontend_dev": ProviderConfig(
                provider="anthropic", model="claude-sonnet-4-6"
            ),
            "backend_dev": ProviderConfig(
                provider="anthropic", model="claude-sonnet-4-6"
            ),
            "accessibility": ProviderConfig(
                provider="anthropic", model="claude-haiku-4-5"
            ),
            "performance": ProviderConfig(
                provider="google", model="gemini-3-flash-preview"
            ),
            "seo_content": ProviderConfig(
                provider="openai", model="gpt-4o"
            ),
            "qa": ProviderConfig(
                provider="xai", model="grok-3"
            ),
        },
        fallbacks={
            "anthropic": ProviderConfig(
                provider="google", model="gemini-3-pro-preview"
            ),
            "google": ProviderConfig(
                provider="anthropic", model="claude-sonnet-4-6"
            ),
            "openai": ProviderConfig(
                provider="anthropic", model="claude-sonnet-4-6"
            ),
            "xai": ProviderConfig(
                provider="google", model="gemini-3-flash-preview"
            ),
        },
    )


@pytest.fixture
def router(routing_config: RoutingConfig) -> ModelRouter:
    return ModelRouter(config=routing_config)


# ---------------------------------------------------------------------------
# ProviderConfig immutability
# ---------------------------------------------------------------------------


class TestProviderConfig:
    def test_provider_config_frozen(self) -> None:
        cfg = ProviderConfig(provider="anthropic", model="claude-opus-4-6")
        with pytest.raises(Exception):
            cfg.provider = "google"  # type: ignore[misc]

    def test_provider_config_fields(self) -> None:
        cfg = ProviderConfig(provider="google", model="gemini-3-pro-preview")
        assert cfg.provider == "google"
        assert cfg.model == "gemini-3-pro-preview"


# ---------------------------------------------------------------------------
# Routing resolution
# ---------------------------------------------------------------------------


class TestRoutingResolution:
    def test_resolve_known_agent(self, router: ModelRouter) -> None:
        result = router.resolve("director")
        assert result.provider == "anthropic"
        assert result.model == "claude-opus-4-6"
        assert result.is_fallback is False

    def test_resolve_all_agents(self, router: ModelRouter) -> None:
        agents = [
            "director", "design_system", "frontend_dev", "backend_dev",
            "accessibility", "performance", "seo_content", "qa",
        ]
        for agent in agents:
            result = router.resolve(agent)
            assert result.provider is not None
            assert result.model is not None

    def test_resolve_unknown_agent_uses_default(self, router: ModelRouter) -> None:
        result = router.resolve("unknown_agent")
        # Should fall back to a sensible default, not crash
        assert result.provider is not None
        assert result.model is not None
        assert result.is_fallback is True


# ---------------------------------------------------------------------------
# Fallback chain
# ---------------------------------------------------------------------------


class TestFallbackChain:
    def test_get_fallback_for_provider(self, router: ModelRouter) -> None:
        fb = router.get_fallback("anthropic")
        assert fb is not None
        assert fb.provider == "google"

    def test_get_fallback_for_unknown_provider(self, router: ModelRouter) -> None:
        fb = router.get_fallback("nonexistent")
        # Should return a default fallback, not None
        assert fb is not None

    def test_fallback_chain_resolves(self, router: ModelRouter) -> None:
        """When primary fails, fallback should be used."""
        # Mark anthropic as unhealthy
        router.mark_unhealthy("anthropic")
        result = router.resolve("director")
        # Should use google fallback
        assert result.provider == "google"
        assert result.is_fallback is True


# ---------------------------------------------------------------------------
# Provider health tracking
# ---------------------------------------------------------------------------


class TestProviderHealth:
    def test_initial_health_is_healthy(self, router: ModelRouter) -> None:
        health = router.get_health("anthropic")
        assert health.status == ProviderStatus.HEALTHY

    def test_mark_unhealthy(self, router: ModelRouter) -> None:
        router.mark_unhealthy("anthropic")
        health = router.get_health("anthropic")
        assert health.status == ProviderStatus.UNHEALTHY

    def test_mark_healthy_recovers(self, router: ModelRouter) -> None:
        router.mark_unhealthy("anthropic")
        router.mark_healthy("anthropic")
        health = router.get_health("anthropic")
        assert health.status == ProviderStatus.HEALTHY

    def test_record_latency(self, router: ModelRouter) -> None:
        router.record_latency("google", 0.5)
        router.record_latency("google", 1.0)
        health = router.get_health("google")
        assert health.avg_latency == pytest.approx(0.75, rel=0.01)

    def test_record_failure_increments(self, router: ModelRouter) -> None:
        router.record_failure("openai")
        router.record_failure("openai")
        health = router.get_health("openai")
        assert health.failure_count == 2

    def test_auto_unhealthy_after_threshold(self, router: ModelRouter) -> None:
        """Provider becomes unhealthy after 5 consecutive failures."""
        for _ in range(5):
            router.record_failure("xai")
        health = router.get_health("xai")
        assert health.status == ProviderStatus.UNHEALTHY


# ---------------------------------------------------------------------------
# Async provider call with ralph-loop resilience
# ---------------------------------------------------------------------------


class TestAsyncProviderCall:
    @pytest.mark.asyncio
    async def test_call_provider_success(self, router: ModelRouter) -> None:
        mock_fn = AsyncMock(return_value="response text")
        result = await router.call_with_fallback(
            agent_name="director",
            operation=mock_fn,
        )
        assert result == "response text"
        mock_fn.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_provider_fallback_on_failure(self, router: ModelRouter) -> None:
        """Primary fails, fallback succeeds."""
        call_count = 0

        async def flaky_operation(provider: str, model: str) -> str:
            nonlocal call_count
            call_count += 1
            if provider == "anthropic":
                raise ConnectionError("Primary down")
            return f"fallback-{provider}"

        result = await router.call_with_fallback(
            agent_name="director",
            operation=flaky_operation,
        )
        assert "fallback" in result
        assert call_count >= 2  # tried primary, then fallback

    @pytest.mark.asyncio
    async def test_call_provider_all_fail_raises(self, router: ModelRouter) -> None:
        """When all providers fail, raises after exhausting retries."""
        async def always_fail(provider: str, model: str) -> str:
            raise ConnectionError(f"{provider} is down")

        with pytest.raises(Exception):
            await router.call_with_fallback(
                agent_name="director",
                operation=always_fail,
                max_attempts=2,
            )

    @pytest.mark.asyncio
    async def test_call_records_health_on_success(self, router: ModelRouter) -> None:
        mock_fn = AsyncMock(return_value="ok")
        await router.call_with_fallback(
            agent_name="seo_content",
            operation=mock_fn,
        )
        health = router.get_health("openai")
        assert health.success_count >= 1

    @pytest.mark.asyncio
    async def test_call_records_health_on_failure(self, router: ModelRouter) -> None:
        async def fail_once(provider: str, model: str) -> str:
            if provider == "openai":
                raise ConnectionError("down")
            return "ok"

        await router.call_with_fallback(
            agent_name="seo_content",
            operation=fail_once,
        )
        health = router.get_health("openai")
        assert health.failure_count >= 1


# ---------------------------------------------------------------------------
# Config loading from JSON
# ---------------------------------------------------------------------------


class TestConfigLoading:
    def test_from_dict(self) -> None:
        data = {
            "routes": {
                "director": {"provider": "anthropic", "model": "claude-opus-4-6"},
            },
            "fallbacks": {
                "anthropic": {"provider": "google", "model": "gemini-3-pro-preview"},
            },
        }
        config = RoutingConfig.from_dict(data)
        assert "director" in config.routes
        assert config.routes["director"].provider == "anthropic"

    def test_from_dict_empty_fallbacks(self) -> None:
        data = {
            "routes": {
                "test": {"provider": "openai", "model": "gpt-4o"},
            },
            "fallbacks": {},
        }
        config = RoutingConfig.from_dict(data)
        assert len(config.fallbacks) == 0
