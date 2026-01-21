# services/ml/replicate_client.py
"""
Replicate API Client for DevSkyy.

Provides async client abstraction for Replicate ML models including:
- Background removal (rembg)
- Image upscaling (Real-ESRGAN)
- Image-to-3D generation
- Style transfer
- Virtual try-on

API Reference: https://replicate.com/docs

CRITICAL: NEVER modify product logos, branding, labels, or features.
Only enhance, clarify, make e-commerce ready.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel, Field, field_validator

from errors.production_errors import (
    DevSkyError,
    DevSkyErrorCode,
    DevSkyErrorSeverity,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

REPLICATE_API_BASE = "https://api.replicate.com/v1"
DEFAULT_TIMEOUT = 60.0
DEFAULT_POLL_INTERVAL = 2.0
MAX_POLL_ATTEMPTS = 150  # 5 minutes with 2s interval


# =============================================================================
# Errors
# =============================================================================


class ReplicateError(DevSkyError):
    """Base error for Replicate API operations."""

    def __init__(
        self,
        message: str,
        *,
        model: str | None = None,
        prediction_id: str | None = None,
        correlation_id: str | None = None,
        cause: Exception | None = None,
        retryable: bool = False,
    ) -> None:
        context: dict[str, Any] = {}
        if model:
            context["model"] = model
        if prediction_id:
            context["prediction_id"] = prediction_id

        super().__init__(
            message,
            code=DevSkyErrorCode.EXTERNAL_SERVICE_ERROR,
            severity=DevSkyErrorSeverity.ERROR,
            context=context,
            cause=cause,
            retryable=retryable,
            correlation_id=correlation_id,
        )


class ReplicateRateLimitError(ReplicateError):
    """Raised when Replicate API rate limit is hit."""

    def __init__(
        self,
        message: str = "Replicate API rate limit exceeded",
        retry_after_seconds: int = 60,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, retryable=True, **kwargs)
        self.retry_after_seconds = retry_after_seconds


class ReplicateTimeoutError(ReplicateError):
    """Raised when prediction times out."""

    def __init__(
        self,
        message: str = "Replicate prediction timed out",
        **kwargs: Any,
    ) -> None:
        super().__init__(message, retryable=True, **kwargs)


# =============================================================================
# Models
# =============================================================================


class ReplicatePredictionStatus(str, Enum):
    """Status of a Replicate prediction."""

    STARTING = "starting"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class ReplicatePrediction(BaseModel):
    """Replicate prediction response."""

    id: str
    version: str | None = None
    model: str | None = None
    status: ReplicatePredictionStatus
    input: dict[str, Any] = Field(default_factory=dict)
    output: Any = None
    error: str | None = None
    logs: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    urls: dict[str, str] = Field(default_factory=dict)

    @property
    def is_terminal(self) -> bool:
        """Check if prediction has reached a terminal state."""
        return self.status in {
            ReplicatePredictionStatus.SUCCEEDED,
            ReplicatePredictionStatus.FAILED,
            ReplicatePredictionStatus.CANCELED,
        }

    @property
    def succeeded(self) -> bool:
        """Check if prediction succeeded."""
        return self.status == ReplicatePredictionStatus.SUCCEEDED


class ReplicateModelInput(BaseModel):
    """Base model for validated Replicate model inputs."""

    pass


class BackgroundRemovalInput(ReplicateModelInput):
    """Input for background removal model."""

    image: str = Field(..., description="URL or base64 of input image")

    @field_validator("image")
    @classmethod
    def validate_image(cls, v: str) -> str:
        """Validate image input is URL or base64."""
        if not v.startswith(("http://", "https://", "data:image/")):
            raise ValueError("Image must be a URL or base64 data URI")
        return v


class ImageUpscaleInput(ReplicateModelInput):
    """Input for image upscaling model."""

    image: str = Field(..., description="URL or base64 of input image")
    scale: int = Field(default=4, ge=2, le=8, description="Upscale factor")
    face_enhance: bool = Field(default=False, description="Enable face enhancement")

    @field_validator("image")
    @classmethod
    def validate_image(cls, v: str) -> str:
        """Validate image input."""
        if not v.startswith(("http://", "https://", "data:image/")):
            raise ValueError("Image must be a URL or base64 data URI")
        return v


class ImageTo3DInput(ReplicateModelInput):
    """Input for image-to-3D generation model."""

    image: str = Field(..., description="URL of input image")
    output_format: str = Field(default="glb", description="Output format (glb, obj)")

    @field_validator("image")
    @classmethod
    def validate_image(cls, v: str) -> str:
        """Validate image URL."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Image must be a URL")
        return v

    @field_validator("output_format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate output format."""
        allowed = {"glb", "gltf", "obj"}
        if v.lower() not in allowed:
            raise ValueError(f"Output format must be one of: {allowed}")
        return v.lower()


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class ReplicateConfig:
    """Replicate API configuration."""

    api_token: str = field(default_factory=lambda: os.getenv("REPLICATE_API_TOKEN", ""))
    base_url: str = REPLICATE_API_BASE
    timeout: float = DEFAULT_TIMEOUT
    poll_interval: float = DEFAULT_POLL_INTERVAL
    max_poll_attempts: int = MAX_POLL_ATTEMPTS
    max_retries: int = 3

    # Model versions (can be overridden)
    background_removal_model: str = (
        "cjwbw/rembg:fb8af171cfa1616ddcf1242c093f9c46bcada5ad4cf6f2fbe8b81b330ec5c003"
    )
    upscale_model: str = (
        "nightmareai/real-esrgan:f121d640bd286e1fdc67f9799164c1d5be36ff74576ee11c803ae5b665dd46aa"
    )
    image_to_3d_model: str = "adirik/wonder3d:e6a3eda1a67e8a9b915e45e1d7b3f7e3"

    @classmethod
    def from_env(cls) -> ReplicateConfig:
        """Create config from environment variables."""
        return cls()

    def validate(self) -> None:
        """Validate configuration."""
        if not self.api_token:
            raise ReplicateError(
                "REPLICATE_API_TOKEN environment variable is required",
                retryable=False,
            )


# =============================================================================
# Client
# =============================================================================


class ReplicateClient:
    """
    Async client for Replicate API.

    Provides:
    - Background removal (rembg)
    - Image upscaling (Real-ESRGAN)
    - Image-to-3D generation
    - Generic prediction interface

    Usage:
        async with ReplicateClient() as client:
            result = await client.remove_background(image_url)
            print(result.output)
    """

    def __init__(self, config: ReplicateConfig | None = None) -> None:
        self.config = config or ReplicateConfig.from_env()
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> ReplicateClient:
        """Enter async context manager."""
        await self.connect()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context manager."""
        await self.close()

    async def connect(self) -> None:
        """Initialize HTTP client."""
        self.config.validate()
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers={
                    "Authorization": f"Token {self.config.api_token}",
                    "Content-Type": "application/json",
                },
                timeout=self.config.timeout,
            )

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _generate_correlation_id(self) -> str:
        """Generate a unique correlation ID for tracing."""
        return str(uuid.uuid4())

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request to Replicate API."""
        await self.connect()
        correlation_id = correlation_id or self._generate_correlation_id()

        for attempt in range(self.config.max_retries):
            try:
                logger.debug(
                    "Replicate API request",
                    extra={
                        "method": method,
                        "endpoint": endpoint,
                        "correlation_id": correlation_id,
                        "attempt": attempt + 1,
                    },
                )

                response = await self._client.request(
                    method,
                    endpoint,
                    json=json,
                    params=params,
                )

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "60"))
                    raise ReplicateRateLimitError(
                        retry_after_seconds=retry_after,
                        correlation_id=correlation_id,
                    )

                if response.status_code == 401:
                    raise ReplicateError(
                        "Invalid Replicate API token",
                        correlation_id=correlation_id,
                        retryable=False,
                    )

                if response.status_code >= 400:
                    error_body = response.text
                    raise ReplicateError(
                        f"Replicate API error: {response.status_code} - {error_body}",
                        correlation_id=correlation_id,
                        retryable=response.status_code >= 500,
                    )

                return response.json()

            except httpx.TimeoutException as e:
                if attempt == self.config.max_retries - 1:
                    raise ReplicateTimeoutError(
                        "Request timed out",
                        correlation_id=correlation_id,
                        cause=e,
                    )
                await asyncio.sleep(2**attempt)  # Exponential backoff

            except httpx.RequestError as e:
                if attempt == self.config.max_retries - 1:
                    raise ReplicateError(
                        f"Request failed: {e}",
                        correlation_id=correlation_id,
                        cause=e,
                        retryable=True,
                    )
                await asyncio.sleep(2**attempt)

        raise ReplicateError(
            "Max retries exceeded",
            correlation_id=correlation_id,
        )

    async def create_prediction(
        self,
        model: str,
        input_data: dict[str, Any],
        *,
        correlation_id: str | None = None,
        webhook: str | None = None,
    ) -> ReplicatePrediction:
        """
        Create a new prediction.

        Args:
            model: Model version string (owner/model:version)
            input_data: Model-specific input parameters
            correlation_id: Optional correlation ID for tracing
            webhook: Optional webhook URL for completion notification

        Returns:
            ReplicatePrediction with prediction details
        """
        correlation_id = correlation_id or self._generate_correlation_id()

        payload: dict[str, Any] = {
            "version": model.split(":")[-1] if ":" in model else model,
            "input": input_data,
        }
        if webhook:
            payload["webhook"] = webhook

        logger.info(
            "Creating Replicate prediction",
            extra={
                "model": model,
                "correlation_id": correlation_id,
            },
        )

        response = await self._request(
            "POST",
            "/predictions",
            json=payload,
            correlation_id=correlation_id,
        )

        prediction = ReplicatePrediction.model_validate(response)
        logger.info(
            "Prediction created",
            extra={
                "prediction_id": prediction.id,
                "status": prediction.status,
                "correlation_id": correlation_id,
            },
        )

        return prediction

    async def get_prediction(
        self,
        prediction_id: str,
        *,
        correlation_id: str | None = None,
    ) -> ReplicatePrediction:
        """Get prediction status and results."""
        response = await self._request(
            "GET",
            f"/predictions/{prediction_id}",
            correlation_id=correlation_id,
        )
        return ReplicatePrediction.model_validate(response)

    async def wait_for_prediction(
        self,
        prediction_id: str,
        *,
        correlation_id: str | None = None,
    ) -> ReplicatePrediction:
        """
        Poll prediction until completion.

        Args:
            prediction_id: ID of the prediction to wait for
            correlation_id: Optional correlation ID for tracing

        Returns:
            Completed ReplicatePrediction

        Raises:
            ReplicateTimeoutError: If prediction takes too long
            ReplicateError: If prediction fails
        """
        correlation_id = correlation_id or self._generate_correlation_id()

        for attempt in range(self.config.max_poll_attempts):
            prediction = await self.get_prediction(
                prediction_id,
                correlation_id=correlation_id,
            )

            if prediction.is_terminal:
                if prediction.status == ReplicatePredictionStatus.FAILED:
                    raise ReplicateError(
                        f"Prediction failed: {prediction.error}",
                        prediction_id=prediction_id,
                        correlation_id=correlation_id,
                    )
                return prediction

            logger.debug(
                "Prediction in progress",
                extra={
                    "prediction_id": prediction_id,
                    "status": prediction.status,
                    "attempt": attempt + 1,
                    "correlation_id": correlation_id,
                },
            )

            await asyncio.sleep(self.config.poll_interval)

        raise ReplicateTimeoutError(
            f"Prediction {prediction_id} timed out after {self.config.max_poll_attempts * self.config.poll_interval}s",
            prediction_id=prediction_id,
            correlation_id=correlation_id,
        )

    async def run_prediction(
        self,
        model: str,
        input_data: dict[str, Any],
        *,
        correlation_id: str | None = None,
        wait: bool = True,
    ) -> ReplicatePrediction:
        """
        Create and optionally wait for a prediction.

        Args:
            model: Model version string
            input_data: Model-specific input parameters
            correlation_id: Optional correlation ID for tracing
            wait: If True, wait for completion

        Returns:
            ReplicatePrediction with results (if wait=True)
        """
        correlation_id = correlation_id or self._generate_correlation_id()

        prediction = await self.create_prediction(
            model,
            input_data,
            correlation_id=correlation_id,
        )

        if wait:
            return await self.wait_for_prediction(
                prediction.id,
                correlation_id=correlation_id,
            )

        return prediction

    # =========================================================================
    # High-Level Methods for SkyyRose Asset Pipeline
    # =========================================================================

    async def remove_background(
        self,
        image_url: str,
        *,
        correlation_id: str | None = None,
    ) -> ReplicatePrediction:
        """
        Remove background from product image.

        CRITICAL: Does not modify product features, only removes background.

        Args:
            image_url: URL of the product image
            correlation_id: Optional correlation ID for tracing

        Returns:
            Prediction with output URL of image with transparent background
        """
        validated = BackgroundRemovalInput(image=image_url)

        return await self.run_prediction(
            self.config.background_removal_model,
            {"image": validated.image},
            correlation_id=correlation_id,
        )

    async def upscale_image(
        self,
        image_url: str,
        *,
        scale: int = 4,
        face_enhance: bool = False,
        correlation_id: str | None = None,
    ) -> ReplicatePrediction:
        """
        Upscale product image while preserving quality.

        CRITICAL: Does not modify product features, only increases resolution.

        Args:
            image_url: URL of the product image
            scale: Upscale factor (2-8)
            face_enhance: Enable face enhancement for model photos
            correlation_id: Optional correlation ID for tracing

        Returns:
            Prediction with output URL of upscaled image
        """
        validated = ImageUpscaleInput(
            image=image_url,
            scale=scale,
            face_enhance=face_enhance,
        )

        return await self.run_prediction(
            self.config.upscale_model,
            {
                "image": validated.image,
                "scale": validated.scale,
                "face_enhance": validated.face_enhance,
            },
            correlation_id=correlation_id,
        )

    async def image_to_3d(
        self,
        image_url: str,
        *,
        output_format: str = "glb",
        correlation_id: str | None = None,
    ) -> ReplicatePrediction:
        """
        Generate 3D model from product image.

        Args:
            image_url: URL of the product image
            output_format: Output format (glb, gltf, obj)
            correlation_id: Optional correlation ID for tracing

        Returns:
            Prediction with output URL of 3D model
        """
        validated = ImageTo3DInput(
            image=image_url,
            output_format=output_format,
        )

        return await self.run_prediction(
            self.config.image_to_3d_model,
            {
                "image": validated.image,
                "output_format": validated.output_format,
            },
            correlation_id=correlation_id,
        )

    async def cancel_prediction(
        self,
        prediction_id: str,
        *,
        correlation_id: str | None = None,
    ) -> ReplicatePrediction:
        """Cancel a running prediction."""
        response = await self._request(
            "POST",
            f"/predictions/{prediction_id}/cancel",
            correlation_id=correlation_id,
        )
        return ReplicatePrediction.model_validate(response)


__all__ = [
    "ReplicateClient",
    "ReplicateConfig",
    "ReplicateError",
    "ReplicatePrediction",
    "ReplicatePredictionStatus",
    "ReplicateRateLimitError",
    "ReplicateTimeoutError",
    "BackgroundRemovalInput",
    "ImageUpscaleInput",
    "ImageTo3DInput",
]
