"""Persistent job state for the clothing 3D pipeline.

A single :class:`JobStore` interface backed by either an in-memory dict
(dev / tests) or Redis (prod). The store survives worker restarts when
Redis-backed, so the ``/v1/clothing-3d/jobs/{id}`` endpoint can return
state even after the API replica that received the submission has died.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

from pipelines.clothing_3d.models import (
    PipelineRequest,
    PipelineResult,
    PipelineStatus,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Job record
# =============================================================================


@dataclass(slots=True)
class JobRecord:
    """Persisted state for one pipeline submission.

    Attributes:
        job_id: External identifier returned to the caller.
        status: Pipeline status — flows ``queued → running → succeeded |
            failed | rejected``.
        request: The original request (used by the worker to actually run).
        result: Set once the run terminates.
        error: String error if the run failed outside the pipeline (e.g.
            worker crash).
        submitted_at: Wall-clock submission time.
        started_at: When the worker picked up the job.
        finished_at: When the worker emitted the result.
        attempt: 1-indexed retry counter (incremented per retry).
        worker_id: Identifier of the worker that processed the job.
        idempotency_key: Optional caller-supplied dedupe key (echoed back).
    """

    job_id: str
    status: PipelineStatus = PipelineStatus.PENDING
    request: PipelineRequest | None = None
    result: PipelineResult | None = None
    error: str | None = None
    submitted_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    finished_at: datetime | None = None
    attempt: int = 0
    worker_id: str | None = None
    idempotency_key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["submitted_at"] = self.submitted_at.isoformat()
        payload["started_at"] = self.started_at.isoformat() if self.started_at else None
        payload["finished_at"] = self.finished_at.isoformat() if self.finished_at else None
        if self.request is not None:
            payload["request"] = self.request.model_dump(mode="json")
        if self.result is not None:
            payload["result"] = self.result.model_dump(mode="json")
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> JobRecord:
        return cls(
            job_id=payload["job_id"],
            status=PipelineStatus(payload["status"]),
            request=(
                PipelineRequest.model_validate(payload["request"])
                if payload.get("request")
                else None
            ),
            result=(
                PipelineResult.model_validate(payload["result"]) if payload.get("result") else None
            ),
            error=payload.get("error"),
            submitted_at=datetime.fromisoformat(payload["submitted_at"]),
            started_at=(
                datetime.fromisoformat(payload["started_at"]) if payload.get("started_at") else None
            ),
            finished_at=(
                datetime.fromisoformat(payload["finished_at"])
                if payload.get("finished_at")
                else None
            ),
            attempt=payload.get("attempt", 0),
            worker_id=payload.get("worker_id"),
            idempotency_key=payload.get("idempotency_key"),
        )


# =============================================================================
# Protocol
# =============================================================================


@runtime_checkable
class JobStore(Protocol):
    """Async key-value store of :class:`JobRecord`."""

    async def put(self, job: JobRecord) -> None: ...

    async def get(self, job_id: str) -> JobRecord | None: ...

    async def update(self, job: JobRecord) -> None: ...

    async def list(self, *, limit: int = 100) -> list[JobRecord]: ...

    async def close(self) -> None: ...


# =============================================================================
# In-memory implementation
# =============================================================================


class InMemoryJobStore:
    """Single-process job store. Used in dev, tests, and as the default for the API."""

    def __init__(self, *, capacity: int = 1024) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._capacity = capacity
        self._lock = asyncio.Lock()

    async def put(self, job: JobRecord) -> None:
        async with self._lock:
            if len(self._jobs) >= self._capacity and job.job_id not in self._jobs:
                # FIFO eviction by submission time
                oldest = min(self._jobs, key=lambda k: self._jobs[k].submitted_at)
                self._jobs.pop(oldest, None)
            self._jobs[job.job_id] = job

    async def get(self, job_id: str) -> JobRecord | None:
        async with self._lock:
            return self._jobs.get(job_id)

    async def update(self, job: JobRecord) -> None:
        await self.put(job)

    async def list(self, *, limit: int = 100) -> list[JobRecord]:
        async with self._lock:
            return sorted(
                self._jobs.values(),
                key=lambda j: j.submitted_at,
                reverse=True,
            )[:limit]

    async def close(self) -> None:
        """No-op. The dict is shared across the API and worker; clearing it
        here would orphan in-flight jobs whose owners outlive ``close()``.
        Use :meth:`reset` explicitly when you want to discard state (tests).
        """
        return

    async def reset(self) -> None:
        """Discard all jobs. Tests only — never call in production."""
        async with self._lock:
            self._jobs.clear()


# =============================================================================
# Redis implementation
# =============================================================================


class RedisJobStore:
    """Redis-backed job store. Use for multi-worker deployments.

    Schema:
        - One Redis key per job: ``{prefix}:job:{job_id}`` (string with JSON value)
        - A sorted set ``{prefix}:jobs`` for chronological listing
            (score = submitted_at unix timestamp)

    Both keys auto-expire via ``ttl_seconds`` so stale jobs don't accrue.
    """

    def __init__(
        self,
        *,
        url: str | None = None,
        prefix: str = "clothing3d",
        ttl_seconds: int = 7 * 24 * 3600,
    ) -> None:
        self._url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._prefix = prefix
        self._ttl = ttl_seconds
        self._client: Any = None
        self._lock = asyncio.Lock()

    async def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        async with self._lock:
            if self._client is not None:
                return self._client
            try:
                import redis.asyncio as redis  # type: ignore[import-not-found]
            except ImportError as e:
                raise RuntimeError("RedisJobStore requires `redis>=5` — pip install redis") from e
            self._client = redis.from_url(self._url, decode_responses=True)
            return self._client

    def _key(self, job_id: str) -> str:
        return f"{self._prefix}:job:{job_id}"

    @property
    def _index_key(self) -> str:
        return f"{self._prefix}:jobs"

    async def put(self, job: JobRecord) -> None:
        client = await self._get_client()
        payload = json.dumps(job.to_dict(), default=str)
        pipe = client.pipeline()
        pipe.set(self._key(job.job_id), payload, ex=self._ttl)
        pipe.zadd(self._index_key, {job.job_id: job.submitted_at.timestamp()})
        await pipe.execute()

    async def get(self, job_id: str) -> JobRecord | None:
        client = await self._get_client()
        raw = await client.get(self._key(job_id))
        if not raw:
            return None
        return JobRecord.from_dict(json.loads(raw))

    async def update(self, job: JobRecord) -> None:
        await self.put(job)

    async def list(self, *, limit: int = 100) -> list[JobRecord]:
        client = await self._get_client()
        ids = await client.zrevrange(self._index_key, 0, limit - 1)
        if not ids:
            return []
        raw_payloads = await client.mget(*[self._key(i) for i in ids])
        out: list[JobRecord] = []
        for raw in raw_payloads:
            if raw:
                out.append(JobRecord.from_dict(json.loads(raw)))
        return out

    async def stream_updates(
        self,
        *,
        interval_seconds: float = 1.0,
    ) -> AsyncIterator[JobRecord]:
        """Poll-based stream of recent job updates. Useful for dashboards."""
        last_seen: dict[str, datetime | None] = {}
        while True:
            jobs = await self.list(limit=50)
            for j in jobs:
                fp = j.finished_at or j.started_at or j.submitted_at
                if last_seen.get(j.job_id) != fp:
                    last_seen[j.job_id] = fp
                    yield j
            await asyncio.sleep(interval_seconds)

    async def close(self) -> None:
        if self._client is not None:
            try:
                await self._client.aclose()
            except AttributeError:  # older redis-py
                await self._client.close()
            self._client = None


# =============================================================================
# Factory
# =============================================================================


def build_job_store() -> JobStore:
    """Pick the right store based on environment.

    ``REDIS_URL`` set → :class:`RedisJobStore`, else :class:`InMemoryJobStore`.
    Override explicitly via ``CLOTHING_3D_JOB_STORE`` (``memory`` | ``redis``).
    """
    backend = os.getenv("CLOTHING_3D_JOB_STORE")
    if backend == "memory":
        return InMemoryJobStore()
    if backend == "redis" or os.getenv("REDIS_URL"):
        return RedisJobStore()
    return InMemoryJobStore()


__all__ = [
    "InMemoryJobStore",
    "JobRecord",
    "JobStore",
    "RedisJobStore",
    "build_job_store",
]
