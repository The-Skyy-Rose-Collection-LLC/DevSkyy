"""
Enterprise API v2 — Creative Operations

Unified endpoint surface for all 14 creative intents.
Supports both async (enqueue) and sync (direct run) modes.

Prefix: /api/v2/creative
Auth:   X-API-Key header (matches v1 pattern)
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/creative", tags=["Creative v2"])

# Module-level imports for mockability in tests
try:
    from skyyrose.elite_studio.creative.runner import run_creative
    from skyyrose.elite_studio.queue.producer import enqueue_creative
except ImportError:  # pragma: no cover
    run_creative = None  # type: ignore[assignment]
    enqueue_creative = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Redis key constants
# ---------------------------------------------------------------------------

_RESULT_KEY_PREFIX = "elite_studio:result:"
_OP_KEY_PREFIX = "elite_studio:v2:operation:"
_QUEUE_NAME = "queue:elite_studio_produce"


# ---------------------------------------------------------------------------
# Auth dependency (mirrors v1)
# ---------------------------------------------------------------------------


def _get_api_key_dependency():
    async def _check_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
        expected = os.getenv("API_KEY", "")
        if not expected:
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
# Pydantic V2 models
# ---------------------------------------------------------------------------


class CreateOperationRequest(BaseModel):
    model_config = {"str_strip_whitespace": True}

    intent: str
    sku: str = ""
    params: dict = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)
    async_mode: bool = True
    webhook_url: str | None = None

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


class OperationResponse(BaseModel):
    operation_id: str
    intent: str
    status: str  # "queued" | "running" | "completed" | "failed"
    sku: str = ""
    created_at: str
    result: dict | None = None
    error: str = ""
    cost_usd: float = 0.0
    stage_timings: dict[str, float] = Field(default_factory=dict)


class OperationListResponse(BaseModel):
    operations: list[OperationResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Redis helpers
# ---------------------------------------------------------------------------


def _get_redis() -> Any | None:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        import redis as redis_lib

        r = redis_lib.from_url(redis_url, decode_responses=True, socket_timeout=3)
        r.ping()
        return r
    except Exception as exc:
        logger.warning("creative v2: Redis unavailable — %s", exc)
        return None


def _require_redis() -> Any:
    r = _get_redis()
    if r is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis unavailable — cannot process request",
        )
    return r


def _store_operation(r: Any, op: OperationResponse, ttl: int = 86_400 * 7) -> None:
    """Persist an OperationResponse to Redis with a 7-day TTL."""
    key = f"{_OP_KEY_PREFIX}{op.operation_id}"
    try:
        r.setex(key, ttl, op.model_dump_json())
    except Exception as exc:
        logger.warning("Failed to store operation %s: %s", op.operation_id, exc)


def _fetch_operation(r: Any, operation_id: str) -> OperationResponse | None:
    """Fetch an OperationResponse from Redis. Falls back to legacy result keys."""
    key = f"{_OP_KEY_PREFIX}{operation_id}"
    raw = r.get(key)
    if raw:
        try:
            return OperationResponse.model_validate_json(raw)
        except Exception as exc:
            logger.warning("Failed to deserialise operation %s: %s", operation_id, exc)

    # Fallback: check legacy v1 result key
    legacy_raw = r.get(f"{_RESULT_KEY_PREFIX}{operation_id}")
    if legacy_raw:
        try:
            data = json.loads(legacy_raw)
            return OperationResponse(
                operation_id=operation_id,
                intent=data.get("intent", "product-render"),
                status=data.get("status", "completed"),
                sku=data.get("sku", ""),
                created_at=data.get("completed_at", datetime.now(UTC).isoformat()),
                result=data,
                error=data.get("error", ""),
                cost_usd=float(data.get("cost_usd", 0.0)),
                stage_timings=data.get("stage_timings", {}),
            )
        except Exception:
            pass
    return None


def _register_webhook_for_op(operation_id: str, webhook_url: str) -> None:
    """Store a per-operation webhook URL in Redis for the consumer to deliver."""
    r = _get_redis()
    if r is None:
        return
    try:
        r.setex(f"elite_studio:job_webhook:{operation_id}", 86_400, webhook_url)
    except Exception as exc:
        logger.warning("Failed to register webhook for op %s: %s", operation_id, exc)


def _cancel_queued_op(r: Any, operation_id: str) -> bool:
    """Remove an operation from the priority queue. Returns True if removed."""
    removed = r.zrem(_QUEUE_NAME, operation_id)
    return bool(removed)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/operations",
    response_model=OperationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a creative operation (enqueue or sync)",
)
async def create_operation(
    body: CreateOperationRequest,
    _auth=Depends(_api_key_dep),
):
    """Create a creative operation.

    - ``async_mode=True`` (default): enqueues via Redis, returns immediately with
      status "queued". Poll ``GET /operations/{id}`` for completion.
    - ``async_mode=False``: runs the graph synchronously, returns the completed
      result inline. Blocks until the operation finishes.
    """
    created_at = datetime.now(UTC).isoformat()

    if not body.async_mode:
        # Synchronous path — run the graph inline
        try:
            final_state = run_creative(
                intent=body.intent,
                params=body.params,
                sku=body.sku,
            )
        except Exception as exc:
            logger.error("Sync creative run failed intent=%s: %s", body.intent, exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Creative operation failed: {exc}",
            ) from exc

        op_status = "completed" if final_state.get("status") == "success" else "failed"
        op = OperationResponse(
            operation_id=final_state.get("operation_id", ""),
            intent=body.intent,
            status=op_status,
            sku=body.sku,
            created_at=created_at,
            result={k: v for k, v in final_state.items() if v is not None},
            error=final_state.get("error", ""),
            cost_usd=float(final_state.get("cost_usd", 0.0)),
            stage_timings=final_state.get("stage_timings", {}),
        )
        r = _get_redis()
        if r is not None:
            _store_operation(r, op)
        return op

    # Async path — enqueue
    try:
        job_id = enqueue_creative(
            intent=body.intent,
            params=body.params,
            sku=body.sku,
            priority=body.priority,
        )
    except Exception as exc:
        logger.error("Failed to enqueue creative op intent=%s: %s", body.intent, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Queue unavailable: {exc}",
        ) from exc

    op = OperationResponse(
        operation_id=job_id,
        intent=body.intent,
        status="queued",
        sku=body.sku,
        created_at=created_at,
    )
    r = _get_redis()
    if r is not None:
        _store_operation(r, op)
        if body.webhook_url:
            _register_webhook_for_op(job_id, body.webhook_url)

    return op


@router.get(
    "/operations/{operation_id}",
    response_model=OperationResponse,
    summary="Get creative operation status and result",
)
async def get_operation(
    operation_id: str,
    _auth=Depends(_api_key_dep),
):
    """Return status and result for a specific operation.

    For async operations, checks Redis for the latest state.
    Completed operations include the full result payload.
    """
    r = _require_redis()
    op = _fetch_operation(r, operation_id)
    if op is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operation not found: {operation_id}",
        )
    return op


@router.get(
    "/operations",
    response_model=OperationListResponse,
    summary="List creative operations (paginated, filterable)",
)
async def list_operations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    intent: str | None = Query(default=None),
    sku: str | None = Query(default=None),
    _auth=Depends(_api_key_dep),
):
    """List creative operations with optional filters.

    Filters: ``status``, ``intent``, ``sku``.
    Results sorted by ``created_at`` descending.
    """
    r = _require_redis()
    try:
        keys = r.keys(f"{_OP_KEY_PREFIX}*")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis error: {exc}",
        ) from exc

    operations: list[OperationResponse] = []
    for key in keys:
        raw = r.get(key)
        if not raw:
            continue
        try:
            op = OperationResponse.model_validate_json(raw)
        except Exception:
            continue

        if status_filter and op.status != status_filter:
            continue
        if intent and op.intent != intent:
            continue
        if sku and op.sku != sku.lower():
            continue
        operations.append(op)

    operations.sort(key=lambda o: o.created_at, reverse=True)
    total = len(operations)
    start = (page - 1) * page_size
    paginated = operations[start : start + page_size]

    return OperationListResponse(
        operations=paginated,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete(
    "/operations/{operation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel a queued creative operation",
)
async def cancel_operation(
    operation_id: str,
    _auth=Depends(_api_key_dep),
):
    """Cancel a queued operation.

    No-ops silently if the operation is already running or complete.
    Returns 404 if the operation does not exist at all.
    """
    r = _require_redis()

    # Attempt removal from the priority queue
    removed = _cancel_queued_op(r, operation_id)
    if removed:
        # Update stored status to "cancelled"
        op = _fetch_operation(r, operation_id)
        if op:
            cancelled = op.model_copy(update={"status": "cancelled"})
            _store_operation(r, cancelled)
        return None

    # Not in queue — check if it exists at all
    op = _fetch_operation(r, operation_id)
    if op is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operation not found: {operation_id}",
        )
    return None
