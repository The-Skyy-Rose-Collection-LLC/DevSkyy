"""Media Generation API Endpoints (3D Models).

This module provides endpoints for:
- 3D model generation from text descriptions
- 3D model generation from images
- Integration with agents/tripo_agent.py via BackgroundTask + TaskStatusStore

Version: 1.1.0
"""

import base64
import logging
import os
import tempfile
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from agents.tripo_agent import TripoAssetAgent
from core.task_status_store import TaskStatusStore, get_initialized_task_status_store
from security.jwt_oauth2_auth import TokenPayload, get_current_user
from security.ssrf_protection import ssrf_protection

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/media", tags=["Media Generation"])


# =============================================================================
# Request/Response Models
# =============================================================================


class ThreeDGenerationFromTextRequest(BaseModel):
    """Request model for text-to-3D generation."""

    product_name: str = Field(
        ...,
        description="Name of the product to generate 3D model for",
        min_length=1,
        max_length=200,
    )
    collection: str = Field(
        default="SIGNATURE",
        description="SkyyRose collection: SIGNATURE, BLACK_ROSE, or LOVE_HURTS",
        max_length=100,
    )
    garment_type: str = Field(
        default="tee",
        description="Garment type: hoodie, bomber, tee, jacket, shorts, etc.",
        max_length=50,
    )
    additional_details: str = Field(
        default="",
        description="Additional design details (colors, materials, special features)",
        max_length=1000,
    )
    output_format: Literal["glb", "gltf", "fbx", "obj", "usdz", "stl"] = Field(
        default="glb",
        description="Output 3D model format. GLB recommended for web.",
    )


class ThreeDGenerationFromImageRequest(BaseModel):
    """Request model for image-to-3D generation."""

    product_name: str = Field(
        ...,
        description="Name of the product to generate 3D model for",
        min_length=1,
        max_length=200,
    )
    image_url: str = Field(
        ...,
        description="URL or base64-encoded image for 3D generation",
        max_length=10000,
    )

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, v: str) -> str:
        if v.startswith(("http://", "https://")):
            ssrf_protection.validate_url(v)
        return v

    output_format: Literal["glb", "gltf", "fbx", "obj", "usdz", "stl"] = Field(
        default="glb",
        description="Output 3D model format. GLB recommended for web.",
    )


class ThreeDAssetMetadata(BaseModel):
    """Metadata for generated 3D asset."""

    polycount: int
    file_size_mb: float
    texture_resolution: str
    includes_materials: bool
    includes_textures: bool
    animation_ready: bool


class ThreeDGenerationResponse(BaseModel):
    """Response model for 3D generation."""

    generation_id: str
    status: str
    timestamp: str
    product_name: str
    output_format: str
    model_url: str | None = None
    preview_url: str | None = None
    download_url: str | None = None
    metadata: ThreeDAssetMetadata | None = None
    estimated_completion_time: str | None = None


# =============================================================================
# Helpers
# =============================================================================


async def _resolve_image_to_tempfile(image_url: str) -> str:
    """Download a URL or decode base64 data into a local temp file.

    Returns the temp file path. Caller is responsible for deleting it.
    Agent's _tool_generate_from_image requires a local filesystem path.
    """
    suffix = ".png"

    if image_url.startswith("data:"):
        # data URI: data:image/jpeg;base64,<data>
        header, encoded = image_url.split(",", 1)
        if "jpeg" in header or "jpg" in header:
            suffix = ".jpg"
        elif "webp" in header:
            suffix = ".webp"
        raw = base64.b64decode(encoded)
    elif image_url.startswith(("http://", "https://")):
        # follow_redirects=False (SSRF): image_url was SSRF-validated at request
        # parse time; following a redirect could bounce to an unvalidated internal
        # host. The validated origin is the only host we contact.
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=False) as hc:
            resp = await hc.get(image_url)
            resp.raise_for_status()
            ct = resp.headers.get("content-type", "")
            if "jpeg" in ct or "jpg" in ct:
                suffix = ".jpg"
            elif "webp" in ct:
                suffix = ".webp"
            raw = resp.content
    else:
        # Treat as raw base64 without data: prefix
        raw = base64.b64decode(image_url)

    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        os.write(fd, raw)
    finally:
        os.close(fd)
    return path


# =============================================================================
# Background Task
# =============================================================================


async def _run_3d_generation_background(
    generation_id: str,
    request: ThreeDGenerationFromTextRequest | ThreeDGenerationFromImageRequest,
    store: TaskStatusStore,
    _agent: TripoAssetAgent | None = None,
) -> None:
    """Run 3D generation in background; write status to TaskStatusStore.

    Uses BackgroundTask pattern so the 202 response is immediate and the
    caller polls GET /media/3d/{generation_id}/status for results.

    _agent is an injection seam for tests — in production it is None and a
    real TripoAssetAgent is constructed from env.
    """
    agent = _agent or TripoAssetAgent()
    image_temp_path: str | None = None

    try:
        if isinstance(request, ThreeDGenerationFromTextRequest):
            result = await agent._tool_generate_from_text(
                product_name=request.product_name,
                collection=request.collection,
                garment_type=request.garment_type,
                additional_details=request.additional_details,
                output_format=request.output_format,
            )
        else:
            # image_url is either an HTTP URL or base64 — bridge to local path
            image_temp_path = await _resolve_image_to_tempfile(request.image_url)
            result = await agent._tool_generate_from_image(
                image_path=image_temp_path,
                product_name=request.product_name,
                output_format=request.output_format,
            )

        # result is GenerationResult.model_dump() — a dict.
        # ThreeDAssetMetadata requires polycount/file_size_mb/… which are absent
        # from GenerationResult.metadata, so metadata is correctly None.
        model_url: str = result["model_url"]
        await store.update_status(
            generation_id,
            {
                "status": "completed",
                "completed_at": datetime.now(UTC).isoformat(),
                "model_url": model_url,
                "preview_url": result.get("thumbnail_path"),
                "download_url": model_url,
                "metadata": None,
            },
        )
        logger.info("3D generation %s completed: %s", generation_id, model_url)

    except Exception as exc:
        logger.error("3D generation %s failed: %s", generation_id, exc, exc_info=True)
        await store.update_status(
            generation_id,
            {
                "status": "failed",
                "failed_at": datetime.now(UTC).isoformat(),
                "error": str(exc),
            },
        )
    finally:
        if image_temp_path and os.path.exists(image_temp_path):
            os.unlink(image_temp_path)
        # TripoAssetAgent.close() exists but is a documented no-op — the Tripo
        # SDK self-manages connections via async context managers inside each
        # _tool_* call, so there is nothing to release here.


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/3d/generate/text",
    response_model=ThreeDGenerationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_3d_from_text(
    request: ThreeDGenerationFromTextRequest,
    background_tasks: BackgroundTasks,
    store: TaskStatusStore = Depends(get_initialized_task_status_store),
    user: TokenPayload = Depends(get_current_user),
) -> ThreeDGenerationResponse:
    """Generate 3D fashion models from text descriptions using Tripo3D AI.

    **INDUSTRY FIRST**: Automated 3D model generation for fashion e-commerce.

    Creates high-quality 3D models of SkyyRose products from detailed text
    descriptions. Perfect for:
    - Product visualization in online stores
    - Virtual try-on experiences
    - Design iteration and prototyping
    - Cross-platform catalog generation

    **Supported Output Formats:**
    - GLB (Binary glTF) - Recommended for web/AR
    - GLTF (JSON glTF) - Human-readable 3D format
    - FBX (Autodesk) - Professional 3D software
    - OBJ (Wavefront) - Universal 3D format
    - USDZ (Apple) - iOS/macOS AR ready
    - STL - 3D printing format

    **SkyyRose Collections:**
    - SIGNATURE: Timeless essentials with rose gold details
    - BLACK_ROSE: Dark elegance limited editions
    - LOVE_HURTS: Emotional expression with bold design

    Args:
        request: Generation parameters (product_name, collection, garment_type, etc.)
        background_tasks: FastAPI background task runner
        store: Task status store for async polling
        user: Authenticated user (from JWT token)

    Returns:
        ThreeDGenerationResponse with status=processing and generation_id for polling
    """
    generation_id = str(uuid4())
    now = datetime.now(UTC).isoformat()

    logger.info(
        "Queuing text-to-3D generation %s for user %s: %s (%s)",
        generation_id,
        user.sub,
        request.product_name,
        request.collection,
    )

    await store.set_status(
        generation_id,
        {
            "status": "processing",
            "started_at": now,
            "generation_id": generation_id,
            "product_name": request.product_name,
            "output_format": request.output_format,
        },
    )

    background_tasks.add_task(
        _run_3d_generation_background,
        generation_id,
        request,
        store,
    )

    return ThreeDGenerationResponse(
        generation_id=generation_id,
        status="processing",
        timestamp=now,
        product_name=request.product_name,
        output_format=request.output_format,
        estimated_completion_time="2-5 minutes",
    )


@router.post(
    "/3d/generate/image",
    response_model=ThreeDGenerationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_3d_from_image(
    request: ThreeDGenerationFromImageRequest,
    background_tasks: BackgroundTasks,
    store: TaskStatusStore = Depends(get_initialized_task_status_store),
    user: TokenPayload = Depends(get_current_user),
) -> ThreeDGenerationResponse:
    """Generate 3D models from reference images using Tripo3D AI.

    **INDUSTRY FIRST**: Image-to-3D conversion for fashion products.

    Converts 2D product images into high-quality 3D models. Perfect for:
    - Converting existing product photos to 3D
    - Design sketches to 3D prototypes
    - AR/VR product visualization
    - Cross-platform 3D catalog

    **Supported Input:**
    - Image URLs (PNG, JPG, WebP)
    - Base64-encoded images (with or without data: prefix)
    - Data URIs (data:image/png;base64,...)

    **Supported Output Formats:**
    - GLB (Binary glTF) - Recommended for web/AR
    - GLTF (JSON glTF) - Human-readable 3D format
    - FBX (Autodesk) - Professional 3D software
    - OBJ (Wavefront) - Universal 3D format
    - USDZ (Apple) - iOS/macOS AR ready
    - STL - 3D printing format

    Args:
        request: Generation parameters (product_name, image_url, output_format)
        background_tasks: FastAPI background task runner
        store: Task status store for async polling
        user: Authenticated user (from JWT token)

    Returns:
        ThreeDGenerationResponse with status=processing and generation_id for polling
    """
    generation_id = str(uuid4())
    now = datetime.now(UTC).isoformat()

    logger.info(
        "Queuing image-to-3D generation %s for user %s: %s",
        generation_id,
        user.sub,
        request.product_name,
    )

    await store.set_status(
        generation_id,
        {
            "status": "processing",
            "started_at": now,
            "generation_id": generation_id,
            "product_name": request.product_name,
            "output_format": request.output_format,
        },
    )

    background_tasks.add_task(
        _run_3d_generation_background,
        generation_id,
        request,
        store,
    )

    return ThreeDGenerationResponse(
        generation_id=generation_id,
        status="processing",
        timestamp=now,
        product_name=request.product_name,
        output_format=request.output_format,
        estimated_completion_time="3-7 minutes",
    )


@router.get(
    "/3d/{generation_id}/status",
    response_model=ThreeDGenerationResponse,
)
async def get_3d_generation_status(
    generation_id: str,
    store: TaskStatusStore = Depends(get_initialized_task_status_store),
    user: TokenPayload = Depends(get_current_user),
) -> ThreeDGenerationResponse:
    """Poll the status of a 3D generation job.

    Args:
        generation_id: ID returned by the POST /media/3d/generate/* endpoints
        store: Task status store
        user: Authenticated user (from JWT token)

    Returns:
        ThreeDGenerationResponse with current status and result URLs when complete

    Raises:
        HTTPException 404: If generation_id is not found
    """
    stored = await store.get_status(generation_id)
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generation {generation_id!r} not found",
        )

    return ThreeDGenerationResponse(
        generation_id=generation_id,
        status=stored["status"],
        timestamp=stored.get("started_at")
        or stored.get("completed_at")
        or stored.get("failed_at", ""),
        product_name=stored.get("product_name", ""),
        output_format=stored.get("output_format", "glb"),
        model_url=stored.get("model_url"),
        preview_url=stored.get("preview_url"),
        download_url=stored.get("download_url"),
        metadata=None,
        estimated_completion_time=None,
    )
