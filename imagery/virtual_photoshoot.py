# imagery/virtual_photoshoot.py
"""
Virtual Photoshoot Automation System for DevSkyy.

Generates professional product imagery using:
- 3D models rendered from multiple angles
- Configurable lighting setups
- Brand-consistent backgrounds
- Automated post-processing

Integrates with SkyyRose brand guidelines for consistent visual identity.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from errors.production_errors import (
    ThreeDGenerationError,
)

logger = logging.getLogger(__name__)

# Lazy imports
try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None  # type: ignore


class LightingPreset(str, Enum):
    """Predefined lighting setups for product photography."""

    STUDIO = "studio"  # Classic 3-point lighting
    SOFT = "soft"  # Soft diffused lighting
    DRAMATIC = "dramatic"  # High contrast dramatic
    NATURAL = "natural"  # Natural daylight simulation
    FASHION = "fashion"  # Fashion runway style
    PRODUCT = "product"  # E-commerce product shot
    LUXURY = "luxury"  # Premium luxury feel


class BackgroundPreset(str, Enum):
    """Background options for product shots."""

    WHITE = "white"  # Pure white (e-commerce standard)
    BLACK = "black"  # Pure black (luxury feel)
    GRADIENT = "gradient"  # Gradient background
    STUDIO = "studio"  # Studio environment
    LIFESTYLE = "lifestyle"  # Lifestyle context
    TRANSPARENT = "transparent"  # Transparent (PNG)
    SKYYROSE_PINK = "skyyrose_pink"  # Brand pink (#B76E79)


class CameraAngle(str, Enum):
    """Camera angle presets."""

    FRONT = "front"
    BACK = "back"
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"
    THREE_QUARTER = "three_quarter"
    HERO = "hero"  # Main marketing shot
    DETAIL = "detail"  # Close-up detail


@dataclass
class CameraConfig:
    """Camera configuration for rendering."""

    angle: CameraAngle = CameraAngle.HERO
    distance: float = 2.0  # Distance from subject
    fov: float = 45.0  # Field of view
    elevation: float = 15.0  # Elevation angle in degrees
    azimuth: float = 45.0  # Azimuth angle in degrees


@dataclass
class LightConfig:
    """Lighting configuration."""

    preset: LightingPreset = LightingPreset.STUDIO
    intensity: float = 1.0
    color_temperature: int = 5500  # Kelvin
    shadows: bool = True
    ambient_occlusion: bool = True


class PhotoshootConfig(BaseModel):
    """Configuration for a virtual photoshoot session."""

    # Output settings
    output_dir: str = Field(..., description="Output directory for rendered images")
    output_format: str = Field(default="png", description="Output image format")
    output_resolution: tuple[int, int] = Field(
        default=(2048, 2048),
        description="Output resolution (width, height)",
    )

    # Camera settings
    camera_angles: list[CameraAngle] = Field(
        default=[
            CameraAngle.FRONT,
            CameraAngle.BACK,
            CameraAngle.LEFT,
            CameraAngle.RIGHT,
            CameraAngle.HERO,
        ],
        description="Camera angles to render",
    )
    camera_distance: float = Field(default=2.0, description="Camera distance")
    camera_fov: float = Field(default=45.0, description="Camera field of view")

    # Lighting
    lighting_preset: LightingPreset = Field(
        default=LightingPreset.STUDIO,
        description="Lighting preset",
    )
    lighting_intensity: float = Field(default=1.0, description="Light intensity")

    # Background
    background: BackgroundPreset = Field(
        default=BackgroundPreset.WHITE,
        description="Background preset",
    )
    background_color: tuple[int, int, int] | None = Field(
        default=None,
        description="Custom background color (RGB)",
    )

    # Post-processing
    auto_crop: bool = Field(default=True, description="Auto-crop to content")
    add_watermark: bool = Field(default=False, description="Add SkyyRose watermark")
    enhance_colors: bool = Field(default=True, description="Enhance color vibrancy")

    # Brand settings
    brand_overlay: bool = Field(default=False, description="Add brand overlay")


@dataclass
class PhotoshootResult:
    """Results from a virtual photoshoot session."""

    success: bool
    model_path: str
    output_dir: str
    rendered_images: list[str] = field(default_factory=list)
    angles_rendered: list[CameraAngle] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def image_count(self) -> int:
        """Number of images rendered."""
        return len(self.rendered_images)


class VirtualPhotoshootPipeline:
    """
    Automated virtual photoshoot pipeline.

    Generates professional product imagery from 3D models
    with configurable lighting, angles, and backgrounds.

    Usage:
        pipeline = VirtualPhotoshootPipeline()
        config = PhotoshootConfig(output_dir="./renders")
        result = await pipeline.run("product.glb", config)
    """

    # SkyyRose brand colors
    BRAND_COLORS = {
        "primary": (183, 110, 121),  # #B76E79 Rose Gold
        "secondary": (26, 26, 26),  # #1A1A1A Charcoal
        "accent": (255, 215, 0),  # Gold
        "white": (255, 255, 255),
        "black": (0, 0, 0),
    }

    # Camera presets by angle
    CAMERA_PRESETS = {
        CameraAngle.FRONT: CameraConfig(angle=CameraAngle.FRONT, azimuth=0, elevation=0),
        CameraAngle.BACK: CameraConfig(angle=CameraAngle.BACK, azimuth=180, elevation=0),
        CameraAngle.LEFT: CameraConfig(angle=CameraAngle.LEFT, azimuth=-90, elevation=0),
        CameraAngle.RIGHT: CameraConfig(angle=CameraAngle.RIGHT, azimuth=90, elevation=0),
        CameraAngle.TOP: CameraConfig(angle=CameraAngle.TOP, azimuth=0, elevation=90),
        CameraAngle.BOTTOM: CameraConfig(angle=CameraAngle.BOTTOM, azimuth=0, elevation=-90),
        CameraAngle.THREE_QUARTER: CameraConfig(
            angle=CameraAngle.THREE_QUARTER, azimuth=45, elevation=30
        ),
        CameraAngle.HERO: CameraConfig(angle=CameraAngle.HERO, azimuth=35, elevation=20),
        CameraAngle.DETAIL: CameraConfig(
            angle=CameraAngle.DETAIL, azimuth=45, elevation=15, distance=1.0
        ),
    }

    def __init__(self) -> None:
        """Initialize the photoshoot pipeline."""
        if not PIL_AVAILABLE:
            raise ImportError(
                "Pillow is required for virtual photoshoot. " "Install with: pip install Pillow"
            )

        # Check for 3D rendering capability
        self._renderer = None
        self._init_renderer()

    def _init_renderer(self) -> None:
        """Initialize the 3D renderer."""
        try:
            import trimesh

            self._trimesh_available = True
        except ImportError:
            self._trimesh_available = False
            logger.warning("trimesh not available, using placeholder rendering")

    async def run(
        self,
        model_path: str | Path,
        config: PhotoshootConfig,
    ) -> PhotoshootResult:
        """
        Run a virtual photoshoot session.

        Args:
            model_path: Path to the 3D model
            config: Photoshoot configuration

        Returns:
            PhotoshootResult with rendered images
        """
        model_path = Path(model_path)
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        result = PhotoshootResult(
            success=False,
            model_path=str(model_path),
            output_dir=str(output_dir),
        )

        # Validate model exists
        if not model_path.exists():
            result.errors.append(f"Model file not found: {model_path}")
            return result

        try:
            # Load the 3D model
            mesh = await self._load_model(model_path)

            # Render each camera angle
            for angle in config.camera_angles:
                try:
                    camera_config = self.CAMERA_PRESETS.get(
                        angle,
                        CameraConfig(angle=angle),
                    )

                    # Override distance and FOV from config
                    camera_config.distance = config.camera_distance
                    camera_config.fov = config.camera_fov

                    # Render the image
                    rendered = await self._render_view(
                        mesh,
                        camera_config,
                        config,
                    )

                    # Post-process
                    if config.auto_crop:
                        rendered = self._auto_crop(rendered)

                    if config.enhance_colors:
                        rendered = self._enhance_colors(rendered)

                    if config.add_watermark:
                        rendered = self._add_watermark(rendered)

                    # Save the image
                    filename = f"{model_path.stem}_{angle.value}.{config.output_format}"
                    output_path = output_dir / filename
                    rendered.save(output_path)

                    result.rendered_images.append(str(output_path))
                    result.angles_rendered.append(angle)

                except Exception as e:
                    error_msg = f"Failed to render {angle.value}: {e}"
                    result.errors.append(error_msg)
                    logger.error(error_msg)

            result.success = len(result.rendered_images) > 0
            result.metadata = {
                "angles_requested": len(config.camera_angles),
                "angles_rendered": len(result.angles_rendered),
                "resolution": config.output_resolution,
                "format": config.output_format,
            }

        except Exception as e:
            result.errors.append(f"Pipeline error: {e}")
            logger.exception("Virtual photoshoot pipeline failed")

        return result

    async def _load_model(self, model_path: Path) -> Any:
        """Load a 3D model."""
        if not self._trimesh_available:
            raise ThreeDGenerationError(
                "trimesh is required for 3D model loading",
                generator="VirtualPhotoshootPipeline",
            )

        import trimesh

        try:
            mesh = trimesh.load(str(model_path), force="mesh")
            return mesh
        except Exception as e:
            raise ThreeDGenerationError(
                f"Failed to load model: {e}",
                generator="VirtualPhotoshootPipeline",
                cause=e,
            )

    async def _render_view(
        self,
        mesh: Any,
        camera_config: CameraConfig,
        photoshoot_config: PhotoshootConfig,
    ) -> Image.Image:
        """Render a single view of the model."""
        import numpy as np
        import trimesh

        # Get resolution
        width, height = photoshoot_config.output_resolution

        # Create scene
        scene = trimesh.Scene(geometry=mesh)

        # Set up camera
        scene.set_camera(
            angles=[
                np.radians(camera_config.elevation),
                np.radians(camera_config.azimuth),
            ],
            distance=camera_config.distance,
            fov=[camera_config.fov, camera_config.fov],
        )

        # Get background color
        bg_color = self._get_background_color(photoshoot_config)

        # Render to image
        try:
            # Use trimesh's built-in rendering
            png_data = scene.save_image(
                resolution=[width, height],
                visible=False,
            )

            # Convert to PIL Image
            from io import BytesIO

            image = Image.open(BytesIO(png_data))

            # Apply background if not transparent
            if photoshoot_config.background != BackgroundPreset.TRANSPARENT:
                if image.mode == "RGBA":
                    background = Image.new("RGB", image.size, bg_color)
                    background.paste(image, mask=image.split()[3])
                    image = background

            return image

        except Exception as e:
            # Fallback: create placeholder image
            logger.warning(f"Rendering failed, creating placeholder: {e}")
            return self._create_placeholder(width, height, bg_color)

    def _get_background_color(
        self,
        config: PhotoshootConfig,
    ) -> tuple[int, int, int]:
        """Get background color from config."""
        if config.background_color:
            return config.background_color

        bg_map = {
            BackgroundPreset.WHITE: (255, 255, 255),
            BackgroundPreset.BLACK: (0, 0, 0),
            BackgroundPreset.SKYYROSE_PINK: self.BRAND_COLORS["primary"],
            BackgroundPreset.GRADIENT: (245, 245, 245),
            BackgroundPreset.STUDIO: (240, 240, 240),
            BackgroundPreset.LIFESTYLE: (250, 248, 245),
            BackgroundPreset.TRANSPARENT: (0, 0, 0),
        }

        return bg_map.get(config.background, (255, 255, 255))

    def _create_placeholder(
        self,
        width: int,
        height: int,
        bg_color: tuple[int, int, int],
    ) -> Image.Image:
        """Create a placeholder image when rendering fails."""
        from PIL import ImageDraw, ImageFont

        image = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(image)

        # Add text
        text = "3D Render\nPlaceholder"
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
        except Exception:
            font = ImageFont.load_default()

        # Center text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2

        draw.text((x, y), text, fill=(128, 128, 128), font=font)

        return image

    def _auto_crop(self, image: Image.Image) -> Image.Image:
        """Auto-crop to content bounds."""
        try:
            # Get bounding box of non-background content
            if image.mode == "RGBA":
                # Use alpha channel
                alpha = image.split()[3]
                bbox = alpha.getbbox()
            else:
                # Convert to grayscale and find bounds
                gray = image.convert("L")
                bbox = gray.getbbox()

            if bbox:
                # Add padding
                padding = 20
                bbox = (
                    max(0, bbox[0] - padding),
                    max(0, bbox[1] - padding),
                    min(image.width, bbox[2] + padding),
                    min(image.height, bbox[3] + padding),
                )
                return image.crop(bbox)

            return image

        except Exception as e:
            logger.warning(f"Auto-crop failed: {e}")
            return image

    def _enhance_colors(self, image: Image.Image) -> Image.Image:
        """Enhance color vibrancy."""
        from PIL import ImageEnhance

        try:
            # Slight saturation boost
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.1)

            # Slight contrast boost
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.05)

            return image

        except Exception as e:
            logger.warning(f"Color enhancement failed: {e}")
            return image

    def _add_watermark(self, image: Image.Image) -> Image.Image:
        """Add SkyyRose watermark."""
        from PIL import ImageDraw, ImageFont

        try:
            draw = ImageDraw.Draw(image)

            # Watermark text
            text = "SkyyRose"

            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    24,
                )
            except Exception:
                font = ImageFont.load_default()

            # Position in bottom right
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x = image.width - text_width - 20
            y = image.height - text_height - 20

            # Semi-transparent watermark
            draw.text(
                (x, y),
                text,
                fill=(183, 110, 121, 128),  # Brand pink with alpha
                font=font,
            )

            return image

        except Exception as e:
            logger.warning(f"Watermark failed: {e}")
            return image

    async def generate_product_set(
        self,
        model_path: str | Path,
        output_dir: str | Path,
        include_hero: bool = True,
        include_360: bool = False,
    ) -> PhotoshootResult:
        """
        Generate a complete product image set.

        Standard e-commerce image set:
        - Hero shot (main marketing image)
        - Front, back, left, right views
        - Detail shot (close-up)

        Args:
            model_path: Path to 3D model
            output_dir: Output directory
            include_hero: Include hero marketing shot
            include_360: Include 360-degree rotation frames

        Returns:
            PhotoshootResult with all generated images
        """
        angles = [
            CameraAngle.FRONT,
            CameraAngle.BACK,
            CameraAngle.LEFT,
            CameraAngle.RIGHT,
        ]

        if include_hero:
            angles.append(CameraAngle.HERO)
            angles.append(CameraAngle.DETAIL)

        config = PhotoshootConfig(
            output_dir=str(output_dir),
            camera_angles=angles,
            lighting_preset=LightingPreset.PRODUCT,
            background=BackgroundPreset.WHITE,
            auto_crop=True,
            enhance_colors=True,
        )

        result = await self.run(model_path, config)

        # Generate 360 rotation if requested
        if include_360:
            rotation_result = await self._generate_360_rotation(
                model_path,
                output_dir,
                frames=36,
            )
            result.rendered_images.extend(rotation_result.rendered_images)

        return result

    async def _generate_360_rotation(
        self,
        model_path: str | Path,
        output_dir: str | Path,
        frames: int = 36,
    ) -> PhotoshootResult:
        """Generate 360-degree rotation frames."""
        model_path = Path(model_path)
        output_dir = Path(output_dir) / "360"
        output_dir.mkdir(parents=True, exist_ok=True)

        result = PhotoshootResult(
            success=False,
            model_path=str(model_path),
            output_dir=str(output_dir),
        )

        try:
            mesh = await self._load_model(model_path)

            for i in range(frames):
                azimuth = (360 / frames) * i

                camera_config = CameraConfig(
                    angle=CameraAngle.FRONT,
                    azimuth=azimuth,
                    elevation=15,
                    distance=2.0,
                )

                config = PhotoshootConfig(
                    output_dir=str(output_dir),
                    output_resolution=(1024, 1024),
                    background=BackgroundPreset.TRANSPARENT,
                )

                rendered = await self._render_view(mesh, camera_config, config)

                filename = f"{model_path.stem}_360_{i:03d}.png"
                output_path = output_dir / filename
                rendered.save(output_path)

                result.rendered_images.append(str(output_path))

            result.success = True

        except Exception as e:
            result.errors.append(f"360 rotation generation failed: {e}")

        return result
