"""
Dead Letter Queue (DLQ) for failed Elite Studio jobs.

Failed jobs are pushed to a Redis list keyed ``elite_studio:dlq``.
Each entry is a JSON object containing the original job payload and
the failure reason. The DLQ supports listing, retry (re-enqueue),
and purge (remove entries older than N hours).

Degrades gracefully when Redis is unavailable.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

_DLQ_KEY = "elite_studio:dlq"
_DLQ_TTL_SECONDS = 7 * 24 * 3600  # 7 days default retention on individual entries


class DeadLetterQueue:
    """Manages failed Elite Studio jobs for inspection and replay.

    Storage: Redis list ``elite_studio:dlq`` (LPUSH on failure, LRANGE to list).
    Each entry is a JSON object:
        {
            "job_id": str,
            "sku": str,
            "error": str,
            "failed_at": ISO datetime string,
            "original_data": dict  # full EliteStudioJobData dump
        }
    """

    def __init__(self, redis_url: str | None = None) -> None:
        self._redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis: Any = None

    def _get_redis(self) -> Any | None:
        """Lazy-connect synchronously. Returns None on failure."""
        if self._redis is not None:
            return self._redis
        try:
            import redis as sync_redis

            self._redis = sync_redis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_timeout=3.0,
                socket_connect_timeout=3.0,
            )
            self._redis.ping()
            return self._redis
        except Exception as exc:
            logger.warning("DeadLetterQueue: Redis unavailable: %s", exc)
            return None

    def move_to_dlq(self, job_id: str, error: str, original_data: dict[str, Any] | None = None) -> None:
        """Push a failed job onto the DLQ.

        Args:
            job_id: The job identifier.
            error: Human-readable error description.
            original_data: Original EliteStudioJobData dict (stored for retry).
        """
        r = self._get_redis()
        if r is None:
            logger.warning("DeadLetterQueue.move_to_dlq: Redis unavailable, job %s lost from DLQ", job_id)
            return

        entry = {
            "job_id": job_id,
            "sku": (original_data or {}).get("sku", ""),
            "error": error,
            "failed_at": datetime.now(UTC).isoformat(),
            "original_data": original_data or {},
        }
        try:
            r.lpush(_DLQ_KEY, json.dumps(entry))
            logger.info("DeadLetterQueue: moved job %s to DLQ (error: %s)", job_id, error[:120])
        except Exception as exc:
            logger.warning("DeadLetterQueue.move_to_dlq: write failed for %s: %s", job_id, exc)

    def list_failed(self) -> list[dict[str, Any]]:
        """Return all entries currently in the DLQ (newest first).

        Returns:
            List of DLQ entry dicts. Empty list if Redis unavailable or DLQ empty.
        """
        r = self._get_redis()
        if r is None:
            return []

        try:
            raw_entries = r.lrange(_DLQ_KEY, 0, -1)
            result: list[dict[str, Any]] = []
            for raw in raw_entries:
                try:
                    result.append(json.loads(raw))
                except json.JSONDecodeError as exc:
                    logger.warning("DeadLetterQueue.list_failed: corrupt entry skipped: %s", exc)
            return result
        except Exception as exc:
            logger.warning("DeadLetterQueue.list_failed: %s", exc)
            return []

    def retry(self, job_id: str) -> str:
        """Re-enqueue a specific failed job from the DLQ.

        Finds the first DLQ entry matching job_id, removes it from the DLQ,
        and enqueues a new job (new job_id) via the producer.

        Args:
            job_id: The job_id to retry.

        Returns:
            New job_id for the re-queued job.

        Raises:
            KeyError: If job_id is not found in the DLQ.
            RuntimeError: If the re-enqueue fails.
        """
        r = self._get_redis()
        if r is None:
            raise RuntimeError("DeadLetterQueue.retry: Redis unavailable")

        # Find and remove the entry
        try:
            raw_entries = r.lrange(_DLQ_KEY, 0, -1)
        except Exception as exc:
            raise RuntimeError(f"DeadLetterQueue.retry: cannot read DLQ: {exc}") from exc

        target_raw: str | None = None
        target_entry: dict[str, Any] | None = None

        for raw in raw_entries:
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if entry.get("job_id") == job_id:
                target_raw = raw
                target_entry = entry
                break

        if target_entry is None:
            raise KeyError(f"job_id '{job_id}' not found in DLQ")

        # Remove the matched entry from the list (LREM first occurrence)
        try:
            r.lrem(_DLQ_KEY, 1, target_raw)
        except Exception as exc:
            raise RuntimeError(f"DeadLetterQueue.retry: cannot remove from DLQ: {exc}") from exc

        # Re-enqueue via producer (imported here to allow patching in tests)
        from skyyrose.elite_studio.queue import producer as _producer

        original = target_entry.get("original_data", {})
        sku = original.get("sku") or target_entry.get("sku")
        if not sku:
            raise RuntimeError(f"DeadLetterQueue.retry: cannot determine SKU for job {job_id}")

        new_job_id = _producer.enqueue_produce(
            sku=sku,
            view=original.get("view", "front"),
            priority=original.get("priority", 5),
            enable_compositor=original.get("enable_compositor", False),
            max_retries=original.get("max_retries", 2),
        )
        logger.info("DeadLetterQueue: retried job %s as new job %s", job_id, new_job_id)
        return new_job_id

    def purge(self, older_than_hours: int = 72) -> int:
        """Remove DLQ entries older than N hours.

        Args:
            older_than_hours: Entries with failed_at older than this are removed.

        Returns:
            Number of entries purged.
        """
        r = self._get_redis()
        if r is None:
            logger.warning("DeadLetterQueue.purge: Redis unavailable")
            return 0

        try:
            raw_entries = r.lrange(_DLQ_KEY, 0, -1)
        except Exception as exc:
            logger.warning("DeadLetterQueue.purge: cannot read DLQ: %s", exc)
            return 0

        cutoff = datetime.now(UTC) - timedelta(hours=older_than_hours)
        purged = 0

        for raw in raw_entries:
            try:
                entry = json.loads(raw)
                failed_at_str = entry.get("failed_at", "")
                if not failed_at_str:
                    continue
                failed_at = datetime.fromisoformat(failed_at_str)
                # Normalize to UTC-aware for comparison
                if failed_at.tzinfo is None:
                    failed_at = failed_at.replace(tzinfo=UTC)
                if failed_at < cutoff:
                    removed = r.lrem(_DLQ_KEY, 1, raw)
                    if removed:
                        purged += 1
            except (json.JSONDecodeError, ValueError):
                continue
            except Exception as exc:
                logger.warning("DeadLetterQueue.purge: error processing entry: %s", exc)

        if purged:
            logger.info("DeadLetterQueue.purge: removed %d entries older than %dh", purged, older_than_hours)
        return purged
