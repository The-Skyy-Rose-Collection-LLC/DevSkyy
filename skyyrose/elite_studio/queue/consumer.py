"""
Elite Studio queue consumer / worker.

Pulls jobs from the Redis priority queue (ZPOPMAX), calls run_single()
from graph/runner.py, stores the result, publishes an event, and handles
SIGTERM cleanly (finishes the current job before exiting).

Degrades gracefully when Redis is unavailable — logs a warning and retries
after a backoff delay rather than crashing.
"""

from __future__ import annotations

import json
import logging
import os
import signal
import socket
import time
from datetime import UTC, datetime
from typing import Any

from ..graph.builder import GraphConfig
from ..graph.runner import run_single
from .dead_letter import DeadLetterQueue
from .job_types import EliteStudioJobData, EliteStudioJobResult


def _get_graph_config(enable_compositor: bool, max_retries: int) -> GraphConfig:
    """Construct a GraphConfig — isolated so tests can patch run_single cleanly."""
    return GraphConfig(enable_compositor=enable_compositor, max_retries=max_retries)


logger = logging.getLogger(__name__)

# Redis key / channel constants
_RESULT_KEY_PREFIX = "elite_studio:result:"
_RESULT_TTL_SECONDS = 86_400  # 24 hours
_EVENT_CHANNEL = "elite_studio:events"
_QUEUE_NAME = "queue:elite_studio_produce"
_LOCK_PREFIX = "elite_studio:lock:"
_LOCK_TTL_SECONDS = 600  # 10 minutes — generous for long renders

_POLL_INTERVAL_SECONDS = 1.0
_ERROR_BACKOFF_SECONDS = 5.0


class EliteStudioWorker:
    """Synchronous worker that processes Elite Studio render jobs from Redis.

    The worker loop:
        1. ZPOPMAX from ``queue:elite_studio_produce``
        2. Acquire an atomic lock (NX) to prevent duplicate processing
        3. Deserialize payload into EliteStudioJobData
        4. Call ``run_single()`` from graph/runner.py
        5. Store EliteStudioJobResult in Redis (24h TTL)
        6. Publish job.completed event on ``elite_studio:events``
        7. On exception: move job to DLQ via DeadLetterQueue

    SIGTERM handling: sets a flag that causes the loop to exit *after* the
    current job finishes (no mid-job kills).
    """

    def __init__(self, concurrency: int = 1, redis_url: str | None = None) -> None:
        """
        Args:
            concurrency: Reserved for future thread-pool expansion. Currently
                the worker processes one job at a time.
            redis_url: Override Redis URL (default: REDIS_URL env var).
        """
        self.concurrency = concurrency
        self._redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis: Any = None
        self._dlq = DeadLetterQueue(redis_url=self._redis_url)
        self._running = False
        self._shutdown_requested = False
        self._hostname = socket.gethostname()

    # ------------------------------------------------------------------
    # Redis helpers
    # ------------------------------------------------------------------

    def _get_redis(self) -> Any | None:
        """Lazy synchronous Redis connection. Returns None on failure."""
        if self._redis is not None:
            try:
                self._redis.ping()
                return self._redis
            except Exception:
                self._redis = None

        try:
            import redis as sync_redis

            self._redis = sync_redis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
                retry_on_timeout=True,
            )
            self._redis.ping()
            logger.info("EliteStudioWorker: connected to Redis")
            return self._redis
        except Exception as exc:
            logger.warning("EliteStudioWorker: Redis unavailable: %s", exc)
            return None

    def _store_result(self, result: EliteStudioJobResult) -> None:
        """Persist result JSON and publish event. Logs on failure."""
        r = self._get_redis()
        if r is None:
            logger.warning("EliteStudioWorker._store_result: Redis unavailable, result not stored")
            return
        try:
            key = f"{_RESULT_KEY_PREFIX}{result.job_id}"
            r.setex(key, _RESULT_TTL_SECONDS, result.model_dump_json())
            event = json.dumps(
                {"event": "job.completed", "job_id": result.job_id, "status": result.status}
            )
            r.publish(_EVENT_CHANNEL, event)
            logger.info(
                "EliteStudioWorker: stored result for %s (status=%s)", result.job_id, result.status
            )
        except Exception as exc:
            logger.warning("EliteStudioWorker._store_result: failed: %s", exc)

    # ------------------------------------------------------------------
    # Job processing
    # ------------------------------------------------------------------

    def process_job(self, job_id: str, job_data: EliteStudioJobData) -> None:
        """Run the Elite Studio pipeline for a single job and store the result.

        Handles all exceptions internally: on failure, moves the job to the DLQ
        and stores an error result. Never raises — callers (including _handle_task
        and tests) always get clean completion.

        Args:
            job_id: The unique job identifier.
            job_data: Deserialized job payload.
        """
        logger.info(
            "EliteStudioWorker: starting job %s (sku=%s, view=%s)",
            job_id,
            job_data.sku,
            job_data.view,
        )
        start_ts = time.monotonic()

        try:
            config = _get_graph_config(
                enable_compositor=job_data.enable_compositor,
                max_retries=job_data.max_retries,
            )
            production_result = run_single(sku=job_data.sku, view=job_data.view, config=config)
            elapsed = time.monotonic() - start_ts

            status = "success" if production_result.status == "success" else "error"
            if production_result.status == "skipped":
                status = "skipped"

            stage_timings: dict[str, float] = {}
            if production_result.quality and hasattr(production_result, "stage_timings"):
                stage_timings = getattr(production_result, "stage_timings", {})

            result = EliteStudioJobResult(
                job_id=job_id,
                sku=job_data.sku,
                status=status,
                output_path=production_result.output_path or "",
                error=production_result.error or "",
                completed_at=datetime.now(UTC).isoformat(),
                stage_timings=stage_timings,
                cost_usd=0.0,
            )
            logger.info(
                "EliteStudioWorker: job %s finished in %.1fs (status=%s)", job_id, elapsed, status
            )
            self._store_result(result)

        except Exception as exc:
            logger.error("EliteStudioWorker: job %s failed: %s", job_id, exc, exc_info=True)
            self._dlq.move_to_dlq(
                job_id=job_id,
                error=str(exc),
                original_data=job_data.model_dump(),
            )
            error_result = EliteStudioJobResult(
                job_id=job_id,
                sku=job_data.sku,
                status="error",
                error=str(exc),
                completed_at=datetime.now(UTC).isoformat(),
            )
            self._store_result(error_result)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run_forever(self) -> None:
        """Main blocking worker loop.

        Polls the priority queue, acquires atomic locks, processes jobs,
        and handles SIGTERM for clean shutdown.
        """
        self._running = True
        self._shutdown_requested = False
        self._register_signal_handlers()

        logger.info(
            "EliteStudioWorker: starting (host=%s, concurrency=%d)",
            self._hostname,
            self.concurrency,
        )

        while self._running and not self._shutdown_requested:
            r = self._get_redis()
            if r is None:
                logger.warning(
                    "EliteStudioWorker: no Redis, retrying in %ds", int(_ERROR_BACKOFF_SECONDS)
                )
                time.sleep(_ERROR_BACKOFF_SECONDS)
                continue

            try:
                # Pop highest priority job (returns [(member, score)] or [])
                popped = r.zpopmax(_QUEUE_NAME, count=1)
                if not popped:
                    time.sleep(_POLL_INTERVAL_SECONDS)
                    continue

                task_id, _priority = popped[0]

                # Atomic lock: prevent duplicate processing across workers
                lock_key = f"{_LOCK_PREFIX}{task_id}"
                acquired = r.set(lock_key, self._hostname, ex=_LOCK_TTL_SECONDS, nx=True)
                if not acquired:
                    logger.warning("EliteStudioWorker: job %s already locked, skipping", task_id)
                    continue

                try:
                    self._handle_task(r, task_id)
                finally:
                    try:
                        r.delete(lock_key)
                    except Exception:
                        pass

            except Exception as exc:
                logger.error("EliteStudioWorker: loop error: %s", exc, exc_info=True)
                time.sleep(_ERROR_BACKOFF_SECONDS)

        logger.info("EliteStudioWorker: shutdown complete")
        self._running = False

    def _handle_task(self, r: Any, task_id: str) -> None:
        """Fetch task metadata, dispatch to process_job, handle exceptions."""
        from agent_sdk.task_queue import QUEUE_PREFIX

        task_key = f"{QUEUE_PREFIX}{task_id}"
        raw = r.get(task_key)
        if not raw:
            logger.warning("EliteStudioWorker: task metadata not found for %s", task_id)
            return

        task_meta: dict[str, Any] = json.loads(raw)
        payload: dict[str, Any] = task_meta.get("data", task_meta)
        job_id: str = payload.get("job_id", task_id)

        try:
            job_data = EliteStudioJobData.model_validate(payload)
        except Exception as exc:
            logger.error("EliteStudioWorker: invalid payload for %s: %s", job_id, exc)
            self._dlq.move_to_dlq(job_id=job_id, error=str(exc), original_data=payload)
            return

        # process_job handles all pipeline exceptions internally
        self.process_job(job_id, job_data)

    # ------------------------------------------------------------------
    # Signal handling
    # ------------------------------------------------------------------

    def _register_signal_handlers(self) -> None:
        """Register SIGTERM/SIGINT handlers for graceful shutdown."""

        def _handle_signal(signum: int, frame: Any) -> None:
            logger.info(
                "EliteStudioWorker: received signal %d, finishing current job then exiting", signum
            )
            self._shutdown_requested = True

        signal.signal(signal.SIGTERM, _handle_signal)
        signal.signal(signal.SIGINT, _handle_signal)
