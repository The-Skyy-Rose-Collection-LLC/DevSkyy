# services/ml/enhancement/background_removal.py
"""
Background Removal Service for DevSkyy.

Removes and replaces product image backgrounds using Replicate ML models.
Supports transparent PNG output, solid color replacement, and custom
background image replacement.

CRITICAL: This service preserves product pixels with high precision.
No halo artifacts or edge degradation allowed.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import base64
import hashlib
import logging
from enum import StrEnum
from io import BytesIO
from typing import Any

import httpx
from PIL import Image, ImageColor
from pydantic import BaseModel
from services.ml.replicate_client import ReplicateClient, ReplicateConfig

from core.errors.production_errors import (
    DevSkyError,
    DevSkyErrorCode,
    DevSkyErrorSeverity,
)
from security.ssrf_protection import SSRFProtection

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Primary model - high quality, good edge preservation
DEFAULT_BACKGROUND_REMOVAL_MODEL = (
    "lucataco/remove-bg:95fcc2a26d3899cd6c2691c900465aaeff466285a65c14638cc5f36f34befaf1"
)

# Fallback models if primary fails
FALLBACK_MODELS = [
    "cjwbw/rembg:fb8af171cfa1616ddcf1242c093f9c46bcada5ad4cf6f2fbe8b81b330ec5c003",
]


# =============================================================================
# Models
# =============================================================================


class BackgroundType(StrEnum):
    """Background replacement type."""

    TRANSPARENT = "transparent"
    SOLID_COLOR = "solid_color"
    CUSTOM_IMAGE = "custom_image"


class BackgroundRemovalResult(BaseModel):
    """Result of background removal operation."""

    original_url: str
    result_url: str
    background_type: BackgroundType
    background_value: str | None = None  # Color hex or image URL
    model_used: str
    product_hash: str  # Hash of product region for verification
    processing_time_ms: int
    correlation_id: str

    @property
    def is_transparent(self) -> bool:
        """Check if result has transparent background."""
        return self.background_type == BackgroundType.TRANSPARENT


class BackgroundRemovalError(DevSkyError):
    """Error during background removal."""

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


class BackgroundRemovalService:
    """
    Service for removing and replacing image backgrounds.

    Features:
    - High-precision edge preservation
    - Multiple output types (transparent, solid color, custom image)
    - Fallback model chain for reliability
    - Product region hash for verification

    CRITICAL: Product pixels must remain unchanged.

    Usage:
        service = BackgroundRemovalService()
        result = await service.remove_background(
            image_url="https://example.com/product.jpg",
            background_type=BackgroundType.TRANSPARENT,
        )
        print(result.result_url)
    """

    def __init__(
        self,
        replicate_client: ReplicateClient | None = None,
        replicate_config: ReplicateConfig | None = None,
    ) -> None:
        self._client = replicate_client
        self._config = replicate_config
        self._owns_client = replicate_client is None

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

    async def __aenter__(self) -> BackgroundRemovalService:
        """Enter async context manager."""
        await self._get_client()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context manager."""
        await self.close()

    async def _download_image_bytes(self, url: str, correlation_id: str) -> bytes:
        """Download image from URL for processing."""
        async with httpx.AsyncClient(timeout=60.0) as http_client:
            response = await http_client.get(url)
            if response.status_code != 200:
                raise BackgroundRemovalError(
                    f"Failed to download image: HTTP {response.status_code}",
                    image_url=url,
                    correlation_id=correlation_id,
                )
            return response.content

    def _compute_image_hash(self, image_data: bytes) -> str:
        """Compute hash of image data for verification."""
        return hashlib.sha256(image_data).hexdigest()[:16]

    def _composite_on_color(self, cutout_bytes: bytes, color: str) -> bytes:
        """Composite an RGBA cutout over a solid color; return flattened PNG bytes."""
        cutout = Image.open(BytesIO(cutout_bytes))
        # Guard against DoS via oversized images (max 50MP)
        max_pixels = 50_000_000
        if cutout.width * cutout.height > max_pixels:
            raise ValueError(
                f"Image too large: {cutout.width}x{cutout.height} exceeds {max_pixels} pixels"
            )
        cutout = cutout.convert("RGBA")
        rgb = ImageColor.getrgb(color)
        background = Image.new("RGBA", cutout.size, (rgb[0], rgb[1], rgb[2], 255))
        flattened = Image.alpha_composite(background, cutout).convert("RGB")
        out = BytesIO()
        flattened.save(out, format="PNG")
        return out.getvalue()

    def _composite_on_image(self, cutout_bytes: bytes, background_bytes: bytes) -> bytes:
        """Composite an RGBA cutout over a background image; return flattened PNG bytes."""
        max_pixels = 50_000_000
        cutout = Image.open(BytesIO(cutout_bytes))
        if cutout.width * cutout.height > max_pixels:
            raise ValueError(
                f"Cutout image too large: {cutout.width}x{cutout.height} "
                f"exceeds {max_pixels} pixels"
            )
        cutout = cutout.convert("RGBA")

        background = Image.open(BytesIO(background_bytes))
        if background.width * background.height > max_pixels:
            raise ValueError(
                f"Background image too large: {background.width}x{background.height} "
                f"exceeds {max_pixels} pixels"
            )
        background = background.convert("RGBA").resize(cutout.size)

        flattened = Image.alpha_composite(background, cutout).convert("RGB")
        out = BytesIO()
        flattened.save(out, format="PNG")
        return out.getvalue()

    @staticmethod
    def _to_png_data_url(png_bytes: bytes) -> str:
        """Encode flattened PNG bytes as a self-contained base64 data URL."""
        encoded = base64.b64encode(png_bytes).decode("ascii")
        return f"data:image/png;base64,{encoded}"

    async def remove_background(
        self,
        image_url: str,
        *,
        background_type: BackgroundType = BackgroundType.TRANSPARENT,
        background_color: str | None = None,
        background_image_url: str | None = None,
        correlation_id: str | None = None,
    ) -> BackgroundRemovalResult:
        """
        Remove background from product image.

        Args:
            image_url: URL of the product image
            background_type: Type of background to apply
            background_color: Hex color for solid background (e.g., "#FFFFFF")
            background_image_url: URL of custom background image
            correlation_id: Optional correlation ID for tracing

        Returns:
            BackgroundRemovalResult with processed image URL

        Raises:
            BackgroundRemovalError: If processing fails
        """
        import time

        start_time = time.time()
        client = await self._get_client()
        correlation_id = correlation_id or client._generate_correlation_id()

        logger.info(
            "Starting background removal",
            extra={
                "image_url": image_url,
                "background_type": background_type.value,
                "correlation_id": correlation_id,
            },
        )

        # Download original for hash verification
        try:
            original_bytes = await self._download_image_bytes(image_url, correlation_id)
            original_hash = self._compute_image_hash(original_bytes)
        except Exception as e:
            raise BackgroundRemovalError(
                f"Failed to download original image: {e}",
                image_url=image_url,
                correlation_id=correlation_id,
                cause=e if isinstance(e, Exception) else None,
            ) from e

        # Try primary model, then fallbacks
        models_to_try = [DEFAULT_BACKGROUND_REMOVAL_MODEL] + FALLBACK_MODELS
        last_error: Exception | None = None
        result_url: str | None = None
        model_used: str = ""

        for model in models_to_try:
            try:
                logger.debug(
                    f"Trying model: {model}",
                    extra={"correlation_id": correlation_id},
                )

                prediction = await client.run_prediction(
                    model,
                    {"image": image_url},
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
            raise BackgroundRemovalError(
                "All background removal models failed",
                image_url=image_url,
                correlation_id=correlation_id,
                cause=last_error,
            )

        # P1 #12: composite the transparent cutout onto the requested background.
        # The composited image is returned as a self-contained PNG data URL (no
        # external storage), so result_url always points at the actual output and
        # background_value is never misleading.
        background_value: str | None = None
        try:
            if background_type == BackgroundType.SOLID_COLOR:
                color = background_color or "#FFFFFF"
                cutout_bytes = await self._download_image_bytes(result_url, correlation_id)
                result_url = self._to_png_data_url(self._composite_on_color(cutout_bytes, color))
                background_value = color
            elif background_type == BackgroundType.CUSTOM_IMAGE:
                if not background_image_url:
                    raise BackgroundRemovalError(
                        "BackgroundType.CUSTOM_IMAGE requires background_image_url",
                        image_url=image_url,
                        correlation_id=correlation_id,
                    )
                # SSRF protection: validate URL before download
                ssrf = SSRFProtection()
                try:
                    ssrf.validate_url(background_image_url)
                except Exception as e:
                    raise BackgroundRemovalError(
                        f"Invalid background_image_url: {e}",
                        image_url=image_url,
                        correlation_id=correlation_id,
                    ) from e
                cutout_bytes = await self._download_image_bytes(result_url, correlation_id)
                bg_bytes = await self._download_image_bytes(background_image_url, correlation_id)
                result_url = self._to_png_data_url(self._composite_on_image(cutout_bytes, bg_bytes))
                background_value = background_image_url
        except BackgroundRemovalError:
            raise
        except (OSError, ValueError) as e:
            raise BackgroundRemovalError(
                f"Failed to composite background: {e}",
                image_url=image_url,
                correlation_id=correlation_id,
                cause=e,
            ) from e

        processing_time_ms = int((time.time() - start_time) * 1000)
        result_is_inline = result_url.startswith("data:")

        logger.info(
            "Background removal complete",
            extra={
                "result_url": "<inline-png-data-url>" if result_is_inline else result_url,
                "result_url_inline": result_is_inline,
                "model_used": model_used,
                "processing_time_ms": processing_time_ms,
                "correlation_id": correlation_id,
            },
        )

        return BackgroundRemovalResult(
            original_url=image_url,
            result_url=result_url,
            background_type=background_type,
            background_value=background_value,
            model_used=model_used,
            product_hash=original_hash,
            processing_time_ms=processing_time_ms,
            correlation_id=correlation_id,
        )

    async def remove_background_batch(
        self,
        image_urls: list[str],
        *,
        background_type: BackgroundType = BackgroundType.TRANSPARENT,
        background_color: str | None = None,
        correlation_id: str | None = None,
    ) -> list[BackgroundRemovalResult | BackgroundRemovalError]:
        """
        Process multiple images in batch.

        Args:
            image_urls: List of image URLs to process
            background_type: Type of background to apply
            background_color: Hex color for solid background
            correlation_id: Optional correlation ID for tracing

        Returns:
            List of results or errors for each image
        """
        import asyncio

        client = await self._get_client()
        correlation_id = correlation_id or client._generate_correlation_id()

        async def process_one(url: str) -> BackgroundRemovalResult | BackgroundRemovalError:
            try:
                return await self.remove_background(
                    url,
                    background_type=background_type,
                    background_color=background_color,
                    correlation_id=correlation_id,
                )
            except BackgroundRemovalError as e:
                return e

        tasks = [process_one(url) for url in image_urls]
        return await asyncio.gather(*tasks)


__all__ = [
    "BackgroundRemovalService",
    "BackgroundRemovalResult",
    "BackgroundRemovalError",
    "BackgroundType",
]
