# tests/services/test_replicate_client.py
"""
Unit tests for Replicate client.

Tests cover:
- Configuration and validation
- Prediction creation and polling
- Error handling and retries
- High-level methods (background removal, upscaling, 3D)

Author: DevSkyy Platform Team
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

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

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def config() -> ReplicateConfig:
    """Create test configuration."""
    return ReplicateConfig(
        api_token="test-token",
        timeout=10.0,
        poll_interval=0.1,
        max_poll_attempts=5,
        max_retries=2,
    )


@pytest.fixture
def client(config: ReplicateConfig) -> ReplicateClient:
    """Create test client."""
    return ReplicateClient(config)


@pytest.fixture
def mock_prediction_starting() -> dict:
    """Create mock starting prediction response."""
    return {
        "id": "pred-123",
        "version": "abc123",
        "status": "starting",
        "input": {"image": "https://example.com/image.jpg"},
        "output": None,
        "error": None,
        "logs": "",
        "urls": {"get": "https://api.replicate.com/v1/predictions/pred-123"},
    }


@pytest.fixture
def mock_prediction_succeeded() -> dict:
    """Create mock succeeded prediction response."""
    return {
        "id": "pred-123",
        "version": "abc123",
        "status": "succeeded",
        "input": {"image": "https://example.com/image.jpg"},
        "output": "https://output.com/result.png",
        "error": None,
        "logs": "Processing complete",
        "metrics": {"predict_time": 2.5},
    }


@pytest.fixture
def mock_prediction_failed() -> dict:
    """Create mock failed prediction response."""
    return {
        "id": "pred-123",
        "version": "abc123",
        "status": "failed",
        "input": {"image": "https://example.com/image.jpg"},
        "output": None,
        "error": "Model execution failed",
        "logs": "Error during inference",
    }


# =============================================================================
# Configuration Tests
# =============================================================================


class TestReplicateConfig:
    """Tests for ReplicateConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = ReplicateConfig(api_token="test")
        assert config.base_url == "https://api.replicate.com/v1"
        assert config.timeout == 60.0
        assert config.poll_interval == 2.0
        assert config.max_retries == 3

    def test_config_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test configuration from environment."""
        monkeypatch.setenv("REPLICATE_API_TOKEN", "env-token")
        config = ReplicateConfig.from_env()
        assert config.api_token == "env-token"

    def test_config_validation_missing_token(self) -> None:
        """Test validation fails without API token."""
        config = ReplicateConfig(api_token="")
        with pytest.raises(ReplicateError) as exc_info:
            config.validate()
        assert "REPLICATE_API_TOKEN" in str(exc_info.value)


# =============================================================================
# Input Validation Tests
# =============================================================================


class TestInputValidation:
    """Tests for input validation models."""

    def test_background_removal_valid_url(self) -> None:
        """Test valid URL input."""
        input_model = BackgroundRemovalInput(image="https://example.com/img.jpg")
        assert input_model.image == "https://example.com/img.jpg"

    def test_background_removal_valid_base64(self) -> None:
        """Test valid base64 input."""
        input_model = BackgroundRemovalInput(image="data:image/png;base64,abc123")
        assert input_model.image.startswith("data:image/")

    def test_background_removal_invalid_image(self) -> None:
        """Test invalid image input."""
        with pytest.raises(ValueError) as exc_info:
            BackgroundRemovalInput(image="not-a-url")
        assert "URL or base64" in str(exc_info.value)

    def test_upscale_valid_input(self) -> None:
        """Test valid upscale input."""
        input_model = ImageUpscaleInput(
            image="https://example.com/img.jpg",
            scale=4,
            face_enhance=True,
        )
        assert input_model.scale == 4
        assert input_model.face_enhance is True

    def test_upscale_invalid_scale(self) -> None:
        """Test invalid scale factor."""
        with pytest.raises(ValueError):
            ImageUpscaleInput(
                image="https://example.com/img.jpg",
                scale=16,  # Max is 8
            )

    def test_image_to_3d_valid_input(self) -> None:
        """Test valid 3D input."""
        input_model = ImageTo3DInput(
            image="https://example.com/img.jpg",
            output_format="glb",
        )
        assert input_model.output_format == "glb"

    def test_image_to_3d_invalid_format(self) -> None:
        """Test invalid output format."""
        with pytest.raises(ValueError) as exc_info:
            ImageTo3DInput(
                image="https://example.com/img.jpg",
                output_format="invalid",
            )
        assert "Output format" in str(exc_info.value)


# =============================================================================
# Prediction Model Tests
# =============================================================================


class TestReplicatePrediction:
    """Tests for ReplicatePrediction model."""

    def test_parse_starting_prediction(self, mock_prediction_starting: dict) -> None:
        """Test parsing starting prediction."""
        pred = ReplicatePrediction.model_validate(mock_prediction_starting)
        assert pred.id == "pred-123"
        assert pred.status == ReplicatePredictionStatus.STARTING
        assert pred.is_terminal is False
        assert pred.succeeded is False

    def test_parse_succeeded_prediction(self, mock_prediction_succeeded: dict) -> None:
        """Test parsing succeeded prediction."""
        pred = ReplicatePrediction.model_validate(mock_prediction_succeeded)
        assert pred.status == ReplicatePredictionStatus.SUCCEEDED
        assert pred.is_terminal is True
        assert pred.succeeded is True
        assert pred.output == "https://output.com/result.png"

    def test_parse_failed_prediction(self, mock_prediction_failed: dict) -> None:
        """Test parsing failed prediction."""
        pred = ReplicatePrediction.model_validate(mock_prediction_failed)
        assert pred.status == ReplicatePredictionStatus.FAILED
        assert pred.is_terminal is True
        assert pred.succeeded is False
        assert pred.error == "Model execution failed"


# =============================================================================
# Client Tests
# =============================================================================


class TestReplicateClient:
    """Tests for ReplicateClient."""

    @pytest.mark.asyncio
    async def test_client_context_manager(self, config: ReplicateConfig) -> None:
        """Test client as async context manager."""
        async with ReplicateClient(config) as client:
            assert client._client is not None
            assert not client._client.is_closed

    @pytest.mark.asyncio
    async def test_create_prediction(
        self,
        client: ReplicateClient,
        mock_prediction_starting: dict,
    ) -> None:
        """Test creating a prediction."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_prediction_starting

            prediction = await client.create_prediction(
                "owner/model:version",
                {"image": "https://example.com/img.jpg"},
            )

            assert prediction.id == "pred-123"
            mock_req.assert_called_once()

    @pytest.mark.asyncio
    async def test_wait_for_prediction_success(
        self,
        client: ReplicateClient,
        mock_prediction_starting: dict,
        mock_prediction_succeeded: dict,
    ) -> None:
        """Test waiting for prediction to complete."""
        with patch.object(client, "get_prediction", new_callable=AsyncMock) as mock_get:
            # Return starting status first, then succeeded
            mock_get.side_effect = [
                ReplicatePrediction.model_validate(mock_prediction_starting),
                ReplicatePrediction.model_validate(mock_prediction_succeeded),
            ]

            prediction = await client.wait_for_prediction("pred-123")

            assert prediction.succeeded is True
            assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_wait_for_prediction_failure(
        self,
        client: ReplicateClient,
        mock_prediction_failed: dict,
    ) -> None:
        """Test waiting for failed prediction."""
        with patch.object(client, "get_prediction", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = ReplicatePrediction.model_validate(mock_prediction_failed)

            with pytest.raises(ReplicateError) as exc_info:
                await client.wait_for_prediction("pred-123")

            assert "Prediction failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_wait_for_prediction_timeout(
        self,
        client: ReplicateClient,
        mock_prediction_starting: dict,
    ) -> None:
        """Test prediction timeout."""
        with patch.object(client, "get_prediction", new_callable=AsyncMock) as mock_get:
            # Always return starting status
            mock_get.return_value = ReplicatePrediction.model_validate(mock_prediction_starting)

            with pytest.raises(ReplicateTimeoutError):
                await client.wait_for_prediction("pred-123")

    @pytest.mark.asyncio
    async def test_remove_background(
        self,
        client: ReplicateClient,
        mock_prediction_succeeded: dict,
    ) -> None:
        """Test background removal convenience method."""
        with patch.object(client, "run_prediction", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = ReplicatePrediction.model_validate(mock_prediction_succeeded)

            result = await client.remove_background("https://example.com/img.jpg")

            assert result.succeeded is True
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert "image" in call_args.args[1]

    @pytest.mark.asyncio
    async def test_upscale_image(
        self,
        client: ReplicateClient,
        mock_prediction_succeeded: dict,
    ) -> None:
        """Test image upscaling convenience method."""
        with patch.object(client, "run_prediction", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = ReplicatePrediction.model_validate(mock_prediction_succeeded)

            result = await client.upscale_image(
                "https://example.com/img.jpg",
                scale=4,
                face_enhance=True,
            )

            assert result.succeeded is True
            call_args = mock_run.call_args
            assert call_args.args[1]["scale"] == 4
            assert call_args.args[1]["face_enhance"] is True

    @pytest.mark.asyncio
    async def test_image_to_3d(
        self,
        client: ReplicateClient,
        mock_prediction_succeeded: dict,
    ) -> None:
        """Test image-to-3D convenience method."""
        with patch.object(client, "run_prediction", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = ReplicatePrediction.model_validate(mock_prediction_succeeded)

            result = await client.image_to_3d(
                "https://example.com/img.jpg",
                output_format="glb",
            )

            assert result.succeeded is True
            call_args = mock_run.call_args
            assert call_args.args[1]["output_format"] == "glb"


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    def test_replicate_error_with_context(self) -> None:
        """Test ReplicateError with context."""
        error = ReplicateError(
            "Test error",
            model="owner/model",
            prediction_id="pred-123",
            correlation_id="corr-456",
        )
        assert error.context["model"] == "owner/model"
        assert error.context["prediction_id"] == "pred-123"
        assert error.correlation_id == "corr-456"

    def test_rate_limit_error(self) -> None:
        """Test rate limit error."""
        error = ReplicateRateLimitError(retry_after_seconds=120)
        assert error.retryable is True
        assert error.retry_after_seconds == 120

    def test_timeout_error(self) -> None:
        """Test timeout error."""
        error = ReplicateTimeoutError("Prediction timed out")
        assert error.retryable is True

    def test_error_to_dict(self) -> None:
        """Test error serialization."""
        error = ReplicateError(
            "Test error",
            correlation_id="corr-123",
        )
        error_dict = error.to_dict()
        assert "error" in error_dict
        assert error_dict["error"]["correlation_id"] == "corr-123"
