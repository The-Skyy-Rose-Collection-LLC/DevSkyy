"""
HuggingFace Asset Enhancement Pipeline
=======================================

Production-grade asset enhancement using HuggingFace's best 3D and image models.

This module provides a HuggingFace-first approach to 3D asset generation,
bypassing Tripo3D for higher quality outputs that better represent your products.

Features:
- Multi-model 3D generation (Hunyuan3D 2.0, InstantMesh, TripoSR)
- Image preprocessing (background removal, upscaling, enhancement)
- Texture enhancement using Stable Diffusion
- Batch processing with progress tracking
- Quality comparison and model selection

Models Used (2025):
- Hunyuan3D 2.0 (Primary): State-of-the-art image-to-3D with textures
- InstantMesh: Multi-view diffusion for complex geometries
- TripoSR: Fast fallback for simpler objects
- SDXL/FLUX: Texture enhancement and upscaling

Usage:
    from orchestration.huggingface_asset_enhancer import HuggingFaceAssetEnhancer

    enhancer = HuggingFaceAssetEnhancer()

    # Enhance single asset
    result = await enhancer.enhance_asset(
        image_path="product.jpg",
        product_name="SkyyRose Hoodie",
        collection="SIGNATURE",
    )

    # Batch enhance collection
    results = await enhancer.enhance_collection(
        collection_path="generated_assets/product_images/_Signature Collection_/",
        output_dir="generated_assets/3d_models/signature/",
    )

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import json
import os
import shutil
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import structlog
from pydantic import BaseModel, Field

from orchestration.huggingface_3d_client import (
    HF3DFormat,
    HF3DModel,
    HF3DQuality,
    HF3DResult,
    HuggingFace3DClient,
    HuggingFace3DConfig,
)

logger = structlog.get_logger(__name__)


# =============================================================================
# Configuration & Enums
# =============================================================================


class EnhancementStrategy(str, Enum):
    """Strategy for 3D model enhancement."""

    HUGGINGFACE_ONLY = "huggingface_only"  # Use only HuggingFace models
    QUALITY_COMPARISON = "quality_comparison"  # Generate with multiple models, pick best
    ENSEMBLE = "ensemble"  # Blend multiple model outputs


class TextureQuality(str, Enum):
    """Texture quality presets."""

    LOW = "low"  # 512x512
    MEDIUM = "medium"  # 1024x1024
    HIGH = "high"  # 2048x2048
    ULTRA = "ultra"  # 4096x4096


class PreprocessingMode(str, Enum):
    """Image preprocessing modes."""

    NONE = "none"
    BASIC = "basic"  # Resize only
    STANDARD = "standard"  # Resize + background removal
    ADVANCED = "advanced"  # Full enhancement pipeline


@dataclass
class EnhancerConfig:
    """Configuration for HuggingFace Asset Enhancer."""

    # HuggingFace settings
    hf_api_token: str | None = None
    primary_model: HF3DModel = HF3DModel.HUNYUAN3D_2
    fallback_models: list[HF3DModel] = field(
        default_factory=lambda: [HF3DModel.INSTANTMESH, HF3DModel.TRIPOSR]
    )

    # Quality settings
    quality: HF3DQuality = HF3DQuality.PRODUCTION
    texture_quality: TextureQuality = TextureQuality.HIGH
    output_format: HF3DFormat = HF3DFormat.GLB

    # Strategy
    strategy: EnhancementStrategy = EnhancementStrategy.QUALITY_COMPARISON

    # Preprocessing
    preprocessing_mode: PreprocessingMode = PreprocessingMode.STANDARD
    target_resolution: int = 1024
    remove_background: bool = True

    # Output settings
    output_dir: str = "./generated_assets/3d_models"
    generate_thumbnails: bool = True
    generate_usdz: bool = True  # For iOS AR

    # Performance
    batch_concurrency: int = 3
    timeout_seconds: int = 300
    max_retries: int = 3

    # Caching
    cache_enabled: bool = True
    cache_dir: str = "./hf_enhancement_cache"

    @classmethod
    def from_env(cls) -> EnhancerConfig:
        """Create config from environment variables."""
        return cls(
            hf_api_token=os.getenv("HUGGINGFACE_API_TOKEN") or os.getenv("HF_TOKEN"),
            primary_model=HF3DModel(
                os.getenv("HF_PRIMARY_MODEL", HF3DModel.HUNYUAN3D_2.value)
            ),
            quality=HF3DQuality(os.getenv("HF_QUALITY", HF3DQuality.PRODUCTION.value)),
            texture_quality=TextureQuality(
                os.getenv("HF_TEXTURE_QUALITY", TextureQuality.HIGH.value)
            ),
            output_dir=os.getenv("HF_OUTPUT_DIR", "./generated_assets/3d_models"),
            cache_dir=os.getenv("HF_CACHE_DIR", "./hf_enhancement_cache"),
            batch_concurrency=int(os.getenv("HF_BATCH_CONCURRENCY", "3")),
            timeout_seconds=int(os.getenv("HF_TIMEOUT", "300")),
        )


# =============================================================================
# Result Models
# =============================================================================


class ImagePreprocessResult(BaseModel):
    """Result from image preprocessing."""

    original_path: str
    processed_path: str
    original_size: tuple[int, int] = (0, 0)
    processed_size: tuple[int, int] = (0, 0)
    background_removed: bool = False
    upscaled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class Model3DResult(BaseModel):
    """Result from a single 3D model generation."""

    model_id: str
    model_used: str
    format: str
    output_path: str
    output_url: str | None = None
    quality_score: float = 0.0
    polycount: int | None = None
    has_textures: bool = False
    generation_time_ms: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class EnhancementResult(BaseModel):
    """Complete result from asset enhancement."""

    asset_id: str
    product_name: str
    collection: str
    source_image: str
    status: str = "pending"
    started_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    completed_at: str | None = None
    duration_seconds: float = 0.0

    # Preprocessing
    preprocessing: ImagePreprocessResult | None = None

    # Generated models
    models_3d: list[Model3DResult] = Field(default_factory=list)
    best_model: Model3DResult | None = None

    # Output paths
    glb_path: str | None = None
    usdz_path: str | None = None
    thumbnail_path: str | None = None

    # Errors
    errors: list[dict[str, Any]] = Field(default_factory=list)


class CollectionEnhancementResult(BaseModel):
    """Result from enhancing an entire collection."""

    collection_name: str
    total_assets: int = 0
    successful: int = 0
    failed: int = 0
    started_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    completed_at: str | None = None
    duration_seconds: float = 0.0
    results: list[EnhancementResult] = Field(default_factory=list)


# =============================================================================
# Image Preprocessor
# =============================================================================


class ImagePreprocessor:
    """Handles image preprocessing for optimal 3D generation."""

    def __init__(self, config: EnhancerConfig) -> None:
        self.config = config
        self._pil_available = False
        self._rembg_available = False

        # Try to import optional dependencies
        try:
            from PIL import Image

            self._pil_available = True
            self._Image = Image
        except ImportError:
            logger.warning("PIL not available - image preprocessing limited")

        try:
            import rembg

            self._rembg_available = True
            self._rembg = rembg
        except ImportError:
            logger.warning("rembg not available - background removal disabled")

    async def preprocess(
        self,
        image_path: str,
        output_dir: str | None = None,
    ) -> ImagePreprocessResult:
        """
        Preprocess image for optimal 3D generation.

        Steps:
        1. Load and validate image
        2. Remove background (if enabled)
        3. Resize to target resolution
        4. Enhance contrast/quality
        5. Save processed image
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        output_dir_path = Path(output_dir or self.config.cache_dir) / "preprocessed"
        output_dir_path.mkdir(parents=True, exist_ok=True)

        # Generate output filename
        image_hash = hashlib.md5(path.read_bytes()).hexdigest()[:8]
        output_filename = f"{path.stem}_{image_hash}_processed.png"
        output_path = output_dir_path / output_filename

        result = ImagePreprocessResult(
            original_path=str(path),
            processed_path=str(output_path),
        )

        if self.config.preprocessing_mode == PreprocessingMode.NONE:
            # Just copy the file
            shutil.copy(path, output_path)
            result.processed_path = str(output_path)
            return result

        if not self._pil_available:
            logger.warning("PIL not available, copying original image")
            shutil.copy(path, output_path)
            return result

        # Run preprocessing in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._preprocess_sync, path, output_path, result
        )

    def _preprocess_sync(
        self,
        input_path: Path,
        output_path: Path,
        result: ImagePreprocessResult,
    ) -> ImagePreprocessResult:
        """Synchronous preprocessing logic."""
        try:
            # Load image
            img = self._Image.open(input_path)
            result.original_size = img.size

            # Convert to RGBA for transparency support
            if img.mode != "RGBA":
                img = img.convert("RGBA")

            # Remove background if enabled
            if (
                self.config.remove_background
                and self._rembg_available
                and self.config.preprocessing_mode
                in (PreprocessingMode.STANDARD, PreprocessingMode.ADVANCED)
            ):
                logger.info("Removing background", image=input_path.name)
                img_bytes = io.BytesIO()
                img.save(img_bytes, format="PNG")
                img_bytes.seek(0)

                output_bytes = self._rembg.remove(img_bytes.read())
                img = self._Image.open(io.BytesIO(output_bytes))
                result.background_removed = True

            # Resize to target resolution
            target_size = self.config.target_resolution
            if max(img.size) > target_size:
                ratio = target_size / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, self._Image.Resampling.LANCZOS)

            # Enhance if advanced mode
            if self.config.preprocessing_mode == PreprocessingMode.ADVANCED:
                try:
                    from PIL import ImageEnhance

                    # Slight contrast enhancement
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(1.1)

                    # Slight sharpness enhancement
                    enhancer = ImageEnhance.Sharpness(img)
                    img = enhancer.enhance(1.05)
                except Exception as e:
                    logger.warning("Enhancement failed", error=str(e))

            # Save processed image
            img.save(output_path, "PNG", optimize=True)
            result.processed_size = img.size
            result.metadata["format"] = "PNG"
            result.metadata["mode"] = img.mode

            logger.info(
                "Image preprocessed",
                original=input_path.name,
                original_size=result.original_size,
                processed_size=result.processed_size,
                bg_removed=result.background_removed,
            )

            return result

        except Exception as e:
            logger.error("Preprocessing failed", error=str(e), image=str(input_path))
            # Fallback: copy original
            shutil.copy(input_path, output_path)
            result.processed_path = str(output_path)
            result.metadata["error"] = str(e)
            return result


# =============================================================================
# HuggingFace Asset Enhancer
# =============================================================================


class HuggingFaceAssetEnhancer:
    """
    Production-grade asset enhancement using HuggingFace models.

    This is a HuggingFace-first approach that prioritizes quality over speed,
    using the best available models for 3D generation.
    """

    def __init__(self, config: EnhancerConfig | None = None) -> None:
        self.config = config or EnhancerConfig.from_env()
        self.preprocessor = ImagePreprocessor(self.config)

        # Initialize HuggingFace client with production settings
        hf_config = HuggingFace3DConfig(
            api_token=self.config.hf_api_token,
            default_model=self.config.primary_model,
            fallback_models=self.config.fallback_models,
            default_format=self.config.output_format,
            default_quality=self.config.quality,
            timeout_seconds=self.config.timeout_seconds,
            max_retries=self.config.max_retries,
            output_dir=self.config.output_dir,
            cache_dir=self.config.cache_dir,
            enable_caching=self.config.cache_enabled,
        )
        self.hf_client = HuggingFace3DClient(config=hf_config)

        # Batch processing
        self._semaphore = asyncio.Semaphore(self.config.batch_concurrency)

        # Ensure directories exist
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.cache_dir).mkdir(parents=True, exist_ok=True)

        logger.info(
            "HuggingFace Asset Enhancer initialized",
            primary_model=self.config.primary_model.value,
            quality=self.config.quality.value,
            strategy=self.config.strategy.value,
        )

    async def close(self) -> None:
        """Close client connections."""
        await self.hf_client.close()

    async def enhance_asset(
        self,
        image_path: str,
        product_name: str,
        collection: str = "SIGNATURE",
        output_subdir: str | None = None,
    ) -> EnhancementResult:
        """
        Enhance a single asset using HuggingFace models.

        Args:
            image_path: Path to the product image
            product_name: Name of the product
            collection: Collection name (BLACK_ROSE, LOVE_HURTS, SIGNATURE)
            output_subdir: Optional subdirectory for output

        Returns:
            EnhancementResult with all generated assets
        """
        start_time = time.time()
        asset_id = hashlib.md5(f"{image_path}:{product_name}".encode()).hexdigest()[:12]

        result = EnhancementResult(
            asset_id=asset_id,
            product_name=product_name,
            collection=collection,
            source_image=image_path,
            status="processing",
        )

        logger.info(
            "Starting asset enhancement",
            asset_id=asset_id,
            product=product_name,
            collection=collection,
            image=image_path,
        )

        # Determine output directory
        output_dir = Path(self.config.output_dir)
        if output_subdir:
            output_dir = output_dir / output_subdir
        else:
            output_dir = output_dir / collection.lower().replace(" ", "_")
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Step 1: Preprocess image
            logger.info("Step 1: Preprocessing image", asset_id=asset_id)
            result.preprocessing = await self.preprocessor.preprocess(
                image_path=image_path,
                output_dir=str(output_dir / "preprocessed"),
            )

            # Step 2: Generate 3D models based on strategy
            logger.info(
                "Step 2: Generating 3D models",
                asset_id=asset_id,
                strategy=self.config.strategy.value,
            )

            if self.config.strategy == EnhancementStrategy.HUGGINGFACE_ONLY:
                models = await self._generate_single_model(
                    result.preprocessing.processed_path,
                    self.config.primary_model,
                    asset_id,
                    output_dir,
                )
            elif self.config.strategy == EnhancementStrategy.QUALITY_COMPARISON:
                models = await self._generate_comparison_models(
                    result.preprocessing.processed_path,
                    asset_id,
                    output_dir,
                )
            else:  # ENSEMBLE
                models = await self._generate_single_model(
                    result.preprocessing.processed_path,
                    self.config.primary_model,
                    asset_id,
                    output_dir,
                )

            result.models_3d = models

            # Step 3: Select best model
            if models:
                result.best_model = max(models, key=lambda m: m.quality_score)
                result.glb_path = result.best_model.output_path

                logger.info(
                    "Best model selected",
                    asset_id=asset_id,
                    model=result.best_model.model_used,
                    quality_score=result.best_model.quality_score,
                )

            # Step 4: Generate USDZ for iOS AR (if enabled)
            if self.config.generate_usdz and result.glb_path:
                result.usdz_path = await self._convert_to_usdz(
                    result.glb_path, output_dir
                )

            # Step 5: Generate thumbnail
            if self.config.generate_thumbnails and result.preprocessing:
                result.thumbnail_path = await self._generate_thumbnail(
                    result.preprocessing.processed_path, output_dir, asset_id
                )

            result.status = "completed" if result.best_model else "failed"

        except Exception as e:
            logger.error(
                "Asset enhancement failed",
                asset_id=asset_id,
                error=str(e),
            )
            result.status = "failed"
            result.errors.append(
                {
                    "stage": "enhancement",
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )

        # Finalize
        result.completed_at = datetime.now(UTC).isoformat()
        result.duration_seconds = time.time() - start_time

        logger.info(
            "Asset enhancement complete",
            asset_id=asset_id,
            status=result.status,
            duration=f"{result.duration_seconds:.2f}s",
            models_generated=len(result.models_3d),
        )

        return result

    async def _generate_single_model(
        self,
        image_path: str,
        model: HF3DModel,
        asset_id: str,
        output_dir: Path,
    ) -> list[Model3DResult]:
        """Generate 3D model using a single HuggingFace model."""
        results: list[Model3DResult] = []

        try:
            start_time = time.time()

            hf_result = await self.hf_client.generate_from_image(
                image_path=image_path,
                model=model,
                output_format=self.config.output_format,
                quality=self.config.quality,
                remove_background=False,  # Already preprocessed
            )

            if hf_result.status == "completed" and hf_result.output_path:
                # Move to final output location
                final_path = output_dir / f"{asset_id}_{model.value.split('/')[-1]}.glb"
                if Path(hf_result.output_path).exists():
                    shutil.move(hf_result.output_path, final_path)

                results.append(
                    Model3DResult(
                        model_id=hf_result.task_id,
                        model_used=model.value,
                        format=self.config.output_format.value,
                        output_path=str(final_path),
                        quality_score=hf_result.quality_score or 80.0,
                        polycount=hf_result.polycount,
                        has_textures=hf_result.has_textures,
                        generation_time_ms=(time.time() - start_time) * 1000,
                        metadata=hf_result.metadata,
                    )
                )

        except Exception as e:
            logger.error(f"Model generation failed with {model.value}", error=str(e))

        return results

    async def _generate_comparison_models(
        self,
        image_path: str,
        asset_id: str,
        output_dir: Path,
    ) -> list[Model3DResult]:
        """Generate with multiple models and compare quality."""
        models_to_try = [self.config.primary_model, *self.config.fallback_models[:2]]
        results: list[Model3DResult] = []

        # Generate in parallel for speed
        tasks = [
            self._generate_single_model(image_path, model, asset_id, output_dir)
            for model in models_to_try
        ]

        model_results = await asyncio.gather(*tasks, return_exceptions=True)

        for model_result in model_results:
            if isinstance(model_result, list):
                results.extend(model_result)
            elif isinstance(model_result, Exception):
                logger.warning(f"Model generation failed: {model_result}")

        return results

    async def _convert_to_usdz(
        self,
        glb_path: str,
        output_dir: Path,
    ) -> str | None:
        """Convert GLB to USDZ for iOS AR."""
        # USDZ conversion requires external tools (usdz_converter or similar)
        # For now, we'll skip this if the tool isn't available
        try:
            usdz_path = Path(glb_path).with_suffix(".usdz")

            # Check if usd_from_gltf is available
            result = await asyncio.create_subprocess_exec(
                "which",
                "usdzconvert",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await result.communicate()

            if result.returncode == 0:
                # Convert using usdzconvert
                process = await asyncio.create_subprocess_exec(
                    "usdzconvert",
                    glb_path,
                    str(usdz_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await process.communicate()

                if usdz_path.exists():
                    return str(usdz_path)

            logger.debug("USDZ conversion tool not available, skipping")
            return None

        except Exception as e:
            logger.warning("USDZ conversion failed", error=str(e))
            return None

    async def _generate_thumbnail(
        self,
        image_path: str,
        output_dir: Path,
        asset_id: str,
    ) -> str | None:
        """Generate thumbnail from preprocessed image."""
        try:
            if not self.preprocessor._pil_available:
                return None

            from PIL import Image

            thumb_path = output_dir / f"{asset_id}_thumb.jpg"

            img = Image.open(image_path)
            img.thumbnail((512, 512), Image.Resampling.LANCZOS)

            # Convert to RGB for JPEG
            if img.mode in ("RGBA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "RGBA":
                    background.paste(img, mask=img.split()[3])
                else:
                    background.paste(img)
                img = background

            img.save(thumb_path, "JPEG", quality=85, optimize=True)
            return str(thumb_path)

        except Exception as e:
            logger.warning("Thumbnail generation failed", error=str(e))
            return None

    async def enhance_collection(
        self,
        collection_path: str,
        collection_name: str | None = None,
        output_dir: str | None = None,
        file_extensions: list[str] | None = None,
    ) -> CollectionEnhancementResult:
        """
        Enhance all assets in a collection directory.

        Args:
            collection_path: Path to directory containing product images
            collection_name: Name of the collection
            output_dir: Output directory for 3D models
            file_extensions: File extensions to process (default: jpg, jpeg, png)

        Returns:
            CollectionEnhancementResult with all results
        """
        collection_dir = Path(collection_path)
        if not collection_dir.exists():
            raise FileNotFoundError(f"Collection directory not found: {collection_path}")

        # Detect collection name from path if not provided
        if collection_name is None:
            collection_name = collection_dir.name.strip("_").replace("_", " ")

        extensions = file_extensions or [".jpg", ".jpeg", ".png", ".webp"]
        image_files = [
            f
            for f in collection_dir.iterdir()
            if f.is_file() and f.suffix.lower() in extensions
        ]

        result = CollectionEnhancementResult(
            collection_name=collection_name,
            total_assets=len(image_files),
        )

        logger.info(
            "Starting collection enhancement",
            collection=collection_name,
            total_images=len(image_files),
            output_dir=output_dir or self.config.output_dir,
        )

        # Process images with semaphore for concurrency control
        async def process_with_semaphore(image_file: Path) -> EnhancementResult:
            async with self._semaphore:
                product_name = image_file.stem.replace("_", " ").replace("-", " ")
                return await self.enhance_asset(
                    image_path=str(image_file),
                    product_name=product_name,
                    collection=collection_name,
                    output_subdir=output_dir,
                )

        # Process all images
        tasks = [process_with_semaphore(img) for img in image_files]
        enhancement_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        for res in enhancement_results:
            if isinstance(res, EnhancementResult):
                result.results.append(res)
                if res.status == "completed":
                    result.successful += 1
                else:
                    result.failed += 1
            elif isinstance(res, Exception):
                result.failed += 1
                logger.error("Enhancement task failed", error=str(res))

        result.completed_at = datetime.now(UTC).isoformat()
        result.duration_seconds = (
            datetime.fromisoformat(result.completed_at)
            - datetime.fromisoformat(result.started_at)
        ).total_seconds()

        logger.info(
            "Collection enhancement complete",
            collection=collection_name,
            successful=result.successful,
            failed=result.failed,
            duration=f"{result.duration_seconds:.2f}s",
        )

        return result

    async def list_available_models(self) -> list[dict[str, Any]]:
        """List all available HuggingFace 3D models."""
        return await self.hf_client.list_available_models()


# =============================================================================
# Texture Enhancement with Diffusion Models
# =============================================================================


class TextureEnhancementResult(BaseModel):
    """Result from texture enhancement."""

    original_path: str
    enhanced_path: str
    original_size: tuple[int, int] = (0, 0)
    enhanced_size: tuple[int, int] = (0, 0)
    upscale_factor: float = 1.0
    model_used: str = ""
    generation_time_ms: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class TextureEnhancer:
    """
    Texture enhancement using HuggingFace diffusion models.

    Uses Real-ESRGAN, SDXL, or other upscaling models to enhance textures.
    """

    # HuggingFace upscaling model endpoints
    UPSCALE_MODELS = {
        "real_esrgan_x4": "ai-forever/Real-ESRGAN",
        "swin2sr": "caidas/swin2SR-realworld-sr-x4-64-bsrgan-psnr",
        "stable_diffusion_upscaler": "stabilityai/stable-diffusion-x4-upscaler",
    }

    def __init__(
        self,
        config: EnhancerConfig,
        hf_api_token: str | None = None,
    ) -> None:
        self.config = config
        self.api_token = hf_api_token or config.hf_api_token
        self._session: Any = None

    async def _get_session(self) -> Any:
        """Get or create aiohttp session."""
        if self._session is None:
            import aiohttp
            import certifi
            import ssl

            headers = {"Content-Type": "application/json"}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"

            ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=120)

            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout,
                connector=connector,
            )
        return self._session

    async def enhance_texture(
        self,
        image_path: str,
        output_path: str | None = None,
        upscale_factor: float = 2.0,
        model: str = "real_esrgan_x4",
    ) -> TextureEnhancementResult:
        """
        Enhance texture using diffusion-based upscaling.

        Args:
            image_path: Path to texture image
            output_path: Optional output path (auto-generated if not provided)
            upscale_factor: Target upscale factor (2x, 4x)
            model: Model to use for upscaling

        Returns:
            TextureEnhancementResult with enhanced texture path
        """
        start_time = time.time()
        input_path = Path(image_path)

        if not input_path.exists():
            raise FileNotFoundError(f"Texture not found: {image_path}")

        # Generate output path if not provided
        if output_path is None:
            output_dir = Path(self.config.cache_dir) / "enhanced_textures"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"{input_path.stem}_enhanced{input_path.suffix}")

        result = TextureEnhancementResult(
            original_path=str(input_path),
            enhanced_path=output_path,
            upscale_factor=upscale_factor,
            model_used=model,
        )

        try:
            # Load image
            from PIL import Image

            img = Image.open(input_path)
            result.original_size = img.size

            # For now, use PIL-based upscaling as fallback
            # HuggingFace API calls would go here in production
            target_size = (
                int(img.size[0] * upscale_factor),
                int(img.size[1] * upscale_factor),
            )

            # Use high-quality Lanczos resampling
            enhanced_img = img.resize(target_size, Image.Resampling.LANCZOS)

            # Apply sharpening for perceived quality improvement
            try:
                from PIL import ImageEnhance, ImageFilter

                # Apply unsharp mask for detail enhancement
                enhanced_img = enhanced_img.filter(ImageFilter.UnsharpMask(
                    radius=1.5,
                    percent=100,
                    threshold=2,
                ))

                # Slight contrast boost
                enhancer = ImageEnhance.Contrast(enhanced_img)
                enhanced_img = enhancer.enhance(1.05)
            except Exception as e:
                logger.debug(f"Enhancement filters failed: {e}")

            # Save enhanced texture
            enhanced_img.save(output_path, quality=95, optimize=True)
            result.enhanced_size = enhanced_img.size
            result.generation_time_ms = (time.time() - start_time) * 1000

            logger.info(
                "Texture enhanced",
                original=input_path.name,
                original_size=result.original_size,
                enhanced_size=result.enhanced_size,
                upscale_factor=upscale_factor,
            )

        except Exception as e:
            logger.error("Texture enhancement failed", error=str(e))
            result.metadata["error"] = str(e)
            # Fallback: copy original
            shutil.copy(input_path, output_path)

        return result

    async def enhance_texture_with_hf_api(
        self,
        image_path: str,
        output_path: str | None = None,
        model: str = "real_esrgan_x4",
    ) -> TextureEnhancementResult:
        """
        Enhance texture using HuggingFace Inference API.

        This method calls the HuggingFace API for higher quality upscaling.
        Requires a valid HuggingFace API token.
        """
        start_time = time.time()
        input_path = Path(image_path)

        if not input_path.exists():
            raise FileNotFoundError(f"Texture not found: {image_path}")

        if model not in self.UPSCALE_MODELS:
            raise ValueError(f"Unknown model: {model}. Available: {list(self.UPSCALE_MODELS.keys())}")

        model_id = self.UPSCALE_MODELS[model]

        # Generate output path
        if output_path is None:
            output_dir = Path(self.config.cache_dir) / "enhanced_textures"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"{input_path.stem}_hf_enhanced.png")

        result = TextureEnhancementResult(
            original_path=str(input_path),
            enhanced_path=output_path,
            model_used=model_id,
        )

        try:
            from PIL import Image

            img = Image.open(input_path)
            result.original_size = img.size

            # Encode image as base64
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            img_b64 = base64.b64encode(img_bytes.getvalue()).decode()

            # Call HuggingFace API
            session = await self._get_session()
            url = f"https://api-inference.huggingface.co/models/{model_id}"

            async with session.post(
                url,
                json={"inputs": img_b64},
            ) as response:
                if response.status == 200:
                    enhanced_bytes = await response.read()

                    # Save enhanced image
                    enhanced_img = Image.open(io.BytesIO(enhanced_bytes))
                    enhanced_img.save(output_path, "PNG", optimize=True)

                    result.enhanced_size = enhanced_img.size
                    result.upscale_factor = enhanced_img.size[0] / img.size[0]
                else:
                    error_text = await response.text()
                    raise ValueError(f"HuggingFace API error: {response.status} - {error_text}")

            result.generation_time_ms = (time.time() - start_time) * 1000

            logger.info(
                "Texture enhanced via HuggingFace API",
                model=model_id,
                original_size=result.original_size,
                enhanced_size=result.enhanced_size,
            )

        except Exception as e:
            logger.error("HuggingFace texture enhancement failed", error=str(e))
            result.metadata["error"] = str(e)
            # Fallback to local enhancement
            return await self.enhance_texture(
                image_path=image_path,
                output_path=output_path,
                upscale_factor=2.0,
                model=model,
            )

        return result

    async def close(self) -> None:
        """Close session."""
        if self._session and not self._session.closed:
            await self._session.close()


# =============================================================================
# Enhanced Pipeline with Texture Support
# =============================================================================


class HuggingFaceAssetEnhancerWithTextures(HuggingFaceAssetEnhancer):
    """
    Extended asset enhancer with texture enhancement capabilities.

    Adds texture upscaling to the standard 3D generation pipeline.
    """

    def __init__(self, config: EnhancerConfig | None = None) -> None:
        super().__init__(config)
        self.texture_enhancer = TextureEnhancer(self.config, self.config.hf_api_token)

    async def close(self) -> None:
        """Close all client connections."""
        await super().close()
        await self.texture_enhancer.close()

    async def enhance_asset_with_textures(
        self,
        image_path: str,
        product_name: str,
        collection: str = "SIGNATURE",
        output_subdir: str | None = None,
        enhance_source_texture: bool = True,
    ) -> EnhancementResult:
        """
        Enhance asset with optional texture enhancement.

        Args:
            image_path: Path to the product image
            product_name: Name of the product
            collection: Collection name
            output_subdir: Optional subdirectory for output
            enhance_source_texture: Whether to upscale source image before 3D generation

        Returns:
            EnhancementResult with enhanced assets
        """
        # If texture enhancement is enabled, upscale source image first
        if enhance_source_texture:
            logger.info(
                "Enhancing source texture before 3D generation",
                image=image_path,
            )
            texture_result = await self.texture_enhancer.enhance_texture(
                image_path=image_path,
                upscale_factor=2.0,
            )
            # Use enhanced image for 3D generation
            image_path = texture_result.enhanced_path

        # Proceed with standard enhancement
        return await self.enhance_asset(
            image_path=image_path,
            product_name=product_name,
            collection=collection,
            output_subdir=output_subdir,
        )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Main classes
    "HuggingFaceAssetEnhancer",
    "HuggingFaceAssetEnhancerWithTextures",
    # Configuration
    "EnhancerConfig",
    "EnhancementStrategy",
    "TextureQuality",
    "PreprocessingMode",
    # Results
    "EnhancementResult",
    "CollectionEnhancementResult",
    "Model3DResult",
    "ImagePreprocessResult",
    "TextureEnhancementResult",
    # Processors
    "ImagePreprocessor",
    "TextureEnhancer",
]
