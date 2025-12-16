"""
Tripo3D Asset Generation Agent
==============================

Generate 3D clothing models using Tripo3D API.

Features:
- Text-to-3D generation
- Image-to-3D generation
- Multiple output formats (GLB, FBX, OBJ, USDZ)
- SkyyRose brand-aware prompting
- Automatic texture generation

API Documentation: https://docs.tripo3d.ai/
Pricing: Pay-per-generation model

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import aiofiles
import aiohttp
from pydantic import BaseModel, Field

from base import (
    AgentCapability,
    AgentConfig,
    ExecutionResult,
    LLMCategory,
    PlanStep,
    RetrievalContext,
    SuperAgent,
    ValidationResult,
)
from runtime.tools import (
    ToolCallContext,
    ToolCategory,
    ToolRegistry,
    ToolSeverity,
    ToolSpec,
    get_tool_registry,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration & Enums
# =============================================================================


class TripoTaskStatus(str, Enum):
    """Tripo task status."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ModelFormat(str, Enum):
    """3D model output formats."""

    GLB = "glb"  # Binary glTF - recommended for web
    GLTF = "gltf"  # JSON glTF
    FBX = "fbx"  # Autodesk FBX
    OBJ = "obj"  # Wavefront OBJ
    USDZ = "usdz"  # Apple AR format
    STL = "stl"  # 3D printing


class ModelStyle(str, Enum):
    """Generation style presets."""

    REALISTIC = "realistic"
    CARTOON = "cartoon"
    ANIME = "anime"
    LOW_POLY = "low-poly"


@dataclass
class TripoConfig:
    """Tripo3D configuration."""

    api_key: str = field(
        default_factory=lambda: os.getenv("TRIPO_API_KEY", "")
        or os.getenv("TRIPO3D_API_KEY", "")
    )
    base_url: str = "https://api.tripo3d.ai/v2"
    timeout: float = 300.0  # 5 minutes for generation
    poll_interval: float = 2.0
    max_retries: int = 3
    output_dir: str = "./generated_assets/3d"

    @classmethod
    def from_env(cls) -> TripoConfig:
        """Create config from environment variables."""
        return cls(
            api_key=os.getenv("TRIPO_API_KEY", "") or os.getenv("TRIPO3D_API_KEY", ""),
            output_dir=os.getenv("TRIPO_OUTPUT_DIR", "./generated_assets/3d"),
        )


# =============================================================================
# SkyyRose Brand Prompts
# =============================================================================

SKYYROSE_BRAND_DNA = """
Brand: SkyyRose
Philosophy: "Where Love Meets Luxury"
Location: Oakland, California
Style: Gender-neutral luxury streetwear
Colors: Rose gold (#D4AF37), Obsidian black (#0D0D0D), Ivory (#F5F5F0)
Aesthetic: Elevated street poetry, intellectual luxury, premium materials
Quality: High-end construction, attention to detail, exclusive limited editions
"""

COLLECTION_PROMPTS = {
    "BLACK_ROSE": {
        "style": "dark elegance, limited edition, exclusive",
        "colors": "deep black, subtle rose gold accents, matte finish",
        "mood": "mysterious, sophisticated, rare",
    },
    "LOVE_HURTS": {
        "style": "emotional expression, storytelling through design",
        "colors": "deep reds, black, heart motifs",
        "mood": "passionate, vulnerable, powerful",
    },
    "SIGNATURE": {
        "style": "timeless essentials, foundation wardrobe",
        "colors": "clean neutrals, rose gold details",
        "mood": "classic, versatile, elevated basics",
    },
}

GARMENT_TEMPLATES = {
    "hoodie": "luxury streetwear hoodie, premium heavyweight cotton, relaxed fit, kangaroo pocket",
    "bomber": "premium bomber jacket, satin lining, ribbed cuffs and hem, quality hardware",
    "track_pants": "luxury track pants, side stripe detail, tapered fit, premium fabric",
    "tee": "premium t-shirt, heavyweight cotton, relaxed fit, quality construction",
    "sweatshirt": "luxury crewneck sweatshirt, heavyweight fleece, ribbed details",
    "jacket": "structured jacket, premium materials, tailored streetwear fit",
    "shorts": "luxury shorts, premium cotton, embroidered details",
    "cap": "structured cap, quality embroidery, adjustable strap",
    "beanie": "luxury knit beanie, soft premium yarn, embroidered logo",
}


# =============================================================================
# Models
# =============================================================================


class TripoTask(BaseModel):
    """Tripo generation task."""

    task_id: str
    status: TripoTaskStatus
    progress: int = 0
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: str = ""
    completed_at: str | None = None

    # Model details
    model_url: str | None = None
    texture_url: str | None = None
    thumbnail_url: str | None = None


class GenerationResult(BaseModel):
    """3D generation result."""

    task_id: str
    model_path: str
    model_url: str
    format: ModelFormat
    texture_path: str | None = None
    thumbnail_path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Tracking
    duration_seconds: float = 0.0
    retries: int = 0


class AssetValidation(BaseModel):
    """3D asset validation result."""

    is_valid: bool = True
    polycount: int | None = None
    texture_size: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


# =============================================================================
# Tripo3D Agent
# =============================================================================


class TripoAssetAgent(SuperAgent):
    """
    Tripo3D Asset Generation Agent.

    Generates 3D clothing models for SkyyRose products.

    Usage:
        agent = TripoAssetAgent()

        # From description
        result = await agent.run({
            "action": "generate_from_description",
            "product_name": "Heart aRose Bomber",
            "collection": "BLACK_ROSE",
            "garment_type": "bomber",
            "additional_details": "Rose gold zipper, embroidered rose on back",
        })

        # From image
        result = await agent.run({
            "action": "generate_from_image",
            "image_path": "/path/to/design.jpg",
            "product_name": "Custom Hoodie",
        })
    """

    def __init__(
        self,
        config: TripoConfig | None = None,
        registry: ToolRegistry | None = None,
    ) -> None:
        agent_config = AgentConfig(
            name="tripo_asset",
            description="Tripo3D Asset Generation Agent for 3D model creation",
            version="1.0.0",
            capabilities={
                AgentCapability.THREE_D_GENERATION,
                AgentCapability.IMAGE_GENERATION,
            },
            llm_category=LLMCategory.CATEGORY_B,
            tool_category=ToolCategory.MEDIA,
            default_timeout=300.0,
        )

        super().__init__(agent_config, registry or get_tool_registry())

        self.tripo_config = config or TripoConfig.from_env()
        self._session: aiohttp.ClientSession | None = None

        # Ensure output directory
        Path(self.tripo_config.output_dir).mkdir(parents=True, exist_ok=True)

    def _register_tools(self) -> None:
        """Register Tripo-specific tools."""
        self.registry.register(
            ToolSpec(
                name="tripo_generate_from_text",
                description="Generate 3D model from text description",
                category=ToolCategory.MEDIA,
                severity=ToolSeverity.MEDIUM,
                timeout_seconds=300.0,
                idempotent=False,
            ),
            self._tool_generate_from_text,
        )

        self.registry.register(
            ToolSpec(
                name="tripo_generate_from_image",
                description="Generate 3D model from reference image",
                category=ToolCategory.MEDIA,
                severity=ToolSeverity.MEDIUM,
                timeout_seconds=300.0,
            ),
            self._tool_generate_from_image,
        )

        self.registry.register(
            ToolSpec(
                name="tripo_validate_asset",
                description="Validate generated 3D asset",
                category=ToolCategory.MEDIA,
                severity=ToolSeverity.READ_ONLY,
            ),
            self._tool_validate_asset,
        )

    # -------------------------------------------------------------------------
    # SuperAgent Implementation
    # -------------------------------------------------------------------------

    async def _plan(
        self,
        request: dict[str, Any],
        context: ToolCallContext,
    ) -> list[PlanStep]:
        """Create execution plan based on request action."""
        action = request.get("action", "generate_from_description")

        steps = []

        if action == "generate_from_description":
            steps.append(
                PlanStep(
                    step_id="gen_text",
                    tool_name="tripo_generate_from_text",
                    description="Generate 3D model from description",
                    inputs={
                        "product_name": request.get("product_name", "Product"),
                        "collection": request.get("collection", "SIGNATURE"),
                        "garment_type": request.get("garment_type", "tee"),
                        "additional_details": request.get("additional_details", ""),
                        "output_format": request.get("output_format", ModelFormat.GLB.value),
                    },
                    priority=0,
                ),
            )
        elif action == "generate_from_image":
            steps.append(
                PlanStep(
                    step_id="gen_image",
                    tool_name="tripo_generate_from_image",
                    description="Generate 3D model from image",
                    inputs={
                        "image_path": request.get("image_path"),
                        "product_name": request.get("product_name", "Product"),
                        "output_format": request.get("output_format", ModelFormat.GLB.value),
                    },
                    priority=0,
                ),
            )
        else:
            raise ValueError(f"Unknown action: {action}")

        # Add validation step
        steps.append(
            PlanStep(
                step_id="validate",
                tool_name="tripo_validate_asset",
                description="Validate generated 3D asset",
                inputs={"model_path": "{model_path}"},
                depends_on=[steps[0].step_id],
                priority=1,
            ),
        )

        return steps

    async def _retrieve(
        self,
        request: dict[str, Any],
        plan: list[PlanStep],
        context: ToolCallContext,
    ) -> RetrievalContext:
        """Retrieve brand context for generation."""
        collection = request.get("collection", "SIGNATURE").upper()
        collection_context = COLLECTION_PROMPTS.get(collection, COLLECTION_PROMPTS["SIGNATURE"])

        return RetrievalContext(
            query=f"SkyyRose {collection} collection context",
            documents=[
                {"content": SKYYROSE_BRAND_DNA, "type": "brand_dna"},
                {"content": str(collection_context), "type": "collection_style"},
            ],
            sources=["brand_guidelines", "collection_prompts"],
        )

    async def _execute_step(
        self,
        step: PlanStep,
        retrieval_context: RetrievalContext,
        context: ToolCallContext,
    ) -> ExecutionResult:
        """Execute a single step."""
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
        """Validate execution results."""
        validation = ValidationResult(is_valid=True)

        for result in results:
            if not result.success:
                validation.add_error(f"{result.tool_name} failed: {result.error}")

        # Check asset validation result
        for result in results:
            if result.tool_name == "tripo_validate_asset" and result.result:
                asset_validation = result.result
                if not asset_validation.get("is_valid", True):
                    for error in asset_validation.get("errors", []):
                        validation.add_error(error)
                for warning in asset_validation.get("warnings", []):
                    validation.add_warning(warning)

        if not validation.errors:
            validation.quality_score = 0.9
            validation.confidence_score = 0.85

        return validation

    async def _emit(
        self,
        results: list[ExecutionResult],
        validation: ValidationResult,
        context: ToolCallContext,
    ) -> dict[str, Any]:
        """Emit final structured output."""
        output = {
            "status": "success" if validation.is_valid else "error",
            "agent": self.name,
            "request_id": context.request_id,
            "validation": validation.to_dict(),
        }

        # Find generation result
        for result in results:
            if result.tool_name.startswith("tripo_generate") and result.success:
                output["data"] = result.result
                break

        output["results"] = [r.to_dict() for r in results]

        return output

    # -------------------------------------------------------------------------
    # Tool Implementations
    # -------------------------------------------------------------------------

    def _build_prompt(
        self,
        product_name: str,
        collection: str,
        garment_type: str,
        additional_details: str = "",
    ) -> str:
        """Build optimized prompt for 3D generation."""
        collection_style = COLLECTION_PROMPTS.get(
            collection.upper(),
            COLLECTION_PROMPTS["SIGNATURE"],
        )

        garment_base = GARMENT_TEMPLATES.get(
            garment_type.lower(),
            "luxury streetwear garment, premium quality",
        )

        prompt_parts = [
            f"3D model of {product_name}",
            garment_base,
            f"Style: {collection_style['style']}",
            f"Colors: {collection_style['colors']}",
            "High quality mesh, clean topology, quad-based geometry",
            "Photorealistic textures, PBR materials",
            "Fashion product visualization, e-commerce ready",
        ]

        if additional_details:
            prompt_parts.append(additional_details)

        return ". ".join(prompt_parts)

    async def _tool_generate_from_text(
        self,
        product_name: str,
        collection: str = "SIGNATURE",
        garment_type: str = "tee",
        additional_details: str = "",
        output_format: str = "glb",
    ) -> dict[str, Any]:
        """Generate 3D model from text description."""
        await self._ensure_session()

        prompt = self._build_prompt(product_name, collection, garment_type, additional_details)

        # Create task
        response = await self._api_request(
            "POST",
            "/task",
            {
                "type": "text_to_model",
                "prompt": prompt,
                "model_version": "v2.0-20240919",
            },
        )

        task_id = response.get("data", {}).get("task_id")
        if not task_id:
            raise ValueError("No task ID returned")

        # Poll for result
        task = await self._poll_task(task_id)

        # Download model
        if task.model_url:
            filename = f"{product_name.lower().replace(' ', '_')}_{task_id[:8]}.{output_format}"
            model_path = await self._download_file(task.model_url, filename)

            result = GenerationResult(
                task_id=task_id,
                model_path=model_path,
                model_url=task.model_url,
                format=ModelFormat(output_format),
                metadata={
                    "product_name": product_name,
                    "collection": collection,
                    "garment_type": garment_type,
                    "prompt": prompt,
                },
            )

            # Download texture if available
            if task.texture_url:
                texture_filename = (
                    f"{product_name.lower().replace(' ', '_')}_{task_id[:8]}_texture.png"
                )
                result.texture_path = await self._download_file(task.texture_url, texture_filename)

            # Download thumbnail if available
            if task.thumbnail_url:
                thumb_filename = f"{product_name.lower().replace(' ', '_')}_{task_id[:8]}_thumb.png"
                result.thumbnail_path = await self._download_file(
                    task.thumbnail_url, thumb_filename
                )

            return result.model_dump()

        raise ValueError("No model generated")

    async def _tool_generate_from_image(
        self,
        image_path: str,
        product_name: str = "Product",
        output_format: str = "glb",
    ) -> dict[str, Any]:
        """Generate 3D model from reference image."""
        await self._ensure_session()

        # Encode image
        async with aiofiles.open(image_path, "rb") as f:
            image_data = await f.read()

        b64_image = base64.b64encode(image_data).decode()

        # Create task
        response = await self._api_request(
            "POST",
            "/task",
            {
                "type": "image_to_model",
                "file": {
                    "type": "png" if image_path.endswith(".png") else "jpg",
                    "data": b64_image,
                },
                "model_version": "v2.0-20240919",
            },
        )

        task_id = response.get("data", {}).get("task_id")
        if not task_id:
            raise ValueError("No task ID returned")

        task = await self._poll_task(task_id)

        if task.model_url:
            filename = f"{product_name.lower().replace(' ', '_')}_{task_id[:8]}.{output_format}"
            model_path = await self._download_file(task.model_url, filename)

            return GenerationResult(
                task_id=task_id,
                model_path=model_path,
                model_url=task.model_url,
                format=ModelFormat(output_format),
                metadata={
                    "product_name": product_name,
                    "source_image": image_path,
                },
            ).model_dump()

        raise ValueError("No model generated")

    async def _tool_validate_asset(
        self,
        model_path: str,
    ) -> dict[str, Any]:
        """Validate generated 3D asset (stub - would check polycount, textures, etc.)."""
        # In production, this would use a 3D library to validate the mesh
        validation = AssetValidation(
            is_valid=True,
            warnings=[],
            errors=[],
        )

        # Basic file existence check
        if not Path(model_path).exists():
            validation.is_valid = False
            validation.errors.append(f"Model file not found: {model_path}")

        # Check file size (rough proxy for polycount)
        if Path(model_path).exists():
            size_mb = Path(model_path).stat().st_size / (1024 * 1024)
            if size_mb > 50:
                validation.warnings.append(f"Large file size: {size_mb:.1f}MB")
            if size_mb < 0.01:
                validation.warnings.append("Very small file size - may be incomplete")

        return validation.model_dump()

    # -------------------------------------------------------------------------
    # HTTP Client Methods
    # -------------------------------------------------------------------------

    async def _ensure_session(self) -> None:
        """Ensure aiohttp session exists."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.tripo_config.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=self.tripo_config.timeout),
            )

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _api_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make API request with retry logic."""
        await self._ensure_session()

        url = f"{self.tripo_config.base_url}/{endpoint.lstrip('/')}"
        last_error: Exception | None = None

        for attempt in range(self.tripo_config.max_retries):
            try:
                async with self._session.request(method, url, json=data) as response:
                    result = await response.json()

                    if response.status >= 400:
                        error_msg = result.get("message", str(result))
                        raise Exception(f"Tripo API error ({response.status}): {error_msg}")

                    return result
            except aiohttp.ClientError as e:
                last_error = e
                if attempt < self.tripo_config.max_retries - 1:
                    await asyncio.sleep(2**attempt)

        raise last_error or Exception("API request failed")

    async def _poll_task(self, task_id: str) -> TripoTask:
        """Poll task until completion."""
        while True:
            result = await self._api_request("GET", f"/task/{task_id}")

            data = result.get("data", {})
            task = TripoTask(
                task_id=task_id,
                status=TripoTaskStatus(data.get("status", "queued")),
                progress=data.get("progress", 0),
                result=data.get("output"),
            )

            if task.status == TripoTaskStatus.SUCCESS:
                output = data.get("output", {})
                task.model_url = output.get("model", {}).get("url")
                task.texture_url = output.get("pbr_model", {}).get("url")
                task.thumbnail_url = output.get("rendered_image", {}).get("url")
                task.completed_at = datetime.now(UTC).isoformat()
                return task

            if task.status == TripoTaskStatus.FAILED:
                task.error = data.get("error", "Unknown error")
                raise Exception(f"Task failed: {task.error}")

            if task.status == TripoTaskStatus.CANCELLED:
                raise Exception("Task was cancelled")

            logger.debug(f"Task {task_id}: {task.status.value} ({task.progress}%)")
            await asyncio.sleep(self.tripo_config.poll_interval)

    async def _download_file(self, url: str, filename: str) -> str:
        """Download file to output directory."""
        await self._ensure_session()

        filepath = Path(self.tripo_config.output_dir) / filename

        async with self._session.get(url) as response:
            if response.status >= 400:
                raise Exception(f"Download failed: {response.status}")

            async with aiofiles.open(filepath, "wb") as f:
                async for chunk in response.content.iter_chunked(8192):
                    await f.write(chunk)

        logger.info(f"Downloaded: {filepath}")
        return str(filepath)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "TripoAssetAgent",
    "TripoConfig",
    "TripoTask",
    "GenerationResult",
    "AssetValidation",
    "ModelFormat",
    "ModelStyle",
    "TripoTaskStatus",
    "SKYYROSE_BRAND_DNA",
    "COLLECTION_PROMPTS",
    "GARMENT_TEMPLATES",
]
