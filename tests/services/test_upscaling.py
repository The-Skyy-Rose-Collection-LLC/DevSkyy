# tests/services/test_upscaling.py
"""Unit tests for UpscalingService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.ml.enhancement.upscaling import (
    DEFAULT_UPSCALE_MODEL,
    FALLBACK_MODELS,
    MIN_RESOLUTION_LONGEST_EDGE,
    UpscaleResult,
    UpscalingError,
    UpscalingService,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_replicate_client() -> MagicMock:
    """Create mock Replicate client."""
    client = MagicMock()
    client.connect = AsyncMock()
    client.close = AsyncMock()
    client._generate_correlation_id = MagicMock(return_value="test-corr-123")
    return client


@pytest.fixture
def service(mock_replicate_client: MagicMock) -> UpscalingService:
    """Create service with mock client."""
    return UpscalingService(replicate_client=mock_replicate_client)


# =============================================================================
# Model Tests
# =============================================================================


class TestUpscaleResult:
    """Test UpscaleResult model."""

    def test_actual_scale_calculation(self) -> None:
        """actual_scale should calculate scale factor correctly."""
        result = UpscaleResult(
            original_url="https://example.com/original.jpg",
            result_url="https://example.com/result.jpg",
            original_dimensions=(500, 400),
            result_dimensions=(2000, 1600),
            scale_factor=4,
            model_used="test-model",
            face_enhance=False,
            processing_time_ms=100,
            correlation_id="test-123",
        )
        assert result.actual_scale == 4.0

    def test_actual_scale_zero_original(self) -> None:
        """actual_scale should return 0 for zero-dimension original."""
        result = UpscaleResult(
            original_url="https://example.com/original.jpg",
            result_url="https://example.com/result.jpg",
            original_dimensions=(0, 0),
            result_dimensions=(2000, 1600),
            scale_factor=4,
            model_used="test-model",
            face_enhance=False,
            processing_time_ms=100,
            correlation_id="test-123",
        )
        assert result.actual_scale == 0.0

    def test_skipped_result(self) -> None:
        """Skipped result should have matching URLs and dimensions."""
        result = UpscaleResult(
            original_url="https://example.com/original.jpg",
            result_url="https://example.com/original.jpg",
            original_dimensions=(3000, 2000),
            result_dimensions=(3000, 2000),
            scale_factor=4,
            model_used="",
            face_enhance=False,
            skipped=True,
            skip_reason="Already meets minimum resolution",
            processing_time_ms=10,
            correlation_id="test-123",
        )
        assert result.skipped is True
        assert result.original_url == result.result_url


class TestUpscalingError:
    """Test UpscalingError class."""

    def test_error_with_all_context(self) -> None:
        """Error should include all context fields."""
        error = UpscalingError(
            "Test error",
            image_url="https://example.com/image.jpg",
            model="test-model",
            correlation_id="corr-123",
        )
        assert "Test error" in str(error)
        assert error.correlation_id == "corr-123"
        assert error.context["image_url"] == "https://example.com/image.jpg"
        assert error.context["model"] == "test-model"

    def test_error_with_cause(self) -> None:
        """Error should preserve cause exception."""
        cause = ValueError("Original error")
        error = UpscalingError("Wrapper error", cause=cause)
        assert error.cause is cause

    def test_error_is_retryable(self) -> None:
        """UpscalingError should be marked as retryable."""
        error = UpscalingError("Test error")
        assert error.retryable is True


# =============================================================================
# Service Tests
# =============================================================================


class TestUpscalingServiceInit:
    """Test service initialization."""

    def test_init_with_client(self, mock_replicate_client: MagicMock) -> None:
        """Service should accept pre-configured client."""
        service = UpscalingService(replicate_client=mock_replicate_client)
        assert service._client is mock_replicate_client
        assert service._owns_client is False

    def test_init_without_client(self) -> None:
        """Service should create client when none provided."""
        service = UpscalingService()
        assert service._client is None
        assert service._owns_client is True

    def test_init_custom_min_resolution(self) -> None:
        """Service should accept custom minimum resolution."""
        service = UpscalingService(min_resolution=3000)
        assert service._min_resolution == 3000


class TestUpscalingServiceContextManager:
    """Test async context manager functionality."""

    @pytest.mark.asyncio
    async def test_context_manager_enter(self, mock_replicate_client: MagicMock) -> None:
        """Context manager should return service on enter."""
        service = UpscalingService(replicate_client=mock_replicate_client)
        async with service as ctx:
            assert ctx is service

    @pytest.mark.asyncio
    async def test_context_manager_closes_owned_client(self) -> None:
        """Context manager should close owned client on exit."""
        mock_client = MagicMock()
        mock_client.connect = AsyncMock()
        mock_client.close = AsyncMock()

        service = UpscalingService()
        service._client = mock_client
        service._owns_client = True

        await service.close()
        mock_client.close.assert_called_once()


class TestShouldSkip:
    """Test resolution check logic."""

    def test_should_skip_above_threshold(self, service: UpscalingService) -> None:
        """Should skip images above minimum resolution."""
        should_skip, reason = service._should_skip((3000, 2000))
        assert should_skip is True
        assert reason is not None
        assert "3000" in reason

    def test_should_not_skip_below_threshold(self, service: UpscalingService) -> None:
        """Should not skip images below minimum resolution."""
        should_skip, reason = service._should_skip((800, 600))
        assert should_skip is False
        assert reason is None

    def test_should_not_skip_zero_dimensions(self, service: UpscalingService) -> None:
        """Should not skip when dimensions are unknown (0, 0)."""
        should_skip, reason = service._should_skip((0, 0))
        assert should_skip is False
        assert reason is None


class TestUpscaleImage:
    """Test upscale_image method."""

    @pytest.mark.asyncio
    async def test_upscale_success(
        self, service: UpscalingService, mock_replicate_client: MagicMock
    ) -> None:
        """Should successfully upscale image."""
        mock_prediction = MagicMock()
        mock_prediction.succeeded = True
        mock_prediction.output = "https://example.com/upscaled.jpg"
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_prediction)

        with patch.object(service, "_get_image_dimensions", new_callable=AsyncMock) as mock_dims:
            mock_dims.side_effect = [
                (500, 400),  # Original
                (2000, 1600),  # Result
            ]

            result = await service.upscale_image(
                "https://example.com/product.jpg",
                scale_factor=4,
            )

        assert result.result_url == "https://example.com/upscaled.jpg"
        assert result.scale_factor == 4
        assert result.skipped is False
        assert result.model_used == DEFAULT_UPSCALE_MODEL

    @pytest.mark.asyncio
    async def test_upscale_with_face_enhance(
        self, service: UpscalingService, mock_replicate_client: MagicMock
    ) -> None:
        """Should pass face_enhance parameter to model."""
        mock_prediction = MagicMock()
        mock_prediction.succeeded = True
        mock_prediction.output = "https://example.com/upscaled.jpg"
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_prediction)

        with patch.object(service, "_get_image_dimensions", new_callable=AsyncMock) as mock_dims:
            mock_dims.return_value = (500, 400)

            result = await service.upscale_image(
                "https://example.com/product.jpg",
                face_enhance=True,
            )

        assert result.face_enhance is True
        # Verify face_enhance was passed
        call_args = mock_replicate_client.run_prediction.call_args
        assert call_args[0][1]["face_enhance"] is True

    @pytest.mark.asyncio
    async def test_upscale_skip_sufficient_resolution(
        self, service: UpscalingService, mock_replicate_client: MagicMock
    ) -> None:
        """Should skip upscaling when image meets minimum resolution."""
        with patch.object(service, "_get_image_dimensions", new_callable=AsyncMock) as mock_dims:
            mock_dims.return_value = (3000, 2000)  # Above MIN_RESOLUTION

            result = await service.upscale_image(
                "https://example.com/product.jpg",
                skip_if_sufficient=True,
            )

        assert result.skipped is True
        assert result.original_url == result.result_url
        assert result.skip_reason is not None
        mock_replicate_client.run_prediction.assert_not_called()

    @pytest.mark.asyncio
    async def test_upscale_no_skip_when_disabled(
        self, service: UpscalingService, mock_replicate_client: MagicMock
    ) -> None:
        """Should not skip when skip_if_sufficient is False."""
        mock_prediction = MagicMock()
        mock_prediction.succeeded = True
        mock_prediction.output = "https://example.com/upscaled.jpg"
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_prediction)

        with patch.object(service, "_get_image_dimensions", new_callable=AsyncMock) as mock_dims:
            mock_dims.return_value = (3000, 2000)

            result = await service.upscale_image(
                "https://example.com/product.jpg",
                skip_if_sufficient=False,
            )

        assert result.skipped is False
        mock_replicate_client.run_prediction.assert_called()

    @pytest.mark.asyncio
    async def test_upscale_invalid_scale_factor(
        self, service: UpscalingService, mock_replicate_client: MagicMock
    ) -> None:
        """Should reject invalid scale factors."""
        with pytest.raises(UpscalingError) as exc_info:
            await service.upscale_image(
                "https://example.com/product.jpg",
                scale_factor=3,  # Invalid - only 2 or 4 allowed
            )

        assert "Invalid scale factor" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upscale_fallback_on_primary_failure(
        self, service: UpscalingService, mock_replicate_client: MagicMock
    ) -> None:
        """Should fallback to secondary model when primary fails."""
        mock_failed = MagicMock()
        mock_failed.succeeded = False
        mock_failed.output = None

        mock_success = MagicMock()
        mock_success.succeeded = True
        mock_success.output = "https://example.com/fallback-upscaled.jpg"

        mock_replicate_client.run_prediction = AsyncMock(side_effect=[mock_failed, mock_success])

        with patch.object(service, "_get_image_dimensions", new_callable=AsyncMock) as mock_dims:
            mock_dims.return_value = (500, 400)

            result = await service.upscale_image(
                "https://example.com/product.jpg",
            )

        assert result.result_url == "https://example.com/fallback-upscaled.jpg"
        assert result.model_used == FALLBACK_MODELS[0]

    @pytest.mark.asyncio
    async def test_upscale_all_models_fail(
        self, service: UpscalingService, mock_replicate_client: MagicMock
    ) -> None:
        """Should raise error when all models fail."""
        mock_failed = MagicMock()
        mock_failed.succeeded = False
        mock_failed.output = None

        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_failed)

        with (
            patch.object(service, "_get_image_dimensions", new_callable=AsyncMock) as mock_dims,
            pytest.raises(UpscalingError) as exc_info,
        ):
            mock_dims.return_value = (500, 400)
            await service.upscale_image("https://example.com/product.jpg")

        assert "All upscaling models failed" in str(exc_info.value)


class TestUpscaleBatch:
    """Test batch processing."""

    @pytest.mark.asyncio
    async def test_batch_success(
        self, service: UpscalingService, mock_replicate_client: MagicMock
    ) -> None:
        """Should process multiple images in batch."""
        mock_prediction = MagicMock()
        mock_prediction.succeeded = True
        mock_prediction.output = "https://example.com/upscaled.jpg"
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_prediction)

        with patch.object(service, "_get_image_dimensions", new_callable=AsyncMock) as mock_dims:
            mock_dims.return_value = (500, 400)

            results = await service.upscale_batch(
                [
                    "https://example.com/product1.jpg",
                    "https://example.com/product2.jpg",
                ]
            )

        assert len(results) == 2
        assert all(isinstance(r, UpscaleResult) for r in results)

    @pytest.mark.asyncio
    async def test_batch_partial_failure(
        self, service: UpscalingService, mock_replicate_client: MagicMock
    ) -> None:
        """Should return errors for failed items in batch."""
        call_count = 0

        async def prediction_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock = MagicMock()
            if call_count == 1:
                mock.succeeded = True
                mock.output = "https://example.com/result.jpg"
            else:
                mock.succeeded = False
                mock.output = None
            return mock

        mock_replicate_client.run_prediction = AsyncMock(side_effect=prediction_side_effect)

        with patch.object(service, "_get_image_dimensions", new_callable=AsyncMock) as mock_dims:
            mock_dims.return_value = (500, 400)

            results = await service.upscale_batch(
                [
                    "https://example.com/product1.jpg",
                    "https://example.com/product2.jpg",
                ]
            )

        assert len(results) == 2
        assert isinstance(results[0], UpscaleResult)
        assert isinstance(results[1], UpscalingError)


class TestConstants:
    """Test module constants."""

    def test_default_model_format(self) -> None:
        """Default model should follow Replicate format."""
        assert "/" in DEFAULT_UPSCALE_MODEL
        assert ":" in DEFAULT_UPSCALE_MODEL

    def test_min_resolution_reasonable(self) -> None:
        """Minimum resolution should be reasonable value."""
        assert MIN_RESOLUTION_LONGEST_EDGE >= 1000
        assert MIN_RESOLUTION_LONGEST_EDGE <= 5000

    def test_fallback_models_exist(self) -> None:
        """Fallback models should be defined."""
        assert len(FALLBACK_MODELS) >= 1
