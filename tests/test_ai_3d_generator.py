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
        texture_path = tmp_path / "texture.png"
        texture_path.touch()

        model = GeneratedModel(
            product_sku="SKR-001",
            model_path=model_path,
            texture_path=texture_path,
            thumbnail_path=thumbnail_path,
            fidelity_score=0.95,
            vertex_count=50000,
            face_count=25000,
            file_size_mb=1.5,
            source_images_used=3,
            generation_time_seconds=30.5,
            model_format="glb",
            passed_fidelity=True,
            validation_report={"source": "huggingface"},
        )

        assert model.product_sku == "SKR-001"
        assert model.model_format == "glb"
        assert model.vertex_count == 50000
        assert model.fidelity_score == 0.95

    def test_generated_model_optional_fields(self, tmp_path):
        """Should handle optional texture_path field."""
        model_path = tmp_path / "test.glb"
        model_path.touch()
        thumbnail_path = tmp_path / "thumb.jpg"
        thumbnail_path.touch()

        model = GeneratedModel(
            product_sku="SKR-002",
            model_path=model_path,
            texture_path=None,
            thumbnail_path=thumbnail_path,
            fidelity_score=0.85,
            vertex_count=25000,
            face_count=12000,
            file_size_mb=0.5,
            source_images_used=1,
            generation_time_seconds=15.0,
        )

        assert model.texture_path is None
        assert model.passed_fidelity is False
        assert model.validation_report == {}


# =============================================================================
# AI3DModelGenerator Tests
# =============================================================================


class TestAI3DModelGenerator:
    """Tests for AI3DModelGenerator class."""

    @pytest.fixture
    def generator(self, tmp_path):
        """Create generator instance with temp directory."""
        output_dir = tmp_path / "generator_output"
        return AI3DModelGenerator(output_dir=output_dir)

    @pytest.fixture
    def sample_images(self, tmp_path):
        """Create sample image files (minimum 4 required)."""
        images = []
        for i in range(4):
            img_path = tmp_path / f"image_{i}.jpg"
            img_path.write_bytes(b"fake image data " + bytes([i]))
            images.append(img_path)
        return images

    def test_generator_initialization(self, generator):
        """Should initialize with defaults."""
        assert generator.output_dir.exists()
        assert generator.config is not None

    def test_generator_custom_output_dir(self, tmp_path):
        """Should use custom output directory."""
        custom_dir = tmp_path / "custom_output"
        generator = AI3DModelGenerator(output_dir=custom_dir)

        assert generator.output_dir == custom_dir
        assert custom_dir.exists()

    @pytest.mark.asyncio
    async def test_generate_model_missing_images(self, generator):
        """Should raise error for missing source images."""
        with pytest.raises(ModelGenerationError, match="Minimum.*source images required"):
            await generator.generate_model(
                product_sku="SKR-001",
                source_images=[],
            )

    @pytest.mark.asyncio
    async def test_generate_model_invalid_image_path(self, generator, sample_images):
        """Should raise error for non-existent image."""
        # Add a non-existent image to otherwise valid list
        images = sample_images[:3] + [Path("/nonexistent/image.jpg")]
        with pytest.raises(ModelGenerationError, match="Source image not found"):
            await generator.generate_model(
                product_sku="SKR-001",
                source_images=images,
            )

    @pytest.mark.asyncio
    async def test_generate_model_structure(self, generator, sample_images):
        """Should return GeneratedModel with correct structure."""
        # Create mock paths
        model_path = sample_images[0].parent / "SKR-001.glb"
        model_path.touch()
        thumbnail_path = sample_images[0].parent / "SKR-001_thumb.jpg"
        thumbnail_path.touch()

        mock_result = GeneratedModel(
            product_sku="SKR-001",
            model_path=model_path,
            texture_path=None,
            thumbnail_path=thumbnail_path,
            fidelity_score=0.92,
            vertex_count=45000,
            face_count=22000,
            file_size_mb=1.5,
            source_images_used=4,
            generation_time_seconds=45.0,
            model_format="glb",
        )

        with (
            patch.object(generator, "_get_hf_client", new_callable=AsyncMock) as mock_hf,
            patch.object(
                generator, "_generate_via_huggingface", new_callable=AsyncMock
            ) as mock_pipeline,
        ):
            mock_hf.return_value = object()
            mock_pipeline.return_value = mock_result

            result = await generator.generate_model(
                product_sku="SKR-001",
                source_images=sample_images,
                validate_fidelity=False,
            )

            assert isinstance(result, GeneratedModel)
            assert result.product_sku == "SKR-001"
            assert result.model_format == "glb"

    @pytest.mark.asyncio
    async def test_generate_model_quality_levels(self, generator, sample_images):
        """Should handle different quality levels."""
        model_path = sample_images[0].parent / "SKR-001.glb"
        model_path.touch()
        thumbnail_path = sample_images[0].parent / "SKR-001_thumb.jpg"
        thumbnail_path.touch()

        mock_result = GeneratedModel(
            product_sku="SKR-001",
            model_path=model_path,
            texture_path=None,
            thumbnail_path=thumbnail_path,
            fidelity_score=0.90,
            vertex_count=25000,
            face_count=12000,
            file_size_mb=0.5,
            source_images_used=4,
            generation_time_seconds=20.0,
            model_format="glb",
        )

        with (
            patch.object(generator, "_get_hf_client", new_callable=AsyncMock) as mock_hf,
            patch.object(
                generator, "_generate_via_huggingface", new_callable=AsyncMock
            ) as mock_pipeline,
        ):
            mock_hf.return_value = object()
            mock_pipeline.return_value = mock_result

            await generator.generate_model(
                product_sku="SKR-001",
                source_images=sample_images,
                quality_level="draft",
                validate_fidelity=False,
            )

            # Verify pipeline was called
            call_args = mock_pipeline.call_args
            assert call_args is not None

    @pytest.mark.asyncio
    async def test_generate_model_with_fidelity_validation(self, generator, sample_images):
        """Should validate fidelity when enabled."""
        model_path = sample_images[0].parent / "SKR-001.glb"
        model_path.touch()
        thumbnail_path = sample_images[0].parent / "SKR-001_thumb.jpg"
        thumbnail_path.touch()

        mock_result = GeneratedModel(
            product_sku="SKR-001",
            model_path=model_path,
            texture_path=None,
            thumbnail_path=thumbnail_path,
            fidelity_score=0.95,
            vertex_count=50000,
            face_count=25000,
            file_size_mb=1.5,
            source_images_used=4,
            generation_time_seconds=45.0,
            model_format="glb",
            passed_fidelity=True,
        )

        with (
            patch.object(generator, "_get_hf_client", new_callable=AsyncMock) as mock_hf,
            patch.object(
                generator, "_generate_via_huggingface", new_callable=AsyncMock
            ) as mock_pipeline,
            patch.object(
                generator, "_validate_model_fidelity", new_callable=AsyncMock
            ) as mock_validate,
        ):
            mock_hf.return_value = object()
            mock_pipeline.return_value = mock_result
            mock_validate.return_value = mock_result

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
        model_path = sample_images[0].parent / "SKR-001.glb"
        model_path.touch()
        thumbnail_path = sample_images[0].parent / "SKR-001_thumb.jpg"
        thumbnail_path.touch()

        mock_result = GeneratedModel(
            product_sku="SKR-001",
            model_path=model_path,
            texture_path=None,
            thumbnail_path=thumbnail_path,
            fidelity_score=0.80,
            vertex_count=50000,
            face_count=25000,
            file_size_mb=1.5,
            source_images_used=4,
            generation_time_seconds=45.0,
            model_format="glb",
            passed_fidelity=False,
        )

        with (
            patch.object(generator, "_get_hf_client", new_callable=AsyncMock) as mock_hf_client,
            patch.object(
                generator, "_generate_via_huggingface", new_callable=AsyncMock
            ) as mock_pipeline,
            patch.object(
                generator, "_validate_model_fidelity", new_callable=AsyncMock
            ) as mock_validate,
        ):
            mock_hf_client.return_value = object()
            mock_pipeline.return_value = mock_result
            mock_validate.side_effect = ModelFidelityError(
                message="Fidelity score 0.80 below threshold 0.95",
                score=0.80,
                threshold=0.95,
            )

            # ModelFidelityError is wrapped in ModelGenerationError by the generator
            raised = False
            try:
                await generator.generate_model(
                    product_sku="SKR-001",
                    source_images=sample_images,
                    validate_fidelity=True,
                )
            except ModelGenerationError as e:
                raised = True
                # The original ModelFidelityError is the cause
                assert e.__cause__ is not None
                assert isinstance(e.__cause__, ModelFidelityError)
                assert e.__cause__.score == 0.80
                assert e.__cause__.threshold == 0.95

            assert (
                raised
            ), "ModelGenerationError (wrapping ModelFidelityError) should have been raised"

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
        error = ModelGenerationError(
            message="Generation failed",
            stage="processing",
        )

        assert str(error) == "Generation failed"
        assert isinstance(error, Exception)
        assert error.stage == "processing"

    def test_model_fidelity_error(self):
        """Should create ModelFidelityError."""
        error = ModelFidelityError(
            message="Fidelity too low",
            score=0.80,
            threshold=0.95,
        )

        assert str(error) == "Fidelity too low"
        assert isinstance(error, Exception)
        assert error.score == 0.80
        assert error.threshold == 0.95

    @pytest.mark.asyncio
    async def test_generator_handles_api_error(self, tmp_path):
        """Should handle API errors gracefully."""
        output_dir = tmp_path / "output"
        generator = AI3DModelGenerator(output_dir=output_dir)

        # Create a test image
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"fake image data")

        with (
            patch.object(
                generator,
                "_generate_via_huggingface",
                new_callable=AsyncMock,
                side_effect=Exception("HuggingFace API error"),
            ),
            pytest.raises((ModelGenerationError, Exception)),
        ):
            await generator.generate_model(
                product_sku="SKR-001",
                source_images=[test_image],
            )


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_generation_pipeline():
    """Test full generation pipeline (mocked)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "output"
        generator = AI3DModelGenerator(output_dir=output_dir)

        try:
            # Create minimum 4 test images (required by config)
            source_images = []
            for i in range(4):
                image_path = Path(tmpdir) / f"product_{i}.jpg"
                image_path.write_bytes(b"fake image data " + bytes([i]))
                source_images.append(image_path)

            # Create mock paths
            model_path = Path(tmpdir) / "TEST-001.glb"
            model_path.touch()
            thumbnail_path = Path(tmpdir) / "TEST-001_thumb.jpg"
            thumbnail_path.touch()

            # Mock the entire pipeline with correct GeneratedModel fields
            mock_result = GeneratedModel(
                product_sku="TEST-001",
                model_path=model_path,
                texture_path=None,
                thumbnail_path=thumbnail_path,
                fidelity_score=0.95,
                vertex_count=50000,
                face_count=25000,
                file_size_mb=1.5,
                source_images_used=4,
                generation_time_seconds=30.0,
                model_format="glb",
                passed_fidelity=True,
            )

            with (
                patch.object(generator, "_get_hf_client", new_callable=AsyncMock) as mock_hf,
                patch.object(
                    generator, "_generate_via_huggingface", new_callable=AsyncMock
                ) as mock_pipeline,
            ):
                mock_hf.return_value = object()
                mock_pipeline.return_value = mock_result

                result = await generator.generate_model(
                    product_sku="TEST-001",
                    source_images=source_images,
                    validate_fidelity=False,
                )

                assert result.product_sku == "TEST-001"
                assert result.model_format == "glb"
                assert result.vertex_count == 50000

        finally:
            await generator.close()


__all__ = [
    "TestGenerationConfig",
    "TestGeneratedModel",
    "TestAI3DModelGenerator",
    "TestErrorHandling",
]
