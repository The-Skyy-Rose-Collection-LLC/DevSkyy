"""
HuggingFace 3D Model Integration
================================

Production-ready integration with HuggingFace's top 3D generation models.

Supported Models (2025):
- Hunyuan3D 2.0 (Tencent): State-of-the-art text/image to 3D
- TripoSR: Fast, high-quality image-to-3D meshes
- Shap-E (OpenAI): Balanced quality/speed for 3D generation
- LGM: 3D Gaussian splatting
- Point-E: Fast point cloud generation

Architecture (Hybrid Approach):
1. Stage 0: HuggingFace generates initial 3D representation
2. Stage 1: Analyze output to optimize prompts for Tripo3D
3. Stage 2: Tripo3D generates production-quality 3D model

Usage:
    from orchestration.huggingface_3d_client import HuggingFace3DClient

    client = HuggingFace3DClient(api_token="hf_xxx")

    # Generate from text
    result = await client.generate_from_text(
        prompt="SkyyRose signature hoodie in rose gold",
        model=HF3DModel.HUNYUAN3D_2,
    )

    # Generate from image
    result = await client.generate_from_image(
        image_path="product.jpg",
        model=HF3DModel.TRIPOSR,
    )

Author: DevSkyy Platform Team
Version: 2.0.0
"""

from __future__ import annotations

import asyncio
import base64
import os
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import aiohttp
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

# HuggingFace API endpoints
HF_API_BASE = "https://api-inference.huggingface.co/models"
HF_SPACES_BASE = "https://huggingface.co/spaces"


class HF3DModel(str, Enum):
    """Available HuggingFace 3D models - 2025 Edition."""

    # Tencent Models (State-of-the-art)
    HUNYUAN3D_2 = "tencent/Hunyuan3D-2"  # Best quality, text/image-to-3D
    HUNYUAN3D_1 = "tencent/Hunyuan3D-1"  # Previous version

    # TripoSR (Fast, High-Quality Meshes)
    TRIPOSR = "stabilityai/TripoSR"  # Fast image-to-3D
    TRIPOSR_TURBO = "stabilityai/TripoSR-turbo"  # Faster variant

    # OpenAI Models
    SHAP_E_TEXT = "openai/shap-e"  # Text-to-3D
    SHAP_E_IMG = "openai/shap-e-img2img"  # Image-to-3D (legacy)
    POINT_E = "openai/point-e"  # Point cloud generation

    # LGM (Gaussian Splatting)
    LGM = "dylanebert/LGM-full"  # 3D Gaussian splatting

    # InstantMesh (Single Image to 3D)
    INSTANTMESH = "TencentARC/InstantMesh"  # Multi-view diffusion

    # Custom/Community Models
    CUSTOM = "custom"  # For user-specified models


class HF3DFormat(str, Enum):
    """Output formats for HuggingFace 3D generation."""

    PLY = "ply"  # Point cloud / mesh format
    OBJ = "obj"  # Wavefront OBJ mesh
    GLB = "glb"  # glTF binary (web-ready)
    GLTF = "gltf"  # glTF JSON
    STL = "stl"  # Stereolithography
    SPLAT = "splat"  # Gaussian splatting
    NPZ = "npz"  # NumPy compressed (for processing)


class HF3DQuality(str, Enum):
    """Quality presets for 3D generation."""

    DRAFT = "draft"  # Fast, low quality
    STANDARD = "standard"  # Balanced
    HIGH = "high"  # Higher quality, slower
    PRODUCTION = "production"  # Best quality, slowest


@dataclass
class HuggingFace3DConfig:
    """Configuration for HuggingFace 3D client."""

    # API Authentication
    api_token: str | None = None
    api_key: str | None = None

    # Model Selection
    default_model: HF3DModel = HF3DModel.TRIPOSR
    fallback_models: list[HF3DModel] = field(
        default_factory=lambda: [HF3DModel.SHAP_E_IMG, HF3DModel.POINT_E]
    )
    custom_model_id: str | None = None  # For HF3DModel.CUSTOM

    # Generation Settings (Production-Grade Defaults)
    default_format: HF3DFormat = HF3DFormat.GLB
    default_quality: HF3DQuality = HF3DQuality.PRODUCTION  # Highest quality
    guidance_scale: float = 17.5  # Higher for better detail
    num_inference_steps: int = 64  # More steps for quality
    seed: int | None = None  # For reproducibility

    # Hunyuan3D specific (Production-Grade)
    hunyuan_resolution: int = 1024  # Higher resolution for production
    hunyuan_remove_bg: bool = True

    # TripoSR specific (Production-Grade)
    triposr_foreground_ratio: float = 0.90  # Higher ratio for better capture
    triposr_mc_resolution: int = 512  # Higher mesh resolution

    # Output Settings
    output_dir: str = "./generated_3d_models"
    cache_enabled: bool = True
    cache_dir: str = "./hf_3d_cache"

    # Performance Settings
    timeout_seconds: int = 120
    max_retries: int = 3
    retry_delay: float = 2.0
    concurrent_limit: int = 3

    # Feature Flags
    enable_optimization_hints: bool = True
    enable_caching: bool = True
    enable_quality_metrics: bool = True
    enable_fallback_chain: bool = True
    enable_background_removal: bool = True

    @classmethod
    def from_env(cls) -> HuggingFace3DConfig:
        """Create config from environment variables with production-grade defaults."""
        return cls(
            api_token=os.getenv("HUGGINGFACE_API_TOKEN") or os.getenv("HF_TOKEN"),
            api_key=os.getenv("HF_API_KEY"),
            default_model=HF3DModel(os.getenv("HF_3D_DEFAULT_MODEL", HF3DModel.TRIPOSR.value)),
            default_format=HF3DFormat(os.getenv("HF_3D_FORMAT", HF3DFormat.GLB.value)),
            # Production quality by default
            default_quality=HF3DQuality(os.getenv("HF_3D_QUALITY", HF3DQuality.PRODUCTION.value)),
            guidance_scale=float(os.getenv("HF_GUIDANCE_SCALE", "17.5")),  # Higher for quality
            num_inference_steps=int(os.getenv("HF_INFERENCE_STEPS", "64")),  # More steps
            output_dir=os.getenv("HF_3D_OUTPUT_DIR", "./generated_3d_models"),
            cache_dir=os.getenv("HF_3D_CACHE_DIR", "./hf_3d_cache"),
            timeout_seconds=int(os.getenv("HF_TIMEOUT_SECONDS", "180")),  # Longer for quality
            enable_optimization_hints=(os.getenv("HF_ENABLE_HINTS", "true").lower() == "true"),
        )


class HF3DResult(BaseModel):
    """Result from HuggingFace 3D generation."""

    task_id: str
    model_used: HF3DModel
    format: HF3DFormat
    output_path: str | None = None
    output_url: str | None = None
    output_bytes: bytes | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    generation_time_ms: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    # Quality metrics
    quality_score: float | None = None
    polycount: int | None = None
    texture_complexity: str | None = None
    has_textures: bool = False

    # Optimization hints for downstream processing
    optimization_hints: str | None = None
    tripo3d_prompt: str | None = None

    # Status
    status: str = "pending"  # pending, processing, completed, failed
    error_message: str | None = None

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class HF3DOptimizationHints(BaseModel):
    """Optimization hints derived from HF 3D generation."""

    detected_geometry: str
    detected_complexity: str
    suggested_tripo_prompt: str
    confidence_score: float
    mesh_analysis: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class HuggingFace3DClient:
    """
    Production-ready client for HuggingFace 3D model generation.

    Features:
    - Multi-model support (Hunyuan3D, TripoSR, Shap-E, LGM)
    - Automatic fallback chain on failures
    - Result caching and rate limiting
    - Quality metrics and optimization hints
    - Async/await for high throughput
    """

    def __init__(self, config: HuggingFace3DConfig | None = None) -> None:
        """Initialize HuggingFace 3D client."""
        self.config = config or HuggingFace3DConfig.from_env()
        self._session: aiohttp.ClientSession | None = None
        self._semaphore = asyncio.Semaphore(self.config.concurrent_limit)
        self._cache: dict[str, HF3DResult] = {}

        # Validate API token
        if not self.config.api_token and not self.config.api_key:
            logger.warning(
                "HuggingFace API token not configured. "
                "Some features may not work. "
                "Set HUGGINGFACE_API_TOKEN or HF_TOKEN environment variable."
            )

        # Ensure output directories exist
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
        if self.config.cache_enabled:
            Path(self.config.cache_dir).mkdir(parents=True, exist_ok=True)

        logger.info(
            "HuggingFace 3D client initialized",
            model=self.config.default_model.value,
            format=self.config.default_format.value,
            cache_enabled=self.config.cache_enabled,
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            headers = {"Content-Type": "application/json"}
            token = self.config.api_token or self.config.api_key
            if token:
                headers["Authorization"] = f"Bearer {token}"

            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            self._session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self._session

    async def generate_from_text(
        self,
        prompt: str,
        model: HF3DModel | None = None,
        output_format: HF3DFormat | None = None,
        quality: HF3DQuality | None = None,
        guidance_scale: float | None = None,
        seed: int | None = None,
    ) -> HF3DResult:
        """
        Generate 3D model from text prompt.

        Args:
            prompt: Text description of the 3D object
            model: Model to use (defaults to config.default_model)
            output_format: Output format (defaults to config.default_format)
            quality: Quality preset
            guidance_scale: Guidance scale for quality
            seed: Random seed for reproducibility

        Returns:
            HF3DResult with generated model data
        """
        model = model or self.config.default_model
        output_format = output_format or self.config.default_format
        quality = quality or self.config.default_quality
        guidance_scale = guidance_scale or self.config.guidance_scale
        seed = seed or self.config.seed

        # Check cache
        cache_key = self._cache_key("text", prompt, model, output_format)
        if self.config.enable_caching and cache_key in self._cache:
            logger.debug("Cache hit for text-to-3D", prompt=prompt[:30])
            return self._cache[cache_key]

        logger.info(
            "HuggingFace 3D generation (text)",
            prompt=prompt[:50],
            model=model.value,
            format=output_format.value,
            quality=quality.value,
        )

        start_time = time.time()
        task_id = self._generate_task_id()

        try:
            async with self._semaphore:
                result = await self._generate_text_to_3d(
                    prompt=prompt,
                    model=model,
                    output_format=output_format,
                    quality=quality,
                    guidance_scale=guidance_scale,
                    seed=seed,
                    task_id=task_id,
                )

            result.generation_time_ms = (time.time() - start_time) * 1000
            result.status = "completed"

            # Cache result
            if self.config.enable_caching:
                self._cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(
                "Text-to-3D generation failed",
                error=str(e),
                model=model.value,
                prompt=prompt[:50],
            )

            # Try fallback models
            if self.config.enable_fallback_chain:
                return await self._try_fallback_text(
                    prompt=prompt,
                    original_model=model,
                    output_format=output_format,
                    quality=quality,
                    task_id=task_id,
                    original_error=str(e),
                )

            return HF3DResult(
                task_id=task_id,
                model_used=model,
                format=output_format,
                status="failed",
                error_message=str(e),
            )

    async def generate_from_image(
        self,
        image_path: str,
        model: HF3DModel | None = None,
        output_format: HF3DFormat | None = None,
        quality: HF3DQuality | None = None,
        remove_background: bool | None = None,
    ) -> HF3DResult:
        """
        Generate 3D model from image.

        Args:
            image_path: Path to input image or URL
            model: Model to use (defaults to config.default_model)
            output_format: Output format (defaults to config.default_format)
            quality: Quality preset
            remove_background: Whether to remove background first

        Returns:
            HF3DResult with generated model data
        """
        model = model or self.config.default_model
        output_format = output_format or self.config.default_format
        quality = quality or self.config.default_quality
        remove_background = (
            remove_background
            if remove_background is not None
            else self.config.enable_background_removal
        )

        # Handle URL vs file path
        if image_path.startswith(("http://", "https://", "data:")):
            image_data = await self._fetch_image_from_url(image_path)
        else:
            path = Path(image_path)
            if not path.exists():
                raise FileNotFoundError(f"Image not found: {image_path}")
            image_data = path.read_bytes()

        # Check cache
        image_hash = self._hash_bytes(image_data)
        cache_key = self._cache_key("image", image_hash, model, output_format)
        if self.config.enable_caching and cache_key in self._cache:
            logger.debug("Cache hit for image-to-3D", image_hash=image_hash[:12])
            return self._cache[cache_key]

        logger.info(
            "HuggingFace 3D generation (image)",
            image=image_path[:50] if len(image_path) < 100 else "base64...",
            model=model.value,
            format=output_format.value,
            quality=quality.value,
        )

        start_time = time.time()
        task_id = self._generate_task_id()

        try:
            async with self._semaphore:
                result = await self._generate_image_to_3d(
                    image_data=image_data,
                    model=model,
                    output_format=output_format,
                    quality=quality,
                    remove_background=remove_background,
                    task_id=task_id,
                )

            result.generation_time_ms = (time.time() - start_time) * 1000
            result.status = "completed"

            # Cache result
            if self.config.enable_caching:
                self._cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(
                "Image-to-3D generation failed",
                error=str(e),
                model=model.value,
            )

            # Try fallback models
            if self.config.enable_fallback_chain:
                return await self._try_fallback_image(
                    image_data=image_data,
                    original_model=model,
                    output_format=output_format,
                    quality=quality,
                    remove_background=remove_background,
                    task_id=task_id,
                    original_error=str(e),
                )

            return HF3DResult(
                task_id=task_id,
                model_used=model,
                format=output_format,
                status="failed",
                error_message=str(e),
            )

    async def _generate_text_to_3d(
        self,
        prompt: str,
        model: HF3DModel,
        output_format: HF3DFormat,
        quality: HF3DQuality,
        guidance_scale: float,
        seed: int | None,
        task_id: str,
    ) -> HF3DResult:
        """Internal text-to-3D generation."""
        session = await self._get_session()

        # Model-specific API calls
        if model == HF3DModel.HUNYUAN3D_2:
            return await self._call_hunyuan3d_text(session, prompt, output_format, quality, task_id)
        elif model in (HF3DModel.SHAP_E_TEXT, HF3DModel.SHAP_E_IMG):
            return await self._call_shap_e_text(
                session, prompt, output_format, guidance_scale, seed, task_id
            )
        else:
            # Generic Inference API call
            return await self._call_inference_api_text(
                session, model, prompt, output_format, task_id
            )

    async def _generate_image_to_3d(
        self,
        image_data: bytes,
        model: HF3DModel,
        output_format: HF3DFormat,
        quality: HF3DQuality,
        remove_background: bool,
        task_id: str,
    ) -> HF3DResult:
        """Internal image-to-3D generation."""
        session = await self._get_session()

        # Model-specific API calls
        if model == HF3DModel.HUNYUAN3D_2:
            return await self._call_hunyuan3d_image(
                session, image_data, output_format, quality, remove_background, task_id
            )
        elif model == HF3DModel.TRIPOSR:
            return await self._call_triposr(
                session, image_data, output_format, remove_background, task_id
            )
        elif model == HF3DModel.LGM:
            return await self._call_lgm(session, image_data, output_format, task_id)
        elif model == HF3DModel.INSTANTMESH:
            return await self._call_instantmesh(
                session, image_data, output_format, remove_background, task_id
            )
        else:
            # Generic Inference API call
            return await self._call_inference_api_image(
                session, model, image_data, output_format, task_id
            )

    async def _call_hunyuan3d_text(
        self,
        session: aiohttp.ClientSession,
        prompt: str,
        output_format: HF3DFormat,
        quality: HF3DQuality,
        task_id: str,
    ) -> HF3DResult:
        """Call Hunyuan3D 2.0 for text-to-3D generation."""
        url = f"{HF_API_BASE}/{HF3DModel.HUNYUAN3D_2.value}"

        # Quality presets
        quality_settings = {
            HF3DQuality.DRAFT: {"steps": 20, "resolution": 256},
            HF3DQuality.STANDARD: {"steps": 50, "resolution": 512},
            HF3DQuality.HIGH: {"steps": 75, "resolution": 512},
            HF3DQuality.PRODUCTION: {"steps": 100, "resolution": 1024},
        }
        settings = quality_settings.get(quality, quality_settings[HF3DQuality.STANDARD])

        payload = {
            "inputs": prompt,
            "parameters": {
                "num_inference_steps": settings["steps"],
                "resolution": settings["resolution"],
                "output_format": output_format.value,
            },
        }

        async with session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.read()
                output_path = await self._save_model(data, task_id, output_format)

                return HF3DResult(
                    task_id=task_id,
                    model_used=HF3DModel.HUNYUAN3D_2,
                    format=output_format,
                    output_path=output_path,
                    output_bytes=data,
                    quality_score=self._estimate_quality_score(len(data), quality),
                    polycount=self._estimate_polycount(len(data)),
                    has_textures=True,
                    metadata={
                        "prompt": prompt,
                        "settings": settings,
                        "model": HF3DModel.HUNYUAN3D_2.value,
                    },
                )
            else:
                error_text = await response.text()
                raise ValueError(f"Hunyuan3D API error: {response.status} - {error_text}")

    async def _call_hunyuan3d_image(
        self,
        session: aiohttp.ClientSession,
        image_data: bytes,
        output_format: HF3DFormat,
        quality: HF3DQuality,
        remove_background: bool,
        task_id: str,
    ) -> HF3DResult:
        """Call Hunyuan3D 2.0 for image-to-3D generation."""
        url = f"{HF_API_BASE}/{HF3DModel.HUNYUAN3D_2.value}"

        # Encode image as base64
        image_b64 = base64.b64encode(image_data).decode()

        quality_settings = {
            HF3DQuality.DRAFT: {"steps": 20},
            HF3DQuality.STANDARD: {"steps": 50},
            HF3DQuality.HIGH: {"steps": 75},
            HF3DQuality.PRODUCTION: {"steps": 100},
        }
        settings = quality_settings.get(quality, quality_settings[HF3DQuality.STANDARD])

        payload = {
            "inputs": image_b64,
            "parameters": {
                "num_inference_steps": settings["steps"],
                "remove_background": remove_background,
                "output_format": output_format.value,
            },
        }

        async with session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.read()
                output_path = await self._save_model(data, task_id, output_format)

                return HF3DResult(
                    task_id=task_id,
                    model_used=HF3DModel.HUNYUAN3D_2,
                    format=output_format,
                    output_path=output_path,
                    output_bytes=data,
                    quality_score=self._estimate_quality_score(len(data), quality),
                    polycount=self._estimate_polycount(len(data)),
                    has_textures=True,
                    metadata={
                        "source": "image",
                        "settings": settings,
                        "remove_background": remove_background,
                    },
                )
            else:
                error_text = await response.text()
                raise ValueError(f"Hunyuan3D API error: {response.status} - {error_text}")

    async def _call_triposr(
        self,
        session: aiohttp.ClientSession,
        image_data: bytes,
        output_format: HF3DFormat,
        remove_background: bool,
        task_id: str,
    ) -> HF3DResult:
        """Call TripoSR for fast image-to-3D generation."""
        url = f"{HF_API_BASE}/{HF3DModel.TRIPOSR.value}"

        image_b64 = base64.b64encode(image_data).decode()

        payload = {
            "inputs": image_b64,
            "parameters": {
                "foreground_ratio": self.config.triposr_foreground_ratio,
                "mc_resolution": self.config.triposr_mc_resolution,
                "remove_background": remove_background,
            },
        }

        async with session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.read()
                output_path = await self._save_model(data, task_id, output_format)

                return HF3DResult(
                    task_id=task_id,
                    model_used=HF3DModel.TRIPOSR,
                    format=output_format,
                    output_path=output_path,
                    output_bytes=data,
                    quality_score=self._estimate_quality_score(len(data), HF3DQuality.STANDARD),
                    polycount=self._estimate_polycount(len(data)),
                    has_textures=False,  # TripoSR generates geometry only
                    metadata={
                        "source": "image",
                        "foreground_ratio": self.config.triposr_foreground_ratio,
                        "mc_resolution": self.config.triposr_mc_resolution,
                    },
                )
            else:
                error_text = await response.text()
                raise ValueError(f"TripoSR API error: {response.status} - {error_text}")

    async def _call_lgm(
        self,
        session: aiohttp.ClientSession,
        image_data: bytes,
        output_format: HF3DFormat,
        task_id: str,
    ) -> HF3DResult:
        """Call LGM for Gaussian splatting generation."""
        url = f"{HF_API_BASE}/{HF3DModel.LGM.value}"

        image_b64 = base64.b64encode(image_data).decode()

        payload = {
            "inputs": image_b64,
            "parameters": {
                "output_format": "splat" if output_format == HF3DFormat.SPLAT else "ply",
            },
        }

        async with session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.read()
                # LGM outputs splat format by default
                actual_format = (
                    HF3DFormat.SPLAT if output_format == HF3DFormat.SPLAT else HF3DFormat.PLY
                )
                output_path = await self._save_model(data, task_id, actual_format)

                return HF3DResult(
                    task_id=task_id,
                    model_used=HF3DModel.LGM,
                    format=actual_format,
                    output_path=output_path,
                    output_bytes=data,
                    quality_score=85.0,  # LGM produces consistent quality
                    metadata={"source": "image", "technique": "gaussian_splatting"},
                )
            else:
                error_text = await response.text()
                raise ValueError(f"LGM API error: {response.status} - {error_text}")

    async def _call_instantmesh(
        self,
        session: aiohttp.ClientSession,
        image_data: bytes,
        output_format: HF3DFormat,
        remove_background: bool,
        task_id: str,
    ) -> HF3DResult:
        """Call InstantMesh for multi-view 3D generation."""
        url = f"{HF_API_BASE}/{HF3DModel.INSTANTMESH.value}"

        image_b64 = base64.b64encode(image_data).decode()

        payload = {
            "inputs": image_b64,
            "parameters": {
                "remove_background": remove_background,
                "output_format": output_format.value,
            },
        }

        async with session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.read()
                output_path = await self._save_model(data, task_id, output_format)

                return HF3DResult(
                    task_id=task_id,
                    model_used=HF3DModel.INSTANTMESH,
                    format=output_format,
                    output_path=output_path,
                    output_bytes=data,
                    quality_score=self._estimate_quality_score(len(data), HF3DQuality.HIGH),
                    polycount=self._estimate_polycount(len(data)),
                    has_textures=True,
                    metadata={"source": "image", "technique": "multi_view_diffusion"},
                )
            else:
                error_text = await response.text()
                raise ValueError(f"InstantMesh API error: {response.status} - {error_text}")

    async def _call_shap_e_text(
        self,
        session: aiohttp.ClientSession,
        prompt: str,
        output_format: HF3DFormat,
        guidance_scale: float,
        seed: int | None,
        task_id: str,
    ) -> HF3DResult:
        """Call Shap-E for text-to-3D generation."""
        url = f"{HF_API_BASE}/{HF3DModel.SHAP_E_TEXT.value}"

        payload = {
            "inputs": prompt,
            "parameters": {
                "guidance_scale": guidance_scale,
                "num_inference_steps": self.config.num_inference_steps,
            },
        }
        if seed is not None:
            payload["parameters"]["seed"] = seed

        async with session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.read()
                output_path = await self._save_model(data, task_id, HF3DFormat.PLY)

                return HF3DResult(
                    task_id=task_id,
                    model_used=HF3DModel.SHAP_E_TEXT,
                    format=HF3DFormat.PLY,  # Shap-E outputs PLY
                    output_path=output_path,
                    output_bytes=data,
                    quality_score=75.0,
                    metadata={
                        "prompt": prompt,
                        "guidance_scale": guidance_scale,
                    },
                )
            else:
                error_text = await response.text()
                raise ValueError(f"Shap-E API error: {response.status} - {error_text}")

    async def _call_inference_api_text(
        self,
        session: aiohttp.ClientSession,
        model: HF3DModel,
        prompt: str,
        output_format: HF3DFormat,
        task_id: str,
    ) -> HF3DResult:
        """Generic Inference API call for text-to-3D."""
        model_id = self.config.custom_model_id if model == HF3DModel.CUSTOM else model.value
        url = f"{HF_API_BASE}/{model_id}"

        payload = {"inputs": prompt}

        async with session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.read()
                output_path = await self._save_model(data, task_id, output_format)

                return HF3DResult(
                    task_id=task_id,
                    model_used=model,
                    format=output_format,
                    output_path=output_path,
                    output_bytes=data,
                    metadata={"prompt": prompt, "model": model_id},
                )
            else:
                error_text = await response.text()
                raise ValueError(f"HF API error: {response.status} - {error_text}")

    async def _call_inference_api_image(
        self,
        session: aiohttp.ClientSession,
        model: HF3DModel,
        image_data: bytes,
        output_format: HF3DFormat,
        task_id: str,
    ) -> HF3DResult:
        """Generic Inference API call for image-to-3D."""
        model_id = self.config.custom_model_id if model == HF3DModel.CUSTOM else model.value
        url = f"{HF_API_BASE}/{model_id}"

        image_b64 = base64.b64encode(image_data).decode()
        payload = {"inputs": image_b64}

        async with session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.read()
                output_path = await self._save_model(data, task_id, output_format)

                return HF3DResult(
                    task_id=task_id,
                    model_used=model,
                    format=output_format,
                    output_path=output_path,
                    output_bytes=data,
                    metadata={"source": "image", "model": model_id},
                )
            else:
                error_text = await response.text()
                raise ValueError(f"HF API error: {response.status} - {error_text}")

    async def _try_fallback_text(
        self,
        prompt: str,
        original_model: HF3DModel,
        output_format: HF3DFormat,
        quality: HF3DQuality,
        task_id: str,
        original_error: str,
    ) -> HF3DResult:
        """Try fallback models for text-to-3D."""
        for fallback in self.config.fallback_models:
            if fallback == original_model:
                continue

            logger.info(
                "Trying fallback model",
                fallback=fallback.value,
                original=original_model.value,
            )

            try:
                return await self.generate_from_text(
                    prompt=prompt,
                    model=fallback,
                    output_format=output_format,
                    quality=quality,
                )
            except Exception as e:
                logger.warning(f"Fallback {fallback.value} also failed: {e}")
                continue

        # All fallbacks failed
        return HF3DResult(
            task_id=task_id,
            model_used=original_model,
            format=output_format,
            status="failed",
            error_message=f"All models failed. Original: {original_error}",
        )

    async def _try_fallback_image(
        self,
        image_data: bytes,
        original_model: HF3DModel,
        output_format: HF3DFormat,
        quality: HF3DQuality,
        remove_background: bool,
        task_id: str,
        original_error: str,
    ) -> HF3DResult:
        """Try fallback models for image-to-3D."""
        for fallback in self.config.fallback_models:
            if fallback == original_model:
                continue

            logger.info(
                "Trying fallback model",
                fallback=fallback.value,
                original=original_model.value,
            )

            try:
                # Re-use internal method with fallback
                return await self._generate_image_to_3d(
                    image_data=image_data,
                    model=fallback,
                    output_format=output_format,
                    quality=quality,
                    remove_background=remove_background,
                    task_id=task_id,
                )
            except Exception as e:
                logger.warning(f"Fallback {fallback.value} also failed: {e}")
                continue

        return HF3DResult(
            task_id=task_id,
            model_used=original_model,
            format=output_format,
            status="failed",
            error_message=f"All models failed. Original: {original_error}",
        )

    async def get_optimization_hints(
        self,
        hf_result: HF3DResult,
    ) -> HF3DOptimizationHints:
        """
        Generate optimization hints for downstream processing.

        Args:
            hf_result: Result from HuggingFace 3D generation

        Returns:
            Optimization hints including auto-generated prompts
        """
        logger.info(
            "Generating optimization hints",
            task_id=hf_result.task_id,
            quality_score=hf_result.quality_score,
        )

        geometry = self._detect_geometry(hf_result)
        complexity = self._detect_complexity(hf_result)
        tripo_prompt = self._generate_tripo_prompt(hf_result, geometry, complexity)

        hints = HF3DOptimizationHints(
            detected_geometry=geometry,
            detected_complexity=complexity,
            suggested_tripo_prompt=tripo_prompt,
            confidence_score=0.85,
            mesh_analysis={
                "estimated_polycount": hf_result.polycount,
                "has_textures": hf_result.has_textures,
            },
            metadata={
                "hf_quality_score": hf_result.quality_score,
                "hf_model": hf_result.model_used.value,
            },
        )

        hf_result.tripo3d_prompt = tripo_prompt
        logger.info(
            "HF optimization hints generated",
            geometry=geometry,
            complexity=complexity,
            tripo_prompt=tripo_prompt[:50],
        )

        return hints

    def _detect_geometry(self, result: HF3DResult) -> str:
        """Detect geometry type from result."""
        if result.polycount and result.polycount < 30000:
            return "simple"
        elif result.polycount and result.polycount < 100000:
            return "medium"
        return "complex"

    def _detect_complexity(self, result: HF3DResult) -> str:
        """Detect complexity from result."""
        if result.quality_score and result.quality_score > 85:
            return "complex"
        elif result.quality_score and result.quality_score > 70:
            return "medium"
        return "simple"

    def _generate_tripo_prompt(
        self,
        result: HF3DResult,
        geometry: str,
        complexity: str,
    ) -> str:
        """Generate optimized prompt for Tripo3D."""
        base_prompt = result.metadata.get("prompt", "3D model")

        enhancements = []
        if geometry:
            enhancements.append(f"with {geometry} geometry")
        if complexity:
            enhancements.append(f"{complexity} detail level")

        if enhancements:
            return f"{base_prompt}, {', '.join(enhancements)}"
        return base_prompt

    async def compare_quality(
        self,
        hf_result: HF3DResult,
        tripo_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Compare quality between HF and Tripo3D results."""
        logger.info(
            "Comparing 3D generation quality",
            hf_score=hf_result.quality_score,
            tripo_score=tripo_result.get("quality_score"),
        )

        hf_score = hf_result.quality_score if hf_result.quality_score is not None else 0.0
        tripo_score_raw = tripo_result.get("quality_score")
        tripo_score = tripo_score_raw if tripo_score_raw is not None else 0.0

        return {
            "hf_score": hf_score,
            "tripo_score": tripo_score,
            "winner": "tripo" if tripo_score > hf_score else "hf",
            "confidence": abs(tripo_score - hf_score) / 100.0,
            "metadata": {
                "hf_model": hf_result.model_used.value,
                "hf_format": hf_result.format.value,
            },
        }

    async def list_available_models(self) -> list[dict[str, Any]]:
        """List all available 3D models."""
        return [
            {
                "id": HF3DModel.HUNYUAN3D_2.value,
                "name": "Hunyuan3D 2.0",
                "type": ["text-to-3d", "image-to-3d"],
                "quality": "production",
                "speed": "medium",
                "has_textures": True,
            },
            {
                "id": HF3DModel.TRIPOSR.value,
                "name": "TripoSR",
                "type": ["image-to-3d"],
                "quality": "high",
                "speed": "fast",
                "has_textures": False,
            },
            {
                "id": HF3DModel.LGM.value,
                "name": "LGM (Gaussian Splatting)",
                "type": ["image-to-3d"],
                "quality": "high",
                "speed": "medium",
                "has_textures": True,
            },
            {
                "id": HF3DModel.INSTANTMESH.value,
                "name": "InstantMesh",
                "type": ["image-to-3d"],
                "quality": "high",
                "speed": "medium",
                "has_textures": True,
            },
            {
                "id": HF3DModel.SHAP_E_TEXT.value,
                "name": "Shap-E (Text)",
                "type": ["text-to-3d"],
                "quality": "medium",
                "speed": "fast",
                "has_textures": False,
            },
            {
                "id": HF3DModel.SHAP_E_IMG.value,
                "name": "Shap-E (Image)",
                "type": ["image-to-3d"],
                "quality": "medium",
                "speed": "fast",
                "has_textures": False,
            },
        ]

    # Helper methods

    def _generate_task_id(self) -> str:
        """Generate unique task ID."""
        import uuid

        return str(uuid.uuid4())[:8]

    async def _save_model(
        self,
        data: bytes,
        task_id: str,
        output_format: HF3DFormat,
    ) -> str:
        """Save model data to file."""
        output_path = Path(self.config.output_dir) / f"{task_id}.{output_format.value}"
        output_path.write_bytes(data)
        return str(output_path)

    async def _fetch_image_from_url(self, url: str) -> bytes:
        """Fetch image from URL."""
        if url.startswith("data:"):
            # Base64 data URI
            _, data = url.split(",", 1)
            return base64.b64decode(data)

        session = await self._get_session()
        async with session.get(url) as response:
            if response.status == 200:
                return await response.read()
            raise ValueError(f"Failed to fetch image: {response.status}")

    def _hash_bytes(self, data: bytes) -> str:
        """Generate hash of bytes for caching."""
        import hashlib

        return hashlib.sha256(data).hexdigest()

    def _cache_key(
        self,
        source_type: str,
        source: str,
        model: HF3DModel,
        output_format: HF3DFormat,
    ) -> str:
        """Generate cache key."""
        import hashlib

        content = f"{source_type}:{source}:{model.value}:{output_format.value}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _estimate_quality_score(self, size_bytes: int, quality: HF3DQuality) -> float:
        """Estimate quality score based on output size and quality preset."""
        base_scores = {
            HF3DQuality.DRAFT: 60.0,
            HF3DQuality.STANDARD: 75.0,
            HF3DQuality.HIGH: 85.0,
            HF3DQuality.PRODUCTION: 95.0,
        }
        base = base_scores.get(quality, 75.0)

        # Adjust based on file size (larger = more detail usually)
        if size_bytes > 10_000_000:  # > 10MB
            return min(base + 5, 100.0)
        elif size_bytes > 5_000_000:  # > 5MB
            return base
        else:
            return max(base - 5, 0.0)

    def _estimate_polycount(self, size_bytes: int) -> int:
        """Estimate polygon count from file size."""
        # Rough estimate: ~100 bytes per triangle for GLB
        return max(size_bytes // 100, 1000)

    async def close(self) -> None:
        """Clean up resources."""
        if self._session and not self._session.closed:
            await self._session.close()
        logger.info("HuggingFace 3D client closed")


__all__ = [
    "HuggingFace3DClient",
    "HuggingFace3DConfig",
    "HF3DResult",
    "HF3DOptimizationHints",
    "HF3DModel",
    "HF3DFormat",
    "HF3DQuality",
]
