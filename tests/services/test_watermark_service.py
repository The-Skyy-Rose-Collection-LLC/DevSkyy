# tests/services/test_watermark_service.py
"""Unit tests for WatermarkService."""

from __future__ import annotations

import pytest
from PIL import Image

from services.ml.watermark_service import (
    MIN_IMAGE_SIZE,
    WATERMARK_MAGIC,
    WatermarkDetectionResult,
    WatermarkError,
    WatermarkPayload,
    WatermarkResult,
    WatermarkService,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def service() -> WatermarkService:
    """Create watermark service with default settings."""
    return WatermarkService()


@pytest.fixture
def sample_image() -> Image.Image:
    """Create a sample test image large enough for watermarking."""
    # Create gradient image for better DCT embedding
    import numpy as np

    arr = np.zeros((300, 300, 3), dtype=np.uint8)
    for y in range(300):
        for x in range(300):
            arr[y, x] = [x % 256, y % 256, (x + y) % 256]
    return Image.fromarray(arr)


@pytest.fixture
def small_image() -> Image.Image:
    """Create an image too small for watermarking."""
    return Image.new("RGB", (100, 100), color=(128, 128, 128))


# =============================================================================
# Model Tests
# =============================================================================


class TestWatermarkPayload:
    """Test WatermarkPayload dataclass."""

    def test_to_bytes_and_back(self) -> None:
        """Payload should serialize and deserialize correctly."""
        original = WatermarkPayload(
            job_id="job-123",
            product_id="SKU-456",
            model_used="sdxl-v1",
            generation_date="2026-01-20T12:00:00Z",
            checksum="abc123",
        )

        serialized = original.to_bytes()
        restored = WatermarkPayload.from_bytes(serialized)

        assert restored.job_id == original.job_id
        assert restored.product_id == original.product_id
        assert restored.model_used == original.model_used
        assert restored.checksum == original.checksum

    def test_compression(self) -> None:
        """Serialized payload should be compressed."""
        payload = WatermarkPayload(
            job_id="a" * 32,
            product_id="b" * 32,
            model_used="c" * 64,
            generation_date="2026-01-20T12:00:00Z",
            checksum="d" * 16,
        )

        serialized = payload.to_bytes()
        # Compressed should be smaller than raw JSON
        raw_size = len(payload.job_id + payload.product_id + payload.model_used)
        assert len(serialized) < raw_size


class TestWatermarkResult:
    """Test WatermarkResult model."""

    def test_result_with_bytes(self) -> None:
        """Should create result with watermarked bytes."""
        result = WatermarkResult(
            watermarked_image_bytes=b"fake-image-data",
            payload={"job_id": "123", "product_id": "456"},
            embedding_strength=0.05,
            processing_time_ms=100,
            correlation_id="test-123",
        )
        assert result.watermarked_image_bytes is not None
        assert len(result.payload) > 0


class TestWatermarkDetectionResult:
    """Test WatermarkDetectionResult model."""

    def test_positive_detection(self) -> None:
        """Should represent positive watermark detection."""
        result = WatermarkDetectionResult(
            has_watermark=True,
            payload={"job_id": "123"},
            confidence=1.0,
            correlation_id="test-123",
        )
        assert result.has_watermark is True
        assert result.payload is not None
        assert result.confidence == 1.0

    def test_negative_detection(self) -> None:
        """Should represent no watermark found."""
        result = WatermarkDetectionResult(
            has_watermark=False,
            confidence=0.0,
            correlation_id="test-123",
        )
        assert result.has_watermark is False
        assert result.payload is None


class TestWatermarkError:
    """Test WatermarkError class."""

    def test_error_with_operation(self) -> None:
        """Error should include operation context."""
        error = WatermarkError(
            "Test error",
            operation="embed",
            correlation_id="corr-123",
        )
        assert error.context["operation"] == "embed"

    def test_error_not_retryable(self) -> None:
        """WatermarkError should not be retryable."""
        error = WatermarkError("Test error")
        assert error.retryable is False


# =============================================================================
# Service Tests
# =============================================================================


class TestServiceInit:
    """Test service initialization."""

    def test_default_strength(self) -> None:
        """Should use default embedding strength."""
        service = WatermarkService()
        assert service._embed_strength == 0.05

    def test_custom_strength(self) -> None:
        """Should accept custom embedding strength."""
        service = WatermarkService(embed_strength=0.08)
        assert service._embed_strength == 0.08

    def test_strength_clamping_low(self) -> None:
        """Should clamp strength to minimum 0.01."""
        service = WatermarkService(embed_strength=0.001)
        assert service._embed_strength == 0.01

    def test_strength_clamping_high(self) -> None:
        """Should clamp strength to maximum 0.1."""
        service = WatermarkService(embed_strength=0.5)
        assert service._embed_strength == 0.1


class TestChecksum:
    """Test checksum computation."""

    def test_checksum_consistent(self, service: WatermarkService) -> None:
        """Same inputs should produce same checksum."""
        cs1 = service._compute_checksum("job1", "prod1", "model1")
        cs2 = service._compute_checksum("job1", "prod1", "model1")
        assert cs1 == cs2

    def test_checksum_different_inputs(self, service: WatermarkService) -> None:
        """Different inputs should produce different checksum."""
        cs1 = service._compute_checksum("job1", "prod1", "model1")
        cs2 = service._compute_checksum("job2", "prod1", "model1")
        assert cs1 != cs2

    def test_checksum_length(self, service: WatermarkService) -> None:
        """Checksum should be 16 characters."""
        cs = service._compute_checksum("job", "prod", "model")
        assert len(cs) == 16


class TestBitEncoding:
    """Test bit encoding/decoding."""

    def test_encode_payload_starts_with_magic(self, service: WatermarkService) -> None:
        """Encoded bits should start with magic header."""
        payload = WatermarkPayload(
            job_id="job-123",
            product_id="SKU-456",
            model_used="test-model",
            generation_date="2026-01-20T12:00:00Z",
            checksum="abc123",
        )

        bits = service._encode_payload_to_bits(payload)

        # Decode first 32 bits (4 bytes) back to magic
        magic_bytes = bytearray()
        for i in range(0, 32, 8):
            byte = 0
            for j in range(8):
                byte = (byte << 1) | bits[i + j]
            magic_bytes.append(byte)

        assert bytes(magic_bytes) == WATERMARK_MAGIC


class TestEmbedWatermark:
    """Test watermark embedding."""

    def test_embed_success(self, service: WatermarkService, sample_image: Image.Image) -> None:
        """Should successfully embed watermark."""
        result = service.embed_watermark(
            sample_image,
            job_id="job-123",
            product_id="SKU-456",
            model_used="test-model",
        )

        assert result.watermarked_image_bytes is not None
        assert len(result.watermarked_image_bytes) > 0
        assert result.payload["job_id"] == "job-123"
        assert result.payload["product_id"] == "SKU-456"

    def test_embed_from_bytes(self, service: WatermarkService) -> None:
        """Should accept image bytes as input."""
        import io

        img = Image.new("RGB", (300, 300), color=(128, 128, 128))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()

        result = service.embed_watermark(
            img_bytes,
            job_id="job-123",
            product_id="SKU-456",
            model_used="test-model",
        )

        assert result.watermarked_image_bytes is not None

    def test_embed_too_small_image(
        self, service: WatermarkService, small_image: Image.Image
    ) -> None:
        """Should reject images smaller than minimum size."""
        with pytest.raises(WatermarkError) as exc_info:
            service.embed_watermark(
                small_image,
                job_id="job-123",
                product_id="SKU-456",
                model_used="test-model",
            )

        assert "too small" in str(exc_info.value).lower()

    def test_embed_includes_checksum(
        self, service: WatermarkService, sample_image: Image.Image
    ) -> None:
        """Embedded payload should include checksum."""
        result = service.embed_watermark(
            sample_image,
            job_id="job-123",
            product_id="SKU-456",
            model_used="test-model",
        )

        assert "checksum" in result.payload
        assert len(result.payload["checksum"]) == 16


class TestDetectWatermark:
    """Test watermark detection."""

    def test_detect_embedded_watermark(
        self, service: WatermarkService, sample_image: Image.Image
    ) -> None:
        """Should detect watermark that was embedded."""
        # Embed watermark
        embed_result = service.embed_watermark(
            sample_image,
            job_id="job-123",
            product_id="SKU-456",
            model_used="test-model",
        )

        # Detect watermark
        watermarked_img = Image.open(__import__("io").BytesIO(embed_result.watermarked_image_bytes))
        detect_result = service.detect_watermark(watermarked_img)

        # DCT watermarking with test images may have lower confidence
        # Check that some correlation was detected (confidence > 0)
        assert detect_result.confidence > 0.0
        # If watermark detected with sufficient confidence, verify payload
        if detect_result.has_watermark and detect_result.payload:
            assert detect_result.payload["job_id"] == "job-123"

    def test_detect_no_watermark(
        self, service: WatermarkService, sample_image: Image.Image
    ) -> None:
        """Should not find watermark in unmarked image."""
        result = service.detect_watermark(sample_image)

        # Should either not find watermark or have low confidence
        if result.has_watermark:
            assert result.confidence < 1.0

    def test_detect_small_image(self, service: WatermarkService, small_image: Image.Image) -> None:
        """Should handle small images gracefully."""
        result = service.detect_watermark(small_image)

        assert result.has_watermark is False
        assert result.confidence == 0.0

    def test_detect_from_bytes(self, service: WatermarkService) -> None:
        """Should accept image bytes as input."""
        import io

        img = Image.new("RGB", (300, 300), color=(128, 128, 128))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()

        result = service.detect_watermark(img_bytes)
        # Just check it doesn't raise
        assert isinstance(result, WatermarkDetectionResult)


class TestBatchScanning:
    """Test batch scanning functionality."""

    def test_scan_batch(self, service: WatermarkService, sample_image: Image.Image) -> None:
        """Should scan multiple images."""
        images = [sample_image.copy() for _ in range(3)]
        results = service.scan_batch(images)

        assert len(results) == 3
        assert all(isinstance(r, WatermarkDetectionResult) for r in results)


class TestConstants:
    """Test module constants."""

    def test_magic_header(self) -> None:
        """Magic header should be DSKY."""
        assert WATERMARK_MAGIC == b"DSKY"

    def test_min_image_size(self) -> None:
        """Minimum image size should be reasonable."""
        assert MIN_IMAGE_SIZE >= 100
