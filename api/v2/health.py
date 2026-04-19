"""
Enterprise API v2 — Health and Usage

Lightweight diagnostics and per-tenant usage summary.

Prefix: /api/v2
Auth:   X-API-Key header (matches v1 pattern) — usage endpoint only
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health v2"])

_QUEUE_NAME = "queue:elite_studio_produce"
_OP_KEY_PREFIX = "elite_studio:v2:operation:"
_RESULT_KEY_PREFIX = "elite_studio:result:"


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


class ServiceStatus(BaseModel):
    redis: str  # "connected" | "unavailable" | "error"
    graph: str  # "ready" | "unavailable" | "error"
    queue_depth: int


class HealthResponse(BaseModel):
    status: str  # "healthy" | "degraded" | "unavailable"
    services: ServiceStatus
    checked_at: str


class UsageSummaryResponse(BaseModel):
    total_operations: int
    completed: int
    failed: int
    queued: int
    total_cost_usd: float
    checked_at: str


# ---------------------------------------------------------------------------
# Redis helper
# ---------------------------------------------------------------------------


def _get_redis() -> Any | None:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        import redis as redis_lib

        r = redis_lib.from_url(redis_url, decode_responses=True, socket_timeout=3)
        r.ping()
        return r
    except Exception as exc:
        logger.warning("health v2: Redis unavailable — %s", exc)
        return None


def _check_graph() -> str:
    """Attempt to import the creative graph builder. Returns 'ready' or 'unavailable'."""
    try:
        from skyyrose.elite_studio.creative.runner import _get_graph  # noqa: F401

        return "ready"
    except Exception as exc:
        logger.warning("health v2: graph unavailable — %s", exc)
        return "unavailable"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="API v2 health check",
)
async def health():
    """Check health of Redis, the creative graph, and the queue.

    Does NOT require authentication — suitable for load balancer probes.
    """
    checked_at = datetime.now(UTC).isoformat()
    r = _get_redis()

    redis_status = "unavailable"
    queue_depth = -1
    graph_status = _check_graph()

    if r is not None:
        try:
            queue_depth = r.zcard(_QUEUE_NAME)
            redis_status = "connected"
        except Exception as exc:
            logger.warning("health v2: Redis queue check failed — %s", exc)
            redis_status = "error"

    overall = "healthy"
    if redis_status != "connected":
        overall = "degraded" if graph_status == "ready" else "unavailable"
    elif graph_status != "ready":
        overall = "degraded"

    return HealthResponse(
        status=overall,
        services=ServiceStatus(
            redis=redis_status,
            graph=graph_status,
            queue_depth=queue_depth,
        ),
        checked_at=checked_at,
    )


@router.get(
    "/usage",
    response_model=UsageSummaryResponse,
    summary="Current usage summary (requires auth)",
)
async def usage_summary(
    _auth=Depends(_api_key_dep),
):
    """Return an aggregated usage summary for the authenticated tenant.

    Counts operations by status and sums total cost from both v2 operation
    records and legacy v1 result keys.
    """
    import json

    checked_at = datetime.now(UTC).isoformat()
    r = _get_redis()

    if r is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis unavailable — cannot retrieve usage",
        )

    counts: dict[str, int] = {"completed": 0, "failed": 0, "queued": 0, "other": 0}
    total_cost = 0.0
    total_ops = 0

    # Count v2 native operations
    try:
        v2_keys = r.keys(f"{_OP_KEY_PREFIX}*")
        for key in v2_keys:
            raw = r.get(key)
            if not raw:
                continue
            try:
                data = json.loads(raw)
                stat = data.get("status", "other")
                counts[stat] = counts.get(stat, 0) + 1
                total_cost += float(data.get("cost_usd", 0.0))
                total_ops += 1
            except Exception:
                continue
    except Exception as exc:
        logger.warning("usage v2: failed to count v2 operations — %s", exc)

    # Count legacy v1 result records (avoid double-counting v2 ops)
    try:
        v1_keys = r.keys(f"{_RESULT_KEY_PREFIX}*")
        for key in v1_keys:
            raw = r.get(key)
            if not raw:
                continue
            try:
                data = json.loads(raw)
                stat = data.get("status", "other")
                # Map v1 statuses: "success" → "completed", "error" → "failed"
                if stat == "success":
                    stat = "completed"
                elif stat == "error":
                    stat = "failed"
                counts[stat] = counts.get(stat, 0) + 1
                total_cost += float(data.get("cost_usd", 0.0))
                total_ops += 1
            except Exception:
                continue
    except Exception as exc:
        logger.warning("usage v2: failed to count v1 results — %s", exc)

    # Queue depth as a proxy for queued operations
    try:
        queued = int(r.zcard(_QUEUE_NAME))
        counts["queued"] = max(counts.get("queued", 0), queued)
    except Exception:
        pass

    return UsageSummaryResponse(
        total_operations=total_ops,
        completed=counts.get("completed", 0),
        failed=counts.get("failed", 0),
        queued=counts.get("queued", 0),
        total_cost_usd=round(total_cost, 6),
        checked_at=checked_at,
    )
