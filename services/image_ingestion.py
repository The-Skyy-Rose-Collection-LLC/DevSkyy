# services/image_ingestion.py
"""Image ingestion service for downloading and processing images.

Implements US-003: WooCommerce auto-ingestion webhook.

Features:
- Download images from URLs with validation
- Validate image format and dimensions
- Upload to R2 storage
- Queue for ML processing pipeline

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import io
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import httpx

from services.image_deduplication import (
    DuplicateCheckResult,
    HashAlgorithm,
    HashResult,
    ImageDeduplicator,
    get_deduplicator,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/tiff",
}

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".tiff", ".tif"}

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB
MIN_DIMENSION = 100  # Minimum image dimension
MAX_DIMENSION = 10000  # Maximum image dimension


# =============================================================================
# Enums
# =============================================================================


class IngestionSource(str, Enum):
    """Source of ingested images."""

    WOOCOMMERCE = "woocommerce"
    API = "api"
    DASHBOARD = "dashboard"
    BULK_IMPORT = "bulk_import"


class IngestionStatus(str, Enum):
    """Status of ingestion operation."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    VALIDATING = "validating"
    DEDUPLICATING = "deduplicating"
    UPLOADING = "uploading"
    QUEUING = "queuing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"  # Duplicate found


# =============================================================================
# Models
# =============================================================================


@dataclass
class IngestionRequest:
    """Request to ingest an image."""

    image_url: str
    source: IngestionSource
    product_id: str | None = None
    woocommerce_product_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    callback_url: str | None = None
    skip_dedup_check: bool = False
    correlation_id: str | None = None


@dataclass
class IngestionResult:
    """Result of image ingestion."""

    status: IngestionStatus
    job_id: str | None = None
    asset_id: str | None = None
    original_url: str | None = None
    r2_key: str | None = None
    content_hash: str | None = None
    file_size_bytes: int = 0
    width: int | None = None
    height: int | None = None
    mime_type: str | None = None

    # Deduplication
    is_duplicate: bool = False
    duplicate_asset_id: str | None = None

    # Error info
    error_message: str | None = None

    # Timestamps
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None


class ImageValidationError(Exception):
    """Raised when image validation fails."""

    def __init__(self, message: str, *, correlation_id: str | None = None):
        self.correlation_id = correlation_id
        super().__init__(message)


# =============================================================================
# Ingestion Service
# =============================================================================


class ImageIngestionService:
    """Service for downloading, validating, and ingesting images.

    Features:
    - Downloads images from URLs with timeout and size limits
    - Validates image format, dimensions, and content
    - Checks for duplicates before processing
    - Uploads to R2 storage
    - Queues for ML processing pipeline

    Usage:
        service = ImageIngestionService()

        result = await service.ingest(IngestionRequest(
            image_url="https://example.com/product.jpg",
            source=IngestionSource.WOOCOMMERCE,
            product_id="prod_123",
        ))

        if result.status == IngestionStatus.COMPLETED:
            print(f"Ingested as job {result.job_id}")
    """

    def __init__(
        self,
        *,
        r2_client: Any | None = None,
        deduplicator: ImageDeduplicator | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize ingestion service.

        Args:
            r2_client: R2 storage client (optional, for testing)
            deduplicator: Image deduplicator (optional)
            timeout: HTTP timeout for downloads
        """
        self._r2_client = r2_client
        self._deduplicator = deduplicator or get_deduplicator()
        self._timeout = timeout
        self._http_client: httpx.AsyncClient | None = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": "DevSkyy-ImageIngestion/1.0",
                },
            )
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def ingest(self, request: IngestionRequest) -> IngestionResult:
        """Ingest an image from a URL.

        Args:
            request: Ingestion request with image URL and metadata

        Returns:
            IngestionResult with status and details
        """
        correlation_id = request.correlation_id or str(uuid.uuid4())
        result = IngestionResult(
            original_url=request.image_url,
            status=IngestionStatus.PENDING,
        )

        logger.info(
            f"Starting ingestion from {request.source.value}",
            extra={
                "url": request.image_url,
                "product_id": request.product_id,
                "correlation_id": correlation_id,
            },
        )

        try:
            # Step 1: Download image
            result.status = IngestionStatus.DOWNLOADING
            content = await self._download_image(
                request.image_url,
                correlation_id=correlation_id,
            )
            result.file_size_bytes = len(content)

            # Step 2: Validate image
            result.status = IngestionStatus.VALIDATING
            validation = await self._validate_image(
                content,
                correlation_id=correlation_id,
            )
            result.width = validation["width"]
            result.height = validation["height"]
            result.mime_type = validation["mime_type"]

            # Step 3: Compute hash and check for duplicates
            result.status = IngestionStatus.DEDUPLICATING
            hash_result = self._deduplicator.compute_hash(content)
            result.content_hash = hash_result.content_hash

            if not request.skip_dedup_check:
                dedup_result = await self._deduplicator.check_duplicate(
                    hash_result.content_hash,
                    correlation_id=correlation_id,
                )

                if dedup_result.is_duplicate:
                    result.status = IngestionStatus.SKIPPED
                    result.is_duplicate = True
                    result.duplicate_asset_id = dedup_result.existing_asset_id
                    result.completed_at = datetime.now(UTC)

                    logger.info(
                        f"Skipped duplicate image",
                        extra={
                            "existing_asset": dedup_result.existing_asset_id,
                            "correlation_id": correlation_id,
                        },
                    )
                    return result

            # Step 4: Upload to R2
            result.status = IngestionStatus.UPLOADING
            asset_id = str(uuid.uuid4())
            r2_key = await self._upload_to_r2(
                content=content,
                asset_id=asset_id,
                mime_type=result.mime_type,
                correlation_id=correlation_id,
            )
            result.asset_id = asset_id
            result.r2_key = r2_key

            # Step 5: Register hash for future dedup
            await self._deduplicator.register_hash(
                content_hash=hash_result.content_hash,
                asset_id=asset_id,
                version=1,
                correlation_id=correlation_id,
            )

            # Step 6: Queue for ML processing
            result.status = IngestionStatus.QUEUING
            job_id = await self._queue_for_processing(
                asset_id=asset_id,
                r2_key=r2_key,
                source=request.source,
                product_id=request.product_id,
                woocommerce_product_id=request.woocommerce_product_id,
                metadata=request.metadata,
                callback_url=request.callback_url,
                correlation_id=correlation_id,
            )
            result.job_id = job_id

            # Complete
            result.status = IngestionStatus.COMPLETED
            result.completed_at = datetime.now(UTC)

            logger.info(
                f"Ingestion completed",
                extra={
                    "job_id": job_id,
                    "asset_id": asset_id,
                    "correlation_id": correlation_id,
                },
            )

        except ImageValidationError as e:
            result.status = IngestionStatus.FAILED
            result.error_message = str(e)
            result.completed_at = datetime.now(UTC)
            logger.error(
                f"Validation failed: {e}",
                extra={"correlation_id": correlation_id},
            )

        except httpx.HTTPError as e:
            result.status = IngestionStatus.FAILED
            result.error_message = f"Download failed: {e}"
            result.completed_at = datetime.now(UTC)
            logger.error(
                f"Download failed: {e}",
                extra={"correlation_id": correlation_id},
            )

        except Exception as e:
            result.status = IngestionStatus.FAILED
            result.error_message = f"Unexpected error: {e}"
            result.completed_at = datetime.now(UTC)
            logger.exception(
                f"Ingestion failed: {e}",
                extra={"correlation_id": correlation_id},
            )

        return result

    async def _download_image(
        self,
        url: str,
        *,
        correlation_id: str | None = None,
    ) -> bytes:
        """Download image from URL.

        Args:
            url: Image URL
            correlation_id: Optional correlation ID

        Returns:
            Image content bytes

        Raises:
            ImageValidationError: If download fails or content invalid
        """
        client = await self._get_http_client()

        try:
            response = await client.get(url)
            response.raise_for_status()

            content = response.content

            # Check content type
            content_type = response.headers.get("content-type", "").split(";")[0].strip()
            if content_type and content_type not in ALLOWED_MIME_TYPES:
                raise ImageValidationError(
                    f"Invalid content type: {content_type}",
                    correlation_id=correlation_id,
                )

            # Check size
            if len(content) > MAX_FILE_SIZE_BYTES:
                raise ImageValidationError(
                    f"File too large: {len(content)} bytes (max {MAX_FILE_SIZE_BYTES})",
                    correlation_id=correlation_id,
                )

            if len(content) == 0:
                raise ImageValidationError(
                    "Empty file downloaded",
                    correlation_id=correlation_id,
                )

            return content

        except httpx.HTTPStatusError as e:
            raise ImageValidationError(
                f"HTTP {e.response.status_code}: {e.response.reason_phrase}",
                correlation_id=correlation_id,
            )

    async def _validate_image(
        self,
        content: bytes,
        *,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Validate image content.

        Args:
            content: Image bytes
            correlation_id: Optional correlation ID

        Returns:
            Dict with width, height, mime_type

        Raises:
            ImageValidationError: If validation fails
        """
        try:
            from PIL import Image

            img = Image.open(io.BytesIO(content))
            width, height = img.size

            # Check dimensions
            if width < MIN_DIMENSION or height < MIN_DIMENSION:
                raise ImageValidationError(
                    f"Image too small: {width}x{height} (min {MIN_DIMENSION}x{MIN_DIMENSION})",
                    correlation_id=correlation_id,
                )

            if width > MAX_DIMENSION or height > MAX_DIMENSION:
                raise ImageValidationError(
                    f"Image too large: {width}x{height} (max {MAX_DIMENSION}x{MAX_DIMENSION})",
                    correlation_id=correlation_id,
                )

            # Get MIME type
            mime_map = {
                "JPEG": "image/jpeg",
                "PNG": "image/png",
                "WEBP": "image/webp",
                "GIF": "image/gif",
                "TIFF": "image/tiff",
            }
            mime_type = mime_map.get(img.format, "application/octet-stream")

            if mime_type not in ALLOWED_MIME_TYPES:
                raise ImageValidationError(
                    f"Unsupported format: {img.format}",
                    correlation_id=correlation_id,
                )

            return {
                "width": width,
                "height": height,
                "mime_type": mime_type,
                "format": img.format,
            }

        except ImageValidationError:
            raise
        except Exception as e:
            raise ImageValidationError(
                f"Invalid image file: {e}",
                correlation_id=correlation_id,
            )

    async def _upload_to_r2(
        self,
        content: bytes,
        asset_id: str,
        mime_type: str,
        *,
        correlation_id: str | None = None,
    ) -> str:
        """Upload image to R2 storage.

        Args:
            content: Image bytes
            asset_id: Asset identifier
            mime_type: MIME type
            correlation_id: Optional correlation ID

        Returns:
            R2 storage key
        """
        # Generate extension from MIME type
        ext_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/gif": ".gif",
            "image/tiff": ".tiff",
        }
        ext = ext_map.get(mime_type, ".bin")

        r2_key = f"originals/{asset_id}/original{ext}"

        if self._r2_client:
            await self._r2_client.upload_object(
                key=r2_key,
                content=content,
                content_type=mime_type,
                correlation_id=correlation_id,
            )
        else:
            # Mock upload for testing
            logger.debug(
                f"Mock upload to R2: {r2_key}",
                extra={"correlation_id": correlation_id},
            )

        return r2_key

    async def _queue_for_processing(
        self,
        asset_id: str,
        r2_key: str,
        source: IngestionSource,
        product_id: str | None,
        woocommerce_product_id: str | None,
        metadata: dict[str, Any],
        callback_url: str | None,
        *,
        correlation_id: str | None = None,
    ) -> str:
        """Queue image for ML processing.

        Args:
            asset_id: Asset identifier
            r2_key: R2 storage key
            source: Ingestion source
            product_id: Optional product ID
            woocommerce_product_id: Optional WooCommerce ID
            metadata: Additional metadata
            callback_url: Optional callback URL
            correlation_id: Optional correlation ID

        Returns:
            Processing job ID
        """
        job_id = str(uuid.uuid4())

        # TODO: Integrate with actual ProcessingQueue
        # await processing_queue.submit_job(
        #     job_id=job_id,
        #     asset_id=asset_id,
        #     r2_key=r2_key,
        #     source=source.value,
        #     product_id=product_id,
        #     woocommerce_product_id=woocommerce_product_id,
        #     metadata=metadata,
        #     callback_url=callback_url,
        # )

        logger.info(
            f"Queued job {job_id} for processing",
            extra={
                "asset_id": asset_id,
                "source": source.value,
                "correlation_id": correlation_id,
            },
        )

        return job_id

    async def ingest_batch(
        self,
        requests: list[IngestionRequest],
        *,
        max_concurrent: int = 5,
    ) -> list[IngestionResult]:
        """Ingest multiple images concurrently.

        Args:
            requests: List of ingestion requests
            max_concurrent: Maximum concurrent downloads

        Returns:
            List of ingestion results
        """
        import asyncio

        semaphore = asyncio.Semaphore(max_concurrent)

        async def _ingest_with_semaphore(req: IngestionRequest) -> IngestionResult:
            async with semaphore:
                return await self.ingest(req)

        results = await asyncio.gather(
            *[_ingest_with_semaphore(req) for req in requests],
            return_exceptions=False,
        )

        return results


# Module singleton
_ingestion_service: ImageIngestionService | None = None


def get_ingestion_service() -> ImageIngestionService:
    """Get or create the image ingestion service singleton."""
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = ImageIngestionService()
    return _ingestion_service


__all__ = [
    "IngestionSource",
    "IngestionStatus",
    "IngestionRequest",
    "IngestionResult",
    "ImageValidationError",
    "ImageIngestionService",
    "get_ingestion_service",
]
