"""
Prompt History — tracks prompt-to-result quality correlation.

Records which enhanced prompts produced the best outputs so the system
learns over time. High-quality patterns get reinforced; failure patterns
get flagged for template revision.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class PromptHistory:
    """Redis-backed prompt quality tracking.

    Graceful degradation: all methods return empty results if Redis is unavailable.
    """

    HISTORY_PREFIX = "elite_studio:prompt_history"
    MAX_ENTRIES_PER_INTENT = 500

    def __init__(self, redis_url: str | None = None) -> None:
        self._redis = self._connect(redis_url)

    def _connect(self, redis_url: str | None) -> Any:
        """Connect to Redis. Returns None on failure."""
        try:
            import redis as redis_lib

            url = redis_url or "redis://localhost:6379/0"
            client = redis_lib.Redis.from_url(url, decode_responses=True)
            client.ping()
            return client
        except Exception:
            logger.warning(
                "PromptHistory: Redis unavailable — history tracking disabled"
            )
            return None

    def record(
        self,
        enhanced_prompt: str,
        intent: str,
        result_quality: float,
        job_id: str,
        context_added: tuple[str, ...] | list[str] = (),
        template_used: str = "",
    ) -> None:
        """Record a prompt-to-quality correlation.

        Args:
            enhanced_prompt: The enhanced prompt that was used.
            intent: Creative intent type.
            result_quality: Quality score 0.0-1.0 from QC.
            job_id: The job ID for traceability.
            context_added: What context was injected during enhancement.
            template_used: Which template shaped the prompt.
        """
        if self._redis is None:
            return

        try:
            key = f"{self.HISTORY_PREFIX}:{intent}"
            entry = json.dumps({
                "prompt": enhanced_prompt[:500],  # truncate for storage efficiency
                "quality": round(result_quality, 3),
                "job_id": job_id,
                "context_added": list(context_added),
                "template_used": template_used,
                "recorded_at": time.time(),
            })

            # Store with quality as score (higher = better)
            self._redis.zadd(key, {entry: result_quality})

            # Trim to max entries (keep highest quality)
            count = self._redis.zcard(key)
            if count > self.MAX_ENTRIES_PER_INTENT:
                self._redis.zremrangebyrank(key, 0, count - self.MAX_ENTRIES_PER_INTENT - 1)

        except Exception:
            logger.warning("PromptHistory: record failed", exc_info=True)

    def get_best_patterns(self, intent: str, n: int = 10) -> list[dict]:
        """Return top N prompt patterns by result quality for an intent.

        Returns list of dicts with: prompt, quality, job_id, context_added,
        template_used, recorded_at.
        """
        if self._redis is None:
            return []

        try:
            key = f"{self.HISTORY_PREFIX}:{intent}"
            # ZREVRANGE: highest scores first
            entries = self._redis.zrevrange(key, 0, n - 1, withscores=True)
            results = []
            for entry_json, score in entries:
                data = json.loads(entry_json)
                data["score"] = round(score, 3)
                results.append(data)
            return results
        except Exception:
            logger.warning("PromptHistory: get_best_patterns failed", exc_info=True)
            return []

    def get_failure_patterns(self, intent: str, n: int = 5) -> list[dict]:
        """Return patterns that consistently produce poor results.

        Returns entries with quality < 0.4 (bottom performers).
        """
        if self._redis is None:
            return []

        try:
            key = f"{self.HISTORY_PREFIX}:{intent}"
            # ZRANGEBYSCORE: entries with score < 0.4
            entries = self._redis.zrangebyscore(key, "-inf", "0.4", start=0, num=n)
            results = []
            for entry_json in entries:
                data = json.loads(entry_json)
                results.append(data)
            return results
        except Exception:
            logger.warning("PromptHistory: get_failure_patterns failed", exc_info=True)
            return []

    def get_average_quality(self, intent: str) -> float:
        """Return average result quality for an intent."""
        if self._redis is None:
            return 0.0

        try:
            key = f"{self.HISTORY_PREFIX}:{intent}"
            entries = self._redis.zrange(key, 0, -1, withscores=True)
            if not entries:
                return 0.0
            total = sum(score for _, score in entries)
            return round(total / len(entries), 3)
        except Exception:
            logger.warning("PromptHistory: get_average_quality failed", exc_info=True)
            return 0.0

    def get_entry_count(self, intent: str) -> int:
        """Return number of recorded entries for an intent."""
        if self._redis is None:
            return 0

        try:
            key = f"{self.HISTORY_PREFIX}:{intent}"
            return self._redis.zcard(key) or 0
        except Exception:
            return 0

    def clear_intent(self, intent: str) -> int:
        """Clear all history for an intent. Returns number of entries removed."""
        if self._redis is None:
            return 0

        try:
            key = f"{self.HISTORY_PREFIX}:{intent}"
            count = self._redis.zcard(key) or 0
            self._redis.delete(key)
            return count
        except Exception:
            logger.warning("PromptHistory: clear_intent failed", exc_info=True)
            return 0
