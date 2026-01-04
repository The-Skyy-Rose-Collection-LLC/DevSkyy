"""SDXL Image Generation Pipeline.

High-fidelity product image generation using:
- Stable Diffusion XL Base + Refiner
- ControlNet (Canny, Depth) for structural accuracy
- IP-Adapter for style transfer
- Custom LoRA for SkyyRose brand consistency

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
from PIL import Image

logger = logging.getLogger(__name__)


class ControlNetMode(str, Enum):
    """ControlNet conditioning modes."""

    CANNY = "canny"
    DEPTH = "depth"
    NONE = "none"


class GenerationQuality(str, Enum):
    """Generation quality presets."""

    DRAFT = "draft"  # Fast, lower quality
    STANDARD = "standard"  # Balanced
    HIGH = "high"  # High quality, slower
    ULTRA = "ultra"  # Maximum quality with refiner


@dataclass
class GenerationConfig:
    """Configuration for image generation."""

    prompt: str
    negative_prompt: str = (
        "low quality, blurry, distorted, deformed, ugly, bad anatomy, "
        "watermark, text, logo, oversaturated, underexposed"
    )
    width: int = 1024
    height: int = 1024
    num_inference_steps: int = 30
    guidance_scale: float = 7.5
    quality: GenerationQuality = GenerationQuality.STANDARD
    controlnet_mode: ControlNetMode = ControlNetMode.NONE
    controlnet_conditioning_scale: float = 0.8
    use_refiner: bool = False
    refiner_strength: float = 0.3
    use_ip_adapter: bool = False
    ip_adapter_scale: float = 0.6
    lora_path: str | None = None
    lora_scale: float = 0.8
    seed: int | None = None


@dataclass
class GenerationResult:
    """Result of image generation."""

    success: bool
    image: Image.Image | None = None
    output_path: Path | None = None
    config: GenerationConfig | None = None
    generation_time_ms: float = 0.0
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class SDXLPipeline:
    """SDXL Image Generation Pipeline.

    Provides high-quality product image generation with:
    - ControlNet for structural guidance
    - IP-Adapter for style consistency
    - LoRA for brand-specific fine-tuning
    - Refiner for enhanced details

    Example:
        >>> pipeline = SDXLPipeline()
        >>> config = GenerationConfig(
        ...     prompt="Luxury black hoodie, SkyyRose style",
        ...     quality=GenerationQuality.HIGH,
        ...     use_refiner=True,
        ... )
        >>> result = await pipeline.generate(config)
    """

    MODEL_DIR = Path("models")

    def __init__(
        self,
        model_dir: Path | str | None = None,
        device: str = "auto",
        dtype: str = "float16",
    ) -> None:
        """Initialize SDXL pipeline.

        Args:
            model_dir: Directory containing downloaded models
            device: Device to use (auto, cuda, mps, cpu)
            dtype: Data type (float16, float32)
        """
        self.model_dir = Path(model_dir) if model_dir else self.MODEL_DIR
        self.device = self._resolve_device(device)
        self.dtype = dtype

        self._base_pipeline = None
        self._refiner_pipeline = None
        self._controlnet_canny = None
        self._controlnet_depth = None
        self._ip_adapter = None
        self._loaded_lora: str | None = None

        logger.info(f"SDXLPipeline initialized (device={self.device}, dtype={dtype})")

    def _resolve_device(self, device: str) -> str:
        """Resolve the best available device."""
        if device != "auto":
            return device

        try:
            import torch

            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass

        return "cpu"

    def _load_base_pipeline(self) -> None:
        """Lazy load the base SDXL pipeline."""
        if self._base_pipeline is not None:
            return

        try:
            import torch
            from diffusers import StableDiffusionXLPipeline

            model_path = self.model_dir / "sdxl-base"

            if not model_path.exists():
                logger.info("SDXL base not found locally, loading from HuggingFace...")
                model_path = "stabilityai/stable-diffusion-xl-base-1.0"

            dtype = torch.float16 if self.dtype == "float16" else torch.float32

            self._base_pipeline = StableDiffusionXLPipeline.from_pretrained(
                str(model_path),
                torch_dtype=dtype,
                variant="fp16" if dtype == torch.float16 else None,
                use_safetensors=True,
            ).to(self.device)

            # Enable memory optimizations
            if self.device == "cuda":
                self._base_pipeline.enable_xformers_memory_efficient_attention()

            logger.info("SDXL base pipeline loaded")

        except ImportError as e:
            raise ImportError(
                "SDXL dependencies not installed. Run: "
                "pip install diffusers transformers accelerate xformers"
            ) from e

    def _load_refiner(self) -> None:
        """Lazy load the SDXL refiner."""
        if self._refiner_pipeline is not None:
            return

        try:
            import torch
            from diffusers import StableDiffusionXLImg2ImgPipeline

            model_path = self.model_dir / "sdxl-refiner"

            if not model_path.exists():
                model_path = "stabilityai/stable-diffusion-xl-refiner-1.0"

            dtype = torch.float16 if self.dtype == "float16" else torch.float32

            self._refiner_pipeline = StableDiffusionXLImg2ImgPipeline.from_pretrained(
                str(model_path),
                torch_dtype=dtype,
                variant="fp16" if dtype == torch.float16 else None,
                use_safetensors=True,
            ).to(self.device)

            logger.info("SDXL refiner loaded")

        except ImportError as e:
            logger.warning(f"Could not load refiner: {e}")

    def _load_controlnet(self, mode: ControlNetMode) -> Any:
        """Lazy load ControlNet model."""
        try:
            import torch
            from diffusers import ControlNetModel

            if mode == ControlNetMode.CANNY:
                if self._controlnet_canny is None:
                    model_path = self.model_dir / "controlnet-canny"
                    if not model_path.exists():
                        model_path = "diffusers/controlnet-canny-sdxl-1.0"

                    dtype = torch.float16 if self.dtype == "float16" else torch.float32
                    self._controlnet_canny = ControlNetModel.from_pretrained(
                        str(model_path),
                        torch_dtype=dtype,
                    ).to(self.device)
                    logger.info("ControlNet Canny loaded")
                return self._controlnet_canny

            elif mode == ControlNetMode.DEPTH:
                if self._controlnet_depth is None:
                    model_path = self.model_dir / "controlnet-depth"
                    if not model_path.exists():
                        model_path = "diffusers/controlnet-depth-sdxl-1.0"

                    dtype = torch.float16 if self.dtype == "float16" else torch.float32
                    self._controlnet_depth = ControlNetModel.from_pretrained(
                        str(model_path),
                        torch_dtype=dtype,
                    ).to(self.device)
                    logger.info("ControlNet Depth loaded")
                return self._controlnet_depth

        except ImportError as e:
            logger.warning(f"Could not load ControlNet: {e}")
            return None

    def _extract_canny_edges(self, image: Image.Image) -> Image.Image:
        """Extract Canny edges from image for ControlNet."""
        import cv2

        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        edges_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        return Image.fromarray(edges_rgb)

    def _extract_depth(self, image: Image.Image) -> Image.Image:
        """Extract depth map from image for ControlNet."""
        try:
            from transformers import pipeline

            depth_estimator = pipeline("depth-estimation", model="Intel/dpt-large")
            result = depth_estimator(image)
            depth = result["depth"]
            return depth.convert("RGB")

        except ImportError:
            logger.warning("Depth estimation not available")
            return image

    def load_lora(self, lora_path: str | Path, scale: float = 0.8) -> None:
        """Load LoRA weights into the pipeline.

        Args:
            lora_path: Path to LoRA weights
            scale: LoRA influence scale (0-1)
        """
        self._load_base_pipeline()

        lora_path = Path(lora_path)
        if not lora_path.exists():
            logger.warning(f"LoRA not found: {lora_path}")
            return

        try:
            self._base_pipeline.load_lora_weights(str(lora_path))
            self._base_pipeline.fuse_lora(lora_scale=scale)
            self._loaded_lora = str(lora_path)
            logger.info(f"LoRA loaded: {lora_path} (scale={scale})")

        except Exception as e:
            logger.error(f"Failed to load LoRA: {e}")

    def unload_lora(self) -> None:
        """Unload currently loaded LoRA weights."""
        if self._base_pipeline and self._loaded_lora:
            self._base_pipeline.unfuse_lora()
            self._base_pipeline.unload_lora_weights()
            self._loaded_lora = None
            logger.info("LoRA unloaded")

    async def generate(
        self,
        config: GenerationConfig,
        reference_image: Image.Image | Path | None = None,
        output_path: Path | str | None = None,
    ) -> GenerationResult:
        """Generate an image using SDXL.

        Args:
            config: Generation configuration
            reference_image: Optional reference for ControlNet/IP-Adapter
            output_path: Optional path to save the result

        Returns:
            GenerationResult with generated image
        """
        import time

        start_time = time.time()

        try:
            import torch

            self._load_base_pipeline()

            # Set seed for reproducibility
            generator = None
            if config.seed is not None:
                generator = torch.Generator(device=self.device).manual_seed(config.seed)

            # Adjust steps based on quality
            steps = config.num_inference_steps
            if config.quality == GenerationQuality.DRAFT:
                steps = min(steps, 15)
            elif config.quality == GenerationQuality.ULTRA:
                steps = max(steps, 40)

            # Load LoRA if specified
            if config.lora_path and config.lora_path != self._loaded_lora:
                self.load_lora(config.lora_path, config.lora_scale)

            # Prepare ControlNet conditioning
            controlnet_image = None
            if config.controlnet_mode != ControlNetMode.NONE and reference_image:
                if isinstance(reference_image, (str, Path)):
                    reference_image = Image.open(reference_image).convert("RGB")

                if config.controlnet_mode == ControlNetMode.CANNY:
                    controlnet_image = self._extract_canny_edges(reference_image)
                elif config.controlnet_mode == ControlNetMode.DEPTH:
                    controlnet_image = self._extract_depth(reference_image)

            # Generate with base pipeline
            if controlnet_image and config.controlnet_mode != ControlNetMode.NONE:
                from diffusers import StableDiffusionXLControlNetPipeline

                controlnet = self._load_controlnet(config.controlnet_mode)
                if controlnet:
                    pipe = StableDiffusionXLControlNetPipeline.from_pipe(
                        self._base_pipeline,
                        controlnet=controlnet,
                    )
                    result = pipe(
                        prompt=config.prompt,
                        negative_prompt=config.negative_prompt,
                        image=controlnet_image,
                        width=config.width,
                        height=config.height,
                        num_inference_steps=steps,
                        guidance_scale=config.guidance_scale,
                        controlnet_conditioning_scale=config.controlnet_conditioning_scale,
                        generator=generator,
                    )
                    image = result.images[0]
                else:
                    # Fallback to base generation
                    result = self._base_pipeline(
                        prompt=config.prompt,
                        negative_prompt=config.negative_prompt,
                        width=config.width,
                        height=config.height,
                        num_inference_steps=steps,
                        guidance_scale=config.guidance_scale,
                        generator=generator,
                    )
                    image = result.images[0]
            else:
                result = self._base_pipeline(
                    prompt=config.prompt,
                    negative_prompt=config.negative_prompt,
                    width=config.width,
                    height=config.height,
                    num_inference_steps=steps,
                    guidance_scale=config.guidance_scale,
                    generator=generator,
                )
                image = result.images[0]

            # Apply refiner for high quality
            if config.use_refiner and config.quality in (
                GenerationQuality.HIGH,
                GenerationQuality.ULTRA,
            ):
                self._load_refiner()
                if self._refiner_pipeline:
                    refined = self._refiner_pipeline(
                        prompt=config.prompt,
                        negative_prompt=config.negative_prompt,
                        image=image,
                        strength=config.refiner_strength,
                        num_inference_steps=int(steps * 0.4),
                        generator=generator,
                    )
                    image = refined.images[0]

            # Save if path provided
            saved_path = None
            if output_path:
                saved_path = Path(output_path)
                saved_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(saved_path, quality=95)

            elapsed_ms = (time.time() - start_time) * 1000

            return GenerationResult(
                success=True,
                image=image,
                output_path=saved_path,
                config=config,
                generation_time_ms=elapsed_ms,
                metadata={
                    "device": self.device,
                    "dtype": self.dtype,
                    "actual_steps": steps,
                    "lora": self._loaded_lora,
                    "controlnet": config.controlnet_mode.value,
                    "used_refiner": config.use_refiner and self._refiner_pipeline is not None,
                },
            )

        except Exception as e:
            logger.exception(f"Generation failed: {e}")
            return GenerationResult(
                success=False,
                error=str(e),
                generation_time_ms=(time.time() - start_time) * 1000,
            )


class SkyyRosePromptBuilder:
    """Build prompts optimized for SkyyRose brand aesthetic."""

    BRAND_DNA = {
        "style": "luxury streetwear, Oakland culture, high-fashion editorial",
        "colors": "#B76E79 rose gold, #1A1A1A black, elegant neutrals",
        "mood": "bold, sophisticated, premium, empowering",
    }

    COLLECTION_STYLES = {
        "black-rose": "dark romantic, gothic elegance, midnight florals, sherpa texture",
        "love-hurts": "edgy romance, heart motifs, urban luxury, windbreaker aesthetic",
        "signature": "classic SkyyRose, rose gold accents, cotton candy pastels",
    }

    GARMENT_DETAILS = {
        "hoodie": "premium heavyweight hoodie, relaxed fit, embroidered details",
        "tee": "soft cotton tee, premium fabric, screen printed graphics",
        "shorts": "athletic shorts, comfortable fit, branded waistband",
        "cropped_hoodie": "cropped hoodie, feminine cut, modern silhouette",
        "beanie": "knit beanie, embroidered logo, cozy winter accessory",
        "sherpa": "sherpa jacket, plush fleece, streetwear luxury",
        "dress": "hooded dress, casual elegance, versatile styling",
        "bomber": "bomber jacket, satin finish, embroidered back panel",
        "windbreaker": "lightweight windbreaker, water resistant, retro athletic",
        "joggers": "jogger pants, tapered fit, side stripe detail",
        "accessory": "branded accessory, premium materials, functional luxury",
    }

    @classmethod
    def build_prompt(
        cls,
        product_name: str,
        garment_type: str,
        collection: str,
        additional_details: str = "",
    ) -> str:
        """Build an optimized prompt for product generation.

        Args:
            product_name: Name of the product
            garment_type: Type of garment (hoodie, tee, etc.)
            collection: Collection name (black-rose, love-hurts, signature)
            additional_details: Extra styling details

        Returns:
            Optimized prompt string
        """
        parts = [
            f"Professional product photography of {product_name}",
            cls.GARMENT_DETAILS.get(garment_type, garment_type),
            cls.COLLECTION_STYLES.get(collection, ""),
            cls.BRAND_DNA["style"],
            "studio lighting, white background, high resolution",
            "8k, commercial photography, fashion catalog",
        ]

        if additional_details:
            parts.append(additional_details)

        return ", ".join(filter(None, parts))

    @classmethod
    def build_negative_prompt(cls) -> str:
        """Build standard negative prompt."""
        return (
            "low quality, blurry, distorted, deformed, ugly, bad anatomy, "
            "watermark, text overlay, logo, oversaturated, underexposed, "
            "mannequin, model, person wearing, wrinkled fabric, dirty, stained, "
            "amateur photography, smartphone photo, cluttered background"
        )


__all__ = [
    "SDXLPipeline",
    "GenerationConfig",
    "GenerationResult",
    "GenerationQuality",
    "ControlNetMode",
    "SkyyRosePromptBuilder",
]
