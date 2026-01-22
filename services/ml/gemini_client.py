# services/ml/gemini_client.py
"""Gemini API Client for DevSkyy.

Provides async client abstraction for Google's Gemini AI models including:
- Vision analysis (image-to-text with Gemini Flash/Pro)
- Image generation (Nano Banana - Gemini 2.5 Flash Image)
- Multi-turn image editing

API Reference: https://ai.google.dev/gemini-api/docs/image-generation

CRITICAL: NEVER modify product logos, branding, labels, or features.
Only enhance, clarify, make e-commerce ready.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel, Field

from errors.production_errors import (
    DevSkyError,
    DevSkyErrorCode,
    DevSkyErrorSeverity,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_TIMEOUT = 120.0
MAX_IMAGE_SIZE_MB = 20
SUPPORTED_IMAGE_FORMATS = {"image/png", "image/jpeg", "image/gif", "image/webp"}


# =============================================================================
# Errors
# =============================================================================


class GeminiError(DevSkyError):
    """Base error for Gemini API operations."""

    def __init__(
        self,
        message: str,
        *,
        model: str | None = None,
        correlation_id: str | None = None,
        cause: Exception | None = None,
        retryable: bool = False,
    ) -> None:
        context: dict[str, Any] = {}
        if model:
            context["model"] = model

        super().__init__(
            message,
            code=DevSkyErrorCode.EXTERNAL_SERVICE_ERROR,
            severity=DevSkyErrorSeverity.ERROR,
            context=context,
            cause=cause,
            retryable=retryable,
            correlation_id=correlation_id,
        )


class GeminiRateLimitError(GeminiError):
    """Raised when Gemini API rate limit is hit."""

    def __init__(
        self,
        message: str = "Gemini API rate limit exceeded",
        retry_after_seconds: int = 60,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, retryable=True, **kwargs)
        self.retry_after_seconds = retry_after_seconds


class GeminiContentFilterError(GeminiError):
    """Raised when content is blocked by safety filters."""

    def __init__(
        self,
        message: str = "Content blocked by Gemini safety filters",
        **kwargs: Any,
    ) -> None:
        super().__init__(message, retryable=False, **kwargs)


# =============================================================================
# Enums
# =============================================================================


class GeminiModel(str, Enum):
    """Available Gemini models.

    Nano Banana = Gemini's native image generation.
    Nano Banana Pro = Gemini 3 Pro Image with 4K, text rendering, 14 refs.
    """

    # Vision/Text models (for analysis)
    FLASH_2_0 = "gemini-2.0-flash"  # Stable, fast vision
    FLASH_2_5 = "gemini-2.5-flash-preview-05-20"  # Fast vision analysis
    PRO_2_5 = "gemini-2.5-pro-preview-05-06"  # Most capable analysis

    # Image generation models (Nano Banana)
    FLASH_IMAGE = "gemini-2.5-flash-preview-native-audio-dialog"  # Nano Banana
    PRO_IMAGE = "gemini-2.0-flash-exp"  # Nano Banana Pro - 4K, text, 14 refs

    @classmethod
    def for_vision(cls) -> GeminiModel:
        """Get recommended model for vision analysis."""
        return cls.FLASH_2_0

    @classmethod
    def for_image_generation(cls) -> GeminiModel:
        """Get recommended model for image generation (Nano Banana Pro)."""
        return cls.PRO_IMAGE


class ImageSize(str, Enum):
    """Output image sizes for Gemini 3 Pro Image."""

    SIZE_1K = "1K"  # 1024 max dimension
    SIZE_2K = "2K"  # 2048 max dimension
    SIZE_4K = "4K"  # 4096 max dimension (Pro only)


class AspectRatio(str, Enum):
    """Supported aspect ratios for image generation."""

    SQUARE = "1:1"
    PORTRAIT_2_3 = "2:3"
    PORTRAIT_3_4 = "3:4"
    PORTRAIT_4_5 = "4:5"
    PORTRAIT_9_16 = "9:16"
    LANDSCAPE_3_2 = "3:2"
    LANDSCAPE_4_3 = "4:3"
    LANDSCAPE_5_4 = "5:4"
    LANDSCAPE_16_9 = "16:9"
    ULTRAWIDE = "21:9"


# =============================================================================
# Models
# =============================================================================


class ImageInput(BaseModel):
    """Image input for Gemini API."""

    url: str | None = None
    base64_data: str | None = None
    mime_type: str = "image/png"

    @classmethod
    async def from_url(cls, url: str, timeout: float = 30.0) -> ImageInput:
        """Create ImageInput from URL by downloading and encoding."""
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "image/png")
            mime_type = content_type.split(";")[0].strip()

            if mime_type not in SUPPORTED_IMAGE_FORMATS:
                logger.warning(f"Unknown image format {mime_type}, assuming image/png")
                mime_type = "image/png"

            return cls(
                base64_data=base64.b64encode(response.content).decode("utf-8"),
                mime_type=mime_type,
            )

    @classmethod
    def from_base64(cls, data: str, mime_type: str = "image/png") -> ImageInput:
        """Create ImageInput from base64 data."""
        return cls(base64_data=data, mime_type=mime_type)


class ImageGenerationRequest(BaseModel):
    """Request for Gemini image generation."""

    prompt: str = Field(..., description="Text prompt for generation")
    reference_images: list[ImageInput] = Field(
        default_factory=list,
        description="Reference images (up to 14 for Pro)",
    )
    aspect_ratio: AspectRatio = Field(default=AspectRatio.SQUARE)
    image_size: ImageSize = Field(default=ImageSize.SIZE_2K)
    model: GeminiModel = Field(default=GeminiModel.FLASH_IMAGE)
    number_of_images: int = Field(default=1, ge=1, le=4)
    use_thinking: bool = Field(
        default=False,
        description="Enable Thinking mode (Pro only)",
    )
    use_search_grounding: bool = Field(
        default=False,
        description="Enable Google Search grounding (Pro only)",
    )
    negative_prompt: str | None = Field(
        default=None,
        description="What to avoid in generation",
    )

    # SkyyRose context
    product_name: str | None = None
    collection: str | None = None
    style: str | None = "luxury"


class GeneratedImage(BaseModel):
    """Generated image from Gemini."""

    base64_data: str
    mime_type: str = "image/png"
    thought_signature: str | None = None  # For multi-turn editing
    generation_seed: int | None = None

    def save(self, path: str) -> None:
        """Save image to file."""
        data = base64.b64decode(self.base64_data)
        with open(path, "wb") as f:
            f.write(data)

    def to_data_uri(self) -> str:
        """Convert to data URI for display."""
        return f"data:{self.mime_type};base64,{self.base64_data}"


class ImageGenerationResponse(BaseModel):
    """Response from Gemini image generation."""

    success: bool
    images: list[GeneratedImage] = Field(default_factory=list)
    text_response: str | None = None  # Interleaved text if any
    model_used: str
    prompt_feedback: str | None = None
    safety_ratings: dict[str, str] = Field(default_factory=dict)
    duration_ms: int = 0


class VisionAnalysisResponse(BaseModel):
    """Response from Gemini vision analysis."""

    success: bool
    text: str
    model_used: str
    token_count: int = 0
    duration_ms: int = 0


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class GeminiConfig:
    """Gemini API configuration."""

    api_key: str = field(
        default_factory=lambda: os.getenv("GOOGLE_AI_API_KEY", "")
    )
    base_url: str = GEMINI_API_BASE
    timeout: float = DEFAULT_TIMEOUT
    max_retries: int = 3

    # Default models
    vision_model: GeminiModel = GeminiModel.FLASH_2_5
    image_model: GeminiModel = GeminiModel.FLASH_IMAGE

    @classmethod
    def from_env(cls) -> GeminiConfig:
        """Create config from environment variables."""
        return cls()

    def validate(self) -> None:
        """Validate configuration."""
        if not self.api_key:
            raise GeminiError(
                "GOOGLE_AI_API_KEY environment variable is required",
                retryable=False,
            )


# =============================================================================
# Client
# =============================================================================


class GeminiClient:
    """
    Async client for Google Gemini API.

    Provides:
    - Vision analysis (image understanding)
    - Image generation (Nano Banana)
    - Multi-turn image editing

    Usage:
        async with GeminiClient() as client:
            # Vision analysis
            result = await client.analyze_image(image_url, "Describe this product")

            # Image generation
            result = await client.generate_image("A luxury handbag on marble")
    """

    def __init__(self, config: GeminiConfig | None = None) -> None:
        self.config = config or GeminiConfig.from_env()
        self._client: httpx.AsyncClient | None = None
        self._conversation_history: list[dict[str, Any]] = []

    async def __aenter__(self) -> GeminiClient:
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
                timeout=self.config.timeout,
            )

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _build_url(self, model: str, action: str = "generateContent") -> str:
        """Build API URL."""
        return (
            f"{self.config.base_url}/models/{model}:{action}"
            f"?key={self.config.api_key}"
        )

    async def _request(
        self,
        model: str,
        contents: list[dict[str, Any]],
        *,
        generation_config: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Make request to Gemini API."""
        await self.connect()

        url = self._build_url(model)
        payload: dict[str, Any] = {"contents": contents}

        if generation_config:
            payload["generationConfig"] = generation_config

        if tools:
            payload["tools"] = tools

        for attempt in range(self.config.max_retries):
            try:
                logger.debug(
                    f"Gemini API request to {model}",
                    extra={"attempt": attempt + 1},
                )

                response = await self._client.post(url, json=payload)

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "60"))
                    raise GeminiRateLimitError(retry_after_seconds=retry_after)

                if response.status_code == 400:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "Bad request")
                    if "safety" in error_msg.lower() or "blocked" in error_msg.lower():
                        raise GeminiContentFilterError(error_msg)
                    raise GeminiError(f"Bad request: {error_msg}", retryable=False)

                if response.status_code == 401:
                    raise GeminiError("Invalid Gemini API key", retryable=False)

                if response.status_code >= 400:
                    raise GeminiError(
                        f"Gemini API error: {response.status_code} - {response.text}",
                        model=model,
                        retryable=response.status_code >= 500,
                    )

                return response.json()

            except httpx.TimeoutException:
                if attempt == self.config.max_retries - 1:
                    raise GeminiError(
                        f"Request to {model} timed out",
                        model=model,
                        retryable=True,
                    )
                await asyncio.sleep(2**attempt)

            except httpx.RequestError as e:
                if attempt == self.config.max_retries - 1:
                    raise GeminiError(
                        f"Request failed: {e}",
                        model=model,
                        cause=e,
                        retryable=True,
                    )
                await asyncio.sleep(2**attempt)

        raise GeminiError("Max retries exceeded", model=model)

    # =========================================================================
    # Vision Analysis Methods
    # =========================================================================

    async def analyze_image(
        self,
        image_url: str,
        prompt: str,
        *,
        model: GeminiModel | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> VisionAnalysisResponse:
        """Analyze image with vision model.

        Args:
            image_url: URL of image to analyze
            prompt: Analysis prompt
            model: Model to use (defaults to config.vision_model)
            max_tokens: Maximum response tokens
            temperature: Sampling temperature

        Returns:
            VisionAnalysisResponse with analysis result
        """
        import time

        start_time = time.time()
        model = model or self.config.vision_model

        # Download and encode image
        image_input = await ImageInput.from_url(image_url)

        contents = [
            {
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": image_input.mime_type,
                            "data": image_input.base64_data,
                        }
                    },
                    {"text": prompt},
                ]
            }
        ]

        generation_config = {
            "maxOutputTokens": max_tokens,
            "temperature": temperature,
        }

        response = await self._request(
            model.value,
            contents,
            generation_config=generation_config,
        )

        # Extract text from response
        text = ""
        token_count = 0

        candidates = response.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            for part in parts:
                if "text" in part:
                    text += part["text"]

        usage = response.get("usageMetadata", {})
        token_count = usage.get("candidatesTokenCount", 0)

        duration_ms = int((time.time() - start_time) * 1000)

        return VisionAnalysisResponse(
            success=bool(text),
            text=text,
            model_used=model.value,
            token_count=token_count,
            duration_ms=duration_ms,
        )

    async def generate_description(
        self,
        image_url: str,
        *,
        product_type: str = "apparel",
        style: str = "luxury",
        word_count: int = 150,
        brand_context: str | None = None,
    ) -> str:
        """Generate product description from image.

        Optimized for SkyyRose luxury fashion products.

        Args:
            image_url: Product image URL
            product_type: Type of product
            style: Writing style
            word_count: Target word count
            brand_context: Brand context to include

        Returns:
            Product description
        """
        brand_info = ""
        if brand_context:
            brand_info = f"\nBrand context: {brand_context}"

        prompt = f"""Analyze this product image and write a compelling {style} product description.

Product type: {product_type}
Target word count: {word_count}
Style: {style}{brand_info}

Write a description that:
1. Opens with an attention-grabbing hook
2. Describes key visual features and materials
3. Evokes the lifestyle and occasions
4. Ends with a call to action

Be specific about what you see. Use sensory language.
Do NOT mention any prices or sizing."""

        response = await self.analyze_image(
            image_url,
            prompt,
            max_tokens=word_count * 2,  # Allow some buffer
            temperature=0.8,
        )

        return response.text

    # =========================================================================
    # Image Generation Methods (Nano Banana)
    # =========================================================================

    async def generate_image(
        self,
        request: ImageGenerationRequest,
    ) -> ImageGenerationResponse:
        """Generate image from text and/or reference images.

        Uses Gemini's Nano Banana (native image generation).

        Args:
            request: Image generation request

        Returns:
            ImageGenerationResponse with generated images
        """
        import time

        start_time = time.time()
        model = request.model

        # Build content parts
        parts: list[dict[str, Any]] = []

        # Add reference images first (up to 14 for Pro)
        max_refs = 14 if "pro" in model.value.lower() else 2
        for i, ref_image in enumerate(request.reference_images[:max_refs]):
            if ref_image.base64_data:
                parts.append({
                    "inlineData": {
                        "mimeType": ref_image.mime_type,
                        "data": ref_image.base64_data,
                    }
                })

        # Add text prompt
        prompt = request.prompt
        if request.negative_prompt:
            prompt += f"\n\nAvoid: {request.negative_prompt}"

        # Add SkyyRose context if provided
        if request.style == "luxury":
            prompt += "\n\nStyle: Luxury, sophisticated, high-end fashion photography"
        if request.collection:
            prompt += f"\nCollection: {request.collection}"

        parts.append({"text": prompt})

        contents = [{"parts": parts}]

        # Build generation config
        generation_config: dict[str, Any] = {
            "responseModalities": ["TEXT", "IMAGE"],
        }

        # Image config varies by model
        image_config: dict[str, Any] = {
            "numberOfImages": request.number_of_images,
            "aspectRatio": request.aspect_ratio.value,
        }

        # Pro model supports 4K and additional features
        if "pro" in model.value.lower():
            image_config["imageSize"] = request.image_size.value
            if request.use_thinking:
                image_config["includeThinkingProcess"] = True

        generation_config["imageConfig"] = image_config

        # Tools (search grounding for Pro)
        tools: list[dict[str, Any]] | None = None
        if request.use_search_grounding and "pro" in model.value.lower():
            tools = [{"googleSearch": {}}]

        response = await self._request(
            model.value,
            contents,
            generation_config=generation_config,
            tools=tools,
        )

        # Parse response
        images: list[GeneratedImage] = []
        text_response: str | None = None
        prompt_feedback: str | None = None

        # Check for blocks
        if "promptFeedback" in response:
            feedback = response["promptFeedback"]
            if feedback.get("blockReason"):
                raise GeminiContentFilterError(
                    f"Prompt blocked: {feedback.get('blockReason')}"
                )
            prompt_feedback = str(feedback)

        candidates = response.get("candidates", [])
        for candidate in candidates:
            parts = candidate.get("content", {}).get("parts", [])
            for part in parts:
                if "inlineData" in part:
                    # Image response
                    inline_data = part["inlineData"]
                    images.append(
                        GeneratedImage(
                            base64_data=inline_data.get("data", ""),
                            mime_type=inline_data.get("mimeType", "image/png"),
                        )
                    )
                elif "text" in part:
                    # Text response (interleaved or description)
                    text_response = part["text"]

        # Get safety ratings
        safety_ratings: dict[str, str] = {}
        if candidates and "safetyRatings" in candidates[0]:
            for rating in candidates[0]["safetyRatings"]:
                safety_ratings[rating.get("category", "")] = rating.get(
                    "probability", ""
                )

        duration_ms = int((time.time() - start_time) * 1000)

        return ImageGenerationResponse(
            success=len(images) > 0,
            images=images,
            text_response=text_response,
            model_used=model.value,
            prompt_feedback=prompt_feedback,
            safety_ratings=safety_ratings,
            duration_ms=duration_ms,
        )

    async def edit_image(
        self,
        image_url: str,
        edit_instruction: str,
        *,
        model: GeminiModel = GeminiModel.FLASH_IMAGE,
        preserve_original: bool = True,
    ) -> ImageGenerationResponse:
        """Edit an existing image.

        CRITICAL: Does NOT modify logos, branding, or product features.

        Args:
            image_url: URL of image to edit
            edit_instruction: What to change
            model: Model to use
            preserve_original: If True, preserves product integrity

        Returns:
            ImageGenerationResponse with edited image
        """
        # Download reference image
        ref_image = await ImageInput.from_url(image_url)

        # Build safety-aware prompt
        safe_instruction = edit_instruction
        if preserve_original:
            safe_instruction = f"""IMPORTANT: Do NOT modify:
- Product logos or branding
- Product colors or textures
- Product shape or features
- Any text or labels

Only modify: {edit_instruction}"""

        request = ImageGenerationRequest(
            prompt=safe_instruction,
            reference_images=[ref_image],
            model=model,
            number_of_images=1,
        )

        return await self.generate_image(request)

    # =========================================================================
    # Multi-turn Conversation
    # =========================================================================

    def start_conversation(self) -> None:
        """Start a new multi-turn conversation."""
        self._conversation_history = []

    async def continue_conversation(
        self,
        prompt: str,
        *,
        image: ImageInput | None = None,
        model: GeminiModel | None = None,
    ) -> ImageGenerationResponse:
        """Continue multi-turn image editing conversation.

        Args:
            prompt: Next instruction
            image: Optional new image input
            model: Model to use

        Returns:
            ImageGenerationResponse
        """
        model = model or self.config.image_model

        # Build parts for this turn
        parts: list[dict[str, Any]] = []

        if image and image.base64_data:
            parts.append({
                "inlineData": {
                    "mimeType": image.mime_type,
                    "data": image.base64_data,
                }
            })

        parts.append({"text": prompt})

        # Add to history
        self._conversation_history.append({
            "role": "user",
            "parts": parts,
        })

        # Make request with full history
        response = await self._request(
            model.value,
            self._conversation_history,
            generation_config={
                "responseModalities": ["TEXT", "IMAGE"],
            },
        )

        # Parse and store assistant response
        images: list[GeneratedImage] = []
        text_response: str | None = None
        assistant_parts: list[dict[str, Any]] = []

        candidates = response.get("candidates", [])
        for candidate in candidates:
            parts = candidate.get("content", {}).get("parts", [])
            for part in parts:
                assistant_parts.append(part)
                if "inlineData" in part:
                    inline_data = part["inlineData"]
                    images.append(
                        GeneratedImage(
                            base64_data=inline_data.get("data", ""),
                            mime_type=inline_data.get("mimeType", "image/png"),
                        )
                    )
                elif "text" in part:
                    text_response = part["text"]

        # Store assistant response in history
        if assistant_parts:
            self._conversation_history.append({
                "role": "model",
                "parts": assistant_parts,
            })

        return ImageGenerationResponse(
            success=len(images) > 0,
            images=images,
            text_response=text_response,
            model_used=model.value,
            duration_ms=0,
        )

    # =========================================================================
    # Health Check
    # =========================================================================

    async def health_check(self) -> dict[str, Any]:
        """Check Gemini API health."""
        try:
            # Simple text generation to verify API key works
            response = await self._request(
                self.config.vision_model.value,
                [{"parts": [{"text": "Hello"}]}],
                generation_config={"maxOutputTokens": 5},
            )
            return {
                "status": "healthy",
                "vision_model": self.config.vision_model.value,
                "image_model": self.config.image_model.value,
            }
        except GeminiError as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }


__all__ = [
    "GeminiClient",
    "GeminiConfig",
    "GeminiError",
    "GeminiRateLimitError",
    "GeminiContentFilterError",
    "GeminiModel",
    "AspectRatio",
    "ImageSize",
    "ImageInput",
    "ImageGenerationRequest",
    "ImageGenerationResponse",
    "GeneratedImage",
    "VisionAnalysisResponse",
]
