# tests/services/three_d/test_gemini_provider.py
"""Tests for Gemini Image Provider (Nano Banana Pro).

Tests integration of Gemini with the 3D provider abstraction.

Author: DevSkyy Platform Team
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.ml.gemini_client import (
    AspectRatio,
    GeminiClient,
    GeminiConfig,
    GeminiError,
    GeminiModel,
    GeneratedImage,
    ImageGenerationResponse,
    ImageInput,
)
from services.three_d.gemini_provider import GeminiImageProvider
from services.three_d.provider_interface import (
    ProviderStatus,
    QualityLevel,
    ThreeDCapability,
    ThreeDGenerationError,
    ThreeDProviderError,
    ThreeDRequest,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_gemini_client() -> AsyncMock:
    """Create mock Gemini client."""
    client = AsyncMock(spec=GeminiClient)
    client.connect = AsyncMock()
    client.close = AsyncMock()
    client.health_check = AsyncMock(return_value={"status": "healthy"})
    return client


@pytest.fixture
def provider() -> GeminiImageProvider:
    """Create Gemini provider with mock config."""
    with patch.dict("os.environ", {"GOOGLE_AI_API_KEY": "test-key"}):
        return GeminiImageProvider(api_key="test-key")


# =============================================================================
# Provider Properties Tests
# =============================================================================


class TestProviderProperties:
    """Tests for provider properties."""

    def test_name(self, provider: GeminiImageProvider) -> None:
        """Test provider name."""
        assert provider.name == "gemini_nano_banana"

    def test_capabilities(self, provider: GeminiImageProvider) -> None:
        """Test provider capabilities."""
        caps = provider.capabilities
        assert ThreeDCapability.TEXT_TO_3D in caps
        assert ThreeDCapability.IMAGE_TO_3D in caps
        assert ThreeDCapability.TEXTURE_GENERATION in caps


# =============================================================================
# Generation Tests
# =============================================================================


class TestGenerateFromText:
    """Tests for text-to-image generation."""

    @pytest.mark.asyncio
    async def test_generate_success(self, provider: GeminiImageProvider) -> None:
        """Test successful text-to-image generation."""
        mock_response = ImageGenerationResponse(
            success=True,
            images=[
                GeneratedImage(
                    base64_data="dGVzdA==",
                    mime_type="image/png",
                )
            ],
            model_used="gemini-2.0-flash-exp",
            duration_ms=1000,
        )

        with patch.object(
            provider._client,
            "generate_image",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            request = ThreeDRequest(
                prompt="A luxury handbag on marble background",
                product_name="Black Rose Clutch",
                collection="Black Rose",
            )

            response = await provider.generate_from_text(request)

            assert response.success is True
            assert response.provider == "gemini_nano_banana"
            assert response.model_url is not None
            assert "data:image/png" in response.model_url

    @pytest.mark.asyncio
    async def test_generate_no_prompt(self, provider: GeminiImageProvider) -> None:
        """Test error when no prompt provided."""
        request = ThreeDRequest()  # No prompt

        with pytest.raises(ThreeDProviderError, match="Prompt is required"):
            await provider.generate_from_text(request)

    @pytest.mark.asyncio
    async def test_generate_failure(self, provider: GeminiImageProvider) -> None:
        """Test handling generation failure."""
        mock_response = ImageGenerationResponse(
            success=False,
            images=[],
            model_used="gemini-2.0-flash-exp",
            duration_ms=0,
        )

        with patch.object(
            provider._client,
            "generate_image",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            request = ThreeDRequest(prompt="test")

            with pytest.raises(ThreeDGenerationError):
                await provider.generate_from_text(request)


class TestGenerateFromImage:
    """Tests for image-to-image editing."""

    @pytest.mark.asyncio
    async def test_edit_image_success(self, provider: GeminiImageProvider) -> None:
        """Test successful image editing."""
        mock_response = ImageGenerationResponse(
            success=True,
            images=[
                GeneratedImage(
                    base64_data="ZWRpdGVk",
                    mime_type="image/png",
                )
            ],
            model_used="gemini-2.0-flash-exp",
            duration_ms=1500,
        )

        with patch.object(
            provider._client,
            "generate_image",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            with patch.object(
                ImageInput,
                "from_url",
                new_callable=AsyncMock,
                return_value=ImageInput(base64_data="dGVzdA==", mime_type="image/png"),
            ):
                request = ThreeDRequest(
                    image_url="https://example.com/product.jpg",
                    prompt="Change background to studio lighting",
                )

                response = await provider.generate_from_image(request)

                assert response.success is True
                assert response.metadata["source_image"] == "https://example.com/product.jpg"

    @pytest.mark.asyncio
    async def test_edit_image_no_source(self, provider: GeminiImageProvider) -> None:
        """Test error when no image source provided."""
        request = ThreeDRequest(prompt="edit something")  # No image

        with pytest.raises(ThreeDProviderError, match="Image URL or path required"):
            await provider.generate_from_image(request)


# =============================================================================
# Health Check Tests
# =============================================================================


class TestHealthCheck:
    """Tests for health check."""

    @pytest.mark.asyncio
    async def test_health_check_available(self, provider: GeminiImageProvider) -> None:
        """Test healthy provider."""
        with patch.object(
            provider._client,
            "health_check",
            new_callable=AsyncMock,
            return_value={"status": "healthy"},
        ):
            health = await provider.health_check()

            assert health.provider == "gemini_nano_banana"
            assert health.status == ProviderStatus.AVAILABLE
            assert len(health.capabilities) > 0

    @pytest.mark.asyncio
    async def test_health_check_unavailable(self, provider: GeminiImageProvider) -> None:
        """Test unhealthy provider."""
        with patch.object(
            provider._client,
            "health_check",
            new_callable=AsyncMock,
            return_value={"status": "unhealthy", "error": "API down"},
        ):
            health = await provider.health_check()

            assert health.status == ProviderStatus.UNAVAILABLE
            assert health.error_message == "API down"

    @pytest.mark.asyncio
    async def test_health_check_exception(self, provider: GeminiImageProvider) -> None:
        """Test health check with exception."""
        with patch.object(
            provider._client,
            "health_check",
            new_callable=AsyncMock,
            side_effect=Exception("Network error"),
        ):
            health = await provider.health_check()

            assert health.status == ProviderStatus.UNAVAILABLE
            assert "Network error" in health.error_message


# =============================================================================
# Extended Methods Tests
# =============================================================================


class TestProductImageGeneration:
    """Tests for SkyyRose-specific generation methods."""

    @pytest.mark.asyncio
    async def test_generate_product_image(self, provider: GeminiImageProvider) -> None:
        """Test product image generation with luxury styling."""
        mock_response = ImageGenerationResponse(
            success=True,
            images=[GeneratedImage(base64_data="cHJvZHVjdA==", mime_type="image/png")],
            model_used="gemini-2.0-flash-exp",
            duration_ms=2000,
        )

        with patch.object(
            provider._client,
            "generate_image",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_gen:
            result = await provider.generate_product_image(
                "A statement clutch with rose gold hardware",
                product_name="Rose Gold Clutch",
                collection="Black Rose",
                quality=QualityLevel.PRODUCTION,
            )

            assert result.success is True
            # Verify luxury prompt was constructed
            call_args = mock_gen.call_args[0][0]
            assert "luxury" in call_args.prompt.lower()
            assert "professional" in call_args.prompt.lower()

    @pytest.mark.asyncio
    async def test_edit_product_image_preserves_product(
        self, provider: GeminiImageProvider
    ) -> None:
        """Test product editing preserves brand integrity."""
        mock_response = ImageGenerationResponse(
            success=True,
            images=[GeneratedImage(base64_data="ZWRpdGVk", mime_type="image/png")],
            model_used="gemini-2.0-flash-exp",
            duration_ms=1500,
        )

        with patch.object(
            provider._client,
            "edit_image",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_edit:
            result = await provider.edit_product_image(
                "https://example.com/handbag.jpg",
                "Add soft studio lighting",
                preserve_product=True,
            )

            assert result.success is True
            # Verify preserve_original was passed
            mock_edit.assert_called_once()
            assert mock_edit.call_args.kwargs["preserve_original"] is True

    @pytest.mark.asyncio
    async def test_generate_background(self, provider: GeminiImageProvider) -> None:
        """Test background generation."""
        mock_response = ImageGenerationResponse(
            success=True,
            images=[GeneratedImage(base64_data="YmFja2dyb3VuZA==", mime_type="image/png")],
            model_used="gemini-2.0-flash-exp",
            duration_ms=1800,
        )

        with patch.object(
            provider,
            "edit_product_image",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_edit:
            result = await provider.generate_background(
                "https://example.com/product.jpg",
                "Marble surface with soft natural lighting",
            )

            assert result.success is True
            # Verify background prompt structure
            call_args = mock_edit.call_args
            assert "background" in call_args.args[1].lower()


# =============================================================================
# Quality Level Tests
# =============================================================================


class TestQualityMapping:
    """Tests for quality level to image size mapping."""

    def test_draft_quality(self, provider: GeminiImageProvider) -> None:
        """Test draft quality maps to 1K."""
        from services.ml.gemini_client import ImageSize

        size = provider._quality_to_size(QualityLevel.DRAFT)
        assert size == ImageSize.SIZE_1K

    def test_standard_quality(self, provider: GeminiImageProvider) -> None:
        """Test standard quality maps to 2K."""
        from services.ml.gemini_client import ImageSize

        size = provider._quality_to_size(QualityLevel.STANDARD)
        assert size == ImageSize.SIZE_2K

    def test_production_quality(self, provider: GeminiImageProvider) -> None:
        """Test production quality maps to 4K."""
        from services.ml.gemini_client import ImageSize

        size = provider._quality_to_size(QualityLevel.PRODUCTION)
        assert size == ImageSize.SIZE_4K


# =============================================================================
# Context Manager Tests
# =============================================================================


class TestContextManager:
    """Tests for async context manager."""

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test provider works as context manager."""
        with patch.dict("os.environ", {"GOOGLE_AI_API_KEY": "test-key"}):
            provider = GeminiImageProvider(api_key="test-key")

            with patch.object(
                provider._client, "connect", new_callable=AsyncMock
            ) as mock_connect:
                with patch.object(
                    provider._client, "close", new_callable=AsyncMock
                ) as mock_close:
                    async with provider as p:
                        assert p is provider
                        mock_connect.assert_called_once()

                    mock_close.assert_called_once()
