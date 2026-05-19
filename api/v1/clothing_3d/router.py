"""FastAPI router for the clothing 3D pipeline.

Endpoints:

- ``POST /generate``               synchronous run
- ``POST /generate/async``         enqueue, returns ``job_id`` + ``status_url``
- ``GET  /jobs/{job_id}``          poll an async job
- ``GET  /jobs``                   list recent jobs (capped at 100)
- ``GET  /health``                 liveness — provider/backend health
- ``GET  /ready``                  readiness — queue+store reachable
- ``GET  /info``                   active config + capabilities
- ``GET  /metrics``                Prometheus text payload

Production wiring:

- Async submissions are pushed to :class:`JobQueue` (Redis Streams when
  ``REDIS_URL`` is set, in-memory otherwise) and processed by the worker
  (``python -m pipelines.clothing_3d.worker``). The router never blocks on
  the pipeline.
- Sync ``/generate`` still runs in-process; use it from internal callers that
  need the result immediately and accept the latency.
- Both paths share :class:`IdempotencyCache` so identical inputs return the
  cached result instead of re-running.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from api.v1.clothing_3d.schemas import (
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    JobAcceptedResponse,
    JobStatusResponse,
)
from pipelines.clothing_3d.job_store import JobRecord, JobStore, build_job_store
from pipelines.clothing_3d.models import (
    PipelineRequest,
    PipelineResult,
    PipelineStatus,
)
from pipelines.clothing_3d.observability import (
    get_metrics,
    metrics_event_subscriber,
    render_metrics,
)
from pipelines.clothing_3d.pipeline import ClothingPipeline
from pipelines.clothing_3d.queue import JobQueue, build_queue
from pipelines.clothing_3d.reliability import (
    IdempotencyCache,
    QuotaExceededError,
    request_fingerprint,
)
from services.three_d.trellis.config import TrellisConfig

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Clothing 3D Pipeline"])


# =============================================================================
# Process-level singletons
# =============================================================================


_pipeline: ClothingPipeline | None = None
_queue: JobQueue | None = None
_store: JobStore | None = None
_idempotency: IdempotencyCache | None = None


def get_pipeline() -> ClothingPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = ClothingPipeline(config=TrellisConfig.from_env())
        # Wire pipeline events into Prometheus metrics for sync runs too.
        _pipeline.event_bus.subscribe(metrics_event_subscriber())
    return _pipeline


def get_queue() -> JobQueue:
    global _queue
    if _queue is None:
        _queue = build_queue()
    return _queue


def get_store() -> JobStore:
    global _store
    if _store is None:
        _store = build_job_store()
    return _store


def get_idempotency() -> IdempotencyCache:
    global _idempotency
    if _idempotency is None:
        _idempotency = IdempotencyCache()
    return _idempotency


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
    pipeline: Annotated[ClothingPipeline, Depends(get_pipeline)],
    idempotency: Annotated[IdempotencyCache, Depends(get_idempotency)],
) -> GenerateResponse:
    """Run the full clothing 3D pipeline and return the result."""

    async def _runner(req: PipelineRequest) -> PipelineResult:
        return await pipeline.run(req)

    try:
        result, hit = await idempotency.get_or_run(body, runner=_runner)
    except QuotaExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"backend cost cap exceeded: {exc}",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("clothing-3d generate failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Pipeline error: {exc}",
        ) from exc

    metrics = get_metrics()
    metrics.cache_total.labels(outcome="hit" if hit else "miss").inc()

    if result.status == PipelineStatus.FAILED:
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
    queue: Annotated[JobQueue, Depends(get_queue)],
    store: Annotated[JobStore, Depends(get_store)],
) -> JobAcceptedResponse:
    """Enqueue a job; the worker picks it up.

    With ``REDIS_URL`` set, the job survives restarts and any worker in the
    pool can pick it up. Without Redis, the job runs against the in-process
    queue and is lost on restart.
    """
    job_id = f"job_{uuid.uuid4().hex[:16]}"
    body.correlation_id = body.correlation_id or job_id

    record = JobRecord(
        job_id=job_id,
        status=PipelineStatus.PENDING,
        request=body,
        idempotency_key=request_fingerprint(body),
    )
    await store.put(record)
    try:
        await queue.enqueue(job_id)
    except Exception as exc:  # noqa: BLE001 — failed enqueue = failed job
        record.status = PipelineStatus.FAILED
        record.error = f"enqueue failed: {exc}"
        record.finished_at = datetime.now(UTC)
        await store.update(record)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Queue unavailable: {exc}",
        ) from exc

    base_url = str(request.url).rstrip("/")
    base = base_url.rsplit("/generate/async", 1)[0]
    return JobAcceptedResponse(
        job_id=job_id,
        correlation_id=body.correlation_id,
        status_url=f"{base}/jobs/{job_id}",
    )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Fetch the status of an async clothing 3D job",
)
async def get_job_endpoint(
    job_id: str,
    store: Annotated[JobStore, Depends(get_store)],
) -> JobStatusResponse:
    job = await store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"job not found: {job_id}")
    return JobStatusResponse(
        ok=job.status in {PipelineStatus.SUCCEEDED, PipelineStatus.PENDING, PipelineStatus.RUNNING},
        job_id=job.job_id,
        status=job.status.value,
        result=job.result,
        error=job.error,
        submitted_at=job.submitted_at.isoformat(),
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
    )


@router.get(
    "/jobs",
    summary="List recent clothing 3D jobs",
)
async def list_jobs_endpoint(
    store: Annotated[JobStore, Depends(get_store)],
    limit: int = 50,
) -> dict[str, Any]:
    jobs = await store.list(limit=min(max(limit, 1), 100))
    return {
        "ok": True,
        "count": len(jobs),
        "jobs": [
            {
                "job_id": j.job_id,
                "status": j.status.value,
                "submitted_at": j.submitted_at.isoformat(),
                "finished_at": j.finished_at.isoformat() if j.finished_at else None,
                "worker_id": j.worker_id,
                "error": j.error,
            }
            for j in jobs
        ],
    }


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness — TRELLIS provider health",
)
async def health_endpoint(
    pipeline: Annotated[ClothingPipeline, Depends(get_pipeline)],
) -> HealthResponse:
    health = await pipeline.provider.health_check()
    # Report the live backend (which respects test-injection), with the
    # configured backend as a secondary signal.
    live_backend = getattr(
        pipeline.provider._backend,  # type: ignore[attr-defined]
        "backend_name",
        pipeline.provider.config.backend.value,
    )
    return HealthResponse(
        ok=health.is_available,
        provider=health.provider,
        status=health.status.value,
        capabilities=[c.value for c in health.capabilities],
        backend=live_backend,
        latency_ms=health.latency_ms,
        error=health.error_message,
        detail={
            "configured_backend": pipeline.provider.config.backend.value,
            "quality_preset": pipeline.provider.config.quality.value,
            "output_dir": pipeline.provider.config.output_dir,
        },
    )


@router.get("/ready", summary="Readiness — queue + store reachable")
async def ready_endpoint(
    queue: Annotated[JobQueue, Depends(get_queue)],
    store: Annotated[JobStore, Depends(get_store)],
) -> dict[str, Any]:
    """Reports OK only when the worker dependencies are reachable."""
    detail: dict[str, Any] = {}
    ok = True

    try:
        detail["queue_depth"] = await queue.depth()
        detail["queue"] = type(queue).__name__
    except Exception as exc:  # noqa: BLE001
        ok = False
        detail["queue_error"] = str(exc)

    try:
        await store.list(limit=1)
        detail["store"] = type(store).__name__
    except Exception as exc:  # noqa: BLE001
        ok = False
        detail["store_error"] = str(exc)

    if not ok:
        return Response(
            content=str({"ok": False, **detail}),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/json",
        )
    return {"ok": True, **detail}


@router.get("/info", summary="Pipeline configuration & capabilities")
async def info_endpoint(
    pipeline: Annotated[ClothingPipeline, Depends(get_pipeline)],
    queue: Annotated[JobQueue, Depends(get_queue)],
) -> dict[str, Any]:
    config = pipeline.provider.config
    return {
        "ok": True,
        "version": "1.1.0",
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
        "queue": {
            "type": type(queue).__name__,
            "depth": await queue.depth(),
        },
    }


@router.get(
    "/metrics",
    summary="Prometheus metrics scrape endpoint",
    include_in_schema=False,
)
async def metrics_endpoint() -> Response:
    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)


__all__ = ["router", "get_pipeline", "get_queue", "get_store", "get_idempotency"]
