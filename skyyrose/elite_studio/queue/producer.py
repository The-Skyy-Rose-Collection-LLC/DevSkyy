"""
Elite Studio queue producer — enqueue SKU render jobs.

Wraps agent_sdk.task_queue.TaskQueue for Elite Studio-specific job IDs
and payload structure. Sync-safe: connects/disconnects inside each call
via asyncio.run() so callers don't need an event loop.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import UTC, datetime
from uuid import uuid4

from sdk.python.agent_sdk.task_queue import TaskQueue

from .job_types import EliteStudioJobData

logger = logging.getLogger(__name__)

# Queue name used for all Elite Studio render tasks
ELITE_TASK_TYPE = "elite_studio_produce"


def _make_job_id(sku: str) -> str:
    """Generate a deterministic-prefix, unique job ID."""
    return f"elite:{sku}:{uuid4().hex[:8]}"


def _get_queue() -> TaskQueue:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return TaskQueue(redis_url=redis_url)


def _run_sync(coro):
    """Run *coro* to completion from a sync context.

    Uses asyncio.run() when no loop is active, or dispatches to a short-lived
    worker thread when already inside a running event loop (e.g. when an async
    FastAPI handler calls these sync helpers). asyncio.run() from a running
    loop raises RuntimeError, which was breaking every creative request.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


async def _async_enqueue(job_data: EliteStudioJobData) -> str:
    """Async core for enqueue_produce."""
    queue = _get_queue()
    try:
        job_id = _make_job_id(job_data.sku)
        await queue.enqueue(
            task_type=ELITE_TASK_TYPE,
            task_data={"job_id": job_id, **job_data.model_dump()},
            priority=job_data.priority,
        )
        logger.info(
            "Enqueued Elite Studio job: %s (sku=%s, view=%s)", job_id, job_data.sku, job_data.view
        )
        return job_id
    finally:
        await queue.disconnect()


async def _async_enqueue_batch(job_datas: list[EliteStudioJobData]) -> list[str]:
    """Async core for enqueue_batch — shares one queue connection."""
    queue = _get_queue()
    try:
        job_ids: list[str] = []
        for jd in job_datas:
            job_id = _make_job_id(jd.sku)
            await queue.enqueue(
                task_type=ELITE_TASK_TYPE,
                task_data={"job_id": job_id, **jd.model_dump()},
                priority=jd.priority,
            )
            logger.info("Enqueued Elite Studio job: %s (sku=%s)", job_id, jd.sku)
            job_ids.append(job_id)
        return job_ids
    finally:
        await queue.disconnect()


def enqueue_produce(
    sku: str,
    view: str = "front",
    priority: int = 5,
    enable_compositor: bool = False,
    max_retries: int = 2,
) -> str:
    """Enqueue a single SKU render job.

    Args:
        sku: Product SKU (e.g. "br-001").
        view: Image view — "front" or "back".
        priority: 1-10 (higher = processed sooner).
        enable_compositor: Run scene compositing after generation.
        max_retries: Number of pipeline retries on failure.

    Returns:
        job_id: Unique job identifier (e.g. "elite:br-001:a1b2c3d4").
    """
    job_data = EliteStudioJobData(
        sku=sku,
        view=view,
        priority=priority,
        enable_compositor=enable_compositor,
        max_retries=max_retries,
        submitted_at=datetime.now(UTC).isoformat(),
    )
    return _run_sync(_async_enqueue(job_data))


async def aenqueue_produce(
    sku: str,
    view: str = "front",
    priority: int = 5,
    enable_compositor: bool = False,
    max_retries: int = 2,
) -> str:
    """Async variant of :func:`enqueue_produce` for use inside async handlers."""
    job_data = EliteStudioJobData(
        sku=sku,
        view=view,
        priority=priority,
        enable_compositor=enable_compositor,
        max_retries=max_retries,
        submitted_at=datetime.now(UTC).isoformat(),
    )
    return await _async_enqueue(job_data)


def enqueue_creative(
    intent: str,
    params: dict,
    sku: str = "",
    priority: int = 5,
) -> str:
    """Enqueue a creative operation job.

    Args:
        intent: Creative intent (e.g. "product-render", "social-pack").
        params: Operation-specific parameters.
        sku: Product SKU (optional).
        priority: 1-10 (higher = processed sooner).

    Returns:
        job_id: Unique job identifier.
    """
    job_data = EliteStudioJobData(
        sku=sku or "creative",
        view="front",
        priority=priority,
        intent=intent,
        creative_params=params,
        submitted_at=datetime.now(UTC).isoformat(),
    )
    return _run_sync(_async_enqueue(job_data))


async def aenqueue_creative(
    intent: str,
    params: dict,
    sku: str = "",
    priority: int = 5,
) -> str:
    """Async variant of :func:`enqueue_creative` for use inside async handlers."""
    job_data = EliteStudioJobData(
        sku=sku or "creative",
        view="front",
        priority=priority,
        intent=intent,
        creative_params=params,
        submitted_at=datetime.now(UTC).isoformat(),
    )
    return await _async_enqueue(job_data)


def enqueue_batch(
    skus: list[str],
    view: str = "front",
    priority: int = 5,
    enable_compositor: bool = False,
    max_retries: int = 2,
) -> list[str]:
    """Enqueue multiple SKU render jobs.

    Args:
        skus: List of product SKUs.
        view: Image view — "front" or "back".
        priority: 1-10 (higher = processed sooner).
        enable_compositor: Run scene compositing for all jobs.
        max_retries: Number of pipeline retries on failure.

    Returns:
        List of job_ids in the same order as skus.
    """
    now = datetime.now(UTC).isoformat()
    job_datas = [
        EliteStudioJobData(
            sku=sku,
            view=view,
            priority=priority,
            enable_compositor=enable_compositor,
            max_retries=max_retries,
            submitted_at=now,
        )
        for sku in skus
    ]
    return _run_sync(_async_enqueue_batch(job_datas))


async def aenqueue_batch(
    skus: list[str],
    view: str = "front",
    priority: int = 5,
    enable_compositor: bool = False,
    max_retries: int = 2,
) -> list[str]:
    """Async variant of :func:`enqueue_batch` for use inside async handlers."""
    now = datetime.now(UTC).isoformat()
    job_datas = [
        EliteStudioJobData(
            sku=sku,
            view=view,
            priority=priority,
            enable_compositor=enable_compositor,
            max_retries=max_retries,
            submitted_at=now,
        )
        for sku in skus
    ]
    return await _async_enqueue_batch(job_datas)
