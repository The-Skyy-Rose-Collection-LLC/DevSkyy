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
from unittest.mock import AsyncMock, Mock, patch

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
        assert ScenePreset.URBAN_MODERN.value == "urban_modern"
        assert ScenePreset.OUTDOOR_NATURE.value == "outdoor_nature"
        assert ScenePreset.MINIMAL_GRADIENT.value == "minimal_gradient"
        assert ScenePreset.LIFESTYLE_HOME.value == "lifestyle_home"
        assert ScenePreset.LUXURY_MARBLE.value == "luxury_marble"


# =============================================================================
# PhotoshootScene Tests
# =============================================================================


class TestPhotoshootScene:
    """Tests for PhotoshootScene dataclass."""

    def test_scene_creation(self):
        """Should create scene with all fields."""
        scene = PhotoshootScene(
            name="custom_scene",
            background_color=(255, 255, 255),
            lighting_preset="studio",
            camera_positions=[{"x": 0, "y": 0, "z": 5}],
            props=[],
        )

        assert scene.name == "custom_scene"
        assert scene.background_color == (255, 255, 255)
        assert scene.lighting_preset == "studio"
        assert len(scene.camera_positions) == 1

    def test_scene_with_props(self):
        """Should include props."""
        scene = PhotoshootScene(
            name="with_props",
            background_color=(26, 26, 26),
            lighting_preset="dramatic",
            camera_positions=[{"x": 0, "y": 0, "z": 5}],
            props=[{"type": "mannequin"}, {"type": "pedestal"}],
        )

        assert len(scene.props) == 2
        assert scene.props[0]["type"] == "mannequin"


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

        hero_image = tmp_path / "hero.jpg"
        hero_image.touch()

        crops = {
            "instagram_square": tmp_path / "ig_square.jpg",
            "instagram_story": tmp_path / "ig_story.jpg",
        }
        for crop in crops.values():
            crop.touch()

        web_optimized = [tmp_path / "web_0.jpg"]
        web_optimized[0].touch()

        raw_renders = [tmp_path / "raw_0.jpg"]
        raw_renders[0].touch()

        photoshoot = GeneratedPhotoshoot(
            product_sku="SKR-001",
            scene_name="studio_white",
            images=images,
            hero_image=hero_image,
            social_crops=crops,
            web_optimized=web_optimized,
            raw_renders=raw_renders,
            generation_time_seconds=25.5,
            total_images_generated=4,
        )

        assert photoshoot.product_sku == "SKR-001"
        assert photoshoot.scene_name == "studio_white"
        assert len(photoshoot.images) == 4
        assert len(photoshoot.social_crops) == 2

    def test_photoshoot_to_dict(self, tmp_path):
        """Should convert to dictionary."""
        images = [tmp_path / "img_0.jpg"]
        images[0].touch()

        hero_image = tmp_path / "hero.jpg"
        hero_image.touch()

        photoshoot = GeneratedPhotoshoot(
            product_sku="SKR-002",
            scene_name="minimal_gradient",
            images=images,
            hero_image=hero_image,
            social_crops={},
            web_optimized=[],
            raw_renders=[],
            generation_time_seconds=15.0,
        )

        result = photoshoot.to_dict()
        assert result["product_sku"] == "SKR-002"
        assert result["scene_name"] == "minimal_gradient"
        assert len(result["images"]) == 1


# =============================================================================
# VirtualPhotoshootGenerator Tests
# =============================================================================


class TestVirtualPhotoshootGenerator:
    """Tests for VirtualPhotoshootGenerator class."""

    @pytest.fixture
    def generator(self, tmp_path):
        """Create generator instance with temp directories."""
        output_dir = tmp_path / "photoshoot_output"
        models_dir = tmp_path / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        return VirtualPhotoshootGenerator(output_dir=output_dir, models_dir=models_dir)

    @pytest.fixture
    def sample_model(self, tmp_path):
        """Create sample 3D model file."""
        model_path = tmp_path / "product.glb"
        model_path.write_bytes(b"fake glb data")
        return model_path

    def test_generator_initialization(self, generator):
        """Should initialize with output directories."""
        assert generator.output_dir.exists()
        assert generator.models_dir.exists()

    def test_generator_custom_output_dir(self, tmp_path):
        """Should use custom output directory."""
        custom_dir = tmp_path / "custom_photos"
        models_dir = tmp_path / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        generator = VirtualPhotoshootGenerator(output_dir=custom_dir, models_dir=models_dir)

        assert generator.output_dir == custom_dir
        assert custom_dir.exists()

    def test_scene_presets_available(self):
        """Should have scene presets available."""
        from ai_3d.virtual_photoshoot import SCENE_PRESETS

        assert "studio_white" in SCENE_PRESETS
        assert "studio_black" in SCENE_PRESETS
        assert "urban_oakland" in SCENE_PRESETS
        assert "lifestyle_minimal" in SCENE_PRESETS
        assert "luxury_display" in SCENE_PRESETS
        assert "skyyrose_brand" in SCENE_PRESETS

    @pytest.mark.asyncio
    async def test_generate_photoshoot_missing_model(self, generator):
        """Should raise error for missing model."""
        # _find_model returns None when no model found
        with (
            patch.object(generator, "_find_model", return_value=None),
            pytest.raises(FileNotFoundError, match="No 3D model found"),
        ):
            await generator.generate_photoshoot(
                product_sku="NONEXISTENT-001",
            )

    @pytest.mark.asyncio
    async def test_generate_photoshoot_invalid_preset(self, generator, sample_model):
        """Should raise error for invalid preset."""
        # Mock _find_model to return a valid path
        with (
            patch.object(generator, "_find_model", return_value=sample_model),
            pytest.raises(ValueError, match="Unknown scene preset"),
        ):
            await generator.generate_photoshoot(
                product_sku="SKR-001",
                scene_preset="nonexistent_preset",
            )

    @pytest.mark.asyncio
    async def test_generate_photoshoot_default_preset(self, generator, sample_model, tmp_path):
        """Should use default preset when not specified."""
        hero_path = tmp_path / "hero" / "SKR-001_hero.png"
        hero_path.parent.mkdir(parents=True, exist_ok=True)

        # Create a mock image
        mock_image = Mock()
        mock_image.save = Mock()

        with (
            patch.object(generator, "_find_model", return_value=sample_model),
            patch.object(generator, "_render_scene", new_callable=AsyncMock) as mock_render,
            patch.object(generator, "_ai_enhance_render", new_callable=AsyncMock) as mock_enhance,
            patch.object(generator, "_select_hero_image", return_value=0),
            patch.object(generator, "_generate_social_crop", new_callable=AsyncMock) as mock_crop,
            patch.object(generator, "_generate_web_versions", new_callable=AsyncMock) as mock_web,
            patch("PIL.Image.open", return_value=mock_image),
        ):
            render_path = tmp_path / "render_0.png"
            render_path.touch()
            mock_render.return_value = render_path
            mock_enhance.return_value = render_path
            mock_crop.return_value = tmp_path / "crop.jpg"
            mock_web.return_value = [tmp_path / "web.jpg"]

            result = await generator.generate_photoshoot(
                product_sku="SKR-001",
            )

            assert result.product_sku == "SKR-001"
            assert result.scene_name == "Studio White"  # Name from preset

    @pytest.mark.asyncio
    async def test_generate_photoshoot_custom_scene(self, generator, sample_model, tmp_path):
        """Should use custom scene configuration."""
        custom_scene = PhotoshootScene(
            name="Custom Scene",
            background_color=(255, 0, 0),
            lighting_preset="dramatic",
            camera_positions=[{"elevation": 15, "azimuth": 0, "distance": 2.5}],
        )

        hero_path = tmp_path / "hero" / "SKR-001_hero.png"
        hero_path.parent.mkdir(parents=True, exist_ok=True)

        # Create a mock image
        mock_image = Mock()
        mock_image.save = Mock()

        with (
            patch.object(generator, "_find_model", return_value=sample_model),
            patch.object(generator, "_render_scene", new_callable=AsyncMock) as mock_render,
            patch.object(generator, "_ai_enhance_render", new_callable=AsyncMock) as mock_enhance,
            patch.object(generator, "_select_hero_image", return_value=0),
            patch.object(generator, "_generate_social_crop", new_callable=AsyncMock) as mock_crop,
            patch.object(generator, "_generate_web_versions", new_callable=AsyncMock) as mock_web,
            patch("PIL.Image.open", return_value=mock_image),
        ):
            render_path = tmp_path / "render_0.png"
            render_path.touch()
            mock_render.return_value = render_path
            mock_enhance.return_value = render_path
            mock_crop.return_value = tmp_path / "crop.jpg"
            mock_web.return_value = [tmp_path / "web.jpg"]

            result = await generator.generate_photoshoot(
                product_sku="SKR-001",
                custom_scene=custom_scene,
            )

            assert result.scene_name == "Custom Scene"

    @pytest.mark.asyncio
    async def test_close(self, generator):
        """Should close cleanly."""
        await generator.close()
        # Should complete without error


# =============================================================================
# Social Media Crop Tests
# =============================================================================


class TestSocialMediaCrops:
    """Tests for social media crop specifications."""

    def test_social_crops_available(self):
        """Should have social crop specifications available."""
        from ai_3d.virtual_photoshoot import SOCIAL_CROPS

        assert "instagram_square" in SOCIAL_CROPS
        assert "instagram_story" in SOCIAL_CROPS
        assert "pinterest" in SOCIAL_CROPS

    def test_instagram_square_dimensions(self):
        """Instagram square should be 1:1 aspect ratio."""
        from ai_3d.virtual_photoshoot import SOCIAL_CROPS

        spec = SOCIAL_CROPS["instagram_square"]
        # Format: (aspect_w, aspect_h, width, height)
        assert spec[2] == spec[3]  # width == height
        assert spec[2] >= 1080

    def test_instagram_story_dimensions(self):
        """Instagram story should be 9:16 aspect ratio."""
        from ai_3d.virtual_photoshoot import SOCIAL_CROPS

        spec = SOCIAL_CROPS["instagram_story"]
        # Format: (aspect_w, aspect_h, width, height)
        assert spec[2] == 1080
        assert spec[3] == 1920

    def test_pinterest_dimensions(self):
        """Pinterest should be 2:3 aspect ratio."""
        from ai_3d.virtual_photoshoot import SOCIAL_CROPS

        spec = SOCIAL_CROPS["pinterest"]
        # Format: (aspect_w, aspect_h, width, height)
        # Pinterest optimal is 1000x1500
        assert spec[3] > spec[2]  # height > width


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestPhotoshootErrors:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_invalid_preset(self):
        """Should raise ValueError for invalid preset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_dir = tmpdir_path / "output"
            models_dir = tmpdir_path / "models"
            models_dir.mkdir(parents=True, exist_ok=True)
            generator = VirtualPhotoshootGenerator(output_dir=output_dir, models_dir=models_dir)
            model_path = Path(tmpdir) / "model.glb"
            model_path.write_bytes(b"fake glb")

            with (
                patch.object(generator, "_find_model", return_value=model_path),
                pytest.raises(ValueError, match="Unknown scene preset"),
            ):
                await generator.generate_photoshoot(
                    product_sku="SKR-001",
                    scene_preset="nonexistent_preset",
                )

    @pytest.mark.asyncio
    async def test_model_not_found(self):
        """Should raise FileNotFoundError for missing model."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            output_dir = tmpdir_path / "output"
            models_dir = tmpdir_path / "models"
            models_dir.mkdir(parents=True, exist_ok=True)
            generator = VirtualPhotoshootGenerator(output_dir=output_dir, models_dir=models_dir)

            with (
                patch.object(generator, "_find_model", return_value=None),
                pytest.raises(FileNotFoundError, match="No 3D model found"),
            ):
                await generator.generate_photoshoot(
                    product_sku="NONEXISTENT-001",
                )


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_photoshoot_pipeline():
    """Test full photoshoot pipeline (mocked)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        output_dir = tmpdir_path / "output"
        models_dir = tmpdir_path / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        generator = VirtualPhotoshootGenerator(output_dir=output_dir, models_dir=models_dir)

        # Create test model
        model_path = Path(tmpdir) / "product.glb"
        model_path.write_bytes(b"fake glb data")

        # Create output directories
        hero_dir = output_dir / "hero"
        hero_dir.mkdir(parents=True, exist_ok=True)

        # Create mock image files
        images = []
        for i in range(4):
            img_path = Path(tmpdir) / f"photo_{i}.jpg"
            img_path.touch()
            images.append(img_path)

        hero_path = hero_dir / "TEST-001_hero.png"
        hero_path.touch()

        # Create a mock image
        mock_image = Mock()
        mock_image.save = Mock()

        with (
            patch.object(generator, "_find_model", return_value=model_path),
            patch.object(generator, "_render_scene", new_callable=AsyncMock) as mock_render,
            patch.object(generator, "_ai_enhance_render", new_callable=AsyncMock) as mock_enhance,
            patch.object(generator, "_select_hero_image", return_value=0),
            patch.object(generator, "_generate_social_crop", new_callable=AsyncMock) as mock_crop,
            patch.object(generator, "_generate_web_versions", new_callable=AsyncMock) as mock_web,
            patch("PIL.Image.open", return_value=mock_image),
        ):
            render_path = Path(tmpdir) / "render_0.png"
            render_path.touch()
            mock_render.return_value = render_path
            mock_enhance.return_value = render_path
            mock_crop.return_value = Path(tmpdir) / "crop.jpg"
            mock_web.return_value = [Path(tmpdir) / "web.jpg"]

            result = await generator.generate_photoshoot(
                product_sku="TEST-001",
                scene_preset="skyyrose_brand",
                generate_social_crops=True,
                ai_enhance=True,
            )

            assert result.product_sku == "TEST-001"
            assert result.scene_name == "SkyyRose Brand"
            assert len(result.images) >= 1


__all__ = [
    "TestScenePreset",
    "TestPhotoshootScene",
    "TestGeneratedPhotoshoot",
    "TestVirtualPhotoshootGenerator",
    "TestSocialMediaCrops",
    "TestPhotoshootErrors",
]
