"""
Task Status Store
=================

Redis-backed task status storage with TTL for background task tracking.
Prevents memory leaks from unbounded in-memory dicts.

Features:
- Redis-backed storage with configurable TTL (default 24 hours)
- Graceful fallback to bounded in-memory LRU dict if Redis unavailable
- Thread-safe async operations
- Automatic cleanup of expired entries

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import OrderedDict
from typing import Any

from .redis_cache import RedisCache, RedisConfig

logger = logging.getLogger(__name__)


class TaskStatusStore:
    """Redis-backed task status storage with TTL.

    Provides a reliable storage mechanism for background task status with:
    - 24-hour default TTL to prevent unbounded growth
    - Graceful fallback to bounded in-memory dict if Redis unavailable
    - JSON serialization for complex status objects

    Usage:
        store = TaskStatusStore()
        await store.initialize()

        # Set task status
        await store.set_status("task-123", {"status": "processing", "progress": 50})

        # Get task status
        status = await store.get_status("task-123")

        # Update task status (partial update)
        await store.update_status("task-123", {"progress": 75})
    """

    DEFAULT_TTL = 86400  # 24 hours
    MAX_IN_MEMORY_ENTRIES = 1000  # Bounded fallback size
    KEY_PREFIX = "task_status:"

    __slots__ = (
        "_redis",
        "_ttl",
        "_fallback_cache",
        "_fallback_lock",
        "_use_fallback",
        "_initialized",
    )

    def __init__(
        self,
        redis_cache: RedisCache | None = None,
        ttl: int = DEFAULT_TTL,
    ) -> None:
        """Initialize TaskStatusStore.

        Args:
            redis_cache: Optional RedisCache instance. Creates new one if not provided.
            ttl: Time-to-live in seconds for task status entries (default: 24 hours)
        """
        self._redis = redis_cache or RedisCache(RedisConfig())
        self._ttl = ttl
        self._fallback_cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._fallback_lock = asyncio.Lock()
        self._use_fallback = False
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize the store by connecting to Redis.

        Returns:
            True if Redis connected successfully, False if using fallback
        """
        if self._initialized:
            return not self._use_fallback

        connected = await self._redis.connect()
        self._use_fallback = not connected
        self._initialized = True

        if self._use_fallback:
            logger.warning(
                "TaskStatusStore using in-memory fallback "
                f"(max {self.MAX_IN_MEMORY_ENTRIES} entries)"
            )
        else:
            logger.info(f"TaskStatusStore initialized with Redis (TTL: {self._ttl}s)")

        return connected

    def _make_key(self, task_id: str) -> str:
        """Generate Redis key for task ID."""
        return f"{self.KEY_PREFIX}{task_id}"

    async def set_status(
        self,
        task_id: str,
        status: dict[str, Any],
        ttl: int | None = None,
    ) -> bool:
        """Set task status.

        Args:
            task_id: Unique task identifier
            status: Status dictionary to store
            ttl: Optional TTL override in seconds

        Returns:
            True if status was stored successfully
        """
        if not self._initialized:
            await self.initialize()

        effective_ttl = ttl if ttl is not None else self._ttl

        if self._use_fallback:
            return await self._set_fallback(task_id, status)

        try:
            key = self._make_key(task_id)
            # Use Redis client directly for setex
            if self._redis._connected and self._redis._client:
                await self._redis._client.setex(
                    key,
                    effective_ttl,
                    json.dumps(status, default=str),
                )
                return True
            else:
                return await self._set_fallback(task_id, status)

        except Exception as e:
            logger.warning(f"Redis set_status failed, using fallback: {e}")
            return await self._set_fallback(task_id, status)

    async def _set_fallback(self, task_id: str, status: dict[str, Any]) -> bool:
        """Set status in fallback in-memory cache."""
        async with self._fallback_lock:
            # Evict oldest if at capacity
            while len(self._fallback_cache) >= self.MAX_IN_MEMORY_ENTRIES:
                self._fallback_cache.popitem(last=False)

            self._fallback_cache[task_id] = status
            # Move to end (most recent)
            self._fallback_cache.move_to_end(task_id)
            return True

    async def get_status(self, task_id: str) -> dict[str, Any] | None:
        """Get task status.

        Args:
            task_id: Unique task identifier

        Returns:
            Status dictionary if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()

        if self._use_fallback:
            return await self._get_fallback(task_id)

        try:
            key = self._make_key(task_id)
            if self._redis._connected and self._redis._client:
                data = await self._redis._client.get(key)
                if data:
                    return json.loads(data)
                return None
            else:
                return await self._get_fallback(task_id)

        except Exception as e:
            logger.warning(f"Redis get_status failed, using fallback: {e}")
            return await self._get_fallback(task_id)

    async def _get_fallback(self, task_id: str) -> dict[str, Any] | None:
        """Get status from fallback in-memory cache."""
        async with self._fallback_lock:
            status = self._fallback_cache.get(task_id)
            if status:
                # Move to end (most recently accessed)
                self._fallback_cache.move_to_end(task_id)
            return status

    async def update_status(
        self,
        task_id: str,
        updates: dict[str, Any],
        ttl: int | None = None,
    ) -> bool:
        """Update task status with partial updates.

        Merges updates into existing status. Creates new entry if not exists.

        Args:
            task_id: Unique task identifier
            updates: Dictionary of fields to update
            ttl: Optional TTL override in seconds

        Returns:
            True if status was updated successfully
        """
        current = await self.get_status(task_id)
        if current:
            current.update(updates)
            return await self.set_status(task_id, current, ttl)
        else:
            return await self.set_status(task_id, updates, ttl)

    async def delete_status(self, task_id: str) -> bool:
        """Delete task status.

        Args:
            task_id: Unique task identifier

        Returns:
            True if status was deleted (or didn't exist)
        """
        if not self._initialized:
            await self.initialize()

        if self._use_fallback:
            async with self._fallback_lock:
                self._fallback_cache.pop(task_id, None)
            return True

        try:
            key = self._make_key(task_id)
            if self._redis._connected and self._redis._client:
                await self._redis._client.delete(key)
                return True
            else:
                async with self._fallback_lock:
                    self._fallback_cache.pop(task_id, None)
                return True

        except Exception as e:
            logger.warning(f"Redis delete_status failed: {e}")
            return False

    async def exists(self, task_id: str) -> bool:
        """Check if task status exists.

        Args:
            task_id: Unique task identifier

        Returns:
            True if status exists
        """
        if not self._initialized:
            await self.initialize()

        if self._use_fallback:
            async with self._fallback_lock:
                return task_id in self._fallback_cache

        try:
            key = self._make_key(task_id)
            if self._redis._connected and self._redis._client:
                return bool(await self._redis._client.exists(key))
            else:
                async with self._fallback_lock:
                    return task_id in self._fallback_cache

        except Exception as e:
            logger.warning(f"Redis exists check failed: {e}")
            async with self._fallback_lock:
                return task_id in self._fallback_cache

    async def get_stats(self) -> dict[str, Any]:
        """Get store statistics.

        Returns:
            Dictionary with store metrics
        """
        stats = {
            "initialized": self._initialized,
            "using_fallback": self._use_fallback,
            "ttl_seconds": self._ttl,
        }

        if self._use_fallback:
            async with self._fallback_lock:
                stats["fallback_entries"] = len(self._fallback_cache)
                stats["fallback_max_entries"] = self.MAX_IN_MEMORY_ENTRIES

        return stats

    async def close(self) -> None:
        """Close the store and disconnect from Redis."""
        if self._redis:
            await self._redis.disconnect()
        self._initialized = False


# Singleton instance for dependency injection
_task_status_store: TaskStatusStore | None = None


def get_task_status_store() -> TaskStatusStore:
    """Get or create the global TaskStatusStore instance.

    Returns:
        TaskStatusStore singleton instance
    """
    global _task_status_store
    if _task_status_store is None:
        _task_status_store = TaskStatusStore()
    return _task_status_store


async def get_initialized_task_status_store() -> TaskStatusStore:
    """Get initialized TaskStatusStore for FastAPI dependency injection.

    Usage in FastAPI:
        @router.get("/status/{task_id}")
        async def get_status(
            task_id: str,
            store: TaskStatusStore = Depends(get_initialized_task_status_store)
        ):
            return await store.get_status(task_id)

    Returns:
        Initialized TaskStatusStore instance
    """
    store = get_task_status_store()
    await store.initialize()
    return store
