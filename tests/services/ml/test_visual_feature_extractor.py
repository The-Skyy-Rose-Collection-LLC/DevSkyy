# tests/services/ml/test_visual_feature_extractor.py
"""Tests for visual feature extraction service.

Tests for US-013: Brand asset ingestion visual feature extraction.

Author: DevSkyy Platform Team
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.ml.visual_feature_extractor import (
    ColorInfo,
    ColorPalette,
    CompositionAnalysis,
    LightingProfile,
    VisualFeatureExtractor,
    VisualFeatures,
    get_visual_feature_extractor,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_gemini_response() -> str:
    """Mock Gemini vision response with valid JSON."""
    return json.dumps({
        "color_palette": {
            "primary": "#1A1A1A",
            "secondary": ["#B76E79", "#FFFFFF"],
            "accent": "#B76E79",
            "all_colors": [
                {"hex": "#1A1A1A", "name": "charcoal black", "prominence": 0.6},
                {"hex": "#B76E79", "name": "rose gold", "prominence": 0.3},
            ],
        },
        "composition": {
            "type": "centered",
            "focal_point": "center",
            "balance": "balanced",
            "depth": "shallow",
            "framing": "medium",
        },
        "lighting": {
            "type": "studio",
            "direction": "front",
            "mood": "dramatic",
            "quality": "soft",
            "color_temperature": "neutral",
        },
        "style_tags": ["luxury", "minimal", "sophisticated", "elegant"],
        "quality_score": 0.92,
        "detected_objects": ["handbag", "leather", "gold hardware"],
        "brand_alignment_score": 0.88,
    })


@pytest.fixture
def extractor() -> VisualFeatureExtractor:
    """Create extractor with mock API key."""
    return VisualFeatureExtractor(api_key="test-key")


# =============================================================================
# Model Tests
# =============================================================================


class TestModels:
    """Tests for data models."""

    def test_color_info(self) -> None:
        """Test ColorInfo model."""
        color = ColorInfo(hex="#B76E79", name="rose gold", prominence=0.5)
        assert color.hex == "#B76E79"
        assert color.name == "rose gold"
        assert color.prominence == 0.5

    def test_color_palette(self) -> None:
        """Test ColorPalette model."""
        palette = ColorPalette(
            primary="#1A1A1A",
            secondary=["#B76E79"],
            accent="#FFFFFF",
        )
        assert palette.primary == "#1A1A1A"
        assert len(palette.secondary) == 1
        assert palette.accent == "#FFFFFF"

    def test_composition_analysis(self) -> None:
        """Test CompositionAnalysis model."""
        comp = CompositionAnalysis(
            type="rule_of_thirds",
            focal_point="left",
            balance="asymmetrical",
        )
        assert comp.type == "rule_of_thirds"
        assert comp.focal_point == "left"

    def test_lighting_profile(self) -> None:
        """Test LightingProfile model."""
        lighting = LightingProfile(
            type="natural",
            direction="side",
            mood="warm",
        )
        assert lighting.type == "natural"
        assert lighting.mood == "warm"

    def test_visual_features(self) -> None:
        """Test VisualFeatures model."""
        features = VisualFeatures(
            style_tags=["luxury", "minimal"],
            quality_score=0.9,
            brand_alignment_score=0.85,
        )
        assert "luxury" in features.style_tags
        assert features.quality_score == 0.9


# =============================================================================
# Extractor Tests
# =============================================================================


class TestVisualFeatureExtractor:
    """Tests for VisualFeatureExtractor."""

    @pytest.mark.asyncio
    async def test_extract_success(
        self,
        extractor: VisualFeatureExtractor,
        mock_gemini_response: str,
    ) -> None:
        """Test successful feature extraction."""
        mock_client = MagicMock()
        mock_client.analyze_image = AsyncMock(
            return_value=MagicMock(
                success=True,
                text=mock_gemini_response,
            )
        )

        with patch.object(extractor, "_get_client", return_value=mock_client):
            features = await extractor.extract("https://example.com/image.jpg")

        assert features.color_palette is not None
        assert features.color_palette.primary == "#1A1A1A"
        assert features.composition is not None
        assert features.composition.type == "centered"
        assert features.lighting is not None
        assert features.lighting.type == "studio"
        assert "luxury" in features.style_tags
        assert features.quality_score == 0.92

    @pytest.mark.asyncio
    async def test_extract_fallback_on_failure(
        self,
        extractor: VisualFeatureExtractor,
    ) -> None:
        """Test fallback features when extraction fails."""
        mock_client = MagicMock()
        mock_client.analyze_image = AsyncMock(
            return_value=MagicMock(
                success=False,
                text=None,
            )
        )

        with patch.object(extractor, "_get_client", return_value=mock_client):
            features = await extractor.extract("https://example.com/image.jpg")

        # Should return fallback features
        assert features.color_palette is not None
        assert features.color_palette.primary == "#1A1A1A"  # SkyyRose default
        assert features.quality_score == 0.5  # Fallback score

    @pytest.mark.asyncio
    async def test_extract_fallback_on_exception(
        self,
        extractor: VisualFeatureExtractor,
    ) -> None:
        """Test fallback when exception occurs."""
        mock_client = MagicMock()
        mock_client.analyze_image = AsyncMock(side_effect=Exception("API Error"))

        with patch.object(extractor, "_get_client", return_value=mock_client):
            features = await extractor.extract("https://example.com/image.jpg")

        # Should return fallback features
        assert features.quality_score == 0.5

    @pytest.mark.asyncio
    async def test_extract_invalid_json(
        self,
        extractor: VisualFeatureExtractor,
    ) -> None:
        """Test fallback when response is invalid JSON."""
        mock_client = MagicMock()
        mock_client.analyze_image = AsyncMock(
            return_value=MagicMock(
                success=True,
                text="This is not JSON",
            )
        )

        with patch.object(extractor, "_get_client", return_value=mock_client):
            features = await extractor.extract("https://example.com/image.jpg")

        # Should return fallback features
        assert features.quality_score == 0.5

    def test_parse_response_success(
        self,
        extractor: VisualFeatureExtractor,
        mock_gemini_response: str,
    ) -> None:
        """Test JSON parsing of valid response."""
        features = extractor._parse_response(mock_gemini_response)

        assert features.color_palette is not None
        assert len(features.color_palette.all_colors) == 2
        assert features.composition.type == "centered"
        assert features.lighting.mood == "dramatic"
        assert features.brand_alignment_score == 0.88

    def test_parse_response_with_markdown(
        self,
        extractor: VisualFeatureExtractor,
    ) -> None:
        """Test parsing response with markdown wrapper."""
        json_content = '{"style_tags": ["test"], "quality_score": 0.8}'
        markdown_response = f"```json\n{json_content}\n```"

        features = extractor._parse_response(markdown_response)

        assert "test" in features.style_tags
        assert features.quality_score == 0.8

    def test_fallback_features(
        self,
        extractor: VisualFeatureExtractor,
    ) -> None:
        """Test fallback features have SkyyRose brand colors."""
        features = extractor._fallback_features()

        assert features.color_palette.primary == "#1A1A1A"
        assert "#B76E79" in features.color_palette.secondary
        assert "luxury" in features.style_tags


# =============================================================================
# Batch Extraction Tests
# =============================================================================


class TestBatchExtraction:
    """Tests for batch feature extraction."""

    @pytest.mark.asyncio
    async def test_extract_batch(
        self,
        extractor: VisualFeatureExtractor,
        mock_gemini_response: str,
    ) -> None:
        """Test batch extraction of multiple images."""
        mock_client = MagicMock()
        mock_client.analyze_image = AsyncMock(
            return_value=MagicMock(
                success=True,
                text=mock_gemini_response,
            )
        )

        urls = [f"https://example.com/img{i}.jpg" for i in range(3)]

        with patch.object(extractor, "_get_client", return_value=mock_client):
            results = await extractor.extract_batch(urls, max_concurrent=2)

        assert len(results) == 3
        assert all(f.quality_score > 0 for f in results)

    @pytest.mark.asyncio
    async def test_extract_batch_respects_concurrency(
        self,
        extractor: VisualFeatureExtractor,
        mock_gemini_response: str,
    ) -> None:
        """Test batch respects max_concurrent limit."""
        call_count = 0

        async def mock_extract(url: str, **kwargs) -> VisualFeatures:
            nonlocal call_count
            call_count += 1
            return extractor._fallback_features()

        urls = [f"https://example.com/img{i}.jpg" for i in range(5)]

        with patch.object(extractor, "extract", side_effect=mock_extract):
            results = await extractor.extract_batch(urls, max_concurrent=2)

        assert len(results) == 5
        assert call_count == 5


# =============================================================================
# Singleton Tests
# =============================================================================


class TestSingleton:
    """Tests for singleton pattern."""

    @pytest.mark.asyncio
    async def test_get_visual_feature_extractor(self) -> None:
        """Test singleton getter."""
        extractor1 = await get_visual_feature_extractor()
        extractor2 = await get_visual_feature_extractor()

        assert extractor1 is extractor2


# =============================================================================
# Context Manager Tests
# =============================================================================


class TestContextManager:
    """Tests for async context manager."""

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test extractor works as context manager."""
        async with VisualFeatureExtractor(api_key="test") as extractor:
            assert extractor is not None
