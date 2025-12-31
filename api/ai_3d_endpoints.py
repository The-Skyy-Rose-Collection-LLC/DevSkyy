"""
AI 3D API Endpoints
===================

REST API endpoints for AI-powered 3D model generation.

Endpoints:
- POST /api/v1/ai-3d/generate-model - Generate 3D model from images
- POST /api/v1/ai-3d/regenerate-model - Regenerate with feedback
- GET /api/v1/ai-3d/models/{sku} - Get model info
- GET /api/v1/ai-3d/status - Get pipeline status

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import shutil
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

ai_3d_router = APIRouter(prefix="/ai-3d", tags=["AI 3D Generation"])


# =============================================================================
# Request/Response Models
# =============================================================================


class GenerateModelRequest(BaseModel):
    """Request to generate 3D model."""

    product_sku: str = Field(..., min_length=1, max_length=100)
    quality_level: str = Field(default="high", pattern="^(draft|standard|high)$")
    validate_fidelity: bool = Field(default=True)


class GenerateModelResponse(BaseModel):
    """Response from model generation."""

    job_id: str
    product_sku: str
    status: str
    created_at: str
    model_url: str | None = None
    thumbnail_url: str | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    validation: dict[str, Any] = Field(default_factory=dict)


class RegenerateRequest(BaseModel):
    """Request to regenerate model with feedback."""

    product_sku: str = Field(..., min_length=1, max_length=100)
    feedback: dict[str, Any] = Field(default_factory=dict)


class ModelInfoResponse(BaseModel):
    """Response with model information."""

    product_sku: str
    model_path: str | None = None
    model_url: str | None = None
    thumbnail_url: str | None = None
    exists: bool = False
    fidelity_score: float | None = None
    vertex_count: int | None = None
    face_count: int | None = None
    file_size_mb: float | None = None
    created_at: str | None = None


class PipelineStatusResponse(BaseModel):
    """Response with pipeline status."""

    status: str
    active_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    available_models: list[str] = Field(default_factory=list)
    last_generation: str | None = None


# =============================================================================
# In-Memory Job Store
# =============================================================================


class JobStore:
    """In-memory job storage for generation jobs."""

    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}

    def create(self, product_sku: str) -> str:
        """Create a new job."""
        job_id = f"ai3d_{uuid.uuid4().hex[:12]}"
        self._jobs[job_id] = {
            "job_id": job_id,
            "product_sku": product_sku,
            "status": "queued",
            "created_at": datetime.now(UTC).isoformat(),
            "completed_at": None,
            "result": None,
            "error": None,
        }
        return job_id

    def get(self, job_id: str) -> dict[str, Any] | None:
        """Get job by ID."""
        return self._jobs.get(job_id)

    def update(self, job_id: str, **kwargs: Any) -> None:
        """Update job fields."""
        if job_id in self._jobs:
            self._jobs[job_id].update(kwargs)

    def complete(self, job_id: str, result: dict[str, Any]) -> None:
        """Mark job as completed."""
        if job_id in self._jobs:
            self._jobs[job_id].update(
                {
                    "status": "completed",
                    "completed_at": datetime.now(UTC).isoformat(),
                    "result": result,
                }
            )

    def fail(self, job_id: str, error: str) -> None:
        """Mark job as failed."""
        if job_id in self._jobs:
            self._jobs[job_id].update(
                {
                    "status": "failed",
                    "completed_at": datetime.now(UTC).isoformat(),
                    "error": error,
                }
            )

    def list_jobs(self, limit: int = 20) -> list[dict[str, Any]]:
        """List recent jobs."""
        jobs = list(self._jobs.values())
        jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return jobs[:limit]

    @property
    def stats(self) -> dict[str, int]:
        """Get job statistics."""
        active = sum(1 for j in self._jobs.values() if j["status"] in ("queued", "processing"))
        completed = sum(1 for j in self._jobs.values() if j["status"] == "completed")
        failed = sum(1 for j in self._jobs.values() if j["status"] == "failed")
        return {"active": active, "completed": completed, "failed": failed}


job_store = JobStore()


# =============================================================================
# Background Tasks
# =============================================================================


async def run_model_generation(
    job_id: str,
    product_sku: str,
    source_paths: list[Path],
    quality_level: str,
    validate_fidelity: bool,
) -> None:
    """Run model generation in background."""
    try:
        job_store.update(job_id, status="processing")

        from ai_3d.model_generator import AI3DModelGenerator

        generator = AI3DModelGenerator(
            output_dir=Path("./generated_models"),
            reference_images_dir=Path("./product_images"),
        )

        try:
            result = await generator.generate_model(
                product_sku=product_sku,
                source_images=source_paths,
                quality_level=quality_level,
                validate_fidelity=validate_fidelity,
            )

            job_store.complete(
                job_id,
                {
                    "model_path": str(result.model_path),
                    "thumbnail_path": str(result.thumbnail_path),
                    "fidelity_score": result.fidelity_score,
                    "vertex_count": result.vertex_count,
                    "face_count": result.face_count,
                    "file_size_mb": result.file_size_mb,
                    "passed_fidelity": result.passed_fidelity,
                },
            )

            logger.info(
                "Model generation completed",
                job_id=job_id,
                product_sku=product_sku,
                fidelity_score=result.fidelity_score,
            )

        finally:
            await generator.close()

    except Exception as e:
        logger.exception("Model generation failed", job_id=job_id, error=str(e))
        job_store.fail(job_id, str(e))


# =============================================================================
# Endpoints
# =============================================================================


@ai_3d_router.get("/status", response_model=PipelineStatusResponse)
async def get_pipeline_status() -> PipelineStatusResponse:
    """Get AI 3D pipeline status."""
    stats = job_store.stats

    # Find last completed job
    jobs = job_store.list_jobs(1)
    last_gen = None
    for job in jobs:
        if job["status"] == "completed" and job.get("completed_at"):
            last_gen = job["completed_at"]
            break

    return PipelineStatusResponse(
        status="operational",
        active_jobs=stats["active"],
        completed_jobs=stats["completed"],
        failed_jobs=stats["failed"],
        available_models=["triposr", "hunyuan3d", "instantmesh", "trellis"],
        last_generation=last_gen,
    )


@ai_3d_router.get("/jobs", response_model=list[dict])
async def list_jobs(limit: int = 20) -> list[dict[str, Any]]:
    """List recent generation jobs."""
    return job_store.list_jobs(limit)


@ai_3d_router.get("/jobs/{job_id}", response_model=dict)
async def get_job(job_id: str) -> dict[str, Any]:
    """Get job status by ID."""
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@ai_3d_router.post("/generate-model", response_model=GenerateModelResponse)
async def generate_model(
    files: list[UploadFile] = File(...),
    product_sku: str = "",
    quality_level: str = "high",
    validate_fidelity: bool = True,
    background_tasks: BackgroundTasks | None = None,
) -> GenerateModelResponse:
    """
    Generate a 3D model from product images.

    Requires minimum 4 images, optimal 8+ from different angles.
    Model must achieve 95% fidelity to pass validation.
    """
    if len(files) < 4:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum 4 source images required, got {len(files)}",
        )

    if quality_level not in ("draft", "standard", "high"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid quality_level: {quality_level}",
        )

    if not product_sku:
        product_sku = f"product_{uuid.uuid4().hex[:8]}"

    # Save uploaded files
    temp_dir = Path(tempfile.mkdtemp())
    source_paths = []

    try:
        for i, file in enumerate(files):
            suffix = Path(file.filename or "image.png").suffix or ".png"
            tmp_path = temp_dir / f"source_{i}{suffix}"
            content = await file.read()
            tmp_path.write_bytes(content)
            source_paths.append(tmp_path)

        # Create job
        job_id = job_store.create(product_sku)

        # Schedule background task
        if background_tasks:
            background_tasks.add_task(
                run_model_generation,
                job_id,
                product_sku,
                source_paths,
                quality_level,
                validate_fidelity,
            )
        else:
            # Run synchronously for testing
            await run_model_generation(
                job_id,
                product_sku,
                source_paths,
                quality_level,
                validate_fidelity,
            )

        return GenerateModelResponse(
            job_id=job_id,
            product_sku=product_sku,
            status="queued",
            created_at=datetime.now(UTC).isoformat(),
        )

    except Exception as e:
        # Cleanup on error
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@ai_3d_router.post("/regenerate-model", response_model=GenerateModelResponse)
async def regenerate_model(
    request: RegenerateRequest,
    background_tasks: BackgroundTasks | None = None,
) -> GenerateModelResponse:
    """Regenerate model with feedback from failed validation."""
    product_sku = request.product_sku

    # Check if model exists
    model_path = Path(f"./generated_models/models/{product_sku}.glb")
    if not model_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No existing model found for {product_sku}",
        )

    # Find source images
    source_dir = Path(f"./product_images/{product_sku}")
    if not source_dir.exists():
        source_dir = Path("./product_images")

    source_images = list(source_dir.glob("*.png")) + list(source_dir.glob("*.jpg"))

    if not source_images:
        raise HTTPException(
            status_code=400,
            detail=f"No source images found for {product_sku}",
        )

    # Create job
    job_id = job_store.create(product_sku)

    # Schedule regeneration
    if background_tasks:
        background_tasks.add_task(
            run_model_generation,
            job_id,
            product_sku,
            source_images,
            "high",  # Always use high quality for regeneration
            True,  # Always validate
        )

    return GenerateModelResponse(
        job_id=job_id,
        product_sku=product_sku,
        status="queued",
        created_at=datetime.now(UTC).isoformat(),
    )


@ai_3d_router.get("/models/{product_sku}", response_model=ModelInfoResponse)
async def get_model_info(product_sku: str) -> ModelInfoResponse:
    """Get information about a generated model."""
    model_path = Path(f"./generated_models/models/{product_sku}.glb")
    thumbnail_path = Path(f"./generated_models/thumbnails/{product_sku}_thumb.png")

    if not model_path.exists():
        return ModelInfoResponse(
            product_sku=product_sku,
            exists=False,
        )

    # Get file stats
    file_size_mb = model_path.stat().st_size / (1024 * 1024)
    created_at = datetime.fromtimestamp(model_path.stat().st_ctime, tz=UTC).isoformat()

    return ModelInfoResponse(
        product_sku=product_sku,
        model_path=str(model_path),
        model_url=f"/assets/models/{product_sku}.glb",
        thumbnail_url=(
            f"/assets/thumbnails/{product_sku}_thumb.png" if thumbnail_path.exists() else None
        ),
        exists=True,
        file_size_mb=round(file_size_mb, 3),
        created_at=created_at,
    )


__all__ = ["ai_3d_router"]
