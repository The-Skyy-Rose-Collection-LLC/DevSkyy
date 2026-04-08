"""
Provider rate limiter using Redis sliding window (sorted sets).

Implements a token bucket / sliding window rate limiter per AI provider.
Degrades gracefully when Redis is unavailable — returns True (allow) so
the pipeline can proceed without blocking.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Raised when a provider rate limit cannot be acquired within the timeout."""

    def __init__(self, provider: str, timeout: float) -> None:
        super().__init__(f"Rate limit not acquired for '{provider}' within {timeout:.1f}s")
        self.provider = provider
        self.timeout = timeout


class ProviderRateLimiter:
    """Sliding window rate limiter per AI provider using Redis sorted sets.

    Limits (requests/minute):
        gemini:    60
        openai:    500
        anthropic: 50

    The sliding window is maintained as a Redis sorted set where each member
    is a unique request token and the score is the unix timestamp of the request.
    Expired entries (older than 60s) are pruned on each acquire call.

    Degrades gracefully: if Redis is unavailable, acquire() returns True.
    """

    LIMITS: dict[str, int] = {
        "gemini": 60,
        "openai": 500,
        "anthropic": 50,
    }

    _KEY_PREFIX = "elite_studio:ratelimit:"
    _WINDOW_SECONDS = 60

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
            logger.warning("ProviderRateLimiter: Redis unavailable, rate limiting disabled: %s", exc)
            return None

    def acquire(self, provider: str, timeout: float = 30.0) -> bool:
        """Attempt to acquire a rate limit slot for a provider.

        Uses a sliding window: prunes requests older than 60s, then checks
        if the current count is below the limit.

        Args:
            provider: Provider name (gemini, openai, anthropic).
            timeout: Maximum seconds to wait for a slot.

        Returns:
            True when a slot is acquired.

        Raises:
            RateLimitExceeded: If no slot is available within timeout.
        """
        r = self._get_redis()
        if r is None:
            # Degrade gracefully — allow the call
            return True

        limit = self.LIMITS.get(provider)
        if limit is None:
            logger.warning("ProviderRateLimiter: unknown provider '%s', allowing", provider)
            return True

        key = f"{self._KEY_PREFIX}{provider}"
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            now = datetime.now(UTC).timestamp()
            window_start = now - self._WINDOW_SECONDS
            request_token = f"{now:.6f}"

            try:
                pipe = r.pipeline()
                # Remove expired entries from the sliding window
                pipe.zremrangebyscore(key, "-inf", window_start)
                # Count current requests in window
                pipe.zcard(key)
                _, current_count = pipe.execute()

                if current_count < limit:
                    # Add our request token with current timestamp as score
                    r.zadd(key, {request_token: now})
                    r.expire(key, self._WINDOW_SECONDS + 5)
                    logger.debug(
                        "RateLimiter: acquired slot for %s (%d/%d)", provider, current_count + 1, limit
                    )
                    return True

                # Window is full — wait briefly and retry
                wait_remaining = deadline - time.monotonic()
                if wait_remaining <= 0:
                    break
                sleep_time = min(0.5, wait_remaining)
                logger.debug(
                    "RateLimiter: %s at limit (%d/%d), waiting %.1fs", provider, current_count, limit, sleep_time
                )
                time.sleep(sleep_time)

            except Exception as exc:
                logger.warning("ProviderRateLimiter.acquire: Redis error for %s: %s", provider, exc)
                # Degrade gracefully on Redis errors
                return True

        raise RateLimitExceeded(provider=provider, timeout=timeout)

    def release(self, provider: str) -> None:
        """Release the oldest slot in the sliding window for a provider.

        In a pure sliding window, entries expire naturally after 60s.
        This method proactively removes the oldest entry to free capacity
        for callers that need to release early (e.g. on job cancellation).

        Args:
            provider: Provider name (gemini, openai, anthropic).
        """
        r = self._get_redis()
        if r is None:
            return

        key = f"{self._KEY_PREFIX}{provider}"
        try:
            # Remove the oldest (lowest score) entry — this frees one slot early
            r.zpopmin(key, count=1)
            logger.debug("RateLimiter: released one slot for %s", provider)
        except Exception as exc:
            logger.warning("ProviderRateLimiter.release: %s", exc)
