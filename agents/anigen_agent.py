"""
AniGen Garment Rigging Agent
============================

Generates rigged, animatable 3D garments from product images using the
damBruh/SkyyRose-AniGen HuggingFace Space (VAST-AI AniGen, SIGGRAPH 2026).

Consolidated responsibilities:
- Image-to-rigged-GLB generation (text-to-3D is unsupported by AniGen)
- Three-stage stateful pipeline (all via named API endpoints, same client session):
    /prepare_input_for_generation → /generate_preview (~52s) → /extract_glb (~18s)
- Output: GLB with T-pose skeleton carrying JOINTS_0, WEIGHTS_0, inverseBindMatrices

ML capabilities:
- Three-dimensional garment reconstruction with animatable rig
- Automatic retargeting to Mixamo-named clips via Three.js (consumer-side)

Hardware requirement: L40S 48GB (L4 24GB OOMs at FlexiCubes mesh extraction step).
Total wall-clock time per generation: ~70s on L40S.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from agents.base_legacy import (
    AgentCapability,
    AgentConfig,
    ExecutionResult,
    LLMCategory,
    PlanStep,
    RetrievalContext,
    SuperAgent,
    ValidationResult,
)
from core.runtime.tool_registry import (
    ToolCallContext,
    ToolCategory,
    ToolRegistry,
    ToolSeverity,
    ToolSpec,
    get_tool_registry,
)

logger = logging.getLogger(__name__)

try:
    from gradio_client import Client as GradioClient

    GRADIO_AVAILABLE = True
except ImportError:
    GRADIO_AVAILABLE = False
    GradioClient = None  # type: ignore[assignment,misc]


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class AniGenConfig:
    """AniGen HuggingFace Space configuration."""

    space_id: str = "damBruh/SkyyRose-AniGen"
    hf_token: str = field(
        default_factory=lambda: os.getenv("HUGGINGFACE_TOKEN", "") or os.getenv("HF_TOKEN", "")
    )
    # 52s preview + 18s extract + generous buffer for cold-start wakeup
    timeout: float = 240.0
    output_dir: str = field(
        default_factory=lambda: os.getenv("ANIGEN_OUTPUT_DIR", "./generated_assets/3d/anigen")
    )

    @classmethod
    def from_env(cls) -> AniGenConfig:
        """Create config from environment variables."""
        return cls()

    def validate(self) -> None:
        """Raise if required credentials are missing."""
        if not self.hf_token:
            raise ValueError(
                "HUGGINGFACE_TOKEN or HF_TOKEN environment variable is required "
                "to access damBruh/SkyyRose-AniGen (private Space)."
            )


# =============================================================================
# Models
# =============================================================================


class AniGenResult(BaseModel):
    """AniGen 3D generation result."""

    task_id: str
    model_path: str
    model_url: str = ""
    format: str = "glb"
    joint_count: int = 10
    has_rig: bool = True
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# AniGen Agent
# =============================================================================


class AniGenAgent(SuperAgent):
    """
    AniGen Garment Rigging Agent.

    Generates rigged, animatable 3D garments from product images by calling
    the damBruh/SkyyRose-AniGen HuggingFace Space via gradio_client.

    Image-to-3D only; AniGen does not support text-to-3D.
    Output GLB carries a 10-joint T-pose rig ready for Mixamo clip retargeting
    in the Three.js immersive worlds pipeline.

    Usage:
        agent = AniGenAgent()

        # From image
        result = await agent.run({
            "action": "generate_from_image",
            "image_url": "/path/to/product.jpg",
            "product_name": "Black Rose Crewneck",
        })

    Direct call (used by ThreeDRoundTable):
        result = await agent._tool_generate_from_image(
            image_url="/path/to/product.jpg",
            product_name="Black Rose Crewneck",
        )
    """

    def __init__(
        self,
        config: AniGenConfig | None = None,
        registry: ToolRegistry | None = None,
    ) -> None:
        agent_config = AgentConfig(
            name="anigen_garment",
            description=(
                "AniGen Garment Rigging Agent — image-to-rigged-GLB via "
                "damBruh/SkyyRose-AniGen HF Space"
            ),
            version="1.0.0",
            capabilities={
                AgentCapability.THREE_D_GENERATION,
                AgentCapability.IMAGE_GENERATION,
            },
            llm_category=LLMCategory.CATEGORY_B,
            tool_category=ToolCategory.MEDIA,
            default_timeout=240.0,
        )

        super().__init__(agent_config, registry or get_tool_registry())

        if not GRADIO_AVAILABLE:
            logger.warning(
                "gradio_client not installed — AniGen unavailable. "
                "Install with: pip install gradio_client"
            )

        self.config = config or AniGenConfig.from_env()
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)

    def _register_tools(self) -> None:
        """Register AniGen-specific tools."""
        self.registry.register(
            ToolSpec(
                name="anigen_generate_from_image",
                description="Generate rigged 3D garment from product image using AniGen",
                category=ToolCategory.MEDIA,
                severity=ToolSeverity.MEDIUM,
                timeout_seconds=240.0,
                idempotent=False,
            ),
            self._tool_generate_from_image,
        )

    # -------------------------------------------------------------------------
    # SuperAgent Implementation
    # -------------------------------------------------------------------------

    async def _plan(
        self,
        request: dict[str, Any],
        context: ToolCallContext,
    ) -> list[PlanStep]:
        """Create execution plan — single step for image-to-3D."""
        action = request.get("action", "generate_from_image")

        if action != "generate_from_image":
            raise ValueError(f"AniGen only supports 'generate_from_image'. Got: {action}")

        return [
            PlanStep(
                step_id="gen_image",
                tool_name="anigen_generate_from_image",
                description="Generate rigged GLB from product image via AniGen HF Space",
                inputs={
                    "image_url": request.get("image_url", ""),
                    "product_name": request.get("product_name", "SkyyRose Product"),
                },
                priority=0,
            )
        ]

    async def _retrieve(
        self,
        request: dict[str, Any],
        plan: list[PlanStep],
        context: ToolCallContext,
    ) -> RetrievalContext:
        """No retrieval needed for AniGen — image drives the generation entirely."""
        return RetrievalContext(
            query="anigen garment generation",
            documents=[],
            sources=[],
        )

    async def _execute_step(
        self,
        step: PlanStep,
        retrieval_context: RetrievalContext,
        context: ToolCallContext,
    ) -> ExecutionResult:
        """Execute a single plan step."""
        started_at = datetime.now(UTC)

        try:
            result = await self.registry.execute(
                step.tool_name,
                step.inputs,
                context,
            )

            return ExecutionResult(
                tool_name=step.tool_name,
                step_id=step.step_id,
                success=result.success,
                result=result.result,
                error=result.error,
                duration_seconds=result.duration_seconds,
                started_at=started_at,
                completed_at=datetime.now(UTC),
                retries=result.retries,
            )
        except Exception as e:
            return ExecutionResult(
                tool_name=step.tool_name,
                step_id=step.step_id,
                success=False,
                error=str(e),
                error_type=type(e).__name__,
                started_at=started_at,
                completed_at=datetime.now(UTC),
            )

    async def _validate(
        self,
        results: list[ExecutionResult],
        context: ToolCallContext,
    ) -> ValidationResult:
        """Validate that the GLB was produced."""
        validation = ValidationResult(is_valid=True)

        for result in results:
            if not result.success:
                validation.add_error(f"{result.tool_name} failed: {result.error}")
            elif result.result:
                model_path = result.result.get("model_path", "")
                if model_path and not Path(model_path).exists():
                    validation.add_warning(f"Output file not found on disk: {model_path}")

        if validation.is_valid:
            validation.quality_score = 85.0
            validation.confidence_score = 0.9

        return validation

    async def _emit(
        self,
        results: list[ExecutionResult],
        validation: ValidationResult,
        context: ToolCallContext,
    ) -> dict[str, Any]:
        """Emit final structured output."""
        output: dict[str, Any] = {
            "status": "success" if validation.is_valid else "error",
            "agent": self.name,
            "request_id": context.request_id,
            "validation": validation.to_dict(),
        }

        for result in results:
            if result.tool_name == "anigen_generate_from_image" and result.success:
                output["data"] = result.result
                break

        output["results"] = [r.to_dict() for r in results]
        return output

    # -------------------------------------------------------------------------
    # Tool Implementations
    # -------------------------------------------------------------------------

    async def _tool_generate_from_image(
        self,
        image_url: str,
        product_name: str = "SkyyRose Product",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Generate a rigged GLB from a product image via AniGen HF Space.

        Two-stage pipeline (runs in a thread to avoid blocking the event loop):
          Stage 1  fn_index=7  → generate_preview (~52s, latent mesh)
          Stage 2  fn_index=10 → extract_glb      (~18s, final export)

        Args:
            image_url: Local file path or URL to the product image.
            product_name: Human-readable name for output file naming.

        Returns:
            dict with model_path, model_url, joint_count, has_rig, metadata.

        Raises:
            RuntimeError: If gradio_client is not installed.
            ValueError: If HF token is missing.
            TimeoutError: If the Space does not respond within config.timeout.
        """
        if not GRADIO_AVAILABLE:
            raise RuntimeError(
                "gradio_client is required for AniGen. Install with: pip install gradio_client"
            )

        self.config.validate()

        start = time.time()
        task_id = uuid.uuid4().hex[:8]

        def _sync_pipeline() -> str:
            """Run the three-stage AniGen pipeline in a thread (stateful session).

            Stages (all use same client session so Gradio State persists):
              1. /prepare_input_for_generation  — uploads + preprocesses image into session state
              2. /generate_preview              — SS+SLAT diffusion, ~52s, produces skeleton GLB
              3. /extract_glb                   — texture bake + mesh export, ~18s, final rigged GLB
            """
            client = GradioClient(
                self.config.space_id,
                token=self.config.hf_token,
                httpx_kwargs={"timeout": 120.0},
            )

            # Stage 1: upload + preprocess image (result stored in Gradio session State)
            logger.info(
                "AniGen stage 0: prepare_input product=%s image=%s task_id=%s",
                product_name,
                str(image_url)[:80],
                task_id,
            )
            client.predict(image_url, api_name="/prepare_input_for_generation")

            # Stage 2: diffusion pass (~52s) — reads image from session State
            logger.info("AniGen stage 1: generate_preview task_id=%s", task_id)
            client.predict(
                42,  # seed
                "ss_flow_duet",  # ss_model_name — best quality/speed balance
                "slat_flow_auto",  # slat_model_name
                7.5,  # ss_guidance_strength
                25,  # ss_sampling_steps
                3.0,  # slat_guidance_strength
                25,  # slat_sampling_steps
                1,  # joints_density
                api_name="/generate_preview",
            )

            # Stage 3: texture bake + final GLB export (~18s)
            logger.info("AniGen stage 2: extract_glb task_id=%s", task_id)
            extract_outputs = client.predict(
                1024,  # texture_size
                0.95,  # simplify_ratio
                True,  # fill_holes
                api_name="/extract_glb",
            )

            # extract_outputs[1] = "Skeleton Preview / Final GLB" (rigged)
            # extract_outputs[0] = "Generated Mesh" (no rig)
            return str(extract_outputs[1])

        raw_glb_path = await asyncio.wait_for(
            asyncio.to_thread(_sync_pipeline),
            timeout=self.config.timeout,
        )

        duration = time.time() - start

        # Copy GLB into managed output directory
        safe_name = "".join(c if c.isalnum() else "_" for c in product_name)[:40]
        dest_filename = f"{safe_name}_{task_id}.glb"
        dest_path = Path(self.config.output_dir) / dest_filename

        src = Path(raw_glb_path)
        if src.exists() and src.resolve() != dest_path.resolve():
            shutil.copy2(src, dest_path)
            output_path = str(dest_path)
        else:
            output_path = raw_glb_path

        logger.info(
            "AniGen generation complete product=%s output=%s duration=%ss task_id=%s",
            product_name,
            output_path,
            f"{duration:.1f}",
            task_id,
        )

        return {
            "task_id": task_id,
            "model_path": output_path,
            "model_url": "",
            "format": "glb",
            "joint_count": 10,
            "has_rig": True,
            "metadata": {
                "space_id": self.config.space_id,
                "product_name": product_name,
                "source_image": str(image_url),
                "duration_seconds": duration,
                "fn_index_preview": 7,
                "fn_index_extract": 10,
            },
        }

    async def _tool_generate_from_description(
        self,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """AniGen is image-to-3D only; text-to-3D is not supported."""
        raise NotImplementedError(
            "AniGen requires a product image. Use _tool_generate_from_image(image_url=...) instead."
        )
