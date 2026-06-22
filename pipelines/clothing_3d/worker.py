"""Background worker for the clothing 3D pipeline.

Single-process async worker that:

1. Pulls a :class:`QueueMessage` from the job queue.
2. Loads the matching :class:`JobRecord` from the job store.
3. Runs the pipeline via :class:`ClothingPipeline`, honoring the retry policy
   and the per-backend cost quota.
4. Persists the final :class:`PipelineResult` back to the store, ACKs the
   queue.

Crash-safety: a worker that dies mid-job leaves the message unacked. With
:class:`RedisStreamsQueue`, :meth:`reclaim_pending` on a sibling worker
re-delivers the message after ``reclaim_idle_ms``. With
:class:`InMemoryQueue`, the message is lost (acceptable for dev).

Scale-out: launch multiple worker processes (``CLOTHING_3D_WORKERS=4``); each
sets a unique ``consumer_name`` and Redis Streams load-balances naturally.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import socket
import uuid
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any

from services.three_d.trellis.config import TrellisConfig

from pipelines.clothing_3d.events import PipelineEventBus
from pipelines.clothing_3d.job_store import JobRecord, JobStore, build_job_store
from pipelines.clothing_3d.models import PipelineRequest, PipelineStatus
from pipelines.clothing_3d.observability import (
    configure_logging,
    get_metrics,
    metrics_event_subscriber,
)
from pipelines.clothing_3d.pipeline import ClothingPipeline
from pipelines.clothing_3d.queue import JobQueue, QueueMessage, build_queue
from pipelines.clothing_3d.reliability import (
    CostQuota,
    IdempotencyCache,
    QuotaExceededError,
    RetryPolicy,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Worker
# =============================================================================


class PipelineWorker:
    """Long-running async worker.

    Args:
        pipeline: Pre-built :class:`ClothingPipeline`. Defaults from env.
        queue: Pre-built :class:`JobQueue`. Defaults from env.
        store: Pre-built :class:`JobStore`. Defaults from env.
        concurrency: Concurrent in-flight jobs.
        retry: Per-job retry policy when the pipeline raises a retryable error.
        quota: Per-backend cost ceiling.
        idempotency: Skip dispatch when an identical fingerprint just succeeded.
        worker_id: Display name; defaults to ``${HOSTNAME}-${PID}-${RAND}``.
        reclaim_interval_seconds: How often to re-queue dropped messages.
        poll_block_seconds: How long each ``dequeue`` blocks; affects shutdown latency.
    """

    def __init__(
        self,
        *,
        pipeline: ClothingPipeline | None = None,
        queue: JobQueue | None = None,
        store: JobStore | None = None,
        concurrency: int = 1,
        retry: RetryPolicy | None = None,
        quota: CostQuota | None = None,
        idempotency: IdempotencyCache | None = None,
        worker_id: str | None = None,
        reclaim_interval_seconds: float = 30.0,
        poll_block_seconds: float = 5.0,
        owns_dependencies: bool | None = None,
    ) -> None:
        # We own dependencies only when we built them ourselves — otherwise
        # the caller (API, test harness) owns lifecycle and we'd corrupt
        # their state by closing on shutdown.
        owned_default = (pipeline is None) and (queue is None) and (store is None)
        self._owns_dependencies = owned_default if owns_dependencies is None else owns_dependencies
        self.pipeline = pipeline or ClothingPipeline(config=TrellisConfig.from_env())
        self.queue = queue or build_queue()
        self.store = store or build_job_store()
        self.concurrency = max(1, concurrency)
        self.retry = retry or RetryPolicy()
        self.quota = quota or CostQuota()
        self.idempotency = idempotency or IdempotencyCache()
        self.worker_id = worker_id or _build_worker_id()
        self.reclaim_interval_seconds = reclaim_interval_seconds
        self.poll_block_seconds = poll_block_seconds

        self._metrics = get_metrics()
        self._stop = asyncio.Event()
        self._sem = asyncio.Semaphore(self.concurrency)
        self._inflight: set[asyncio.Task[Any]] = set()

        # Wire metrics into the pipeline's event bus.
        if isinstance(self.pipeline.event_bus, PipelineEventBus):
            self.pipeline.event_bus.subscribe(metrics_event_subscriber(self._metrics))

    # ---------------------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------------------

    async def run(self) -> None:
        """Main loop. Returns when :meth:`shutdown` is called."""
        logger.info(
            "worker.start id=%s concurrency=%s queue=%s store=%s",
            self.worker_id,
            self.concurrency,
            type(self.queue).__name__,
            type(self.store).__name__,
        )
        reclaim_task: asyncio.Task[Any] | None = None
        if hasattr(self.queue, "reclaim_pending"):
            reclaim_task = asyncio.create_task(self._reclaim_loop(), name="reclaim-loop")

        try:
            while not self._stop.is_set():
                # Backpressure: gate dequeue on the semaphore.
                await self._sem.acquire()
                msg = await self.queue.dequeue(block_seconds=self.poll_block_seconds)
                if msg is None:
                    self._sem.release()
                    continue

                task = asyncio.create_task(self._process_one(msg), name=f"job-{msg.job_id}")
                self._inflight.add(task)
                task.add_done_callback(self._on_task_done)
        finally:
            if reclaim_task:
                reclaim_task.cancel()
                with suppress(asyncio.CancelledError):
                    await reclaim_task
            await self._drain()
            if self._owns_dependencies:
                await self.queue.close()
                await self.store.close()
                await self.pipeline.close()
            logger.info("worker.stopped id=%s", self.worker_id)

    async def shutdown(self) -> None:
        """Request a clean shutdown. Idempotent."""
        self._stop.set()

    # ---------------------------------------------------------------------
    # Per-job pipeline
    # ---------------------------------------------------------------------

    async def _process_one(self, msg: QueueMessage) -> None:
        try:
            job = await self.store.get(msg.job_id)
            if job is None:
                logger.warning("worker.job_missing job_id=%s", msg.job_id)
                await self.queue.ack(msg)
                return
            if job.request is None:
                logger.warning("worker.no_request job_id=%s", msg.job_id)
                job.status = PipelineStatus.FAILED
                job.error = "missing request body"
                job.finished_at = datetime.now(UTC)
                await self.store.update(job)
                await self.queue.ack(msg)
                return

            await self._mark_running(job, msg)
            backend = self._backend_for(job.request)
            try:
                self.quota.charge(backend)
            except QuotaExceededError as exc:
                logger.warning(
                    "worker.quota_exceeded backend=%s job=%s err=%s", backend, job.job_id, exc
                )
                job.status = PipelineStatus.FAILED
                job.error = f"quota exceeded: {exc}"
                job.finished_at = datetime.now(UTC)
                await self.store.update(job)
                await self.queue.ack(msg)
                return

            await self._run_with_retry(job, msg, backend)
        except Exception as exc:  # noqa: BLE001 — worker must never crash on a job
            logger.exception("worker.unhandled job=%s", msg.job_id)
            await self._fail_terminal(msg, str(exc))
        finally:
            self._sem.release()

    async def _mark_running(self, job: JobRecord, msg: QueueMessage) -> None:
        job.status = PipelineStatus.RUNNING
        job.started_at = datetime.now(UTC)
        job.attempt = msg.attempt
        job.worker_id = self.worker_id
        await self.store.update(job)

    async def _run_with_retry(
        self,
        job: JobRecord,
        msg: QueueMessage,
        backend: str,
    ) -> None:
        async def _runner(req: PipelineRequest):
            return await self.pipeline.run(req)

        try:
            result, hit = await self.idempotency.get_or_run(job.request, runner=_runner)  # type: ignore[arg-type]
            self._metrics.cache_total.labels(outcome="hit" if hit else "miss").inc()
            if backend in {"replicate", "modal"} and not hit:
                cost_usd = self.quota.spent(backend) - (
                    self.quota.spent(backend) - 0.0  # placeholder; charge already recorded
                )
                self._metrics.backend_cost_usd.labels(backend=backend).inc(max(cost_usd, 0.0))

            job.result = result
            job.status = result.status
            job.error = None
        except Exception as exc:  # noqa: BLE001
            job.status = PipelineStatus.FAILED
            job.error = f"{type(exc).__name__}: {exc}"
            logger.exception("worker.pipeline_error job=%s", job.job_id)

        job.finished_at = datetime.now(UTC)
        await self.store.update(job)

        terminal = job.status in {PipelineStatus.SUCCEEDED, PipelineStatus.REJECTED}
        if terminal or job.attempt >= self.retry.max_attempts:
            await self.queue.ack(msg)
        else:
            logger.info(
                "worker.requeue job=%s attempt=%s err=%s",
                job.job_id,
                job.attempt,
                job.error,
            )
            await self.queue.nack(msg, requeue=True)

    async def _fail_terminal(self, msg: QueueMessage, error: str) -> None:
        job = await self.store.get(msg.job_id)
        if job is not None:
            job.status = PipelineStatus.FAILED
            job.error = error
            job.finished_at = datetime.now(UTC)
            await self.store.update(job)
        with suppress(Exception):  # noqa: BLE001
            await self.queue.ack(msg)

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    def _backend_for(self, request: PipelineRequest) -> str:
        if request.backend is not None:
            return request.backend.value
        return self.pipeline.provider.config.backend.value

    def _on_task_done(self, task: asyncio.Task[Any]) -> None:
        self._inflight.discard(task)

    async def _drain(self) -> None:
        if not self._inflight:
            return
        logger.info("worker.draining count=%s", len(self._inflight))
        await asyncio.gather(*self._inflight, return_exceptions=True)

    async def _reclaim_loop(self) -> None:
        reclaim = getattr(self.queue, "reclaim_pending", None)
        if reclaim is None:
            return
        while not self._stop.is_set():
            try:
                count = await reclaim()
                if count:
                    logger.info("worker.reclaimed count=%s", count)
            except Exception:  # noqa: BLE001
                logger.exception("worker.reclaim_failed")
            try:
                await asyncio.wait_for(
                    self._stop.wait(),
                    timeout=self.reclaim_interval_seconds,
                )
            except TimeoutError:
                pass


def _build_worker_id() -> str:
    host = socket.gethostname()
    return f"{host}-{os.getpid()}-{uuid.uuid4().hex[:6]}"


# =============================================================================
# CLI entry
# =============================================================================


async def _run_worker(args: Any) -> int:
    configure_logging(level=args.log_level)
    worker = PipelineWorker(concurrency=args.concurrency)

    loop = asyncio.get_running_loop()

    async def _shutdown(sig: signal.Signals) -> None:
        logger.info("worker.signal sig=%s", sig.name)
        await worker.shutdown()

    for sig_name in ("SIGINT", "SIGTERM"):
        sig = getattr(signal, sig_name, None)
        if sig is None:
            continue
        try:
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(_shutdown(s)))
        except NotImplementedError:  # pragma: no cover — Windows
            pass

    await worker.run()
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point: ``python -m pipelines.clothing_3d.worker``."""
    import argparse

    parser = argparse.ArgumentParser(prog="clothing_3d.worker")
    parser.add_argument(
        "--concurrency", type=int, default=int(os.getenv("CLOTHING_3D_CONCURRENCY", "1"))
    )
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))
    args = parser.parse_args(argv)
    return asyncio.run(_run_worker(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


__all__ = ["PipelineWorker", "main"]
