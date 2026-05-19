"""FastAPI router for the clothing 3D pipeline.

Endpoints:

- ``POST /generate`` — synchronous run. Returns the full :class:`PipelineResult`.
- ``POST /generate/async`` — fire-and-forget; returns a job ID for polling.
- ``GET  /jobs/{job_id}`` — fetch a previously submitted async job.
- ``GET  /health`` — provider/backend health.

The async path uses an in-process job store; for multi-worker deployments,
swap in the existing :mod:`services.ml.processing_queue` or Celery worker.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from api.v1.clothing_3d.schemas import (
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    JobAcceptedResponse,
    JobStatusResponse,
)
from pipelines.clothing_3d.models import PipelineResult, PipelineStatus
from pipelines.clothing_3d.pipeline import ClothingPipeline
from services.three_d.trellis.config import TrellisConfig

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Clothing 3D Pipeline"])


# =============================================================================
# Singletons (one pipeline per process)
# =============================================================================


_pipeline: ClothingPipeline | None = None


def get_pipeline() -> ClothingPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = ClothingPipeline(config=TrellisConfig.from_env())
    return _pipeline


# =============================================================================
# In-process job store
# =============================================================================


@dataclass(slots=True)
class _Job:
    job_id: str
    status: str = "queued"
    result: PipelineResult | None = None
    error: str | None = None
    submitted_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None


_jobs: dict[str, _Job] = {}
_jobs_lock = asyncio.Lock()

# Cap at 256 entries to avoid unbounded growth — older jobs evicted FIFO.
_JOB_LIMIT = 256


async def _put_job(job: _Job) -> None:
    async with _jobs_lock:
        if len(_jobs) >= _JOB_LIMIT:
            oldest = min(_jobs, key=lambda k: _jobs[k].submitted_at)
            _jobs.pop(oldest, None)
        _jobs[job.job_id] = job


async def _get_job(job_id: str) -> _Job | None:
    async with _jobs_lock:
        return _jobs.get(job_id)


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/generate",
    response_model=GenerateResponse,
    summary="Generate a 3D garment model (synchronous)",
)
async def generate_endpoint(
    body: GenerateRequest,
    pipeline: ClothingPipeline = Depends(get_pipeline),
) -> GenerateResponse:
    """Run the full clothing 3D pipeline and return the result.

    Use this for one-off calls. For batch workloads or long-running runs
    (PRODUCTION quality preset, 60+ second backend latency), prefer
    :func:`generate_async_endpoint`.
    """
    try:
        result = await pipeline.run(body)
    except Exception as exc:  # noqa: BLE001 — convert to HTTP error
        logger.exception("clothing-3d generate failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Pipeline error: {exc}",
        ) from exc

    if result.status == PipelineStatus.FAILED:
        # Body still returned so the caller sees per-stage detail.
        return GenerateResponse(ok=False, result=result)
    return GenerateResponse(ok=result.succeeded, result=result)


@router.post(
    "/generate/async",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a clothing 3D job for background processing",
)
async def generate_async_endpoint(
    body: GenerateRequest,
    request: Request,
    background: BackgroundTasks,
    pipeline: ClothingPipeline = Depends(get_pipeline),
) -> JobAcceptedResponse:
    """Submit a job and immediately return a polling URL."""
    job_id = f"job_{uuid.uuid4().hex[:16]}"
    body.correlation_id = body.correlation_id or job_id

    job = _Job(job_id=job_id, status="queued")
    await _put_job(job)

    background.add_task(_run_async_job, job_id, body, pipeline)

    base_url = str(request.url).rstrip("/")
    # /generate/async → /jobs/{job_id}
    base = base_url.rsplit("/generate/async", 1)[0]
    return JobAcceptedResponse(
        job_id=job_id,
        correlation_id=body.correlation_id,
        status_url=f"{base}/jobs/{job_id}",
    )


async def _run_async_job(
    job_id: str,
    body: GenerateRequest,
    pipeline: ClothingPipeline,
) -> None:
    job = await _get_job(job_id)
    if job is None:
        logger.warning("async job vanished before execution: %s", job_id)
        return

    job.status = "running"
    await _put_job(job)

    try:
        result = await pipeline.run(body)
        job.result = result
        job.status = result.status.value
    except Exception as exc:  # noqa: BLE001 — captured on the job
        logger.exception("async clothing-3d job failed: %s", job_id)
        job.status = PipelineStatus.FAILED.value
        job.error = str(exc)
    finally:
        job.finished_at = datetime.now(UTC)
        await _put_job(job)


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Fetch the status of an async clothing 3D job",
)
async def get_job_endpoint(job_id: str) -> JobStatusResponse:
    job = await _get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"job not found: {job_id}")
    return JobStatusResponse(
        ok=job.status in {PipelineStatus.SUCCEEDED.value, "queued", "running"},
        job_id=job.job_id,
        status=job.status,
        result=job.result,
        error=job.error,
        submitted_at=job.submitted_at.isoformat() if job.submitted_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="TRELLIS provider health check",
)
async def health_endpoint(
    pipeline: ClothingPipeline = Depends(get_pipeline),
) -> HealthResponse:
    health = await pipeline.provider.health_check()
    return HealthResponse(
        ok=health.is_available,
        provider=health.provider,
        status=health.status.value,
        capabilities=[c.value for c in health.capabilities],
        backend=pipeline.provider.config.backend.value,
        latency_ms=health.latency_ms,
        error=health.error_message,
        detail={
            "quality_preset": pipeline.provider.config.quality.value,
            "output_dir": pipeline.provider.config.output_dir,
        },
    )


@router.get("/info", summary="Pipeline configuration & capabilities")
async def info_endpoint(
    pipeline: ClothingPipeline = Depends(get_pipeline),
) -> dict[str, Any]:
    config = pipeline.provider.config
    return {
        "ok": True,
        "version": "1.0.0",
        "backend": config.backend.value,
        "quality": config.quality.value,
        "capabilities": [c.value for c in pipeline.provider.capabilities],
        "sampling": {
            "ss_steps": config.sampling.ss_sampling_steps,
            "slat_steps": config.sampling.slat_sampling_steps,
            "mesh_simplify": config.sampling.mesh_simplify,
            "texture_size": config.sampling.texture_size,
        },
        "outputs": {
            "glb": True,
            "usdz": config.export_usdz_for_ios,
            "thumbnail": True,
        },
    }


__all__ = ["router", "get_pipeline"]
