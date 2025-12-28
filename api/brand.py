"""
Brand Context API Endpoints
===========================

Real SkyyRose brand configuration endpoints.
Exposes brand DNA, collections, and styling for frontend consumption.

Author: DevSkyy Platform Team
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from orchestration.brand_context import COLLECTION_CONTEXT, SKYYROSE_BRAND, Collection

logger = logging.getLogger(__name__)

brand_router = APIRouter(tags=["Brand"])


# =============================================================================
# Response Models
# =============================================================================


class ColorInfo(BaseModel):
    """Color information."""

    name: str
    hex: str
    rgb: str


class ToneInfo(BaseModel):
    """Brand tone information."""

    primary: str
    descriptors: list[str]
    avoid: list[str]


class TypographyInfo(BaseModel):
    """Typography information."""

    heading: str
    body: str
    accent: str


class AudienceInfo(BaseModel):
    """Target audience information."""

    age_range: str
    description: str
    interests: list[str]
    values: list[str]


class CollectionInfo(BaseModel):
    """Collection information."""

    id: str
    name: str
    tagline: str
    mood: str
    colors: str
    style: str
    description: str


class BrandResponse(BaseModel):
    """Complete brand information."""

    name: str
    tagline: str
    philosophy: str
    location: str
    tone: ToneInfo
    colors: dict[str, ColorInfo]
    typography: TypographyInfo
    target_audience: AudienceInfo
    product_types: list[str]
    quality_descriptors: list[str]
    collections: list[CollectionInfo]


class BrandSummary(BaseModel):
    """Lightweight brand summary."""

    name: str
    tagline: str
    philosophy: str
    primary_color: str
    accent_color: str


# =============================================================================
# Endpoints
# =============================================================================


@brand_router.get("/brand", response_model=BrandResponse)
async def get_brand() -> BrandResponse:
    """Get complete brand configuration."""
    brand = SKYYROSE_BRAND

    # Build colors dict
    colors = {}
    for key, value in brand.get("colors", {}).items():
        colors[key] = ColorInfo(
            name=value.get("name", key),
            hex=value.get("hex", "#000000"),
            rgb=value.get("rgb", "0, 0, 0"),
        )

    # Build tone info
    tone_data = brand.get("tone", {})
    tone = ToneInfo(
        primary=tone_data.get("primary", ""),
        descriptors=tone_data.get("descriptors", []),
        avoid=tone_data.get("avoid", []),
    )

    # Build typography
    typo_data = brand.get("typography", {})
    typography = TypographyInfo(
        heading=typo_data.get("heading", "sans-serif"),
        body=typo_data.get("body", "sans-serif"),
        accent=typo_data.get("accent", "serif"),
    )

    # Build audience info
    audience_data = brand.get("target_audience", {})
    audience = AudienceInfo(
        age_range=audience_data.get("age_range", "18-35"),
        description=audience_data.get("description", ""),
        interests=audience_data.get("interests", []),
        values=audience_data.get("values", []),
    )

    # Build collections
    collections = []
    for collection_enum, context in COLLECTION_CONTEXT.items():
        collections.append(
            CollectionInfo(
                id=collection_enum.value,
                name=context.get("name", ""),
                tagline=context.get("tagline", ""),
                mood=context.get("mood", ""),
                colors=context.get("colors", ""),
                style=context.get("style", ""),
                description=context.get("description", ""),
            )
        )

    return BrandResponse(
        name=brand.get("name", "The Skyy Rose Collection"),
        tagline=brand.get("tagline", ""),
        philosophy=brand.get("philosophy", ""),
        location=brand.get("location", ""),
        tone=tone,
        colors=colors,
        typography=typography,
        target_audience=audience,
        product_types=brand.get("product_types", []),
        quality_descriptors=brand.get("quality_descriptors", []),
        collections=collections,
    )


@brand_router.get("/brand/summary", response_model=BrandSummary)
async def get_brand_summary() -> BrandSummary:
    """Get lightweight brand summary."""
    brand = SKYYROSE_BRAND
    colors = brand.get("colors", {})

    return BrandSummary(
        name=brand.get("name", "The Skyy Rose Collection"),
        tagline=brand.get("tagline", ""),
        philosophy=brand.get("philosophy", ""),
        primary_color=colors.get("primary", {}).get("hex", "#1A1A1A"),
        accent_color=colors.get("accent", {}).get("hex", "#D4AF37"),
    )


@brand_router.get("/brand/colors", response_model=dict[str, ColorInfo])
async def get_brand_colors() -> dict[str, ColorInfo]:
    """Get brand color palette."""
    colors = {}
    for key, value in SKYYROSE_BRAND.get("colors", {}).items():
        colors[key] = ColorInfo(
            name=value.get("name", key),
            hex=value.get("hex", "#000000"),
            rgb=value.get("rgb", "0, 0, 0"),
        )
    return colors


@brand_router.get("/brand/collections", response_model=list[CollectionInfo])
async def list_collections() -> list[CollectionInfo]:
    """List all collections."""
    collections = []
    for collection_enum, context in COLLECTION_CONTEXT.items():
        collections.append(
            CollectionInfo(
                id=collection_enum.value,
                name=context.get("name", ""),
                tagline=context.get("tagline", ""),
                mood=context.get("mood", ""),
                colors=context.get("colors", ""),
                style=context.get("style", ""),
                description=context.get("description", ""),
            )
        )
    return collections


@brand_router.get("/brand/collections/{collection_id}", response_model=CollectionInfo)
async def get_collection(collection_id: str) -> CollectionInfo:
    """Get a specific collection by ID."""
    # Normalize collection ID
    collection_id_upper = collection_id.upper().replace("-", "_")

    try:
        collection_enum = Collection(collection_id_upper)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Collection '{collection_id}' not found. "
            f"Valid collections: {[c.value for c in Collection]}",
        )

    context = COLLECTION_CONTEXT.get(collection_enum)
    if not context:
        raise HTTPException(status_code=404, detail=f"Collection '{collection_id}' not found")

    return CollectionInfo(
        id=collection_enum.value,
        name=context.get("name", ""),
        tagline=context.get("tagline", ""),
        mood=context.get("mood", ""),
        colors=context.get("colors", ""),
        style=context.get("style", ""),
        description=context.get("description", ""),
    )


@brand_router.get("/brand/tone", response_model=ToneInfo)
async def get_brand_tone() -> ToneInfo:
    """Get brand tone guidelines."""
    tone_data = SKYYROSE_BRAND.get("tone", {})
    return ToneInfo(
        primary=tone_data.get("primary", ""),
        descriptors=tone_data.get("descriptors", []),
        avoid=tone_data.get("avoid", []),
    )


@brand_router.get("/brand/typography", response_model=TypographyInfo)
async def get_brand_typography() -> TypographyInfo:
    """Get brand typography settings."""
    typo_data = SKYYROSE_BRAND.get("typography", {})
    return TypographyInfo(
        heading=typo_data.get("heading", "sans-serif"),
        body=typo_data.get("body", "sans-serif"),
        accent=typo_data.get("accent", "serif"),
    )
