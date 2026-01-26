# tests/services/test_image_ingestion.py
"""Unit tests for ImageIngestionService.

Tests cover:
- Image download with validation
- Image format and dimension validation
- Deduplication checks
- R2 upload mocking
- ML processing queue integration
- Batch ingestion
- Error handling for all failure modes

Author: DevSkyy Platform Team
"""

from __future__ import annotations

import io
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from services.image_ingestion import (
    ALLOWED_MIME_TYPES,
    MAX_DIMENSION,
    MAX_FILE_SIZE_BYTES,
    MIN_DIMENSION,
    ImageIngestionService,
    ImageValidationError,
    IngestionRequest,
    IngestionResult,
    IngestionSource,
    IngestionStatus,
    get_ingestion_service,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_deduplicator() -> MagicMock:
    """Create mock deduplicator that returns no duplicates by default."""
    from services.image_deduplication import DuplicateCheckResult, HashResult

    dedup = MagicMock()

    # compute_hash returns a HashResult
    dedup.compute_hash.return_value = HashResult(
        content_hash="abc123hash",
        algorithm="sha256",
        file_size_bytes=1024,
    )

    # check_duplicate returns non-duplicate by default
    async def check_dup(*args, **kwargs):
        return DuplicateCheckResult(is_duplicate=False)

    dedup.check_duplicate = AsyncMock(side_effect=check_dup)

    # register_hash is async
    dedup.register_hash = AsyncMock()

    return dedup


@pytest.fixture
def mock_r2_client() -> MagicMock:
    """Create mock R2 storage client."""
    client = MagicMock()
    client.upload_object = AsyncMock()
    return client


@pytest.fixture
def service(mock_deduplicator: MagicMock, mock_r2_client: MagicMock) -> ImageIngestionService:
    """Create ingestion service with mocked dependencies."""
    return ImageIngestionService(
        r2_client=mock_r2_client,
        deduplicator=mock_deduplicator,
        timeout=5.0,
    )


@pytest.fixture
def valid_jpeg_bytes() -> bytes:
    """Create valid JPEG image bytes using PIL."""
    from PIL import Image

    # Create a simple 200x200 red image
    img = Image.new("RGB", (200, 200), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()


@pytest.fixture
def valid_png_bytes() -> bytes:
    """Create valid PNG image bytes using PIL."""
    from PIL import Image

    img = Image.new("RGBA", (300, 300), color="blue")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def small_image_bytes() -> bytes:
    """Create an image that is too small (below MIN_DIMENSION)."""
    from PIL import Image

    img = Image.new("RGB", (50, 50), color="green")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def ingestion_request() -> IngestionRequest:
    """Create a standard ingestion request."""
    return IngestionRequest(
        image_url="https://example.com/product.jpg",
        source=IngestionSource.WOOCOMMERCE,
        product_id="prod_123",
        woocommerce_product_id="wc_456",
        metadata={"color": "red", "size": "large"},
        callback_url="https://example.com/callback",
        correlation_id="test-correlation-id",
    )


# =============================================================================
# Enum Tests
# =============================================================================


class TestIngestionSource:
    """Test IngestionSource enum."""

    def test_woocommerce_value(self) -> None:
        """IngestionSource.WOOCOMMERCE should have correct value."""
        assert IngestionSource.WOOCOMMERCE.value == "woocommerce"

    def test_api_value(self) -> None:
        """IngestionSource.API should have correct value."""
        assert IngestionSource.API.value == "api"

    def test_dashboard_value(self) -> None:
        """IngestionSource.DASHBOARD should have correct value."""
        assert IngestionSource.DASHBOARD.value == "dashboard"

    def test_bulk_import_value(self) -> None:
        """IngestionSource.BULK_IMPORT should have correct value."""
        assert IngestionSource.BULK_IMPORT.value == "bulk_import"


class TestIngestionStatus:
    """Test IngestionStatus enum."""

    def test_pending_value(self) -> None:
        """IngestionStatus.PENDING should have correct value."""
        assert IngestionStatus.PENDING.value == "pending"

    def test_downloading_value(self) -> None:
        """IngestionStatus.DOWNLOADING should have correct value."""
        assert IngestionStatus.DOWNLOADING.value == "downloading"

    def test_validating_value(self) -> None:
        """IngestionStatus.VALIDATING should have correct value."""
        assert IngestionStatus.VALIDATING.value == "validating"

    def test_deduplicating_value(self) -> None:
        """IngestionStatus.DEDUPLICATING should have correct value."""
        assert IngestionStatus.DEDUPLICATING.value == "deduplicating"

    def test_uploading_value(self) -> None:
        """IngestionStatus.UPLOADING should have correct value."""
        assert IngestionStatus.UPLOADING.value == "uploading"

    def test_queuing_value(self) -> None:
        """IngestionStatus.QUEUING should have correct value."""
        assert IngestionStatus.QUEUING.value == "queuing"

    def test_completed_value(self) -> None:
        """IngestionStatus.COMPLETED should have correct value."""
        assert IngestionStatus.COMPLETED.value == "completed"

    def test_failed_value(self) -> None:
        """IngestionStatus.FAILED should have correct value."""
        assert IngestionStatus.FAILED.value == "failed"

    def test_skipped_value(self) -> None:
        """IngestionStatus.SKIPPED should have correct value."""
        assert IngestionStatus.SKIPPED.value == "skipped"


# =============================================================================
# Model Tests
# =============================================================================


class TestIngestionRequest:
    """Test IngestionRequest dataclass."""

    def test_required_fields(self) -> None:
        """Should require image_url and source."""
        request = IngestionRequest(
            image_url="https://example.com/image.jpg",
            source=IngestionSource.API,
        )
        assert request.image_url == "https://example.com/image.jpg"
        assert request.source == IngestionSource.API

    def test_optional_fields_default_values(self) -> None:
        """Optional fields should have correct defaults."""
        request = IngestionRequest(
            image_url="https://example.com/image.jpg",
            source=IngestionSource.API,
        )
        assert request.product_id is None
        assert request.woocommerce_product_id is None
        assert request.metadata == {}
        assert request.callback_url is None
        assert request.skip_dedup_check is False
        assert request.correlation_id is None

    def test_all_fields(self) -> None:
        """Should accept all fields."""
        request = IngestionRequest(
            image_url="https://example.com/image.jpg",
            source=IngestionSource.WOOCOMMERCE,
            product_id="prod_123",
            woocommerce_product_id="wc_456",
            metadata={"key": "value"},
            callback_url="https://callback.com",
            skip_dedup_check=True,
            correlation_id="corr-123",
        )
        assert request.product_id == "prod_123"
        assert request.woocommerce_product_id == "wc_456"
        assert request.metadata == {"key": "value"}
        assert request.callback_url == "https://callback.com"
        assert request.skip_dedup_check is True
        assert request.correlation_id == "corr-123"


class TestIngestionResult:
    """Test IngestionResult dataclass."""

    def test_default_values(self) -> None:
        """Should have correct default values."""
        result = IngestionResult(status=IngestionStatus.PENDING)
        assert result.status == IngestionStatus.PENDING
        assert result.job_id is None
        assert result.asset_id is None
        assert result.original_url is None
        assert result.r2_key is None
        assert result.content_hash is None
        assert result.file_size_bytes == 0
        assert result.width is None
        assert result.height is None
        assert result.mime_type is None
        assert result.is_duplicate is False
        assert result.duplicate_asset_id is None
        assert result.error_message is None
        assert result.completed_at is None
        assert isinstance(result.started_at, datetime)

    def test_completed_result(self) -> None:
        """Should store completed result values."""
        result = IngestionResult(
            status=IngestionStatus.COMPLETED,
            job_id="job_123",
            asset_id="asset_456",
            original_url="https://example.com/img.jpg",
            r2_key="originals/asset_456/original.jpg",
            content_hash="abc123",
            file_size_bytes=1024,
            width=200,
            height=200,
            mime_type="image/jpeg",
        )
        assert result.job_id == "job_123"
        assert result.asset_id == "asset_456"
        assert result.file_size_bytes == 1024


class TestImageValidationError:
    """Test ImageValidationError exception."""

    def test_message(self) -> None:
        """Should store error message."""
        error = ImageValidationError("Invalid format")
        assert str(error) == "Invalid format"

    def test_correlation_id(self) -> None:
        """Should store correlation ID."""
        error = ImageValidationError("Invalid", correlation_id="corr-123")
        assert error.correlation_id == "corr-123"

    def test_inheritance(self) -> None:
        """Should be an Exception subclass."""
        error = ImageValidationError("Test")
        assert isinstance(error, Exception)


# =============================================================================
# Service Initialization Tests
# =============================================================================


class TestImageIngestionServiceInit:
    """Test ImageIngestionService initialization."""

    def test_default_initialization(self) -> None:
        """Should initialize with defaults."""
        service = ImageIngestionService()
        assert service._r2_client is None
        assert service._timeout == 30.0
        assert service._deduplicator is not None

    def test_custom_timeout(self) -> None:
        """Should accept custom timeout."""
        service = ImageIngestionService(timeout=60.0)
        assert service._timeout == 60.0

    def test_custom_r2_client(self, mock_r2_client: MagicMock) -> None:
        """Should accept custom R2 client."""
        service = ImageIngestionService(r2_client=mock_r2_client)
        assert service._r2_client is mock_r2_client

    def test_custom_deduplicator(self, mock_deduplicator: MagicMock) -> None:
        """Should accept custom deduplicator."""
        service = ImageIngestionService(deduplicator=mock_deduplicator)
        assert service._deduplicator is mock_deduplicator


# =============================================================================
# HTTP Client Tests
# =============================================================================


class TestHTTPClient:
    """Test HTTP client management."""

    @pytest.mark.asyncio
    async def test_get_http_client_creates_client(
        self, service: ImageIngestionService
    ) -> None:
        """Should create HTTP client on first call."""
        assert service._http_client is None
        client = await service._get_http_client()
        assert client is not None
        assert isinstance(client, httpx.AsyncClient)
        await service.close()

    @pytest.mark.asyncio
    async def test_get_http_client_reuses_client(
        self, service: ImageIngestionService
    ) -> None:
        """Should reuse existing HTTP client."""
        client1 = await service._get_http_client()
        client2 = await service._get_http_client()
        assert client1 is client2
        await service.close()

    @pytest.mark.asyncio
    async def test_close_closes_client(
        self, service: ImageIngestionService
    ) -> None:
        """Should close HTTP client."""
        await service._get_http_client()
        assert service._http_client is not None
        await service.close()
        assert service._http_client is None


# =============================================================================
# Download Tests
# =============================================================================


class TestDownloadImage:
    """Test _download_image method."""

    @pytest.mark.asyncio
    async def test_successful_download(
        self,
        service: ImageIngestionService,
        valid_jpeg_bytes: bytes,
    ) -> None:
        """Should download image successfully."""
        with patch.object(service, "_get_http_client") as mock_get_client:
            mock_response = MagicMock()
            mock_response.content = valid_jpeg_bytes
            mock_response.headers = {"content-type": "image/jpeg"}
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            content = await service._download_image("https://example.com/img.jpg")

            assert content == valid_jpeg_bytes
            mock_client.get.assert_called_once_with("https://example.com/img.jpg")

    @pytest.mark.asyncio
    async def test_download_invalid_content_type(
        self,
        service: ImageIngestionService,
    ) -> None:
        """Should reject invalid content type."""
        with patch.object(service, "_get_http_client") as mock_get_client:
            mock_response = MagicMock()
            mock_response.content = b"not an image"
            mock_response.headers = {"content-type": "text/html"}
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with pytest.raises(ImageValidationError) as exc_info:
                await service._download_image("https://example.com/page.html")

            assert "Invalid content type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_download_file_too_large(
        self,
        service: ImageIngestionService,
    ) -> None:
        """Should reject files exceeding size limit."""
        with patch.object(service, "_get_http_client") as mock_get_client:
            # Create content larger than MAX_FILE_SIZE_BYTES
            large_content = b"x" * (MAX_FILE_SIZE_BYTES + 1)

            mock_response = MagicMock()
            mock_response.content = large_content
            mock_response.headers = {"content-type": "image/jpeg"}
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with pytest.raises(ImageValidationError) as exc_info:
                await service._download_image("https://example.com/large.jpg")

            assert "File too large" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_download_empty_file(
        self,
        service: ImageIngestionService,
    ) -> None:
        """Should reject empty files."""
        with patch.object(service, "_get_http_client") as mock_get_client:
            mock_response = MagicMock()
            mock_response.content = b""
            mock_response.headers = {"content-type": "image/jpeg"}
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with pytest.raises(ImageValidationError) as exc_info:
                await service._download_image("https://example.com/empty.jpg")

            assert "Empty file" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_download_http_error(
        self,
        service: ImageIngestionService,
    ) -> None:
        """Should handle HTTP errors."""
        with patch.object(service, "_get_http_client") as mock_get_client:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.reason_phrase = "Not Found"

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Not Found",
                    request=MagicMock(),
                    response=mock_response,
                )
            )
            mock_get_client.return_value = mock_client

            with pytest.raises(ImageValidationError) as exc_info:
                await service._download_image("https://example.com/missing.jpg")

            assert "HTTP 404" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_download_no_content_type_header(
        self,
        service: ImageIngestionService,
        valid_jpeg_bytes: bytes,
    ) -> None:
        """Should accept images without content-type header."""
        with patch.object(service, "_get_http_client") as mock_get_client:
            mock_response = MagicMock()
            mock_response.content = valid_jpeg_bytes
            mock_response.headers = {}  # No content-type
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            # Should not raise since no content-type to validate
            content = await service._download_image("https://example.com/img.jpg")
            assert content == valid_jpeg_bytes


# =============================================================================
# Validation Tests
# =============================================================================


class TestValidateImage:
    """Test _validate_image method."""

    @pytest.mark.asyncio
    async def test_validate_valid_jpeg(
        self,
        service: ImageIngestionService,
        valid_jpeg_bytes: bytes,
    ) -> None:
        """Should validate valid JPEG image."""
        result = await service._validate_image(valid_jpeg_bytes)

        assert result["width"] == 200
        assert result["height"] == 200
        assert result["mime_type"] == "image/jpeg"
        assert result["format"] == "JPEG"

    @pytest.mark.asyncio
    async def test_validate_valid_png(
        self,
        service: ImageIngestionService,
        valid_png_bytes: bytes,
    ) -> None:
        """Should validate valid PNG image."""
        result = await service._validate_image(valid_png_bytes)

        assert result["width"] == 300
        assert result["height"] == 300
        assert result["mime_type"] == "image/png"
        assert result["format"] == "PNG"

    @pytest.mark.asyncio
    async def test_validate_image_too_small(
        self,
        service: ImageIngestionService,
        small_image_bytes: bytes,
    ) -> None:
        """Should reject images below minimum dimensions."""
        with pytest.raises(ImageValidationError) as exc_info:
            await service._validate_image(small_image_bytes)

        assert "Image too small" in str(exc_info.value)
        assert f"min {MIN_DIMENSION}" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_image_too_large(
        self,
        service: ImageIngestionService,
    ) -> None:
        """Should reject images above maximum dimensions."""
        from PIL import Image

        # Create an image larger than MAX_DIMENSION
        img = Image.new("RGB", (MAX_DIMENSION + 100, MAX_DIMENSION + 100), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=50)
        large_image_bytes = buffer.getvalue()

        with pytest.raises(ImageValidationError) as exc_info:
            await service._validate_image(large_image_bytes)

        assert "Image too large" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_invalid_image_data(
        self,
        service: ImageIngestionService,
    ) -> None:
        """Should reject invalid image data."""
        with pytest.raises(ImageValidationError) as exc_info:
            await service._validate_image(b"not an image at all")

        assert "Invalid image file" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_webp_image(
        self,
        service: ImageIngestionService,
    ) -> None:
        """Should validate WEBP images."""
        from PIL import Image

        img = Image.new("RGB", (200, 200), color="purple")
        buffer = io.BytesIO()
        img.save(buffer, format="WEBP")
        webp_bytes = buffer.getvalue()

        result = await service._validate_image(webp_bytes)

        assert result["mime_type"] == "image/webp"
        assert result["format"] == "WEBP"

    @pytest.mark.asyncio
    async def test_validate_unsupported_format(
        self,
        service: ImageIngestionService,
    ) -> None:
        """Should reject unsupported image formats like BMP."""
        from PIL import Image

        # BMP format is recognized by PIL but not in our ALLOWED_MIME_TYPES
        img = Image.new("RGB", (200, 200), color="yellow")
        buffer = io.BytesIO()
        img.save(buffer, format="BMP")
        bmp_bytes = buffer.getvalue()

        with pytest.raises(ImageValidationError) as exc_info:
            await service._validate_image(bmp_bytes)

        assert "Unsupported format" in str(exc_info.value)


# =============================================================================
# Upload Tests
# =============================================================================


class TestUploadToR2:
    """Test _upload_to_r2 method."""

    @pytest.mark.asyncio
    async def test_upload_jpeg(
        self,
        service: ImageIngestionService,
        mock_r2_client: MagicMock,
        valid_jpeg_bytes: bytes,
    ) -> None:
        """Should upload JPEG with correct key."""
        r2_key = await service._upload_to_r2(
            content=valid_jpeg_bytes,
            asset_id="asset_123",
            mime_type="image/jpeg",
            correlation_id="corr-123",
        )

        assert r2_key == "originals/asset_123/original.jpg"
        mock_r2_client.upload_object.assert_called_once_with(
            key="originals/asset_123/original.jpg",
            content=valid_jpeg_bytes,
            content_type="image/jpeg",
            correlation_id="corr-123",
        )

    @pytest.mark.asyncio
    async def test_upload_png(
        self,
        service: ImageIngestionService,
        mock_r2_client: MagicMock,
        valid_png_bytes: bytes,
    ) -> None:
        """Should upload PNG with correct extension."""
        r2_key = await service._upload_to_r2(
            content=valid_png_bytes,
            asset_id="asset_456",
            mime_type="image/png",
        )

        assert r2_key == "originals/asset_456/original.png"

    @pytest.mark.asyncio
    async def test_upload_webp(
        self,
        service: ImageIngestionService,
        mock_r2_client: MagicMock,
    ) -> None:
        """Should upload WEBP with correct extension."""
        r2_key = await service._upload_to_r2(
            content=b"webp content",
            asset_id="asset_789",
            mime_type="image/webp",
        )

        assert r2_key == "originals/asset_789/original.webp"

    @pytest.mark.asyncio
    async def test_upload_unknown_mime_type(
        self,
        service: ImageIngestionService,
        mock_r2_client: MagicMock,
    ) -> None:
        """Should use .bin extension for unknown MIME types."""
        r2_key = await service._upload_to_r2(
            content=b"unknown content",
            asset_id="asset_000",
            mime_type="application/octet-stream",
        )

        assert r2_key == "originals/asset_000/original.bin"

    @pytest.mark.asyncio
    async def test_upload_without_r2_client(
        self,
        mock_deduplicator: MagicMock,
    ) -> None:
        """Should handle mock upload when no R2 client."""
        service = ImageIngestionService(
            r2_client=None,
            deduplicator=mock_deduplicator,
        )

        r2_key = await service._upload_to_r2(
            content=b"test content",
            asset_id="asset_mock",
            mime_type="image/jpeg",
        )

        assert r2_key == "originals/asset_mock/original.jpg"


# =============================================================================
# Queue Tests
# =============================================================================


class TestQueueForProcessing:
    """Test _queue_for_processing method."""

    @pytest.mark.asyncio
    async def test_queue_returns_job_id(
        self,
        service: ImageIngestionService,
    ) -> None:
        """Should return a job ID."""
        job_id = await service._queue_for_processing(
            asset_id="asset_123",
            r2_key="originals/asset_123/original.jpg",
            source=IngestionSource.WOOCOMMERCE,
            product_id="prod_123",
            woocommerce_product_id="wc_456",
            metadata={"color": "red"},
            callback_url="https://example.com/callback",
            correlation_id="corr-123",
        )

        assert job_id is not None
        assert len(job_id) > 0
        # UUID format check
        assert len(job_id) == 36

    @pytest.mark.asyncio
    async def test_queue_with_optional_fields(
        self,
        service: ImageIngestionService,
    ) -> None:
        """Should handle optional fields."""
        job_id = await service._queue_for_processing(
            asset_id="asset_123",
            r2_key="originals/asset_123/original.jpg",
            source=IngestionSource.API,
            product_id=None,
            woocommerce_product_id=None,
            metadata={},
            callback_url=None,
        )

        assert job_id is not None


# =============================================================================
# Full Ingestion Flow Tests
# =============================================================================


class TestIngest:
    """Test full ingest method."""

    @pytest.mark.asyncio
    async def test_successful_ingestion(
        self,
        service: ImageIngestionService,
        mock_deduplicator: MagicMock,
        mock_r2_client: MagicMock,
        valid_jpeg_bytes: bytes,
        ingestion_request: IngestionRequest,
    ) -> None:
        """Should complete full ingestion successfully."""
        with patch.object(service, "_download_image", return_value=valid_jpeg_bytes):
            result = await service.ingest(ingestion_request)

        assert result.status == IngestionStatus.COMPLETED
        assert result.original_url == ingestion_request.image_url
        assert result.asset_id is not None
        assert result.job_id is not None
        assert result.r2_key is not None
        assert result.file_size_bytes == len(valid_jpeg_bytes)
        assert result.width == 200
        assert result.height == 200
        assert result.mime_type == "image/jpeg"
        assert result.is_duplicate is False
        assert result.completed_at is not None

        # Verify deduplicator was called
        mock_deduplicator.compute_hash.assert_called_once_with(valid_jpeg_bytes)
        mock_deduplicator.check_duplicate.assert_called_once()
        mock_deduplicator.register_hash.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingestion_duplicate_detected(
        self,
        service: ImageIngestionService,
        mock_deduplicator: MagicMock,
        valid_jpeg_bytes: bytes,
        ingestion_request: IngestionRequest,
    ) -> None:
        """Should skip ingestion when duplicate detected."""
        from services.image_deduplication import DuplicateCheckResult

        # Configure deduplicator to return duplicate
        async def return_duplicate(*args, **kwargs):
            return DuplicateCheckResult(
                is_duplicate=True,
                existing_asset_id="existing_asset_123",
                existing_version=1,
                hash_match="abc123hash",
            )

        mock_deduplicator.check_duplicate = AsyncMock(side_effect=return_duplicate)

        with patch.object(service, "_download_image", return_value=valid_jpeg_bytes):
            result = await service.ingest(ingestion_request)

        assert result.status == IngestionStatus.SKIPPED
        assert result.is_duplicate is True
        assert result.duplicate_asset_id == "existing_asset_123"
        assert result.completed_at is not None

        # R2 upload should NOT have been called
        service._r2_client.upload_object.assert_not_called()

    @pytest.mark.asyncio
    async def test_ingestion_skip_dedup_check(
        self,
        service: ImageIngestionService,
        mock_deduplicator: MagicMock,
        mock_r2_client: MagicMock,
        valid_jpeg_bytes: bytes,
    ) -> None:
        """Should skip dedup check when requested."""
        request = IngestionRequest(
            image_url="https://example.com/img.jpg",
            source=IngestionSource.API,
            skip_dedup_check=True,
        )

        with patch.object(service, "_download_image", return_value=valid_jpeg_bytes):
            result = await service.ingest(request)

        assert result.status == IngestionStatus.COMPLETED
        # check_duplicate should NOT have been called
        mock_deduplicator.check_duplicate.assert_not_called()

    @pytest.mark.asyncio
    async def test_ingestion_download_failure(
        self,
        service: ImageIngestionService,
        ingestion_request: IngestionRequest,
    ) -> None:
        """Should handle download failures."""
        with patch.object(
            service,
            "_download_image",
            side_effect=ImageValidationError("Download failed: HTTP 404"),
        ):
            result = await service.ingest(ingestion_request)

        assert result.status == IngestionStatus.FAILED
        assert "Download failed" in result.error_message
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_ingestion_validation_failure(
        self,
        service: ImageIngestionService,
        small_image_bytes: bytes,
        ingestion_request: IngestionRequest,
    ) -> None:
        """Should handle validation failures."""
        with patch.object(service, "_download_image", return_value=small_image_bytes):
            result = await service.ingest(ingestion_request)

        assert result.status == IngestionStatus.FAILED
        assert "Image too small" in result.error_message

    @pytest.mark.asyncio
    async def test_ingestion_http_error(
        self,
        service: ImageIngestionService,
        ingestion_request: IngestionRequest,
    ) -> None:
        """Should handle HTTP errors during download."""
        with patch.object(
            service,
            "_download_image",
            side_effect=httpx.HTTPError("Connection timeout"),
        ):
            result = await service.ingest(ingestion_request)

        assert result.status == IngestionStatus.FAILED
        assert "Download failed" in result.error_message

    @pytest.mark.asyncio
    async def test_ingestion_unexpected_error(
        self,
        service: ImageIngestionService,
        ingestion_request: IngestionRequest,
    ) -> None:
        """Should handle unexpected errors."""
        with patch.object(
            service,
            "_download_image",
            side_effect=RuntimeError("Unexpected system error"),
        ):
            result = await service.ingest(ingestion_request)

        assert result.status == IngestionStatus.FAILED
        assert "Unexpected error" in result.error_message

    @pytest.mark.asyncio
    async def test_ingestion_generates_correlation_id(
        self,
        service: ImageIngestionService,
        valid_jpeg_bytes: bytes,
    ) -> None:
        """Should generate correlation ID if not provided."""
        request = IngestionRequest(
            image_url="https://example.com/img.jpg",
            source=IngestionSource.API,
            correlation_id=None,
        )

        with patch.object(service, "_download_image", return_value=valid_jpeg_bytes):
            result = await service.ingest(request)

        assert result.status == IngestionStatus.COMPLETED


# =============================================================================
# Batch Ingestion Tests
# =============================================================================


class TestIngestBatch:
    """Test batch ingestion functionality."""

    @pytest.mark.asyncio
    async def test_batch_ingestion_success(
        self,
        service: ImageIngestionService,
        valid_jpeg_bytes: bytes,
    ) -> None:
        """Should process multiple images concurrently."""
        requests = [
            IngestionRequest(
                image_url=f"https://example.com/img{i}.jpg",
                source=IngestionSource.BULK_IMPORT,
            )
            for i in range(3)
        ]

        with patch.object(service, "_download_image", return_value=valid_jpeg_bytes):
            results = await service.ingest_batch(requests, max_concurrent=2)

        assert len(results) == 3
        assert all(r.status == IngestionStatus.COMPLETED for r in results)

    @pytest.mark.asyncio
    async def test_batch_ingestion_partial_failure(
        self,
        service: ImageIngestionService,
        valid_jpeg_bytes: bytes,
    ) -> None:
        """Should handle partial failures in batch."""
        requests = [
            IngestionRequest(
                image_url=f"https://example.com/img{i}.jpg",
                source=IngestionSource.BULK_IMPORT,
            )
            for i in range(3)
        ]

        call_count = 0

        async def download_with_failure(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise ImageValidationError("Download failed")
            return valid_jpeg_bytes

        with patch.object(service, "_download_image", side_effect=download_with_failure):
            results = await service.ingest_batch(requests, max_concurrent=1)

        assert len(results) == 3
        completed_count = sum(1 for r in results if r.status == IngestionStatus.COMPLETED)
        failed_count = sum(1 for r in results if r.status == IngestionStatus.FAILED)
        assert completed_count == 2
        assert failed_count == 1

    @pytest.mark.asyncio
    async def test_batch_ingestion_empty_list(
        self,
        service: ImageIngestionService,
    ) -> None:
        """Should handle empty batch."""
        results = await service.ingest_batch([])
        assert results == []

    @pytest.mark.asyncio
    async def test_batch_ingestion_respects_concurrency(
        self,
        service: ImageIngestionService,
        valid_jpeg_bytes: bytes,
    ) -> None:
        """Should respect max_concurrent limit."""
        import asyncio

        active_count = 0
        max_active = 0

        async def track_concurrency(url, **kwargs):
            nonlocal active_count, max_active
            active_count += 1
            max_active = max(max_active, active_count)
            await asyncio.sleep(0.01)  # Small delay to test concurrency
            active_count -= 1
            return valid_jpeg_bytes

        requests = [
            IngestionRequest(
                image_url=f"https://example.com/img{i}.jpg",
                source=IngestionSource.BULK_IMPORT,
            )
            for i in range(10)
        ]

        with patch.object(service, "_download_image", side_effect=track_concurrency):
            await service.ingest_batch(requests, max_concurrent=3)

        assert max_active <= 3


# =============================================================================
# Singleton Tests
# =============================================================================


class TestGetIngestionService:
    """Test singleton getter."""

    def test_returns_service(self) -> None:
        """Should return an ImageIngestionService instance."""
        # Reset singleton for test
        import services.image_ingestion as module

        module._ingestion_service = None

        service = get_ingestion_service()
        assert isinstance(service, ImageIngestionService)

    def test_returns_same_instance(self) -> None:
        """Should return the same instance on subsequent calls."""
        import services.image_ingestion as module

        module._ingestion_service = None

        service1 = get_ingestion_service()
        service2 = get_ingestion_service()
        assert service1 is service2


# =============================================================================
# Constants Tests
# =============================================================================


class TestConstants:
    """Test module constants."""

    def test_allowed_mime_types(self) -> None:
        """Should have expected MIME types."""
        assert "image/jpeg" in ALLOWED_MIME_TYPES
        assert "image/png" in ALLOWED_MIME_TYPES
        assert "image/webp" in ALLOWED_MIME_TYPES
        assert "image/gif" in ALLOWED_MIME_TYPES
        assert "image/tiff" in ALLOWED_MIME_TYPES
        assert "text/html" not in ALLOWED_MIME_TYPES

    def test_max_file_size(self) -> None:
        """Should have 50MB max file size."""
        assert MAX_FILE_SIZE_BYTES == 50 * 1024 * 1024

    def test_dimension_limits(self) -> None:
        """Should have expected dimension limits."""
        assert MIN_DIMENSION == 100
        assert MAX_DIMENSION == 10000
