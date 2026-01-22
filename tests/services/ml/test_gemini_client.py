# tests/services/ml/test_gemini_client.py
"""Tests for Gemini client (Nano Banana Pro).

Tests vision analysis and image generation capabilities.

Author: DevSkyy Platform Team
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.ml.gemini_client import (
    AspectRatio,
    GeminiClient,
    GeminiConfig,
    GeminiContentFilterError,
    GeminiError,
    GeminiModel,
    GeminiRateLimitError,
    GeneratedImage,
    ImageGenerationRequest,
    ImageInput,
    ImageSize,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_config() -> GeminiConfig:
    """Create mock config."""
    return GeminiConfig(api_key="test-api-key")


@pytest.fixture
def client(mock_config: GeminiConfig) -> GeminiClient:
    """Create Gemini client with mock config."""
    return GeminiClient(mock_config)


# =============================================================================
# Config Tests
# =============================================================================


class TestGeminiConfig:
    """Tests for GeminiConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = GeminiConfig(api_key="test")
        assert config.api_key == "test"
        assert config.vision_model == GeminiModel.FLASH_2_5
        assert config.image_model == GeminiModel.FLASH_IMAGE
        assert config.timeout == 120.0

    def test_validate_missing_api_key(self) -> None:
        """Test validation fails without API key."""
        config = GeminiConfig(api_key="")
        with pytest.raises(GeminiError, match="API_KEY"):
            config.validate()

    def test_validate_with_api_key(self) -> None:
        """Test validation passes with API key."""
        config = GeminiConfig(api_key="valid-key")
        config.validate()  # Should not raise


# =============================================================================
# Model Tests
# =============================================================================


class TestGeminiModel:
    """Tests for GeminiModel enum."""

    def test_vision_model(self) -> None:
        """Test for_vision returns correct model."""
        assert GeminiModel.for_vision() == GeminiModel.FLASH_2_0

    def test_image_generation_model(self) -> None:
        """Test for_image_generation returns Nano Banana Pro."""
        assert GeminiModel.for_image_generation() == GeminiModel.PRO_IMAGE

    def test_model_values(self) -> None:
        """Test model values are valid strings."""
        for model in GeminiModel:
            assert isinstance(model.value, str)
            assert len(model.value) > 0


class TestImageInput:
    """Tests for ImageInput."""

    def test_from_base64(self) -> None:
        """Test creating from base64 data."""
        data = "SGVsbG8gV29ybGQ="  # "Hello World" in base64
        image = ImageInput.from_base64(data, "image/png")

        assert image.base64_data == data
        assert image.mime_type == "image/png"
        assert image.url is None

    @pytest.mark.asyncio
    async def test_from_url(self) -> None:
        """Test creating from URL by downloading."""
        mock_response = MagicMock()
        mock_response.content = b"fake image data"
        mock_response.headers = {"content-type": "image/jpeg"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance

            image = await ImageInput.from_url("https://example.com/image.jpg")

            assert image.base64_data is not None
            assert image.mime_type == "image/jpeg"


class TestGeneratedImage:
    """Tests for GeneratedImage."""

    def test_to_data_uri(self) -> None:
        """Test data URI generation."""
        image = GeneratedImage(
            base64_data="SGVsbG8=",
            mime_type="image/png",
        )

        uri = image.to_data_uri()
        assert uri == "data:image/png;base64,SGVsbG8="


class TestImageGenerationRequest:
    """Tests for ImageGenerationRequest."""

    def test_default_values(self) -> None:
        """Test default request values."""
        request = ImageGenerationRequest(prompt="test")

        assert request.prompt == "test"
        assert request.aspect_ratio == AspectRatio.SQUARE
        assert request.image_size == ImageSize.SIZE_2K
        assert request.model == GeminiModel.FLASH_IMAGE
        assert request.number_of_images == 1
        assert request.use_thinking is False
        assert request.use_search_grounding is False

    def test_luxury_style(self) -> None:
        """Test luxury style default for SkyyRose."""
        request = ImageGenerationRequest(
            prompt="handbag",
            style="luxury",
        )
        assert request.style == "luxury"


# =============================================================================
# Client Tests
# =============================================================================


class TestGeminiClient:
    """Tests for GeminiClient."""

    @pytest.mark.asyncio
    async def test_context_manager(self, client: GeminiClient) -> None:
        """Test async context manager."""
        with patch.object(client, "connect", new_callable=AsyncMock) as mock_connect:
            with patch.object(client, "close", new_callable=AsyncMock) as mock_close:
                async with client as c:
                    assert c is client
                    mock_connect.assert_called_once()
                mock_close.assert_called_once()

    def test_build_url(self, client: GeminiClient) -> None:
        """Test URL building."""
        url = client._build_url("gemini-2.0-flash", "generateContent")

        assert "generativelanguage.googleapis.com" in url
        assert "gemini-2.0-flash" in url
        assert "generateContent" in url
        assert "key=test-api-key" in url

    @pytest.mark.asyncio
    async def test_analyze_image_success(self, client: GeminiClient) -> None:
        """Test successful image analysis."""
        mock_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "A luxury handbag"}]
                    }
                }
            ],
            "usageMetadata": {"candidatesTokenCount": 5}
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            with patch.object(ImageInput, "from_url", new_callable=AsyncMock) as mock_from_url:
                mock_from_url.return_value = ImageInput(
                    base64_data="test",
                    mime_type="image/png"
                )

                result = await client.analyze_image(
                    "https://example.com/image.jpg",
                    "Describe this product"
                )

                assert result.success is True
                assert result.text == "A luxury handbag"
                assert result.token_count == 5

    @pytest.mark.asyncio
    async def test_generate_image_success(self, client: GeminiClient) -> None:
        """Test successful image generation."""
        mock_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "inlineData": {
                                    "mimeType": "image/png",
                                    "data": "base64imagedata"
                                }
                            }
                        ]
                    },
                    "safetyRatings": []
                }
            ]
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            request = ImageGenerationRequest(
                prompt="A luxury handbag on marble",
                model=GeminiModel.PRO_IMAGE,
            )
            result = await client.generate_image(request)

            assert result.success is True
            assert len(result.images) == 1
            assert result.images[0].base64_data == "base64imagedata"

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, client: GeminiClient) -> None:
        """Test rate limit handling."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = GeminiRateLimitError(
                retry_after_seconds=60
            )

            request = ImageGenerationRequest(prompt="test")

            with pytest.raises(GeminiRateLimitError) as exc_info:
                await client.generate_image(request)

            assert exc_info.value.retry_after_seconds == 60

    @pytest.mark.asyncio
    async def test_content_filter_error(self, client: GeminiClient) -> None:
        """Test content filter handling."""
        mock_response = {
            "promptFeedback": {
                "blockReason": "SAFETY"
            }
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            request = ImageGenerationRequest(prompt="blocked content")

            with pytest.raises(GeminiContentFilterError):
                await client.generate_image(request)

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, client: GeminiClient) -> None:
        """Test healthy health check."""
        mock_response = {
            "candidates": [{"content": {"parts": [{"text": "Hi"}]}}]
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await client.health_check()

            assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, client: GeminiClient) -> None:
        """Test unhealthy health check."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = GeminiError("API error")

            result = await client.health_check()

            assert result["status"] == "unhealthy"
            assert "error" in result


# =============================================================================
# Multi-turn Tests
# =============================================================================


class TestMultiTurnConversation:
    """Tests for multi-turn image editing."""

    @pytest.mark.asyncio
    async def test_start_conversation(self, client: GeminiClient) -> None:
        """Test starting a new conversation."""
        client.start_conversation()
        assert client._conversation_history == []

    @pytest.mark.asyncio
    async def test_continue_conversation(self, client: GeminiClient) -> None:
        """Test continuing conversation."""
        mock_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "I made the changes"},
                            {
                                "inlineData": {
                                    "mimeType": "image/png",
                                    "data": "edited"
                                }
                            }
                        ]
                    }
                }
            ]
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            client.start_conversation()
            result = await client.continue_conversation("Make it darker")

            assert result.success is True
            assert result.text_response == "I made the changes"
            assert len(result.images) == 1
            # History should be updated
            assert len(client._conversation_history) == 2  # user + model


# =============================================================================
# AspectRatio and ImageSize Tests
# =============================================================================


class TestEnums:
    """Tests for enums."""

    def test_aspect_ratios(self) -> None:
        """Test all aspect ratios are valid."""
        ratios = [
            AspectRatio.SQUARE,
            AspectRatio.PORTRAIT_2_3,
            AspectRatio.PORTRAIT_3_4,
            AspectRatio.LANDSCAPE_16_9,
            AspectRatio.ULTRAWIDE,
        ]
        for ratio in ratios:
            assert ":" in ratio.value

    def test_image_sizes(self) -> None:
        """Test image size values."""
        assert ImageSize.SIZE_1K.value == "1K"
        assert ImageSize.SIZE_2K.value == "2K"
        assert ImageSize.SIZE_4K.value == "4K"
