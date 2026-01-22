# tests/api/test_descriptions_api.py
"""Tests for descriptions API endpoints.

Implements US-029: Image-to-description pipeline.

Author: DevSkyy Platform Team
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1.descriptions import get_pipeline, get_vision_client, router
from services.ml.schemas.description import (
    DescriptionOutput,
    ExtractedFeatures,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_user() -> MagicMock:
    """Create mock authenticated user."""
    from security.jwt_oauth2_auth import TokenPayload, TokenType

    return TokenPayload(
        sub="user_123",
        jti="test_jti_123",
        type=TokenType.ACCESS,
        roles=["user"],
        exp=datetime.now(UTC),
        iat=datetime.now(UTC),
    )


@pytest.fixture
def mock_pipeline() -> MagicMock:
    """Create mock description pipeline."""
    pipeline = MagicMock()
    pipeline.generate_description = AsyncMock()
    pipeline.generate_batch = AsyncMock()
    pipeline.extract_features = AsyncMock()
    return pipeline


@pytest.fixture
def mock_vision_client() -> MagicMock:
    """Create mock vision client."""
    client = MagicMock()
    client.health_check = AsyncMock(return_value=True)
    return client


@pytest.fixture
def app(mock_user: MagicMock, mock_pipeline: MagicMock, mock_vision_client: MagicMock) -> FastAPI:
    """Create test FastAPI app."""
    from security.jwt_oauth2_auth import get_current_user

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_pipeline] = lambda: mock_pipeline
    app.dependency_overrides[get_vision_client] = lambda: mock_vision_client
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_output() -> DescriptionOutput:
    """Create sample description output."""
    return DescriptionOutput(
        image_url="https://example.com/product.jpg",
        product_name="Black Rose Midi Dress",
        description="This elegant midi dress embodies luxury and sophistication.",
        short_description="Elegant black midi dress.",
        bullet_points=[],
        suggested_tags=["black", "midi", "dress"],
        seo=None,
        features=None,
        model_used="yorickvp/llava-v1.6-34b",
        word_count=8,
        processing_time_ms=1500,
    )


# =============================================================================
# Generate Description Tests
# =============================================================================


class TestGenerateDescription:
    """Tests for generate description endpoint."""

    def test_generate_description_success(
        self,
        client: TestClient,
        mock_pipeline: MagicMock,
        sample_output: DescriptionOutput,
    ) -> None:
        """Should generate description successfully."""
        mock_pipeline.generate_description.return_value = sample_output

        response = client.post(
            "/descriptions/generate",
            json={
                "image_url": "https://example.com/product.jpg",
                "product_name": "Black Rose Midi Dress",
                "product_type": "apparel",
                "style": "luxury",
                "target_word_count": 150,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["image_url"] == "https://example.com/product.jpg"
        assert data["description"] == sample_output.description
        assert data["word_count"] == 8

    def test_generate_description_minimal_request(
        self,
        client: TestClient,
        mock_pipeline: MagicMock,
        sample_output: DescriptionOutput,
    ) -> None:
        """Should work with minimal required fields."""
        mock_pipeline.generate_description.return_value = sample_output

        response = client.post(
            "/descriptions/generate",
            json={
                "image_url": "https://example.com/product.jpg",
            },
        )

        assert response.status_code == 200

    def test_generate_description_all_options(
        self,
        client: TestClient,
        mock_pipeline: MagicMock,
        sample_output: DescriptionOutput,
    ) -> None:
        """Should accept all optional parameters."""
        mock_pipeline.generate_description.return_value = sample_output

        response = client.post(
            "/descriptions/generate",
            json={
                "image_url": "https://example.com/product.jpg",
                "product_name": "Test Product",
                "product_type": "accessories",
                "style": "storytelling",
                "brand_context": "SkyyRose Spring Collection",
                "target_word_count": 200,
                "include_seo": True,
                "include_bullets": True,
                "include_tags": True,
                "model": "yorickvp/llava-13b",
            },
        )

        assert response.status_code == 200

    def test_generate_description_invalid_url(
        self,
        client: TestClient,
    ) -> None:
        """Should reject invalid URL."""
        response = client.post(
            "/descriptions/generate",
            json={
                "image_url": "not-a-url",
            },
        )

        assert response.status_code == 422

    def test_generate_description_error_handling(
        self,
        client: TestClient,
        mock_pipeline: MagicMock,
    ) -> None:
        """Should handle errors gracefully."""
        mock_pipeline.generate_description.side_effect = Exception("Vision model error")

        response = client.post(
            "/descriptions/generate",
            json={
                "image_url": "https://example.com/product.jpg",
            },
        )

        assert response.status_code == 500
        assert "Vision model error" in response.json()["detail"]


class TestQuickDescription:
    """Tests for quick description endpoint."""

    def test_quick_description_success(
        self,
        client: TestClient,
        mock_pipeline: MagicMock,
        sample_output: DescriptionOutput,
    ) -> None:
        """Should generate quick description."""
        mock_pipeline.generate_description.return_value = sample_output

        response = client.post(
            "/descriptions/generate/quick",
            params={
                "image_url": "https://example.com/product.jpg",
            },
        )

        assert response.status_code == 200

    def test_quick_description_with_options(
        self,
        client: TestClient,
        mock_pipeline: MagicMock,
        sample_output: DescriptionOutput,
    ) -> None:
        """Should accept product type and style."""
        mock_pipeline.generate_description.return_value = sample_output

        response = client.post(
            "/descriptions/generate/quick",
            params={
                "image_url": "https://example.com/product.jpg",
                "product_type": "footwear",
                "style": "casual",
            },
        )

        assert response.status_code == 200


# =============================================================================
# Batch Description Tests
# =============================================================================


class TestBatchDescription:
    """Tests for batch description endpoint."""

    def test_batch_description_success(
        self,
        client: TestClient,
        mock_pipeline: MagicMock,
    ) -> None:
        """Should process batch successfully."""
        from services.ml.schemas.description import BatchDescriptionOutput

        mock_pipeline.generate_batch.return_value = BatchDescriptionOutput(
            total=2,
            completed=2,
            failed=0,
            results=[],
            errors=[],
        )

        response = client.post(
            "/descriptions/generate/batch",
            json={
                "requests": [
                    {"image_url": "https://example.com/img1.jpg"},
                    {"image_url": "https://example.com/img2.jpg"},
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["completed"] == 2

    def test_batch_with_callback_url(
        self,
        client: TestClient,
        mock_pipeline: MagicMock,
    ) -> None:
        """Should accept callback URL."""
        from services.ml.schemas.description import BatchDescriptionOutput

        mock_pipeline.generate_batch.return_value = BatchDescriptionOutput(
            total=1,
            completed=1,
            failed=0,
            results=[],
            errors=[],
        )

        response = client.post(
            "/descriptions/generate/batch",
            json={
                "requests": [
                    {"image_url": "https://example.com/img1.jpg"},
                ],
                "callback_url": "https://webhook.example.com/callback",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["webhook_url"] == "https://webhook.example.com/callback"
        assert data["webhook_sent"] is True

    def test_batch_max_50_images(
        self,
        client: TestClient,
    ) -> None:
        """Should reject over 50 images."""
        response = client.post(
            "/descriptions/generate/batch",
            json={
                "requests": [{"image_url": f"https://example.com/img{i}.jpg"} for i in range(51)],
            },
        )

        assert response.status_code == 422


# =============================================================================
# Feature Extraction Tests
# =============================================================================


class TestExtractFeatures:
    """Tests for feature extraction endpoint."""

    def test_extract_features_success(
        self,
        client: TestClient,
        mock_pipeline: MagicMock,
    ) -> None:
        """Should extract features successfully."""
        mock_pipeline.extract_features.return_value = ExtractedFeatures(
            colors=[],
            materials=[],
            style=None,
            detected_elements=["zipper", "button"],
            confidence_score=0.85,
        )

        response = client.post(
            "/descriptions/extract-features",
            json={
                "image_url": "https://example.com/product.jpg",
                "product_type": "apparel",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["confidence_score"] == 0.85
        assert "zipper" in data["detected_elements"]

    def test_extract_features_with_options(
        self,
        client: TestClient,
        mock_pipeline: MagicMock,
    ) -> None:
        """Should accept extraction options."""
        mock_pipeline.extract_features.return_value = ExtractedFeatures(
            colors=[],
            materials=[],
            style=None,
            detected_elements=[],
            confidence_score=0.9,
        )

        response = client.post(
            "/descriptions/extract-features",
            json={
                "image_url": "https://example.com/product.jpg",
                "product_type": "jewelry",
                "extract_colors": True,
                "extract_materials": True,
                "extract_style": False,
                "model": "yorickvp/llava-13b",
            },
        )

        assert response.status_code == 200


# =============================================================================
# Models and Styles Endpoints Tests
# =============================================================================


class TestModelsEndpoint:
    """Tests for models listing endpoint."""

    def test_list_models(self, client: TestClient) -> None:
        """Should list available models."""
        response = client.get("/descriptions/models")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5  # 2 Gemini + 3 Replicate

        # Check Gemini Pro (recommended, no rate limits)
        gemini_pro = next(
            m for m in data if "gemini" in m["id"].lower() and "pro" in m["id"].lower()
        )
        assert gemini_pro["provider"] == "google"
        assert gemini_pro["rate_limited"] is False
        assert "(RECOMMENDED)" in gemini_pro["description"]

        # Check Gemini Flash (fast, no rate limits)
        gemini_flash = next(
            m for m in data if "gemini" in m["id"].lower() and "flash" in m["id"].lower()
        )
        assert gemini_flash["provider"] == "google"
        assert gemini_flash["rate_limited"] is False

        # Check LLaVA 34B (Replicate)
        llava_34b = next(m for m in data if "34b" in m["id"].lower())
        assert llava_34b["quality"] == "highest"
        assert llava_34b["provider"] == "replicate"

        # Check BLIP-2
        blip2 = next(m for m in data if "blip" in m["id"].lower())
        assert "fallback" in blip2["recommended_for"]


class TestStylesEndpoint:
    """Tests for styles listing endpoint."""

    def test_list_styles(self, client: TestClient) -> None:
        """Should list available styles."""
        response = client.get("/descriptions/styles")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

        style_ids = [s["id"] for s in data]
        assert "luxury" in style_ids
        assert "casual" in style_ids
        assert "technical" in style_ids
        assert "minimal" in style_ids
        assert "storytelling" in style_ids

    def test_luxury_style_has_brand_voice(self, client: TestClient) -> None:
        """Should include brand voice for luxury style."""
        response = client.get("/descriptions/styles")

        data = response.json()
        luxury = next(s for s in data if s["id"] == "luxury")

        assert "SkyyRose" in luxury["brand_voice"]


# =============================================================================
# Health Check Tests
# =============================================================================


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check_healthy(
        self,
        client: TestClient,
        mock_vision_client: MagicMock,
    ) -> None:
        """Should return healthy when models available."""
        mock_vision_client.health_check.return_value = True

        response = client.get("/descriptions/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "descriptions"

    def test_health_check_degraded(
        self,
        client: TestClient,
        mock_vision_client: MagicMock,
    ) -> None:
        """Should return degraded when models unavailable."""
        mock_vision_client.health_check.return_value = False

        response = client.get("/descriptions/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"


# =============================================================================
# Product Type Tests
# =============================================================================


class TestProductTypes:
    """Tests for product type handling."""

    @pytest.mark.parametrize(
        "product_type",
        [
            "apparel",
            "footwear",
            "accessories",
            "jewelry",
            "home",
            "beauty",
            "other",
        ],
    )
    def test_all_product_types_accepted(
        self,
        client: TestClient,
        mock_pipeline: MagicMock,
        sample_output: DescriptionOutput,
        product_type: str,
    ) -> None:
        """Should accept all valid product types."""
        mock_pipeline.generate_description.return_value = sample_output

        response = client.post(
            "/descriptions/generate",
            json={
                "image_url": "https://example.com/product.jpg",
                "product_type": product_type,
            },
        )

        assert response.status_code == 200


# =============================================================================
# Description Style Tests
# =============================================================================


class TestDescriptionStyles:
    """Tests for description style handling."""

    @pytest.mark.parametrize(
        "style",
        [
            "luxury",
            "casual",
            "technical",
            "minimal",
            "storytelling",
        ],
    )
    def test_all_styles_accepted(
        self,
        client: TestClient,
        mock_pipeline: MagicMock,
        sample_output: DescriptionOutput,
        style: str,
    ) -> None:
        """Should accept all valid styles."""
        mock_pipeline.generate_description.return_value = sample_output

        response = client.post(
            "/descriptions/generate",
            json={
                "image_url": "https://example.com/product.jpg",
                "style": style,
            },
        )

        assert response.status_code == 200
