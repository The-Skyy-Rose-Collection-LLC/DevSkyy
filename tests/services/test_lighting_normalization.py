# tests/services/test_lighting_normalization.py
"""Unit tests for LightingNormalizationService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from services.ml.enhancement.lighting_normalization import (
    MAX_COLOR_DELTA_E,
    ColorPreservationError,
    LightingIntensity,
    LightingNormalizationError,
    LightingNormalizationService,
    LightingResult,
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
def service(mock_replicate_client: MagicMock) -> LightingNormalizationService:
    """Create service with mock client."""
    return LightingNormalizationService(replicate_client=mock_replicate_client)


@pytest.fixture
def red_image() -> Image.Image:
    """Create a solid red test image."""
    return Image.new("RGB", (100, 100), color=(255, 0, 0))


# =============================================================================
# Model Tests
# =============================================================================


class TestLightingIntensity:
    """Test LightingIntensity enum."""

    def test_subtle_value(self) -> None:
        """LightingIntensity.SUBTLE should have correct value."""
        assert LightingIntensity.SUBTLE.value == "subtle"

    def test_moderate_value(self) -> None:
        """LightingIntensity.MODERATE should have correct value."""
        assert LightingIntensity.MODERATE.value == "moderate"

    def test_strong_value(self) -> None:
        """LightingIntensity.STRONG should have correct value."""
        assert LightingIntensity.STRONG.value == "strong"


class TestLightingResult:
    """Test LightingResult model."""

    def test_is_valid_when_preserved(self) -> None:
        """is_valid should return True when colors preserved."""
        result = LightingResult(
            original_url="https://example.com/original.jpg",
            result_url="https://example.com/result.jpg",
            intensity=LightingIntensity.MODERATE,
            model_used="test-model",
            color_delta_e=1.5,
            color_preserved=True,
            processing_time_ms=100,
            correlation_id="test-123",
        )
        assert result.is_valid is True

    def test_is_valid_false_when_not_preserved(self) -> None:
        """is_valid should return False when colors not preserved."""
        result = LightingResult(
            original_url="https://example.com/original.jpg",
            result_url="https://example.com/result.jpg",
            intensity=LightingIntensity.MODERATE,
            model_used="test-model",
            color_delta_e=5.0,
            color_preserved=False,
            processing_time_ms=100,
            correlation_id="test-123",
        )
        assert result.is_valid is False


class TestLightingNormalizationError:
    """Test LightingNormalizationError class."""

    def test_error_with_context(self) -> None:
        """Error should include context fields."""
        error = LightingNormalizationError(
            "Test error",
            image_url="https://example.com/image.jpg",
            model="test-model",
            correlation_id="corr-123",
        )
        assert error.context["image_url"] == "https://example.com/image.jpg"
        assert error.context["model"] == "test-model"

    def test_error_is_retryable(self) -> None:
        """LightingNormalizationError should be retryable."""
        error = LightingNormalizationError("Test error")
        assert error.retryable is True


class TestColorPreservationError:
    """Test ColorPreservationError class."""

    def test_error_includes_delta_e(self) -> None:
        """Error should include Delta-E information."""
        error = ColorPreservationError(
            "Color deviation detected",
            delta_e=5.5,
            threshold=2.0,
        )
        assert error.context["delta_e"] == 5.5
        assert error.context["threshold"] == 2.0

    def test_error_not_retryable(self) -> None:
        """ColorPreservationError should not be retryable."""
        error = ColorPreservationError("Test", delta_e=3.0)
        assert error.retryable is False


# =============================================================================
# Service Tests
# =============================================================================


class TestServiceInit:
    """Test service initialization."""

    def test_init_with_client(self, mock_replicate_client: MagicMock) -> None:
        """Service should accept pre-configured client."""
        service = LightingNormalizationService(replicate_client=mock_replicate_client)
        assert service._client is mock_replicate_client
        assert service._owns_client is False

    def test_init_without_client(self) -> None:
        """Service should create client when none provided."""
        service = LightingNormalizationService()
        assert service._client is None
        assert service._owns_client is True

    def test_init_custom_max_delta_e(self) -> None:
        """Service should accept custom max Delta-E."""
        service = LightingNormalizationService(max_delta_e=1.0)
        assert service._max_delta_e == 1.0


class TestColorConversion:
    """Test color conversion methods."""

    def test_rgb_to_lab_white(self, service: LightingNormalizationService) -> None:
        """White should convert to high L value."""
        L, a, b = service._rgb_to_lab((255, 255, 255))
        assert L > 99

    def test_rgb_to_lab_black(self, service: LightingNormalizationService) -> None:
        """Black should convert to low L value."""
        L, a, b = service._rgb_to_lab((0, 0, 0))
        assert L < 1

    def test_delta_e_identical_colors(self, service: LightingNormalizationService) -> None:
        """Identical colors should have Delta-E of 0."""
        lab = (50.0, 10.0, -20.0)
        delta_e = service._compute_delta_e(lab, lab)
        assert delta_e == 0.0


class TestIntensityParams:
    """Test intensity parameter generation."""

    def test_subtle_params(self, service: LightingNormalizationService) -> None:
        """Subtle intensity should use v1.3."""
        params = service._get_intensity_params(LightingIntensity.SUBTLE)
        assert params["version"] == "v1.3"
        assert params["upscale"] == 1

    def test_moderate_params(self, service: LightingNormalizationService) -> None:
        """Moderate intensity should use v1.4."""
        params = service._get_intensity_params(LightingIntensity.MODERATE)
        assert params["version"] == "v1.4"
        assert params["upscale"] == 1

    def test_strong_params(self, service: LightingNormalizationService) -> None:
        """Strong intensity should upscale 2x."""
        params = service._get_intensity_params(LightingIntensity.STRONG)
        assert params["upscale"] == 2


class TestNormalizeLighting:
    """Test normalize_lighting method."""

    @pytest.mark.asyncio
    async def test_normalize_success(
        self,
        service: LightingNormalizationService,
        mock_replicate_client: MagicMock,
        red_image: Image.Image,
    ) -> None:
        """Should successfully normalize lighting."""
        mock_prediction = MagicMock()
        mock_prediction.succeeded = True
        mock_prediction.output = "https://example.com/result.jpg"
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_prediction)

        with patch.object(service, "_download_image", new_callable=AsyncMock) as mock_download:
            mock_download.return_value = red_image

            result = await service.normalize_lighting(
                "https://example.com/product.jpg",
                correlation_id="test-corr-123",
            )

        assert result.result_url == "https://example.com/result.jpg"
        assert result.intensity == LightingIntensity.MODERATE

    @pytest.mark.asyncio
    async def test_normalize_validates_colors(
        self,
        service: LightingNormalizationService,
        mock_replicate_client: MagicMock,
        red_image: Image.Image,
    ) -> None:
        """Should validate color preservation."""
        mock_prediction = MagicMock()
        mock_prediction.succeeded = True
        mock_prediction.output = "https://example.com/result.jpg"
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_prediction)

        with patch.object(service, "_download_image", new_callable=AsyncMock) as mock_download:
            # Return same image for both original and result
            mock_download.return_value = red_image

            result = await service.normalize_lighting(
                "https://example.com/product.jpg",
                validate_colors=True,
            )

        assert result.color_preserved is True
        assert result.color_delta_e < MAX_COLOR_DELTA_E

    @pytest.mark.asyncio
    async def test_normalize_skip_validation(
        self,
        service: LightingNormalizationService,
        mock_replicate_client: MagicMock,
    ) -> None:
        """Should skip color validation when disabled."""
        mock_prediction = MagicMock()
        mock_prediction.succeeded = True
        mock_prediction.output = "https://example.com/result.jpg"
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_prediction)

        result = await service.normalize_lighting(
            "https://example.com/product.jpg",
            validate_colors=False,
        )

        assert result.color_delta_e == 0.0
        assert result.color_preserved is True

    @pytest.mark.asyncio
    async def test_normalize_all_models_fail(
        self,
        service: LightingNormalizationService,
        mock_replicate_client: MagicMock,
    ) -> None:
        """Should raise error when all models fail."""
        mock_failed = MagicMock()
        mock_failed.succeeded = False
        mock_failed.output = None
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_failed)

        with pytest.raises(LightingNormalizationError) as exc_info:
            await service.normalize_lighting(
                "https://example.com/product.jpg",
                validate_colors=False,
            )

        assert "All lighting normalization models failed" in str(exc_info.value)


class TestNormalizeBatch:
    """Test batch processing."""

    @pytest.mark.asyncio
    async def test_batch_success(
        self,
        service: LightingNormalizationService,
        mock_replicate_client: MagicMock,
    ) -> None:
        """Should process multiple images in batch."""
        mock_prediction = MagicMock()
        mock_prediction.succeeded = True
        mock_prediction.output = "https://example.com/result.jpg"
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_prediction)

        results = await service.normalize_lighting_batch(
            [
                "https://example.com/product1.jpg",
                "https://example.com/product2.jpg",
            ],
            validate_colors=False,
        )

        assert len(results) == 2
        assert all(isinstance(r, LightingResult) for r in results)


class TestConstants:
    """Test module constants."""

    def test_max_delta_e_reasonable(self) -> None:
        """Max Delta-E should be reasonable."""
        assert 1.0 <= MAX_COLOR_DELTA_E <= 5.0
