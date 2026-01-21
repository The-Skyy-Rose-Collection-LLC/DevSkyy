# services/three_d/provider_interface.py
"""3D Provider Interface Protocol and Models.

Defines the contract for all 3D generation providers.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from errors.production_errors import (
    DevSkyError,
    DevSkyErrorCode,
    DevSkyErrorSeverity,
)


# =============================================================================
# Errors
# =============================================================================


class ThreeDProviderError(DevSkyError):
    """Base error for 3D provider operations."""

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        correlation_id: str | None = None,
        cause: Exception | None = None,
        retryable: bool = False,
    ) -> None:
        context: dict[str, Any] = {}
        if provider:
            context["provider"] = provider

        super().__init__(
            message,
            code=DevSkyErrorCode.EXTERNAL_SERVICE_ERROR,
            severity=DevSkyErrorSeverity.ERROR,
            context=context,
            cause=cause,
            retryable=retryable,
            correlation_id=correlation_id,
        )
        self.provider = provider


class ThreeDGenerationError(ThreeDProviderError):
    """Error during 3D generation."""

    def __init__(
        self,
        message: str,
        *,
        task_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.task_id = task_id


class ThreeDTimeoutError(ThreeDProviderError):
    """Timeout error during 3D generation."""

    def __init__(
        self,
        message: str = "3D generation timed out",
        *,
        timeout_seconds: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, retryable=True, **kwargs)
        self.timeout_seconds = timeout_seconds


# =============================================================================
# Enums
# =============================================================================


class ProviderStatus(str, Enum):
    """Provider availability status."""

    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"


class ThreeDCapability(str, Enum):
    """3D generation capabilities."""

    TEXT_TO_3D = "text_to_3d"
    IMAGE_TO_3D = "image_to_3d"
    MULTI_VIEW = "multi_view"
    TEXTURE_GENERATION = "texture_generation"


class OutputFormat(str, Enum):
    """3D output formats."""

    GLB = "glb"
    GLTF = "gltf"
    OBJ = "obj"
    FBX = "fbx"
    USDZ = "usdz"
    STL = "stl"


class QualityLevel(str, Enum):
    """Generation quality levels."""

    DRAFT = "draft"  # Fast, lower quality
    STANDARD = "standard"  # Balanced
    PRODUCTION = "production"  # Best quality, slower


# =============================================================================
# Request/Response Models
# =============================================================================


class ThreeDRequest(BaseModel):
    """Unified request for 3D generation."""

    # Input (one of)
    prompt: str | None = Field(default=None, description="Text prompt for text-to-3D")
    image_url: str | None = Field(default=None, description="Image URL for image-to-3D")
    image_path: str | None = Field(default=None, description="Local image path for image-to-3D")

    # Options
    output_format: OutputFormat = Field(default=OutputFormat.GLB)
    quality: QualityLevel = Field(default=QualityLevel.PRODUCTION)
    texture_size: int = Field(default=1024, ge=256, le=4096)

    # SkyyRose context
    product_name: str | None = Field(default=None)
    collection: str | None = Field(default=None)
    garment_type: str | None = Field(default=None)

    # Metadata
    correlation_id: str | None = Field(default=None)
    callback_url: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def is_text_request(self) -> bool:
        """Check if this is a text-to-3D request."""
        return self.prompt is not None

    def is_image_request(self) -> bool:
        """Check if this is an image-to-3D request."""
        return self.image_url is not None or self.image_path is not None

    def get_image_source(self) -> str | None:
        """Get the image source (URL or path)."""
        return self.image_url or self.image_path


class ThreeDResponse(BaseModel):
    """Unified response from 3D generation."""

    # Status
    success: bool
    task_id: str
    status: str  # Provider-specific status

    # Output
    model_url: str | None = Field(default=None, description="URL to generated model")
    model_path: str | None = Field(default=None, description="Local path to model file")
    texture_url: str | None = Field(default=None)
    thumbnail_url: str | None = Field(default=None)

    # Metadata
    output_format: OutputFormat = Field(default=OutputFormat.GLB)
    provider: str
    duration_seconds: float = 0.0
    polycount: int | None = None
    file_size_bytes: int | None = None

    # Error info
    error_message: str | None = None
    error_code: str | None = None

    # Timestamps
    created_at: datetime | None = None
    completed_at: datetime | None = None

    # Request correlation
    correlation_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProviderHealth(BaseModel):
    """Provider health status."""

    provider: str
    status: ProviderStatus
    capabilities: list[ThreeDCapability] = Field(default_factory=list)
    latency_ms: float | None = None
    last_check: datetime | None = None
    error_message: str | None = None
    rate_limit_reset: datetime | None = None

    @property
    def is_available(self) -> bool:
        """Check if provider is available for requests."""
        return self.status in (ProviderStatus.AVAILABLE, ProviderStatus.DEGRADED)

    def supports(self, capability: ThreeDCapability) -> bool:
        """Check if provider supports a capability."""
        return capability in self.capabilities


# =============================================================================
# Provider Protocol
# =============================================================================


@runtime_checkable
class I3DProvider(Protocol):
    """Protocol for 3D generation providers.

    All 3D providers must implement this interface to be usable
    with the ThreeDProviderFactory.

    Example:
        class MyProvider:
            @property
            def name(self) -> str:
                return "my_provider"

            async def generate_from_text(
                self,
                request: ThreeDRequest,
            ) -> ThreeDResponse:
                ...

            async def generate_from_image(
                self,
                request: ThreeDRequest,
            ) -> ThreeDResponse:
                ...

            async def health_check(self) -> ProviderHealth:
                ...
    """

    @property
    def name(self) -> str:
        """Provider name identifier."""
        ...

    @property
    def capabilities(self) -> list[ThreeDCapability]:
        """List of supported capabilities."""
        ...

    async def generate_from_text(
        self,
        request: ThreeDRequest,
    ) -> ThreeDResponse:
        """Generate 3D model from text prompt.

        Args:
            request: ThreeDRequest with prompt set

        Returns:
            ThreeDResponse with generation result

        Raises:
            ThreeDProviderError: If generation fails
            ThreeDTimeoutError: If generation times out
        """
        ...

    async def generate_from_image(
        self,
        request: ThreeDRequest,
    ) -> ThreeDResponse:
        """Generate 3D model from image.

        Args:
            request: ThreeDRequest with image_url or image_path set

        Returns:
            ThreeDResponse with generation result

        Raises:
            ThreeDProviderError: If generation fails
            ThreeDTimeoutError: If generation times out
        """
        ...

    async def health_check(self) -> ProviderHealth:
        """Check provider health and availability.

        Returns:
            ProviderHealth with current status
        """
        ...

    async def close(self) -> None:
        """Close provider resources."""
        ...


__all__ = [
    # Protocol
    "I3DProvider",
    # Models
    "ThreeDRequest",
    "ThreeDResponse",
    "ProviderHealth",
    # Enums
    "ProviderStatus",
    "ThreeDCapability",
    "OutputFormat",
    "QualityLevel",
    # Errors
    "ThreeDProviderError",
    "ThreeDGenerationError",
    "ThreeDTimeoutError",
]
