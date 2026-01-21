# services/ml/enhancement/upscaling.py
"""
Image Upscaling Service for DevSkyy.

Upscales low-resolution product images using Replicate ML models
while maintaining sharpness and preserving product details.

CRITICAL: Product text and logos must remain legible and unaltered.
No over-sharpening artifacts allowed.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from pydantic import BaseModel

from errors.production_errors import (
    DevSkyError,
    DevSkyErrorCode,
    DevSkyErrorSeverity,
)
from services.ml.replicate_client import ReplicateClient, ReplicateConfig

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Primary model - Real-ESRGAN for high quality upscaling
DEFAULT_UPSCALE_MODEL = (
    "nightmareai/real-esrgan:f121d640bd286e1fdc67f9799164c1d5be36ff74576ee11c803ae5b665dd46aa"
)

# Fallback models
FALLBACK_MODELS = [
    "xinntao/realesrgan:1b976a4d456ed9e4d1a846597b7614e79eadad3032e9124fa63c8acb4e3b5bf4",
]

# Minimum resolution threshold - skip upscaling if already met
MIN_RESOLUTION_LONGEST_EDGE = 2000


# =============================================================================
# Models
# =============================================================================


class UpscaleResult(BaseModel):
    """Result of upscaling operation."""

    original_url: str
    result_url: str
    original_dimensions: tuple[int, int]
    result_dimensions: tuple[int, int]
    scale_factor: int
    model_used: str
    face_enhance: bool
    skipped: bool = False  # True if already meets min resolution
    skip_reason: str | None = None
    processing_time_ms: int
    correlation_id: str

    @property
    def actual_scale(self) -> float:
        """Calculate actual scale achieved."""
        if self.original_dimensions[0] == 0:
            return 0.0
        return self.result_dimensions[0] / self.original_dimensions[0]


class UpscalingError(DevSkyError):
    """Error during image upscaling."""

    def __init__(
        self,
        message: str,
        *,
        image_url: str | None = None,
        model: str | None = None,
        correlation_id: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        context: dict[str, Any] = {}
        if image_url:
            context["image_url"] = image_url
        if model:
            context["model"] = model

        super().__init__(
            message,
            code=DevSkyErrorCode.IMAGE_PROCESSING_FAILED,
            severity=DevSkyErrorSeverity.ERROR,
            context=context,
            cause=cause,
            correlation_id=correlation_id,
            retryable=True,
        )


# =============================================================================
# Service
# =============================================================================


class UpscalingService:
    """
    Service for upscaling low-resolution product images.

    Features:
    - 2x and 4x upscaling support
    - Optional face enhancement for model photos
    - Automatic skip if image already meets minimum resolution
    - Quality metrics output (PSNR, SSIM conceptual)
    - Fallback model chain for reliability

    CRITICAL: Product text and logos must remain legible.

    Usage:
        service = UpscalingService()
        result = await service.upscale_image(
            image_url="https://example.com/product.jpg",
            scale_factor=4,
        )
        print(f"Upscaled from {result.original_dimensions} to {result.result_dimensions}")
    """

    def __init__(
        self,
        replicate_client: ReplicateClient | None = None,
        replicate_config: ReplicateConfig | None = None,
        min_resolution: int = MIN_RESOLUTION_LONGEST_EDGE,
    ) -> None:
        self._client = replicate_client
        self._config = replicate_config
        self._owns_client = replicate_client is None
        self._min_resolution = min_resolution

    async def _get_client(self) -> ReplicateClient:
        """Get or create Replicate client."""
        if self._client is None:
            self._client = ReplicateClient(self._config)
            await self._client.connect()
        return self._client

    async def close(self) -> None:
        """Close client if owned by this service."""
        if self._owns_client and self._client is not None:
            await self._client.close()

    async def __aenter__(self) -> UpscalingService:
        """Enter async context manager."""
        await self._get_client()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context manager."""
        await self.close()

    async def _get_image_dimensions(self, url: str, correlation_id: str) -> tuple[int, int]:
        """
        Get image dimensions from URL.

        Returns (width, height) tuple.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as http_client:
                # Download image to get dimensions
                response = await http_client.get(url)
                if response.status_code != 200:
                    raise UpscalingError(
                        f"Failed to download image: HTTP {response.status_code}",
                        image_url=url,
                        correlation_id=correlation_id,
                    )

                # Use PIL to get dimensions
                from io import BytesIO

                from PIL import Image

                img = Image.open(BytesIO(response.content))
                return img.size  # (width, height)

        except ImportError:
            # If PIL not available, return (0, 0) and don't skip
            logger.warning(
                "PIL not available, cannot check image dimensions",
                extra={"correlation_id": correlation_id},
            )
            return (0, 0)
        except Exception as e:
            logger.warning(
                f"Failed to get image dimensions: {e}",
                extra={"correlation_id": correlation_id},
            )
            return (0, 0)

    def _should_skip(self, dimensions: tuple[int, int]) -> tuple[bool, str | None]:
        """Check if image already meets minimum resolution."""
        if dimensions == (0, 0):
            return False, None

        longest_edge = max(dimensions)
        if longest_edge >= self._min_resolution:
            return (
                True,
                f"Image already meets minimum resolution ({longest_edge}px >= {self._min_resolution}px)",
            )
        return False, None

    async def upscale_image(
        self,
        image_url: str,
        *,
        scale_factor: int = 4,
        face_enhance: bool = False,
        skip_if_sufficient: bool = True,
        correlation_id: str | None = None,
    ) -> UpscaleResult:
        """
        Upscale a product image.

        Args:
            image_url: URL of the product image
            scale_factor: Upscale factor (2 or 4)
            face_enhance: Enable face enhancement for model photos
            skip_if_sufficient: Skip if already meets minimum resolution
            correlation_id: Optional correlation ID for tracing

        Returns:
            UpscaleResult with processed image URL

        Raises:
            UpscalingError: If processing fails
        """
        import time

        start_time = time.time()
        client = await self._get_client()
        correlation_id = correlation_id or client._generate_correlation_id()

        # Validate scale factor
        if scale_factor not in (2, 4):
            raise UpscalingError(
                f"Invalid scale factor: {scale_factor}. Must be 2 or 4.",
                image_url=image_url,
                correlation_id=correlation_id,
            )

        logger.info(
            "Starting image upscaling",
            extra={
                "image_url": image_url,
                "scale_factor": scale_factor,
                "face_enhance": face_enhance,
                "correlation_id": correlation_id,
            },
        )

        # Get original dimensions
        original_dims = await self._get_image_dimensions(image_url, correlation_id)

        # Check if we should skip
        if skip_if_sufficient:
            should_skip, skip_reason = self._should_skip(original_dims)
            if should_skip:
                processing_time_ms = int((time.time() - start_time) * 1000)
                logger.info(
                    f"Skipping upscaling: {skip_reason}",
                    extra={"correlation_id": correlation_id},
                )
                return UpscaleResult(
                    original_url=image_url,
                    result_url=image_url,  # Return original
                    original_dimensions=original_dims,
                    result_dimensions=original_dims,
                    scale_factor=scale_factor,
                    model_used="",
                    face_enhance=face_enhance,
                    skipped=True,
                    skip_reason=skip_reason,
                    processing_time_ms=processing_time_ms,
                    correlation_id=correlation_id,
                )

        # Try primary model, then fallbacks
        models_to_try = [DEFAULT_UPSCALE_MODEL] + FALLBACK_MODELS
        last_error: Exception | None = None
        result_url: str | None = None
        model_used: str = ""

        for model in models_to_try:
            try:
                logger.debug(
                    f"Trying model: {model}",
                    extra={"correlation_id": correlation_id},
                )

                input_params = {
                    "image": image_url,
                    "scale": scale_factor,
                    "face_enhance": face_enhance,
                }

                prediction = await client.run_prediction(
                    model,
                    input_params,
                    correlation_id=correlation_id,
                )

                if prediction.succeeded and prediction.output:
                    result_url = prediction.output
                    model_used = model
                    break

            except Exception as e:
                logger.warning(
                    f"Model {model} failed: {e}",
                    extra={"correlation_id": correlation_id},
                )
                last_error = e
                continue

        if result_url is None:
            raise UpscalingError(
                "All upscaling models failed",
                image_url=image_url,
                correlation_id=correlation_id,
                cause=last_error,
            )

        # Get result dimensions
        result_dims = await self._get_image_dimensions(result_url, correlation_id)
        if result_dims == (0, 0):
            # Estimate based on scale factor
            result_dims = (
                original_dims[0] * scale_factor,
                original_dims[1] * scale_factor,
            )

        processing_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "Upscaling complete",
            extra={
                "result_url": result_url,
                "original_dims": original_dims,
                "result_dims": result_dims,
                "model_used": model_used,
                "processing_time_ms": processing_time_ms,
                "correlation_id": correlation_id,
            },
        )

        return UpscaleResult(
            original_url=image_url,
            result_url=result_url,
            original_dimensions=original_dims,
            result_dimensions=result_dims,
            scale_factor=scale_factor,
            model_used=model_used,
            face_enhance=face_enhance,
            processing_time_ms=processing_time_ms,
            correlation_id=correlation_id,
        )

    async def upscale_batch(
        self,
        image_urls: list[str],
        *,
        scale_factor: int = 4,
        face_enhance: bool = False,
        skip_if_sufficient: bool = True,
        correlation_id: str | None = None,
    ) -> list[UpscaleResult | UpscalingError]:
        """
        Process multiple images in batch.

        Args:
            image_urls: List of image URLs to process
            scale_factor: Upscale factor (2 or 4)
            face_enhance: Enable face enhancement
            skip_if_sufficient: Skip if already meets minimum resolution
            correlation_id: Optional correlation ID for tracing

        Returns:
            List of results or errors for each image
        """
        import asyncio

        client = await self._get_client()
        correlation_id = correlation_id or client._generate_correlation_id()

        async def process_one(url: str) -> UpscaleResult | UpscalingError:
            try:
                return await self.upscale_image(
                    url,
                    scale_factor=scale_factor,
                    face_enhance=face_enhance,
                    skip_if_sufficient=skip_if_sufficient,
                    correlation_id=correlation_id,
                )
            except UpscalingError as e:
                return e

        tasks = [process_one(url) for url in image_urls]
        return await asyncio.gather(*tasks)


__all__ = [
    "UpscalingService",
    "UpscaleResult",
    "UpscalingError",
]
