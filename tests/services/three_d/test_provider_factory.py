# tests/services/three_d/test_provider_factory.py
"""Tests for 3D provider factory."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from services.three_d.provider_factory import (
    FactoryConfig,
    ProviderConfig,
    ProviderPriority,
    ThreeDProviderFactory,
)
from services.three_d.provider_interface import (
    OutputFormat,
    ProviderHealth,
    ProviderStatus,
    ThreeDCapability,
    ThreeDProviderError,
    ThreeDRequest,
    ThreeDResponse,
)


@pytest.fixture
def factory_config() -> FactoryConfig:
    """Create test factory config."""
    return FactoryConfig(
        enable_failover=True,
        max_failover_attempts=3,
        cache_provider_health=False,
    )


@pytest.fixture
def mock_provider() -> MagicMock:
    """Create a mock provider."""
    provider = MagicMock()
    provider.name = "mock_provider"
    provider.capabilities = [ThreeDCapability.TEXT_TO_3D, ThreeDCapability.IMAGE_TO_3D]

    # Mock async methods
    provider.generate_from_text = AsyncMock(
        return_value=ThreeDResponse(
            success=True,
            task_id="mock_task_123",
            status="completed",
            provider="mock_provider",
            model_path="/path/to/model.glb",
            output_format=OutputFormat.GLB,
        )
    )
    provider.generate_from_image = AsyncMock(
        return_value=ThreeDResponse(
            success=True,
            task_id="mock_task_456",
            status="completed",
            provider="mock_provider",
            model_path="/path/to/model.glb",
            output_format=OutputFormat.GLB,
        )
    )
    provider.health_check = AsyncMock(
        return_value=ProviderHealth(
            provider="mock_provider",
            status=ProviderStatus.AVAILABLE,
            capabilities=[ThreeDCapability.TEXT_TO_3D, ThreeDCapability.IMAGE_TO_3D],
        )
    )
    provider.close = AsyncMock()

    return provider


class TestFactoryConfig:
    """Tests for FactoryConfig."""

    def test_default_values(self) -> None:
        """Config should have sensible defaults."""
        config = FactoryConfig()
        assert config.enable_failover is True
        assert config.max_failover_attempts == 3
        assert "tripo" in config.text_to_3d_order

    def test_from_env(self) -> None:
        """Config should be creatable from environment."""
        config = FactoryConfig.from_env()
        assert isinstance(config, FactoryConfig)


class TestProviderRegistration:
    """Tests for provider registration."""

    @pytest.mark.asyncio
    async def test_register_provider(
        self,
        factory_config: FactoryConfig,
        mock_provider: MagicMock,
    ) -> None:
        """Factory should register and track providers."""
        factory = ThreeDProviderFactory(factory_config)
        factory._register_provider(
            "mock",
            mock_provider,
            ProviderConfig(
                provider_type="mock",
                priority=ProviderPriority.PRIMARY,
            ),
        )

        assert "mock" in factory._providers
        assert "mock" in factory._provider_configs
        assert "mock" in factory._circuit_breakers


class TestProviderSelection:
    """Tests for provider selection logic."""

    @pytest.mark.asyncio
    async def test_select_text_providers(
        self,
        factory_config: FactoryConfig,
        mock_provider: MagicMock,
    ) -> None:
        """Factory should select providers for text-to-3D."""
        factory = ThreeDProviderFactory(factory_config)
        factory._register_provider(
            "mock",
            mock_provider,
            ProviderConfig(
                provider_type="mock",
                priority=ProviderPriority.PRIMARY,
            ),
        )
        factory.config.text_to_3d_order = ["mock"]

        request = ThreeDRequest(prompt="test prompt")
        providers = factory._select_providers(request)

        assert "mock" in providers

    @pytest.mark.asyncio
    async def test_select_image_providers(
        self,
        factory_config: FactoryConfig,
        mock_provider: MagicMock,
    ) -> None:
        """Factory should select providers for image-to-3D."""
        factory = ThreeDProviderFactory(factory_config)
        factory._register_provider(
            "mock",
            mock_provider,
            ProviderConfig(
                provider_type="mock",
                priority=ProviderPriority.PRIMARY,
            ),
        )
        factory.config.image_to_3d_order = ["mock"]

        request = ThreeDRequest(image_path="/path/to/image.jpg")
        providers = factory._select_providers(request)

        assert "mock" in providers

    @pytest.mark.asyncio
    async def test_select_specific_provider(
        self,
        factory_config: FactoryConfig,
        mock_provider: MagicMock,
    ) -> None:
        """Factory should allow selecting a specific provider."""
        factory = ThreeDProviderFactory(factory_config)
        factory._register_provider(
            "mock",
            mock_provider,
            ProviderConfig(
                provider_type="mock",
                priority=ProviderPriority.PRIMARY,
            ),
        )

        request = ThreeDRequest(prompt="test")
        providers = factory._select_providers(request, provider_name="mock")

        assert providers == ["mock"]


class TestCircuitBreaker:
    """Tests for circuit breaker functionality."""

    def test_circuit_initially_closed(
        self,
        factory_config: FactoryConfig,
        mock_provider: MagicMock,
    ) -> None:
        """Circuit breaker should be closed initially."""
        factory = ThreeDProviderFactory(factory_config)
        factory._register_provider(
            "mock",
            mock_provider,
            ProviderConfig(
                provider_type="mock",
                priority=ProviderPriority.PRIMARY,
                circuit_breaker_threshold=3,
            ),
        )

        assert factory._is_circuit_open("mock") is False

    def test_circuit_opens_after_threshold(
        self,
        factory_config: FactoryConfig,
        mock_provider: MagicMock,
    ) -> None:
        """Circuit breaker should open after failure threshold."""
        factory = ThreeDProviderFactory(factory_config)
        factory._register_provider(
            "mock",
            mock_provider,
            ProviderConfig(
                provider_type="mock",
                priority=ProviderPriority.PRIMARY,
                circuit_breaker_threshold=3,
            ),
        )

        # Record failures
        for _ in range(3):
            factory._record_failure("mock", Exception("test"))

        assert factory._is_circuit_open("mock") is True

    def test_success_resets_circuit(
        self,
        factory_config: FactoryConfig,
        mock_provider: MagicMock,
    ) -> None:
        """Circuit breaker should reset after success."""
        factory = ThreeDProviderFactory(factory_config)
        factory._register_provider(
            "mock",
            mock_provider,
            ProviderConfig(
                provider_type="mock",
                priority=ProviderPriority.PRIMARY,
                circuit_breaker_threshold=3,
            ),
        )

        # Record some failures (but not enough to open)
        factory._record_failure("mock", Exception("test"))
        factory._record_failure("mock", Exception("test"))

        # Record success
        factory._record_success("mock")

        # Check failures were reset
        assert factory._circuit_breakers["mock"].failures == 0


class TestGeneration:
    """Tests for generation with mock providers."""

    @pytest.mark.asyncio
    async def test_generate_text_to_3d(
        self,
        factory_config: FactoryConfig,
        mock_provider: MagicMock,
    ) -> None:
        """Factory should generate from text using provider."""
        factory = ThreeDProviderFactory(factory_config)
        factory._register_provider(
            "mock",
            mock_provider,
            ProviderConfig(
                provider_type="mock",
                priority=ProviderPriority.PRIMARY,
            ),
        )
        factory.config.text_to_3d_order = ["mock"]
        factory._initialized = True

        request = ThreeDRequest(prompt="luxury hoodie")
        response = await factory.generate(request)

        assert response.success is True
        assert response.task_id == "mock_task_123"
        mock_provider.generate_from_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_image_to_3d(
        self,
        factory_config: FactoryConfig,
        mock_provider: MagicMock,
    ) -> None:
        """Factory should generate from image using provider."""
        factory = ThreeDProviderFactory(factory_config)
        factory._register_provider(
            "mock",
            mock_provider,
            ProviderConfig(
                provider_type="mock",
                priority=ProviderPriority.PRIMARY,
            ),
        )
        factory.config.image_to_3d_order = ["mock"]
        factory._initialized = True

        request = ThreeDRequest(image_path="/path/to/image.jpg")
        response = await factory.generate(request)

        assert response.success is True
        assert response.task_id == "mock_task_456"
        mock_provider.generate_from_image.assert_called_once()


class TestFailover:
    """Tests for failover functionality."""

    @pytest.mark.asyncio
    async def test_failover_to_second_provider(
        self,
        factory_config: FactoryConfig,
    ) -> None:
        """Factory should failover to second provider on failure."""
        factory = ThreeDProviderFactory(factory_config)

        # First provider fails
        failing_provider = MagicMock()
        failing_provider.name = "failing"
        failing_provider.capabilities = [ThreeDCapability.TEXT_TO_3D]
        failing_provider.generate_from_text = AsyncMock(
            side_effect=ThreeDProviderError("Failed", provider="failing")
        )
        failing_provider.close = AsyncMock()

        # Second provider succeeds
        success_provider = MagicMock()
        success_provider.name = "success"
        success_provider.capabilities = [ThreeDCapability.TEXT_TO_3D]
        success_provider.generate_from_text = AsyncMock(
            return_value=ThreeDResponse(
                success=True,
                task_id="success_task",
                status="completed",
                provider="success",
            )
        )
        success_provider.close = AsyncMock()

        factory._register_provider(
            "failing",
            failing_provider,
            ProviderConfig(provider_type="failing", priority=ProviderPriority.PRIMARY),
        )
        factory._register_provider(
            "success",
            success_provider,
            ProviderConfig(provider_type="success", priority=ProviderPriority.SECONDARY),
        )
        factory.config.text_to_3d_order = ["failing", "success"]
        factory._initialized = True

        request = ThreeDRequest(prompt="test")
        response = await factory.generate(request)

        assert response.success is True
        assert response.provider == "success"

    @pytest.mark.asyncio
    async def test_all_providers_fail(
        self,
        factory_config: FactoryConfig,
    ) -> None:
        """Factory should raise error when all providers fail."""
        factory = ThreeDProviderFactory(factory_config)

        failing_provider = MagicMock()
        failing_provider.name = "failing"
        failing_provider.capabilities = [ThreeDCapability.TEXT_TO_3D]
        failing_provider.generate_from_text = AsyncMock(
            side_effect=ThreeDProviderError("Failed", provider="failing")
        )
        failing_provider.close = AsyncMock()

        factory._register_provider(
            "failing",
            failing_provider,
            ProviderConfig(provider_type="failing", priority=ProviderPriority.PRIMARY),
        )
        factory.config.text_to_3d_order = ["failing"]
        factory._initialized = True

        request = ThreeDRequest(prompt="test")

        with pytest.raises(ThreeDProviderError) as exc_info:
            await factory.generate(request)

        assert "All providers failed" in str(exc_info.value)


class TestHealthCheck:
    """Tests for health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_all_providers(
        self,
        factory_config: FactoryConfig,
        mock_provider: MagicMock,
    ) -> None:
        """Factory should check health of all providers."""
        factory = ThreeDProviderFactory(factory_config)
        factory._register_provider(
            "mock",
            mock_provider,
            ProviderConfig(provider_type="mock", priority=ProviderPriority.PRIMARY),
        )
        factory._initialized = True

        results = await factory.health_check()

        assert "mock" in results
        assert results["mock"].status == ProviderStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_health_check_specific_provider(
        self,
        factory_config: FactoryConfig,
        mock_provider: MagicMock,
    ) -> None:
        """Factory should check health of specific provider."""
        factory = ThreeDProviderFactory(factory_config)
        factory._register_provider(
            "mock",
            mock_provider,
            ProviderConfig(provider_type="mock", priority=ProviderPriority.PRIMARY),
        )
        factory._initialized = True

        results = await factory.health_check(provider_name="mock")

        assert len(results) == 1
        assert "mock" in results


class TestListProviders:
    """Tests for listing providers."""

    @pytest.mark.asyncio
    async def test_list_providers(
        self,
        factory_config: FactoryConfig,
        mock_provider: MagicMock,
    ) -> None:
        """Factory should list all registered providers."""
        factory = ThreeDProviderFactory(factory_config)
        factory._register_provider(
            "mock",
            mock_provider,
            ProviderConfig(provider_type="mock", priority=ProviderPriority.PRIMARY),
        )
        factory._initialized = True

        providers = await factory.list_providers()

        assert len(providers) == 1
        assert providers[0]["name"] == "mock"
        assert providers[0]["priority"] == "primary"
        assert "text_to_3d" in providers[0]["capabilities"]
