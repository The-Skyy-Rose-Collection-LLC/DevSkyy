# tests/services/three_d/test_provider_interface.py
"""Tests for 3D provider interface and models."""

import pytest
from datetime import datetime, UTC

from services.three_d.provider_interface import (
    I3DProvider,
    OutputFormat,
    ProviderHealth,
    ProviderStatus,
    QualityLevel,
    ThreeDCapability,
    ThreeDGenerationError,
    ThreeDProviderError,
    ThreeDRequest,
    ThreeDResponse,
    ThreeDTimeoutError,
)


class TestThreeDRequest:
    """Tests for ThreeDRequest model."""

    def test_text_request_detection(self) -> None:
        """Request with prompt should be detected as text request."""
        request = ThreeDRequest(prompt="luxury hoodie")
        assert request.is_text_request() is True
        assert request.is_image_request() is False

    def test_image_url_request_detection(self) -> None:
        """Request with image_url should be detected as image request."""
        request = ThreeDRequest(image_url="https://example.com/image.jpg")
        assert request.is_text_request() is False
        assert request.is_image_request() is True

    def test_image_path_request_detection(self) -> None:
        """Request with image_path should be detected as image request."""
        request = ThreeDRequest(image_path="/path/to/image.jpg")
        assert request.is_text_request() is False
        assert request.is_image_request() is True

    def test_get_image_source_url(self) -> None:
        """get_image_source should return image_url if set."""
        request = ThreeDRequest(
            image_url="https://example.com/image.jpg",
            image_path="/path/to/image.jpg",
        )
        assert request.get_image_source() == "https://example.com/image.jpg"

    def test_get_image_source_path(self) -> None:
        """get_image_source should return image_path if no URL."""
        request = ThreeDRequest(image_path="/path/to/image.jpg")
        assert request.get_image_source() == "/path/to/image.jpg"

    def test_default_values(self) -> None:
        """Request should have sensible defaults."""
        request = ThreeDRequest()
        assert request.output_format == OutputFormat.GLB
        assert request.quality == QualityLevel.PRODUCTION
        assert request.texture_size == 1024


class TestThreeDResponse:
    """Tests for ThreeDResponse model."""

    def test_response_creation(self) -> None:
        """Response should be created with required fields."""
        response = ThreeDResponse(
            success=True,
            task_id="test_123",
            status="completed",
            provider="test_provider",
        )
        assert response.success is True
        assert response.task_id == "test_123"
        assert response.provider == "test_provider"

    def test_response_with_model_urls(self) -> None:
        """Response should store model URLs."""
        response = ThreeDResponse(
            success=True,
            task_id="test_123",
            status="completed",
            provider="test_provider",
            model_url="https://cdn.example.com/model.glb",
            model_path="/local/path/model.glb",
        )
        assert response.model_url == "https://cdn.example.com/model.glb"
        assert response.model_path == "/local/path/model.glb"


class TestProviderHealth:
    """Tests for ProviderHealth model."""

    def test_is_available_when_available(self) -> None:
        """Provider should be available when status is AVAILABLE."""
        health = ProviderHealth(
            provider="test",
            status=ProviderStatus.AVAILABLE,
            capabilities=[ThreeDCapability.TEXT_TO_3D],
        )
        assert health.is_available is True

    def test_is_available_when_degraded(self) -> None:
        """Provider should be available when status is DEGRADED."""
        health = ProviderHealth(
            provider="test",
            status=ProviderStatus.DEGRADED,
            capabilities=[ThreeDCapability.TEXT_TO_3D],
        )
        assert health.is_available is True

    def test_not_available_when_unavailable(self) -> None:
        """Provider should not be available when status is UNAVAILABLE."""
        health = ProviderHealth(
            provider="test",
            status=ProviderStatus.UNAVAILABLE,
            capabilities=[ThreeDCapability.TEXT_TO_3D],
        )
        assert health.is_available is False

    def test_supports_capability(self) -> None:
        """Health should correctly report supported capabilities."""
        health = ProviderHealth(
            provider="test",
            status=ProviderStatus.AVAILABLE,
            capabilities=[ThreeDCapability.TEXT_TO_3D, ThreeDCapability.IMAGE_TO_3D],
        )
        assert health.supports(ThreeDCapability.TEXT_TO_3D) is True
        assert health.supports(ThreeDCapability.IMAGE_TO_3D) is True
        assert health.supports(ThreeDCapability.MULTI_VIEW) is False


class TestErrors:
    """Tests for error classes."""

    def test_provider_error(self) -> None:
        """ThreeDProviderError should include provider context."""
        error = ThreeDProviderError(
            "Test error",
            provider="test_provider",
            correlation_id="corr_123",
        )
        assert "Test error" in str(error)
        assert error.provider == "test_provider"
        assert error.correlation_id == "corr_123"

    def test_generation_error_with_task_id(self) -> None:
        """ThreeDGenerationError should include task_id."""
        error = ThreeDGenerationError(
            "Generation failed",
            provider="test_provider",
            task_id="task_123",
        )
        assert error.task_id == "task_123"

    def test_timeout_error_is_retryable(self) -> None:
        """ThreeDTimeoutError should be marked as retryable."""
        error = ThreeDTimeoutError(
            "Timed out",
            timeout_seconds=60.0,
        )
        assert error.retryable is True
        assert error.timeout_seconds == 60.0


class TestEnums:
    """Tests for enum values."""

    def test_output_format_values(self) -> None:
        """OutputFormat enum should have expected values."""
        assert OutputFormat.GLB.value == "glb"
        assert OutputFormat.GLTF.value == "gltf"
        assert OutputFormat.OBJ.value == "obj"

    def test_quality_level_values(self) -> None:
        """QualityLevel enum should have expected values."""
        assert QualityLevel.DRAFT.value == "draft"
        assert QualityLevel.STANDARD.value == "standard"
        assert QualityLevel.PRODUCTION.value == "production"

    def test_capability_values(self) -> None:
        """ThreeDCapability enum should have expected values."""
        assert ThreeDCapability.TEXT_TO_3D.value == "text_to_3d"
        assert ThreeDCapability.IMAGE_TO_3D.value == "image_to_3d"
