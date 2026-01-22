# services/ml/visual_feature_extractor.py
"""Visual feature extraction service using Gemini vision.

Extracts color palettes, composition, lighting, and style tags from images.
Used for brand asset training data preparation (US-013).

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Models
# =============================================================================


class ColorInfo(BaseModel):
    """Color information extracted from image."""

    hex: str = Field(..., description="Hex color code")
    name: str = Field("", description="Color name")
    prominence: float = Field(0.0, ge=0.0, le=1.0, description="How prominent in image")


class ColorPalette(BaseModel):
    """Extracted color palette from image."""

    primary: str = Field(..., description="Primary color hex")
    secondary: list[str] = Field(default_factory=list, description="Secondary colors")
    accent: str | None = Field(None, description="Accent color hex")
    all_colors: list[ColorInfo] = Field(default_factory=list, description="All detected colors")


class CompositionAnalysis(BaseModel):
    """Composition analysis of image."""

    type: str = Field(..., description="Composition type (centered, rule_of_thirds, etc.)")
    focal_point: str | None = Field(None, description="Focal point location")
    balance: str = Field("balanced", description="Visual balance")
    depth: str | None = Field(None, description="Depth perception")
    framing: str | None = Field(None, description="Framing style")


class LightingProfile(BaseModel):
    """Lighting analysis of image."""

    type: str = Field(..., description="Lighting type (natural, studio, dramatic, etc.)")
    direction: str | None = Field(None, description="Light direction")
    mood: str | None = Field(None, description="Lighting mood")
    quality: str | None = Field(None, description="Light quality (soft, hard)")
    color_temperature: str | None = Field(None, description="Warm, neutral, cool")


class VisualFeatures(BaseModel):
    """Extracted visual features from image."""

    color_palette: ColorPalette | None = None
    composition: CompositionAnalysis | None = None
    lighting: LightingProfile | None = None
    style_tags: list[str] = Field(default_factory=list)
    quality_score: float = Field(0.0, ge=0.0, le=1.0)
    detected_objects: list[str] = Field(default_factory=list)
    brand_alignment_score: float = Field(0.0, ge=0.0, le=1.0)


# =============================================================================
# Prompts
# =============================================================================

VISUAL_FEATURES_PROMPT = """Analyze this image and extract visual features for luxury fashion brand training.

Return a JSON object with the following structure:
{
    "color_palette": {
        "primary": "#hexcode",
        "secondary": ["#hex1", "#hex2"],
        "accent": "#hexcode or null",
        "all_colors": [
            {"hex": "#hexcode", "name": "color name", "prominence": 0.0-1.0}
        ]
    },
    "composition": {
        "type": "centered|rule_of_thirds|symmetrical|diagonal|framed",
        "focal_point": "center|left|right|top|bottom|corner",
        "balance": "balanced|asymmetrical|dynamic",
        "depth": "flat|shallow|deep",
        "framing": "tight|medium|wide|environmental"
    },
    "lighting": {
        "type": "natural|studio|dramatic|ambient|mixed",
        "direction": "front|side|back|top|bottom|diffused",
        "mood": "bright|moody|warm|cool|neutral",
        "quality": "soft|hard|mixed",
        "color_temperature": "warm|neutral|cool"
    },
    "style_tags": ["luxury", "minimal", "sophisticated", ...],
    "quality_score": 0.0-1.0,
    "detected_objects": ["handbag", "jewelry", "dress", ...],
    "brand_alignment_score": 0.0-1.0
}

For brand_alignment_score, consider:
- SkyyRose brand: Luxury, sophisticated, bold, Oakland-inspired
- Colors: Rose gold (#B76E79), Black (#1A1A1A)
- Style: High-end fashion, elegant minimalism

Only return valid JSON, no markdown or explanations."""


# =============================================================================
# Service
# =============================================================================


class VisualFeatureExtractor:
    """Extracts visual features from images using Gemini vision.

    Usage:
        extractor = VisualFeatureExtractor()
        features = await extractor.extract(image_url)
    """

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize extractor.

        Args:
            api_key: Google AI API key (defaults to GOOGLE_AI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GOOGLE_AI_API_KEY", "")
        self._client: Any = None

    async def _get_client(self) -> Any:
        """Get or create Gemini client."""
        if self._client is None:
            from services.ml.gemini_client import GeminiClient, GeminiConfig

            config = GeminiConfig(api_key=self.api_key)
            self._client = GeminiClient(config)
        return self._client

    async def extract(
        self,
        image_url: str,
        *,
        correlation_id: str | None = None,
    ) -> VisualFeatures:
        """Extract visual features from image.

        Args:
            image_url: URL of image to analyze
            correlation_id: Optional correlation ID for tracing

        Returns:
            VisualFeatures with extracted data
        """
        try:
            client = await self._get_client()

            # Analyze with Gemini vision
            response = await client.analyze_image(
                image_url,
                VISUAL_FEATURES_PROMPT,
                max_tokens=2048,
                temperature=0.3,  # Lower temp for more consistent JSON
            )

            if not response.success or not response.text:
                logger.warning(
                    f"Gemini analysis failed for {image_url}",
                    extra={"correlation_id": correlation_id},
                )
                return self._fallback_features()

            # Parse JSON from response
            features = self._parse_response(response.text)

            logger.info(
                f"Extracted features from {image_url}",
                extra={
                    "correlation_id": correlation_id,
                    "quality_score": features.quality_score,
                    "style_tags": features.style_tags[:5],
                },
            )

            return features

        except Exception as e:
            logger.error(
                f"Feature extraction failed for {image_url}: {e}",
                extra={"correlation_id": correlation_id},
            )
            return self._fallback_features()

    def _parse_response(self, text: str) -> VisualFeatures:
        """Parse JSON response from Gemini.

        Args:
            text: Raw response text

        Returns:
            Parsed VisualFeatures
        """
        try:
            # Try to extract JSON from response
            json_match = re.search(r"\{[\s\S]*\}", text)
            if not json_match:
                logger.warning("No JSON found in response")
                return self._fallback_features()

            data = json.loads(json_match.group())

            # Build color palette
            color_data = data.get("color_palette", {})
            color_palette = ColorPalette(
                primary=color_data.get("primary", "#1A1A1A"),
                secondary=color_data.get("secondary", []),
                accent=color_data.get("accent"),
                all_colors=[ColorInfo(**c) for c in color_data.get("all_colors", [])],
            )

            # Build composition
            comp_data = data.get("composition", {})
            composition = CompositionAnalysis(
                type=comp_data.get("type", "centered"),
                focal_point=comp_data.get("focal_point"),
                balance=comp_data.get("balance", "balanced"),
                depth=comp_data.get("depth"),
                framing=comp_data.get("framing"),
            )

            # Build lighting
            light_data = data.get("lighting", {})
            lighting = LightingProfile(
                type=light_data.get("type", "studio"),
                direction=light_data.get("direction"),
                mood=light_data.get("mood"),
                quality=light_data.get("quality"),
                color_temperature=light_data.get("color_temperature"),
            )

            return VisualFeatures(
                color_palette=color_palette,
                composition=composition,
                lighting=lighting,
                style_tags=data.get("style_tags", []),
                quality_score=float(data.get("quality_score", 0.85)),
                detected_objects=data.get("detected_objects", []),
                brand_alignment_score=float(data.get("brand_alignment_score", 0.5)),
            )

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse features JSON: {e}")
            return self._fallback_features()

    def _fallback_features(self) -> VisualFeatures:
        """Return placeholder features when extraction fails.

        Returns:
            Default VisualFeatures with SkyyRose brand colors
        """
        return VisualFeatures(
            color_palette=ColorPalette(
                primary="#1A1A1A",
                secondary=["#B76E79", "#FFFFFF"],
                accent="#B76E79",
            ),
            composition=CompositionAnalysis(
                type="centered",
                focal_point="center",
                balance="balanced",
            ),
            lighting=LightingProfile(
                type="studio",
                direction="front",
                mood="neutral",
            ),
            style_tags=["luxury", "fashion"],
            quality_score=0.5,
            detected_objects=[],
            brand_alignment_score=0.5,
        )

    async def extract_batch(
        self,
        image_urls: list[str],
        *,
        max_concurrent: int = 5,
        correlation_id: str | None = None,
    ) -> list[VisualFeatures]:
        """Extract features from multiple images.

        Args:
            image_urls: List of image URLs
            max_concurrent: Maximum concurrent extractions
            correlation_id: Optional correlation ID

        Returns:
            List of VisualFeatures in same order as input
        """
        import asyncio

        semaphore = asyncio.Semaphore(max_concurrent)

        async def extract_with_limit(url: str) -> VisualFeatures:
            async with semaphore:
                return await self.extract(url, correlation_id=correlation_id)

        tasks = [extract_with_limit(url) for url in image_urls]
        return await asyncio.gather(*tasks)

    async def close(self) -> None:
        """Close the client."""
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def __aenter__(self) -> VisualFeatureExtractor:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()


# Singleton instance for dependency injection
_extractor: VisualFeatureExtractor | None = None


async def get_visual_feature_extractor() -> VisualFeatureExtractor:
    """Get or create singleton extractor instance."""
    global _extractor
    if _extractor is None:
        _extractor = VisualFeatureExtractor()
    return _extractor


__all__ = [
    "VisualFeatureExtractor",
    "VisualFeatures",
    "ColorPalette",
    "ColorInfo",
    "CompositionAnalysis",
    "LightingProfile",
    "get_visual_feature_extractor",
]
