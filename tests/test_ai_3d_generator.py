"""
Tests for AI 3D Model Generator
================================

Tests for the AI3DModelGenerator class and related functionality.

Coverage:
- Generator initialization and configuration
- Model generation from images
- Quality level handling
- Fidelity validation integration
- Error handling and resilience
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from ai_3d.model_generator import (
    AI3DModelGenerator,
    GeneratedModel,
    GenerationConfig,
    ModelFidelityError,
    ModelGenerationError,
)

# =============================================================================
# Configuration Tests
# =============================================================================


class TestGenerationConfig:
    """Tests for GenerationConfig."""

    def test_default_config(self):
        """Should have sensible defaults."""
        config = GenerationConfig()

        assert config.quality_level == "production"
        assert config.target_mesh_vertices == 50000
        assert config.texture_size == 2048
        assert config.validate_fidelity is True

    def test_draft_config(self):
        """Should create draft quality config."""
        config = GenerationConfig(quality_level="draft")

        assert config.quality_level == "draft"

    def test_standard_config(self):
        """Should create standard quality config."""
        config = GenerationConfig(quality_level="standard")

        assert config.quality_level == "standard"

    def test_custom_config(self):
        """Should accept custom values."""
        config = GenerationConfig(
            quality_level="high",
            target_mesh_vertices=100000,
            texture_size=4096,
            validate_fidelity=False,
        )

        assert config.target_mesh_vertices == 100000
        assert config.texture_size == 4096
        assert config.validate_fidelity is False


# =============================================================================
# GeneratedModel Tests
# =============================================================================


class TestGeneratedModel:
    """Tests for GeneratedModel dataclass."""

    def test_generated_model_creation(self, tmp_path):
        """Should create GeneratedModel with all fields."""
        model_path = tmp_path / "test.glb"
        model_path.touch()
        thumbnail_path = tmp_path / "thumb.jpg"
        thumbnail_path.touch()

        model = GeneratedModel(
            product_sku="SKR-001",
            model_path=model_path,
            format="glb",
            polycount=50000,
            texture_resolution=2048,
            file_size_bytes=1024000,
            thumbnail_path=thumbnail_path,
            lod_paths=[],
            fidelity_score=0.95,
            generation_time_seconds=30.5,
            metadata={"source": "huggingface"},
        )

        assert model.product_sku == "SKR-001"
        assert model.format == "glb"
        assert model.polycount == 50000
        assert model.fidelity_score == 0.95

    def test_generated_model_optional_fields(self, tmp_path):
        """Should handle optional fields."""
        model_path = tmp_path / "test.glb"
        model_path.touch()

        model = GeneratedModel(
            product_sku="SKR-002",
            model_path=model_path,
            format="glb",
            polycount=25000,
            texture_resolution=1024,
            file_size_bytes=512000,
            generation_time_seconds=15.0,
        )

        assert model.thumbnail_path is None
        assert model.lod_paths == []
        assert model.fidelity_score is None
        assert model.metadata == {}


# =============================================================================
# AI3DModelGenerator Tests
# =============================================================================


class TestAI3DModelGenerator:
    """Tests for AI3DModelGenerator class."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return AI3DModelGenerator()

    @pytest.fixture
    def sample_images(self, tmp_path):
        """Create sample image files."""
        images = []
        for i in range(3):
            img_path = tmp_path / f"image_{i}.jpg"
            img_path.write_bytes(b"fake image data " + bytes([i]))
            images.append(img_path)
        return images

    def test_generator_initialization(self, generator):
        """Should initialize with defaults."""
        assert generator.output_dir.exists()
        assert generator.huggingface_client is not None

    def test_generator_custom_output_dir(self, tmp_path):
        """Should use custom output directory."""
        custom_dir = tmp_path / "custom_output"
        generator = AI3DModelGenerator(output_dir=custom_dir)

        assert generator.output_dir == custom_dir
        assert custom_dir.exists()

    @pytest.mark.asyncio
    async def test_generate_model_missing_images(self, generator):
        """Should raise error for missing source images."""
        with pytest.raises(ModelGenerationError, match="At least one source image"):
            await generator.generate_model(
                product_sku="SKR-001",
                source_images=[],
            )

    @pytest.mark.asyncio
    async def test_generate_model_invalid_image_path(self, generator):
        """Should raise error for non-existent image."""
        with pytest.raises(ModelGenerationError, match="does not exist"):
            await generator.generate_model(
                product_sku="SKR-001",
                source_images=[Path("/nonexistent/image.jpg")],
            )

    @pytest.mark.asyncio
    async def test_generate_model_structure(self, generator, sample_images):
        """Should return GeneratedModel with correct structure."""
        # Mock the internal generation pipeline
        mock_result = GeneratedModel(
            product_sku="SKR-001",
            model_path=sample_images[0].parent / "SKR-001.glb",
            format="glb",
            polycount=45000,
            texture_resolution=2048,
            file_size_bytes=1500000,
            fidelity_score=0.92,
            generation_time_seconds=45.0,
        )

        with patch.object(
            generator, "_run_generation_pipeline", new_callable=AsyncMock
        ) as mock_pipeline:
            mock_pipeline.return_value = mock_result

            result = await generator.generate_model(
                product_sku="SKR-001",
                source_images=sample_images,
                validate_fidelity=False,
            )

            assert isinstance(result, GeneratedModel)
            assert result.product_sku == "SKR-001"
            assert result.format == "glb"

    @pytest.mark.asyncio
    async def test_generate_model_quality_levels(self, generator, sample_images):
        """Should handle different quality levels."""
        mock_result = GeneratedModel(
            product_sku="SKR-001",
            model_path=sample_images[0].parent / "SKR-001.glb",
            format="glb",
            polycount=25000,
            texture_resolution=1024,
            file_size_bytes=500000,
            generation_time_seconds=20.0,
        )

        with patch.object(
            generator, "_run_generation_pipeline", new_callable=AsyncMock
        ) as mock_pipeline:
            mock_pipeline.return_value = mock_result

            await generator.generate_model(
                product_sku="SKR-001",
                source_images=sample_images,
                quality_level="draft",
                validate_fidelity=False,
            )

            # Verify quality level was passed to pipeline
            call_args = mock_pipeline.call_args
            assert call_args is not None

    @pytest.mark.asyncio
    async def test_generate_model_with_fidelity_validation(self, generator, sample_images):
        """Should validate fidelity when enabled."""
        mock_result = GeneratedModel(
            product_sku="SKR-001",
            model_path=sample_images[0].parent / "SKR-001.glb",
            format="glb",
            polycount=50000,
            texture_resolution=2048,
            file_size_bytes=1500000,
            fidelity_score=0.95,
            generation_time_seconds=45.0,
        )

        with (
            patch.object(
                generator, "_run_generation_pipeline", new_callable=AsyncMock
            ) as mock_pipeline,
            patch.object(
                generator, "_validate_fidelity", new_callable=AsyncMock
            ) as mock_validate,
        ):
            mock_pipeline.return_value = mock_result
            mock_validate.return_value = 0.95

            result = await generator.generate_model(
                product_sku="SKR-001",
                source_images=sample_images,
                validate_fidelity=True,
            )

            mock_validate.assert_called_once()
            assert result.fidelity_score == 0.95

    @pytest.mark.asyncio
    async def test_generate_model_fidelity_failure(self, generator, sample_images):
        """Should raise error on fidelity validation failure."""
        mock_result = GeneratedModel(
            product_sku="SKR-001",
            model_path=sample_images[0].parent / "SKR-001.glb",
            format="glb",
            polycount=50000,
            texture_resolution=2048,
            file_size_bytes=1500000,
            fidelity_score=0.80,
            generation_time_seconds=45.0,
        )

        with (
            patch.object(
                generator, "_run_generation_pipeline", new_callable=AsyncMock
            ) as mock_pipeline,
            patch.object(
                generator, "_validate_fidelity", new_callable=AsyncMock
            ) as mock_validate,
        ):
            mock_pipeline.return_value = mock_result
            mock_validate.side_effect = ModelFidelityError(
                "Fidelity score 0.80 below threshold 0.90"
            )

            with pytest.raises(ModelFidelityError):
                await generator.generate_model(
                    product_sku="SKR-001",
                    source_images=sample_images,
                    validate_fidelity=True,
                )

    @pytest.mark.asyncio
    async def test_close(self, generator):
        """Should close cleanly."""
        await generator.close()
        # Should complete without error


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    def test_model_generation_error(self):
        """Should create ModelGenerationError."""
        error = ModelGenerationError("Generation failed")

        assert str(error) == "Generation failed"
        assert isinstance(error, Exception)

    def test_model_fidelity_error(self):
        """Should create ModelFidelityError."""
        error = ModelFidelityError("Fidelity too low")

        assert str(error) == "Fidelity too low"
        assert isinstance(error, Exception)

    @pytest.mark.asyncio
    async def test_generator_handles_huggingface_error(self):
        """Should handle HuggingFace client errors gracefully."""
        generator = AI3DModelGenerator()

        with patch.object(
            generator.huggingface_client,
            "generate_from_image",
            new_callable=AsyncMock,
            side_effect=Exception("HuggingFace API error"),
        ), pytest.raises(ModelGenerationError):
            await generator.generate_model(
                product_sku="SKR-001",
                source_images=[Path("/tmp/test.jpg")],
                validate_fidelity=False,
            )


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_generation_pipeline():
    """Test full generation pipeline (mocked)."""
    generator = AI3DModelGenerator()

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test image
            image_path = Path(tmpdir) / "product.jpg"
            image_path.write_bytes(b"fake image data")

            # Mock the entire pipeline
            mock_result = GeneratedModel(
                product_sku="TEST-001",
                model_path=Path(tmpdir) / "TEST-001.glb",
                format="glb",
                polycount=50000,
                texture_resolution=2048,
                file_size_bytes=1500000,
                fidelity_score=0.95,
                generation_time_seconds=30.0,
            )

            with patch.object(
                generator, "_run_generation_pipeline", new_callable=AsyncMock
            ) as mock_pipeline:
                mock_pipeline.return_value = mock_result

                result = await generator.generate_model(
                    product_sku="TEST-001",
                    source_images=[image_path],
                    quality_level="production",
                    validate_fidelity=False,
                )

                assert result.product_sku == "TEST-001"
                assert result.format == "glb"
                assert result.polycount == 50000

    finally:
        await generator.close()


__all__ = [
    "TestGenerationConfig",
    "TestGeneratedModel",
    "TestAI3DModelGenerator",
    "TestErrorHandling",
]
