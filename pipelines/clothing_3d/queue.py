"""Queue abstraction for the clothing 3D worker.

Two implementations:

- :class:`InMemoryQueue` — single-process ``asyncio.Queue`` for dev / tests.
- :class:`RedisStreamsQueue` — Redis Streams with consumer groups for prod.
  Consumer groups give at-least-once delivery plus per-worker isolation, and
  ``XACK`` only on success means a crashed worker's job is automatically
  reclaimed by another worker after ``XCLAIM``.

The :class:`QueueMessage` envelope carries the job_id; the worker resolves
the full :class:`JobRecord` from the :class:`JobStore`. This avoids dumping
large request bodies into Redis Streams twice.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


# =============================================================================
# Message envelope
# =============================================================================


@dataclass(frozen=True, slots=True)
class QueueMessage:
    """Worker job envelope.

    Attributes:
        job_id: Lookup key into :class:`JobStore`.
        delivery_id: Backend-specific ID needed to ACK the message.
        enqueued_at: When the producer pushed it.
        attempt: Delivery attempt number (>=1).
    """

    job_id: str
    delivery_id: str
    enqueued_at: datetime
    attempt: int = 1


# =============================================================================
# Protocol
# =============================================================================


@runtime_checkable
class JobQueue(Protocol):
    """Pluggable queue contract used by the worker."""

    async def enqueue(self, job_id: str) -> None: ...

    async def dequeue(self, *, block_seconds: float = 5.0) -> QueueMessage | None: ...

    async def ack(self, message: QueueMessage) -> None: ...

    async def nack(self, message: QueueMessage, *, requeue: bool = True) -> None: ...

    async def depth(self) -> int: ...

    async def close(self) -> None: ...


# =============================================================================
# In-memory implementation
# =============================================================================


class InMemoryQueue:
    """Single-process queue. Fine for dev and tests; ephemeral on restart."""

    def __init__(self, *, maxsize: int = 1024) -> None:
        self._q: asyncio.Queue[QueueMessage] = asyncio.Queue(maxsize=maxsize)
        self._unacked: dict[str, QueueMessage] = {}

    async def enqueue(self, job_id: str) -> None:
        msg = QueueMessage(
            job_id=job_id,
            delivery_id=str(uuid.uuid4()),
            enqueued_at=datetime.now(UTC),
        )
        await self._q.put(msg)

    async def dequeue(self, *, block_seconds: float = 5.0) -> QueueMessage | None:
        try:
            msg = await asyncio.wait_for(self._q.get(), timeout=block_seconds)
        except asyncio.TimeoutError:
            return None
        self._unacked[msg.delivery_id] = msg
        return msg

    async def ack(self, message: QueueMessage) -> None:
        self._unacked.pop(message.delivery_id, None)
        self._q.task_done()

    async def nack(self, message: QueueMessage, *, requeue: bool = True) -> None:
        self._unacked.pop(message.delivery_id, None)
        self._q.task_done()
        if requeue:
            requeued = QueueMessage(
                job_id=message.job_id,
                delivery_id=str(uuid.uuid4()),
                enqueued_at=datetime.now(UTC),
                attempt=message.attempt + 1,
            )
            await self._q.put(requeued)

    async def depth(self) -> int:
        return self._q.qsize()

    async def close(self) -> None:
        pass


# =============================================================================
# Redis Streams implementation
# =============================================================================


class RedisStreamsQueue:
    """At-least-once queue backed by Redis Streams.

    Schema:
        Stream:   ``{prefix}:queue``  (field: ``job_id``)
        Group:    ``{prefix}:workers`` (auto-created)

    Best practices:
    - Workers ``XREADGROUP`` then explicitly ``XACK`` only on full success.
    - Crashed worker's pending messages auto-reclaimed by another via
      :meth:`reclaim_pending` (call periodically from a janitor task).
    - Backpressure: cap stream length with ``MAXLEN`` to drop oldest if
      producers outrun consumers (configurable).
    """

    def __init__(
        self,
        *,
        url: str | None = None,
        prefix: str = "clothing3d",
        consumer_group: str = "workers",
        consumer_name: str | None = None,
        maxlen: int = 10_000,
        reclaim_idle_ms: int = 60_000,
    ) -> None:
        self._url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._prefix = prefix
        self._group = consumer_group
        self._consumer_name = consumer_name or f"worker-{uuid.uuid4().hex[:8]}"
        self._maxlen = maxlen
        self._reclaim_idle_ms = reclaim_idle_ms
        self._client: Any = None
        self._group_ensured = False
        self._lock = asyncio.Lock()

    @property
    def _stream(self) -> str:
        return f"{self._prefix}:queue"

    async def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        async with self._lock:
            if self._client is not None:
                return self._client
            try:
                import redis.asyncio as redis  # type: ignore[import-not-found]
            except ImportError as e:
                raise RuntimeError(
                    "RedisStreamsQueue requires `redis>=5` — pip install redis"
                ) from e
            self._client = redis.from_url(self._url, decode_responses=True)
            return self._client

    async def _ensure_group(self) -> None:
        if self._group_ensured:
            return
        client = await self._get_client()
        try:
            await client.xgroup_create(self._stream, self._group, id="0", mkstream=True)
        except Exception as exc:  # noqa: BLE001 — only BUSYGROUP is acceptable
            msg = str(exc)
            if "BUSYGROUP" not in msg:
                logger.warning("xgroup_create error: %s", msg)
        self._group_ensured = True

    async def enqueue(self, job_id: str) -> None:
        client = await self._get_client()
        await self._ensure_group()
        await client.xadd(
            self._stream,
            {"job_id": job_id, "enqueued_at": datetime.now(UTC).isoformat()},
            maxlen=self._maxlen,
            approximate=True,
        )

    async def dequeue(self, *, block_seconds: float = 5.0) -> QueueMessage | None:
        client = await self._get_client()
        await self._ensure_group()
        block_ms = int(block_seconds * 1000)
        result = await client.xreadgroup(
            self._group,
            self._consumer_name,
            {self._stream: ">"},
            count=1,
            block=block_ms,
        )
        if not result:
            return None
        # result = [(stream, [(delivery_id, {fields})])]
        _, items = result[0]
        delivery_id, fields = items[0]
        return QueueMessage(
            job_id=fields["job_id"],
            delivery_id=delivery_id,
            enqueued_at=datetime.fromisoformat(fields["enqueued_at"]),
            attempt=int(fields.get("attempt", 1)),
        )

    async def ack(self, message: QueueMessage) -> None:
        client = await self._get_client()
        await client.xack(self._stream, self._group, message.delivery_id)
        # Trim acknowledged entries; they're not needed in the stream.
        try:
            await client.xdel(self._stream, message.delivery_id)
        except Exception:  # noqa: BLE001 — best effort
            pass

    async def nack(self, message: QueueMessage, *, requeue: bool = True) -> None:
        client = await self._get_client()
        await client.xack(self._stream, self._group, message.delivery_id)
        try:
            await client.xdel(self._stream, message.delivery_id)
        except Exception:  # noqa: BLE001
            pass
        if requeue:
            await client.xadd(
                self._stream,
                {
                    "job_id": message.job_id,
                    "enqueued_at": datetime.now(UTC).isoformat(),
                    "attempt": message.attempt + 1,
                },
                maxlen=self._maxlen,
                approximate=True,
            )

    async def depth(self) -> int:
        client = await self._get_client()
        await self._ensure_group()
        try:
            return int(await client.xlen(self._stream))
        except Exception:  # noqa: BLE001
            return -1

    async def reclaim_pending(self) -> int:
        """Reclaim messages idle longer than ``reclaim_idle_ms``.

        Returns the number of messages reclaimed. Run from a janitor task
        every minute or so to recover from worker crashes.
        """
        client = await self._get_client()
        await self._ensure_group()
        try:
            _, claimed, _ = await client.xautoclaim(
                self._stream,
                self._group,
                self._consumer_name,
                min_idle_time=self._reclaim_idle_ms,
                count=100,
            )
            return len(claimed)
        except Exception as exc:  # noqa: BLE001
            logger.warning("xautoclaim failed: %s", exc)
            return 0

    async def close(self) -> None:
        if self._client is not None:
            try:
                await self._client.aclose()
            except AttributeError:
                await self._client.close()
            self._client = None


# =============================================================================
# Factory
# =============================================================================


def build_queue() -> JobQueue:
    """Pick the right queue per environment.

    ``REDIS_URL`` set → :class:`RedisStreamsQueue`, else :class:`InMemoryQueue`.
    Override with ``CLOTHING_3D_QUEUE`` (``memory`` | ``redis``).
    """
    backend = os.getenv("CLOTHING_3D_QUEUE")
    if backend == "memory":
        return InMemoryQueue()
    if backend == "redis" or os.getenv("REDIS_URL"):
        return RedisStreamsQueue()
    return InMemoryQueue()


__all__ = [
    "InMemoryQueue",
    "JobQueue",
    "QueueMessage",
    "RedisStreamsQueue",
    "build_queue",
]
