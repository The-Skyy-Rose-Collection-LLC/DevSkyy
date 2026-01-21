# api/v1/descriptions.py
"""API endpoints for image-to-description pipeline.

Implements US-029: Image-to-description pipeline.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from security.jwt_oauth2_auth import TokenPayload, get_current_user
from services.ml.image_description_pipeline import (
    ImageDescriptionPipeline,
    VisionModelClient,
)
from services.ml.schemas.description import (
    BatchDescriptionOutput,
    BatchDescriptionRequest,
    DescriptionOutput,
    DescriptionRequest,
    DescriptionStyle,
    ExtractedFeatures,
    FeatureExtractionRequest,
    ProductType,
    VisionModel,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/descriptions", tags=["descriptions"])


# =============================================================================
# Dependency Injection
# =============================================================================


def get_vision_client() -> VisionModelClient:
    """Get vision model client."""
    return VisionModelClient()


def get_pipeline(
    vision_client: VisionModelClient = Depends(get_vision_client),
) -> ImageDescriptionPipeline:
    """Get description pipeline."""
    return ImageDescriptionPipeline(vision_client=vision_client)


# =============================================================================
# Request/Response Models
# =============================================================================


class QuickDescriptionRequest(DescriptionRequest):
    """Simplified request for quick description generation."""

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "image_url": "https://example.com/product.jpg",
                "product_name": "Black Rose Midi Dress",
                "product_type": "apparel",
                "style": "luxury",
                "target_word_count": 150,
            }
        }


class BatchStatusResponse(BatchDescriptionOutput):
    """Batch job status response."""

    webhook_sent: bool = False
    webhook_url: str | None = None


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/generate", response_model=DescriptionOutput)
async def generate_description(
    request: DescriptionRequest,
    pipeline: ImageDescriptionPipeline = Depends(get_pipeline),
    current_user: TokenPayload = Depends(get_current_user),
) -> DescriptionOutput:
    """Generate product description from image.

    Analyzes the image and generates:
    - Full product description (100-200 words)
    - Short description (< 50 words)
    - Bullet points (5-7)
    - SEO content (title, meta description, keywords)
    - Suggested tags (10-15)
    - Extracted visual features (colors, materials, style)
    """
    try:
        logger.info(
            f"Generating description for {request.image_url} "
            f"(user: {current_user.sub}, style: {request.style})"
        )

        result = await pipeline.generate_description(request)

        logger.info(
            f"Generated description: {result.word_count} words "
            f"in {result.processing_time_ms}ms"
        )

        return result

    except Exception as e:
        logger.error(f"Description generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/quick", response_model=DescriptionOutput)
async def generate_quick_description(
    image_url: str = Query(..., description="URL of image to analyze"),
    product_type: ProductType = Query(ProductType.APPAREL),
    style: DescriptionStyle = Query(DescriptionStyle.LUXURY),
    pipeline: ImageDescriptionPipeline = Depends(get_pipeline),
    current_user: TokenPayload = Depends(get_current_user),
) -> DescriptionOutput:
    """Quick description generation with minimal parameters.

    Simplified endpoint for fast description generation using query parameters.
    """
    request = DescriptionRequest(
        image_url=image_url,
        product_type=product_type,
        style=style,
        model=VisionModel.LLAVA_13B,  # Use faster model
        target_word_count=100,  # Shorter target
    )

    return await generate_description(request, pipeline, current_user)


@router.post("/generate/batch", response_model=BatchStatusResponse)
async def generate_batch_descriptions(
    request: BatchDescriptionRequest,
    background_tasks: BackgroundTasks,
    pipeline: ImageDescriptionPipeline = Depends(get_pipeline),
    current_user: TokenPayload = Depends(get_current_user),
) -> BatchStatusResponse:
    """Generate descriptions for multiple images.

    Processes up to 50 images in a single request.
    If callback_url is provided, sends results via webhook when complete.
    """
    try:
        logger.info(
            f"Starting batch description: {len(request.requests)} images "
            f"(user: {current_user.sub})"
        )

        # Process batch
        result = await pipeline.generate_batch(request, max_concurrent=5)

        # Send webhook if configured
        webhook_sent = False
        if request.callback_url:
            background_tasks.add_task(
                _send_webhook,
                request.callback_url,
                result.model_dump(),
            )
            webhook_sent = True

        return BatchStatusResponse(
            **result.model_dump(),
            webhook_sent=webhook_sent,
            webhook_url=request.callback_url,
        )

    except Exception as e:
        logger.error(f"Batch description failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-features", response_model=ExtractedFeatures)
async def extract_features(
    request: FeatureExtractionRequest,
    pipeline: ImageDescriptionPipeline = Depends(get_pipeline),
    current_user: TokenPayload = Depends(get_current_user),
) -> ExtractedFeatures:
    """Extract visual features from image without generating description.

    Returns:
    - Colors (name, hex, category, prominence)
    - Materials (name, texture, quality indicator)
    - Style attributes (aesthetic, mood, occasion, season)
    - Detected elements
    """
    try:
        logger.info(f"Extracting features from {request.image_url}")

        result = await pipeline.extract_features(request)

        return result

    except Exception as e:
        logger.error(f"Feature extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=list[dict[str, Any]])
async def list_models(
    current_user: TokenPayload = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """List available vision models.

    Returns available models with their characteristics.
    """
    return [
        {
            "id": VisionModel.LLAVA_34B.value,
            "name": "LLaVA 34B",
            "description": "Highest quality, best for detailed descriptions",
            "speed": "slow",
            "quality": "highest",
            "recommended_for": ["full descriptions", "luxury content", "detailed analysis"],
        },
        {
            "id": VisionModel.LLAVA_13B.value,
            "name": "LLaVA 13B",
            "description": "Good balance of speed and quality",
            "speed": "medium",
            "quality": "high",
            "recommended_for": ["quick descriptions", "batch processing", "feature extraction"],
        },
        {
            "id": VisionModel.BLIP2.value,
            "name": "BLIP-2",
            "description": "Fast fallback model",
            "speed": "fast",
            "quality": "good",
            "recommended_for": ["fallback", "basic captions", "high volume"],
        },
    ]


@router.get("/styles", response_model=list[dict[str, Any]])
async def list_styles(
    current_user: TokenPayload = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """List available description styles.

    Returns available writing styles with examples.
    """
    return [
        {
            "id": DescriptionStyle.LUXURY.value,
            "name": "Luxury",
            "description": "Sophisticated, evocative language for high-end fashion",
            "brand_voice": "SkyyRose - Where Love Meets Luxury",
            "example_tone": "Crafted with precision, this piece embodies effortless elegance...",
        },
        {
            "id": DescriptionStyle.CASUAL.value,
            "name": "Casual",
            "description": "Friendly, approachable language for everyday wear",
            "example_tone": "Your new go-to piece that works with everything in your closet...",
        },
        {
            "id": DescriptionStyle.TECHNICAL.value,
            "name": "Technical",
            "description": "Detailed specifications and construction information",
            "example_tone": "Constructed from 100% organic cotton with reinforced stitching...",
        },
        {
            "id": DescriptionStyle.MINIMAL.value,
            "name": "Minimal",
            "description": "Clean, essential descriptions with no fluff",
            "example_tone": "Black silk midi. Relaxed fit. Hidden zip.",
        },
        {
            "id": DescriptionStyle.STORYTELLING.value,
            "name": "Storytelling",
            "description": "Narrative-driven descriptions that create emotional connection",
            "example_tone": "She walks into the room and everything stops...",
        },
    ]


@router.get("/health")
async def health_check(
    vision_client: VisionModelClient = Depends(get_vision_client),
) -> dict[str, Any]:
    """Check health of description service.

    Returns status of vision models and service availability.
    """
    # Check primary model
    primary_ok = await vision_client.health_check(VisionModel.LLAVA_34B)
    fallback_ok = await vision_client.health_check(VisionModel.BLIP2)

    return {
        "status": "healthy" if (primary_ok or fallback_ok) else "degraded",
        "models": {
            "llava_34b": "available" if primary_ok else "unavailable",
            "llava_13b": "not_checked",
            "blip2": "available" if fallback_ok else "unavailable",
        },
        "service": "descriptions",
        "version": "1.0.0",
    }


# =============================================================================
# Helper Functions
# =============================================================================


async def _send_webhook(url: str, data: dict[str, Any]) -> None:
    """Send webhook notification.

    Args:
        url: Webhook URL
        data: Data to send
    """
    try:
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=30.0,
            )
            response.raise_for_status()
            logger.info(f"Webhook sent to {url}: {response.status_code}")
    except Exception as e:
        logger.error(f"Webhook failed: {e}")
