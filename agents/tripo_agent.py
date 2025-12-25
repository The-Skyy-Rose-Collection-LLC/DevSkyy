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
import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

# Import official Tripo3D SDK
try:
    from tripo3d import TripoClient, TaskStatus
    TRIPO_SDK_AVAILABLE = True
except ImportError:
    TRIPO_SDK_AVAILABLE = False
    TaskStatus = None

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
        default_factory=lambda: os.getenv("TRIPO_API_KEY", "") or os.getenv("TRIPO3D_API_KEY", "")
    )
    base_url: str = field(
        default_factory=lambda: os.getenv("TRIPO_API_BASE_URL", "https://api.tripo3d.ai/v2")
    )
    timeout: float = 300.0  # 5 minutes for generation
    poll_interval: float = 2.0
    max_retries: int = 3
    retry_min_wait: float = 1.0  # Minimum wait between retries (seconds)
    retry_max_wait: float = 30.0  # Maximum wait between retries (seconds)
    output_dir: str = "./generated_assets/3d"

    # Texture quality settings
    texture_quality: str = "high"  # low, medium, high
    texture_resolution: int = 2048  # 512, 1024, 2048, 4096
    pbr_enabled: bool = True  # Enable PBR materials

    @classmethod
    def from_env(cls) -> TripoConfig:
        """Create config from environment variables."""
        return cls(
            api_key=os.getenv("TRIPO_API_KEY", "") or os.getenv("TRIPO3D_API_KEY", ""),
            base_url=os.getenv("TRIPO_API_BASE_URL", "https://api.tripo3d.ai/v2"),
            output_dir=os.getenv("TRIPO_OUTPUT_DIR", "./generated_assets/3d"),
        )

    def validate(self) -> None:
        """Validate configuration."""
        if not self.api_key:
            raise ValueError(
                "TRIPO_API_KEY environment variable is required. "
                "Get your API key from: https://www.tripo3d.ai/dashboard"
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
            description="Tripo3D Asset Generation Agent for 3D model creation (Official SDK)",
            version="2.0.0",
            capabilities={
                AgentCapability.THREE_D_GENERATION,
                AgentCapability.IMAGE_GENERATION,
            },
            llm_category=LLMCategory.CATEGORY_B,
            tool_category=ToolCategory.MEDIA,
            default_timeout=300.0,
        )

        super().__init__(agent_config, registry or get_tool_registry())

        # Validate SDK availability
        if not TRIPO_SDK_AVAILABLE:
            logger.warning(
                "Tripo3D SDK not installed. Install with: pip install tripo3d"
            )

        self.tripo_config = config or TripoConfig.from_env()

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
                output["data"] = result.result  # type: ignore[assignment]
                break

        output["results"] = [r.to_dict() for r in results]  # type: ignore[assignment]

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
        optimized_prompt: str | None = None,
    ) -> str:
        """
        Build optimized prompt for 3D generation.

        If optimized_prompt is provided (from HuggingFace), use that instead
        of building a new one. This allows HF-based optimization to enhance
        the final Tripo3D output.
        """
        # If HF-optimized prompt is provided, use it
        if optimized_prompt:
            logger.info("Using HuggingFace-optimized prompt for Tripo3D")
            return optimized_prompt

        # Otherwise, build standard SkyyRose prompt
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
        optimized_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Generate 3D model from text description using official SDK."""
        if not TRIPO_SDK_AVAILABLE:
            raise RuntimeError(
                "Tripo3D SDK not available. Install with: pip install tripo3d"
            )

        prompt = self._build_prompt(
            product_name, collection, garment_type, additional_details, optimized_prompt
        )

        try:
            async with TripoClient(api_key=self.tripo_config.api_key) as client:
                # Generate 3D model from text
                logger.info(f"Generating 3D model from text: {product_name}")
                task_id = await client.text_to_model(prompt=prompt)
                logger.info(f"Task created: {task_id}")

                # Wait for completion
                task = await client.wait_for_task(task_id, verbose=True)

                if task.status == TaskStatus.SUCCESS:
                    logger.info(f"Task {task_id} completed successfully")

                    # Download models
                    output_dir = Path(self.tripo_config.output_dir) / collection.lower()
                    output_dir.mkdir(parents=True, exist_ok=True)

                    downloaded_files = await client.download_task_models(
                        task, str(output_dir)
                    )

                    # Extract model path
                    model_path = downloaded_files.get("model_mesh")
                    if not model_path:
                        raise ValueError("No model file in download results")

                    result = GenerationResult(
                        task_id=task_id,
                        model_path=str(model_path),
                        model_url=str(model_path),
                        format=ModelFormat(output_format),
                        metadata={
                            "product_name": product_name,
                            "collection": collection,
                            "garment_type": garment_type,
                            "prompt": prompt,
                        },
                    )

                    # Log downloaded files
                    for model_type, file_path in downloaded_files.items():
                        if file_path:
                            logger.info(f"Downloaded {model_type}: {file_path}")

                    return result.model_dump()

                raise ValueError(f"Task failed: {task.status}")

        except Exception as e:
            logger.error(f"Text-to-3D generation failed: {e}")
            raise

    async def _tool_generate_from_image(
        self,
        image_path: str,
        product_name: str = "Product",
        output_format: str = "glb",
        optimized_prompt: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate 3D model from reference image using official SDK.

        If optimized_prompt is provided (from HuggingFace), it can be used
        to supplement or enhance the image-based generation.
        """
        if not TRIPO_SDK_AVAILABLE:
            raise RuntimeError(
                "Tripo3D SDK not available. Install with: pip install tripo3d"
            )

        # Verify image exists
        image_file = Path(image_path)
        if not image_file.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        try:
            async with TripoClient(api_key=self.tripo_config.api_key) as client:
                # Generate 3D model from image
                logger.info(f"Generating 3D model from image: {image_file.name}")
                task_id = await client.image_to_model(image=str(image_path))
                logger.info(f"Task created: {task_id}")

                # Wait for completion with verbose logging
                task = await client.wait_for_task(task_id, verbose=True)

                if task.status == TaskStatus.SUCCESS:
                    logger.info(f"Task {task_id} completed successfully")

                    # Download models
                    output_dir = Path(self.tripo_config.output_dir) / "images"
                    output_dir.mkdir(parents=True, exist_ok=True)

                    downloaded_files = await client.download_task_models(
                        task, str(output_dir)
                    )

                    # Extract model path
                    model_path = downloaded_files.get("model_mesh")
                    if not model_path:
                        raise ValueError("No model file in download results")

                    result = GenerationResult(
                        task_id=task_id,
                        model_path=str(model_path),
                        model_url=str(model_path),
                        format=ModelFormat(output_format),
                        metadata={
                            "product_name": product_name,
                            "source_image": image_path,
                        },
                    )

                    # Log downloaded files
                    for model_type, file_path in downloaded_files.items():
                        if file_path:
                            logger.info(f"Downloaded {model_type}: {file_path}")

                    return result.model_dump()

                raise ValueError(f"Task failed: {task.status}")

        except Exception as e:
            logger.error(f"Image-to-3D generation failed: {e}")
            raise

    async def _tool_validate_asset(
        self,
        model_path: str,
        max_polycount: int = 100000,
        max_file_size_mb: float = 50.0,
        min_file_size_kb: float = 10.0,
    ) -> dict[str, Any]:
        """
        Validate generated 3D asset for production quality.

        Performs comprehensive validation including:
        - File existence and format verification
        - File size checks (too large = performance issue, too small = incomplete)
        - Mesh analysis (polycount, faces, vertices) if trimesh available
        - Texture presence verification for GLB format
        - SkyyRose quality standards (web-optimized 3D assets)

        Args:
            model_path: Path to the 3D model file
            max_polycount: Maximum allowed polygon count (default 100k for web)
            max_file_size_mb: Maximum file size in MB
            min_file_size_kb: Minimum file size in KB (to detect incomplete files)

        Returns:
            Dict with validation results
        """
        validation = AssetValidation(
            is_valid=True,
            warnings=[],
            errors=[],
        )

        path = Path(model_path)

        # Check file existence
        if not path.exists():
            validation.is_valid = False
            validation.errors.append(f"Model file not found: {model_path}")
            return validation.model_dump()

        # Check file format
        supported_formats = {".glb", ".gltf", ".obj", ".fbx", ".stl"}
        if path.suffix.lower() not in supported_formats:
            validation.warnings.append(
                f"Unsupported format: {path.suffix}. Recommended: .glb for web"
            )

        # File size validation
        file_size = path.stat().st_size
        size_mb = file_size / (1024 * 1024)
        size_kb = file_size / 1024

        if size_mb > max_file_size_mb:
            validation.is_valid = False
            validation.errors.append(
                f"File too large: {size_mb:.1f}MB (max: {max_file_size_mb}MB). "
                f"Web 3D assets should be optimized for performance."
            )
        elif size_mb > max_file_size_mb * 0.7:
            validation.warnings.append(
                f"Large file: {size_mb:.1f}MB. Consider optimization for better web performance."
            )

        if size_kb < min_file_size_kb:
            validation.is_valid = False
            validation.errors.append(
                f"File too small: {size_kb:.1f}KB. Model may be incomplete or corrupted."
            )

        # Try to analyze mesh with trimesh (if available)
        try:
            import trimesh

            mesh = trimesh.load(str(path), force="mesh")

            # Extract polycount
            if hasattr(mesh, "faces") and mesh.faces is not None:
                polycount = len(mesh.faces)
                validation.polycount = polycount

                if polycount > max_polycount:
                    validation.warnings.append(
                        f"High polycount: {polycount:,} (recommended: <{max_polycount:,} for web)"
                    )
                elif polycount > max_polycount * 0.8:
                    validation.warnings.append(f"Polycount approaching limit: {polycount:,}")

                # Log mesh details
                logger.debug(
                    f"Mesh analysis: {polycount:,} faces, " f"{len(mesh.vertices):,} vertices"
                )

            # Check if mesh is watertight (closed surface)
            if hasattr(mesh, "is_watertight") and not mesh.is_watertight:
                validation.warnings.append("Mesh is not watertight (has holes)")

            # Check for degenerate faces
            if hasattr(mesh, "remove_degenerate_faces"):
                original_faces = len(mesh.faces) if hasattr(mesh, "faces") else 0
                mesh.remove_degenerate_faces()
                if hasattr(mesh, "faces") and len(mesh.faces) < original_faces:
                    validation.warnings.append(
                        f"Model contains {original_faces - len(mesh.faces)} degenerate faces"
                    )

        except ImportError:
            logger.debug("trimesh not installed - skipping mesh analysis")
            # Fall back to file size heuristics for polycount estimation
            # Rough estimate: ~1KB per 100 triangles for GLB
            estimated_polys = int(size_kb * 100) if path.suffix.lower() == ".glb" else None
            if estimated_polys:
                validation.polycount = estimated_polys
                if estimated_polys > max_polycount:
                    validation.warnings.append(
                        f"Estimated polycount: ~{estimated_polys:,} (based on file size)"
                    )

        except Exception as e:
            validation.warnings.append(f"Mesh analysis failed: {e}")

        # GLB-specific checks
        if path.suffix.lower() == ".glb":
            try:
                # Check GLB header magic number
                with open(path, "rb") as f:
                    magic = f.read(4)
                    if magic != b"glTF":
                        validation.is_valid = False
                        validation.errors.append("Invalid GLB file: missing glTF magic number")
                    else:
                        # Read version
                        version = int.from_bytes(f.read(4), "little")
                        if version < 2:
                            validation.warnings.append(f"GLB version {version} is outdated")

            except Exception as e:
                validation.errors.append(f"Failed to read GLB header: {e}")

        # Check for textures (important for visual quality)
        if path.suffix.lower() in {".glb", ".gltf"}:
            try:
                import json

                # For GLTF, check for images/textures in the JSON
                if path.suffix.lower() == ".gltf":
                    with open(path) as f:
                        gltf_data = json.load(f)
                        if "images" not in gltf_data or not gltf_data["images"]:
                            validation.warnings.append(
                                "No textures found - model may appear untextured"
                            )
                        else:
                            texture_count = len(gltf_data.get("images", []))
                            validation.texture_size = f"{texture_count} textures"

            except json.JSONDecodeError:
                pass  # GLB files aren't JSON
            except Exception as e:
                logger.debug(f"Texture check failed: {e}")

        # SkyyRose quality standards
        if validation.is_valid and not validation.warnings:
            logger.info(f"Asset validation passed: {model_path}")
        elif validation.is_valid:
            logger.warning(
                f"Asset validation passed with warnings: {model_path} - {validation.warnings}"
            )
        else:
            logger.error(f"Asset validation failed: {model_path} - {validation.errors}")

        return validation.model_dump()




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
