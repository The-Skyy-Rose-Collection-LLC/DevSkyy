# services/ml/schemas/description.py
"""Schema definitions for image-to-description pipeline.

Implements US-029: Image-to-description pipeline.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl

# =============================================================================
# Enums
# =============================================================================


class DescriptionStyle(str, Enum):
    """Writing style for descriptions."""

    LUXURY = "luxury"
    CASUAL = "casual"
    TECHNICAL = "technical"
    MINIMAL = "minimal"
    STORYTELLING = "storytelling"


class ProductType(str, Enum):
    """Type of product being described."""

    APPAREL = "apparel"
    FOOTWEAR = "footwear"
    ACCESSORIES = "accessories"
    JEWELRY = "jewelry"
    HOME = "home"
    BEAUTY = "beauty"
    OTHER = "other"


class VisionModel(str, Enum):
    """Vision model to use for analysis."""

    # Replicate models
    LLAVA_34B = "yorickvp/llava-v1.6-34b"  # Primary - best quality
    LLAVA_13B = "yorickvp/llava-13b"  # Fast - lower latency
    BLIP2 = "salesforce/blip-2"  # Fallback

    # Gemini models (no rate limiting issues)
    GEMINI_FLASH = "gemini-2.5-flash-preview-05-20"  # Fast, reliable
    GEMINI_PRO = "gemini-2.5-pro-preview-05-06"  # Best quality

    def is_gemini(self) -> bool:
        """Check if this is a Gemini model."""
        return self.value.startswith("gemini-")

    def is_replicate(self) -> bool:
        """Check if this is a Replicate model."""
        return not self.is_gemini()


# =============================================================================
# Request Models
# =============================================================================


class DescriptionRequest(BaseModel):
    """Request to generate description from image."""

    image_url: HttpUrl = Field(..., description="URL of image to analyze")
    product_name: str | None = Field(None, description="Product name if known")
    product_type: ProductType = Field(ProductType.APPAREL, description="Type of product")
    style: DescriptionStyle = Field(DescriptionStyle.LUXURY, description="Writing style")
    brand_context: str | None = Field(None, description="Brand-specific context to include")
    target_word_count: int = Field(150, ge=50, le=500, description="Target word count")
    include_seo: bool = Field(True, description="Generate SEO content")
    include_bullets: bool = Field(True, description="Generate bullet points")
    include_tags: bool = Field(True, description="Generate suggested tags")
    model: VisionModel = Field(VisionModel.LLAVA_34B, description="Vision model to use")
    metadata: dict[str, Any] = Field(default_factory=dict)


class BatchDescriptionRequest(BaseModel):
    """Request for batch description generation."""

    requests: list[DescriptionRequest] = Field(
        ..., min_length=1, max_length=50, description="Images to process"
    )
    callback_url: str | None = Field(None, description="Webhook URL for completion notification")


class FeatureExtractionRequest(BaseModel):
    """Request to extract visual features only."""

    image_url: HttpUrl = Field(..., description="URL of image to analyze")
    product_type: ProductType = Field(ProductType.APPAREL)
    extract_colors: bool = Field(True)
    extract_materials: bool = Field(True)
    extract_style: bool = Field(True)
    model: VisionModel = Field(VisionModel.LLAVA_13B)  # Use faster model for features


# =============================================================================
# Response Models
# =============================================================================


class ColorInfo(BaseModel):
    """Color information extracted from image."""

    name: str = Field(..., description="Color name (e.g., 'charcoal black')")
    hex: str | None = Field(None, description="Hex code if determinable")
    category: str = Field(..., description="Color category (neutral, warm, cool)")
    prominence: float = Field(0.0, ge=0.0, le=1.0, description="How prominent in image (0-1)")


class MaterialInfo(BaseModel):
    """Material information extracted from image."""

    name: str = Field(..., description="Material name (e.g., 'premium cotton')")
    texture: str | None = Field(None, description="Texture description")
    quality_indicator: str | None = Field(
        None, description="Quality indicator (luxury, premium, standard)"
    )


class StyleAttributes(BaseModel):
    """Style attributes extracted from image."""

    aesthetic: str = Field(..., description="Overall aesthetic (minimalist, bold, etc.)")
    mood: str = Field(..., description="Mood conveyed (sophisticated, casual, etc.)")
    occasion: list[str] = Field(default_factory=list, description="Suitable occasions")
    season: list[str] = Field(default_factory=list, description="Suitable seasons")


class ExtractedFeatures(BaseModel):
    """Visual features extracted from image."""

    colors: list[ColorInfo] = Field(default_factory=list)
    materials: list[MaterialInfo] = Field(default_factory=list)
    style: StyleAttributes | None = None
    detected_elements: list[str] = Field(
        default_factory=list, description="Detected visual elements"
    )
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="Overall confidence")


class BulletPoint(BaseModel):
    """Single bullet point for product description."""

    text: str = Field(..., description="Bullet point text")
    category: str = Field("feature", description="Category: feature, material, fit, care")


class SEOContent(BaseModel):
    """SEO-optimized content."""

    title: str = Field(..., max_length=60, description="SEO title (< 60 chars)")
    meta_description: str = Field(..., max_length=160, description="Meta description (< 160 chars)")
    focus_keyword: str = Field(..., description="Primary keyword")
    secondary_keywords: list[str] = Field(default_factory=list, description="Secondary keywords")


class DescriptionOutput(BaseModel):
    """Complete description output."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    image_url: str
    product_name: str | None = None

    # Main description
    description: str = Field(..., description="Full product description (100-200 words)")
    short_description: str = Field(..., description="Short description (< 50 words)")

    # Structured content
    bullet_points: list[BulletPoint] = Field(default_factory=list)
    suggested_tags: list[str] = Field(default_factory=list)
    seo: SEOContent | None = None

    # Extracted features
    features: ExtractedFeatures | None = None

    # Metadata
    model_used: str | None = None
    word_count: int = 0
    processing_time_ms: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        """Pydantic config."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class BatchDescriptionOutput(BaseModel):
    """Output for batch description generation."""

    job_id: str = Field(default_factory=lambda: str(uuid4()))
    total: int = 0
    completed: int = 0
    failed: int = 0
    results: list[DescriptionOutput] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
