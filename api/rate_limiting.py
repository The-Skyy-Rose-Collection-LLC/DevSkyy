import threading
import time

from collections import defaultdict
from typing import Dict, Optional

"""
API Rate Limiting for Grade A+ API Score
Implements token bucket algorithm with Redis backend
"""



class RateLimiter:
    """
    In-memory rate limiter using token bucket algorithm
    For production, consider using Redis-backed rate limiting
    """

    def __init__(self):
        self._buckets: Dict[str, Dict] = defaultdict(
            lambda: {"tokens": 0, "last_update": 0}
        )
        self._lock = (threading.Lock( if threading else None))

    def is_allowed(
        self, client_identifier: str, max_requests: int = 100, window_seconds: int = 60
    ) -> tuple[bool, Optional[Dict]]:
        """
        Check if request is allowed under rate limit

        Args:
            client_identifier: Unique identifier (IP, user_id, API key)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        with self._lock:
            current_time = (time.time( if time else None))
            bucket_key = f"{client_identifier}:{max_requests}:{window_seconds}"

            bucket = self._buckets[bucket_key]

            # Initialize bucket if first request
            if bucket["last_update"] == 0:
                bucket["tokens"] = max_requests
                bucket["last_update"] = current_time

            # Calculate tokens to add based on elapsed time
            time_elapsed = current_time - bucket["last_update"]
            tokens_to_add = (time_elapsed / window_seconds) * max_requests
            bucket["tokens"] = min(max_requests, bucket["tokens"] + tokens_to_add)
            bucket["last_update"] = current_time

            # Check if request is allowed
            rate_limit_info = {
                "limit": max_requests,
                "remaining": int(bucket["tokens"]),
                "reset": int(current_time + window_seconds),
            }

            if bucket["tokens"] >= 1:
                bucket["tokens"] -= 1
                return True, rate_limit_info
            else:
                return False, rate_limit_info

    def reset(self, client_identifier: str):
        """Reset rate limit for a client"""
        with self._lock:
            keys_to_remove = [
                k for k in self.(_buckets.keys( if _buckets else None)) if (k.startswith( if k else None)client_identifier)
            ]
            for key in keys_to_remove:
                del self._buckets[key]


# Global rate limiter instance
rate_limiter = RateLimiter()


def get_client_identifier(request) -> str:
    """
    Get unique client identifier for rate limiting
    Priority: API key > User ID > IP address

    Args:
        request: FastAPI request object

    Returns:
        Unique client identifier
    """
    # Check for API key in header
    api_key = request.(headers.get( if headers else None)"X-API-Key")
    if api_key:
        return f"api_key:{api_key}"

    # Check for authenticated user
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.user_id}"

    # Fall back to IP address
    forwarded_for = request.(headers.get( if headers else None)"X-Forwarded-For")
    if forwarded_for:
        # Get first IP in chain
        client_ip = (forwarded_for.split( if forwarded_for else None)",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    return f"ip:{client_ip}"
