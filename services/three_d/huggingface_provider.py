# services/three_d/huggingface_provider.py
"""HuggingFace 3D Provider Adapter.

Provides free 3D generation via HuggingFace Spaces and models.

Supported Models:
- TRELLIS (Microsoft) - High quality image-to-3D
- TripoSR - Fast image-to-3D
- InstantMesh - Multi-view to 3D
- SHAP-E - Text-to-3D
- Hunyuan3D-2 - High quality text/image to 3D

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
import os
import shutil
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from services.three_d.provider_interface import (
    OutputFormat,
    ProviderHealth,
    ProviderStatus,
    ThreeDCapability,
    ThreeDGenerationError,
    ThreeDProviderError,
    ThreeDRequest,
    ThreeDResponse,
    ThreeDTimeoutError,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


class HuggingFaceModel(str, Enum):
    """Supported HuggingFace 3D models."""

    TRELLIS = "trellis"
    TRIPOSR = "triposr"
    INSTANTMESH = "instantmesh"
    SHAP_E = "shap_e"
    HUNYUAN3D = "hunyuan3d"


# Model to Space mapping
HUGGINGFACE_SPACES = {
    HuggingFaceModel.TRELLIS: "JeffreyXiang/TRELLIS",
    HuggingFaceModel.TRIPOSR: "stabilityai/TripoSR",
    HuggingFaceModel.INSTANTMESH: "TencentARC/InstantMesh",
    HuggingFaceModel.SHAP_E: "hysts/Shap-E",
    HuggingFaceModel.HUNYUAN3D: "tencent/Hunyuan3D-2",
}

# Model capabilities
MODEL_CAPABILITIES = {
    HuggingFaceModel.TRELLIS: [ThreeDCapability.IMAGE_TO_3D],
    HuggingFaceModel.TRIPOSR: [ThreeDCapability.IMAGE_TO_3D],
    HuggingFaceModel.INSTANTMESH: [ThreeDCapability.IMAGE_TO_3D, ThreeDCapability.MULTI_VIEW],
    HuggingFaceModel.SHAP_E: [ThreeDCapability.TEXT_TO_3D],
    HuggingFaceModel.HUNYUAN3D: [ThreeDCapability.TEXT_TO_3D, ThreeDCapability.IMAGE_TO_3D],
}


@dataclass
class HuggingFaceProviderConfig:
    """HuggingFace provider configuration."""

    # Default model for each capability
    default_text_model: HuggingFaceModel = HuggingFaceModel.SHAP_E
    default_image_model: HuggingFaceModel = HuggingFaceModel.TRELLIS

    # Output settings
    output_dir: str = field(
        default_factory=lambda: os.getenv("THREE_D_OUTPUT_DIR", "./assets/3d-models-generated")
    )

    # Generation settings
    texture_size: int = 1024
    seed: int = 42

    # Timeouts (HuggingFace Spaces can be slow)
    timeout_seconds: float = 300.0

    @classmethod
    def from_env(cls) -> HuggingFaceProviderConfig:
        """Create config from environment."""
        return cls()


# =============================================================================
# Provider Implementation
# =============================================================================


class HuggingFaceProvider:
    """HuggingFace 3D generation provider.

    Uses HuggingFace Spaces for free 3D model generation.
    Supports multiple models via Gradio client.

    Usage:
        provider = HuggingFaceProvider()
        response = await provider.generate_from_image(
            ThreeDRequest(image_path="/path/to/image.jpg")
        )
    """

    def __init__(self, config: HuggingFaceProviderConfig | None = None) -> None:
        self.config = config or HuggingFaceProviderConfig.from_env()
        self._gradio_client = None

        # Ensure output directory
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        """Provider name identifier."""
        return "huggingface"

    @property
    def capabilities(self) -> list[ThreeDCapability]:
        """List of supported capabilities (union of all models)."""
        return [
            ThreeDCapability.TEXT_TO_3D,
            ThreeDCapability.IMAGE_TO_3D,
            ThreeDCapability.MULTI_VIEW,
        ]

    def _generate_correlation_id(self) -> str:
        """Generate correlation ID."""
        return str(uuid.uuid4())

    def _select_model(
        self,
        request: ThreeDRequest,
    ) -> HuggingFaceModel:
        """Select appropriate model based on request."""
        # Check metadata for specific model request
        requested_model = request.metadata.get("hf_model")
        if requested_model:
            try:
                return HuggingFaceModel(requested_model)
            except ValueError:
                logger.warning(f"Unknown HuggingFace model: {requested_model}")

        # Select based on input type
        if request.is_text_request():
            return self.config.default_text_model
        else:
            return self.config.default_image_model

    async def _run_trellis(
        self,
        image_path: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        """Run TRELLIS generation via Gradio."""
        try:
            from gradio_client import Client, handle_file
        except ImportError:
            raise ThreeDProviderError(
                "gradio_client not installed. Run: pip install gradio_client",
                provider=self.name,
                correlation_id=correlation_id,
            )

        logger.info(f"Running TRELLIS generation for {image_path}")

        client = Client(HUGGINGFACE_SPACES[HuggingFaceModel.TRELLIS])

        result = client.predict(
            image=handle_file(image_path),
            multiimages=[],
            seed=self.config.seed,
            ss_guidance_strength=7.5,
            ss_sampling_steps=12,
            slat_guidance_strength=3,
            slat_sampling_steps=12,
            multiimage_algo="stochastic",
            mesh_simplify=0.95,
            texture_size=self.config.texture_size,
            api_name="/generate_and_extract_glb",
        )

        # result is (video_info, glb_path, download_path)
        video_info, glb_path, download_path = result

        if not glb_path or not os.path.exists(glb_path):
            raise ThreeDGenerationError(
                "TRELLIS returned no GLB file",
                provider=self.name,
                correlation_id=correlation_id,
            )

        return {
            "model_path": glb_path,
            "video_info": video_info,
            "download_path": download_path,
        }

    async def _run_triposr(
        self,
        image_path: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        """Run TripoSR generation via Gradio."""
        try:
            from gradio_client import Client, handle_file
        except ImportError:
            raise ThreeDProviderError(
                "gradio_client not installed. Run: pip install gradio_client",
                provider=self.name,
                correlation_id=correlation_id,
            )

        logger.info(f"Running TripoSR generation for {image_path}")

        client = Client(HUGGINGFACE_SPACES[HuggingFaceModel.TRIPOSR])

        result = client.predict(
            image=handle_file(image_path),
            mc_resolution=256,
            api_name="/run",
        )

        # TripoSR returns (mesh_path, ...)
        if isinstance(result, tuple):
            mesh_path = result[0]
        else:
            mesh_path = result

        if not mesh_path or not os.path.exists(mesh_path):
            raise ThreeDGenerationError(
                "TripoSR returned no mesh file",
                provider=self.name,
                correlation_id=correlation_id,
            )

        return {"model_path": mesh_path}

    async def _run_shap_e(
        self,
        prompt: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        """Run SHAP-E text-to-3D generation via Gradio."""
        try:
            from gradio_client import Client
        except ImportError:
            raise ThreeDProviderError(
                "gradio_client not installed. Run: pip install gradio_client",
                provider=self.name,
                correlation_id=correlation_id,
            )

        logger.info(f"Running SHAP-E generation for prompt: {prompt[:50]}...")

        client = Client(HUGGINGFACE_SPACES[HuggingFaceModel.SHAP_E])

        result = client.predict(
            prompt=prompt,
            seed=self.config.seed,
            guidance_scale=15.0,
            num_steps=64,
            api_name="/run",
        )

        if isinstance(result, tuple):
            mesh_path = result[0]
        else:
            mesh_path = result

        if not mesh_path or not os.path.exists(mesh_path):
            raise ThreeDGenerationError(
                "SHAP-E returned no mesh file",
                provider=self.name,
                correlation_id=correlation_id,
            )

        return {"model_path": mesh_path}

    async def generate_from_text(
        self,
        request: ThreeDRequest,
    ) -> ThreeDResponse:
        """Generate 3D model from text prompt.

        Args:
            request: ThreeDRequest with prompt set

        Returns:
            ThreeDResponse with generation result
        """
        correlation_id = request.correlation_id or self._generate_correlation_id()
        start_time = time.time()
        task_id = f"hf_txt_{uuid.uuid4().hex[:12]}"

        if not request.prompt:
            raise ThreeDProviderError(
                "Text prompt is required for text-to-3D generation",
                provider=self.name,
                correlation_id=correlation_id,
            )

        model = self._select_model(request)

        if ThreeDCapability.TEXT_TO_3D not in MODEL_CAPABILITIES.get(model, []):
            raise ThreeDProviderError(
                f"Model {model.value} does not support text-to-3D",
                provider=self.name,
                correlation_id=correlation_id,
            )

        logger.info(
            "Generating 3D from text via HuggingFace",
            extra={
                "correlation_id": correlation_id,
                "model": model.value,
                "prompt_length": len(request.prompt),
            },
        )

        try:
            # Route to appropriate model
            if model == HuggingFaceModel.SHAP_E:
                result = await self._run_shap_e(request.prompt, correlation_id)
            elif model == HuggingFaceModel.HUNYUAN3D:
                # Hunyuan3D also supports text - use SHAP-E as fallback for now
                result = await self._run_shap_e(request.prompt, correlation_id)
            else:
                raise ThreeDProviderError(
                    f"Text-to-3D not implemented for {model.value}",
                    provider=self.name,
                    correlation_id=correlation_id,
                )

            # Copy to output directory
            source_path = result["model_path"]
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            output_filename = f"hf_{model.value}_{timestamp}_{correlation_id[:8]}.glb"
            output_path = Path(self.config.output_dir) / output_filename

            shutil.copy2(source_path, output_path)

            duration = time.time() - start_time

            return ThreeDResponse(
                success=True,
                task_id=task_id,
                status="completed",
                model_url=f"/assets/3d-models-generated/{output_filename}",
                model_path=str(output_path),
                output_format=OutputFormat.GLB,
                provider=f"{self.name}:{model.value}",
                duration_seconds=duration,
                created_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
                correlation_id=correlation_id,
                metadata={
                    "prompt": request.prompt,
                    "hf_model": model.value,
                    "hf_space": HUGGINGFACE_SPACES[model],
                },
            )

        except ThreeDProviderError:
            raise

        except TimeoutError as e:
            raise ThreeDTimeoutError(
                f"HuggingFace generation timed out: {e}",
                provider=self.name,
                timeout_seconds=self.config.timeout_seconds,
                correlation_id=correlation_id,
            ) from e

        except Exception as e:
            raise ThreeDGenerationError(
                f"HuggingFace generation failed: {e}",
                provider=self.name,
                task_id=task_id,
                correlation_id=correlation_id,
            ) from e

    async def generate_from_image(
        self,
        request: ThreeDRequest,
    ) -> ThreeDResponse:
        """Generate 3D model from image.

        Args:
            request: ThreeDRequest with image_url or image_path set

        Returns:
            ThreeDResponse with generation result
        """
        correlation_id = request.correlation_id or self._generate_correlation_id()
        start_time = time.time()
        task_id = f"hf_img_{uuid.uuid4().hex[:12]}"

        image_source = request.get_image_source()
        if not image_source:
            raise ThreeDProviderError(
                "Image URL or path is required for image-to-3D generation",
                provider=self.name,
                correlation_id=correlation_id,
            )

        model = self._select_model(request)

        if ThreeDCapability.IMAGE_TO_3D not in MODEL_CAPABILITIES.get(model, []):
            raise ThreeDProviderError(
                f"Model {model.value} does not support image-to-3D",
                provider=self.name,
                correlation_id=correlation_id,
            )

        logger.info(
            "Generating 3D from image via HuggingFace",
            extra={
                "correlation_id": correlation_id,
                "model": model.value,
                "image_source": image_source[:100],
            },
        )

        try:
            # Route to appropriate model
            if model == HuggingFaceModel.TRELLIS:
                result = await self._run_trellis(image_source, correlation_id)
            elif model == HuggingFaceModel.TRIPOSR:
                result = await self._run_triposr(image_source, correlation_id)
            elif model in (HuggingFaceModel.INSTANTMESH, HuggingFaceModel.HUNYUAN3D):
                # Fall back to TRELLIS for these
                result = await self._run_trellis(image_source, correlation_id)
            else:
                raise ThreeDProviderError(
                    f"Image-to-3D not implemented for {model.value}",
                    provider=self.name,
                    correlation_id=correlation_id,
                )

            # Copy to output directory
            source_path = result["model_path"]
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            output_filename = f"hf_{model.value}_{timestamp}_{correlation_id[:8]}.glb"
            output_path = Path(self.config.output_dir) / output_filename

            shutil.copy2(source_path, output_path)

            duration = time.time() - start_time

            # Get file size
            file_size = output_path.stat().st_size if output_path.exists() else None

            return ThreeDResponse(
                success=True,
                task_id=task_id,
                status="completed",
                model_url=f"/assets/3d-models-generated/{output_filename}",
                model_path=str(output_path),
                output_format=OutputFormat.GLB,
                provider=f"{self.name}:{model.value}",
                duration_seconds=duration,
                file_size_bytes=file_size,
                created_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
                correlation_id=correlation_id,
                metadata={
                    "image_source": image_source,
                    "hf_model": model.value,
                    "hf_space": HUGGINGFACE_SPACES[model],
                    "texture_size": self.config.texture_size,
                },
            )

        except ThreeDProviderError:
            raise

        except TimeoutError as e:
            raise ThreeDTimeoutError(
                f"HuggingFace generation timed out: {e}",
                provider=self.name,
                timeout_seconds=self.config.timeout_seconds,
                correlation_id=correlation_id,
            ) from e

        except Exception as e:
            raise ThreeDGenerationError(
                f"HuggingFace generation failed: {e}",
                provider=self.name,
                task_id=task_id,
                correlation_id=correlation_id,
            ) from e

    async def health_check(self) -> ProviderHealth:
        """Check provider health and availability."""
        start_time = time.time()

        try:
            # Check if gradio_client is available
            try:
                from gradio_client import Client

                GRADIO_AVAILABLE = True
            except ImportError:
                GRADIO_AVAILABLE = False

            if not GRADIO_AVAILABLE:
                return ProviderHealth(
                    provider=self.name,
                    status=ProviderStatus.UNAVAILABLE,
                    capabilities=self.capabilities,
                    last_check=datetime.now(UTC),
                    error_message="gradio_client not installed",
                )

            latency = (time.time() - start_time) * 1000

            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.AVAILABLE,
                capabilities=self.capabilities,
                latency_ms=latency,
                last_check=datetime.now(UTC),
            )

        except Exception as e:
            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.UNAVAILABLE,
                capabilities=self.capabilities,
                last_check=datetime.now(UTC),
                error_message=str(e),
            )

    async def close(self) -> None:
        """Close provider resources."""
        # Gradio client doesn't need explicit cleanup
        pass


__all__ = [
    "HuggingFaceProvider",
    "HuggingFaceProviderConfig",
    "HuggingFaceModel",
    "HUGGINGFACE_SPACES",
    "MODEL_CAPABILITIES",
]
