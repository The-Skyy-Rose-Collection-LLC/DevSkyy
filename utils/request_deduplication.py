"""
Request Deduplication for DevSkyy MCP Server
=============================================

Prevents duplicate concurrent requests to the same endpoint.
"""

import asyncio
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class PendingRequest:
    """Represents a pending request."""

    future: asyncio.Future
    started_at: datetime


class RequestDeduplicator:
    """
    Deduplicates concurrent requests.

    If multiple identical requests are made simultaneously,
    only the first is executed. Others wait for the same result.
    """

    def __init__(self, ttl_seconds: float = 60.0):
        """
        Initialize request deduplicator.

        Args:
            ttl_seconds: How long to cache request results
        """
        self.ttl_seconds = ttl_seconds
        self.pending: dict[str, PendingRequest] = {}
        self._lock = asyncio.Lock()

    def _compute_request_hash(
        self,
        endpoint: str,
        method: str,
        data: dict | None = None,
        params: dict | None = None,
    ) -> str:
        """
        Compute unique hash for request.

        Args:
            endpoint: API endpoint
            method: HTTP method
            data: Request body
            params: Query parameters

        Returns:
            Hash string
        """
        request_key = {
            "endpoint": endpoint,
            "method": method,
            "data": data or {},
            "params": params or {},
        }

        # Stable JSON serialization for consistent hashing
        json_str = json.dumps(request_key, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]

    async def deduplicate(
        self,
        endpoint: str,
        method: str,
        request_func,
        data: dict | None = None,
        params: dict | None = None,
    ) -> Any:
        """
        Deduplicate concurrent requests.

        Args:
            endpoint: API endpoint
            method: HTTP method
            request_func: Async function to call if not deduplicated
            data: Request body
            params: Query parameters

        Returns:
            Request result (from cache or fresh execution)
        """
        request_hash = self._compute_request_hash(endpoint, method, data, params)

        async with self._lock:
            # Check if request is already pending
            if request_hash in self.pending:
                pending_request = self.pending[request_hash]

                # Clean up stale requests
                age = (datetime.now() - pending_request.started_at).total_seconds()
                if age > self.ttl_seconds:
                    logger.warning(
                        "stale_pending_request",
                        request_hash=request_hash,
                        age_seconds=age,
                    )
                    del self.pending[request_hash]
                else:
                    logger.info(
                        "request_deduplicated",
                        request_hash=request_hash,
                        endpoint=endpoint,
                    )

                    # Wait for the original request to complete
                    return await pending_request.future

            # Create new pending request
            future = asyncio.Future()
            self.pending[request_hash] = PendingRequest(
                future=future,
                started_at=datetime.now(),
            )

        try:
            # Execute the request
            logger.info(
                "request_executing",
                request_hash=request_hash,
                endpoint=endpoint,
            )

            result = await request_func()

            # Mark as complete
            async with self._lock:
                if request_hash in self.pending:
                    self.pending[request_hash].future.set_result(result)
                    del self.pending[request_hash]

            return result

        except Exception as e:
            # Propagate exception to all waiting requests
            async with self._lock:
                if request_hash in self.pending:
                    self.pending[request_hash].future.set_exception(e)
                    del self.pending[request_hash]

            raise

    def clear(self) -> None:
        """Clear all pending requests."""
        self.pending.clear()

    def get_stats(self) -> dict[str, Any]:
        """
        Get deduplication statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "pending_requests": len(self.pending),
            "requests": [
                {
                    "hash": req_hash,
                    "age_seconds": (datetime.now() - req.started_at).total_seconds(),
                }
                for req_hash, req in self.pending.items()
            ],
        }


# Global deduplicator instance
_global_deduplicator = RequestDeduplicator(ttl_seconds=60.0)


async def deduplicate_request(
    endpoint: str,
    method: str,
    request_func,
    data: dict | None = None,
    params: dict | None = None,
) -> Any:
    """
    Deduplicate concurrent requests globally.

    Args:
        endpoint: API endpoint
        method: HTTP method
        request_func: Async function to execute
        data: Request body
        params: Query parameters

    Returns:
        Request result
    """
    return await _global_deduplicator.deduplicate(
        endpoint=endpoint,
        method=method,
        request_func=request_func,
        data=data,
        params=params,
    )


def get_deduplication_stats() -> dict[str, Any]:
    """Get global deduplication statistics."""
    return _global_deduplicator.get_stats()


def clear_deduplication_cache() -> None:
    """Clear global deduplication cache."""
    _global_deduplicator.clear()
