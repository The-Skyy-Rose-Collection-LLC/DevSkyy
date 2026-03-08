# tests/services/test_background_removal.py
"""Unit tests for BackgroundRemovalService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.ml.enhancement.background_removal import (
    DEFAULT_BACKGROUND_REMOVAL_MODEL,
    FALLBACK_MODELS,
    BackgroundRemovalError,
    BackgroundRemovalResult,
    BackgroundRemovalService,
    BackgroundType,
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
def service(mock_replicate_client: MagicMock) -> BackgroundRemovalService:
    """Create service with mock client."""
    return BackgroundRemovalService(replicate_client=mock_replicate_client)


# =============================================================================
# Model Tests
# =============================================================================


class TestBackgroundType:
    """Test BackgroundType enum."""

    def test_transparent_value(self) -> None:
        """BackgroundType.TRANSPARENT should have correct value."""
        assert BackgroundType.TRANSPARENT.value == "transparent"

    def test_solid_color_value(self) -> None:
        """BackgroundType.SOLID_COLOR should have correct value."""
        assert BackgroundType.SOLID_COLOR.value == "solid_color"

    def test_custom_image_value(self) -> None:
        """BackgroundType.CUSTOM_IMAGE should have correct value."""
        assert BackgroundType.CUSTOM_IMAGE.value == "custom_image"


class TestBackgroundRemovalResult:
    """Test BackgroundRemovalResult model."""

    def test_is_transparent_true(self) -> None:
        """is_transparent should return True for transparent background."""
        result = BackgroundRemovalResult(
            original_url="https://example.com/original.jpg",
            result_url="https://example.com/result.png",
            background_type=BackgroundType.TRANSPARENT,
            model_used="test-model",
            product_hash="abc123",
            processing_time_ms=100,
            correlation_id="test-123",
        )
        assert result.is_transparent is True

    def test_is_transparent_false(self) -> None:
        """is_transparent should return False for non-transparent background."""
        result = BackgroundRemovalResult(
            original_url="https://example.com/original.jpg",
            result_url="https://example.com/result.jpg",
            background_type=BackgroundType.SOLID_COLOR,
            background_value="#FFFFFF",
            model_used="test-model",
            product_hash="abc123",
            processing_time_ms=100,
            correlation_id="test-123",
        )
        assert result.is_transparent is False


class TestBackgroundRemovalError:
    """Test BackgroundRemovalError class."""

    def test_error_with_all_context(self) -> None:
        """Error should include all context fields."""
        error = BackgroundRemovalError(
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
        error = BackgroundRemovalError("Wrapper error", cause=cause)
        assert error.cause is cause


# =============================================================================
# Service Tests
# =============================================================================


class TestBackgroundRemovalServiceInit:
    """Test service initialization."""

    def test_init_with_client(self, mock_replicate_client: MagicMock) -> None:
        """Service should accept pre-configured client."""
        service = BackgroundRemovalService(replicate_client=mock_replicate_client)
        assert service._client is mock_replicate_client
        assert service._owns_client is False

    def test_init_without_client(self) -> None:
        """Service should create client when none provided."""
        service = BackgroundRemovalService()
        assert service._client is None
        assert service._owns_client is True


class TestBackgroundRemovalServiceContextManager:
    """Test async context manager functionality."""

    @pytest.mark.asyncio
    async def test_context_manager_enter(self, mock_replicate_client: MagicMock) -> None:
        """Context manager should return service on enter."""
        service = BackgroundRemovalService(replicate_client=mock_replicate_client)
        async with service as ctx:
            assert ctx is service

    @pytest.mark.asyncio
    async def test_context_manager_closes_owned_client(self) -> None:
        """Context manager should close owned client on exit."""
        mock_client = MagicMock()
        mock_client.connect = AsyncMock()
        mock_client.close = AsyncMock()

        service = BackgroundRemovalService()
        service._client = mock_client
        service._owns_client = True

        await service.close()
        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_does_not_close_external_client(
        self, mock_replicate_client: MagicMock
    ) -> None:
        """Context manager should not close externally provided client."""
        service = BackgroundRemovalService(replicate_client=mock_replicate_client)
        await service.close()
        mock_replicate_client.close.assert_not_called()


class TestRemoveBackground:
    """Test remove_background method."""

    @pytest.mark.asyncio
    async def test_remove_background_success(
        self, service: BackgroundRemovalService, mock_replicate_client: MagicMock
    ) -> None:
        """Should successfully remove background."""
        # Mock prediction result
        mock_prediction = MagicMock()
        mock_prediction.succeeded = True
        mock_prediction.output = "https://example.com/result.png"
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_prediction)

        # Mock image download
        with patch.object(
            service, "_download_image_bytes", new_callable=AsyncMock
        ) as mock_download:
            mock_download.return_value = b"fake-image-data"

            result = await service.remove_background(
                "https://example.com/product.jpg",
                correlation_id="test-corr-123",
            )

        assert result.result_url == "https://example.com/result.png"
        assert result.background_type == BackgroundType.TRANSPARENT
        assert result.model_used == DEFAULT_BACKGROUND_REMOVAL_MODEL

    @pytest.mark.asyncio
    async def test_remove_background_with_solid_color(
        self, service: BackgroundRemovalService, mock_replicate_client: MagicMock
    ) -> None:
        """Should handle solid color background request."""
        mock_prediction = MagicMock()
        mock_prediction.succeeded = True
        mock_prediction.output = "https://example.com/result.png"
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_prediction)

        with patch.object(
            service, "_download_image_bytes", new_callable=AsyncMock
        ) as mock_download:
            mock_download.return_value = b"fake-image-data"

            result = await service.remove_background(
                "https://example.com/product.jpg",
                background_type=BackgroundType.SOLID_COLOR,
                background_color="#FF0000",
            )

        assert result.background_type == BackgroundType.SOLID_COLOR
        assert result.background_value == "#FF0000"

    @pytest.mark.asyncio
    async def test_remove_background_fallback_on_primary_failure(
        self, service: BackgroundRemovalService, mock_replicate_client: MagicMock
    ) -> None:
        """Should fallback to secondary model when primary fails."""
        # First call fails, second succeeds
        mock_failed = MagicMock()
        mock_failed.succeeded = False
        mock_failed.output = None

        mock_success = MagicMock()
        mock_success.succeeded = True
        mock_success.output = "https://example.com/fallback-result.png"

        mock_replicate_client.run_prediction = AsyncMock(side_effect=[mock_failed, mock_success])

        with patch.object(
            service, "_download_image_bytes", new_callable=AsyncMock
        ) as mock_download:
            mock_download.return_value = b"fake-image-data"

            result = await service.remove_background(
                "https://example.com/product.jpg",
            )

        assert result.result_url == "https://example.com/fallback-result.png"
        assert result.model_used == FALLBACK_MODELS[0]

    @pytest.mark.asyncio
    async def test_remove_background_all_models_fail(
        self, service: BackgroundRemovalService, mock_replicate_client: MagicMock
    ) -> None:
        """Should raise error when all models fail."""
        mock_failed = MagicMock()
        mock_failed.succeeded = False
        mock_failed.output = None

        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_failed)

        with patch.object(
            service, "_download_image_bytes", new_callable=AsyncMock
        ) as mock_download:
            mock_download.return_value = b"fake-image-data"

            with pytest.raises(BackgroundRemovalError) as exc_info:
                await service.remove_background("https://example.com/product.jpg")

        assert "All background removal models failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_remove_background_download_failure(
        self, service: BackgroundRemovalService, mock_replicate_client: MagicMock
    ) -> None:
        """Should handle image download failure."""
        with patch.object(
            service, "_download_image_bytes", new_callable=AsyncMock
        ) as mock_download:
            mock_download.side_effect = BackgroundRemovalError("Download failed")

            with pytest.raises(BackgroundRemovalError) as exc_info:
                await service.remove_background("https://example.com/product.jpg")

        assert "download" in str(exc_info.value).lower()


class TestRemoveBackgroundBatch:
    """Test batch processing."""

    @pytest.mark.asyncio
    async def test_batch_success(
        self, service: BackgroundRemovalService, mock_replicate_client: MagicMock
    ) -> None:
        """Should process multiple images in batch."""
        mock_prediction = MagicMock()
        mock_prediction.succeeded = True
        mock_prediction.output = "https://example.com/result.png"
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_prediction)

        with patch.object(
            service, "_download_image_bytes", new_callable=AsyncMock
        ) as mock_download:
            mock_download.return_value = b"fake-image-data"

            results = await service.remove_background_batch(
                [
                    "https://example.com/product1.jpg",
                    "https://example.com/product2.jpg",
                ]
            )

        assert len(results) == 2
        assert all(isinstance(r, BackgroundRemovalResult) for r in results)

    @pytest.mark.asyncio
    async def test_batch_partial_failure(
        self, service: BackgroundRemovalService, mock_replicate_client: MagicMock
    ) -> None:
        """Should return errors for failed items in batch."""
        # First succeeds, second fails
        mock_success = MagicMock()
        mock_success.succeeded = True
        mock_success.output = "https://example.com/result.png"

        mock_failed = MagicMock()
        mock_failed.succeeded = False
        mock_failed.output = None

        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Primary model: alternate success/failure, fallbacks all fail
            if call_count == 1:
                return mock_success
            return mock_failed

        mock_replicate_client.run_prediction = AsyncMock(side_effect=side_effect)

        with patch.object(
            service, "_download_image_bytes", new_callable=AsyncMock
        ) as mock_download:
            mock_download.return_value = b"fake-image-data"

            results = await service.remove_background_batch(
                [
                    "https://example.com/product1.jpg",
                    "https://example.com/product2.jpg",
                ]
            )

        assert len(results) == 2
        assert isinstance(results[0], BackgroundRemovalResult)
        assert isinstance(results[1], BackgroundRemovalError)


class TestComputeImageHash:
    """Test image hash computation."""

    def test_compute_hash(self, service: BackgroundRemovalService) -> None:
        """Should compute consistent hash for same data."""
        data = b"test image data"
        hash1 = service._compute_image_hash(data)
        hash2 = service._compute_image_hash(data)
        assert hash1 == hash2
        assert len(hash1) == 16  # First 16 chars of SHA-256 hex

    def test_different_data_different_hash(self, service: BackgroundRemovalService) -> None:
        """Should compute different hash for different data."""
        hash1 = service._compute_image_hash(b"data1")
        hash2 = service._compute_image_hash(b"data2")
        assert hash1 != hash2


class TestConstants:
    """Test module constants."""

    def test_default_model_format(self) -> None:
        """Default model should follow Replicate format."""
        assert "/" in DEFAULT_BACKGROUND_REMOVAL_MODEL
        assert ":" in DEFAULT_BACKGROUND_REMOVAL_MODEL

    def test_fallback_models_exist(self) -> None:
        """Fallback models should be defined."""
        assert len(FALLBACK_MODELS) >= 1
        for model in FALLBACK_MODELS:
            assert "/" in model
            assert ":" in model
