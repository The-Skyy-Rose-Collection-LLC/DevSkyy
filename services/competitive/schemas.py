# services/competitive/schemas.py
"""Schema definitions for competitor asset analysis.

Implements US-034: Competitor image upload and tagging.

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


class CompetitorCategory(str, Enum):
    """Category of competitor."""

    DIRECT = "direct"  # Direct competitors in same market
    INDIRECT = "indirect"  # Adjacent market competitors
    ASPIRATIONAL = "aspirational"  # Brands to emulate
    EMERGING = "emerging"  # Up-and-coming competitors


class PricePositioning(str, Enum):
    """Price positioning relative to our brand."""

    BUDGET = "budget"
    MID_RANGE = "mid_range"
    PREMIUM = "premium"
    LUXURY = "luxury"
    ULTRA_LUXURY = "ultra_luxury"


class CompositionType(str, Enum):
    """Type of image composition."""

    FLAT_LAY = "flat_lay"
    ON_MODEL = "on_model"
    GHOST_MANNEQUIN = "ghost_mannequin"
    STILL_LIFE = "still_life"
    LIFESTYLE = "lifestyle"
    DETAIL_SHOT = "detail_shot"
    OTHER = "other"


class StyleCategory(str, Enum):
    """Style category of the product."""

    MINIMALIST = "minimalist"
    BOLD = "bold"
    CLASSIC = "classic"
    AVANT_GARDE = "avant_garde"
    STREETWEAR = "streetwear"
    BOHEMIAN = "bohemian"
    ROMANTIC = "romantic"
    EDGY = "edgy"
    SPORTY = "sporty"
    OTHER = "other"


# =============================================================================
# Competitor Models
# =============================================================================


class Competitor(BaseModel):
    """Competitor brand information."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1, max_length=100, description="Competitor brand name")
    category: CompetitorCategory = Field(CompetitorCategory.DIRECT)
    price_positioning: PricePositioning = Field(PricePositioning.PREMIUM)
    website: HttpUrl | None = Field(None, description="Competitor website URL")
    notes: str | None = Field(None, max_length=500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_by: str | None = None


class CompetitorCreate(BaseModel):
    """Request to create a competitor."""

    name: str = Field(..., min_length=1, max_length=100)
    category: CompetitorCategory = Field(CompetitorCategory.DIRECT)
    price_positioning: PricePositioning = Field(PricePositioning.PREMIUM)
    website: HttpUrl | None = None
    notes: str | None = None


# =============================================================================
# Competitor Asset Models
# =============================================================================


class ExtractedAttributes(BaseModel):
    """Attributes auto-extracted from competitor image."""

    composition_type: CompositionType = Field(CompositionType.OTHER)
    style_category: StyleCategory = Field(StyleCategory.OTHER)
    primary_colors: list[str] = Field(default_factory=list)
    detected_materials: list[str] = Field(default_factory=list)
    mood_tags: list[str] = Field(default_factory=list)
    quality_assessment: str | None = Field(None, description="Assessment of image/product quality")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)


class CompetitorAsset(BaseModel):
    """A competitor's product image for analysis."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    competitor_id: str = Field(..., description="Reference to competitor")
    url: str = Field(..., description="Original image URL or R2 URL")
    product_type: str | None = Field(None, description="Type of product")
    product_name: str | None = Field(None, description="Product name if known")
    estimated_price: float | None = Field(None, ge=0, description="Estimated price point")
    currency: str = Field("USD", max_length=3)

    # Auto-extracted attributes
    extracted_attributes: ExtractedAttributes | None = None

    # Manual tags
    manual_tags: list[str] = Field(default_factory=list)
    notes: str | None = Field(None, max_length=1000)

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_by: str | None = None
    source_url: HttpUrl | None = Field(None, description="Original source page URL")


class CompetitorAssetCreate(BaseModel):
    """Request to upload a competitor asset."""

    competitor_id: str = Field(..., description="ID of competitor brand")
    url: HttpUrl = Field(..., description="Image URL to analyze")
    product_type: str | None = Field(None)
    product_name: str | None = Field(None)
    estimated_price: float | None = Field(None, ge=0)
    currency: str = Field("USD", max_length=3)
    manual_tags: list[str] = Field(default_factory=list)
    notes: str | None = Field(None, max_length=1000)
    source_url: HttpUrl | None = Field(None)


class CompetitorAssetUpdate(BaseModel):
    """Request to update competitor asset."""

    product_type: str | None = None
    product_name: str | None = None
    estimated_price: float | None = None
    currency: str | None = None
    manual_tags: list[str] | None = None
    notes: str | None = None


# =============================================================================
# Query/Filter Models
# =============================================================================


class CompetitorAssetFilter(BaseModel):
    """Filter for competitor assets."""

    competitor_id: str | None = None
    competitor_category: CompetitorCategory | None = None
    price_positioning: PricePositioning | None = None
    composition_type: CompositionType | None = None
    style_category: StyleCategory | None = None
    tags: list[str] | None = None


# =============================================================================
# Response Models
# =============================================================================


class CompetitorListResponse(BaseModel):
    """List of competitors."""

    total: int = 0
    competitors: list[Competitor] = Field(default_factory=list)


class CompetitorAssetListResponse(BaseModel):
    """List of competitor assets."""

    total: int = 0
    page: int = 1
    page_size: int = 20
    assets: list[CompetitorAsset] = Field(default_factory=list)


# =============================================================================
# Analytics Models
# =============================================================================


class StyleDistribution(BaseModel):
    """Distribution of styles across competitor assets."""

    style: StyleCategory
    count: int
    percentage: float


class CompositionDistribution(BaseModel):
    """Distribution of composition types."""

    composition: CompositionType
    count: int
    percentage: float


class PriceAnalytics(BaseModel):
    """Price analytics for competitor products."""

    competitor_id: str
    competitor_name: str
    average_price: float | None
    min_price: float | None
    max_price: float | None
    asset_count: int


class StyleAnalyticsResponse(BaseModel):
    """Analytics response for style distribution."""

    total_assets: int = 0
    style_distribution: list[StyleDistribution] = Field(default_factory=list)
    composition_distribution: list[CompositionDistribution] = Field(default_factory=list)
    top_colors: list[dict[str, Any]] = Field(default_factory=list)
    top_materials: list[dict[str, Any]] = Field(default_factory=list)
    price_by_competitor: list[PriceAnalytics] = Field(default_factory=list)
