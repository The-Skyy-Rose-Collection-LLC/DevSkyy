# ai_3d/generation_pipeline.py
"""
AI-Powered 3D Model Generation Pipeline.

MANDATORY: All generated models must achieve 95% fidelity score.

Supports multiple generation providers:
- Tripo3D: High-quality clothing/product 3D models
- HuggingFace: Open-source 3D generation models
- Meshy: Alternative 3D generation service

Pipeline stages:
1. Image preprocessing (background removal, normalization)
2. 3D generation via selected provider
3. Model validation (95% fidelity check)
4. Quality enhancement (texture upscaling, mesh optimization)
5. Format conversion and export
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from errors.production_errors import (
    ModelFidelityError,
)
from imagery.image_processor import ImagePreprocessor
from imagery.model_fidelity import (
    MINIMUM_FIDELITY_SCORE,
    FidelityReport,
    ModelFidelityValidator,
)

logger = logging.getLogger(__name__)


class ThreeDProvider(str, Enum):
    """Supported 3D generation providers."""

    TRELLIS = "trellis"  # HuggingFace TRELLIS (preferred)
    TRIPO = "tripo"
    HUGGINGFACE = "huggingface"
    MESHY = "meshy"
    AUTO = "auto"  # Automatic provider selection with fallback chain


class ModelFormat(str, Enum):
    """Supported 3D model formats."""

    GLB = "glb"
    GLTF = "gltf"
    OBJ = "obj"
    FBX = "fbx"
    USD = "usd"
    STL = "stl"


class GenerationQuality(str, Enum):
    """Quality presets for generation."""

    DRAFT = "draft"  # Fast, lower quality
    STANDARD = "standard"  # Balanced
    HIGH = "high"  # High quality
    PRODUCTION = "production"  # Maximum quality (enforces 95%)


class GenerationConfig(BaseModel):
    """Configuration for 3D model generation."""

    # Provider settings
    provider: ThreeDProvider = Field(
        default=ThreeDProvider.AUTO,
        description="3D generation provider",
    )
    fallback_providers: list[ThreeDProvider] = Field(
        default=[ThreeDProvider.TRELLIS, ThreeDProvider.MESHY, ThreeDProvider.TRIPO],
        description="Fallback chain: TRELLIS -> Meshy -> Tripo3D",
    )

    # Quality settings
    quality: GenerationQuality = Field(
        default=GenerationQuality.PRODUCTION,
        description="Generation quality preset",
    )
    minimum_fidelity: float = Field(
        default=MINIMUM_FIDELITY_SCORE,
        description="Minimum fidelity score (95% for production)",
    )
    enforce_fidelity: bool = Field(
        default=True,
        description="Enforce fidelity threshold",
    )

    # Output settings
    output_format: ModelFormat = Field(
        default=ModelFormat.GLB,
        description="Output model format",
    )
    output_dir: str = Field(
        default="./generated_3d_models",
        description="Output directory",
    )

    # Generation parameters
    texture_resolution: int = Field(
        default=2048,
        description="Texture resolution",
    )
    mesh_quality: str = Field(
        default="high",
        description="Mesh quality level",
    )
    generate_pbr: bool = Field(
        default=True,
        description="Generate PBR materials",
    )

    # Retry settings
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay_seconds: int = Field(default=10, description="Delay between retries")


@dataclass
class GenerationResult:
    """Result from 3D model generation."""

    success: bool
    model_path: str | None = None
    provider_used: ThreeDProvider | None = None
    fidelity_score: float = 0.0
    fidelity_passed: bool = False
    fidelity_report: FidelityReport | None = None
    generation_time_seconds: float = 0.0
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "model_path": self.model_path,
            "provider_used": self.provider_used.value if self.provider_used else None,
            "fidelity_score": self.fidelity_score,
            "fidelity_passed": self.fidelity_passed,
            "generation_time_seconds": self.generation_time_seconds,
            "errors": self.errors,
            "metadata": self.metadata,
            "correlation_id": self.correlation_id,
        }


class ThreeDGenerationPipeline:
    """
    Production-grade 3D model generation pipeline.

    MANDATORY: All models must achieve 95% fidelity to pass.

    Usage:
        pipeline = ThreeDGenerationPipeline()
        config = GenerationConfig(quality=GenerationQuality.PRODUCTION)
        result = await pipeline.generate_from_image("product.jpg", config)

        if not result.fidelity_passed:
            raise ModelFidelityError(result.fidelity_score)
    """

    def __init__(self) -> None:
        """Initialize the generation pipeline."""
        self._providers: dict[ThreeDProvider, Any] = {}
        self._preprocessor = ImagePreprocessor()
        self._fidelity_validator = ModelFidelityValidator()
        self._init_providers()

    def _init_providers(self) -> None:
        """
        Initialize available providers.

        Provider priority (fallback chain):
        1. TRELLIS (HuggingFace) - Best quality, open-source
        2. Meshy - Good quality, commercial
        3. Tripo3D - Good quality, commercial
        4. HuggingFace (TripoSR/Shap-E) - Fallback open-source
        """
        # TRELLIS (via HuggingFace) - PREFERRED
        if os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN"):
            try:
                from ai_3d.providers.huggingface import HuggingFace3DClient

                # TRELLIS client (uses TRELLIS as default model)
                trellis_client = HuggingFace3DClient()
                self._providers[ThreeDProvider.TRELLIS] = trellis_client
                # Also register as HuggingFace for backward compatibility
                self._providers[ThreeDProvider.HUGGINGFACE] = trellis_client
                logger.info("TRELLIS/HuggingFace 3D provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize TRELLIS/HuggingFace: {e}")

        # Meshy - Second priority
        if os.getenv("MESHY_API_KEY"):
            try:
                from ai_3d.providers.meshy import MeshyClient

                self._providers[ThreeDProvider.MESHY] = MeshyClient()
                logger.info("Meshy provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Meshy: {e}")

        # Tripo3D - Third priority
        if os.getenv("TRIPO_API_KEY"):
            try:
                from ai_3d.providers.tripo import TripoClient

                self._providers[ThreeDProvider.TRIPO] = TripoClient()
                logger.info("Tripo3D provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Tripo3D: {e}")

        if not self._providers:
            logger.warning(
                "No 3D generation providers available. "
                "Set HUGGINGFACE_API_KEY (for TRELLIS), MESHY_API_KEY, or TRIPO_API_KEY."
            )

    def get_available_providers(self) -> list[ThreeDProvider]:
        """Get list of available providers."""
        return list(self._providers.keys())

    async def generate_from_image(
        self,
        image_path: str | Path,
        config: GenerationConfig | None = None,
        prompt: str | None = None,
    ) -> GenerationResult:
        """
        Generate a 3D model from a 2D image.

        Args:
            image_path: Path to the source image
            config: Generation configuration
            prompt: Optional text description to guide generation

        Returns:
            GenerationResult with model path and fidelity info

        Raises:
            ThreeDGenerationError: If generation fails
            ModelFidelityError: If enforce_fidelity=True and model fails threshold
        """
        config = config or GenerationConfig()
        start_time = datetime.now(UTC)
        correlation_id = str(uuid.uuid4())

        result = GenerationResult(
            success=False,
            correlation_id=correlation_id,
        )

        image_path = Path(image_path)
        if not image_path.exists():
            result.errors.append(f"Image file not found: {image_path}")
            return result

        # Create output directory
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Stage 1: Preprocess image
            logger.info(f"[{correlation_id}] Stage 1: Preprocessing image")
            processed_image = await self._preprocessor.preprocess_for_3d(
                image_path,
                remove_background=True,
                target_size=(1024, 1024),
            )

            # Save preprocessed image
            preprocessed_path = output_dir / f"{image_path.stem}_preprocessed.png"
            processed_image.save(preprocessed_path)

            # Stage 2: Select provider
            provider = self._select_provider(config)
            if not provider:
                result.errors.append("No 3D generation providers available")
                return result

            result.provider_used = provider

            # Stage 3: Generate 3D model with retries
            logger.info(f"[{correlation_id}] Stage 2: Generating 3D model with {provider.value}")
            model_path = await self._generate_with_retries(
                provider,
                preprocessed_path,
                prompt,
                config,
                correlation_id,
            )

            if not model_path:
                result.errors.append("3D generation failed after all retries")
                return result

            result.model_path = str(model_path)

            # Stage 4: Validate fidelity
            logger.info(f"[{correlation_id}] Stage 3: Validating model fidelity")
            fidelity_report = await self._fidelity_validator.validate(model_path)
            result.fidelity_score = fidelity_report.overall_score
            result.fidelity_passed = fidelity_report.passed
            result.fidelity_report = fidelity_report

            # Stage 5: Enforce fidelity if required
            if config.enforce_fidelity and not fidelity_report.passed:
                logger.warning(
                    f"[{correlation_id}] Model fidelity {fidelity_report.overall_score}% "
                    f"below threshold {config.minimum_fidelity}%"
                )

                # Try to enhance the model
                enhanced_path = await self._enhance_model(model_path, config)
                if enhanced_path:
                    # Re-validate
                    enhanced_report = await self._fidelity_validator.validate(enhanced_path)
                    if enhanced_report.passed:
                        result.model_path = str(enhanced_path)
                        result.fidelity_score = enhanced_report.overall_score
                        result.fidelity_passed = True
                        result.fidelity_report = enhanced_report
                    else:
                        raise ModelFidelityError(
                            actual_fidelity=enhanced_report.overall_score,
                            required_fidelity=config.minimum_fidelity,
                            context={
                                "correlation_id": correlation_id,
                                "provider": provider.value,
                                "issues": enhanced_report.issues,
                            },
                        )
                else:
                    raise ModelFidelityError(
                        actual_fidelity=fidelity_report.overall_score,
                        required_fidelity=config.minimum_fidelity,
                        context={
                            "correlation_id": correlation_id,
                            "provider": provider.value,
                            "issues": fidelity_report.issues,
                        },
                    )

            result.success = True

        except ModelFidelityError:
            raise  # Re-raise fidelity errors

        except Exception as e:
            result.errors.append(f"Pipeline error: {str(e)}")
            logger.exception(f"[{correlation_id}] Generation pipeline failed")

        finally:
            end_time = datetime.now(UTC)
            result.generation_time_seconds = (end_time - start_time).total_seconds()
            result.metadata["started_at"] = start_time.isoformat()
            result.metadata["completed_at"] = end_time.isoformat()

        return result

    async def generate_from_text(
        self,
        prompt: str,
        config: GenerationConfig | None = None,
    ) -> GenerationResult:
        """
        Generate a 3D model from a text description.

        Args:
            prompt: Text description of the desired 3D model
            config: Generation configuration

        Returns:
            GenerationResult with model path and fidelity info
        """
        config = config or GenerationConfig()
        start_time = datetime.now(UTC)
        correlation_id = str(uuid.uuid4())

        result = GenerationResult(
            success=False,
            correlation_id=correlation_id,
        )

        # Create output directory
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Select provider with text-to-3D support
            provider = self._select_provider(config, text_to_3d=True)
            if not provider:
                result.errors.append("No text-to-3D providers available")
                return result

            result.provider_used = provider

            # Generate
            logger.info(f"[{correlation_id}] Generating 3D from text with {provider.value}")
            model_path = await self._generate_text_to_3d(
                provider,
                prompt,
                config,
                correlation_id,
            )

            if not model_path:
                result.errors.append("Text-to-3D generation failed")
                return result

            result.model_path = str(model_path)

            # Validate fidelity
            fidelity_report = await self._fidelity_validator.validate(model_path)
            result.fidelity_score = fidelity_report.overall_score
            result.fidelity_passed = fidelity_report.passed
            result.fidelity_report = fidelity_report

            result.success = True

        except Exception as e:
            result.errors.append(f"Pipeline error: {str(e)}")
            logger.exception(f"[{correlation_id}] Text-to-3D pipeline failed")

        finally:
            end_time = datetime.now(UTC)
            result.generation_time_seconds = (end_time - start_time).total_seconds()

        return result

    def _select_provider(
        self,
        config: GenerationConfig,
        text_to_3d: bool = False,
    ) -> ThreeDProvider | None:
        """
        Select the best available provider using fallback chain.

        Priority order for image-to-3D:
        1. TRELLIS (best quality)
        2. Meshy
        3. Tripo3D
        4. HuggingFace (TripoSR fallback)

        Priority order for text-to-3D:
        1. Meshy (good text-to-3D support)
        2. TRELLIS
        3. Tripo3D
        4. HuggingFace (Shap-E)
        """
        if config.provider == ThreeDProvider.AUTO:
            if text_to_3d:
                # Different priority for text-to-3D
                priority = [
                    ThreeDProvider.MESHY,
                    ThreeDProvider.TRELLIS,
                    ThreeDProvider.TRIPO,
                    ThreeDProvider.HUGGINGFACE,
                ]
            else:
                # Prefer TRELLIS for image-to-3D (best quality)
                priority = [
                    ThreeDProvider.TRELLIS,
                    ThreeDProvider.MESHY,
                    ThreeDProvider.TRIPO,
                    ThreeDProvider.HUGGINGFACE,
                ]

            for provider in priority:
                if provider in self._providers:
                    logger.info(f"Auto-selected provider: {provider.value}")
                    return provider
        else:
            if config.provider in self._providers:
                return config.provider
            else:
                logger.warning(
                    f"Requested provider {config.provider.value} not available, "
                    f"trying fallbacks"
                )

        # Try fallbacks from config
        for provider in config.fallback_providers:
            if provider in self._providers:
                logger.info(f"Using fallback provider: {provider.value}")
                return provider

        return None

    async def _generate_with_retries(
        self,
        provider: ThreeDProvider,
        image_path: Path,
        prompt: str | None,
        config: GenerationConfig,
        correlation_id: str,
    ) -> Path | None:
        """
        Generate with retry logic and provider fallback.

        Tries the primary provider first, then falls back to other
        providers in the fallback chain if the primary fails.
        """
        # Build ordered list of providers to try
        providers_to_try = [provider]
        for fallback in config.fallback_providers:
            if fallback in self._providers and fallback not in providers_to_try:
                providers_to_try.append(fallback)

        for current_provider in providers_to_try:
            logger.info(f"[{correlation_id}] Trying provider: {current_provider.value}")

            last_error = None

            for attempt in range(config.max_retries):
                try:
                    logger.info(
                        f"[{correlation_id}] Generation attempt {attempt + 1}/{config.max_retries} "
                        f"with {current_provider.value}"
                    )

                    client = self._providers[current_provider]
                    model_path = await client.generate_from_image(
                        image_path=str(image_path),
                        output_dir=config.output_dir,
                        output_format=config.output_format.value,
                        prompt=prompt,
                        texture_resolution=config.texture_resolution,
                    )

                    if model_path and Path(model_path).exists():
                        logger.info(
                            f"[{correlation_id}] Successfully generated with {current_provider.value}"
                        )
                        return Path(model_path)

                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"[{correlation_id}] Attempt {attempt + 1} with {current_provider.value} failed: {e}"
                    )

                    if attempt < config.max_retries - 1:
                        await asyncio.sleep(config.retry_delay_seconds)

            # All retries failed for this provider, try next
            if last_error:
                logger.warning(
                    f"[{correlation_id}] Provider {current_provider.value} failed after "
                    f"{config.max_retries} attempts, trying next provider"
                )

        logger.error(f"[{correlation_id}] All providers and retries exhausted")
        return None

    async def _generate_text_to_3d(
        self,
        provider: ThreeDProvider,
        prompt: str,
        config: GenerationConfig,
        correlation_id: str,
    ) -> Path | None:
        """Generate 3D model from text."""
        try:
            client = self._providers[provider]

            if not hasattr(client, "generate_from_text"):
                logger.warning(f"{provider.value} does not support text-to-3D")
                return None

            model_path = await client.generate_from_text(
                prompt=prompt,
                output_dir=config.output_dir,
                output_format=config.output_format.value,
            )

            if model_path and Path(model_path).exists():
                return Path(model_path)

        except Exception as e:
            logger.error(f"[{correlation_id}] Text-to-3D failed: {e}")

        return None

    async def _enhance_model(
        self,
        model_path: Path,
        config: GenerationConfig,
    ) -> Path | None:
        """Attempt to enhance a model to meet fidelity requirements."""
        try:
            from ai_3d.quality_enhancer import EnhancementConfig, ModelQualityEnhancer

            enhancer = ModelQualityEnhancer()
            enhancement_config = EnhancementConfig(
                target_fidelity=config.minimum_fidelity,
                texture_upscale=True,
                mesh_optimization=True,
            )

            enhanced_path = await enhancer.enhance(model_path, enhancement_config)
            return enhanced_path

        except Exception as e:
            logger.warning(f"Model enhancement failed: {e}")
            return None
