# tests/services/test_authenticity_validator.py
"""Unit tests for AuthenticityValidator."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from PIL import Image

from services.ml.enhancement.authenticity_validator import (
    HASH_SIZE,
    MAX_DELTA_E,
    MIN_SIMILARITY_THRESHOLD,
    AuthenticityReport,
    AuthenticityValidationError,
    AuthenticityValidator,
    ValidationResult,
    ValidationStatus,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def validator() -> AuthenticityValidator:
    """Create validator with default settings."""
    return AuthenticityValidator()


@pytest.fixture
def red_image() -> Image.Image:
    """Create a solid red test image."""
    return Image.new("RGB", (100, 100), color=(255, 0, 0))


@pytest.fixture
def slightly_different_red_image() -> Image.Image:
    """Create a slightly different red image."""
    return Image.new("RGB", (100, 100), color=(250, 5, 5))


@pytest.fixture
def blue_image() -> Image.Image:
    """Create a solid blue test image."""
    return Image.new("RGB", (100, 100), color=(0, 0, 255))


# =============================================================================
# Model Tests
# =============================================================================


class TestValidationStatus:
    """Test ValidationStatus enum."""

    def test_passed_value(self) -> None:
        """ValidationStatus.PASSED should have correct value."""
        assert ValidationStatus.PASSED.value == "passed"

    def test_failed_value(self) -> None:
        """ValidationStatus.FAILED should have correct value."""
        assert ValidationStatus.FAILED.value == "failed"

    def test_needs_review_value(self) -> None:
        """ValidationStatus.NEEDS_REVIEW should have correct value."""
        assert ValidationStatus.NEEDS_REVIEW.value == "needs_review"


class TestValidationResult:
    """Test ValidationResult model."""

    def test_passed_result(self) -> None:
        """Should create passed result."""
        result = ValidationResult(
            check_name="perceptual_hash",
            passed=True,
            score=0.98,
            threshold=0.95,
            details="Perceptual similarity: 98%",
        )
        assert result.passed is True
        assert result.score > result.threshold

    def test_failed_result(self) -> None:
        """Should create failed result."""
        result = ValidationResult(
            check_name="color_accuracy",
            passed=False,
            score=5.5,
            threshold=2.0,
            details="Delta-E: 5.5",
        )
        assert result.passed is False

    def test_result_with_visual_diff(self) -> None:
        """Should support visual diff URL."""
        result = ValidationResult(
            check_name="perceptual_hash",
            passed=False,
            score=0.75,
            threshold=0.95,
            details="Similarity: 75%",
            visual_diff_url="https://example.com/diff.png",
        )
        assert result.visual_diff_url is not None


class TestAuthenticityReport:
    """Test AuthenticityReport model."""

    def test_is_approved_when_passed(self) -> None:
        """is_approved should return True when passed without review."""
        report = AuthenticityReport(
            original_url="https://example.com/original.jpg",
            enhanced_url="https://example.com/enhanced.jpg",
            status=ValidationStatus.PASSED,
            overall_similarity=0.98,
            color_accuracy_delta_e=1.5,
            validation_results=[],
            requires_human_review=False,
            review_reasons=[],
            processing_time_ms=100,
            correlation_id="test-123",
        )
        assert report.is_approved is True

    def test_is_approved_false_when_needs_review(self) -> None:
        """is_approved should return False when human review required."""
        report = AuthenticityReport(
            original_url="https://example.com/original.jpg",
            enhanced_url="https://example.com/enhanced.jpg",
            status=ValidationStatus.PASSED,
            overall_similarity=0.96,
            color_accuracy_delta_e=1.8,
            validation_results=[],
            requires_human_review=True,
            review_reasons=["Edge case"],
            processing_time_ms=100,
            correlation_id="test-123",
        )
        assert report.is_approved is False

    def test_is_approved_false_when_failed(self) -> None:
        """is_approved should return False when validation failed."""
        report = AuthenticityReport(
            original_url="https://example.com/original.jpg",
            enhanced_url="https://example.com/enhanced.jpg",
            status=ValidationStatus.FAILED,
            overall_similarity=0.70,
            color_accuracy_delta_e=8.0,
            validation_results=[],
            requires_human_review=True,
            review_reasons=["Failed all checks"],
            processing_time_ms=100,
            correlation_id="test-123",
        )
        assert report.is_approved is False


class TestAuthenticityValidationError:
    """Test AuthenticityValidationError class."""

    def test_error_with_context(self) -> None:
        """Error should include context fields."""
        error = AuthenticityValidationError(
            "Test error",
            original_url="https://example.com/original.jpg",
            enhanced_url="https://example.com/enhanced.jpg",
            correlation_id="corr-123",
        )
        assert error.context["original_url"] == "https://example.com/original.jpg"
        assert error.context["enhanced_url"] == "https://example.com/enhanced.jpg"
        assert error.correlation_id == "corr-123"

    def test_error_not_retryable(self) -> None:
        """AuthenticityValidationError should not be retryable."""
        error = AuthenticityValidationError("Test error")
        assert error.retryable is False


# =============================================================================
# Perceptual Hash Tests
# =============================================================================


class TestComputePhash:
    """Test perceptual hash computation."""

    def test_identical_images_same_hash(
        self, validator: AuthenticityValidator, red_image: Image.Image
    ) -> None:
        """Identical images should have same hash."""
        hash1 = validator._compute_phash(red_image)
        hash2 = validator._compute_phash(red_image.copy())
        assert hash1 == hash2

    def test_hash_is_hex_string(
        self, validator: AuthenticityValidator, red_image: Image.Image
    ) -> None:
        """Hash should be a hex string."""
        hash_val = validator._compute_phash(red_image)
        assert isinstance(hash_val, str)
        # Should be valid hex
        int(hash_val, 16)

    def test_different_images_different_hash(
        self,
        validator: AuthenticityValidator,
    ) -> None:
        """Very different images should have different hashes."""
        # Create images with distinct patterns
        # dHash compares left-to-right pixel differences, so we need
        # images with different horizontal gradient patterns
        import numpy as np

        # Image 1: checkerboard pattern
        arr1 = np.zeros((100, 100), dtype=np.uint8)
        for y in range(100):
            for x in range(100):
                if (x + y) % 2 == 0:
                    arr1[y, x] = 255
        img1 = Image.fromarray(arr1, mode="L").convert("RGB")

        # Image 2: vertical stripes
        arr2 = np.zeros((100, 100), dtype=np.uint8)
        for x in range(100):
            if x % 10 < 5:
                arr2[:, x] = 255
        img2 = Image.fromarray(arr2, mode="L").convert("RGB")

        hash1 = validator._compute_phash(img1)
        hash2 = validator._compute_phash(img2)
        # Checkerboard and stripes should produce different hashes
        assert hash1 != hash2


class TestComputeHashSimilarity:
    """Test hash similarity computation."""

    def test_identical_hashes_100_percent(self, validator: AuthenticityValidator) -> None:
        """Identical hashes should have 100% similarity."""
        similarity = validator._compute_hash_similarity("abcd1234", "abcd1234")
        assert similarity == 1.0

    def test_completely_different_hashes(self, validator: AuthenticityValidator) -> None:
        """Completely different hashes should have low similarity."""
        # All 0s vs all Fs
        similarity = validator._compute_hash_similarity("00000000", "ffffffff")
        assert similarity == 0.0

    def test_different_length_hashes(self, validator: AuthenticityValidator) -> None:
        """Different length hashes should return 0."""
        similarity = validator._compute_hash_similarity("abc", "abcdef")
        assert similarity == 0.0


# =============================================================================
# Color Accuracy Tests
# =============================================================================


class TestRgbToLab:
    """Test RGB to LAB color conversion."""

    def test_white_conversion(self, validator: AuthenticityValidator) -> None:
        """White should convert to L=100, a=0, b=0 approximately."""
        L, a, b = validator._rgb_to_lab((255, 255, 255))
        assert L > 99  # Should be close to 100
        assert abs(a) < 1  # Should be close to 0
        assert abs(b) < 1  # Should be close to 0

    def test_black_conversion(self, validator: AuthenticityValidator) -> None:
        """Black should convert to L=0, a=0, b=0."""
        L, a, b = validator._rgb_to_lab((0, 0, 0))
        assert L < 1  # Should be close to 0


class TestComputeDeltaE:
    """Test Delta-E computation."""

    def test_identical_colors_zero_delta(self, validator: AuthenticityValidator) -> None:
        """Identical colors should have Delta-E of 0."""
        lab = (50.0, 10.0, -20.0)
        delta_e = validator._compute_delta_e(lab, lab)
        assert delta_e == 0.0

    def test_similar_colors_small_delta(self, validator: AuthenticityValidator) -> None:
        """Similar colors should have small Delta-E."""
        lab1 = (50.0, 10.0, 10.0)
        lab2 = (50.5, 10.2, 10.1)
        delta_e = validator._compute_delta_e(lab1, lab2)
        assert delta_e < 1.0


class TestComputeAverageDeltaE:
    """Test average Delta-E computation."""

    def test_identical_images_zero_delta(
        self, validator: AuthenticityValidator, red_image: Image.Image
    ) -> None:
        """Identical images should have Delta-E of 0."""
        delta_e = validator._compute_average_delta_e(red_image, red_image.copy())
        assert delta_e == 0.0

    def test_similar_images_small_delta(
        self,
        validator: AuthenticityValidator,
        red_image: Image.Image,
        slightly_different_red_image: Image.Image,
    ) -> None:
        """Similar images should have small Delta-E."""
        delta_e = validator._compute_average_delta_e(red_image, slightly_different_red_image)
        assert delta_e < 5.0  # Should be relatively small

    def test_different_images_large_delta(
        self,
        validator: AuthenticityValidator,
        red_image: Image.Image,
        blue_image: Image.Image,
    ) -> None:
        """Very different images should have large Delta-E."""
        delta_e = validator._compute_average_delta_e(red_image, blue_image)
        assert delta_e > 50.0  # Red to blue is a large difference

    def test_handles_different_sizes(self, validator: AuthenticityValidator) -> None:
        """Should handle images of different sizes."""
        img1 = Image.new("RGB", (100, 100), color=(255, 0, 0))
        img2 = Image.new("RGB", (200, 200), color=(255, 0, 0))
        delta_e = validator._compute_average_delta_e(img1, img2)
        assert delta_e < 1.0  # Same color, should be near 0


# =============================================================================
# Edge Similarity Tests
# =============================================================================


class TestComputeEdgeSimilarity:
    """Test edge similarity computation."""

    def test_identical_images_high_similarity(
        self, validator: AuthenticityValidator, red_image: Image.Image
    ) -> None:
        """Identical images should have high edge similarity."""
        similarity = validator._compute_edge_similarity(red_image, red_image.copy())
        assert similarity > 0.9

    def test_handles_different_sizes(self, validator: AuthenticityValidator) -> None:
        """Should handle images of different sizes."""
        img1 = Image.new("RGB", (100, 100), color=(255, 0, 0))
        img2 = Image.new("RGB", (200, 200), color=(255, 0, 0))
        # Should not raise, just compute
        similarity = validator._compute_edge_similarity(img1, img2)
        assert 0.0 <= similarity <= 1.0


# =============================================================================
# Validation Tests
# =============================================================================


class TestValidate:
    """Test the main validate method."""

    @pytest.mark.asyncio
    async def test_validate_identical_images_passes(
        self, validator: AuthenticityValidator, red_image: Image.Image
    ) -> None:
        """Identical images should pass validation."""
        with patch.object(validator, "_download_image", new_callable=AsyncMock) as mock_download:
            mock_download.return_value = red_image

            report = await validator.validate(
                "https://example.com/original.jpg",
                "https://example.com/enhanced.jpg",
            )

        assert report.status == ValidationStatus.PASSED
        assert report.is_approved is True
        assert report.overall_similarity >= MIN_SIMILARITY_THRESHOLD

    @pytest.mark.asyncio
    async def test_validate_very_different_images_fails(
        self,
        validator: AuthenticityValidator,
        red_image: Image.Image,
        blue_image: Image.Image,
    ) -> None:
        """Very different images should fail validation."""
        call_count = 0

        async def download_side_effect(url, correlation_id):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return red_image
            return blue_image

        with patch.object(validator, "_download_image", new_callable=AsyncMock) as mock_download:
            mock_download.side_effect = download_side_effect

            report = await validator.validate(
                "https://example.com/original.jpg",
                "https://example.com/enhanced.jpg",
            )

        assert report.status == ValidationStatus.FAILED
        assert report.is_approved is False
        assert len(report.review_reasons) > 0

    @pytest.mark.asyncio
    async def test_validate_download_failure(self, validator: AuthenticityValidator) -> None:
        """Should raise error on download failure."""
        with (
            patch.object(validator, "_download_image", new_callable=AsyncMock) as mock_download,
            pytest.raises(AuthenticityValidationError),
        ):
            mock_download.side_effect = Exception("Download failed")
            await validator.validate(
                "https://example.com/original.jpg",
                "https://example.com/enhanced.jpg",
            )

    @pytest.mark.asyncio
    async def test_validate_includes_correlation_id(
        self, validator: AuthenticityValidator, red_image: Image.Image
    ) -> None:
        """Report should include correlation ID."""
        with patch.object(validator, "_download_image", new_callable=AsyncMock) as mock_download:
            mock_download.return_value = red_image

            report = await validator.validate(
                "https://example.com/original.jpg",
                "https://example.com/enhanced.jpg",
                correlation_id="my-corr-id",
            )

        assert report.correlation_id == "my-corr-id"

    @pytest.mark.asyncio
    async def test_validate_generates_correlation_id(
        self, validator: AuthenticityValidator, red_image: Image.Image
    ) -> None:
        """Should generate correlation ID when not provided."""
        with patch.object(validator, "_download_image", new_callable=AsyncMock) as mock_download:
            mock_download.return_value = red_image

            report = await validator.validate(
                "https://example.com/original.jpg",
                "https://example.com/enhanced.jpg",
            )

        assert report.correlation_id is not None
        assert len(report.correlation_id) > 0


class TestCustomThresholds:
    """Test validator with custom thresholds."""

    def test_custom_similarity_threshold(self) -> None:
        """Should accept custom similarity threshold."""
        validator = AuthenticityValidator(similarity_threshold=0.99)
        assert validator._similarity_threshold == 0.99

    def test_custom_max_delta_e(self) -> None:
        """Should accept custom max Delta-E."""
        validator = AuthenticityValidator(max_delta_e=1.0)
        assert validator._max_delta_e == 1.0


class TestConstants:
    """Test module constants."""

    def test_min_similarity_threshold_reasonable(self) -> None:
        """Minimum similarity should be reasonable."""
        assert 0.90 <= MIN_SIMILARITY_THRESHOLD <= 0.99

    def test_max_delta_e_reasonable(self) -> None:
        """Max Delta-E should be reasonable."""
        assert 1.0 <= MAX_DELTA_E <= 5.0

    def test_hash_size_is_power_of_two(self) -> None:
        """Hash size should be power of 2."""
        assert HASH_SIZE > 0
        assert (HASH_SIZE & (HASH_SIZE - 1)) == 0  # Power of 2 check
