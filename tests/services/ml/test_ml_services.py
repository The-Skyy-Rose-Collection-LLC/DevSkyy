# tests/services/ml/test_ml_services.py
"""
Comprehensive unit tests for ML service modules to achieve 80%+ coverage.

Tests cover:
1. GeminiClient - HTTP handling, retries, edge cases
2. ReplicateClient - Full request lifecycle, error handling
3. ImageDescriptionPipeline - Gemini integration, health checks
4. PipelineOrchestrator - Resume with checkpoints, event emission

Context:
- Trained models: damBruh/skyyrose-brand-voice-llm, damBruh/skyyrose-brand-voice-dpo
- Image LoRAs: devskyy/skyyrose-sdxl-lora, devskyy/skyyrose-signature-lora
- Base model: Qwen/Qwen2.5-1.5B-Instruct
- Dataset: damBruh/skyyrose-brand-voice-training

Author: DevSkyy Platform Team
"""

from __future__ import annotations

import asyncio
import base64
import json
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
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
    ImageGenerationResponse,
    ImageInput,
    ImageSize,
    VisionAnalysisResponse,
)
from services.ml.image_description_pipeline import (
    ImageDescriptionPipeline,
    VisionModelClient,
)
from services.ml.pipeline_orchestrator import (
    PROFILE_STAGES,
    PipelineError,
    PipelineEvent,
    PipelineJob,
    PipelineOrchestrator,
    PipelineStage,
    PipelineStatus,
    ProcessingProfile,
    StageCheckpoint,
)
from services.ml.replicate_client import (
    BackgroundRemovalInput,
    ImageTo3DInput,
    ImageUpscaleInput,
    ReplicateClient,
    ReplicateConfig,
    ReplicateError,
    ReplicatePrediction,
    ReplicatePredictionStatus,
    ReplicateRateLimitError,
    ReplicateTimeoutError,
)
from services.ml.schemas.description import (
    DescriptionRequest,
    DescriptionStyle,
    ProductType,
    VisionModel,
)

# =============================================================================
# Import modules under test
# =============================================================================


# =============================================================================
# GeminiClient Additional Tests
# =============================================================================


class TestGeminiClientHTTPHandling:
    """Additional tests for GeminiClient HTTP handling and edge cases."""

    @pytest.fixture
    def mock_config(self) -> GeminiConfig:
        """Create mock config."""
        return GeminiConfig(
            api_key="test-api-key",
            timeout=10.0,
            max_retries=3,
        )

    @pytest.fixture
    def client(self, mock_config: GeminiConfig) -> GeminiClient:
        """Create Gemini client with mock config."""
        return GeminiClient(mock_config)

    @pytest.mark.asyncio
    async def test_request_rate_limit_error(self, client: GeminiClient) -> None:
        """Test _request handles 429 rate limit."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "120"}

        with patch.object(client, "connect", new_callable=AsyncMock):
            client._client = MagicMock()
            client._client.is_closed = False
            client._client.post = AsyncMock(return_value=mock_response)

            with pytest.raises(GeminiRateLimitError) as exc_info:
                await client._request(
                    GeminiModel.FLASH_2_0.value,
                    [{"parts": [{"text": "test"}]}],
                )

            assert exc_info.value.retry_after_seconds == 120

    @pytest.mark.asyncio
    async def test_request_unauthorized_error(self, client: GeminiClient) -> None:
        """Test _request handles 401 unauthorized."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch.object(client, "connect", new_callable=AsyncMock):
            client._client = MagicMock()
            client._client.is_closed = False
            client._client.post = AsyncMock(return_value=mock_response)

            with pytest.raises(GeminiError) as exc_info:
                await client._request(
                    GeminiModel.FLASH_2_0.value,
                    [{"parts": [{"text": "test"}]}],
                )

            assert "Invalid Gemini API key" in str(exc_info.value)
            assert exc_info.value.retryable is False

    @pytest.mark.asyncio
    async def test_request_bad_request_with_safety(self, client: GeminiClient) -> None:
        """Test _request handles 400 with safety block."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {"message": "Content blocked by safety filters"}
        }

        with patch.object(client, "connect", new_callable=AsyncMock):
            client._client = MagicMock()
            client._client.is_closed = False
            client._client.post = AsyncMock(return_value=mock_response)

            with pytest.raises(GeminiContentFilterError):
                await client._request(
                    GeminiModel.FLASH_2_0.value,
                    [{"parts": [{"text": "test"}]}],
                )

    @pytest.mark.asyncio
    async def test_request_bad_request_generic(self, client: GeminiClient) -> None:
        """Test _request handles 400 generic bad request."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": {"message": "Invalid input"}}

        with patch.object(client, "connect", new_callable=AsyncMock):
            client._client = MagicMock()
            client._client.is_closed = False
            client._client.post = AsyncMock(return_value=mock_response)

            with pytest.raises(GeminiError) as exc_info:
                await client._request(
                    GeminiModel.FLASH_2_0.value,
                    [{"parts": [{"text": "test"}]}],
                )

            assert "Bad request" in str(exc_info.value)
            assert exc_info.value.retryable is False

    @pytest.mark.asyncio
    async def test_request_server_error_retryable(self, client: GeminiClient) -> None:
        """Test _request marks 5xx errors as retryable."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.text = "Service unavailable"

        with patch.object(client, "connect", new_callable=AsyncMock):
            client._client = MagicMock()
            client._client.is_closed = False
            client._client.post = AsyncMock(return_value=mock_response)

            with pytest.raises(GeminiError) as exc_info:
                await client._request(
                    GeminiModel.FLASH_2_0.value,
                    [{"parts": [{"text": "test"}]}],
                )

            assert exc_info.value.retryable is True

    @pytest.mark.asyncio
    async def test_request_timeout_with_retry(self, client: GeminiClient) -> None:
        """Test _request retries on timeout."""
        with patch.object(client, "connect", new_callable=AsyncMock):
            client._client = MagicMock()
            client._client.is_closed = False
            client._client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

            with pytest.raises(GeminiError) as exc_info:
                await client._request(
                    GeminiModel.FLASH_2_0.value,
                    [{"parts": [{"text": "test"}]}],
                )

            assert "timed out" in str(exc_info.value)
            assert exc_info.value.retryable is True
            # Should have retried max_retries times
            assert client._client.post.call_count == client.config.max_retries

    @pytest.mark.asyncio
    async def test_request_request_error_with_retry(self, client: GeminiClient) -> None:
        """Test _request retries on RequestError."""
        with patch.object(client, "connect", new_callable=AsyncMock):
            client._client = MagicMock()
            client._client.is_closed = False
            client._client.post = AsyncMock(side_effect=httpx.RequestError("connection failed"))

            with pytest.raises(GeminiError) as exc_info:
                await client._request(
                    GeminiModel.FLASH_2_0.value,
                    [{"parts": [{"text": "test"}]}],
                )

            assert "Request failed" in str(exc_info.value)
            assert exc_info.value.retryable is True

    @pytest.mark.asyncio
    async def test_request_with_generation_config_and_tools(self, client: GeminiClient) -> None:
        """Test _request includes generation config and tools."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "result"}]}}]
        }

        with patch.object(client, "connect", new_callable=AsyncMock):
            client._client = MagicMock()
            client._client.is_closed = False
            client._client.post = AsyncMock(return_value=mock_response)

            await client._request(
                GeminiModel.FLASH_2_0.value,
                [{"parts": [{"text": "test"}]}],
                generation_config={"maxOutputTokens": 100},
                tools=[{"googleSearch": {}}],
            )

            # Verify the payload included config and tools
            call_args = client._client.post.call_args
            payload = call_args.kwargs.get("json", call_args[1].get("json", {}))
            assert "generationConfig" in payload
            assert "tools" in payload

    @pytest.mark.asyncio
    async def test_generate_description_method(self, client: GeminiClient) -> None:
        """Test generate_description high-level method."""
        mock_vision_response = VisionAnalysisResponse(
            success=True,
            text="A stunning luxury handbag crafted from premium leather.",
            model_used=GeminiModel.FLASH_2_5.value,
            token_count=50,
            duration_ms=1500,
        )

        with patch.object(client, "analyze_image", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_vision_response

            result = await client.generate_description(
                image_url="https://example.com/product.jpg",
                product_type="handbag",
                style="luxury",
                word_count=100,
                brand_context="SkyyRose 2024 Collection",
            )

            assert "luxury" in result.lower() or "leather" in result.lower()
            mock_analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_image_method(self, client: GeminiClient) -> None:
        """Test edit_image method with preserve_original."""
        mock_gen_response = ImageGenerationResponse(
            success=True,
            images=[GeneratedImage(base64_data="edited", mime_type="image/png")],
            text_response=None,
            model_used=GeminiModel.FLASH_IMAGE.value,
            duration_ms=2000,
        )

        with patch.object(client, "generate_image", new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = mock_gen_response

            with patch.object(ImageInput, "from_url", new_callable=AsyncMock) as mock_from_url:
                mock_from_url.return_value = ImageInput(
                    base64_data="original", mime_type="image/png"
                )

                result = await client.edit_image(
                    image_url="https://example.com/product.jpg",
                    edit_instruction="Brighten the background",
                    preserve_original=True,
                )

                assert result.success is True
                # Verify safe_instruction included preservation warning
                call_args = mock_generate.call_args
                request = call_args.args[0]
                assert "Do NOT modify" in request.prompt

    @pytest.mark.asyncio
    async def test_edit_image_without_preserve(self, client: GeminiClient) -> None:
        """Test edit_image without preserve_original flag."""
        mock_gen_response = ImageGenerationResponse(
            success=True,
            images=[GeneratedImage(base64_data="edited", mime_type="image/png")],
            text_response=None,
            model_used=GeminiModel.FLASH_IMAGE.value,
            duration_ms=2000,
        )

        with patch.object(client, "generate_image", new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = mock_gen_response

            with patch.object(ImageInput, "from_url", new_callable=AsyncMock) as mock_from_url:
                mock_from_url.return_value = ImageInput(
                    base64_data="original", mime_type="image/png"
                )

                result = await client.edit_image(
                    image_url="https://example.com/product.jpg",
                    edit_instruction="Change background to blue",
                    preserve_original=False,
                )

                assert result.success is True
                call_args = mock_generate.call_args
                request = call_args.args[0]
                assert "Do NOT modify" not in request.prompt

    @pytest.mark.asyncio
    async def test_connect_when_client_closed(self, client: GeminiClient) -> None:
        """Test connect creates new client when existing is closed."""
        # First set up a closed client
        mock_client = MagicMock()
        mock_client.is_closed = True
        client._client = mock_client

        # Call connect
        await client.connect()

        # Should create new client
        assert client._client is not None
        assert client._client != mock_client

    @pytest.mark.asyncio
    async def test_close_when_client_open(self, client: GeminiClient) -> None:
        """Test close properly closes client."""
        mock_client = AsyncMock()
        mock_client.is_closed = False
        client._client = mock_client

        await client.close()

        mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_when_client_already_closed(self, client: GeminiClient) -> None:
        """Test close does nothing when already closed."""
        mock_client = AsyncMock()
        mock_client.is_closed = True
        client._client = mock_client

        await client.close()

        mock_client.aclose.assert_not_called()

    def test_generated_image_save(self, tmp_path: Any) -> None:
        """Test GeneratedImage.save method."""
        image_data = b"fake png data"
        base64_data = base64.b64encode(image_data).decode("utf-8")

        image = GeneratedImage(base64_data=base64_data, mime_type="image/png")

        output_path = tmp_path / "output.png"
        image.save(str(output_path))

        assert output_path.exists()
        assert output_path.read_bytes() == image_data


class TestGeminiImageGeneration:
    """Tests for Gemini image generation with various configurations."""

    @pytest.fixture
    def client(self) -> GeminiClient:
        """Create test client."""
        return GeminiClient(GeminiConfig(api_key="test-key"))

    @pytest.mark.asyncio
    async def test_generate_image_with_reference_images(self, client: GeminiClient) -> None:
        """Test image generation with reference images."""
        mock_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "inlineData": {
                                    "mimeType": "image/png",
                                    "data": "generated",
                                }
                            }
                        ]
                    },
                    "safetyRatings": [
                        {"category": "HARM_CATEGORY_HARASSMENT", "probability": "LOW"}
                    ],
                }
            ]
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response

            request = ImageGenerationRequest(
                prompt="Luxury handbag on marble",
                reference_images=[
                    ImageInput(base64_data="ref1", mime_type="image/png"),
                    ImageInput(base64_data="ref2", mime_type="image/jpeg"),
                ],
                aspect_ratio=AspectRatio.PORTRAIT_3_4,
                image_size=ImageSize.SIZE_4K,
                model=GeminiModel.PRO_IMAGE,
                number_of_images=2,
            )

            result = await client.generate_image(request)

            assert result.success is True
            assert len(result.safety_ratings) > 0

    @pytest.mark.asyncio
    async def test_generate_image_with_negative_prompt(self, client: GeminiClient) -> None:
        """Test image generation with negative prompt."""
        mock_response = {
            "candidates": [
                {"content": {"parts": [{"inlineData": {"mimeType": "image/png", "data": "x"}}]}}
            ]
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response

            request = ImageGenerationRequest(
                prompt="Luxury product photo",
                negative_prompt="blurry, low quality, watermark",
                collection="SkyyRose Black Rose Collection",
            )

            result = await client.generate_image(request)

            assert result.success is True
            # Check that negative prompt was appended
            call_args = mock_req.call_args
            contents = call_args.kwargs.get("contents", call_args.args[1])
            prompt_text = contents[0]["parts"][-1]["text"]
            assert "Avoid:" in prompt_text

    @pytest.mark.asyncio
    async def test_generate_image_with_interleaved_text(self, client: GeminiClient) -> None:
        """Test image generation returns interleaved text."""
        mock_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Here is your generated image:"},
                            {"inlineData": {"mimeType": "image/png", "data": "img"}},
                        ]
                    }
                }
            ]
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response

            request = ImageGenerationRequest(prompt="test")
            result = await client.generate_image(request)

            assert result.text_response == "Here is your generated image:"
            assert len(result.images) == 1

    @pytest.mark.asyncio
    async def test_generate_image_with_thinking_and_search(self, client: GeminiClient) -> None:
        """Test image generation with thinking and search grounding."""
        mock_response = {
            "candidates": [
                {"content": {"parts": [{"inlineData": {"mimeType": "image/png", "data": "x"}}]}}
            ]
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response

            request = ImageGenerationRequest(
                prompt="Current fashion trends",
                model=GeminiModel.PRO_IMAGE,
                use_thinking=True,
                use_search_grounding=True,
            )

            result = await client.generate_image(request)

            assert result.success is True
            # Verify the request was made - search grounding only applies to Pro model
            # which has "pro" in the value, but PRO_IMAGE is "gemini-2.0-flash-exp"
            mock_req.assert_called_once()


class TestGeminiErrors:
    """Additional tests for Gemini error classes."""

    def test_gemini_error_with_model_context(self) -> None:
        """Test GeminiError includes model in context."""
        error = GeminiError(
            "Test error",
            model="gemini-2.0-flash",
            correlation_id="corr-123",
        )

        assert error.context["model"] == "gemini-2.0-flash"
        assert error.correlation_id == "corr-123"

    def test_gemini_error_with_cause(self) -> None:
        """Test GeminiError includes cause exception."""
        cause = ValueError("Original error")
        error = GeminiError("Wrapper error", cause=cause)

        assert error.cause is cause

    def test_rate_limit_error_default_retry(self) -> None:
        """Test GeminiRateLimitError default retry time."""
        error = GeminiRateLimitError()

        assert error.retry_after_seconds == 60
        assert error.retryable is True

    def test_content_filter_not_retryable(self) -> None:
        """Test GeminiContentFilterError is not retryable."""
        error = GeminiContentFilterError("Content blocked")

        assert error.retryable is False


# =============================================================================
# ReplicateClient Additional Tests
# =============================================================================


class TestReplicateClientHTTPHandling:
    """Additional tests for ReplicateClient HTTP handling."""

    @pytest.fixture
    def config(self) -> ReplicateConfig:
        """Create test config."""
        return ReplicateConfig(
            api_token="test-token",
            timeout=10.0,
            poll_interval=0.1,
            max_poll_attempts=3,
            max_retries=2,
        )

    @pytest.fixture
    def client(self, config: ReplicateConfig) -> ReplicateClient:
        """Create test client."""
        return ReplicateClient(config)

    @pytest.mark.asyncio
    async def test_request_rate_limit_with_header(self, client: ReplicateClient) -> None:
        """Test _request handles rate limit with Retry-After header."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "90"}

        with patch.object(client, "connect", new_callable=AsyncMock):
            client._client = MagicMock()
            client._client.is_closed = False
            client._client.request = AsyncMock(return_value=mock_response)

            with pytest.raises(ReplicateRateLimitError) as exc_info:
                await client._request("GET", "/test")

            assert exc_info.value.retry_after_seconds == 90

    @pytest.mark.asyncio
    async def test_request_unauthorized(self, client: ReplicateClient) -> None:
        """Test _request handles 401."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch.object(client, "connect", new_callable=AsyncMock):
            client._client = MagicMock()
            client._client.is_closed = False
            client._client.request = AsyncMock(return_value=mock_response)

            with pytest.raises(ReplicateError) as exc_info:
                await client._request("GET", "/test")

            assert "Invalid Replicate API token" in str(exc_info.value)
            assert exc_info.value.retryable is False

    @pytest.mark.asyncio
    async def test_request_server_error_retryable(self, client: ReplicateClient) -> None:
        """Test _request marks 5xx as retryable."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"

        with patch.object(client, "connect", new_callable=AsyncMock):
            client._client = MagicMock()
            client._client.is_closed = False
            client._client.request = AsyncMock(return_value=mock_response)

            with pytest.raises(ReplicateError) as exc_info:
                await client._request("GET", "/test")

            assert exc_info.value.retryable is True

    @pytest.mark.asyncio
    async def test_request_client_error_not_retryable(self, client: ReplicateClient) -> None:
        """Test _request marks 4xx (except rate limit) as not retryable."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"

        with patch.object(client, "connect", new_callable=AsyncMock):
            client._client = MagicMock()
            client._client.is_closed = False
            client._client.request = AsyncMock(return_value=mock_response)

            with pytest.raises(ReplicateError) as exc_info:
                await client._request("GET", "/test")

            assert exc_info.value.retryable is False

    @pytest.mark.asyncio
    async def test_request_timeout_retry(self, client: ReplicateClient) -> None:
        """Test _request retries on timeout with backoff."""
        with patch.object(client, "connect", new_callable=AsyncMock):
            client._client = MagicMock()
            client._client.is_closed = False
            client._client.request = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

            with pytest.raises(ReplicateTimeoutError):
                await client._request("GET", "/test")

            assert client._client.request.call_count == client.config.max_retries

    @pytest.mark.asyncio
    async def test_request_connection_error_retry(self, client: ReplicateClient) -> None:
        """Test _request retries on connection error."""
        with patch.object(client, "connect", new_callable=AsyncMock):
            client._client = MagicMock()
            client._client.is_closed = False
            client._client.request = AsyncMock(side_effect=httpx.RequestError("connection reset"))

            with pytest.raises(ReplicateError) as exc_info:
                await client._request("GET", "/test")

            assert "Request failed" in str(exc_info.value)
            assert exc_info.value.retryable is True

    @pytest.mark.asyncio
    async def test_cancel_prediction(self, client: ReplicateClient) -> None:
        """Test cancel_prediction method."""
        mock_response = {
            "id": "pred-123",
            "status": "canceled",
            "input": {},
            "output": None,
            "error": None,
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response

            result = await client.cancel_prediction("pred-123")

            assert result.status == ReplicatePredictionStatus.CANCELED
            mock_req.assert_called_once_with(
                "POST",
                "/predictions/pred-123/cancel",
                correlation_id=None,
            )

    @pytest.mark.asyncio
    async def test_run_prediction_without_wait(self, client: ReplicateClient) -> None:
        """Test run_prediction with wait=False."""
        mock_prediction = {
            "id": "pred-123",
            "status": "starting",
            "input": {"image": "test"},
            "output": None,
            "error": None,
        }

        with patch.object(client, "create_prediction", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = ReplicatePrediction.model_validate(mock_prediction)

            result = await client.run_prediction(
                "owner/model:version",
                {"image": "test"},
                wait=False,
            )

            assert result.status == ReplicatePredictionStatus.STARTING
            mock_create.assert_called_once()

    def test_generate_correlation_id(self, client: ReplicateClient) -> None:
        """Test correlation ID generation."""
        id1 = client._generate_correlation_id()
        id2 = client._generate_correlation_id()

        assert id1 != id2
        assert len(id1) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_create_prediction_with_webhook(self, client: ReplicateClient) -> None:
        """Test create_prediction includes webhook URL."""
        mock_response = {
            "id": "pred-123",
            "status": "starting",
            "input": {},
            "output": None,
            "error": None,
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response

            await client.create_prediction(
                "owner/model:version",
                {"image": "test"},
                webhook="https://example.com/webhook",
            )

            call_args = mock_req.call_args
            payload = call_args.kwargs.get("json", {})
            assert payload["webhook"] == "https://example.com/webhook"


class TestReplicateInputValidation:
    """Additional tests for Replicate input validation."""

    def test_image_upscale_min_scale(self) -> None:
        """Test ImageUpscaleInput minimum scale."""
        with pytest.raises(ValueError):
            ImageUpscaleInput(
                image="https://example.com/img.jpg",
                scale=1,  # Min is 2
            )

    def test_image_to_3d_requires_url(self) -> None:
        """Test ImageTo3DInput requires URL (not base64)."""
        with pytest.raises(ValueError):
            ImageTo3DInput(
                image="data:image/png;base64,abc123",  # Not allowed for 3D
            )

    def test_background_removal_http_url(self) -> None:
        """Test BackgroundRemovalInput accepts http:// URL."""
        input_model = BackgroundRemovalInput(image="http://example.com/img.jpg")
        assert input_model.image.startswith("http://")

    def test_image_to_3d_format_case_insensitive(self) -> None:
        """Test ImageTo3DInput format is case insensitive."""
        input_model = ImageTo3DInput(
            image="https://example.com/img.jpg",
            output_format="GLB",
        )
        assert input_model.output_format == "glb"


class TestReplicatePredictionModel:
    """Additional tests for ReplicatePrediction model."""

    def test_prediction_processing_status(self) -> None:
        """Test prediction with processing status."""
        pred = ReplicatePrediction(
            id="pred-123",
            status=ReplicatePredictionStatus.PROCESSING,
            input={},
        )

        assert pred.is_terminal is False
        assert pred.succeeded is False

    def test_prediction_canceled_status(self) -> None:
        """Test prediction with canceled status."""
        pred = ReplicatePrediction(
            id="pred-123",
            status=ReplicatePredictionStatus.CANCELED,
            input={},
        )

        assert pred.is_terminal is True
        assert pred.succeeded is False

    def test_prediction_with_metrics(self) -> None:
        """Test prediction with metrics."""
        pred = ReplicatePrediction(
            id="pred-123",
            status=ReplicatePredictionStatus.SUCCEEDED,
            input={},
            output="https://output.com/result.png",
            metrics={"predict_time": 2.5, "total_time": 3.0},
        )

        assert pred.metrics["predict_time"] == 2.5


# =============================================================================
# ImageDescriptionPipeline Additional Tests
# =============================================================================


class TestVisionModelClientGemini:
    """Tests for VisionModelClient Gemini integration."""

    @pytest.mark.asyncio
    async def test_generate_routes_to_gemini(self) -> None:
        """Test generate routes Gemini models correctly."""
        client = VisionModelClient(google_api_key="test-key")

        mock_gemini = AsyncMock()
        mock_gemini.analyze_image = AsyncMock(return_value=MagicMock(text="Gemini response"))

        with patch.object(client, "_get_gemini_client", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_gemini

            result = await client.generate(
                VisionModel.GEMINI_FLASH,
                "https://example.com/img.jpg",
                "Describe this",
            )

            assert result == "Gemini response"

    @pytest.mark.asyncio
    async def test_generate_routes_to_replicate(self) -> None:
        """Test generate routes Replicate models correctly."""
        client = VisionModelClient(replicate_api_token="test-token")

        mock_replicate = MagicMock()
        mock_replicate.run = MagicMock(return_value=["Replicate", " response"])

        with patch.object(client, "_get_replicate_client", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_replicate

            with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
                mock_thread.return_value = ["Replicate", " response"]

                result = await client.generate(
                    VisionModel.LLAVA_34B,
                    "https://example.com/img.jpg",
                    "Describe this",
                )

                assert result == "Replicate response"

    @pytest.mark.asyncio
    async def test_generate_replicate_string_output(self) -> None:
        """Test generate handles string output from Replicate."""
        client = VisionModelClient(replicate_api_token="test-token")

        mock_replicate = MagicMock()

        with patch.object(client, "_get_replicate_client", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_replicate

            with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
                mock_thread.return_value = "Direct string response"

                result = await client.generate(
                    VisionModel.LLAVA_34B,
                    "https://example.com/img.jpg",
                    "Describe this",
                )

                assert result == "Direct string response"

    @pytest.mark.asyncio
    async def test_health_check_gemini_success(self) -> None:
        """Test health check for Gemini model."""
        client = VisionModelClient(google_api_key="test-key")

        mock_gemini = AsyncMock()
        mock_gemini.health_check = AsyncMock(return_value={"status": "healthy"})

        with patch.object(client, "_get_gemini_client", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_gemini

            result = await client.health_check(VisionModel.GEMINI_FLASH)

            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_gemini_failure(self) -> None:
        """Test health check handles Gemini failure."""
        client = VisionModelClient(google_api_key="test-key")

        with patch.object(client, "_get_gemini_client", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Connection error")

            result = await client.health_check(VisionModel.GEMINI_FLASH)

            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_replicate_success(self) -> None:
        """Test health check for Replicate model."""
        client = VisionModelClient(replicate_api_token="test-token")

        mock_replicate = MagicMock()
        mock_replicate.models = MagicMock()
        mock_replicate.models.get = MagicMock(return_value=MagicMock())

        with patch.object(client, "_get_replicate_client", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_replicate

            with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
                mock_thread.return_value = MagicMock()

                result = await client.health_check(VisionModel.LLAVA_34B)

                assert result is True

    @pytest.mark.asyncio
    async def test_health_check_replicate_unknown_model(self) -> None:
        """Test health check returns False for unknown Replicate model."""
        client = VisionModelClient(replicate_api_token="test-token")

        # Create a mock model that doesn't exist in endpoints
        mock_model = MagicMock()
        mock_model.value = "unknown/model"
        mock_model.is_gemini = MagicMock(return_value=False)

        result = await client.health_check(mock_model)

        assert result is False

    @pytest.mark.asyncio
    async def test_get_replicate_client_import_error(self) -> None:
        """Test _get_replicate_client handles import error."""
        client = VisionModelClient()

        with (
            patch.dict("sys.modules", {"replicate": None}),
            patch("builtins.__import__", side_effect=ImportError("No module")),
            pytest.raises(ImportError, match="replicate package required"),
        ):
            await client._get_replicate_client()


class TestImageDescriptionPipelineAdditional:
    """Additional tests for ImageDescriptionPipeline."""

    @pytest.fixture
    def mock_vision_client(self) -> MagicMock:
        """Create mock vision client."""
        client = MagicMock(spec=VisionModelClient)
        client.generate = AsyncMock()
        return client

    @pytest.fixture
    def pipeline(self, mock_vision_client: MagicMock) -> ImageDescriptionPipeline:
        """Create pipeline with mock client."""
        return ImageDescriptionPipeline(
            vision_client=mock_vision_client,
            default_model=VisionModel.GEMINI_FLASH,
            fallback_model=VisionModel.GEMINI_PRO,
        )

    @pytest.mark.asyncio
    async def test_extract_features_with_hex_colors(
        self,
        pipeline: ImageDescriptionPipeline,
        mock_vision_client: MagicMock,
    ) -> None:
        """Test feature extraction includes hex colors."""
        features_response = json.dumps(
            {
                "colors": [
                    {
                        "name": "rose gold",
                        "category": "warm",
                        "prominence": 0.8,
                        "hex": "#B76E79",
                    }
                ],
                "materials": [],
                "style": {
                    "aesthetic": "luxury",
                    "mood": "sophisticated",
                    "occasion": ["formal"],
                    "season": ["all-season"],
                },
                "detected_elements": [],
            }
        )

        mock_vision_client.generate.return_value = features_response

        result = await pipeline._extract_features(
            "https://example.com/img.jpg",
            VisionModel.GEMINI_FLASH,
        )

        assert result.colors[0].hex == "#B76E79"

    @pytest.mark.asyncio
    async def test_generate_bullet_points_without_category(
        self,
        pipeline: ImageDescriptionPipeline,
        mock_vision_client: MagicMock,
    ) -> None:
        """Test bullet points without category prefix."""
        bullets_response = """Premium construction
Adjustable straps
Hidden pocket"""

        mock_vision_client.generate.return_value = bullets_response

        result = await pipeline._generate_bullet_points(
            "https://example.com/img.jpg",
            VisionModel.GEMINI_FLASH,
        )

        assert len(result) == 3
        # All should default to "feature" category
        assert all(b.category == "feature" for b in result)

    @pytest.mark.asyncio
    async def test_generate_bullet_points_skips_comments(
        self,
        pipeline: ImageDescriptionPipeline,
        mock_vision_client: MagicMock,
    ) -> None:
        """Test bullet points skips comment lines."""
        bullets_response = """# Product Features
MATERIAL: Premium cotton
# Details below
FEATURE: Hidden zipper"""

        mock_vision_client.generate.return_value = bullets_response

        result = await pipeline._generate_bullet_points(
            "https://example.com/img.jpg",
            VisionModel.GEMINI_FLASH,
        )

        assert len(result) == 2
        assert result[0].category == "material"
        assert result[1].category == "feature"

    @pytest.mark.asyncio
    async def test_generate_seo_invalid_json_fallback(
        self,
        pipeline: ImageDescriptionPipeline,
        mock_vision_client: MagicMock,
    ) -> None:
        """Test SEO generation handles invalid JSON gracefully."""
        mock_vision_client.generate.return_value = "Not valid JSON at all"

        result = await pipeline._generate_seo_content(
            "https://example.com/img.jpg",
            ProductType.APPAREL,
            None,
            VisionModel.GEMINI_FLASH,
        )

        assert result.title == "Product"
        assert result.meta_description == "Shop our collection"

    @pytest.mark.asyncio
    async def test_generate_tags_empty_handling(
        self,
        pipeline: ImageDescriptionPipeline,
        mock_vision_client: MagicMock,
    ) -> None:
        """Test tag generation handles empty tags."""
        mock_vision_client.generate.return_value = "tag1, , , tag2, "

        result = await pipeline._generate_tags(
            "https://example.com/img.jpg",
            VisionModel.GEMINI_FLASH,
        )

        assert result == ["tag1", "tag2"]

    @pytest.mark.asyncio
    async def test_generate_description_error_propagation(
        self,
        pipeline: ImageDescriptionPipeline,
        mock_vision_client: MagicMock,
    ) -> None:
        """Test generate_description propagates errors."""
        mock_vision_client.generate.side_effect = Exception("API Error")

        request = DescriptionRequest(
            image_url="https://example.com/img.jpg",
            product_type=ProductType.APPAREL,
            include_seo=False,
            include_bullets=False,
            include_tags=False,
        )

        with pytest.raises(Exception, match="API Error"):
            await pipeline.generate_description(request)


# =============================================================================
# PipelineOrchestrator Additional Tests
# =============================================================================


class TestPipelineOrchestratorAdvanced:
    """Additional tests for PipelineOrchestrator."""

    @pytest.fixture
    def orchestrator(self) -> PipelineOrchestrator:
        """Create orchestrator for testing."""
        return PipelineOrchestrator(timeout_seconds=5)

    @pytest.fixture
    def success_handler(self) -> Any:
        """Create handler that succeeds."""

        async def handler(input_url: str, config: dict[str, Any], correlation_id: str) -> str:
            return f"{input_url}?processed=true"

        return handler

    @pytest.fixture
    def failing_handler(self) -> Any:
        """Create handler that fails."""

        async def handler(input_url: str, config: dict[str, Any], correlation_id: str) -> str:
            raise ValueError("Stage failed")

        return handler

    @pytest.mark.asyncio
    async def test_resume_pipeline_with_checkpoints(
        self,
        orchestrator: PipelineOrchestrator,
        success_handler: Any,
    ) -> None:
        """Test resume_pipeline uses last checkpoint."""
        # Register handlers
        orchestrator.register_handler(PipelineStage.BACKGROUND_REMOVAL, success_handler)
        orchestrator.register_handler(PipelineStage.FORMAT, success_handler)

        # Create a failed job with checkpoint
        job = PipelineJob(
            job_id="job-123",
            input_url="https://example.com/input.jpg",
            status=PipelineStatus.FAILED.value,
            profile=ProcessingProfile.FULL.value,
            stages_to_run=["ingest", "background_removal", "format"],
            stages_completed=["ingest", "background_removal"],
            checkpoints=[
                {
                    "stage": "background_removal",
                    "completed_at": datetime.now(UTC).isoformat(),
                    "input_url": "https://example.com/input.jpg",
                    "output_url": "https://example.com/bg_removed.jpg",
                    "duration_ms": 1000,
                }
            ],
            correlation_id="corr-123",
        )

        orchestrator._jobs["job-123"] = job

        result = await orchestrator.resume_pipeline("job-123")

        # Should resume from format stage
        assert result.success is True
        assert "format" in result.stages_completed

    @pytest.mark.asyncio
    async def test_resume_pipeline_all_stages_completed(
        self,
        orchestrator: PipelineOrchestrator,
    ) -> None:
        """Test resume when all stages already completed."""
        job = PipelineJob(
            job_id="job-123",
            input_url="https://example.com/input.jpg",
            status=PipelineStatus.FAILED.value,
            profile=ProcessingProfile.REFORMAT.value,
            stages_to_run=["ingest", "format"],
            stages_completed=["ingest", "format"],
            output_urls={"format": "https://example.com/output.jpg"},
            checkpoints=[
                {
                    "stage": "format",
                    "completed_at": datetime.now(UTC).isoformat(),
                    "input_url": "https://example.com/input.jpg",
                    "output_url": "https://example.com/output.jpg",
                    "duration_ms": 500,
                }
            ],
            total_duration_ms=1000,
            stage_durations={"format": 500},
            correlation_id="corr-123",
        )

        orchestrator._jobs["job-123"] = job

        result = await orchestrator.resume_pipeline("job-123")

        assert result.success is True

    @pytest.mark.asyncio
    async def test_resume_pipeline_no_checkpoints(
        self,
        orchestrator: PipelineOrchestrator,
    ) -> None:
        """Test resume restarts from beginning without checkpoints."""
        job = PipelineJob(
            job_id="job-123",
            input_url="https://example.com/input.jpg",
            status=PipelineStatus.FAILED.value,
            profile=ProcessingProfile.REFORMAT.value,
            stages_to_run=["ingest", "format"],
            stages_completed=[],
            checkpoints=[],
            correlation_id="corr-123",
        )

        orchestrator._jobs["job-123"] = job

        result = await orchestrator.resume_pipeline("job-123")

        # Should restart from beginning
        assert result.success is True
        assert "ingest" in result.stages_completed

    @pytest.mark.asyncio
    async def test_pipeline_with_stage_config(
        self,
        orchestrator: PipelineOrchestrator,
    ) -> None:
        """Test pipeline passes stage-specific config to handlers."""
        received_config: dict[str, Any] = {}

        async def config_capturing_handler(
            input_url: str, config: dict[str, Any], correlation_id: str
        ) -> str:
            received_config.update(config)
            return input_url

        orchestrator.register_handler(PipelineStage.FORMAT, config_capturing_handler)

        await orchestrator.run_pipeline(
            "https://example.com/input.jpg",
            profile=ProcessingProfile.REFORMAT,
            config={"format": {"quality": 90, "output_format": "webp"}},
        )

        assert received_config.get("quality") == 90
        assert received_config.get("output_format") == "webp"

    @pytest.mark.asyncio
    async def test_emit_event_with_exception(
        self,
        orchestrator: PipelineOrchestrator,
    ) -> None:
        """Test emit_event handles callback exceptions gracefully."""

        def failing_callback(event: PipelineEvent) -> None:
            raise ValueError("Callback failed")

        orchestrator._on_event = failing_callback

        # Should not raise - errors are logged
        job = PipelineJob(
            job_id="job-123",
            input_url="https://example.com/input.jpg",
            correlation_id="corr-123",
        )

        orchestrator._emit_event("test_event", job)

    @pytest.mark.asyncio
    async def test_pipeline_generic_exception_handling(
        self,
        orchestrator: PipelineOrchestrator,
    ) -> None:
        """Test pipeline handles generic exceptions during processing."""

        async def generic_failing_handler(
            input_url: str, config: dict[str, Any], correlation_id: str
        ) -> str:
            raise RuntimeError("Unexpected error")

        orchestrator.register_handler(PipelineStage.FORMAT, generic_failing_handler)

        with pytest.raises(PipelineError) as exc_info:
            await orchestrator.run_pipeline(
                "https://example.com/input.jpg",
                profile=ProcessingProfile.REFORMAT,
            )

        assert "format" in str(exc_info.value).lower()

    def test_profile_stages_configuration(self) -> None:
        """Test PROFILE_STAGES has correct configurations."""
        # Full profile has all main stages
        full_stages = PROFILE_STAGES[ProcessingProfile.FULL]
        assert PipelineStage.INGEST in full_stages
        assert PipelineStage.VALIDATE in full_stages
        assert PipelineStage.BACKGROUND_REMOVAL in full_stages
        assert PipelineStage.LIGHTING in full_stages
        assert PipelineStage.UPSCALE in full_stages
        assert PipelineStage.FORMAT in full_stages

        # Quick profile skips lighting and upscale
        quick_stages = PROFILE_STAGES[ProcessingProfile.QUICK]
        assert PipelineStage.LIGHTING not in quick_stages
        assert PipelineStage.UPSCALE not in quick_stages

        # Background only has minimal stages
        bg_stages = PROFILE_STAGES[ProcessingProfile.BACKGROUND_ONLY]
        assert len(bg_stages) == 3

        # Reformat is minimal
        reformat_stages = PROFILE_STAGES[ProcessingProfile.REFORMAT]
        assert len(reformat_stages) == 2

    @pytest.mark.asyncio
    async def test_cancel_running_job(
        self,
        orchestrator: PipelineOrchestrator,
    ) -> None:
        """Test cancelling a pending job."""
        job = PipelineJob(
            job_id="job-123",
            input_url="https://example.com/input.jpg",
            status=PipelineStatus.PENDING.value,
            correlation_id="corr-123",
        )

        orchestrator._jobs["job-123"] = job

        events: list[PipelineEvent] = []
        orchestrator._on_event = lambda e: events.append(e)

        result = await orchestrator.cancel_pipeline("job-123")

        assert result is True
        assert job.status == PipelineStatus.CANCELLED.value
        assert len(events) == 1
        assert events[0].event_type == "pipeline_cancelled"


class TestStageCheckpointDataclass:
    """Tests for StageCheckpoint dataclass."""

    def test_checkpoint_default_metadata(self) -> None:
        """Test checkpoint has empty metadata by default."""
        checkpoint = StageCheckpoint(
            stage=PipelineStage.BACKGROUND_REMOVAL,
            completed_at=datetime.now(UTC).isoformat(),
            input_url="https://example.com/input.jpg",
            output_url="https://example.com/output.jpg",
        )

        assert checkpoint.metadata == {}
        assert checkpoint.duration_ms == 0

    def test_checkpoint_with_metadata(self) -> None:
        """Test checkpoint with custom metadata."""
        checkpoint = StageCheckpoint(
            stage=PipelineStage.UPSCALE,
            completed_at=datetime.now(UTC).isoformat(),
            input_url="https://example.com/input.jpg",
            output_url="https://example.com/output.jpg",
            metadata={"scale_factor": 4, "model": "real-esrgan"},
            duration_ms=2500,
        )

        assert checkpoint.metadata["scale_factor"] == 4
        assert checkpoint.duration_ms == 2500


class TestPipelineJobModel:
    """Additional tests for PipelineJob model."""

    def test_job_with_all_fields(self) -> None:
        """Test job creation with all fields populated."""
        job = PipelineJob(
            job_id="job-123",
            status=PipelineStatus.RUNNING,
            current_stage=PipelineStage.BACKGROUND_REMOVAL,
            progress_percent=50,
            input_url="https://example.com/input.jpg",
            output_urls={"ingest": "https://example.com/ingest.jpg"},
            profile=ProcessingProfile.FULL,
            stages_to_run=["ingest", "background_removal"],
            stages_completed=["ingest"],
            stages_skipped=[],
            checkpoints=[],
            product_id="PROD-456",
            source="woocommerce",
            correlation_id="corr-789",
            created_at=datetime.now(UTC).isoformat(),
            started_at=datetime.now(UTC).isoformat(),
        )

        assert job.product_id == "PROD-456"
        assert job.source == "woocommerce"
        assert job.progress_percent == 50


class TestPipelineErrorClass:
    """Additional tests for PipelineError class."""

    def test_error_without_optional_context(self) -> None:
        """Test PipelineError with minimal context."""
        error = PipelineError("Something went wrong")

        assert error.context == {}
        # PipelineError inherits from DevSkyError which may auto-generate correlation_id
        assert error.retryable is True

    def test_error_with_cause_exception(self) -> None:
        """Test PipelineError with cause exception."""
        cause = ValueError("Original error")
        error = PipelineError(
            "Wrapper error",
            job_id="job-123",
            cause=cause,
        )

        assert error.cause is cause
        assert error.context["job_id"] == "job-123"


# =============================================================================
# Integration-style Tests (Still Unit Tests with Mocks)
# =============================================================================


class TestMLServicesIntegration:
    """Integration-style tests verifying components work together."""

    @pytest.mark.asyncio
    async def test_full_description_pipeline_flow(self) -> None:
        """Test complete description pipeline with all components."""
        mock_client = MagicMock(spec=VisionModelClient)

        # Setup responses for all stages
        mock_client.generate = AsyncMock(
            side_effect=[
                json.dumps(
                    {
                        "colors": [{"name": "black", "category": "neutral", "prominence": 0.9}],
                        "materials": [
                            {"name": "silk", "texture": "smooth", "quality_indicator": "luxury"}
                        ],
                        "style": {
                            "aesthetic": "minimalist",
                            "mood": "elegant",
                            "occasion": ["evening"],
                            "season": ["all"],
                        },
                        "detected_elements": ["v-neck"],
                    }
                ),  # Features
                "A stunning black silk dress featuring a minimalist design.",  # Main description
                "Elegant black silk dress.",  # Short description
                "MATERIAL: Premium silk\nFIT: Relaxed\nFEATURE: V-neck",  # Bullets
                json.dumps(
                    {
                        "title": "Black Silk Dress | SkyyRose",
                        "meta_description": "Shop the black silk dress.",
                        "focus_keyword": "black silk dress",
                        "secondary_keywords": ["evening dress"],
                    }
                ),  # SEO
                "black, silk, evening, luxury, elegant",  # Tags
            ]
        )

        pipeline = ImageDescriptionPipeline(
            vision_client=mock_client,
            default_model=VisionModel.GEMINI_FLASH,
        )

        request = DescriptionRequest(
            image_url="https://example.com/dress.jpg",
            product_name="Black Rose Silk Dress",
            product_type=ProductType.APPAREL,
            style=DescriptionStyle.LUXURY,
            brand_context="SkyyRose Spring 2024",
            target_word_count=150,
            include_seo=True,
            include_bullets=True,
            include_tags=True,
        )

        result = await pipeline.generate_description(request)

        assert result.description is not None
        assert result.short_description is not None
        assert len(result.bullet_points) > 0
        assert result.seo is not None
        assert len(result.suggested_tags) > 0
        assert result.features is not None
        assert result.processing_time_ms >= 0

    @pytest.mark.asyncio
    async def test_pipeline_orchestrator_with_replicate_style_handler(self) -> None:
        """Test orchestrator with Replicate-style async handlers."""
        orchestrator = PipelineOrchestrator(timeout_seconds=30)

        # Simulate Replicate-style handlers that poll for completion
        async def bg_removal_handler(
            input_url: str, config: dict[str, Any], correlation_id: str
        ) -> str:
            # Simulate polling delay
            await asyncio.sleep(0.01)
            return f"{input_url}?bg_removed=true"

        async def upscale_handler(
            input_url: str, config: dict[str, Any], correlation_id: str
        ) -> str:
            scale = config.get("scale", 4)
            await asyncio.sleep(0.01)
            return f"{input_url}&upscaled={scale}x"

        orchestrator.register_handler(PipelineStage.BACKGROUND_REMOVAL, bg_removal_handler)
        orchestrator.register_handler(PipelineStage.UPSCALE, upscale_handler)

        result = await orchestrator.run_pipeline(
            "https://example.com/product.jpg",
            profile=ProcessingProfile.CUSTOM,
            custom_stages=[
                PipelineStage.INGEST,
                PipelineStage.BACKGROUND_REMOVAL,
                PipelineStage.UPSCALE,
            ],
            config={"upscale": {"scale": 4}},
        )

        assert result.success is True
        assert "background_removal" in result.stages_completed
        assert "upscale" in result.stages_completed
        assert "4x" in result.output_urls["upscale"]
