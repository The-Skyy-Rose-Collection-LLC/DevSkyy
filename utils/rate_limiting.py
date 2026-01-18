"""
Token Bucket Rate Limiting for DevSkyy MCP Server
===================================================

Proactive rate limiting to prevent API abuse and ensure fair usage.
Following Context7 best practices for httpx rate limiting.
"""

import asyncio
import time
from dataclasses import dataclass

from logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class TokenBucket:
    """
    Token bucket for rate limiting.

    Tokens are added at a constant rate. Each request consumes a token.
    If no tokens available, request is rate-limited.
    """

    capacity: int  # Maximum tokens in bucket
    refill_rate: float  # Tokens per second
    tokens: float  # Current token count
    last_refill: float  # Last refill timestamp

    def consume(self, tokens: int = 1) -> bool:
        """
        Attempt to consume tokens from the bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens consumed successfully, False if rate-limited
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    def _refill(self) -> None:
        """Refill tokens based on time elapsed."""
        now = time.time()
        elapsed = now - self.last_refill

        # Add tokens based on refill rate
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

    def get_retry_after(self) -> float:
        """
        Get seconds until next token available.

        Returns:
            Seconds to wait before retry
        """
        self._refill()

        if self.tokens >= 1:
            return 0.0

        tokens_needed = 1 - self.tokens
        return tokens_needed / self.refill_rate


class RateLimiter:
    """
    Multi-user token bucket rate limiter.

    Maintains separate buckets for each user/endpoint combination.
    """

    def __init__(
        self,
        requests_per_second: float = 10.0,
        burst_size: int = 20,
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Sustained request rate
            burst_size: Maximum burst capacity
        """
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.buckets: dict[str, TokenBucket] = {}
        self._lock = asyncio.Lock()

    def _get_bucket(self, key: str) -> TokenBucket:
        """
        Get or create token bucket for key.

        Args:
            key: Unique identifier (user_id, endpoint, etc.)

        Returns:
            Token bucket for this key
        """
        if key not in self.buckets:
            self.buckets[key] = TokenBucket(
                capacity=self.burst_size,
                refill_rate=self.requests_per_second,
                tokens=self.burst_size,  # Start with full bucket
                last_refill=time.time(),
            )

        return self.buckets[key]

    async def check_rate_limit(
        self,
        key: str,
        tokens: int = 1,
    ) -> tuple[bool, float | None]:
        """
        Check if request is allowed under rate limit.

        Args:
            key: Unique identifier for rate limiting
            tokens: Number of tokens to consume

        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        async with self._lock:
            bucket = self._get_bucket(key)

            if bucket.consume(tokens):
                # Request allowed
                logger.debug(
                    "rate_limit_allowed",
                    key=key,
                    tokens_remaining=bucket.tokens,
                )
                return True, None

            # Rate limited
            retry_after = bucket.get_retry_after()

            logger.warning(
                "rate_limit_exceeded",
                key=key,
                retry_after=retry_after,
            )

            return False, retry_after

    async def wait_if_needed(self, key: str, tokens: int = 1) -> None:
        """
        Wait if rate limited, then consume tokens.

        Args:
            key: Unique identifier for rate limiting
            tokens: Number of tokens to consume
        """
        while True:
            allowed, retry_after = await self.check_rate_limit(key, tokens)

            if allowed:
                return

            if retry_after:
                logger.info(
                    "rate_limit_waiting",
                    key=key,
                    retry_after=retry_after,
                )
                await asyncio.sleep(retry_after)

    def reset(self, key: str | None = None) -> None:
        """
        Reset rate limits.

        Args:
            key: Specific key to reset, or None to reset all
        """
        if key:
            self.buckets.pop(key, None)
        else:
            self.buckets.clear()

    def get_stats(self) -> dict[str, dict]:
        """
        Get rate limiting statistics.

        Returns:
            Dictionary of key -> stats
        """
        stats = {}

        for key, bucket in self.buckets.items():
            bucket._refill()
            stats[key] = {
                "tokens_available": bucket.tokens,
                "capacity": bucket.capacity,
                "refill_rate": bucket.refill_rate,
                "utilization": 1 - (bucket.tokens / bucket.capacity),
            }

        return stats


# Global rate limiter instance
# 10 requests/second sustained, 20 burst
_global_rate_limiter = RateLimiter(
    requests_per_second=10.0,
    burst_size=20,
)


async def check_rate_limit(
    user_id: str,
    endpoint: str,
    tokens: int = 1,
) -> tuple[bool, float | None]:
    """
    Check rate limit for user/endpoint combination.

    Args:
        user_id: User identifier
        endpoint: API endpoint
        tokens: Tokens to consume

        Returns:
        Tuple of (allowed, retry_after_seconds)
    """
    key = f"{user_id}:{endpoint}"
    return await _global_rate_limiter.check_rate_limit(key, tokens)


async def wait_for_rate_limit(
    user_id: str,
    endpoint: str,
    tokens: int = 1,
) -> None:
    """
    Wait if rate limited, then proceed.

    Args:
        user_id: User identifier
        endpoint: API endpoint
        tokens: Tokens to consume
    """
    key = f"{user_id}:{endpoint}"
    await _global_rate_limiter.wait_if_needed(key, tokens)


def get_rate_limit_stats() -> dict[str, dict]:
    """Get global rate limiting statistics."""
    return _global_rate_limiter.get_stats()


def reset_rate_limits(user_id: str | None = None, endpoint: str | None = None) -> None:
    """
    Reset rate limits.

    Args:
        user_id: Specific user to reset
        endpoint: Specific endpoint to reset
    """
    if user_id and endpoint:
        key = f"{user_id}:{endpoint}"
        _global_rate_limiter.reset(key)
    elif user_id:
        # Reset all endpoints for this user
        keys = [k for k in _global_rate_limiter.buckets if k.startswith(f"{user_id}:")]
        for key in keys:
            _global_rate_limiter.reset(key)
    elif endpoint:
        # Reset this endpoint for all users
        keys = [k for k in _global_rate_limiter.buckets if k.endswith(f":{endpoint}")]
        for key in keys:
            _global_rate_limiter.reset(key)
    else:
        # Reset everything
        _global_rate_limiter.reset()
