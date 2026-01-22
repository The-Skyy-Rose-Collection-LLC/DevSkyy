# services/three_d/gemini_provider.py
"""Gemini Image Generation Provider (Nano Banana Pro).

Provides image generation using Google's Gemini API with native
image generation capabilities (Nano Banana / Nano Banana Pro).

Features:
- Text-to-image generation
- Image editing (image-to-image)
- Multi-turn image editing
- 4K output (Pro)
- Up to 14 reference images (Pro)
- Google Search grounding (Pro)

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from services.ml.gemini_client import (
    AspectRatio,
    GeminiClient,
    GeminiConfig,
    GeminiError,
    GeminiModel,
    ImageGenerationRequest,
    ImageGenerationResponse,
    ImageInput,
    ImageSize,
)
from services.three_d.provider_interface import (
    OutputFormat,
    ProviderHealth,
    ProviderStatus,
    QualityLevel,
    ThreeDCapability,
    ThreeDGenerationError,
    ThreeDProviderError,
    ThreeDRequest,
    ThreeDResponse,
)

logger = logging.getLogger(__name__)


class GeminiImageProvider:
    """
    Gemini image generation provider (Nano Banana Pro).

    Implements I3DProvider protocol for integration with the
    ThreeDProviderFactory, plus additional image-specific methods.

    Usage:
        async with GeminiImageProvider() as provider:
            # Text-to-image
            response = await provider.generate_from_text(
                ThreeDRequest(prompt="A luxury handbag on marble")
            )

            # Image editing
            response = await provider.edit_image(
                image_url="https://...",
                instruction="Change background to studio lighting"
            )
    """

    def __init__(
        self,
        api_key: str | None = None,
        default_model: GeminiModel = GeminiModel.PRO_IMAGE,
    ) -> None:
        """Initialize Gemini image provider.

        Args:
            api_key: Google AI API key (uses env var if not provided)
            default_model: Default model for generation (Nano Banana Pro)
        """
        config = GeminiConfig()
        if api_key:
            config.api_key = api_key
        config.image_model = default_model

        self._client = GeminiClient(config)
        self._default_model = default_model

    @property
    def name(self) -> str:
        """Provider name identifier."""
        return "gemini_nano_banana"

    @property
    def capabilities(self) -> list[ThreeDCapability]:
        """List of supported capabilities."""
        return [
            ThreeDCapability.TEXT_TO_3D,  # Text-to-image
            ThreeDCapability.IMAGE_TO_3D,  # Image editing
            ThreeDCapability.TEXTURE_GENERATION,  # Texture/background gen
        ]

    async def __aenter__(self) -> GeminiImageProvider:
        """Enter async context."""
        await self._client.connect()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context."""
        await self.close()

    async def close(self) -> None:
        """Close provider resources."""
        await self._client.close()

    # =========================================================================
    # I3DProvider Implementation
    # =========================================================================

    async def generate_from_text(
        self,
        request: ThreeDRequest,
    ) -> ThreeDResponse:
        """Generate image from text prompt.

        Uses Nano Banana Pro for high-quality image generation.

        Args:
            request: ThreeDRequest with prompt set

        Returns:
            ThreeDResponse with generated image URL
        """
        if not request.prompt:
            raise ThreeDProviderError(
                "Prompt is required for text-to-image generation",
                provider=self.name,
            )

        task_id = str(uuid.uuid4())
        start_time = datetime.now(UTC)

        try:
            # Map quality to image size
            image_size = self._quality_to_size(request.quality)

            # Build generation request
            gen_request = ImageGenerationRequest(
                prompt=request.prompt,
                aspect_ratio=AspectRatio.SQUARE,  # Default
                image_size=image_size,
                model=self._default_model,
                number_of_images=1,
                product_name=request.product_name,
                collection=request.collection,
                style="luxury",  # SkyyRose default
            )

            # Generate
            result = await self._client.generate_image(gen_request)

            if not result.success or not result.images:
                raise ThreeDGenerationError(
                    "Image generation failed",
                    provider=self.name,
                    task_id=task_id,
                )

            # Convert to response
            image = result.images[0]
            duration = (datetime.now(UTC) - start_time).total_seconds()

            return ThreeDResponse(
                success=True,
                task_id=task_id,
                status="completed",
                model_url=image.to_data_uri(),  # Base64 data URI
                output_format=OutputFormat.GLB,  # Marker, actual is PNG
                provider=self.name,
                duration_seconds=duration,
                created_at=start_time,
                completed_at=datetime.now(UTC),
                correlation_id=request.correlation_id,
                metadata={
                    "model_used": result.model_used,
                    "image_mime_type": image.mime_type,
                    "prompt": request.prompt,
                },
            )

        except GeminiError as e:
            logger.error(f"Gemini generation error: {e}")
            raise ThreeDGenerationError(
                str(e),
                provider=self.name,
                task_id=task_id,
                correlation_id=request.correlation_id,
                cause=e,
            )

    async def generate_from_image(
        self,
        request: ThreeDRequest,
    ) -> ThreeDResponse:
        """Generate/edit image from reference image.

        Uses Nano Banana Pro for image editing/transformation.

        Args:
            request: ThreeDRequest with image_url or image_path set

        Returns:
            ThreeDResponse with generated image
        """
        image_source = request.get_image_source()
        if not image_source:
            raise ThreeDProviderError(
                "Image URL or path required for image-to-image",
                provider=self.name,
            )

        task_id = str(uuid.uuid4())
        start_time = datetime.now(UTC)

        try:
            # Download reference image
            ref_image = await ImageInput.from_url(image_source)

            # Build prompt for editing
            prompt = request.prompt or "Enhance this product image for e-commerce"

            # Build generation request with reference
            gen_request = ImageGenerationRequest(
                prompt=prompt,
                reference_images=[ref_image],
                aspect_ratio=AspectRatio.SQUARE,
                image_size=self._quality_to_size(request.quality),
                model=self._default_model,
                number_of_images=1,
                product_name=request.product_name,
                collection=request.collection,
                style="luxury",
            )

            # Generate
            result = await self._client.generate_image(gen_request)

            if not result.success or not result.images:
                raise ThreeDGenerationError(
                    "Image editing failed",
                    provider=self.name,
                    task_id=task_id,
                )

            image = result.images[0]
            duration = (datetime.now(UTC) - start_time).total_seconds()

            return ThreeDResponse(
                success=True,
                task_id=task_id,
                status="completed",
                model_url=image.to_data_uri(),
                output_format=OutputFormat.GLB,
                provider=self.name,
                duration_seconds=duration,
                created_at=start_time,
                completed_at=datetime.now(UTC),
                correlation_id=request.correlation_id,
                metadata={
                    "model_used": result.model_used,
                    "image_mime_type": image.mime_type,
                    "source_image": image_source,
                    "prompt": prompt,
                },
            )

        except GeminiError as e:
            logger.error(f"Gemini edit error: {e}")
            raise ThreeDGenerationError(
                str(e),
                provider=self.name,
                task_id=task_id,
                correlation_id=request.correlation_id,
                cause=e,
            )

    async def health_check(self) -> ProviderHealth:
        """Check provider health and availability."""
        try:
            result = await self._client.health_check()

            if result.get("status") == "healthy":
                return ProviderHealth(
                    provider=self.name,
                    status=ProviderStatus.AVAILABLE,
                    capabilities=self.capabilities,
                    last_check=datetime.now(UTC),
                )
            else:
                return ProviderHealth(
                    provider=self.name,
                    status=ProviderStatus.UNAVAILABLE,
                    capabilities=[],
                    last_check=datetime.now(UTC),
                    error_message=result.get("error"),
                )

        except Exception as e:
            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.UNAVAILABLE,
                capabilities=[],
                last_check=datetime.now(UTC),
                error_message=str(e),
            )

    # =========================================================================
    # Extended Image Generation Methods
    # =========================================================================

    async def generate_product_image(
        self,
        prompt: str,
        *,
        product_name: str | None = None,
        collection: str | None = None,
        aspect_ratio: AspectRatio = AspectRatio.SQUARE,
        quality: QualityLevel = QualityLevel.PRODUCTION,
    ) -> ImageGenerationResponse:
        """Generate product image for SkyyRose.

        Optimized for luxury fashion product imagery.

        Args:
            prompt: Image generation prompt
            product_name: Product name for context
            collection: Collection name (e.g., "Black Rose")
            aspect_ratio: Output aspect ratio
            quality: Quality level

        Returns:
            ImageGenerationResponse with generated images
        """
        # Build luxury fashion prompt
        full_prompt = f"""Create a professional luxury fashion product image.

{prompt}

Style: High-end fashion photography
Lighting: Professional studio lighting
Background: Clean, minimal
Quality: Premium e-commerce ready
Brand aesthetic: Sophisticated, bold, luxurious"""

        if collection:
            full_prompt += f"\nCollection: {collection}"

        request = ImageGenerationRequest(
            prompt=full_prompt,
            aspect_ratio=aspect_ratio,
            image_size=self._quality_to_size(quality),
            model=self._default_model,
            number_of_images=1,
            product_name=product_name,
            collection=collection,
            style="luxury",
        )

        return await self._client.generate_image(request)

    async def edit_product_image(
        self,
        image_url: str,
        instruction: str,
        *,
        preserve_product: bool = True,
    ) -> ImageGenerationResponse:
        """Edit product image while preserving brand integrity.

        CRITICAL: Does NOT modify logos, branding, colors, or features.

        Args:
            image_url: Source image URL
            instruction: Edit instruction
            preserve_product: If True, protects product integrity

        Returns:
            ImageGenerationResponse with edited image
        """
        return await self._client.edit_image(
            image_url,
            instruction,
            model=self._default_model,
            preserve_original=preserve_product,
        )

    async def generate_background(
        self,
        product_image_url: str,
        background_prompt: str,
        *,
        maintain_product: bool = True,
    ) -> ImageGenerationResponse:
        """Generate new background for product image.

        Keeps the product intact, replaces/enhances background.

        Args:
            product_image_url: Product image URL
            background_prompt: Desired background description
            maintain_product: Keep product unchanged

        Returns:
            ImageGenerationResponse with new background
        """
        instruction = f"""Replace the background with: {background_prompt}

IMPORTANT: Keep the product EXACTLY as it is:
- Do NOT modify the product shape, color, or features
- Do NOT modify any logos or branding
- Only change the background/environment"""

        return await self.edit_product_image(
            product_image_url,
            instruction,
            preserve_product=maintain_product,
        )

    # =========================================================================
    # Multi-turn Editing
    # =========================================================================

    def start_editing_session(self) -> None:
        """Start a new multi-turn editing session."""
        self._client.start_conversation()

    async def continue_editing(
        self,
        instruction: str,
        *,
        new_image: str | None = None,
    ) -> ImageGenerationResponse:
        """Continue multi-turn editing session.

        Args:
            instruction: Next edit instruction
            new_image: Optional new reference image URL

        Returns:
            ImageGenerationResponse with edited image
        """
        image_input = None
        if new_image:
            image_input = await ImageInput.from_url(new_image)

        return await self._client.continue_conversation(
            instruction,
            image=image_input,
            model=self._default_model,
        )

    # =========================================================================
    # Helpers
    # =========================================================================

    def _quality_to_size(self, quality: QualityLevel) -> ImageSize:
        """Map quality level to image size."""
        mapping = {
            QualityLevel.DRAFT: ImageSize.SIZE_1K,
            QualityLevel.STANDARD: ImageSize.SIZE_2K,
            QualityLevel.PRODUCTION: ImageSize.SIZE_4K,
        }
        return mapping.get(quality, ImageSize.SIZE_2K)


__all__ = [
    "GeminiImageProvider",
]
