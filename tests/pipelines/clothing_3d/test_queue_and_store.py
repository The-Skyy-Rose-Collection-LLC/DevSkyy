"""Unit tests for InMemoryQueue + InMemoryJobStore."""

from __future__ import annotations

import asyncio

import pytest

from pipelines.clothing_3d.job_store import InMemoryJobStore, JobRecord
from pipelines.clothing_3d.models import PipelineRequest, PipelineStatus
from pipelines.clothing_3d.queue import InMemoryQueue

# =============================================================================
# InMemoryQueue
# =============================================================================


@pytest.mark.asyncio
async def test_enqueue_dequeue_ack_roundtrip() -> None:
    q = InMemoryQueue()
    await q.enqueue("job-1")
    msg = await q.dequeue(block_seconds=1.0)
    assert msg is not None
    assert msg.job_id == "job-1"
    assert msg.attempt == 1
    await q.ack(msg)
    # After ack the queue is empty
    assert await q.depth() == 0
    assert await q.dequeue(block_seconds=0.05) is None


@pytest.mark.asyncio
async def test_nack_requeues_with_incremented_attempt() -> None:
    q = InMemoryQueue()
    await q.enqueue("job-1")
    msg = await q.dequeue(block_seconds=1.0)
    assert msg is not None
    await q.nack(msg, requeue=True)

    msg2 = await q.dequeue(block_seconds=1.0)
    assert msg2 is not None
    assert msg2.job_id == "job-1"
    assert msg2.attempt == msg.attempt + 1


@pytest.mark.asyncio
async def test_nack_no_requeue_drops_message() -> None:
    q = InMemoryQueue()
    await q.enqueue("drop-me")
    msg = await q.dequeue(block_seconds=1.0)
    assert msg is not None
    await q.nack(msg, requeue=False)
    assert await q.dequeue(block_seconds=0.05) is None


@pytest.mark.asyncio
async def test_depth_reports_pending_messages() -> None:
    q = InMemoryQueue()
    for i in range(3):
        await q.enqueue(f"j{i}")
    assert await q.depth() == 3


# =============================================================================
# InMemoryJobStore
# =============================================================================


def _make_record(job_id: str) -> JobRecord:
    return JobRecord(
        job_id=job_id,
        status=PipelineStatus.PENDING,
        request=PipelineRequest(prompt="x", product_name="x"),
    )


@pytest.mark.asyncio
async def test_store_put_and_get() -> None:
    store = InMemoryJobStore()
    rec = _make_record("a")
    await store.put(rec)
    fetched = await store.get("a")
    assert fetched is not None
    assert fetched.job_id == "a"
    assert fetched.status == PipelineStatus.PENDING


@pytest.mark.asyncio
async def test_store_update_replaces_record() -> None:
    store = InMemoryJobStore()
    rec = _make_record("a")
    await store.put(rec)

    rec.status = PipelineStatus.SUCCEEDED
    await store.update(rec)

    fetched = await store.get("a")
    assert fetched is not None
    assert fetched.status == PipelineStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_store_list_returns_newest_first() -> None:
    store = InMemoryJobStore()
    await store.put(_make_record("a"))
    await asyncio.sleep(0.01)
    await store.put(_make_record("b"))

    jobs = await store.list(limit=10)
    assert [j.job_id for j in jobs] == ["b", "a"]


@pytest.mark.asyncio
async def test_store_evicts_oldest_at_capacity() -> None:
    store = InMemoryJobStore(capacity=2)
    await store.put(_make_record("a"))
    await asyncio.sleep(0.01)
    await store.put(_make_record("b"))
    await asyncio.sleep(0.01)
    await store.put(_make_record("c"))

    assert await store.get("a") is None
    assert await store.get("b") is not None
    assert await store.get("c") is not None


@pytest.mark.asyncio
async def test_record_to_from_dict_roundtrip() -> None:
    rec = _make_record("rt-1")
    rec.attempt = 2
    rec.worker_id = "worker-7"
    rec.idempotency_key = "sha256:abc"

    payload = rec.to_dict()
    restored = JobRecord.from_dict(payload)
    assert restored.job_id == "rt-1"
    assert restored.status == PipelineStatus.PENDING
    assert restored.attempt == 2
    assert restored.worker_id == "worker-7"
    assert restored.idempotency_key == "sha256:abc"
    assert restored.request is not None
    assert restored.request.prompt == "x"
