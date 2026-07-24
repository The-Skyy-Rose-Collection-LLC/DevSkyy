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
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ai_3d.model_generator import (
    AI3DModelGenerator,
    GeneratedModel,
    GenerationConfig,
    ModelFidelityError,
    ModelGenerationError,
)
from imagery.model_fidelity import MINIMUM_FIDELITY_SCORE

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
        """Should validate fidelity when enabled, exercising the real validator."""
        model_path = sample_images[0].parent / "SKR-001.glb"
        model_path.touch()
        thumbnail_path = sample_images[0].parent / "SKR-001_thumb.jpg"
        thumbnail_path.touch()

        mock_result = GeneratedModel(
            product_sku="SKR-001",
            model_path=model_path,
            texture_path=None,
            thumbnail_path=thumbnail_path,
            fidelity_score=0.0,
            vertex_count=50000,
            face_count=25000,
            file_size_mb=1.5,
            source_images_used=4,
            generation_time_seconds=45.0,
            model_format="glb",
        )

        pytest.importorskip("trimesh")
        import numpy as np

        mock_mesh = Mock()
        mock_mesh.is_watertight = True
        mock_mesh.is_volume = True
        mock_mesh.euler_number = 2
        mock_mesh.volume = 400.0
        mock_mesh.area = 300.0
        mock_mesh.area_faces = np.ones(5000)
        mock_mesh.vertices = np.zeros((10000, 3))
        mock_mesh.faces = np.zeros((5000, 3))
        mock_mesh.edges_unique = np.zeros((20000, 2))
        mock_mesh.bounding_box = Mock()
        mock_mesh.bounding_box.bounds = np.array([[0.0, 0.0, 0.0], [10.0, 10.0, 10.0]])
        mock_mesh.bounding_box.volume = 800.0
        mock_mesh.visual = Mock()
        mock_mesh.visual.material = Mock()
        mock_mesh.visual.material.image = Mock(width=2048, height=2048)
        mock_mesh.visual.uv = np.array([[0.0, 0.0], [1.0, 1.0]] * 5000)

        with (
            patch.object(generator, "_get_hf_client", new_callable=AsyncMock) as mock_hf,
            patch.object(
                generator, "_generate_via_huggingface", new_callable=AsyncMock
            ) as mock_pipeline,
            patch("trimesh.load", return_value=mock_mesh),
        ):
            mock_hf.return_value = object()
            mock_pipeline.return_value = mock_result

            result = await generator.generate_model(
                product_sku="SKR-001",
                source_images=sample_images,
                validate_fidelity=True,
            )

            assert result.passed_fidelity is True
            assert result.fidelity_score >= MINIMUM_FIDELITY_SCORE
            assert result.validation_report["overall_score"] == result.fidelity_score

    @pytest.mark.asyncio
    async def test_configured_fidelity_threshold_reaches_validator(self, tmp_path, sample_images):
        """Regression lock (code-review HIGH): a non-default fidelity_threshold
        must be plumbed to ModelFidelityValidator.minimum_threshold (0-1 -> 0-100
        scale), not silently dropped so the 95.0 class default always wins."""
        generator = AI3DModelGenerator(
            output_dir=tmp_path / "out",
            config=GenerationConfig(fidelity_threshold=0.50),
        )
        model_path = tmp_path / "m.glb"
        model_path.touch()
        thumbnail_path = tmp_path / "m_thumb.jpg"
        thumbnail_path.touch()
        result = GeneratedModel(
            product_sku="SKR-001",
            model_path=model_path,
            texture_path=None,
            thumbnail_path=thumbnail_path,
            fidelity_score=0.0,
            vertex_count=1,
            face_count=1,
            file_size_mb=0.1,
            source_images_used=1,
            generation_time_seconds=1.0,
            model_format="glb",
        )

        captured = {}

        class _FakeReport:
            overall_score = 72.0
            passed = True

            def model_dump(self):
                return {"overall_score": 72.0}

        class _FakeValidator:
            # default 95.0 mirrors the real class default — if the callsite ever
            # drops the kwarg again, captured['minimum_threshold'] becomes 95.0
            # and the assertion below fails.
            def __init__(self, *, minimum_threshold=95.0, reference_image_path=None):
                captured["minimum_threshold"] = minimum_threshold

            async def validate(self, model_path):
                return _FakeReport()

        with patch("imagery.model_fidelity.ModelFidelityValidator", _FakeValidator):
            out = await generator._validate_model_fidelity(result, sample_images)

        assert captured["minimum_threshold"] == pytest.approx(50.0)  # 0.50 * 100, not 95.0
        assert out.passed_fidelity is True
        assert out.fidelity_score == 72.0

    @pytest.mark.asyncio
    async def test_generate_model_fidelity_low_score_does_not_raise(self, generator, sample_images):
        """A low-fidelity mesh should be reported, not raised, by the real validator."""
        model_path = sample_images[0].parent / "SKR-001.glb"
        model_path.touch()
        thumbnail_path = sample_images[0].parent / "SKR-001_thumb.jpg"
        thumbnail_path.touch()

        mock_result = GeneratedModel(
            product_sku="SKR-001",
            model_path=model_path,
            texture_path=None,
            thumbnail_path=thumbnail_path,
            fidelity_score=0.0,
            vertex_count=500,
            face_count=100,
            file_size_mb=0.1,
            source_images_used=4,
            generation_time_seconds=45.0,
            model_format="glb",
        )

        pytest.importorskip("trimesh")
        mock_mesh = Mock()
        mock_mesh.is_watertight = False
        mock_mesh.is_volume = False
        mock_mesh.euler_number = 0
        mock_mesh.area = 1.0
        mock_mesh.bounds = [[0, 0, 0], [1, 1, 1]]
        mock_mesh.vertices = Mock()
        mock_mesh.vertices.__len__ = Mock(return_value=10)
        mock_mesh.faces = Mock()
        mock_mesh.faces.__len__ = Mock(return_value=5)
        mock_mesh.visual = None

        with (
            patch.object(generator, "_get_hf_client", new_callable=AsyncMock) as mock_hf_client,
            patch.object(
                generator, "_generate_via_huggingface", new_callable=AsyncMock
            ) as mock_pipeline,
            patch("trimesh.load", return_value=mock_mesh),
        ):
            mock_hf_client.return_value = object()
            mock_pipeline.return_value = mock_result

            result = await generator.generate_model(
                product_sku="SKR-001",
                source_images=sample_images,
                validate_fidelity=True,
            )

            # Low fidelity is reported on the result, not raised — generate_model
            # never enforces the threshold itself.
            assert result.passed_fidelity is False
            assert result.fidelity_score < MINIMUM_FIDELITY_SCORE

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
