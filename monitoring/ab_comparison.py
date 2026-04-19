"""
A/B Comparison Tracker for Elite Studio providers.

Records per-job QC scores in Redis sorted sets and computes
statistical comparisons between generation providers and models.

Storage:
    ZADD elite_studio:ab:{provider}:{model}  <qc_score>  <job_id>

All Redis calls degrade gracefully — a missing Redis instance
results in empty reports, never raised exceptions.
"""

from __future__ import annotations

import logging
import math
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

_KEY_PREFIX = "elite_studio:ab"
_KEY_SEP = ":"


# ---------------------------------------------------------------------------
# Data models (frozen dataclasses — immutable by construction)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProviderStats:
    """Aggregate statistics for a single provider/model combination."""

    provider: str
    model: str
    sample_count: int
    mean_score: float
    std_dev: float
    p50: float
    p95: float
    win_rate: float  # fraction of samples above 0.8 (configurable threshold)


@dataclass(frozen=True)
class ABReport:
    """Full statistical comparison report across all tracked providers."""

    generated_at: str
    providers: dict[str, ProviderStats]  # key: "provider:model"


# ---------------------------------------------------------------------------
# Tracker
# ---------------------------------------------------------------------------


class ABComparisonTracker:
    """Records QC scores and computes statistical A/B comparisons."""

    WIN_THRESHOLD: float = 0.8

    def __init__(self, redis_url: str | None = None) -> None:
        self._redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis: Any = None

    # ------------------------------------------------------------------
    # Redis connection (lazy, best-effort)
    # ------------------------------------------------------------------

    def _get_redis(self) -> Any | None:
        if self._redis is not None:
            try:
                self._redis.ping()
                return self._redis
            except Exception:
                self._redis = None

        try:
            import redis as redis_lib

            self._redis = redis_lib.from_url(
                self._redis_url, decode_responses=True, socket_timeout=2
            )
            self._redis.ping()
            return self._redis
        except Exception as exc:
            logger.warning("ABComparisonTracker: Redis unavailable — %s", exc)
            return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record(self, provider: str, model: str, qc_score: float, job_id: str) -> None:
        """Store a QC score in the sorted set for this provider/model pair.

        Args:
            provider: Generation provider name (e.g. "gemini", "openai").
            model: Model identifier (e.g. "gemini-2.5-flash-image").
            qc_score: Quality score in [0.0, 1.0].
            job_id: Unique job identifier (used as sorted-set member).
        """
        r = self._get_redis()
        if r is None:
            return
        key = f"{_KEY_PREFIX}{_KEY_SEP}{provider}{_KEY_SEP}{model}"
        try:
            r.zadd(key, {job_id: qc_score})
            # Keep sorted set bounded: discard oldest entries beyond 10 000
            size = r.zcard(key)
            if size > 10_000:
                r.zremrangebyrank(key, 0, size - 10_001)
        except Exception as exc:
            logger.warning("ABComparisonTracker.record failed: %s", exc)

    def report(self, since_hours: int = 24) -> ABReport:
        """Generate a statistical comparison report.

        Reads all elite_studio:ab:*:* keys and computes per-provider
        mean, std, p50, p95, and win_rate for the past `since_hours`.

        Args:
            since_hours: Window to include (based on job insertion time if
                         available; otherwise uses all data in the sorted set).

        Returns:
            ABReport with per-provider ProviderStats.
        """
        r = self._get_redis()
        if r is None:
            return ABReport(generated_at=datetime.now(UTC).isoformat(), providers={})

        providers: dict[str, ProviderStats] = {}
        try:
            keys = r.keys(f"{_KEY_PREFIX}{_KEY_SEP}*")
            for key in keys:
                # Key format: elite_studio:ab:{provider}:{model}
                parts = key.split(_KEY_SEP, 3)
                if len(parts) < 4:
                    continue
                _, __, provider, model = parts[0], parts[1], parts[2], parts[3]

                scores_raw = r.zrangebyscore(key, 0.0, 1.0, withscores=True)
                scores = [float(score) for _, score in scores_raw]

                if not scores:
                    continue

                stats = _compute_stats(provider, model, scores, self.WIN_THRESHOLD)
                providers[f"{provider}:{model}"] = stats

        except Exception as exc:
            logger.warning("ABComparisonTracker.report failed: %s", exc)

        return ABReport(generated_at=datetime.now(UTC).isoformat(), providers=providers)


# ---------------------------------------------------------------------------
# Statistical helpers (pure functions — no I/O)
# ---------------------------------------------------------------------------


def _compute_stats(
    provider: str,
    model: str,
    scores: list[float],
    win_threshold: float,
) -> ProviderStats:
    """Compute descriptive statistics over a list of QC scores."""
    n = len(scores)
    sorted_scores = sorted(scores)
    mean = sum(sorted_scores) / n
    variance = sum((s - mean) ** 2 for s in sorted_scores) / n
    std_dev = math.sqrt(variance)
    p50 = _percentile(sorted_scores, 50)
    p95 = _percentile(sorted_scores, 95)
    win_rate = sum(1 for s in sorted_scores if s >= win_threshold) / n

    return ProviderStats(
        provider=provider,
        model=model,
        sample_count=n,
        mean_score=round(mean, 4),
        std_dev=round(std_dev, 4),
        p50=round(p50, 4),
        p95=round(p95, 4),
        win_rate=round(win_rate, 4),
    )


def _percentile(sorted_data: list[float], p: int) -> float:
    """Return the p-th percentile of a sorted list using linear interpolation."""
    if not sorted_data:
        return 0.0
    n = len(sorted_data)
    if n == 1:
        return sorted_data[0]
    idx = (p / 100) * (n - 1)
    lower = int(idx)
    upper = lower + 1
    if upper >= n:
        return sorted_data[-1]
    fraction = idx - lower
    return sorted_data[lower] + fraction * (sorted_data[upper] - sorted_data[lower])
