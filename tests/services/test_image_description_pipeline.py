# tests/services/test_image_description_pipeline.py
"""Tests for image-to-description pipeline.

Implements US-029: Image-to-description pipeline.

Author: DevSkyy Platform Team
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.ml.image_description_pipeline import (
    ImageDescriptionPipeline,
    VisionModelClient,
)
from services.ml.schemas.description import (
    BatchDescriptionRequest,
    DescriptionRequest,
    DescriptionStyle,
    FeatureExtractionRequest,
    ProductType,
    VisionModel,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_vision_client() -> MagicMock:
    """Create mock vision client."""
    client = MagicMock(spec=VisionModelClient)
    client.generate = AsyncMock()
    client.health_check = AsyncMock(return_value=True)
    return client


@pytest.fixture
def pipeline(mock_vision_client: MagicMock) -> ImageDescriptionPipeline:
    """Create pipeline with mock client."""
    return ImageDescriptionPipeline(vision_client=mock_vision_client)


@pytest.fixture
def sample_request() -> DescriptionRequest:
    """Create sample description request."""
    return DescriptionRequest(
        image_url="https://example.com/product.jpg",
        product_name="Black Rose Midi Dress",
        product_type=ProductType.APPAREL,
        style=DescriptionStyle.LUXURY,
        target_word_count=150,
    )


@pytest.fixture
def mock_features_response() -> str:
    """Mock features JSON response."""
    return json.dumps({
        "colors": [
            {"name": "charcoal black", "category": "neutral", "prominence": 0.8},
            {"name": "rose gold", "category": "warm", "prominence": 0.2},
        ],
        "materials": [
            {"name": "silk", "texture": "smooth", "quality_indicator": "luxury"},
        ],
        "style": {
            "aesthetic": "minimalist",
            "mood": "sophisticated",
            "occasion": ["evening", "formal"],
            "season": ["fall", "winter"],
        },
        "detected_elements": ["zipper", "v-neck", "midi length"],
    })


@pytest.fixture
def mock_seo_response() -> str:
    """Mock SEO JSON response."""
    return json.dumps({
        "title": "Black Rose Midi Dress | SkyyRose Luxury",
        "meta_description": "Discover the Black Rose Midi Dress. Shop now at SkyyRose.",
        "focus_keyword": "black midi dress",
        "secondary_keywords": ["evening dress", "luxury fashion", "silk dress"],
    })


# =============================================================================
# VisionModelClient Tests
# =============================================================================


class TestVisionModelClient:
    """Tests for VisionModelClient."""

    @pytest.mark.asyncio
    async def test_model_endpoints_defined(self) -> None:
        """Should have all Replicate model endpoints defined."""
        client = VisionModelClient()

        # Replicate endpoints
        assert VisionModel.LLAVA_34B in client.REPLICATE_ENDPOINTS
        assert VisionModel.LLAVA_13B in client.REPLICATE_ENDPOINTS
        assert VisionModel.BLIP2 in client.REPLICATE_ENDPOINTS

    @pytest.mark.asyncio
    async def test_generate_unknown_replicate_model(self) -> None:
        """Should raise error for unknown Replicate model."""
        client = VisionModelClient()

        # Mock the _get_replicate_client method
        client._get_replicate_client = AsyncMock()

        with pytest.raises(ValueError, match="Unknown Replicate model"):
            # Create a fake Replicate model value
            fake_model = MagicMock()
            fake_model.value = "fake-replicate-model"
            fake_model.is_gemini = MagicMock(return_value=False)
            await client.generate(fake_model, "https://example.com/img.jpg", "prompt")

    def test_gemini_model_detection(self) -> None:
        """Test that Gemini models are correctly detected."""
        assert VisionModel.GEMINI_FLASH.is_gemini() is True
        assert VisionModel.GEMINI_PRO.is_gemini() is True
        assert VisionModel.LLAVA_34B.is_gemini() is False
        assert VisionModel.BLIP2.is_gemini() is False


# =============================================================================
# ImageDescriptionPipeline Tests
# =============================================================================


class TestGenerateDescription:
    """Tests for description generation."""

    @pytest.mark.asyncio
    async def test_generate_basic_description(
        self,
        pipeline: ImageDescriptionPipeline,
        mock_vision_client: MagicMock,
        sample_request: DescriptionRequest,
        mock_features_response: str,
        mock_seo_response: str,
    ) -> None:
        """Should generate complete description."""
        # Setup mock responses
        mock_vision_client.generate.side_effect = [
            mock_features_response,  # Features extraction
            "This elegant midi dress embodies luxury fashion.",  # Main description
            "Elegant black midi dress.",  # Short description
            "MATERIAL: Premium silk fabric\nFIT: Relaxed silhouette",  # Bullets
            mock_seo_response,  # SEO
            "black dress, midi, elegant, evening wear, luxury",  # Tags
        ]

        result = await pipeline.generate_description(sample_request)

        assert result.image_url == str(sample_request.image_url)
        assert result.product_name == sample_request.product_name
        assert len(result.description) > 0
        assert len(result.short_description) > 0
        assert result.model_used == sample_request.model.value

    @pytest.mark.asyncio
    async def test_generate_without_optional_fields(
        self,
        pipeline: ImageDescriptionPipeline,
        mock_vision_client: MagicMock,
    ) -> None:
        """Should generate description without optional fields."""
        request = DescriptionRequest(
            image_url="https://example.com/img.jpg",
            product_type=ProductType.APPAREL,
            include_seo=False,
            include_bullets=False,
            include_tags=False,
        )

        mock_vision_client.generate.side_effect = [
            "A beautiful garment.",  # Main description
            "Beautiful garment.",  # Short description
        ]

        result = await pipeline.generate_description(request)

        assert result.description == "A beautiful garment."
        assert result.seo is None
        assert result.bullet_points == []
        assert result.suggested_tags == []

    @pytest.mark.asyncio
    async def test_generate_with_brand_context(
        self,
        pipeline: ImageDescriptionPipeline,
        mock_vision_client: MagicMock,
        sample_request: DescriptionRequest,
        mock_features_response: str,
        mock_seo_response: str,
    ) -> None:
        """Should include brand context in prompt."""
        sample_request.brand_context = "SkyyRose Spring 2024 Collection"

        mock_vision_client.generate.side_effect = [
            mock_features_response,
            "From the Spring 2024 Collection, this piece embodies...",
            "Spring 2024 elegance.",
            "MATERIAL: Silk\nFIT: Relaxed",
            mock_seo_response,
            "spring, collection, luxury",
        ]

        result = await pipeline.generate_description(sample_request)

        assert result.description is not None
        # Verify brand context was passed to prompt (check call args)
        calls = mock_vision_client.generate.call_args_list
        assert any("Spring 2024" in str(call) for call in calls)

    @pytest.mark.asyncio
    async def test_processing_time_tracked(
        self,
        pipeline: ImageDescriptionPipeline,
        mock_vision_client: MagicMock,
        sample_request: DescriptionRequest,
        mock_features_response: str,
        mock_seo_response: str,
    ) -> None:
        """Should track processing time."""
        mock_vision_client.generate.side_effect = [
            mock_features_response,
            "Description text here.",
            "Short desc.",
            "FEATURE: bullet",
            mock_seo_response,
            "tag1, tag2",
        ]

        result = await pipeline.generate_description(sample_request)

        assert result.processing_time_ms >= 0
        assert isinstance(result.processing_time_ms, int)


class TestGenerateBatch:
    """Tests for batch description generation."""

    @pytest.mark.asyncio
    async def test_batch_single_image(
        self,
        pipeline: ImageDescriptionPipeline,
        mock_vision_client: MagicMock,
        mock_features_response: str,
        mock_seo_response: str,
    ) -> None:
        """Should process single image batch."""
        request = BatchDescriptionRequest(
            requests=[
                DescriptionRequest(
                    image_url="https://example.com/img1.jpg",
                    product_type=ProductType.APPAREL,
                    include_seo=False,
                    include_bullets=False,
                    include_tags=False,
                )
            ]
        )

        mock_vision_client.generate.side_effect = [
            "Description 1.",
            "Short 1.",
        ]

        result = await pipeline.generate_batch(request)

        assert result.total == 1
        assert result.completed == 1
        assert result.failed == 0
        assert len(result.results) == 1

    @pytest.mark.asyncio
    async def test_batch_multiple_images(
        self,
        pipeline: ImageDescriptionPipeline,
        mock_vision_client: MagicMock,
    ) -> None:
        """Should process multiple images."""
        request = BatchDescriptionRequest(
            requests=[
                DescriptionRequest(
                    image_url=f"https://example.com/img{i}.jpg",
                    product_type=ProductType.APPAREL,
                    include_seo=False,
                    include_bullets=False,
                    include_tags=False,
                )
                for i in range(3)
            ]
        )

        mock_vision_client.generate.side_effect = [
            "Desc 1.", "Short 1.",
            "Desc 2.", "Short 2.",
            "Desc 3.", "Short 3.",
        ]

        result = await pipeline.generate_batch(request)

        assert result.total == 3
        assert result.completed == 3
        assert result.failed == 0

    @pytest.mark.asyncio
    async def test_batch_handles_failures(
        self,
        pipeline: ImageDescriptionPipeline,
        mock_vision_client: MagicMock,
    ) -> None:
        """Should handle individual failures in batch."""
        request = BatchDescriptionRequest(
            requests=[
                DescriptionRequest(
                    image_url=f"https://example.com/img{i}.jpg",
                    product_type=ProductType.APPAREL,
                    include_seo=False,
                    include_bullets=False,
                    include_tags=False,
                )
                for i in range(2)
            ]
        )

        # First succeeds, second fails
        mock_vision_client.generate.side_effect = [
            "Desc 1.", "Short 1.",
            Exception("Network error"),
        ]

        result = await pipeline.generate_batch(request)

        assert result.total == 2
        assert result.completed == 1
        assert result.failed == 1
        assert len(result.errors) == 1


class TestExtractFeatures:
    """Tests for feature extraction."""

    @pytest.mark.asyncio
    async def test_extract_features_success(
        self,
        pipeline: ImageDescriptionPipeline,
        mock_vision_client: MagicMock,
        mock_features_response: str,
    ) -> None:
        """Should extract features from image."""
        mock_vision_client.generate.return_value = mock_features_response

        request = FeatureExtractionRequest(
            image_url="https://example.com/product.jpg",
            product_type=ProductType.APPAREL,
        )

        result = await pipeline.extract_features(request)

        assert len(result.colors) == 2
        assert result.colors[0].name == "charcoal black"
        assert len(result.materials) == 1
        assert result.materials[0].name == "silk"
        assert result.style is not None
        assert result.style.aesthetic == "minimalist"
        assert "zipper" in result.detected_elements

    @pytest.mark.asyncio
    async def test_extract_features_invalid_json(
        self,
        pipeline: ImageDescriptionPipeline,
        mock_vision_client: MagicMock,
    ) -> None:
        """Should handle invalid JSON response."""
        mock_vision_client.generate.return_value = "This is not JSON"

        request = FeatureExtractionRequest(
            image_url="https://example.com/product.jpg",
            product_type=ProductType.APPAREL,
        )

        result = await pipeline.extract_features(request)

        # Should return empty features with 0 confidence
        assert result.colors == []
        assert result.materials == []
        assert result.style is None
        assert result.confidence_score == 0.0


class TestBulletPoints:
    """Tests for bullet point generation."""

    @pytest.mark.asyncio
    async def test_parse_bullet_points(
        self,
        pipeline: ImageDescriptionPipeline,
        mock_vision_client: MagicMock,
    ) -> None:
        """Should parse bullet points from response."""
        bullets_response = """MATERIAL: Premium silk fabric with soft drape
FIT: Relaxed silhouette with adjustable waist
FEATURE: Hidden side zip closure
CARE: Dry clean only
STYLE: Perfect for evening events"""

        mock_vision_client.generate.return_value = bullets_response

        result = await pipeline._generate_bullet_points(
            "https://example.com/img.jpg",
            VisionModel.LLAVA_34B,
        )

        assert len(result) == 5
        assert result[0].category == "material"
        assert "silk" in result[0].text.lower()
        assert result[1].category == "fit"
        assert result[3].category == "care"

    @pytest.mark.asyncio
    async def test_bullet_points_max_seven(
        self,
        pipeline: ImageDescriptionPipeline,
        mock_vision_client: MagicMock,
    ) -> None:
        """Should limit to 7 bullet points."""
        bullets_response = "\n".join([
            f"FEATURE: Point {i}" for i in range(10)
        ])

        mock_vision_client.generate.return_value = bullets_response

        result = await pipeline._generate_bullet_points(
            "https://example.com/img.jpg",
            VisionModel.LLAVA_34B,
        )

        assert len(result) <= 7


class TestSEOGeneration:
    """Tests for SEO content generation."""

    @pytest.mark.asyncio
    async def test_generate_seo_content(
        self,
        pipeline: ImageDescriptionPipeline,
        mock_vision_client: MagicMock,
        mock_seo_response: str,
    ) -> None:
        """Should generate SEO content."""
        mock_vision_client.generate.return_value = mock_seo_response

        result = await pipeline._generate_seo_content(
            "https://example.com/img.jpg",
            ProductType.APPAREL,
            "SkyyRose",
            VisionModel.LLAVA_34B,
        )

        assert len(result.title) <= 60
        assert len(result.meta_description) <= 160
        assert result.focus_keyword == "black midi dress"
        assert len(result.secondary_keywords) > 0

    @pytest.mark.asyncio
    async def test_seo_truncates_long_fields(
        self,
        pipeline: ImageDescriptionPipeline,
        mock_vision_client: MagicMock,
    ) -> None:
        """Should truncate overly long SEO fields."""
        long_response = json.dumps({
            "title": "A" * 100,  # Too long
            "meta_description": "B" * 200,  # Too long
            "focus_keyword": "test",
            "secondary_keywords": [],
        })

        mock_vision_client.generate.return_value = long_response

        result = await pipeline._generate_seo_content(
            "https://example.com/img.jpg",
            ProductType.APPAREL,
            None,
            VisionModel.LLAVA_34B,
        )

        assert len(result.title) <= 60
        assert len(result.meta_description) <= 160


class TestTagGeneration:
    """Tests for tag generation."""

    @pytest.mark.asyncio
    async def test_generate_tags(
        self,
        pipeline: ImageDescriptionPipeline,
        mock_vision_client: MagicMock,
    ) -> None:
        """Should generate tags from image."""
        mock_vision_client.generate.return_value = (
            "black dress, midi length, evening wear, formal, elegant, silk, minimalist"
        )

        result = await pipeline._generate_tags(
            "https://example.com/img.jpg",
            VisionModel.LLAVA_34B,
        )

        assert "black dress" in result
        assert "midi length" in result
        assert all(tag == tag.lower() for tag in result)

    @pytest.mark.asyncio
    async def test_tags_max_fifteen(
        self,
        pipeline: ImageDescriptionPipeline,
        mock_vision_client: MagicMock,
    ) -> None:
        """Should limit to 15 tags."""
        mock_vision_client.generate.return_value = ", ".join([
            f"tag{i}" for i in range(20)
        ])

        result = await pipeline._generate_tags(
            "https://example.com/img.jpg",
            VisionModel.LLAVA_34B,
        )

        assert len(result) <= 15


class TestFallback:
    """Tests for model fallback behavior."""

    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(
        self,
        pipeline: ImageDescriptionPipeline,
        mock_vision_client: MagicMock,
    ) -> None:
        """Should use fallback model when primary fails."""
        # Primary fails, fallback succeeds
        mock_vision_client.generate.side_effect = [
            Exception("Primary model error"),
            "Fallback response",
        ]

        result = await pipeline._generate_with_fallback(
            "https://example.com/img.jpg",
            "Test prompt",
            VisionModel.LLAVA_34B,
        )

        assert result == "Fallback response"
        assert mock_vision_client.generate.call_count == 2
