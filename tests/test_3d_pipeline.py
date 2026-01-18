#!/usr/bin/env python3
"""
Tests for 3D Generation Pipeline.

Verifies:
1. Proper async/await patterns (no deadlocks)
2. Rate limiting implementation
3. Provider fallback chain
4. Response parsing
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestMeshyClient:
    """Tests for MeshyClient async implementation."""

    @pytest.mark.asyncio
    async def test_meshy_client_initialization(self):
        """Test MeshyClient initializes properly."""
        with patch("ai_3d.providers.meshy.MESHY_API_KEY", "test-api-key"):
            from ai_3d.providers.meshy import MeshyClient

            client = MeshyClient()
            assert client.api_key == "test-api-key"
            assert client._semaphore._value == 5  # MAX_CONCURRENT_REQUESTS
            await client.close()

    @pytest.mark.asyncio
    async def test_meshy_client_context_manager(self):
        """Test MeshyClient works as async context manager."""
        with patch("ai_3d.providers.meshy.MESHY_API_KEY", "test-api-key"):
            from ai_3d.providers.meshy import MeshyClient

            async with MeshyClient() as client:
                assert client is not None
                assert client.api_key == "test-api-key"

    @pytest.mark.asyncio
    async def test_meshy_rate_limiting_semaphore(self):
        """Test rate limiting semaphore is properly configured."""
        with patch("ai_3d.providers.meshy.MESHY_API_KEY", "test-api-key"):
            from ai_3d.providers.meshy import MeshyClient

            client = MeshyClient()

            # Verify semaphore limits concurrent requests
            assert client.MAX_CONCURRENT_REQUESTS == 5
            assert client.MIN_DELAY_BETWEEN_CALLS == 2.0

            await client.close()

    def test_meshy_client_requires_api_key(self):
        """Test MeshyClient raises error without API key."""
        from ai_3d.providers.meshy import MeshyClient
        from errors.production_errors import ConfigurationError

        # Patch both the module constant AND os.getenv to ensure no API key
        with (
            patch("ai_3d.providers.meshy.MESHY_API_KEY", ""),
            patch("os.getenv", return_value=None),
        ):
            with pytest.raises(ConfigurationError) as exc_info:
                MeshyClient()

            assert "MESHY_API_KEY" in str(exc_info.value)


class TestHuggingFaceClient:
    """Tests for HuggingFace3DClient async implementation."""

    @pytest.fixture
    def mock_hf_token(self, monkeypatch):
        """Set mock HuggingFace token."""
        monkeypatch.setenv("HUGGINGFACE_API_KEY", "test-hf-token")

    @pytest.mark.asyncio
    async def test_huggingface_client_initialization(self, mock_hf_token):
        """Test HuggingFace3DClient initializes properly."""
        from ai_3d.providers.huggingface import HuggingFace3DClient

        client = HuggingFace3DClient()
        assert client.api_key == "test-hf-token"
        assert client._semaphore._value == 5
        await client.close()

    @pytest.mark.asyncio
    async def test_huggingface_trellis_is_default(self, mock_hf_token):
        """Test TRELLIS is the default model."""
        from ai_3d.providers.huggingface import HuggingFace3DClient

        client = HuggingFace3DClient()
        assert client.DEFAULT_MODEL == "trellis"
        assert "trellis" in client.MODELS
        assert client.MODELS["trellis"] == "microsoft/TRELLIS-image-large"
        await client.close()

    def test_huggingface_client_requires_token(self, monkeypatch):
        """Test HuggingFace3DClient raises error without token."""
        monkeypatch.delenv("HUGGINGFACE_API_KEY", raising=False)
        monkeypatch.delenv("HF_TOKEN", raising=False)

        from ai_3d.providers.huggingface import HuggingFace3DClient
        from errors.production_errors import ConfigurationError

        with pytest.raises(ConfigurationError) as exc_info:
            HuggingFace3DClient()

        assert "HUGGINGFACE_API_KEY" in str(exc_info.value)


class TestGenerationPipeline:
    """Tests for ThreeDGenerationPipeline."""

    @pytest.fixture
    def mock_providers(self, monkeypatch):
        """Set mock API keys for all providers."""
        monkeypatch.setenv("HUGGINGFACE_API_KEY", "test-hf-token")
        monkeypatch.setenv("MESHY_API_KEY", "test-meshy-key")
        monkeypatch.setenv("TRIPO_API_KEY", "test-tripo-key")

    def test_provider_enum_includes_trellis(self):
        """Test TRELLIS is in the provider enum."""
        from ai_3d.generation_pipeline import ThreeDProvider

        assert ThreeDProvider.TRELLIS.value == "trellis"
        assert ThreeDProvider.MESHY.value == "meshy"
        assert ThreeDProvider.TRIPO.value == "tripo"

    def test_default_fallback_chain(self):
        """Test default fallback chain is TRELLIS -> Meshy -> Tripo."""
        from ai_3d.generation_pipeline import GenerationConfig, ThreeDProvider

        config = GenerationConfig()
        assert config.fallback_providers == [
            ThreeDProvider.TRELLIS,
            ThreeDProvider.MESHY,
            ThreeDProvider.TRIPO,
        ]

    @pytest.mark.asyncio
    async def test_pipeline_selects_trellis_first(self, mock_providers):
        """Test pipeline prefers TRELLIS for image-to-3D."""
        from ai_3d.generation_pipeline import (
            GenerationConfig,
            ThreeDGenerationPipeline,
            ThreeDProvider,
        )

        # Mock the providers AND ModelFidelityValidator (which requires trimesh)
        with (
            patch("ai_3d.providers.huggingface.HuggingFace3DClient"),
            patch("ai_3d.providers.meshy.MeshyClient"),
            patch("ai_3d.providers.tripo.TripoClient"),
            patch("ai_3d.generation_pipeline.ModelFidelityValidator"),
        ):
            pipeline = ThreeDGenerationPipeline()
            config = GenerationConfig()

            # Should select TRELLIS first
            selected = pipeline._select_provider(config, text_to_3d=False)
            assert selected in [ThreeDProvider.TRELLIS, ThreeDProvider.HUGGINGFACE]


class TestRateLimitingPatterns:
    """Tests for rate limiting and exponential backoff."""

    @pytest.mark.asyncio
    async def test_exponential_backoff_config(self):
        """Test exponential backoff is properly configured."""
        from ai_3d.providers.meshy import MeshyClient

        # Verify backoff settings
        assert MeshyClient.INITIAL_BACKOFF == 1.0
        assert MeshyClient.MAX_BACKOFF == 60.0
        assert MeshyClient.BACKOFF_MULTIPLIER == 2.0
        assert MeshyClient.MAX_RETRIES == 5

    @pytest.mark.asyncio
    async def test_semaphore_concurrency_limit(self):
        """Test semaphore properly limits concurrent requests."""
        with patch("ai_3d.providers.meshy.MESHY_API_KEY", "test-key"):
            from ai_3d.providers.meshy import MeshyClient

            client = MeshyClient()

            # Acquire all semaphore slots
            acquired = []
            for _ in range(5):
                acquired.append(await client._semaphore.acquire())

            # Semaphore should be at 0
            assert client._semaphore._value == 0

            # Release all
            for _ in acquired:
                client._semaphore.release()

            assert client._semaphore._value == 5

            await client.close()


class TestAsyncPatterns:
    """Tests for proper async/await patterns (no deadlocks)."""

    @pytest.mark.asyncio
    async def test_no_blocking_calls_in_meshy(self):
        """Test MeshyClient doesn't use blocking calls."""
        with patch("ai_3d.providers.meshy.MESHY_API_KEY", "test-key"):
            from ai_3d.providers.meshy import MeshyClient

            # Should complete without deadlock in reasonable time
            async def test_init():
                client = MeshyClient()
                await client.close()

            try:
                await asyncio.wait_for(test_init(), timeout=5.0)
            except TimeoutError:
                pytest.fail("MeshyClient initialization timed out - possible deadlock")

    @pytest.mark.asyncio
    async def test_context_manager_cleanup(self):
        """Test async context manager properly cleans up."""
        with patch("ai_3d.providers.meshy.MESHY_API_KEY", "test-key"):
            from ai_3d.providers.meshy import MeshyClient

            async with MeshyClient() as client:
                assert client._client is not None

            # Client should be closed after context manager exits


class TestErrorHandling:
    """Tests for error handling in 3D pipeline."""

    def test_rate_limit_error_has_service(self):
        """Test RateLimitError includes service name."""
        from errors.production_errors import RateLimitError

        error = RateLimitError(service="Meshy", retry_after=60)
        assert "Meshy" in str(error)
        assert error.retry_after_seconds == 60
        assert error.retryable is True

    def test_external_service_error_formats(self):
        """Test ExternalServiceError accepts error_message param."""
        from errors.production_errors import ExternalServiceError

        error = ExternalServiceError(
            service_name="Meshy",
            error_message="HTTP 429: Rate limited",
        )
        assert "429" in str(error)
        assert error.context["service_name"] == "Meshy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
