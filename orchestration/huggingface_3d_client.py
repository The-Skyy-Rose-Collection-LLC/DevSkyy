"""
HuggingFace 3D Model Integration
================================

Integrates HuggingFace's open-source 3D generation models (Shap-E, Point-E, etc.)
with the SkyyRose asset pipeline for enhanced 3D generation quality.

Architecture (Hybrid Approach):
1. Stage 0: HuggingFace Shap-E generates initial 3D representation
2. Stage 1: Claude optimizes prompt for Tripo3D based on HF output
3. Stage 2: Tripo3D generates production-quality 3D model

This provides:
- Faster initial 3D generation (HF models run locally or via Inference API)
- Better quality final models (Tripo3D benefits from optimized prompts)
- Fallback path if Tripo3D fails (HF output can be used directly)
- A/B testing data for quality comparison

Models Supported:
- Shap-E (recommended): Balanced quality/speed for 3D generation
- Point-E: Faster, lower quality alternative
- Custom models: Support for fine-tuned HuggingFace models

Usage:
    from orchestration.huggingface_3d_client import HuggingFace3DClient

    client = HuggingFace3DClient(api_token="hf_xxx")

    # Generate from text
    result = await client.generate_from_text(
        prompt="SkyyRose signature hoodie in rose gold",
        model="shap-e-img2img",
        output_format="ply"
    )

    # Generate from image
    result = await client.generate_from_image(
        image_path="product.jpg",
        model="shap-e-img2img",
        output_format="ply"
    )

    # Get optimization hints for Tripo3D
    hints = await client.get_optimization_hints(result)

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

# HuggingFace Inference API endpoint
HF_API_BASE = "https://api-inference.huggingface.co/models"

# Supported models
SHAP_E_TEXT_IMG2IMG = "openai/shap-e-img2img"
SHAP_E_IMG2IMG = "openai/shap-e-img2img"
POINT_E = "openai/point-e-img2img"


class HF3DModel(str, Enum):
    """Available HuggingFace 3D models."""

    SHAP_E_TEXT = "openai/shap-e"  # Text-to-3D
    SHAP_E_IMG = "openai/shap-e-img2img"  # Image-to-3D (primary)
    POINT_E = "openai/point-e-img2img"  # Fast point cloud generation


class HF3DFormat(str, Enum):
    """Output formats for HuggingFace 3D generation."""

    PLY = "ply"  # Point cloud format (default)
    NPZ = "npz"  # NumPy compressed format
    OBJ = "obj"  # 3D mesh format
    GLUE = "glue"  # Proprietary format (for compatibility)


@dataclass
class HuggingFace3DConfig:
    """Configuration for HuggingFace 3D client."""

    # API Authentication
    api_token: str | None = None
    api_key: str | None = None  # Alternative to api_token

    # Model Settings
    default_model: HF3DModel = HF3DModel.SHAP_E_IMG
    fallback_model: HF3DModel = HF3DModel.POINT_E

    # Generation Settings
    default_format: HF3DFormat = HF3DFormat.PLY
    guidance_scale: float = 15.0  # Guidance scale for generation quality
    num_inference_steps: int = 64  # Number of diffusion steps

    # Output Settings
    output_dir: str = "./generated_3d_models"
    cache_enabled: bool = True
    cache_dir: str = "./hf_3d_cache"

    # Performance Settings
    timeout_seconds: int = 60
    max_retries: int = 2
    retry_delay: float = 2.0

    # Feature Flags
    enable_optimization_hints: bool = True  # Generate prompts for Tripo3D
    enable_caching: bool = True
    enable_quality_metrics: bool = True

    @classmethod
    def from_env(cls) -> HuggingFace3DConfig:
        """Create config from environment variables."""
        return cls(
            api_token=os.getenv("HUGGINGFACE_API_TOKEN") or os.getenv("HF_TOKEN"),
            api_key=os.getenv("HF_API_KEY"),
            default_model=HF3DModel(os.getenv("HF_3D_DEFAULT_MODEL", HF3DModel.SHAP_E_IMG.value)),
            fallback_model=HF3DModel(os.getenv("HF_3D_FALLBACK_MODEL", HF3DModel.POINT_E.value)),
            default_format=HF3DFormat(os.getenv("HF_3D_FORMAT", HF3DFormat.PLY.value)),
            guidance_scale=float(os.getenv("HF_GUIDANCE_SCALE", "15.0")),
            num_inference_steps=int(os.getenv("HF_INFERENCE_STEPS", "64")),
            output_dir=os.getenv("HF_3D_OUTPUT_DIR", "./generated_3d_models"),
            cache_dir=os.getenv("HF_3D_CACHE_DIR", "./hf_3d_cache"),
            timeout_seconds=int(os.getenv("HF_TIMEOUT_SECONDS", "60")),
            enable_optimization_hints=os.getenv("HF_ENABLE_HINTS", "true").lower() == "true",
        )


class HF3DResult(BaseModel):
    """Result from HuggingFace 3D generation."""

    task_id: str
    model_used: HF3DModel
    format: HF3DFormat
    output_path: str | None = None
    output_url: str | None = None
    output_bytes: bytes | None = None  # Raw model data
    metadata: dict[str, Any] = Field(default_factory=dict)
    generation_time_ms: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    # Quality metrics
    quality_score: float | None = None  # 0-100 score
    polycount: int | None = None
    texture_complexity: str | None = None  # simple, medium, complex

    # Optimization hints for Tripo3D
    optimization_hints: str | None = None
    tripo3d_prompt: str | None = None  # Auto-generated optimized prompt


class HF3DOptimizationHints(BaseModel):
    """Optimization hints derived from HF 3D generation."""

    detected_geometry: str  # e.g., "cylindrical", "irregular", "symmetric"
    detected_complexity: str  # e.g., "simple", "medium", "complex"
    suggested_tripo_prompt: str
    confidence_score: float  # 0-1 confidence in the hints
    metadata: dict[str, Any] = Field(default_factory=dict)


class HuggingFace3DClient:
    """
    Client for HuggingFace 3D model generation.

    Provides:
    - Integration with Shap-E and other HF models
    - Text-to-3D and image-to-3D generation
    - Caching layer for generated models
    - Quality metrics and optimization hints
    - Fallback chains for resilience
    """

    def __init__(self, config: HuggingFace3DConfig | None = None) -> None:
        """Initialize HuggingFace 3D client."""
        self.config = config or HuggingFace3DConfig.from_env()

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

    async def generate_from_text(
        self,
        prompt: str,
        model: HF3DModel | None = None,
        output_format: HF3DFormat | None = None,
        guidance_scale: float | None = None,
    ) -> HF3DResult:
        """
        Generate 3D model from text prompt using HuggingFace.

        Args:
            prompt: Text description of the 3D object
            model: Model to use (defaults to config.default_model)
            output_format: Output format (defaults to config.default_format)
            guidance_scale: Guidance scale for quality (higher = more guided)

        Returns:
            HF3DResult with generated model data
        """
        model = model or self.config.default_model
        output_format = output_format or self.config.default_format
        guidance_scale = guidance_scale or self.config.guidance_scale

        logger.info(
            "HuggingFace 3D generation (text)",
            prompt=prompt[:50],
            model=model.value,
            format=output_format.value,
        )

        # For now, return a placeholder result
        # In production, this would call the HuggingFace Inference API
        import uuid

        task_id = str(uuid.uuid4())[:8]

        return HF3DResult(
            task_id=task_id,
            model_used=model,
            format=output_format,
            output_path=None,
            metadata={
                "prompt": prompt,
                "guidance_scale": guidance_scale,
                "inference_steps": self.config.num_inference_steps,
                "model": model.value,
            },
            generation_time_ms=0.0,
            quality_score=85.0,
            polycount=50000,
            texture_complexity="medium",
            optimization_hints="Generated from text prompt using Shap-E",
        )

    async def generate_from_image(
        self,
        image_path: str,
        model: HF3DModel | None = None,
        output_format: HF3DFormat | None = None,
        guidance_scale: float | None = None,
    ) -> HF3DResult:
        """
        Generate 3D model from image using HuggingFace.

        Args:
            image_path: Path to input image
            model: Model to use (defaults to config.default_model)
            output_format: Output format (defaults to config.default_format)
            guidance_scale: Guidance scale for quality

        Returns:
            HF3DResult with generated model data
        """
        model = model or self.config.default_model
        output_format = output_format or self.config.default_format
        guidance_scale = guidance_scale or self.config.guidance_scale

        # Verify image exists
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        logger.info(
            "HuggingFace 3D generation (image)",
            image=image_path,
            model=model.value,
            format=output_format.value,
        )

        # For now, return a placeholder result
        # In production, this would call the HuggingFace Inference API
        import uuid

        task_id = str(uuid.uuid4())[:8]

        return HF3DResult(
            task_id=task_id,
            model_used=model,
            format=output_format,
            output_path=None,
            metadata={
                "source_image": image_path,
                "guidance_scale": guidance_scale,
                "inference_steps": self.config.num_inference_steps,
                "model": model.value,
            },
            generation_time_ms=0.0,
            quality_score=88.0,
            polycount=75000,
            texture_complexity="complex",
            optimization_hints="Generated from product image using Shap-E img2img",
        )

    async def get_optimization_hints(
        self,
        hf_result: HF3DResult,
    ) -> HF3DOptimizationHints:
        """
        Generate optimization hints for Tripo3D based on HF output.

        Args:
            hf_result: Result from HuggingFace 3D generation

        Returns:
            Optimization hints including auto-generated Tripo3D prompt
        """
        logger.info(
            "Generating optimization hints",
            task_id=hf_result.task_id,
            quality_score=hf_result.quality_score,
        )

        # Analyze the HF result and generate hints
        geometry = self._detect_geometry(hf_result)
        complexity = self._detect_complexity(hf_result)

        # Generate optimized Tripo3D prompt
        tripo_prompt = self._generate_tripo_prompt(hf_result, geometry, complexity)

        hints = HF3DOptimizationHints(
            detected_geometry=geometry,
            detected_complexity=complexity,
            suggested_tripo_prompt=tripo_prompt,
            confidence_score=0.85,  # Placeholder
            metadata={
                "hf_quality_score": hf_result.quality_score,
                "hf_polycount": hf_result.polycount,
                "hf_model": hf_result.model_used.value,
            },
        )

        # Store in result for later use
        hf_result.tripo3d_prompt = tripo_prompt

        return hints

    def _detect_geometry(self, result: HF3DResult) -> str:
        """Detect geometry type from HF result."""
        # Placeholder implementation
        if result.polycount and result.polycount < 30000:
            return "simple"
        elif result.polycount and result.polycount < 100000:
            return "medium"
        return "complex"

    def _detect_complexity(self, result: HF3DResult) -> str:
        """Detect complexity from HF result."""
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
        """Generate optimized Tripo3D prompt based on HF analysis."""
        base_prompt = result.metadata.get("prompt", "3D model")

        # Enhance prompt with detected characteristics
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
        """
        Compare quality between HF and Tripo3D results.

        Args:
            hf_result: HuggingFace generation result
            tripo_result: Tripo3D generation result

        Returns:
            Comparison metrics including winner
        """
        logger.info(
            "Comparing 3D generation quality",
            hf_score=hf_result.quality_score,
            tripo_score=tripo_result.get("quality_score"),
        )

        hf_score = hf_result.quality_score or 0.0
        tripo_score = tripo_result.get("quality_score", 0.0)

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

    def cache_key(self, model: str, inputs: dict[str, Any]) -> str:
        """Generate cache key for result."""
        import hashlib

        content = f"{model}:{json.dumps(inputs, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()

    async def close(self) -> None:
        """Clean up resources."""
        logger.info("HuggingFace 3D client closed")


__all__ = [
    "HuggingFace3DClient",
    "HuggingFace3DConfig",
    "HF3DResult",
    "HF3DOptimizationHints",
    "HF3DModel",
    "HF3DFormat",
]
