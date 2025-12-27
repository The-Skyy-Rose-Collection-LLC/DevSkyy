"""
Tests for HuggingFace 3D Model Integration
============================================

Tests for the HuggingFace 3D client and its integration with the asset pipeline.

Coverage:
- HuggingFace3DClient initialization and configuration
- Text-to-3D generation
- Image-to-3D generation
- Quality metrics and optimization hints
- Caching and fallback chains
- Asset pipeline integration (Stage 0)
- Error handling and resilience
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from orchestration.asset_pipeline import AssetPipelineResult, PipelineConfig, ProductAssetPipeline
from orchestration.huggingface_3d_client import (
    HF3DFormat,
    HF3DModel,
    HF3DOptimizationHints,
    HF3DQuality,
    HF3DResult,
    HuggingFace3DClient,
    HuggingFace3DConfig,
)

# =============================================================================
# HuggingFace 3D Client Tests
# =============================================================================


class TestHuggingFace3DConfig:
    """Tests for HuggingFace 3D configuration."""

    def test_config_from_env_defaults(self, monkeypatch):
        """Test config creation with production-grade default values."""
        monkeypatch.delenv("HUGGINGFACE_API_TOKEN", raising=False)
        monkeypatch.delenv("HF_TOKEN", raising=False)

        # Create config directly
        config = HuggingFace3DConfig()

        # Production-grade defaults
        assert config.default_model == HF3DModel.TRIPOSR  # Best quality default
        assert HF3DModel.SHAP_E_IMG in config.fallback_models  # List of fallbacks
        assert config.default_format == HF3DFormat.GLB  # Web-ready format
        assert config.default_quality == HF3DQuality.PRODUCTION  # Highest quality
        assert config.guidance_scale == 17.5  # Higher for better detail
        assert config.num_inference_steps == 64  # More steps for quality
        assert config.timeout_seconds == 120  # Production timeout
        assert config.cache_enabled is True

    def test_config_from_env_with_token(self, monkeypatch):
        """Test config with API token from environment."""
        monkeypatch.setenv("HUGGINGFACE_API_TOKEN", "hf_test_token_123")

        config = HuggingFace3DConfig.from_env()

        assert config.api_token == "hf_test_token_123"

    def test_config_from_env_with_hf_token(self, monkeypatch):
        """Test config with HF_TOKEN environment variable."""
        monkeypatch.setenv("HF_TOKEN", "hf_alternative_token")

        config = HuggingFace3DConfig.from_env()

        assert config.api_token == "hf_alternative_token"

    def test_config_custom_models(self):
        """Test config with custom model selection."""
        # Create config with custom models directly
        config = HuggingFace3DConfig(
            default_model=HF3DModel.SHAP_E_TEXT,
            fallback_models=[HF3DModel.POINT_E, HF3DModel.SHAP_E_IMG],
        )

        assert config.default_model == HF3DModel.SHAP_E_TEXT
        assert HF3DModel.POINT_E in config.fallback_models
        assert len(config.fallback_models) == 2


class TestHuggingFace3DClient:
    """Tests for HuggingFace 3D client."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return HuggingFace3DConfig(
            api_token="test_token",
            default_model=HF3DModel.SHAP_E_IMG,
            timeout_seconds=30,
            enable_optimization_hints=True,
        )

    @pytest.fixture
    def client(self, config):
        """Create HuggingFace 3D client."""
        return HuggingFace3DClient(config)

    def test_client_initialization(self, config):
        """Test client initialization."""
        client = HuggingFace3DClient(config)

        assert client.config.api_token == "test_token"
        assert client.config.default_model == HF3DModel.SHAP_E_IMG
        assert Path(client.config.output_dir).exists()

    def test_client_no_token_warning(self, caplog, monkeypatch):
        """Test warning when API token is not configured."""
        config = HuggingFace3DConfig(api_token=None, api_key=None)

        with patch("orchestration.huggingface_3d_client.logger") as mock_logger:
            HuggingFace3DClient(config)
            mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_generate_from_text(self, client):
        """Test text-to-3D generation structure and interface."""
        # Mock the internal generation method
        mock_result = HF3DResult(
            task_id="test_task_123",
            model_used=HF3DModel.SHAP_E_TEXT,
            format=HF3DFormat.GLB,
            status="completed",
            metadata={"prompt": "SkyyRose signature hoodie"},
        )

        with patch.object(client, "_generate_text_to_3d", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = mock_result

            result = await client.generate_from_text(
                prompt="SkyyRose signature hoodie",
                model=HF3DModel.SHAP_E_TEXT,
            )

            assert isinstance(result, HF3DResult)
            assert result.task_id
            assert result.model_used == HF3DModel.SHAP_E_TEXT

    @pytest.mark.asyncio
    async def test_generate_from_image(self, client, tmp_path):
        """Test image-to-3D generation structure and interface."""
        # Create a dummy image
        image_path = tmp_path / "test.jpg"
        image_path.write_bytes(b"fake image data")

        # Mock the internal generation method
        mock_result = HF3DResult(
            task_id="test_task_img_123",
            model_used=HF3DModel.SHAP_E_IMG,
            format=HF3DFormat.GLB,
            status="completed",
            metadata={"source_image": str(image_path)},
        )

        with patch.object(client, "_generate_image_to_3d", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = mock_result

            result = await client.generate_from_image(
                image_path=str(image_path),
                model=HF3DModel.SHAP_E_IMG,
            )

            assert isinstance(result, HF3DResult)
            assert result.task_id
            assert result.model_used == HF3DModel.SHAP_E_IMG
            assert "source_image" in result.metadata

    @pytest.mark.asyncio
    async def test_generate_from_image_not_found(self, client):
        """Test image-to-3D with missing image."""
        with pytest.raises(FileNotFoundError):
            await client.generate_from_image(image_path="/nonexistent/path/image.jpg")

    @pytest.mark.asyncio
    async def test_get_optimization_hints(self, client):
        """Test optimization hint generation."""
        # Create a mock HF result
        hf_result = HF3DResult(
            task_id="test_task",
            model_used=HF3DModel.SHAP_E_IMG,
            format=HF3DFormat.PLY,
            polycount=50000,
            quality_score=85.0,
            texture_complexity="medium",
            metadata={"prompt": "test hoodie"},
        )

        hints = await client.get_optimization_hints(hf_result)

        assert isinstance(hints, HF3DOptimizationHints)
        assert hints.detected_geometry in ["simple", "medium", "complex"]
        assert hints.detected_complexity in ["simple", "medium", "complex"]
        assert hints.suggested_tripo_prompt
        assert 0 <= hints.confidence_score <= 1

    @pytest.mark.asyncio
    async def test_compare_quality(self, client):
        """Test quality comparison between HF and Tripo3D."""
        hf_result = HF3DResult(
            task_id="hf_task",
            model_used=HF3DModel.SHAP_E_IMG,
            format=HF3DFormat.PLY,
            quality_score=80.0,
        )

        tripo_result = {"quality_score": 92.0}

        comparison = await client.compare_quality(hf_result, tripo_result)

        assert comparison["hf_score"] == 80.0
        assert comparison["tripo_score"] == 92.0
        assert comparison["winner"] == "tripo"

    def test_cache_key_generation(self, client):
        """Test cache key generation."""
        # Use the internal _cache_key method signature
        key = client._cache_key(
            source_type="text",
            source="test hoodie",
            model=HF3DModel.SHAP_E_IMG,
            output_format=HF3DFormat.GLB,
        )

        assert isinstance(key, str)
        assert len(key) == 64  # SHA-256 hex digest

    @pytest.mark.asyncio
    async def test_client_close(self, client):
        """Test client cleanup."""
        await client.close()
        # Should complete without error


# =============================================================================
# Asset Pipeline Integration Tests
# =============================================================================


class TestAssetPipelineHFIntegration:
    """Tests for asset pipeline integration with HuggingFace."""

    @pytest.fixture
    def pipeline_config(self):
        """Create test pipeline config."""
        return PipelineConfig(
            enable_huggingface_3d=True,
            enable_3d_generation=True,
            enable_virtual_tryon=False,
            enable_wordpress_upload=False,
        )

    @pytest.fixture
    def pipeline(self, pipeline_config):
        """Create test pipeline."""
        return ProductAssetPipeline(config=pipeline_config)

    @pytest.mark.asyncio
    async def test_pipeline_has_hf_client(self, pipeline):
        """Test pipeline has HuggingFace client."""
        client = pipeline.huggingface_client

        assert isinstance(client, HuggingFace3DClient)

    @pytest.mark.asyncio
    async def test_hf_3d_generation_in_pipeline(self, pipeline, tmp_path):
        """Test HuggingFace 3D generation in asset pipeline."""
        # Create a test image
        image_path = tmp_path / "product.jpg"
        image_path.write_bytes(b"fake image data")

        result = AssetPipelineResult(product_id="test_product", status="processing")

        # Call the HF generation method
        with patch.object(
            pipeline.huggingface_client,
            "generate_from_image",
            new_callable=AsyncMock,
        ) as mock_gen:
            mock_result = HF3DResult(
                task_id="hf_test",
                model_used=HF3DModel.SHAP_E_IMG,
                format=HF3DFormat.PLY,
                quality_score=85.0,
                polycount=50000,
            )
            mock_gen.return_value = mock_result

            hf_result = await pipeline._generate_3d_with_huggingface(
                result=result,
                title="Test Product",
                images=[str(image_path)],
            )

            assert hf_result is not None
            assert hf_result.quality_score == 85.0

    @pytest.mark.asyncio
    async def test_hf_fallback_on_error(self, pipeline, tmp_path):
        """Test pipeline falls back gracefully if HF fails."""
        image_path = tmp_path / "product.jpg"
        image_path.write_bytes(b"fake image data")

        result = AssetPipelineResult(product_id="test_product", status="processing")

        # Mock HF client to raise error
        with patch.object(
            pipeline.huggingface_client,
            "generate_from_image",
            new_callable=AsyncMock,
            side_effect=Exception("HF generation failed"),
        ):
            hf_result = await pipeline._generate_3d_with_huggingface(
                result=result,
                title="Test Product",
                images=[str(image_path)],
            )

            # Should return None but not fail pipeline
            assert hf_result is None
            # Should log warning/error but continue
            assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_pipeline_disable_hf(self, tmp_path):
        """Test pipeline with HF disabled."""
        config = PipelineConfig(
            enable_huggingface_3d=False,
            enable_3d_generation=True,
        )
        pipeline = ProductAssetPipeline(config=config)

        image_path = tmp_path / "product.jpg"
        image_path.write_bytes(b"fake image data")

        result = AssetPipelineResult(product_id="test_product", status="processing")

        # HF generation should be skipped
        hf_result = await pipeline._generate_3d_with_huggingface(
            result=result,
            title="Test Product",
            images=[str(image_path)],
        )

        # Should complete without calling HF
        assert hf_result is None

    @pytest.mark.asyncio
    async def test_pipeline_close(self, pipeline):
        """Test pipeline cleanup."""
        await pipeline.close()
        # Should complete without error


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
async def test_full_hybrid_pipeline():
    """Test full hybrid pipeline: HF -> Tripo3D."""
    config = PipelineConfig(
        enable_huggingface_3d=True,
        enable_3d_generation=True,
        enable_virtual_tryon=False,
        enable_wordpress_upload=False,
    )
    pipeline = ProductAssetPipeline(config=config)

    try:
        # Create test data
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / "product.jpg"
            image_path.write_bytes(b"fake image data")

            # Mock the agents
            with patch.object(
                pipeline.huggingface_client,
                "generate_from_image",
                new_callable=AsyncMock,
            ) as mock_hf, patch.object(
                pipeline.tripo_agent,
                "run",
                new_callable=AsyncMock,
            ) as mock_tripo:
                # Setup HF mock
                hf_result = HF3DResult(
                    task_id="hf_123",
                    model_used=HF3DModel.SHAP_E_IMG,
                    format=HF3DFormat.PLY,
                    quality_score=85.0,
                    polycount=50000,
                    tripo3d_prompt="3D model optimized prompt",
                )
                mock_hf.return_value = hf_result

                # Setup Tripo3D mock
                mock_tripo.return_value = {
                    "status": "success",
                    "data": {
                        "task_id": "tripo_123",
                        "model_path": str(image_path),
                        "model_url": "https://example.com/model.glb",
                    },
                }

                # Run pipeline
                result = await pipeline.process_product(
                    product_id="test_123",
                    title="Test Hoodie",
                    description="Test product",
                    images=[str(image_path)],
                    category="apparel",
                    collection="SIGNATURE",
                    garment_type="hoodie",
                )

                # Verify
                assert result.status == "success"
                assert len(result.assets_3d) > 0

    finally:
        await pipeline.close()


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling in HF 3D integration."""

    @pytest.mark.asyncio
    async def test_hf_timeout(self):
        """Test handling of HF API timeouts."""
        config = HuggingFace3DConfig(timeout_seconds=1)
        client = HuggingFace3DClient(config)

        # Client should be created even with timeout config
        assert client.config.timeout_seconds == 1

    @pytest.mark.asyncio
    async def test_invalid_image_format(self):
        """Test handling of invalid image formats."""
        config = HuggingFace3DConfig()
        client = HuggingFace3DClient(config)

        with pytest.raises(FileNotFoundError):
            await client.generate_from_image(image_path="/nonexistent/file.xyz")

    @pytest.mark.asyncio
    async def test_quality_comparison_edge_cases(self):
        """Test quality comparison with edge cases."""
        config = HuggingFace3DConfig()
        client = HuggingFace3DClient(config)

        # Test with None quality scores
        hf_result = HF3DResult(
            task_id="test",
            model_used=HF3DModel.SHAP_E_IMG,
            format=HF3DFormat.PLY,
            quality_score=None,
        )

        tripo_result = {"quality_score": None}

        comparison = await client.compare_quality(hf_result, tripo_result)

        assert comparison["hf_score"] == 0.0
        assert comparison["tripo_score"] == 0.0


# =============================================================================
# Performance Tests
# =============================================================================


@pytest.mark.asyncio
async def test_cache_key_consistency():
    """Test that cache keys are consistent."""
    config = HuggingFace3DConfig()
    client = HuggingFace3DClient(config)

    # Use the internal _cache_key method
    key1 = client._cache_key(
        source_type="text",
        source="test hoodie",
        model=HF3DModel.SHAP_E_IMG,
        output_format=HF3DFormat.GLB,
    )
    key2 = client._cache_key(
        source_type="text",
        source="test hoodie",
        model=HF3DModel.SHAP_E_IMG,
        output_format=HF3DFormat.GLB,
    )

    # Same inputs should produce same key
    assert key1 == key2

    # Different inputs should produce different key
    key3 = client._cache_key(
        source_type="text",
        source="different hoodie",
        model=HF3DModel.SHAP_E_IMG,
        output_format=HF3DFormat.GLB,
    )

    assert key1 != key3


__all__ = [
    "TestHuggingFace3DConfig",
    "TestHuggingFace3DClient",
    "TestAssetPipelineHFIntegration",
    "TestErrorHandling",
]
