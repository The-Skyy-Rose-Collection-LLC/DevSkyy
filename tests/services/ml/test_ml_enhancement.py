# tests/services/ml/test_ml_enhancement.py
"""
Comprehensive Unit Tests for ML Enhancement Modules.

Tests the following modules with >90% coverage target:
- authenticity_validator.py: Image validation and authenticity checking
- background_removal.py: Background removal operations
- format_optimizer.py: Format optimization (WebP, JPEG quality)
- lighting_normalization.py: Lighting normalization
- upscaling.py: Image upscaling

Author: DevSkyy Platform Team
"""

from __future__ import annotations

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from errors.production_errors import DevSkyErrorCode, DevSkyErrorSeverity
from services.ml.enhancement.authenticity_validator import (
    AuthenticityReport,
    AuthenticityValidationError,
    AuthenticityValidator,
    ValidationResult,
    ValidationStatus,
)
from services.ml.enhancement.background_removal import (
    BackgroundRemovalError,
    BackgroundRemovalResult,
    BackgroundRemovalService,
    BackgroundType,
)
from services.ml.enhancement.format_optimizer import (
    FormatOptimizationError,
    FormatOptimizationResult,
    FormatOptimizer,
    ImageVariant,
    OutputFormat,
)
from services.ml.enhancement.lighting_normalization import (
    ColorPreservationError,
    LightingIntensity,
    LightingNormalizationError,
    LightingNormalizationService,
    LightingResult,
)
from services.ml.enhancement.upscaling import (
    UpscaleResult,
    UpscalingError,
    UpscalingService,
)
from services.ml.replicate_client import (
    ReplicateClient,
    ReplicateConfig,
    ReplicatePrediction,
    ReplicatePredictionStatus,
)

# =============================================================================
# Module Imports
# =============================================================================


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def test_image_rgb() -> Image.Image:
    """Create a test RGB image."""
    img = Image.new("RGB", (100, 100), color=(128, 64, 192))
    # Add some variation
    pixels = img.load()
    for i in range(100):
        for j in range(100):
            pixels[i, j] = (
                (128 + i) % 256,
                (64 + j) % 256,
                (192 + i + j) % 256,
            )
    return img


@pytest.fixture
def test_image_rgba() -> Image.Image:
    """Create a test RGBA image with transparency."""
    img = Image.new("RGBA", (100, 100), color=(128, 64, 192, 255))
    return img


@pytest.fixture
def test_image_bytes(test_image_rgb) -> bytes:
    """Create test image bytes."""
    buffer = io.BytesIO()
    test_image_rgb.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def mock_replicate_config() -> ReplicateConfig:
    """Create mock Replicate config."""
    return ReplicateConfig(api_token="test-token-12345")


@pytest.fixture
def mock_replicate_client(mock_replicate_config) -> MagicMock:
    """Create mock Replicate client."""
    client = MagicMock(spec=ReplicateClient)
    client.config = mock_replicate_config
    client._generate_correlation_id = MagicMock(return_value="test-correlation-id")
    return client


@pytest.fixture
def mock_r2_client() -> MagicMock:
    """Create mock R2 client."""
    from services.storage.r2_client import R2UploadResult

    client = MagicMock()
    client.upload_bytes = MagicMock(
        return_value=R2UploadResult(
            key="test/image.webp",
            bucket="skyyrose-assets",
            etag="abc123",
            size=1024,
            url="https://cdn.example.com/test/image.webp",
            cdn_url="https://cdn.example.com/test/image.webp",
            content_hash="abc123def456",
            correlation_id="test-correlation-id",
        )
    )
    return client


@pytest.fixture
def mock_httpx_response(test_image_bytes) -> MagicMock:
    """Create mock httpx response with image content."""
    response = MagicMock()
    response.status_code = 200
    response.content = test_image_bytes
    response.headers = {"content-type": "image/jpeg"}
    return response


@pytest.fixture
def mock_prediction_success() -> ReplicatePrediction:
    """Create mock successful prediction."""
    return ReplicatePrediction(
        id="pred-123",
        version="abc123",
        status=ReplicatePredictionStatus.SUCCEEDED,
        output="https://replicate.delivery/output.png",
    )


@pytest.fixture
def mock_prediction_failed() -> ReplicatePrediction:
    """Create mock failed prediction."""
    return ReplicatePrediction(
        id="pred-456",
        version="abc123",
        status=ReplicatePredictionStatus.FAILED,
        error="Model execution failed",
    )


# =============================================================================
# AuthenticityValidator Tests
# =============================================================================


class TestValidationStatus:
    """Tests for ValidationStatus enum."""

    def test_status_values(self) -> None:
        """Test validation status values."""
        assert ValidationStatus.PASSED.value == "passed"
        assert ValidationStatus.FAILED.value == "failed"
        assert ValidationStatus.NEEDS_REVIEW.value == "needs_review"

    def test_status_comparisons(self) -> None:
        """Test status comparisons work correctly."""
        assert ValidationStatus.PASSED != ValidationStatus.FAILED
        assert ValidationStatus.PASSED == ValidationStatus.PASSED


class TestValidationResult:
    """Tests for ValidationResult model."""

    def test_validation_result_creation(self) -> None:
        """Test creating a validation result."""
        result = ValidationResult(
            check_name="perceptual_hash",
            passed=True,
            score=0.98,
            threshold=0.95,
            details="Perceptual similarity: 98%",
        )
        assert result.check_name == "perceptual_hash"
        assert result.passed is True
        assert result.score == 0.98
        assert result.threshold == 0.95
        assert result.visual_diff_url is None

    def test_validation_result_with_visual_diff(self) -> None:
        """Test validation result with visual diff URL."""
        result = ValidationResult(
            check_name="color_accuracy",
            passed=False,
            score=3.5,
            threshold=2.0,
            details="Delta-E exceeds threshold",
            visual_diff_url="https://example.com/diff.png",
        )
        assert result.visual_diff_url == "https://example.com/diff.png"


class TestAuthenticityReport:
    """Tests for AuthenticityReport model."""

    def test_report_is_approved_when_passed(self) -> None:
        """Test is_approved returns True when status is PASSED."""
        report = AuthenticityReport(
            original_url="https://example.com/original.jpg",
            enhanced_url="https://example.com/enhanced.jpg",
            status=ValidationStatus.PASSED,
            overall_similarity=0.98,
            color_accuracy_delta_e=1.5,
            validation_results=[],
            requires_human_review=False,
            review_reasons=[],
            processing_time_ms=500,
            correlation_id="test-123",
        )
        assert report.is_approved is True

    def test_report_not_approved_when_needs_review(self) -> None:
        """Test is_approved returns False when requires review."""
        report = AuthenticityReport(
            original_url="https://example.com/original.jpg",
            enhanced_url="https://example.com/enhanced.jpg",
            status=ValidationStatus.NEEDS_REVIEW,
            overall_similarity=0.85,
            color_accuracy_delta_e=3.0,
            validation_results=[],
            requires_human_review=True,
            review_reasons=["Color deviation detected"],
            processing_time_ms=500,
            correlation_id="test-123",
        )
        assert report.is_approved is False

    def test_report_not_approved_when_failed(self) -> None:
        """Test is_approved returns False when status is FAILED."""
        report = AuthenticityReport(
            original_url="https://example.com/original.jpg",
            enhanced_url="https://example.com/enhanced.jpg",
            status=ValidationStatus.FAILED,
            overall_similarity=0.5,
            color_accuracy_delta_e=10.0,
            validation_results=[],
            requires_human_review=True,
            review_reasons=["Images are too different"],
            processing_time_ms=500,
            correlation_id="test-123",
        )
        assert report.is_approved is False


class TestAuthenticityValidationError:
    """Tests for AuthenticityValidationError."""

    def test_error_creation(self) -> None:
        """Test creating validation error."""
        error = AuthenticityValidationError(
            "Validation failed",
            original_url="https://example.com/orig.jpg",
            enhanced_url="https://example.com/enh.jpg",
            correlation_id="test-123",
        )
        assert error.code == DevSkyErrorCode.MODEL_FIDELITY_BELOW_THRESHOLD
        assert error.severity == DevSkyErrorSeverity.WARNING
        assert error.context["original_url"] == "https://example.com/orig.jpg"
        assert error.context["enhanced_url"] == "https://example.com/enh.jpg"
        assert error.retryable is False

    def test_error_with_cause(self) -> None:
        """Test error with underlying cause."""
        cause = ValueError("Download failed")
        error = AuthenticityValidationError(
            "Failed to validate",
            cause=cause,
        )
        assert error.cause == cause


class TestAuthenticityValidator:
    """Tests for AuthenticityValidator service."""

    def test_init_default_thresholds(self) -> None:
        """Test validator initializes with default thresholds."""
        validator = AuthenticityValidator()
        assert validator._similarity_threshold == 0.95
        assert validator._max_delta_e == 2.0

    def test_init_custom_thresholds(self) -> None:
        """Test validator with custom thresholds."""
        validator = AuthenticityValidator(
            similarity_threshold=0.90,
            max_delta_e=3.0,
        )
        assert validator._similarity_threshold == 0.90
        assert validator._max_delta_e == 3.0

    def test_compute_phash(self, test_image_rgb) -> None:
        """Test perceptual hash computation."""
        validator = AuthenticityValidator()
        phash = validator._compute_phash(test_image_rgb)

        assert isinstance(phash, str)
        assert len(phash) == 64  # 256 bits / 4 = 64 hex chars

    def test_compute_phash_identical_images(self, test_image_rgb) -> None:
        """Test identical images have identical hashes."""
        validator = AuthenticityValidator()
        hash1 = validator._compute_phash(test_image_rgb)
        hash2 = validator._compute_phash(test_image_rgb.copy())
        assert hash1 == hash2

    def test_compute_hash_similarity_identical(self) -> None:
        """Test similarity of identical hashes is 1.0."""
        validator = AuthenticityValidator()
        hash1 = "abcdef1234567890" * 4
        similarity = validator._compute_hash_similarity(hash1, hash1)
        assert similarity == 1.0

    def test_compute_hash_similarity_different_lengths(self) -> None:
        """Test similarity returns 0 for different length hashes."""
        validator = AuthenticityValidator()
        similarity = validator._compute_hash_similarity("abc", "abcdef")
        assert similarity == 0.0

    def test_compute_hash_similarity_partial_match(self) -> None:
        """Test similarity for partially matching hashes."""
        validator = AuthenticityValidator()
        # Half the bits should match
        hash1 = "ffffffffffffffff" * 4  # All 1s
        hash2 = "0000000000000000" * 4  # All 0s
        similarity = validator._compute_hash_similarity(hash1, hash2)
        assert similarity == 0.0

    def test_rgb_to_lab_conversion(self) -> None:
        """Test RGB to LAB color conversion."""
        validator = AuthenticityValidator()

        # Test white (255, 255, 255)
        lab_white = validator._rgb_to_lab((255, 255, 255))
        assert lab_white[0] > 99  # L should be ~100 for white

        # Test black (0, 0, 0)
        lab_black = validator._rgb_to_lab((0, 0, 0))
        assert lab_black[0] < 1  # L should be ~0 for black

    def test_compute_delta_e_identical_colors(self) -> None:
        """Test Delta-E is 0 for identical colors."""
        validator = AuthenticityValidator()
        lab = (50.0, 25.0, -10.0)
        delta_e = validator._compute_delta_e(lab, lab)
        assert delta_e == 0.0

    def test_compute_delta_e_different_colors(self) -> None:
        """Test Delta-E for different colors."""
        validator = AuthenticityValidator()
        lab1 = (50.0, 0.0, 0.0)
        lab2 = (60.0, 0.0, 0.0)
        delta_e = validator._compute_delta_e(lab1, lab2)
        assert delta_e == pytest.approx(10.0)

    def test_compute_average_delta_e_identical(self, test_image_rgb) -> None:
        """Test average Delta-E for identical images is near 0."""
        validator = AuthenticityValidator()
        delta_e = validator._compute_average_delta_e(test_image_rgb, test_image_rgb.copy())
        assert delta_e < 0.1

    def test_compute_average_delta_e_different_sizes(self, test_image_rgb) -> None:
        """Test average Delta-E resizes images if needed."""
        validator = AuthenticityValidator()
        img2 = test_image_rgb.resize((50, 50))
        # Should not raise - will resize internally
        delta_e = validator._compute_average_delta_e(test_image_rgb, img2)
        assert isinstance(delta_e, float)

    def test_compute_average_delta_e_empty_image(self) -> None:
        """Test average Delta-E returns 0 for empty images."""
        validator = AuthenticityValidator()
        img1 = Image.new("RGB", (0, 0))
        img2 = Image.new("RGB", (0, 0))
        delta_e = validator._compute_average_delta_e(img1, img2)
        assert delta_e == 0.0

    def test_compute_edge_similarity_identical(self, test_image_rgb) -> None:
        """Test edge similarity for identical images."""
        validator = AuthenticityValidator()
        similarity = validator._compute_edge_similarity(test_image_rgb, test_image_rgb.copy())
        assert similarity >= 0.99

    def test_compute_edge_similarity_different_sizes(self, test_image_rgb) -> None:
        """Test edge similarity handles different sizes."""
        validator = AuthenticityValidator()
        img2 = test_image_rgb.resize((50, 50))
        similarity = validator._compute_edge_similarity(test_image_rgb, img2)
        assert 0.0 <= similarity <= 1.0

    @pytest.mark.asyncio
    async def test_download_image_success(self, test_image_bytes, test_image_rgb) -> None:
        """Test successful image download."""
        validator = AuthenticityValidator()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_image_bytes

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            img = await validator._download_image("https://example.com/image.jpg", "test-123")

            assert isinstance(img, Image.Image)

    @pytest.mark.asyncio
    async def test_download_image_failure(self) -> None:
        """Test image download failure raises error."""
        validator = AuthenticityValidator()

        mock_response = AsyncMock()
        mock_response.status_code = 404

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response

        with patch(
            "services.ml.enhancement.authenticity_validator.httpx.AsyncClient"
        ) as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance
            MockAsyncClient.return_value.__aexit__.return_value = None

            with pytest.raises(AuthenticityValidationError) as exc_info:
                await validator._download_image("https://example.com/notfound.jpg", "test-123")

            assert "HTTP 404" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_success(self, test_image_bytes) -> None:
        """Test successful validation with identical images."""
        validator = AuthenticityValidator()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_image_bytes

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            report = await validator.validate(
                original_url="https://example.com/original.jpg",
                enhanced_url="https://example.com/enhanced.jpg",
                correlation_id="test-123",
            )

            assert report.status == ValidationStatus.PASSED
            assert len(report.validation_results) == 3
            assert report.requires_human_review is False
            assert report.correlation_id == "test-123"

    @pytest.mark.asyncio
    async def test_validate_download_failure(self) -> None:
        """Test validation handles download failure."""
        validator = AuthenticityValidator()

        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = Exception("Network error")

        with patch(
            "services.ml.enhancement.authenticity_validator.httpx.AsyncClient"
        ) as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance
            MockAsyncClient.return_value.__aexit__.return_value = None

            with pytest.raises(AuthenticityValidationError) as exc_info:
                await validator.validate(
                    original_url="https://example.com/original.jpg",
                    enhanced_url="https://example.com/enhanced.jpg",
                )

            assert "Failed to download images" in str(exc_info.value)


# =============================================================================
# BackgroundRemovalService Tests
# =============================================================================


class TestBackgroundType:
    """Tests for BackgroundType enum."""

    def test_background_type_values(self) -> None:
        """Test background type values."""
        assert BackgroundType.TRANSPARENT.value == "transparent"
        assert BackgroundType.SOLID_COLOR.value == "solid_color"
        assert BackgroundType.CUSTOM_IMAGE.value == "custom_image"


class TestBackgroundRemovalResult:
    """Tests for BackgroundRemovalResult model."""

    def test_result_creation(self) -> None:
        """Test creating a background removal result."""
        result = BackgroundRemovalResult(
            original_url="https://example.com/input.jpg",
            result_url="https://example.com/output.png",
            background_type=BackgroundType.TRANSPARENT,
            model_used="test-model",
            product_hash="abc123",
            processing_time_ms=1500,
            correlation_id="test-123",
        )
        assert result.is_transparent is True
        assert result.background_value is None

    def test_result_solid_color(self) -> None:
        """Test result with solid color background."""
        result = BackgroundRemovalResult(
            original_url="https://example.com/input.jpg",
            result_url="https://example.com/output.png",
            background_type=BackgroundType.SOLID_COLOR,
            background_value="#FFFFFF",
            model_used="test-model",
            product_hash="abc123",
            processing_time_ms=1500,
            correlation_id="test-123",
        )
        assert result.is_transparent is False
        assert result.background_value == "#FFFFFF"


class TestBackgroundRemovalError:
    """Tests for BackgroundRemovalError."""

    def test_error_creation(self) -> None:
        """Test creating background removal error."""
        error = BackgroundRemovalError(
            "Removal failed",
            image_url="https://example.com/image.jpg",
            model="test-model",
            correlation_id="test-123",
        )
        assert error.code == DevSkyErrorCode.IMAGE_PROCESSING_FAILED
        assert error.context["image_url"] == "https://example.com/image.jpg"
        assert error.context["model"] == "test-model"
        assert error.retryable is True


class TestBackgroundRemovalService:
    """Tests for BackgroundRemovalService."""

    def test_init_with_client(self, mock_replicate_client) -> None:
        """Test initialization with provided client."""
        service = BackgroundRemovalService(replicate_client=mock_replicate_client)
        assert service._client == mock_replicate_client
        assert service._owns_client is False

    def test_init_without_client(self) -> None:
        """Test initialization without client (creates own)."""
        service = BackgroundRemovalService()
        assert service._client is None
        assert service._owns_client is True

    def test_compute_image_hash(self) -> None:
        """Test image hash computation."""
        service = BackgroundRemovalService()
        data = b"test image data"
        hash_result = service._compute_image_hash(data)
        assert len(hash_result) == 16  # SHA-256 truncated to 16 chars
        assert all(c in "0123456789abcdef" for c in hash_result)

    @pytest.mark.asyncio
    async def test_download_image_bytes_success(self, test_image_bytes) -> None:
        """Test successful image bytes download."""
        service = BackgroundRemovalService()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_image_bytes

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            result = await service._download_image_bytes(
                "https://example.com/image.jpg", "test-123"
            )

            assert result == test_image_bytes

    @pytest.mark.asyncio
    async def test_download_image_bytes_failure(self) -> None:
        """Test image bytes download failure."""
        service = BackgroundRemovalService()

        mock_response = AsyncMock()
        mock_response.status_code = 500

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response

        with patch(
            "services.ml.enhancement.background_removal.httpx.AsyncClient"
        ) as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance
            MockAsyncClient.return_value.__aexit__.return_value = None

            with pytest.raises(BackgroundRemovalError) as exc_info:
                await service._download_image_bytes("https://example.com/image.jpg", "test-123")

            assert "HTTP 500" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_remove_background_success(
        self, mock_replicate_client, mock_prediction_success, test_image_bytes
    ) -> None:
        """Test successful background removal."""
        mock_replicate_client.connect = AsyncMock()
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_prediction_success)

        service = BackgroundRemovalService(replicate_client=mock_replicate_client)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_image_bytes

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            result = await service.remove_background(
                "https://example.com/product.jpg",
                correlation_id="test-123",
            )

            assert isinstance(result, BackgroundRemovalResult)
            assert result.result_url == mock_prediction_success.output
            assert result.background_type == BackgroundType.TRANSPARENT

    @pytest.mark.asyncio
    async def test_remove_background_with_solid_color(
        self, mock_replicate_client, mock_prediction_success, test_image_bytes
    ) -> None:
        """Test background removal with solid color replacement."""
        mock_replicate_client.connect = AsyncMock()
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_prediction_success)

        service = BackgroundRemovalService(replicate_client=mock_replicate_client)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_image_bytes

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            result = await service.remove_background(
                "https://example.com/product.jpg",
                background_type=BackgroundType.SOLID_COLOR,
                background_color="#B76E79",
            )

            assert result.background_type == BackgroundType.SOLID_COLOR
            assert result.background_value == "#B76E79"

    @pytest.mark.asyncio
    async def test_remove_background_all_models_fail(
        self, mock_replicate_client, test_image_bytes
    ) -> None:
        """Test background removal when all models fail."""
        mock_replicate_client.connect = AsyncMock()
        mock_replicate_client.run_prediction = AsyncMock(side_effect=Exception("Model failed"))

        service = BackgroundRemovalService(replicate_client=mock_replicate_client)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_image_bytes

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            with pytest.raises(BackgroundRemovalError) as exc_info:
                await service.remove_background(
                    "https://example.com/product.jpg",
                )

            assert "All background removal models failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_remove_background_batch(
        self, mock_replicate_client, mock_prediction_success, test_image_bytes
    ) -> None:
        """Test batch background removal."""
        mock_replicate_client.connect = AsyncMock()
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_prediction_success)

        service = BackgroundRemovalService(replicate_client=mock_replicate_client)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_image_bytes

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            urls = [
                "https://example.com/product1.jpg",
                "https://example.com/product2.jpg",
            ]
            results = await service.remove_background_batch(urls)

            assert len(results) == 2
            assert all(
                isinstance(r, (BackgroundRemovalResult, BackgroundRemovalError)) for r in results
            )

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_replicate_client) -> None:
        """Test service as context manager."""
        mock_replicate_client.connect = AsyncMock()
        mock_replicate_client.close = AsyncMock()

        service = BackgroundRemovalService(replicate_client=mock_replicate_client)

        async with service as svc:
            assert svc == service

        mock_replicate_client.close.assert_not_called()  # doesn't own client


# =============================================================================
# FormatOptimizer Tests
# =============================================================================


class TestOutputFormat:
    """Tests for OutputFormat enum."""

    def test_output_format_values(self) -> None:
        """Test output format values."""
        assert OutputFormat.WEBP.value == "webp"
        assert OutputFormat.JPEG.value == "jpeg"
        assert OutputFormat.PNG.value == "png"
        assert OutputFormat.TIFF.value == "tiff"


class TestImageVariant:
    """Tests for ImageVariant model."""

    def test_variant_creation(self) -> None:
        """Test creating an image variant."""
        variant = ImageVariant(
            name="web",
            format=OutputFormat.WEBP,
            width=1920,
            height=1080,
            size_bytes=50000,
            url="https://cdn.example.com/image.webp",
            key="enhanced/SKU-123/image.webp",
            content_type="image/webp",
            quality=85,
        )
        assert variant.name == "web"
        assert variant.format == OutputFormat.WEBP
        assert variant.quality == 85
        assert variant.dpi is None


class TestFormatOptimizationResult:
    """Tests for FormatOptimizationResult model."""

    def test_result_creation(self) -> None:
        """Test creating optimization result."""
        webp_variant = ImageVariant(
            name="web",
            format=OutputFormat.WEBP,
            width=1920,
            height=1080,
            size_bytes=50000,
            url="https://cdn.example.com/image.webp",
            key="enhanced/SKU-123/image.webp",
            content_type="image/webp",
            quality=85,
        )
        result = FormatOptimizationResult(
            original_url="https://example.com/original.jpg",
            original_dimensions=(1920, 1080),
            variants=[webp_variant],
            total_size_bytes=50000,
            processing_time_ms=1000,
            correlation_id="test-123",
        )
        assert result.web_variant == webp_variant
        assert result.print_variant is None

    def test_web_variant_property(self) -> None:
        """Test web_variant property returns correct variant."""
        web = ImageVariant(
            name="web",
            format=OutputFormat.WEBP,
            width=1920,
            height=1080,
            size_bytes=50000,
            url="https://cdn.example.com/web.webp",
            key="enhanced/SKU-123/web.webp",
            content_type="image/webp",
        )
        jpeg = ImageVariant(
            name="fallback",
            format=OutputFormat.JPEG,
            width=1920,
            height=1080,
            size_bytes=60000,
            url="https://cdn.example.com/fallback.jpg",
            key="enhanced/SKU-123/fallback.jpg",
            content_type="image/jpeg",
        )
        result = FormatOptimizationResult(
            original_url="https://example.com/original.jpg",
            original_dimensions=(1920, 1080),
            variants=[web, jpeg],
            total_size_bytes=110000,
            processing_time_ms=1000,
            correlation_id="test-123",
        )
        assert result.web_variant == web

    def test_print_variant_property(self) -> None:
        """Test print_variant property returns TIFF variant."""
        tiff = ImageVariant(
            name="print",
            format=OutputFormat.TIFF,
            width=1920,
            height=1080,
            size_bytes=5000000,
            url="https://cdn.example.com/print.tiff",
            key="enhanced/SKU-123/print.tiff",
            content_type="image/tiff",
            dpi=300,
        )
        result = FormatOptimizationResult(
            original_url="https://example.com/original.jpg",
            original_dimensions=(1920, 1080),
            variants=[tiff],
            total_size_bytes=5000000,
            processing_time_ms=1000,
            correlation_id="test-123",
        )
        assert result.print_variant == tiff


class TestFormatOptimizationError:
    """Tests for FormatOptimizationError."""

    def test_error_creation(self) -> None:
        """Test creating format optimization error."""
        error = FormatOptimizationError(
            "Optimization failed",
            image_url="https://example.com/image.jpg",
            correlation_id="test-123",
        )
        assert error.code == DevSkyErrorCode.IMAGE_PROCESSING_FAILED
        assert error.context["image_url"] == "https://example.com/image.jpg"
        assert error.retryable is True


class TestFormatOptimizer:
    """Tests for FormatOptimizer service."""

    def test_init_with_client(self, mock_r2_client) -> None:
        """Test initialization with provided client."""
        optimizer = FormatOptimizer(r2_client=mock_r2_client)
        assert optimizer._r2_client == mock_r2_client

    def test_resize_image_maintain_aspect(self, test_image_rgb) -> None:
        """Test image resize maintaining aspect ratio."""
        optimizer = FormatOptimizer()
        resized = optimizer._resize_image(test_image_rgb.copy(), (50, 50), maintain_aspect=True)
        # Original is 100x100, so should resize to 50x50
        assert resized.size[0] <= 50
        assert resized.size[1] <= 50

    def test_resize_image_no_aspect(self, test_image_rgb) -> None:
        """Test image resize without maintaining aspect."""
        optimizer = FormatOptimizer()
        resized = optimizer._resize_image(test_image_rgb.copy(), (80, 60), maintain_aspect=False)
        assert resized.size == (80, 60)

    def test_create_thumbnail(self, test_image_rgb) -> None:
        """Test thumbnail creation with center crop."""
        optimizer = FormatOptimizer()
        # Create non-square image
        wide_img = Image.new("RGB", (200, 100), color=(128, 128, 128))
        thumb = optimizer._create_thumbnail(wide_img, (50, 50))
        assert thumb.size == (50, 50)

    def test_convert_to_webp(self, test_image_rgb) -> None:
        """Test WebP conversion."""
        optimizer = FormatOptimizer()
        data, content_type = optimizer._convert_to_format(
            test_image_rgb, OutputFormat.WEBP, quality=85
        )
        assert content_type == "image/webp"
        assert len(data) > 0
        # Verify it's valid WebP
        img = Image.open(io.BytesIO(data))
        assert img.format == "WEBP"

    def test_convert_to_jpeg(self, test_image_rgb) -> None:
        """Test JPEG conversion."""
        optimizer = FormatOptimizer()
        data, content_type = optimizer._convert_to_format(
            test_image_rgb, OutputFormat.JPEG, quality=90
        )
        assert content_type == "image/jpeg"
        img = Image.open(io.BytesIO(data))
        assert img.format == "JPEG"

    def test_convert_to_png(self, test_image_rgb) -> None:
        """Test PNG conversion."""
        optimizer = FormatOptimizer()
        data, content_type = optimizer._convert_to_format(test_image_rgb, OutputFormat.PNG)
        assert content_type == "image/png"
        img = Image.open(io.BytesIO(data))
        assert img.format == "PNG"

    def test_convert_to_tiff(self, test_image_rgb) -> None:
        """Test TIFF conversion with DPI."""
        optimizer = FormatOptimizer()
        data, content_type = optimizer._convert_to_format(
            test_image_rgb, OutputFormat.TIFF, dpi=300
        )
        assert content_type == "image/tiff"
        img = Image.open(io.BytesIO(data))
        assert img.format == "TIFF"

    def test_convert_rgba_to_jpeg(self, test_image_rgba) -> None:
        """Test RGBA to JPEG conversion (removes alpha)."""
        optimizer = FormatOptimizer()
        data, content_type = optimizer._convert_to_format(test_image_rgba, OutputFormat.JPEG)
        assert content_type == "image/jpeg"
        img = Image.open(io.BytesIO(data))
        assert img.mode == "RGB"

    def test_convert_unsupported_format(self, test_image_rgb) -> None:
        """Test conversion with invalid format."""
        optimizer = FormatOptimizer()
        with pytest.raises(ValueError, match="Unsupported format"):
            optimizer._convert_to_format(test_image_rgb, "invalid")  # type: ignore

    def test_generate_key(self) -> None:
        """Test storage key generation."""
        optimizer = FormatOptimizer()
        key = optimizer._generate_key("SKU-123", "web", "webp")
        assert key.startswith("enhanced/SKU-123/")
        assert key.endswith("_web.webp")

    @pytest.mark.asyncio
    async def test_download_image_success(self, test_image_bytes) -> None:
        """Test successful image download."""
        optimizer = FormatOptimizer()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_image_bytes

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            img = await optimizer._download_image("https://example.com/image.jpg", "test-123")

            assert isinstance(img, Image.Image)

    @pytest.mark.asyncio
    async def test_download_image_failure(self) -> None:
        """Test image download failure."""
        optimizer = FormatOptimizer()

        mock_response = AsyncMock()
        mock_response.status_code = 404

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response

        with patch("services.ml.enhancement.format_optimizer.httpx.AsyncClient") as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance
            MockAsyncClient.return_value.__aexit__.return_value = None

            with pytest.raises(FormatOptimizationError) as exc_info:
                await optimizer._download_image("https://example.com/notfound.jpg", "test-123")

            assert "HTTP 404" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_optimize_full(self, mock_r2_client, test_image_bytes) -> None:
        """Test full optimization with all variants."""
        optimizer = FormatOptimizer(r2_client=mock_r2_client)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_image_bytes

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            result = await optimizer.optimize(
                "https://example.com/product.jpg",
                "SKU-123",
                generate_thumbnails=True,
                generate_social=True,
                generate_print=True,
            )

            assert isinstance(result, FormatOptimizationResult)
            assert len(result.variants) > 0
            # Should have WebP, JPEG, TIFF, thumbnails, social
            variant_names = [v.name for v in result.variants]
            assert "web" in variant_names
            assert "fallback" in variant_names

    @pytest.mark.asyncio
    async def test_optimize_minimal(self, mock_r2_client, test_image_bytes) -> None:
        """Test optimization with minimal variants."""
        optimizer = FormatOptimizer(r2_client=mock_r2_client)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_image_bytes

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            result = await optimizer.optimize(
                "https://example.com/product.jpg",
                "SKU-123",
                generate_thumbnails=False,
                generate_social=False,
                generate_print=False,
            )

            # Should only have WebP and JPEG
            variant_names = [v.name for v in result.variants]
            assert "web" in variant_names
            assert "fallback" in variant_names
            assert "print" not in variant_names


# =============================================================================
# LightingNormalizationService Tests
# =============================================================================


class TestLightingIntensity:
    """Tests for LightingIntensity enum."""

    def test_intensity_values(self) -> None:
        """Test intensity values."""
        assert LightingIntensity.SUBTLE.value == "subtle"
        assert LightingIntensity.MODERATE.value == "moderate"
        assert LightingIntensity.STRONG.value == "strong"


class TestLightingResult:
    """Tests for LightingResult model."""

    def test_result_valid(self) -> None:
        """Test result validity check."""
        result = LightingResult(
            original_url="https://example.com/original.jpg",
            result_url="https://example.com/result.jpg",
            intensity=LightingIntensity.MODERATE,
            model_used="test-model",
            color_delta_e=1.5,
            color_preserved=True,
            processing_time_ms=1000,
            correlation_id="test-123",
        )
        assert result.is_valid is True

    def test_result_invalid_delta_e(self) -> None:
        """Test result invalid due to high Delta-E."""
        result = LightingResult(
            original_url="https://example.com/original.jpg",
            result_url="https://example.com/result.jpg",
            intensity=LightingIntensity.MODERATE,
            model_used="test-model",
            color_delta_e=3.0,
            color_preserved=False,
            processing_time_ms=1000,
            correlation_id="test-123",
        )
        assert result.is_valid is False


class TestLightingNormalizationError:
    """Tests for LightingNormalizationError."""

    def test_error_creation(self) -> None:
        """Test creating lighting normalization error."""
        error = LightingNormalizationError(
            "Normalization failed",
            image_url="https://example.com/image.jpg",
            model="test-model",
            correlation_id="test-123",
        )
        assert error.code == DevSkyErrorCode.IMAGE_PROCESSING_FAILED
        assert error.retryable is True


class TestColorPreservationError:
    """Tests for ColorPreservationError."""

    def test_error_creation(self) -> None:
        """Test creating color preservation error."""
        error = ColorPreservationError(
            "Color deviation too high",
            delta_e=5.0,
            threshold=2.0,
            correlation_id="test-123",
        )
        assert error.code == DevSkyErrorCode.MODEL_FIDELITY_BELOW_THRESHOLD
        assert error.context["delta_e"] == 5.0
        assert error.context["threshold"] == 2.0
        assert error.retryable is False


class TestLightingNormalizationService:
    """Tests for LightingNormalizationService."""

    def test_init_default(self) -> None:
        """Test default initialization."""
        service = LightingNormalizationService()
        assert service._max_delta_e == 2.0
        assert service._owns_client is True

    def test_init_custom_delta_e(self) -> None:
        """Test initialization with custom delta E."""
        service = LightingNormalizationService(max_delta_e=3.5)
        assert service._max_delta_e == 3.5

    def test_rgb_to_lab(self) -> None:
        """Test RGB to LAB conversion."""
        service = LightingNormalizationService()
        lab = service._rgb_to_lab((128, 64, 192))
        assert isinstance(lab, tuple)
        assert len(lab) == 3

    def test_compute_delta_e(self) -> None:
        """Test Delta-E computation."""
        service = LightingNormalizationService()
        lab1 = (50.0, 10.0, -20.0)
        lab2 = (55.0, 15.0, -25.0)
        delta_e = service._compute_delta_e(lab1, lab2)
        assert delta_e > 0

    def test_get_intensity_params_subtle(self) -> None:
        """Test intensity params for subtle level."""
        service = LightingNormalizationService()
        params = service._get_intensity_params(LightingIntensity.SUBTLE)
        assert params["upscale"] == 1
        assert params["version"] == "v1.3"

    def test_get_intensity_params_moderate(self) -> None:
        """Test intensity params for moderate level."""
        service = LightingNormalizationService()
        params = service._get_intensity_params(LightingIntensity.MODERATE)
        assert params["upscale"] == 1
        assert params["version"] == "v1.4"

    def test_get_intensity_params_strong(self) -> None:
        """Test intensity params for strong level."""
        service = LightingNormalizationService()
        params = service._get_intensity_params(LightingIntensity.STRONG)
        assert params["upscale"] == 2
        assert params["version"] == "v1.4"

    def test_compute_average_color_delta(self, test_image_rgb) -> None:
        """Test average color delta computation."""
        service = LightingNormalizationService()
        delta = service._compute_average_color_delta(test_image_rgb, test_image_rgb.copy())
        assert delta < 0.1  # Identical images

    def test_compute_average_color_delta_filters_background(self) -> None:
        """Test that white background pixels are filtered."""
        service = LightingNormalizationService()
        # Create image with mostly white
        white_img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        delta = service._compute_average_color_delta(white_img, white_img)
        assert isinstance(delta, float)

    @pytest.mark.asyncio
    async def test_normalize_lighting_success(
        self, mock_replicate_client, mock_prediction_success, test_image_bytes
    ) -> None:
        """Test successful lighting normalization."""
        mock_replicate_client.connect = AsyncMock()
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_prediction_success)

        service = LightingNormalizationService(replicate_client=mock_replicate_client)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_image_bytes

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            result = await service.normalize_lighting(
                "https://example.com/product.jpg",
                intensity=LightingIntensity.MODERATE,
            )

            assert isinstance(result, LightingResult)
            assert result.intensity == LightingIntensity.MODERATE

    @pytest.mark.asyncio
    async def test_normalize_lighting_no_color_validation(
        self, mock_replicate_client, mock_prediction_success, test_image_bytes
    ) -> None:
        """Test lighting normalization without color validation."""
        mock_replicate_client.connect = AsyncMock()
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_prediction_success)

        service = LightingNormalizationService(replicate_client=mock_replicate_client)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_image_bytes

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            result = await service.normalize_lighting(
                "https://example.com/product.jpg",
                validate_colors=False,
            )

            assert result.color_delta_e == 0.0
            assert result.color_preserved is True

    @pytest.mark.asyncio
    async def test_normalize_lighting_all_models_fail(
        self, mock_replicate_client, test_image_bytes
    ) -> None:
        """Test lighting normalization when all models fail."""
        mock_replicate_client.connect = AsyncMock()
        mock_replicate_client.run_prediction = AsyncMock(side_effect=Exception("Model failed"))

        service = LightingNormalizationService(replicate_client=mock_replicate_client)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_image_bytes

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            with pytest.raises(LightingNormalizationError) as exc_info:
                await service.normalize_lighting(
                    "https://example.com/product.jpg",
                )

            assert "All lighting normalization models failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_normalize_lighting_batch(
        self, mock_replicate_client, mock_prediction_success, test_image_bytes
    ) -> None:
        """Test batch lighting normalization."""
        mock_replicate_client.connect = AsyncMock()
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_prediction_success)

        service = LightingNormalizationService(replicate_client=mock_replicate_client)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_image_bytes

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            urls = [
                "https://example.com/product1.jpg",
                "https://example.com/product2.jpg",
            ]
            results = await service.normalize_lighting_batch(urls)

            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_replicate_client) -> None:
        """Test service as async context manager."""
        mock_replicate_client.connect = AsyncMock()
        mock_replicate_client.close = AsyncMock()

        service = LightingNormalizationService(replicate_client=mock_replicate_client)

        async with service as svc:
            assert svc == service

        # Doesn't own client, so close should not be called on the client
        mock_replicate_client.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_context_manager_owns_client(self) -> None:
        """Test service as context manager when it owns the client."""
        service = LightingNormalizationService()
        # Set owns_client to True and create a mock client
        service._owns_client = True
        mock_client = AsyncMock()
        service._client = mock_client

        await service.close()

        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_image_failure(self) -> None:
        """Test image download failure."""
        service = LightingNormalizationService()

        mock_response = AsyncMock()
        mock_response.status_code = 500

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response

        with patch(
            "services.ml.enhancement.lighting_normalization.httpx.AsyncClient"
        ) as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance
            MockAsyncClient.return_value.__aexit__.return_value = None

            with pytest.raises(LightingNormalizationError) as exc_info:
                await service._download_image("https://example.com/image.jpg", "test-123")

            assert "HTTP 500" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_normalize_lighting_color_validation_failure(
        self, mock_replicate_client, mock_prediction_success, test_image_bytes
    ) -> None:
        """Test lighting normalization handles color validation download failure."""
        mock_replicate_client.connect = AsyncMock()
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_prediction_success)

        service = LightingNormalizationService(replicate_client=mock_replicate_client)

        # First call returns original image, second call fails (for result image)
        call_count = [0]
        original_response = MagicMock()
        original_response.status_code = 200
        original_response.content = test_image_bytes

        async def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return original_response
            else:
                raise Exception("Failed to download result")

        mock_client_instance = AsyncMock()
        mock_client_instance.get = side_effect

        with patch(
            "services.ml.enhancement.lighting_normalization.httpx.AsyncClient"
        ) as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance
            MockAsyncClient.return_value.__aexit__.return_value = None

            # Should not raise, but should log warning
            result = await service.normalize_lighting(
                "https://example.com/product.jpg",
                validate_colors=True,
            )

            # Color validation failed silently, so default values used
            assert result.color_delta_e == 0.0
            assert result.color_preserved is True

    @pytest.mark.asyncio
    async def test_normalize_lighting_original_download_failure(
        self, mock_replicate_client, mock_prediction_success
    ) -> None:
        """Test lighting normalization handles original image download failure."""
        mock_replicate_client.connect = AsyncMock()
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_prediction_success)

        service = LightingNormalizationService(replicate_client=mock_replicate_client)

        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = Exception("Network error")

        with patch(
            "services.ml.enhancement.lighting_normalization.httpx.AsyncClient"
        ) as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance
            MockAsyncClient.return_value.__aexit__.return_value = None

            # Should not raise because original image download failure is logged but not fatal
            result = await service.normalize_lighting(
                "https://example.com/product.jpg",
                validate_colors=True,
            )

            # Validation couldn't run, defaults used
            assert result.color_delta_e == 0.0


# =============================================================================
# UpscalingService Tests
# =============================================================================


class TestUpscaleResult:
    """Tests for UpscaleResult model."""

    def test_result_creation(self) -> None:
        """Test creating upscale result."""
        result = UpscaleResult(
            original_url="https://example.com/original.jpg",
            result_url="https://example.com/upscaled.jpg",
            original_dimensions=(500, 500),
            result_dimensions=(2000, 2000),
            scale_factor=4,
            model_used="test-model",
            face_enhance=False,
            processing_time_ms=5000,
            correlation_id="test-123",
        )
        assert result.actual_scale == 4.0
        assert result.skipped is False

    def test_result_skipped(self) -> None:
        """Test skipped upscale result."""
        result = UpscaleResult(
            original_url="https://example.com/original.jpg",
            result_url="https://example.com/original.jpg",
            original_dimensions=(3000, 3000),
            result_dimensions=(3000, 3000),
            scale_factor=4,
            model_used="",
            face_enhance=False,
            skipped=True,
            skip_reason="Image already meets minimum resolution",
            processing_time_ms=100,
            correlation_id="test-123",
        )
        assert result.skipped is True
        assert result.actual_scale == 1.0

    def test_actual_scale_zero_width(self) -> None:
        """Test actual_scale with zero original width."""
        result = UpscaleResult(
            original_url="https://example.com/original.jpg",
            result_url="https://example.com/upscaled.jpg",
            original_dimensions=(0, 0),
            result_dimensions=(1000, 1000),
            scale_factor=4,
            model_used="test-model",
            face_enhance=False,
            processing_time_ms=5000,
            correlation_id="test-123",
        )
        assert result.actual_scale == 0.0


class TestUpscalingError:
    """Tests for UpscalingError."""

    def test_error_creation(self) -> None:
        """Test creating upscaling error."""
        error = UpscalingError(
            "Upscaling failed",
            image_url="https://example.com/image.jpg",
            model="test-model",
            correlation_id="test-123",
        )
        assert error.code == DevSkyErrorCode.IMAGE_PROCESSING_FAILED
        assert error.retryable is True


class TestUpscalingService:
    """Tests for UpscalingService."""

    def test_init_default(self) -> None:
        """Test default initialization."""
        service = UpscalingService()
        assert service._min_resolution == 2000
        assert service._owns_client is True

    def test_init_custom_resolution(self) -> None:
        """Test initialization with custom minimum resolution."""
        service = UpscalingService(min_resolution=3000)
        assert service._min_resolution == 3000

    def test_should_skip_high_res(self) -> None:
        """Test should_skip for high resolution image."""
        service = UpscalingService(min_resolution=2000)
        should_skip, reason = service._should_skip((2500, 1800))
        assert should_skip is True
        assert "already meets minimum resolution" in reason

    def test_should_skip_low_res(self) -> None:
        """Test should_skip for low resolution image."""
        service = UpscalingService(min_resolution=2000)
        should_skip, reason = service._should_skip((800, 600))
        assert should_skip is False
        assert reason is None

    def test_should_skip_zero_dimensions(self) -> None:
        """Test should_skip with zero dimensions."""
        service = UpscalingService()
        should_skip, reason = service._should_skip((0, 0))
        assert should_skip is False

    @pytest.mark.asyncio
    async def test_get_image_dimensions_success(self, test_image_bytes) -> None:
        """Test successful dimension retrieval."""
        service = UpscalingService()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_image_bytes

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            dims = await service._get_image_dimensions("https://example.com/image.jpg", "test-123")

            assert dims == (100, 100)  # Test image is 100x100

    @pytest.mark.asyncio
    async def test_get_image_dimensions_failure(self) -> None:
        """Test dimension retrieval failure returns (0, 0)."""
        service = UpscalingService()

        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = Exception("Network error")

        with patch("services.ml.enhancement.upscaling.httpx.AsyncClient") as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance
            MockAsyncClient.return_value.__aexit__.return_value = None

            dims = await service._get_image_dimensions("https://example.com/image.jpg", "test-123")

            assert dims == (0, 0)

    @pytest.mark.asyncio
    async def test_upscale_image_success(
        self, mock_replicate_client, mock_prediction_success, test_image_bytes
    ) -> None:
        """Test successful image upscaling."""
        mock_replicate_client.connect = AsyncMock()
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_prediction_success)

        service = UpscalingService(replicate_client=mock_replicate_client, min_resolution=2000)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_image_bytes

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            result = await service.upscale_image(
                "https://example.com/product.jpg",
                scale_factor=4,
            )

            assert isinstance(result, UpscaleResult)
            assert result.scale_factor == 4

    @pytest.mark.asyncio
    async def test_upscale_image_invalid_scale(self, mock_replicate_client) -> None:
        """Test upscaling with invalid scale factor."""
        mock_replicate_client.connect = AsyncMock()

        service = UpscalingService(replicate_client=mock_replicate_client)

        with pytest.raises(UpscalingError) as exc_info:
            await service.upscale_image(
                "https://example.com/product.jpg",
                scale_factor=8,  # Invalid - must be 2 or 4
            )

        assert "Invalid scale factor" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upscale_image_skip_sufficient(
        self, mock_replicate_client, test_image_bytes
    ) -> None:
        """Test upscaling skips when resolution is sufficient."""
        mock_replicate_client.connect = AsyncMock()

        service = UpscalingService(replicate_client=mock_replicate_client, min_resolution=50)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_image_bytes

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            result = await service.upscale_image(
                "https://example.com/product.jpg",
                skip_if_sufficient=True,
            )

            assert result.skipped is True
            assert "already meets minimum resolution" in result.skip_reason

    @pytest.mark.asyncio
    async def test_upscale_image_face_enhance(
        self, mock_replicate_client, mock_prediction_success, test_image_bytes
    ) -> None:
        """Test upscaling with face enhancement."""
        mock_replicate_client.connect = AsyncMock()
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_prediction_success)

        service = UpscalingService(replicate_client=mock_replicate_client, min_resolution=2000)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_image_bytes

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            result = await service.upscale_image(
                "https://example.com/model.jpg",
                scale_factor=2,
                face_enhance=True,
            )

            assert result.face_enhance is True

    @pytest.mark.asyncio
    async def test_upscale_image_all_models_fail(
        self, mock_replicate_client, test_image_bytes
    ) -> None:
        """Test upscaling when all models fail."""
        mock_replicate_client.connect = AsyncMock()
        mock_replicate_client.run_prediction = AsyncMock(side_effect=Exception("Model failed"))

        service = UpscalingService(replicate_client=mock_replicate_client, min_resolution=2000)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_image_bytes

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            with pytest.raises(UpscalingError) as exc_info:
                await service.upscale_image(
                    "https://example.com/product.jpg",
                )

            assert "All upscaling models failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upscale_batch(
        self, mock_replicate_client, mock_prediction_success, test_image_bytes
    ) -> None:
        """Test batch upscaling."""
        mock_replicate_client.connect = AsyncMock()
        mock_replicate_client.run_prediction = AsyncMock(return_value=mock_prediction_success)

        service = UpscalingService(replicate_client=mock_replicate_client, min_resolution=2000)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_image_bytes

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            urls = [
                "https://example.com/product1.jpg",
                "https://example.com/product2.jpg",
            ]
            results = await service.upscale_batch(urls, scale_factor=4)

            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_replicate_client) -> None:
        """Test service as async context manager."""
        mock_replicate_client.connect = AsyncMock()
        mock_replicate_client.close = AsyncMock()

        service = UpscalingService(replicate_client=mock_replicate_client)

        async with service as svc:
            assert svc == service


# =============================================================================
# Integration Tests (marked for optional execution)
# =============================================================================


@pytest.mark.integration
class TestMLEnhancementIntegration:
    """Integration tests requiring external services."""

    @pytest.mark.skip(reason="Requires Replicate API key")
    @pytest.mark.asyncio
    async def test_full_enhancement_pipeline(self) -> None:
        """Test complete enhancement pipeline with real services."""
        # This test would use real Replicate API
        pass
