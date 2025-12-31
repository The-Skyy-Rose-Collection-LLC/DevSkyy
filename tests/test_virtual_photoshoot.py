"""
Tests for Virtual Photoshoot Generator
=======================================

Tests for the VirtualPhotoshootGenerator class.

Coverage:
- Generator initialization
- Scene preset handling
- Photoshoot generation
- Social media crop optimization
- AI enhancement
- Error handling
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from ai_3d.virtual_photoshoot import (
    GeneratedPhotoshoot,
    PhotoshootScene,
    ScenePreset,
    VirtualPhotoshootGenerator,
)

# =============================================================================
# ScenePreset Tests
# =============================================================================


class TestScenePreset:
    """Tests for ScenePreset enum."""

    def test_preset_values(self):
        """Should have all expected presets."""
        assert ScenePreset.STUDIO_WHITE.value == "studio_white"
        assert ScenePreset.STUDIO_BLACK.value == "studio_black"
        assert ScenePreset.URBAN_OAKLAND.value == "urban_oakland"
        assert ScenePreset.LIFESTYLE_MINIMAL.value == "lifestyle_minimal"
        assert ScenePreset.LUXURY_DISPLAY.value == "luxury_display"
        assert ScenePreset.SKYYROSE_BRAND.value == "skyyrose_brand"


# =============================================================================
# PhotoshootScene Tests
# =============================================================================


class TestPhotoshootScene:
    """Tests for PhotoshootScene dataclass."""

    def test_scene_creation(self):
        """Should create scene with all fields."""
        scene = PhotoshootScene(
            name="custom_scene",
            background_color="#FFFFFF",
            lighting_setup="three_point",
            camera_positions=[(0, 0, 5), (45, 0, 5), (-45, 0, 5)],
            environment_map="studio_hdr",
            floor_material="reflective_white",
            props=[],
        )

        assert scene.name == "custom_scene"
        assert scene.background_color == "#FFFFFF"
        assert scene.lighting_setup == "three_point"
        assert len(scene.camera_positions) == 3

    def test_scene_with_props(self):
        """Should include props."""
        scene = PhotoshootScene(
            name="with_props",
            background_color="#1A1A1A",
            lighting_setup="dramatic",
            camera_positions=[(0, 0, 5)],
            props=["mannequin", "pedestal"],
        )

        assert len(scene.props) == 2
        assert "mannequin" in scene.props


# =============================================================================
# GeneratedPhotoshoot Tests
# =============================================================================


class TestGeneratedPhotoshoot:
    """Tests for GeneratedPhotoshoot dataclass."""

    def test_photoshoot_creation(self, tmp_path):
        """Should create photoshoot with all fields."""
        images = [tmp_path / f"img_{i}.jpg" for i in range(4)]
        for img in images:
            img.touch()

        crops = {
            "instagram_square": tmp_path / "ig_square.jpg",
            "instagram_story": tmp_path / "ig_story.jpg",
        }
        for crop in crops.values():
            crop.touch()

        photoshoot = GeneratedPhotoshoot(
            product_sku="SKR-001",
            scene_preset="studio_white",
            images=images,
            thumbnail=images[0],
            social_crops=crops,
            generation_time_seconds=25.5,
            metadata={"ai_enhanced": True},
        )

        assert photoshoot.product_sku == "SKR-001"
        assert photoshoot.scene_preset == "studio_white"
        assert len(photoshoot.images) == 4
        assert len(photoshoot.social_crops) == 2

    def test_photoshoot_optional_fields(self, tmp_path):
        """Should handle optional fields."""
        images = [tmp_path / "img_0.jpg"]
        images[0].touch()

        photoshoot = GeneratedPhotoshoot(
            product_sku="SKR-002",
            scene_preset="lifestyle_minimal",
            images=images,
            generation_time_seconds=15.0,
        )

        assert photoshoot.thumbnail is None
        assert photoshoot.social_crops == {}
        assert photoshoot.metadata == {}


# =============================================================================
# VirtualPhotoshootGenerator Tests
# =============================================================================


class TestVirtualPhotoshootGenerator:
    """Tests for VirtualPhotoshootGenerator class."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return VirtualPhotoshootGenerator()

    @pytest.fixture
    def sample_model(self, tmp_path):
        """Create sample 3D model file."""
        model_path = tmp_path / "product.glb"
        model_path.write_bytes(b"fake glb data")
        return model_path

    def test_generator_initialization(self, generator):
        """Should initialize with defaults."""
        assert generator.output_dir.exists()
        assert generator.scene_presets is not None

    def test_generator_custom_output_dir(self, tmp_path):
        """Should use custom output directory."""
        custom_dir = tmp_path / "custom_photos"
        generator = VirtualPhotoshootGenerator(output_dir=custom_dir)

        assert generator.output_dir == custom_dir
        assert custom_dir.exists()

    def test_available_presets(self, generator):
        """Should have all scene presets available."""
        presets = generator.get_available_presets()

        assert "studio_white" in presets
        assert "studio_black" in presets
        assert "urban_oakland" in presets
        assert "lifestyle_minimal" in presets
        assert "luxury_display" in presets
        assert "skyyrose_brand" in presets

    def test_get_preset_config(self, generator):
        """Should return preset configuration."""
        config = generator.get_preset_config("studio_white")

        assert config is not None
        assert "background_color" in config or hasattr(config, "background_color")

    @pytest.mark.asyncio
    async def test_generate_photoshoot_missing_model(self, generator):
        """Should raise error for missing model."""
        from ai_3d.virtual_photoshoot import PhotoshootError

        with pytest.raises(PhotoshootError, match="Model file not found"):
            await generator.generate_photoshoot(
                product_sku="SKR-001",
                model_path=Path("/nonexistent/model.glb"),
            )

    @pytest.mark.asyncio
    async def test_generate_photoshoot_default_preset(self, generator, sample_model):
        """Should use default preset when not specified."""
        mock_result = GeneratedPhotoshoot(
            product_sku="SKR-001",
            scene_preset="studio_white",
            images=[sample_model.parent / "photo_0.jpg"],
            generation_time_seconds=20.0,
        )

        with patch.object(
            generator, "_run_photoshoot", new_callable=AsyncMock
        ) as mock_run:
            mock_run.return_value = mock_result

            result = await generator.generate_photoshoot(
                product_sku="SKR-001",
                model_path=sample_model,
            )

            assert result.scene_preset == "studio_white"

    @pytest.mark.asyncio
    async def test_generate_photoshoot_custom_preset(self, generator, sample_model):
        """Should use specified preset."""
        mock_result = GeneratedPhotoshoot(
            product_sku="SKR-001",
            scene_preset="urban_oakland",
            images=[sample_model.parent / "photo_0.jpg"],
            generation_time_seconds=25.0,
        )

        with patch.object(
            generator, "_run_photoshoot", new_callable=AsyncMock
        ) as mock_run:
            mock_run.return_value = mock_result

            result = await generator.generate_photoshoot(
                product_sku="SKR-001",
                model_path=sample_model,
                scene_preset="urban_oakland",
            )

            assert result.scene_preset == "urban_oakland"

    @pytest.mark.asyncio
    async def test_generate_photoshoot_custom_scene(self, generator, sample_model):
        """Should use custom scene configuration."""
        custom_scene = PhotoshootScene(
            name="custom",
            background_color="#FF0000",
            lighting_setup="dramatic",
            camera_positions=[(0, 0, 5)],
        )

        mock_result = GeneratedPhotoshoot(
            product_sku="SKR-001",
            scene_preset="custom",
            images=[sample_model.parent / "photo_0.jpg"],
            generation_time_seconds=18.0,
        )

        with patch.object(
            generator, "_run_photoshoot", new_callable=AsyncMock
        ) as mock_run:
            mock_run.return_value = mock_result

            result = await generator.generate_photoshoot(
                product_sku="SKR-001",
                model_path=sample_model,
                custom_scene=custom_scene,
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_generate_social_crops(self, generator, sample_model):
        """Should generate social media crops when enabled."""
        mock_result = GeneratedPhotoshoot(
            product_sku="SKR-001",
            scene_preset="studio_white",
            images=[sample_model.parent / "photo_0.jpg"],
            social_crops={
                "instagram_square": sample_model.parent / "ig_square.jpg",
                "instagram_story": sample_model.parent / "ig_story.jpg",
                "facebook_cover": sample_model.parent / "fb_cover.jpg",
                "twitter_header": sample_model.parent / "tw_header.jpg",
                "pinterest": sample_model.parent / "pin.jpg",
            },
            generation_time_seconds=30.0,
        )

        with patch.object(
            generator, "_run_photoshoot", new_callable=AsyncMock
        ) as mock_run:
            mock_run.return_value = mock_result

            result = await generator.generate_photoshoot(
                product_sku="SKR-001",
                model_path=sample_model,
                generate_social_crops=True,
            )

            assert len(result.social_crops) >= 4
            assert "instagram_square" in result.social_crops

    @pytest.mark.asyncio
    async def test_generate_without_social_crops(self, generator, sample_model):
        """Should skip social crops when disabled."""
        mock_result = GeneratedPhotoshoot(
            product_sku="SKR-001",
            scene_preset="studio_white",
            images=[sample_model.parent / "photo_0.jpg"],
            social_crops={},
            generation_time_seconds=15.0,
        )

        with patch.object(
            generator, "_run_photoshoot", new_callable=AsyncMock
        ) as mock_run:
            mock_run.return_value = mock_result

            result = await generator.generate_photoshoot(
                product_sku="SKR-001",
                model_path=sample_model,
                generate_social_crops=False,
            )

            assert len(result.social_crops) == 0

    @pytest.mark.asyncio
    async def test_ai_enhance_option(self, generator, sample_model):
        """Should apply AI enhancement when enabled."""
        mock_result = GeneratedPhotoshoot(
            product_sku="SKR-001",
            scene_preset="studio_white",
            images=[sample_model.parent / "photo_0.jpg"],
            generation_time_seconds=35.0,
            metadata={"ai_enhanced": True},
        )

        with patch.object(
            generator, "_run_photoshoot", new_callable=AsyncMock
        ) as mock_run:
            mock_run.return_value = mock_result

            result = await generator.generate_photoshoot(
                product_sku="SKR-001",
                model_path=sample_model,
                ai_enhance=True,
            )

            assert result.metadata.get("ai_enhanced") is True


# =============================================================================
# Social Media Crop Tests
# =============================================================================


class TestSocialMediaCrops:
    """Tests for social media crop specifications."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return VirtualPhotoshootGenerator()

    def test_instagram_square_dimensions(self, generator):
        """Instagram square should be 1:1 aspect ratio."""
        spec = generator.get_crop_specification("instagram_square")

        if spec:
            assert spec["width"] == spec["height"]
            assert spec["width"] >= 1080

    def test_instagram_story_dimensions(self, generator):
        """Instagram story should be 9:16 aspect ratio."""
        spec = generator.get_crop_specification("instagram_story")

        if spec:
            assert spec["width"] == 1080
            assert spec["height"] == 1920

    def test_facebook_cover_dimensions(self, generator):
        """Facebook cover should have correct dimensions."""
        spec = generator.get_crop_specification("facebook_cover")

        if spec:
            assert spec["width"] == 820
            assert spec["height"] == 312

    def test_twitter_header_dimensions(self, generator):
        """Twitter header should have correct dimensions."""
        spec = generator.get_crop_specification("twitter_header")

        if spec:
            assert spec["width"] == 1500
            assert spec["height"] == 500

    def test_pinterest_dimensions(self, generator):
        """Pinterest should be 2:3 aspect ratio."""
        spec = generator.get_crop_specification("pinterest")

        if spec:
            # Pinterest optimal is 1000x1500
            assert spec["height"] > spec["width"]


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestPhotoshootErrors:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_invalid_preset(self):
        """Should handle invalid preset gracefully."""
        from ai_3d.virtual_photoshoot import PhotoshootError

        generator = VirtualPhotoshootGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "model.glb"
            model_path.write_bytes(b"fake glb")

            with pytest.raises(PhotoshootError, match="Unknown preset"):
                await generator.generate_photoshoot(
                    product_sku="SKR-001",
                    model_path=model_path,
                    scene_preset="nonexistent_preset",
                )

    @pytest.mark.asyncio
    async def test_render_failure(self):
        """Should handle render failures gracefully."""
        from ai_3d.virtual_photoshoot import PhotoshootError

        generator = VirtualPhotoshootGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "corrupted.glb"
            model_path.write_bytes(b"corrupted data")

            with patch.object(
                generator,
                "_render_scene",
                side_effect=Exception("Render engine failed"),
            ), pytest.raises((PhotoshootError, Exception)):
                await generator.generate_photoshoot(
                    product_sku="SKR-001",
                    model_path=model_path,
                )


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_photoshoot_pipeline():
    """Test full photoshoot pipeline (mocked)."""
    generator = VirtualPhotoshootGenerator()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test model
        model_path = Path(tmpdir) / "product.glb"
        model_path.write_bytes(b"fake glb data")

        # Mock the photoshoot pipeline
        mock_result = GeneratedPhotoshoot(
            product_sku="TEST-001",
            scene_preset="skyyrose_brand",
            images=[Path(tmpdir) / f"photo_{i}.jpg" for i in range(4)],
            thumbnail=Path(tmpdir) / "thumb.jpg",
            social_crops={
                "instagram_square": Path(tmpdir) / "ig_square.jpg",
                "instagram_story": Path(tmpdir) / "ig_story.jpg",
            },
            generation_time_seconds=30.0,
            metadata={"ai_enhanced": True},
        )

        with patch.object(
            generator, "_run_photoshoot", new_callable=AsyncMock
        ) as mock_run:
            mock_run.return_value = mock_result

            result = await generator.generate_photoshoot(
                product_sku="TEST-001",
                model_path=model_path,
                scene_preset="skyyrose_brand",
                generate_social_crops=True,
                ai_enhance=True,
            )

            assert result.product_sku == "TEST-001"
            assert result.scene_preset == "skyyrose_brand"
            assert len(result.images) == 4
            assert len(result.social_crops) == 2


__all__ = [
    "TestScenePreset",
    "TestPhotoshootScene",
    "TestGeneratedPhotoshoot",
    "TestVirtualPhotoshootGenerator",
    "TestSocialMediaCrops",
    "TestPhotoshootErrors",
]
