"""Luxury Product Photography Generation.

Enterprise-grade product photography using multi-stage refinement
for magazine-quality output matching SkyyRose brand standards.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)


class ShotType(str, Enum):
    """Types of product shots."""

    HERO = "hero"
    FRONT = "front"
    BACK = "back"
    SIDE_LEFT = "side_left"
    SIDE_RIGHT = "side_right"
    DETAIL_FABRIC = "detail_fabric"
    DETAIL_CONSTRUCTION = "detail_construction"
    LIFESTYLE_URBAN = "lifestyle_urban"
    LIFESTYLE_LUXURY = "lifestyle_luxury"
    PACKAGING = "packaging"


class LightingPreset(str, Enum):
    """Professional lighting presets."""

    STUDIO_DRAMATIC = "studio_dramatic"
    STUDIO_FLAT = "studio_flat"
    STUDIO_CONTOUR = "studio_contour"
    MACRO_CLOSEUP = "macro_closeup"
    GOLDEN_HOUR = "golden_hour_natural"
    AMBIENT_LUXURY = "ambient_luxury"
    SOFT_COMMERCIAL = "soft_commercial"


class ColorGrade(str, Enum):
    """Color grading profiles."""

    LUXURY_NEUTRAL = "luxury_neutral"
    MOODY_NOIR = "moody_noir"
    WARM_ROMANTIC = "warm_romantic"
    COOL_EDITORIAL = "cool_editorial"


@dataclass
class GarmentSpecs:
    """Specifications for a garment."""

    name: str
    garment_type: str
    collection: str
    colors: list[str] = field(default_factory=list)
    materials: list[str] = field(default_factory=list)
    details: str = ""


@dataclass
class PhotoSuite:
    """Complete product photography suite."""

    hero: Image.Image | None = None
    front: Image.Image | None = None
    back: Image.Image | None = None
    side_left: Image.Image | None = None
    side_right: Image.Image | None = None
    detail_fabric: Image.Image | None = None
    detail_construction: Image.Image | None = None
    lifestyle_urban: Image.Image | None = None
    lifestyle_luxury: Image.Image | None = None
    packaging: Image.Image | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def save_all(self, output_dir: Path, prefix: str = "") -> dict[str, Path]:
        """Save all images to directory."""
        output_dir.mkdir(parents=True, exist_ok=True)
        saved = {}

        for shot_type in ShotType:
            img = getattr(self, shot_type.value, None)
            if img:
                filename = f"{prefix}_{shot_type.value}.jpg" if prefix else f"{shot_type.value}.jpg"
                path = output_dir / filename
                img.save(path, quality=95)
                saved[shot_type.value] = path

        return saved


class LuxuryProductPhotography:
    """Enterprise-grade product photography generation.

    Multi-stage refinement pipeline:
    1. Structure generation with ControlNet
    2. Style transfer with IP-Adapter
    3. Quality refinement with SDXL Refiner
    4. Professional post-processing

    Example:
        >>> photography = LuxuryProductPhotography()
        >>> specs = GarmentSpecs(
        ...     name="Black Rose Sherpa",
        ...     garment_type="sherpa",
        ...     collection="BLACK_ROSE"
        ... )
        >>> suite = await photography.generate_complete_product_suite(specs)
    """

    COLLECTION_AESTHETICS = {
        "BLACK_ROSE": "dark elegance, limited edition mystique, moody lighting, noir aesthetic, gothic romance",
        "LOVE_HURTS": "emotional depth, vulnerable strength, romantic rebellion, artistic expression, edgy passion",
        "SIGNATURE": "refined foundation, timeless sophistication, versatile luxury, essential wardrobe, rose gold accents",
        # Aliases
        "black-rose": "dark elegance, limited edition mystique, moody lighting, noir aesthetic, gothic romance",
        "love-hurts": "emotional depth, vulnerable strength, romantic rebellion, artistic expression, edgy passion",
        "signature": "refined foundation, timeless sophistication, versatile luxury, essential wardrobe, rose gold accents",
    }

    LIGHTING_PROMPTS = {
        LightingPreset.STUDIO_DRAMATIC: "dramatic studio lighting, deep shadows, high contrast, single key light",
        LightingPreset.STUDIO_FLAT: "even studio lighting, minimal shadows, commercial product photography",
        LightingPreset.STUDIO_CONTOUR: "contour lighting, rim light, shape-defining shadows",
        LightingPreset.MACRO_CLOSEUP: "macro photography, detailed texture, shallow depth of field",
        LightingPreset.GOLDEN_HOUR: "golden hour natural light, warm tones, outdoor ambient",
        LightingPreset.AMBIENT_LUXURY: "soft ambient lighting, luxury interior, elegant atmosphere",
        LightingPreset.SOFT_COMMERCIAL: "soft commercial lighting, clean white background, catalog photography",
    }

    ANGLE_PROMPTS = {
        ShotType.HERO: "front three-quarter view, hero angle, dynamic presentation",
        ShotType.FRONT: "straight front view, centered, symmetrical",
        ShotType.BACK: "straight back view, showing back design details",
        ShotType.SIDE_LEFT: "left side profile, silhouette visible",
        ShotType.SIDE_RIGHT: "right side profile, silhouette visible",
        ShotType.DETAIL_FABRIC: "extreme close-up, fabric texture visible, material detail",
        ShotType.DETAIL_CONSTRUCTION: "close-up, stitching detail, construction quality",
        ShotType.LIFESTYLE_URBAN: "oakland street setting, urban environment, authentic streetwear context",
        ShotType.LIFESTYLE_LUXURY: "upscale interior setting, luxury environment, premium lifestyle",
        ShotType.PACKAGING: "product with luxury packaging, unboxing experience, premium presentation",
    }

    def __init__(
        self,
        model_dir: Path | str = Path("models"),
        device: str = "auto",
    ) -> None:
        """Initialize luxury photography pipeline.

        Args:
            model_dir: Directory containing SDXL models
            device: Device to use (auto, cuda, mps, cpu)
        """
        self.model_dir = Path(model_dir)
        self.device = device
        self._pipeline = None
        self._refiner = None
        self._controlnet = None
        self._ip_adapter = None
        self._lora_loaded = False

    def _get_pipeline(self):
        """Lazy load the SDXL pipeline."""
        if self._pipeline is None:
            from imagery.sdxl_pipeline import SDXLPipeline

            self._pipeline = SDXLPipeline(
                model_dir=self.model_dir,
                device=self.device,
            )
        return self._pipeline

    def _build_luxury_prompt(
        self,
        specs: GarmentSpecs,
        shot_type: ShotType = ShotType.HERO,
        lighting: LightingPreset = LightingPreset.STUDIO_DRAMATIC,
    ) -> str:
        """Build optimized prompt for luxury positioning."""
        collection_key = specs.collection.upper().replace("-", "_")
        collection_aesthetic = self.COLLECTION_AESTHETICS.get(
            collection_key,
            self.COLLECTION_AESTHETICS.get(specs.collection, "luxury streetwear"),
        )

        lighting_desc = self.LIGHTING_PROMPTS.get(lighting, "")
        angle_desc = self.ANGLE_PROMPTS.get(shot_type, "")

        materials = ", ".join(specs.materials) if specs.materials else "premium fabric"
        colors = ", ".join(specs.colors) if specs.colors else ""

        prompt_parts = [
            f"{specs.garment_type} from {specs.collection} collection",
            f"product name: {specs.name}",
            collection_aesthetic,
            angle_desc,
            lighting_desc,
            f"materials: {materials}",
            f"colors: {colors}" if colors else "",
            specs.details,
            "luxury streetwear, high-fashion photography",
            "Oakland street culture meets high fashion",
            "professional studio lighting, Phase One camera quality",
            "Hasselblad medium format aesthetic",
            "8K resolution, ultra detailed fabric texture",
            "premium materials visible, impeccable craftsmanship",
            "editorial fashion magazine quality, Vogue standard",
            "neutral background with subtle gradients",
            "gender-neutral presentation, inclusive fashion",
            "SkyyRose signature aesthetic",
        ]

        return ", ".join(filter(None, prompt_parts))

    def _luxury_negative_prompt(self) -> str:
        """Build negative prompt for luxury quality."""
        return (
            "low quality, blurry, pixelated, amateur photography, "
            "cheap fabric, poor lighting, cluttered background, "
            "oversaturated colors, consumer camera quality, "
            "smartphone photo, social media quality, "
            "distorted proportions, unrealistic anatomy, "
            "generic stock photo, fast fashion aesthetic, "
            "watermark, text overlay, logo, mannequin, model, "
            "person wearing, wrinkled, dirty, stained"
        )

    def _apply_color_grade(
        self,
        image: Image.Image,
        profile: ColorGrade = ColorGrade.LUXURY_NEUTRAL,
    ) -> Image.Image:
        """Apply professional color grading."""
        if profile == ColorGrade.LUXURY_NEUTRAL:
            # Subtle contrast boost, neutral tones
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.1)
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(0.95)

        elif profile == ColorGrade.MOODY_NOIR:
            # High contrast, desaturated
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.3)
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(0.7)
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(0.9)

        elif profile == ColorGrade.WARM_ROMANTIC:
            # Warm tones, soft contrast
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.1)
            # Add warmth via RGB adjustment
            r, g, b = image.split()
            r = r.point(lambda x: min(255, int(x * 1.05)))
            b = b.point(lambda x: int(x * 0.95))
            image = Image.merge("RGB", (r, g, b))

        elif profile == ColorGrade.COOL_EDITORIAL:
            # Cool tones, high contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            r, g, b = image.split()
            r = r.point(lambda x: int(x * 0.95))
            b = b.point(lambda x: min(255, int(x * 1.05)))
            image = Image.merge("RGB", (r, g, b))

        return image

    def _apply_subtle_vignette(self, image: Image.Image, strength: float = 0.3) -> Image.Image:
        """Apply subtle vignette for focus."""
        width, height = image.size

        # Create radial gradient mask
        x = np.linspace(-1, 1, width)
        y = np.linspace(-1, 1, height)
        X, Y = np.meshgrid(x, y)
        R = np.sqrt(X**2 + Y**2)

        # Smooth falloff
        vignette = 1 - (strength * np.clip(R - 0.5, 0, 1))
        vignette = np.clip(vignette, 0.7, 1.0)

        # Apply to image
        img_array = np.array(image, dtype=np.float32)
        for i in range(3):
            img_array[:, :, i] *= vignette

        return Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))

    def _luxury_post_process(
        self,
        image: Image.Image,
        color_grade: ColorGrade = ColorGrade.LUXURY_NEUTRAL,
    ) -> Image.Image:
        """Apply professional post-processing."""
        # Color grading
        image = self._apply_color_grade(image, color_grade)

        # Subtle sharpening for fabric detail
        image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

        # Subtle vignette for focus
        image = self._apply_subtle_vignette(image, strength=0.2)

        return image

    async def generate_luxury_shot(
        self,
        specs: GarmentSpecs,
        shot_type: ShotType = ShotType.HERO,
        lighting: LightingPreset = LightingPreset.STUDIO_DRAMATIC,
        reference_image: Image.Image | Path | None = None,
        use_controlnet: bool = False,
        use_refiner: bool = True,
        color_grade: ColorGrade = ColorGrade.LUXURY_NEUTRAL,
    ) -> Image.Image | None:
        """Generate a single luxury product shot.

        Multi-pass generation:
        1. Base generation with SDXL + LoRA
        2. Optional ControlNet for structure
        3. Refiner pass for detail
        4. Post-processing

        Args:
            specs: Garment specifications
            shot_type: Type of shot to generate
            lighting: Lighting preset
            reference_image: Optional reference for ControlNet
            use_controlnet: Whether to use ControlNet
            use_refiner: Whether to use SDXL refiner
            color_grade: Color grading profile

        Returns:
            Generated image or None on failure
        """
        from imagery.sdxl_pipeline import (
            ControlNetMode,
            GenerationConfig,
            GenerationQuality,
        )

        pipeline = self._get_pipeline()

        # Load SkyyRose LoRA if available
        lora_path = self.model_dir / "skyyrose-luxury-lora"
        if lora_path.exists() and not self._lora_loaded:
            pipeline.load_lora(lora_path, scale=0.8)
            self._lora_loaded = True

        # Build prompt
        prompt = self._build_luxury_prompt(specs, shot_type, lighting)
        negative_prompt = self._luxury_negative_prompt()

        # Configure generation
        config = GenerationConfig(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=1024,
            height=1024,
            num_inference_steps=80,
            guidance_scale=12.0,
            quality=GenerationQuality.ULTRA if use_refiner else GenerationQuality.HIGH,
            controlnet_mode=ControlNetMode.CANNY if use_controlnet else ControlNetMode.NONE,
            controlnet_conditioning_scale=0.8,
            use_refiner=use_refiner,
            refiner_strength=0.3,
        )

        # Generate
        result = await pipeline.generate(
            config,
            reference_image=reference_image if use_controlnet else None,
        )

        if not result.success or result.image is None:
            logger.error(f"Generation failed: {result.error}")
            return None

        # Post-process
        final_image = self._luxury_post_process(result.image, color_grade)

        return final_image

    async def generate_complete_product_suite(
        self,
        specs: GarmentSpecs,
        output_dir: Path | None = None,
        shots: list[ShotType] | None = None,
    ) -> PhotoSuite:
        """Generate complete luxury product photography suite.

        Args:
            specs: Garment specifications
            output_dir: Optional directory to save images
            shots: Specific shots to generate (default: all)

        Returns:
            PhotoSuite with all generated images
        """
        if shots is None:
            shots = list(ShotType)

        suite = PhotoSuite()

        # Shot configurations
        shot_configs = {
            ShotType.HERO: (LightingPreset.STUDIO_DRAMATIC, ColorGrade.LUXURY_NEUTRAL),
            ShotType.FRONT: (LightingPreset.STUDIO_FLAT, ColorGrade.LUXURY_NEUTRAL),
            ShotType.BACK: (LightingPreset.STUDIO_FLAT, ColorGrade.LUXURY_NEUTRAL),
            ShotType.SIDE_LEFT: (LightingPreset.STUDIO_CONTOUR, ColorGrade.LUXURY_NEUTRAL),
            ShotType.SIDE_RIGHT: (LightingPreset.STUDIO_CONTOUR, ColorGrade.LUXURY_NEUTRAL),
            ShotType.DETAIL_FABRIC: (LightingPreset.MACRO_CLOSEUP, ColorGrade.LUXURY_NEUTRAL),
            ShotType.DETAIL_CONSTRUCTION: (LightingPreset.MACRO_CLOSEUP, ColorGrade.LUXURY_NEUTRAL),
            ShotType.LIFESTYLE_URBAN: (LightingPreset.GOLDEN_HOUR, ColorGrade.WARM_ROMANTIC),
            ShotType.LIFESTYLE_LUXURY: (LightingPreset.AMBIENT_LUXURY, ColorGrade.COOL_EDITORIAL),
            ShotType.PACKAGING: (LightingPreset.SOFT_COMMERCIAL, ColorGrade.LUXURY_NEUTRAL),
        }

        # Collection-specific color grades
        collection_grades = {
            "BLACK_ROSE": ColorGrade.MOODY_NOIR,
            "black-rose": ColorGrade.MOODY_NOIR,
            "LOVE_HURTS": ColorGrade.WARM_ROMANTIC,
            "love-hurts": ColorGrade.WARM_ROMANTIC,
        }

        # Override color grade for collection if specified
        base_grade = collection_grades.get(specs.collection.upper().replace("-", "_"))

        for shot_type in shots:
            lighting, default_grade = shot_configs.get(
                shot_type, (LightingPreset.STUDIO_FLAT, ColorGrade.LUXURY_NEUTRAL)
            )

            # Use collection grade for hero/lifestyle, default for technical shots
            if shot_type in (ShotType.HERO, ShotType.LIFESTYLE_URBAN, ShotType.LIFESTYLE_LUXURY):
                grade = base_grade or default_grade
            else:
                grade = default_grade

            logger.info(f"Generating {shot_type.value} shot...")

            image = await self.generate_luxury_shot(
                specs=specs,
                shot_type=shot_type,
                lighting=lighting,
                color_grade=grade,
            )

            if image:
                setattr(suite, shot_type.value, image)

        # Save if output directory provided
        if output_dir:
            prefix = specs.name.lower().replace(" ", "_")
            saved = suite.save_all(output_dir, prefix)
            suite.metadata["saved_paths"] = {k: str(v) for k, v in saved.items()}

        return suite


__all__ = [
    "LuxuryProductPhotography",
    "GarmentSpecs",
    "PhotoSuite",
    "ShotType",
    "LightingPreset",
    "ColorGrade",
]
