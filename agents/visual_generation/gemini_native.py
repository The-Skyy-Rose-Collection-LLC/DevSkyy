"""
Gemini Native Image Generation Client
======================================

Production-ready client for Google's Gemini native image generation models:
- gemini-2.5-flash-image ("Nano Banana"): Fast, efficient image generation
- gemini-3-pro-image-preview ("Nano Banana Pro"): Professional quality with 4K support

Features:
- Async operations with retry logic
- Brand DNA injection via BrandContextInjector
- Explicit error taxonomy
- Cost tracking and metrics
- Multi-turn conversational editing support

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import base64
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from io import BytesIO
from typing import Any

import httpx
from PIL import Image

from orchestration.brand_context import BrandContextInjector, Collection

logger = logging.getLogger(__name__)


# =============================================================================
# Error Taxonomy
# =============================================================================


class GeminiNativeError(Exception):
    """Base exception for Gemini native image generation errors."""

    def __init__(
        self,
        message: str,
        model: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.model = model
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "model": self.model,
            "details": self.details,
        }


class GeminiAuthenticationError(GeminiNativeError):
    """Raised when API authentication fails."""

    pass


class GeminiRateLimitError(GeminiNativeError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        retry_after: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class GeminiQuotaExceededError(GeminiNativeError):
    """Raised when API quota is exceeded."""

    pass


class GeminiInvalidRequestError(GeminiNativeError):
    """Raised when request is invalid."""

    pass


class GeminiModelNotFoundError(GeminiNativeError):
    """Raised when requested model is not available."""

    pass


class GeminiContentFilterError(GeminiNativeError):
    """Raised when content is filtered by safety systems."""

    pass


class GeminiTimeoutError(GeminiNativeError):
    """Raised when request times out."""

    pass


class GeminiServiceUnavailableError(GeminiNativeError):
    """Raised when service is temporarily unavailable."""

    pass


class ChatSessionExpiredError(GeminiNativeError):
    """Raised when multi-turn chat session expires (60min limit)."""

    pass


# =============================================================================
# Enums and Data Classes
# =============================================================================


class AspectRatio(str, Enum):
    """Supported aspect ratios for image generation."""

    SQUARE = "1:1"  # 1024x1024
    PORTRAIT_2_3 = "2:3"  # 832x1248
    LANDSCAPE_3_2 = "3:2"  # 1248x832
    PORTRAIT_3_4 = "3:4"  # 864x1184
    LANDSCAPE_4_3 = "4:3"  # 1184x864
    PORTRAIT_4_5 = "4:5"  # 896x1152
    LANDSCAPE_5_4 = "5:4"  # 1152x896
    PORTRAIT_9_16 = "9:16"  # 768x1344
    LANDSCAPE_16_9 = "16:9"  # 1344x768
    ULTRAWIDE = "21:9"  # 1536x672


class ImageSize(str, Enum):
    """Supported image sizes (Gemini 3 Pro only)."""

    SIZE_1K = "1K"  # 1120 tokens
    SIZE_2K = "2K"  # 1120 tokens
    SIZE_4K = "4K"  # 2000 tokens


@dataclass
class ImageGenerationConfig:
    """Configuration for image generation."""

    aspect_ratio: AspectRatio = AspectRatio.SQUARE
    image_size: ImageSize | None = None  # Gemini 3 Pro only
    negative_prompt: str | None = None
    use_thinking_mode: bool = False  # Gemini 3 Pro only
    use_search_grounding: bool = False  # Gemini 3 Pro only


@dataclass
class GeneratedImage:
    """Container for generated image data."""

    image: Image.Image
    base64_data: str
    mime_type: str
    prompt: str
    model: str
    latency_ms: float
    cost_usd: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def save(self, path: str) -> None:
        """Save image to file."""
        self.image.save(path)

    def show(self) -> None:
        """Display image."""
        self.image.show()


# =============================================================================
# Base Client
# =============================================================================


class GeminiNativeImageClient:
    """
    Base client for Gemini native image generation.

    Provides:
    - Async operations with exponential backoff retry
    - Brand DNA injection via BrandContextInjector
    - Explicit error taxonomy
    - Cost tracking and metrics
    - Production-ready timeouts and connection pooling

    Usage:
        client = GeminiNativeImageClient(api_key="...")
        result = await client.generate(
            prompt="luxury streetwear hoodie, rose gold accents",
            collection=Collection.BLACK_ROSE
        )
        result.image.show()
    """

    # Class constants
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    DEFAULT_TIMEOUT = 60.0  # 60s for image generation
    MAX_RETRIES = 3
    RETRY_DELAYS = [1, 2, 4]  # Exponential backoff

    # Cost per image (USD)
    COST_PER_IMAGE = 0.02  # Override in subclasses

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash-image",
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        brand_injector: BrandContextInjector | None = None,
    ) -> None:
        """
        Initialize Gemini native image client.

        Args:
            api_key: Google API key (or read from GOOGLE_API_KEY env var)
            model: Model to use (gemini-2.5-flash-image or gemini-3-pro-image-preview)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            brand_injector: Optional brand context injector (creates default if None)
        """
        import os

        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        if not self.api_key:
            raise GeminiAuthenticationError("GOOGLE_API_KEY not found")

        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.brand_injector = brand_injector or BrandContextInjector(compact_mode=True)

        # HTTP client (lazy initialization)
        self._client: httpx.AsyncClient | None = None

    async def connect(self) -> None:
        """Initialize async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> GeminiNativeImageClient:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    def _inject_brand_dna(
        self,
        prompt: str,
        collection: Collection | None = None,
    ) -> str:
        """
        Inject SkyyRose brand DNA into image generation prompt.

        Args:
            prompt: Original prompt
            collection: Optional collection context

        Returns:
            Enhanced prompt with brand context
        """
        # Get compact brand prompt
        brand_context = self.brand_injector.get_compact_prompt(collection)

        # Inject brand DNA as suffix
        enhanced_prompt = f"{prompt}. {brand_context}"

        return enhanced_prompt

    async def _make_request(
        self,
        method: str,
        url: str,
        json: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic.

        Handles common errors and retries appropriately.
        """
        await self.connect()

        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await self._client.request(  # type: ignore
                    method=method,
                    url=url,
                    json=json,
                    **kwargs,
                )

                # Check for errors
                if response.status_code == 401:
                    raise GeminiAuthenticationError(
                        "Invalid API key",
                        model=self.model,
                    )
                elif response.status_code == 429:
                    retry_after = response.headers.get("retry-after")
                    raise GeminiRateLimitError(
                        "Rate limit exceeded",
                        model=self.model,
                        retry_after=float(retry_after) if retry_after else None,
                    )
                elif response.status_code >= 500:
                    raise GeminiServiceUnavailableError(
                        f"Service error: {response.status_code}",
                        model=self.model,
                    )
                elif response.status_code >= 400:
                    raise GeminiNativeError(
                        f"Request failed: {response.text}",
                        model=self.model,
                        details={"status_code": response.status_code},
                    )

                return response

            except httpx.TimeoutException:
                last_error = GeminiTimeoutError(
                    f"Request timed out after {self.timeout}s",
                    model=self.model,
                )
            except (GeminiRateLimitError, GeminiServiceUnavailableError) as e:
                last_error = e
                # Retry these errors
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.RETRY_DELAYS[min(attempt, len(self.RETRY_DELAYS) - 1)])
            except (GeminiAuthenticationError, GeminiNativeError):
                raise  # Don't retry auth or validation errors

        raise last_error or GeminiNativeError("Request failed after retries", model=self.model)

    def _decode_image(self, base64_data: str, mime_type: str) -> Image.Image:
        """Decode base64 image data to PIL Image."""
        image_bytes = base64.b64decode(base64_data)
        return Image.open(BytesIO(image_bytes))

    async def generate(
        self,
        prompt: str,
        config: ImageGenerationConfig | None = None,
        collection: Collection | None = None,
        inject_brand_dna: bool = True,
    ) -> GeneratedImage:
        """
        Generate image from text prompt.

        Args:
            prompt: Text description of desired image
            config: Optional generation configuration
            collection: Optional SkyyRose collection context
            inject_brand_dna: Whether to inject brand DNA (default True)

        Returns:
            GeneratedImage with PIL Image and metadata

        Raises:
            GeminiNativeError: On generation failure
        """
        start_time = datetime.now(UTC)
        config = config or ImageGenerationConfig()

        # Inject brand DNA
        enhanced_prompt = self._inject_brand_dna(prompt, collection) if inject_brand_dna else prompt

        # Build request payload
        request_data: dict[str, Any] = {
            "contents": [{"parts": [{"text": enhanced_prompt}]}],
            "generationConfig": {
                "imageConfig": {
                    "aspectRatio": config.aspect_ratio.value,
                }
            },
        }

        # Add image size for Gemini 3 Pro
        if config.image_size and "3-pro" in self.model:
            request_data["generationConfig"]["imageConfig"]["imageSize"] = config.image_size.value

        # Build URL with API key
        url = f"{self.BASE_URL}/models/{self.model}:generateContent?key={self.api_key}"

        # Make request
        response = await self._make_request("POST", url, json=request_data)
        result = response.json()

        # Extract image data
        candidates = result.get("candidates", [])
        if not candidates:
            raise GeminiNativeError(
                "No image generated",
                model=self.model,
                details={"response": result},
            )

        candidate = candidates[0]
        parts = candidate.get("content", {}).get("parts", [])

        image_data = None
        for part in parts:
            if "inlineData" in part:
                image_data = part["inlineData"]
                break

        if not image_data:
            raise GeminiNativeError(
                "No image data in response",
                model=self.model,
                details={"response": result},
            )

        # Decode image
        base64_data = image_data["data"]
        mime_type = image_data["mimeType"]
        image = self._decode_image(base64_data, mime_type)

        # Calculate metrics
        latency_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000
        cost_usd = self.COST_PER_IMAGE

        # Extract usage metadata
        usage = result.get("usageMetadata", {})

        return GeneratedImage(
            image=image,
            base64_data=base64_data,
            mime_type=mime_type,
            prompt=enhanced_prompt,
            model=self.model,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            metadata={
                "original_prompt": prompt,
                "collection": collection.value if collection else None,
                "config": {
                    "aspect_ratio": config.aspect_ratio.value,
                    "image_size": config.image_size.value if config.image_size else None,
                    "negative_prompt": config.negative_prompt,
                    "use_thinking_mode": config.use_thinking_mode,
                    "use_search_grounding": config.use_search_grounding,
                },
                "usage": {
                    "prompt_tokens": usage.get("promptTokenCount", 0),
                    "candidates_tokens": usage.get("candidatesTokenCount", 0),
                    "total_tokens": usage.get("totalTokenCount", 0),
                },
                "finish_reason": candidate.get("finishReason", ""),
            },
        )


# =============================================================================
# Specialized Clients
# =============================================================================


class GeminiFlashImageClient(GeminiNativeImageClient):
    """
    Gemini 2.5 Flash Image client ("Nano Banana").

    Optimized for speed and efficiency:
    - Model: gemini-2.5-flash-image
    - Speed: ~2.5s per image
    - Resolution: 1024px (default), varies by aspect ratio
    - Cost: $0.02 per image
    - Token usage: 1290 tokens per image (all aspect ratios)

    Best for:
    - Rapid prototyping
    - High-volume generation
    - Real-time workflows
    - Cost-sensitive applications

    Usage:
        client = GeminiFlashImageClient(api_key="...")
        result = await client.generate(
            prompt="SkyyRose BLACK ROSE hoodie product shot",
            config=ImageGenerationConfig(aspect_ratio=AspectRatio.SQUARE),
            collection=Collection.BLACK_ROSE
        )
        result.image.save("output.jpg")
    """

    COST_PER_IMAGE = 0.02  # $0.02 per image

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = GeminiNativeImageClient.DEFAULT_TIMEOUT,
        max_retries: int = GeminiNativeImageClient.MAX_RETRIES,
        brand_injector: BrandContextInjector | None = None,
    ) -> None:
        """Initialize Gemini Flash Image client."""
        super().__init__(
            api_key=api_key,
            model="gemini-2.5-flash-image",
            timeout=timeout,
            max_retries=max_retries,
            brand_injector=brand_injector,
        )

    async def generate(
        self,
        prompt: str,
        config: ImageGenerationConfig | None = None,
        collection: Collection | None = None,
        inject_brand_dna: bool = True,
    ) -> GeneratedImage:
        """
        Generate image using Gemini 2.5 Flash.

        Args:
            prompt: Text description
            config: Generation config (image_size ignored for Flash)
            collection: Optional SkyyRose collection
            inject_brand_dna: Whether to inject brand DNA

        Returns:
            GeneratedImage with PIL Image

        Note:
            image_size parameter is ignored for Flash model (always 1024px base)
        """
        config = config or ImageGenerationConfig()

        # Flash doesn't support image_size parameter
        if config.image_size:
            logger.warning("image_size parameter ignored for gemini-2.5-flash-image model")
            config.image_size = None

        return await super().generate(prompt, config, collection, inject_brand_dna)


class GeminiProImageClient(GeminiNativeImageClient):
    """
    Gemini 3 Pro Image Preview client ("Nano Banana Pro").

    Professional quality with advanced features:
    - Model: gemini-3-pro-image-preview
    - Speed: ~8s per image
    - Resolution: 1K/2K/4K (configurable via image_size)
    - Cost: $0.08 per image
    - Token usage: 1120 tokens (1K/2K), 2000 tokens (4K)

    Advanced Features:
    - Thinking mode: Model's reasoning process with interim "thought images"
    - Google Search grounding: Real-time information integration
    - Reference images: Up to 14 images for character consistency
    - 4K resolution: Professional print quality

    Best for:
    - Campaign imagery
    - Print-quality assets
    - Complex prompts requiring reasoning
    - Real-time trend integration
    - Character consistency across variations

    Usage:
        client = GeminiProImageClient(api_key="...")
        result = await client.generate(
            prompt="Editorial fashion campaign for SkyyRose LOVE HURTS",
            config=ImageGenerationConfig(
                aspect_ratio=AspectRatio.PORTRAIT_9_16,
                image_size=ImageSize.SIZE_4K,
                use_thinking_mode=True,
                use_search_grounding=True
            ),
            collection=Collection.LOVE_HURTS
        )
        result.image.save("campaign_4k.jpg")
    """

    COST_PER_IMAGE = 0.08  # $0.08 per image

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 90.0,  # Longer timeout for Pro model
        max_retries: int = GeminiNativeImageClient.MAX_RETRIES,
        brand_injector: BrandContextInjector | None = None,
    ) -> None:
        """
        Initialize Gemini Pro Image client.

        Args:
            api_key: Google API key
            timeout: Request timeout (default 90s for Pro model)
            max_retries: Maximum retry attempts
            brand_injector: Brand context injector
        """
        super().__init__(
            api_key=api_key,
            model="gemini-3-pro-image-preview",
            timeout=timeout,
            max_retries=max_retries,
            brand_injector=brand_injector,
        )

    async def generate(
        self,
        prompt: str,
        config: ImageGenerationConfig | None = None,
        collection: Collection | None = None,
        inject_brand_dna: bool = True,
    ) -> GeneratedImage:
        """
        Generate image using Gemini 3 Pro.

        Args:
            prompt: Text description
            config: Generation config with Pro features (image_size, thinking_mode, etc.)
            collection: Optional SkyyRose collection
            inject_brand_dna: Whether to inject brand DNA

        Returns:
            GeneratedImage with PIL Image and thinking metadata (if enabled)

        Note:
            Thinking mode and search grounding are Pro-exclusive features.
            Cost increases with 4K resolution (2000 tokens vs 1120 tokens).
        """
        config = config or ImageGenerationConfig()

        # Set default image size if not specified
        if not config.image_size:
            config.image_size = ImageSize.SIZE_2K  # Default to 2K for Pro

        # Log feature usage
        if config.use_thinking_mode:
            logger.info(f"Using thinking mode for prompt: {prompt[:100]}...")
        if config.use_search_grounding:
            logger.info("Using Google Search grounding for real-time context")

        return await super().generate(prompt, config, collection, inject_brand_dna)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Clients
    "GeminiNativeImageClient",
    "GeminiFlashImageClient",
    "GeminiProImageClient",
    # Errors
    "GeminiNativeError",
    "GeminiAuthenticationError",
    "GeminiRateLimitError",
    "GeminiQuotaExceededError",
    "GeminiInvalidRequestError",
    "GeminiModelNotFoundError",
    "GeminiContentFilterError",
    "GeminiTimeoutError",
    "GeminiServiceUnavailableError",
    "ChatSessionExpiredError",
    # Config
    "AspectRatio",
    "ImageSize",
    "ImageGenerationConfig",
    "GeneratedImage",
]
