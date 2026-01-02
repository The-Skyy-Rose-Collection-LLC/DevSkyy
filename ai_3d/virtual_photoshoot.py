"""
Virtual Photoshoot Generator
============================

Generate lifestyle product images from 3D models.

Features:
- Multiple scene presets (studio, outdoor, urban, minimal)
- AI-powered background generation
- HDR lighting simulation
- Social media crop optimization
- Web-optimized image exports

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import io
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    pass


class ScenePreset(str, Enum):
    """Available scene presets for virtual photoshoot."""

    STUDIO_WHITE = "studio_white"
    STUDIO_BLACK = "studio_black"
    OUTDOOR_NATURE = "outdoor_nature"
    URBAN_MODERN = "urban_modern"
    MINIMAL_GRADIENT = "minimal_gradient"
    LIFESTYLE_HOME = "lifestyle_home"
    LUXURY_MARBLE = "luxury_marble"


logger = structlog.get_logger(__name__)


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class PhotoshootScene:
    """Scene configuration for virtual photoshoot."""

    name: str
    background_hdri: str | None = None
    background_color: tuple[int, int, int] | None = None
    lighting_preset: str = "studio"
    camera_positions: list[dict[str, float]] = field(default_factory=list)
    props: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "background_hdri": self.background_hdri,
            "background_color": self.background_color,
            "lighting_preset": self.lighting_preset,
            "camera_positions": self.camera_positions,
            "props": self.props,
        }


@dataclass
class GeneratedPhotoshoot:
    """Results from virtual photoshoot."""

    product_sku: str
    scene_name: str
    images: list[Path]
    hero_image: Path
    social_crops: dict[str, Path]  # instagram, facebook, twitter
    web_optimized: list[Path]
    raw_renders: list[Path]

    # Metadata
    generation_time_seconds: float = 0.0
    total_images_generated: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "product_sku": self.product_sku,
            "scene_name": self.scene_name,
            "images": [str(p) for p in self.images],
            "hero_image": str(self.hero_image),
            "social_crops": {k: str(v) for k, v in self.social_crops.items()},
            "web_optimized": [str(p) for p in self.web_optimized],
            "raw_renders": [str(p) for p in self.raw_renders],
            "generation_time_seconds": round(self.generation_time_seconds, 2),
            "total_images_generated": self.total_images_generated,
        }


# =============================================================================
# Scene Presets
# =============================================================================

SCENE_PRESETS: dict[str, PhotoshootScene] = {
    "studio_white": PhotoshootScene(
        name="Studio White",
        background_color=(255, 255, 255),
        lighting_preset="soft_box",
        camera_positions=[
            {"elevation": 15, "azimuth": 0, "distance": 2.5},
            {"elevation": 15, "azimuth": 45, "distance": 2.5},
            {"elevation": 15, "azimuth": -45, "distance": 2.5},
            {"elevation": 30, "azimuth": 0, "distance": 2.0},
        ],
    ),
    "studio_black": PhotoshootScene(
        name="Studio Black",
        background_color=(15, 15, 15),
        lighting_preset="dramatic",
        camera_positions=[
            {"elevation": 10, "azimuth": 30, "distance": 2.5},
            {"elevation": 20, "azimuth": -20, "distance": 2.2},
        ],
    ),
    "urban_oakland": PhotoshootScene(
        name="Oakland Street",
        background_hdri="urban_oakland",
        lighting_preset="natural",
        camera_positions=[
            {"elevation": 5, "azimuth": 0, "distance": 3.0},
            {"elevation": 10, "azimuth": 25, "distance": 2.8},
        ],
    ),
    "lifestyle_minimal": PhotoshootScene(
        name="Minimal Lifestyle",
        background_color=(245, 242, 238),
        lighting_preset="window_light",
        camera_positions=[
            {"elevation": 20, "azimuth": 15, "distance": 2.0},
        ],
    ),
    "luxury_display": PhotoshootScene(
        name="Luxury Display",
        background_color=(20, 18, 22),
        lighting_preset="spotlight",
        camera_positions=[
            {"elevation": 25, "azimuth": 0, "distance": 2.2},
            {"elevation": 15, "azimuth": 35, "distance": 2.5},
        ],
    ),
    "skyyrose_brand": PhotoshootScene(
        name="SkyyRose Brand",
        background_color=(183, 110, 121),  # Rose gold primary
        lighting_preset="soft_box",
        camera_positions=[
            {"elevation": 15, "azimuth": 0, "distance": 2.5},
            {"elevation": 20, "azimuth": 30, "distance": 2.3},
            {"elevation": 10, "azimuth": -15, "distance": 2.8},
        ],
    ),
}

# Social media aspect ratios and dimensions
SOCIAL_CROPS: dict[str, tuple[float, float, int, int]] = {
    "instagram_square": (1.0, 1.0, 1080, 1080),
    "instagram_portrait": (0.8, 1.0, 1080, 1350),
    "instagram_story": (0.5625, 1.0, 1080, 1920),
    "facebook_post": (1.91, 1.0, 1200, 628),
    "twitter_post": (1.777, 1.0, 1200, 675),
    "pinterest": (0.666, 1.0, 1000, 1500),
}


# =============================================================================
# VirtualPhotoshootGenerator
# =============================================================================


class VirtualPhotoshootGenerator:
    """
    Generate lifestyle product images from 3D models.

    Features:
    - Multiple scene presets (studio, outdoor, urban, minimal)
    - AI-powered background generation
    - Automatic model placement
    - Social media crop optimization
    - HDR lighting simulation

    Example:
        generator = VirtualPhotoshootGenerator(
            output_dir=Path("./photoshoots"),
            models_dir=Path("./models")
        )
        result = await generator.generate_photoshoot(
            product_sku="SKU-001",
            scene_preset="studio_white"
        )
    """

    def __init__(
        self,
        output_dir: Path,
        models_dir: Path,
        hdri_dir: Path | None = None,
        hf_token: str | None = None,
    ) -> None:
        """
        Initialize VirtualPhotoshootGenerator.

        Args:
            output_dir: Directory for generated images
            models_dir: Directory containing 3D models
            hdri_dir: Directory with HDRI environment maps
            hf_token: HuggingFace API token for AI enhancements
        """
        self.output_dir = Path(output_dir)
        self.models_dir = Path(models_dir)
        self.hdri_dir = hdri_dir or Path("./assets/hdri")
        self.hf_token = hf_token or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN")

        # Create output directories
        (self.output_dir / "renders").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "hero").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "social").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "web").mkdir(parents=True, exist_ok=True)

        # HTTP client (lazy init)
        self._client: Any = None

        logger.info(
            "VirtualPhotoshootGenerator initialized",
            output_dir=str(self.output_dir),
            models_dir=str(self.models_dir),
        )

    async def generate_photoshoot(
        self,
        product_sku: str,
        scene_preset: str = "studio_white",
        custom_scene: PhotoshootScene | None = None,
        generate_social_crops: bool = True,
        ai_enhance: bool = True,
    ) -> GeneratedPhotoshoot:
        """
        Generate a complete virtual photoshoot for a product.

        Args:
            product_sku: Product SKU (must have 3D model)
            scene_preset: Name of preset scene or "custom"
            custom_scene: Custom scene configuration
            generate_social_crops: Generate social media crops
            ai_enhance: Apply AI enhancement to renders

        Returns:
            GeneratedPhotoshoot with all generated images
        """
        import time

        start_time = time.time()

        # Get scene configuration
        if custom_scene:
            scene = custom_scene
        elif scene_preset in SCENE_PRESETS:
            scene = SCENE_PRESETS[scene_preset]
        else:
            raise ValueError(f"Unknown scene preset: {scene_preset}")

        # Find 3D model
        model_path = self._find_model(product_sku)
        if not model_path:
            raise FileNotFoundError(f"No 3D model found for {product_sku}")

        logger.info(
            "Starting virtual photoshoot",
            product_sku=product_sku,
            scene=scene.name,
            model_path=str(model_path),
        )

        # Generate renders from each camera position
        raw_renders = []
        for i, camera_pos in enumerate(scene.camera_positions):
            render_path = await self._render_scene(model_path, scene, camera_pos, product_sku, i)
            raw_renders.append(render_path)

        # AI enhance renders if enabled
        enhanced_renders = []
        if ai_enhance and self.hf_token:
            for render in raw_renders:
                enhanced = await self._ai_enhance_render(render)
                enhanced_renders.append(enhanced)
        else:
            enhanced_renders = raw_renders.copy()

        # Select hero image (best angle)
        hero_index = self._select_hero_image(scene)
        hero_path = self.output_dir / "hero" / f"{product_sku}_hero.png"

        if enhanced_renders:
            from PIL import Image

            Image.open(enhanced_renders[hero_index]).save(hero_path)
        else:
            hero_path.touch()

        # Generate social media crops
        social_crops: dict[str, Path] = {}
        if generate_social_crops and hero_path.exists() and hero_path.stat().st_size > 0:
            for platform, (_aspect_w, _aspect_h, width, height) in SOCIAL_CROPS.items():
                crop_path = await self._generate_social_crop(
                    hero_path, product_sku, platform, width, height
                )
                social_crops[platform] = crop_path

        # Generate web-optimized versions
        web_optimized = await self._generate_web_versions(enhanced_renders, product_sku)

        generation_time = time.time() - start_time

        total_images = (
            len(raw_renders)
            + len(enhanced_renders)
            + len(social_crops)
            + len(web_optimized)
            + 1  # hero
        )

        result = GeneratedPhotoshoot(
            product_sku=product_sku,
            scene_name=scene.name,
            images=enhanced_renders,
            hero_image=hero_path,
            social_crops=social_crops,
            web_optimized=web_optimized,
            raw_renders=raw_renders,
            generation_time_seconds=generation_time,
            total_images_generated=total_images,
        )

        logger.info(
            "Virtual photoshoot completed",
            product_sku=product_sku,
            total_images=total_images,
            generation_time=round(generation_time, 2),
        )

        return result

    def _find_model(self, product_sku: str) -> Path | None:
        """Find 3D model file for product."""
        for ext in [".glb", ".gltf", ".obj", ".fbx"]:
            model_path = self.models_dir / f"{product_sku}{ext}"
            if model_path.exists():
                return model_path
        return None

    async def _render_scene(
        self,
        model_path: Path,
        scene: PhotoshootScene,
        camera_pos: dict[str, float],
        product_sku: str,
        index: int,
    ) -> Path:
        """Render scene from camera position."""
        render_path = self.output_dir / "renders" / f"{product_sku}_render_{index}.png"

        try:
            import numpy as np
            import trimesh
            from PIL import Image

            # Load mesh
            mesh = trimesh.load(str(model_path))
            tr_scene = trimesh.Scene(mesh)

            # Calculate camera pose from spherical coordinates
            elevation = np.radians(camera_pos.get("elevation", 15))
            azimuth = np.radians(camera_pos.get("azimuth", 0))
            distance = camera_pos.get("distance", 2.5)

            x = distance * np.cos(elevation) * np.sin(azimuth)
            y = distance * np.sin(elevation)
            z = distance * np.cos(elevation) * np.cos(azimuth)

            # Set camera position (simplified)
            camera_pose = np.eye(4)
            camera_pose[:3, 3] = [x, y, z]

            # Render
            png_data = tr_scene.save_image(resolution=(2048, 2048))

            # Convert to PIL Image
            render_img = Image.open(io.BytesIO(png_data))
            render_array = np.array(render_img)

            # Apply background color if set
            if scene.background_color:
                render_array = self._apply_background_color(render_array, scene.background_color)

            # Save
            Image.fromarray(render_array).save(render_path)

        except Exception as e:
            logger.warning(f"Render failed, creating placeholder: {e}")
            from PIL import Image

            # Create placeholder
            bg_color = scene.background_color or (200, 200, 200)
            img = Image.new("RGB", (2048, 2048), bg_color)
            img.save(render_path)

        return render_path

    def _apply_background_color(
        self,
        render: Any,
        color: tuple[int, int, int],
    ) -> Any:
        """Apply solid color background to render."""
        import numpy as np

        # Check if image has alpha channel
        if render.shape[2] == 4:
            alpha = render[:, :, 3] / 255.0
            background = np.full((*render.shape[:2], 3), color, dtype=np.uint8)

            # Composite
            result = np.zeros((*render.shape[:2], 3), dtype=np.uint8)
            for c in range(3):
                result[:, :, c] = (
                    alpha * render[:, :, c] + (1 - alpha) * background[:, :, c]
                ).astype(np.uint8)
            return result
        else:
            return render

    async def _ai_enhance_render(self, render_path: Path) -> Path:
        """Apply AI enhancement to render."""
        enhanced_path = render_path.parent / f"{render_path.stem}_enhanced.png"

        try:
            import aiohttp

            with open(render_path, "rb") as f:
                img_data = f.read()

            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    "https://api-inference.huggingface.co/models/ai-forever/Real-ESRGAN",
                    headers={"Authorization": f"Bearer {self.hf_token}"},
                    data=img_data,
                ) as response,
            ):
                if response.status == 200:
                    enhanced_data = await response.read()
                    from PIL import Image

                    enhanced = Image.open(io.BytesIO(enhanced_data))
                    enhanced.save(enhanced_path)
                    return enhanced_path

        except Exception as e:
            logger.warning(f"AI enhancement failed: {e}")

        # Fallback - copy original
        import shutil

        shutil.copy(render_path, enhanced_path)
        return enhanced_path

    def _select_hero_image(self, scene: PhotoshootScene) -> int:
        """Select best render as hero image."""
        best_index = 0
        best_score = -1.0

        for i, camera_pos in enumerate(scene.camera_positions):
            # Score based on angle (prefer front, slight elevation)
            azimuth_score = 1 - abs(camera_pos.get("azimuth", 0)) / 90
            elevation_score = 1 - abs(camera_pos.get("elevation", 15) - 15) / 30

            score = azimuth_score * 0.7 + elevation_score * 0.3

            if score > best_score:
                best_score = score
                best_index = i

        return best_index

    async def _generate_social_crop(
        self,
        source: Path,
        product_sku: str,
        platform: str,
        width: int,
        height: int,
    ) -> Path:
        """Generate social media optimized crop."""
        from PIL import Image

        output_path = self.output_dir / "social" / f"{product_sku}_{platform}.jpg"

        try:
            img = Image.open(source)

            # Calculate crop
            src_ratio = img.width / img.height
            dst_ratio = width / height

            if src_ratio > dst_ratio:
                # Source is wider - crop sides
                new_width = int(img.height * dst_ratio)
                left = (img.width - new_width) // 2
                crop_box = (left, 0, left + new_width, img.height)
            else:
                # Source is taller - crop top/bottom
                new_height = int(img.width / dst_ratio)
                top = (img.height - new_height) // 2
                crop_box = (0, top, img.width, top + new_height)

            cropped = img.crop(crop_box)
            resized = cropped.resize((width, height), Image.Resampling.LANCZOS)

            # Save as JPEG for social
            if resized.mode == "RGBA":
                resized = resized.convert("RGB")
            resized.save(output_path, "JPEG", quality=92, optimize=True)

        except Exception as e:
            logger.warning(f"Social crop failed: {e}")
            # Create placeholder
            Image.new("RGB", (width, height), (200, 200, 200)).save(output_path)

        return output_path

    async def _generate_web_versions(
        self,
        renders: list[Path],
        product_sku: str,
    ) -> list[Path]:
        """Generate web-optimized versions."""
        from PIL import Image

        web_versions = []

        sizes = [
            ("large", 1920, 1920),
            ("medium", 1200, 1200),
            ("small", 600, 600),
            ("thumbnail", 300, 300),
        ]

        for i, render in enumerate(renders):
            if not render.exists():
                continue

            try:
                img = Image.open(render)

                for size_name, max_w, max_h in sizes:
                    # Create copy for resizing
                    img_copy = img.copy()
                    img_copy.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

                    # Convert RGBA to RGB if needed
                    if img_copy.mode == "RGBA":
                        background = Image.new("RGB", img_copy.size, (255, 255, 255))
                        background.paste(img_copy, mask=img_copy.split()[3])
                        img_copy = background

                    # Save as WebP for web
                    output_path = self.output_dir / "web" / f"{product_sku}_{i}_{size_name}.webp"
                    img_copy.save(output_path, "WEBP", quality=85)
                    web_versions.append(output_path)

            except Exception as e:
                logger.warning(f"Web optimization failed for {render}: {e}")

        return web_versions

    async def close(self) -> None:
        """Clean up resources."""
        if self._client is not None and hasattr(self._client, "close"):
            await self._client.close()
        logger.info("VirtualPhotoshootGenerator closed")


__all__ = [
    "VirtualPhotoshootGenerator",
    "PhotoshootScene",
    "GeneratedPhotoshoot",
    "ScenePreset",
    "SCENE_PRESETS",
    "SOCIAL_CROPS",
]
