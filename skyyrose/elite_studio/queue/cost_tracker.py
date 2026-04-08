"""
Cost tracker for Elite Studio API usage.

Records token usage and estimated cost per job in Redis hashes.
Degrades gracefully when Redis is unavailable (logs warning, no exception).
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# Pricing constants (USD per 1K tokens)
PRICING_PER_1K: dict[str, float] = {
    "gemini": 0.000075,   # Gemini Flash
    "openai": 0.005,      # GPT-4o input
    "anthropic": 0.003,   # Claude Sonnet input
}

# Redis key patterns
_COST_KEY_PREFIX = "elite_studio:costs:"
_TOTAL_COST_SORTED_SET = "elite_studio:costs:timeline"

# TTL for individual job cost records: 7 days
_COST_TTL_SECONDS = 604_800


class CostTracker:
    """Records API token usage and estimated cost per job.

    Storage layout (per job):
        HASH  elite_studio:costs:{job_id}
              gemini_tokens    <int>
              openai_tokens    <int>
              anthropic_tokens <int>
              total_usd        <float>

    Timeline (for get_total_cost):
        ZADD  elite_studio:costs:timeline  <unix_ts> <json_cost_entry>
    """

    def __init__(self, redis_url: str | None = None) -> None:
        self._redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis: Any = None

    def _get_redis(self) -> Any | None:
        """Lazy-connect to Redis synchronously. Returns None on failure."""
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
            logger.warning("CostTracker: Redis unavailable — cost tracking degraded: %s", exc)
            return None

    def record(self, job_id: str, provider: str, tokens: int, cost_usd: float) -> None:
        """Record token usage and cost for a provider call in a job.

        Args:
            job_id: The job this cost belongs to.
            provider: One of "gemini", "openai", "anthropic".
            tokens: Number of tokens consumed.
            cost_usd: Estimated cost in USD.
        """
        r = self._get_redis()
        if r is None:
            logger.warning("CostTracker.record: Redis unavailable, skipping cost record")
            return

        try:
            key = f"{_COST_KEY_PREFIX}{job_id}"
            token_field = f"{provider}_tokens"

            pipe = r.pipeline()
            pipe.hincrbyfloat(key, token_field, tokens)
            pipe.hincrbyfloat(key, "total_usd", cost_usd)
            pipe.expire(key, _COST_TTL_SECONDS)

            # Record in timeline for aggregation
            timeline_entry = f"{job_id}:{provider}:{cost_usd:.6f}"
            score = datetime.now(UTC).timestamp()
            pipe.zadd(_TOTAL_COST_SORTED_SET, {timeline_entry: score})
            pipe.execute()

            logger.debug(
                "CostTracker: job=%s provider=%s tokens=%d cost=$%.6f",
                job_id, provider, tokens, cost_usd,
            )
        except Exception as exc:
            logger.warning("CostTracker.record: failed to write cost data: %s", exc)

    def get_job_cost(self, job_id: str) -> float:
        """Return total USD cost recorded for a job.

        Returns 0.0 if Redis is unavailable or job not found.
        """
        r = self._get_redis()
        if r is None:
            return 0.0

        try:
            key = f"{_COST_KEY_PREFIX}{job_id}"
            value = r.hget(key, "total_usd")
            return float(value) if value is not None else 0.0
        except Exception as exc:
            logger.warning("CostTracker.get_job_cost: %s", exc)
            return 0.0

    def get_total_cost(self, since_hours: int = 24) -> float:
        """Return total USD cost across all jobs in the last N hours.

        Args:
            since_hours: Look-back window in hours (default 24).

        Returns:
            Summed cost in USD, or 0.0 on Redis failure.
        """
        r = self._get_redis()
        if r is None:
            return 0.0

        try:
            cutoff = (datetime.now(UTC) - timedelta(hours=since_hours)).timestamp()
            entries = r.zrangebyscore(_TOTAL_COST_SORTED_SET, cutoff, "+inf")
            total = 0.0
            for entry in entries:
                # Format: "job_id:provider:cost_usd"
                parts = entry.rsplit(":", 1)
                if len(parts) == 2:
                    try:
                        total += float(parts[1])
                    except ValueError:
                        pass
            return round(total, 6)
        except Exception as exc:
            logger.warning("CostTracker.get_total_cost: %s", exc)
            return 0.0

    @staticmethod
    def estimate_cost(provider: str, tokens: int) -> float:
        """Estimate cost for a provider call without recording it.

        Args:
            provider: Provider name (gemini, openai, anthropic).
            tokens: Token count.

        Returns:
            Estimated cost in USD.
        """
        rate = PRICING_PER_1K.get(provider, 0.0)
        return round(rate * tokens / 1000, 6)
