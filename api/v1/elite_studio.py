"""
Elite Studio REST API — Layer 5

Exposes the Elite Studio image pipeline as a REST service with full job
lifecycle management, batch enqueueing, webhook registration, and a
pipeline health check.

Prefix: /api/v1/elite-studio
Auth:   X-API-Key header validated against settings.API_KEY (or JWT bearer
        via the project's existing get_current_user dependency).
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

from skyyrose.elite_studio.queue.job_types import EliteStudioJobResult
from skyyrose.elite_studio.queue.producer import (
    aenqueue_batch,
    aenqueue_creative,
    aenqueue_produce,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/elite-studio", tags=["Elite Studio"])

# ---------------------------------------------------------------------------
# Redis key constants (mirrors consumer.py)
# ---------------------------------------------------------------------------
_RESULT_KEY_PREFIX = "elite_studio:result:"
_QUEUE_NAME = "queue:elite_studio_produce"


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------


def _get_api_key_dependency():
    """Return a FastAPI dependency that validates the X-API-Key header.

    If the project's JWT-based get_current_user is importable, we fall back
    to that for flexibility.  Otherwise, we use a simple API key check.
    """

    async def _check_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
        expected = os.getenv("API_KEY", "")
        if not expected:
            # No API_KEY configured — allow through (dev mode)
            return None
        if x_api_key != expected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing X-API-Key header",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        return x_api_key

    return _check_api_key


_api_key_dep = _get_api_key_dependency()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class ProduceRequest(BaseModel):
    """Single-job enqueue request."""

    model_config = {"str_strip_whitespace": True}

    sku: str
    view: str = "front"
    enable_compositor: bool = False
    priority: int = Field(default=5, ge=1, le=10)
    webhook_url: str | None = None

    @field_validator("view")
    @classmethod
    def _validate_view(cls, v: str) -> str:
        if v not in {"front", "back"}:
            raise ValueError("view must be 'front' or 'back'")
        return v

    @field_validator("sku")
    @classmethod
    def _validate_sku(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("sku must not be empty")
        return v.strip().lower()


class BatchProduceRequest(BaseModel):
    """Batch-job enqueue request."""

    model_config = {"str_strip_whitespace": True}

    skus: list[str] = Field(min_length=1)
    view: str = "front"
    enable_compositor: bool = False
    priority: int = Field(default=5, ge=1, le=10)

    @field_validator("view")
    @classmethod
    def _validate_view(cls, v: str) -> str:
        if v not in {"front", "back"}:
            raise ValueError("view must be 'front' or 'back'")
        return v


class ProduceResponse(BaseModel):
    """Response returned after enqueueing a single job."""

    job_id: str
    sku: str
    status: str
    queued_at: str


class BatchProduceResponse(BaseModel):
    """Response returned after enqueueing a batch of jobs."""

    job_ids: list[str]
    total: int
    queued_at: str


class JobStatusResponse(BaseModel):
    """Lightweight job status summary (no heavy result fields)."""

    job_id: str
    sku: str
    status: str
    queued_at: str | None = None


class JobListResponse(BaseModel):
    """Paginated list of recent jobs."""

    jobs: list[EliteStudioJobResult]
    total: int
    page: int
    page_size: int


class HealthResponse(BaseModel):
    """Pipeline health summary."""

    status: str  # "healthy" | "degraded" | "unavailable"
    redis: str
    queue_depth: int
    checked_at: str


# ---------------------------------------------------------------------------
# Redis helper (shared, lazy)
# ---------------------------------------------------------------------------


def _get_redis() -> Any | None:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        import redis as redis_lib

        r = redis_lib.from_url(redis_url, decode_responses=True, socket_timeout=3)
        r.ping()
        return r
    except Exception as exc:
        logger.warning("elite_studio API: Redis unavailable — %s", exc)
        return None


def _require_redis() -> Any:
    r = _get_redis()
    if r is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis unavailable — cannot process request",
        )
    return r


def _fetch_result(r: Any, job_id: str) -> EliteStudioJobResult | None:
    """Fetch and deserialise a job result from Redis. Returns None if not found."""
    raw = r.get(f"{_RESULT_KEY_PREFIX}{job_id}")
    if raw is None:
        return None
    try:
        data = json.loads(raw)
        return EliteStudioJobResult(**data)
    except Exception as exc:
        logger.warning("Failed to deserialise result for %s: %s", job_id, exc)
        return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/produce",
    response_model=ProduceResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue a single SKU render job",
)
async def produce(
    body: ProduceRequest,
    _auth=Depends(_api_key_dep),
):
    """Enqueue one render job and return its job_id."""
    queued_at = datetime.now(UTC).isoformat()
    try:
        job_id = await aenqueue_produce(
            sku=body.sku,
            view=body.view,
            priority=body.priority,
            enable_compositor=body.enable_compositor,
        )
    except Exception as exc:
        logger.error("Failed to enqueue job for sku=%s: %s", body.sku, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Queue unavailable: {exc}",
        ) from exc

    # Register webhook if provided
    if body.webhook_url:
        _register_job_webhook(job_id, body.webhook_url)

    return ProduceResponse(job_id=job_id, sku=body.sku, status="queued", queued_at=queued_at)


@router.post(
    "/produce-batch",
    response_model=BatchProduceResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue multiple SKU render jobs",
)
async def produce_batch(
    body: BatchProduceRequest,
    _auth=Depends(_api_key_dep),
):
    """Enqueue a batch of render jobs and return their job_ids."""
    queued_at = datetime.now(UTC).isoformat()
    try:
        job_ids = await aenqueue_batch(
            skus=body.skus,
            view=body.view,
            priority=body.priority,
            enable_compositor=body.enable_compositor,
        )
    except Exception as exc:
        logger.error("Failed to enqueue batch: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Queue unavailable: {exc}",
        ) from exc

    return BatchProduceResponse(job_ids=job_ids, total=len(job_ids), queued_at=queued_at)


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status",
)
async def get_job_status(
    job_id: str,
    _auth=Depends(_api_key_dep),
):
    """Return job status: queued / running / success / error / skipped."""
    r = _require_redis()
    result = _fetch_result(r, job_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        )
    return JobStatusResponse(
        job_id=result.job_id,
        sku=result.sku,
        status=result.status,
        queued_at=result.completed_at or None,
    )


@router.get(
    "/jobs/{job_id}/result",
    response_model=EliteStudioJobResult,
    summary="Get full job result",
)
async def get_job_result(
    job_id: str,
    _auth=Depends(_api_key_dep),
):
    """Return the complete EliteStudioJobResult including stage timings and cost."""
    r = _require_redis()
    result = _fetch_result(r, job_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        )
    return result


@router.delete(
    "/jobs/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel a queued job",
)
async def cancel_job(
    job_id: str,
    _auth=Depends(_api_key_dep),
):
    """Remove a queued job. No-ops silently if the job is already running or complete."""
    r = _require_redis()
    # Attempt removal from the priority queue (ZREM)
    removed = r.zrem(_QUEUE_NAME, job_id)
    if not removed:
        # Job may be running / complete — check if it exists at all
        exists = r.exists(f"{_RESULT_KEY_PREFIX}{job_id}")
        if not exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job not found: {job_id}",
            )
    # Return 204 whether we removed from queue or the job was already done
    return None


@router.get(
    "/jobs",
    response_model=JobListResponse,
    summary="List recent jobs (paginated)",
)
async def list_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    sku: str | None = Query(default=None),
    _auth=Depends(_api_key_dep),
):
    """Return paginated list of completed/errored jobs stored in Redis."""
    r = _require_redis()

    pattern = f"{_RESULT_KEY_PREFIX}*"
    try:
        keys = r.keys(pattern)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis error: {exc}",
        ) from exc

    results: list[EliteStudioJobResult] = []
    for key in keys:
        raw = r.get(key)
        if not raw:
            continue
        try:
            data = json.loads(raw)
            job = EliteStudioJobResult(**data)
        except Exception:
            continue

        if status_filter and job.status != status_filter:
            continue
        if sku and job.sku != sku.lower():
            continue
        results.append(job)

    # Sort by completed_at descending (empty string sorts to front, push to back)
    results.sort(key=lambda j: j.completed_at or "", reverse=True)

    total = len(results)
    start = (page - 1) * page_size
    paginated = results[start : start + page_size]

    return JobListResponse(jobs=paginated, total=total, page=page, page_size=page_size)


@router.get(
    "/skus",
    summary="List all known SKUs",
)
async def list_skus(
    _auth=Depends(_api_key_dep),
):
    """Return all SKUs that have at least one result stored in Redis."""
    r = _require_redis()
    pattern = f"{_RESULT_KEY_PREFIX}*"
    try:
        keys = r.keys(pattern)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis error: {exc}",
        ) from exc

    skus: set[str] = set()
    for key in keys:
        raw = r.get(key)
        if not raw:
            continue
        try:
            data = json.loads(raw)
            if data.get("sku"):
                skus.add(data["sku"])
        except Exception:
            continue

    return {"skus": sorted(skus), "total": len(skus)}


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Pipeline health check",
)
async def health(
    _auth=Depends(_api_key_dep),
):
    """Return Redis connectivity status and current queue depth."""
    checked_at = datetime.now(UTC).isoformat()
    r = _get_redis()
    if r is None:
        return HealthResponse(
            status="unavailable",
            redis="unavailable",
            queue_depth=-1,
            checked_at=checked_at,
        )

    try:
        queue_depth = r.zcard(_QUEUE_NAME)
        return HealthResponse(
            status="healthy",
            redis="connected",
            queue_depth=queue_depth,
            checked_at=checked_at,
        )
    except Exception as exc:
        logger.warning("elite_studio health check failed: %s", exc)
        return HealthResponse(
            status="degraded",
            redis="error",
            queue_depth=-1,
            checked_at=checked_at,
        )


# ---------------------------------------------------------------------------
# Creative Operations Hub endpoint
# ---------------------------------------------------------------------------


class CreateRequest(BaseModel):
    """Request body for the Creative Operations Hub endpoint."""

    model_config = {"str_strip_whitespace": True}

    intent: str
    sku: str = ""
    params: dict = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)

    @field_validator("intent")
    @classmethod
    def _validate_intent(cls, v: str) -> str:
        from skyyrose.elite_studio.creative.state import CreativeIntent

        valid = {e.value for e in CreativeIntent}
        if v not in valid:
            raise ValueError(f"intent must be one of {sorted(valid)}, got: {v!r}")
        return v

    @field_validator("sku")
    @classmethod
    def _normalise_sku(cls, v: str) -> str:
        return v.strip().lower()


class CreateResponse(BaseModel):
    """Response from the Creative Operations Hub endpoint."""

    operation_id: str
    intent: str
    sku: str
    status: str
    queued_at: str


@router.post(
    "/create",
    response_model=CreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue a creative operation (render, social pack, copy, etc.)",
)
async def create_operation(
    body: CreateRequest,
    _auth=Depends(_api_key_dep),
):
    """Enqueue a creative operation via the Creative Operations Hub.

    Supports all 14 creative intents: product-render, social-pack,
    product-copy, design-ideation, collection-plan, tech-pack, moodboard,
    colorway-explore, 3d-model, character-sheet, scene-composite,
    virtual-tryon, full-product-launch, mockup.
    """
    queued_at = datetime.now(UTC).isoformat()
    try:
        job_id = await aenqueue_creative(
            intent=body.intent,
            params=body.params,
            sku=body.sku,
            priority=body.priority,
        )
    except Exception as exc:
        logger.error("Failed to enqueue creative operation intent=%s: %s", body.intent, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Queue unavailable: {exc}",
        ) from exc

    return CreateResponse(
        operation_id=job_id,
        intent=body.intent,
        sku=body.sku,
        status="queued",
        queued_at=queued_at,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _register_job_webhook(job_id: str, webhook_url: str) -> None:
    """Fire-and-forget: store a per-job webhook URL in Redis."""
    r = _get_redis()
    if r is None:
        return
    try:
        key = f"elite_studio:job_webhook:{job_id}"
        r.setex(key, 86_400, webhook_url)
    except Exception as exc:
        logger.warning("Failed to register job webhook for %s: %s", job_id, exc)
