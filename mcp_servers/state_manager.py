"""
MCP State Manager for DevSkyy Unified Cloud Server

Persistent state management using Redis for hot data and in-memory fallback.

Sources Verified (5-Source Requirement per CLAUDE.md):
1. FastMCP 2.13 Persistent Storage: https://gofastmcp.com/updates
2. Redis Async Best Practices: https://redis.io/docs/clients/python/
3. MCP State Management: https://modelcontextprotocol.io/development/roadmap
4. Python Redis Patterns: https://realpython.com/python-redis/
5. Enterprise Caching Patterns: https://aws.amazon.com/caching/best-practices/

Per Truth Protocol:
- Rule #5: No secrets in code (REDIS_URL from env)
- Rule #10: No-skip rule - fallback to in-memory on Redis failure
- Rule #12: Performance SLOs - P95 < 200ms
- Rule #14: Error ledger for persistence failures
"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from enum import Enum
import json
import logging
import os
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)

# Constants
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
STATE_KEY_PREFIX = "mcp:state:"
DEFAULT_TTL_SECONDS = 3600  # 1 hour
MAX_MEMORY_ENTRIES = 10000


# ============================================================================
# STATE MODELS
# ============================================================================


class StateCategory(str, Enum):
    """Categories of persistent state."""

    THEME_BUILDS = "theme_builds"
    PRODUCT_CATALOG = "product_catalog"
    CONTENT_DRAFTS = "content_drafts"
    AGENT_TASKS = "agent_tasks"
    DISCOUNT_CODES = "discount_codes"
    RAG_DOCUMENTS = "rag_documents"
    RAG_CHUNKS = "rag_chunks"
    SESSION = "session"
    CACHE = "cache"


T = TypeVar("T")


class StateEntry(BaseModel, Generic[T]):
    """Generic state entry with metadata."""

    key: str
    category: StateCategory
    value: Any
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ttl_seconds: int | None = None
    version: int = 1

    def to_json(self) -> str:
        """Serialize to JSON."""
        data = self.model_dump()
        data["created_at"] = data["created_at"].isoformat()
        data["updated_at"] = data["updated_at"].isoformat()
        data["category"] = data["category"].value
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> "StateEntry":
        """Deserialize from JSON."""
        data = json.loads(json_str)
        data["category"] = StateCategory(data["category"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)


# ============================================================================
# IN-MEMORY STATE BACKEND (Fallback)
# ============================================================================


class InMemoryStateBackend:
    """In-memory state backend for local development or Redis fallback."""

    def __init__(self, max_entries: int = MAX_MEMORY_ENTRIES) -> None:
        """Initialize in-memory backend."""
        self._store: dict[str, StateEntry] = {}
        self._max_entries = max_entries
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> StateEntry | None:
        """Get state entry by key."""
        async with self._lock:
            entry = self._store.get(key)
            if entry and entry.ttl_seconds:
                # Check expiration
                age = (datetime.now(UTC) - entry.updated_at).total_seconds()
                if age > entry.ttl_seconds:
                    del self._store[key]
                    return None
            return entry

    async def set(self, entry: StateEntry) -> bool:
        """Set state entry."""
        async with self._lock:
            # Evict oldest if at capacity
            if len(self._store) >= self._max_entries and entry.key not in self._store:
                oldest_key = min(self._store.keys(), key=lambda k: self._store[k].updated_at)
                del self._store[oldest_key]
            entry.updated_at = datetime.now(UTC)
            self._store[entry.key] = entry
            return True

    async def delete(self, key: str) -> bool:
        """Delete state entry."""
        async with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return key in self._store

    async def keys(self, pattern: str = "*") -> list[str]:
        """Get keys matching pattern."""
        if pattern == "*":
            return list(self._store)
        # Simple prefix matching
        prefix = pattern.rstrip("*")
        return [k for k in self._store if k.startswith(prefix)]

    async def get_by_category(self, category: StateCategory) -> list[StateEntry]:
        """Get all entries in a category."""
        return [e for e in self._store.values() if e.category == category]

    async def clear_category(self, category: StateCategory) -> int:
        """Clear all entries in a category."""
        async with self._lock:
            keys_to_delete = [k for k, v in self._store.items() if v.category == category]
            for key in keys_to_delete:
                del self._store[key]
            return len(keys_to_delete)

    async def stats(self) -> dict[str, Any]:
        """Get backend statistics."""
        category_counts: dict[str, int] = {}
        for entry in self._store.values():
            cat = entry.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            "backend": "in_memory",
            "total_entries": len(self._store),
            "max_entries": self._max_entries,
            "categories": category_counts,
        }


# ============================================================================
# REDIS STATE BACKEND
# ============================================================================


class RedisStateBackend:
    """Redis-backed state storage for production deployments."""

    def __init__(self, redis_url: str = REDIS_URL) -> None:
        """Initialize Redis backend."""
        self._redis_url = redis_url
        self._client: Any = None
        self._connected = False
        self._fallback = InMemoryStateBackend()

    async def _ensure_connected(self) -> bool:
        """Ensure Redis connection is established."""
        if self._connected and self._client:
            return True

        try:
            import redis.asyncio as redis  # noqa: PLC0415 - lazy import for optional dependency

            self._client = redis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
            )
            await self._client.ping()
            self._connected = True
            logger.info("Redis connection established")
            return True
        except ImportError:
            logger.warning("redis package not installed, using in-memory fallback")
            return False
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, using in-memory fallback")
            self._connected = False
            return False

    async def get(self, key: str) -> StateEntry | None:
        """Get state entry by key."""
        if not await self._ensure_connected():
            return await self._fallback.get(key)

        try:
            full_key = f"{STATE_KEY_PREFIX}{key}"
            data = await self._client.get(full_key)
            if data:
                return StateEntry.from_json(data)
            return None
        except Exception as e:
            logger.error(f"Redis get failed: {e}")
            return await self._fallback.get(key)

    async def set(self, entry: StateEntry) -> bool:
        """Set state entry."""
        if not await self._ensure_connected():
            return await self._fallback.set(entry)

        try:
            full_key = f"{STATE_KEY_PREFIX}{entry.key}"
            entry.updated_at = datetime.now(UTC)
            json_data = entry.to_json()

            if entry.ttl_seconds:
                await self._client.setex(full_key, entry.ttl_seconds, json_data)
            else:
                await self._client.set(full_key, json_data)
            return True
        except Exception as e:
            logger.error(f"Redis set failed: {e}")
            return await self._fallback.set(entry)

    async def delete(self, key: str) -> bool:
        """Delete state entry."""
        if not await self._ensure_connected():
            return await self._fallback.delete(key)

        try:
            full_key = f"{STATE_KEY_PREFIX}{key}"
            result = await self._client.delete(full_key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete failed: {e}")
            return await self._fallback.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not await self._ensure_connected():
            return await self._fallback.exists(key)

        try:
            full_key = f"{STATE_KEY_PREFIX}{key}"
            return await self._client.exists(full_key) > 0
        except Exception as e:
            logger.error(f"Redis exists failed: {e}")
            return await self._fallback.exists(key)

    async def keys(self, pattern: str = "*") -> list[str]:
        """Get keys matching pattern."""
        if not await self._ensure_connected():
            return await self._fallback.keys(pattern)

        try:
            full_pattern = f"{STATE_KEY_PREFIX}{pattern}"
            keys = await self._client.keys(full_pattern)
            # Remove prefix from returned keys
            prefix_len = len(STATE_KEY_PREFIX)
            return [k[prefix_len:] for k in keys]
        except Exception as e:
            logger.error(f"Redis keys failed: {e}")
            return await self._fallback.keys(pattern)

    async def get_by_category(self, category: StateCategory) -> list[StateEntry]:
        """Get all entries in a category."""
        pattern = f"{category.value}:*"
        keys = await self.keys(pattern)
        entries = []
        for key in keys:
            entry = await self.get(key)
            if entry:
                entries.append(entry)
        return entries

    async def clear_category(self, category: StateCategory) -> int:
        """Clear all entries in a category."""
        pattern = f"{category.value}:*"
        keys = await self.keys(pattern)
        count = 0
        for key in keys:
            if await self.delete(key):
                count += 1
        return count

    async def stats(self) -> dict[str, Any]:
        """Get backend statistics."""
        if not await self._ensure_connected():
            fallback_stats = await self._fallback.stats()
            fallback_stats["redis_available"] = False
            return fallback_stats

        try:
            info = await self._client.info("memory")
            keys = await self.keys("*")

            # Count by category
            category_counts: dict[str, int] = {}
            for key in keys:
                parts = key.split(":")
                if parts:
                    cat = parts[0]
                    category_counts[cat] = category_counts.get(cat, 0) + 1

            return {
                "backend": "redis",
                "redis_available": True,
                "total_entries": len(keys),
                "memory_used": info.get("used_memory_human", "unknown"),
                "categories": category_counts,
            }
        except Exception as e:
            logger.error(f"Redis stats failed: {e}")
            return {"backend": "redis", "redis_available": False, "error": str(e)}

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._connected = False


# ============================================================================
# UNIFIED STATE MANAGER
# ============================================================================


class MCPStateManager:
    """
    Unified state manager for MCP server.

    Provides a simple interface for persistent state with automatic
    fallback to in-memory storage when Redis is unavailable.
    """

    _instance: "MCPStateManager | None" = None

    def __new__(cls) -> "MCPStateManager":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize state manager."""
        if self._initialized:
            return
        self._initialized = True

        # Use Redis if REDIS_URL is set, otherwise in-memory
        if os.getenv("REDIS_URL"):
            self._backend = RedisStateBackend()
            logger.info("Using Redis state backend")
        else:
            self._backend = InMemoryStateBackend()
            logger.info("Using in-memory state backend")

    # ========================================================================
    # GENERIC STATE OPERATIONS
    # ========================================================================

    async def get(self, category: StateCategory, key: str) -> Any | None:
        """Get a value from state."""
        full_key = f"{category.value}:{key}"
        entry = await self._backend.get(full_key)
        return entry.value if entry else None

    async def set(
        self,
        category: StateCategory,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> bool:
        """Set a value in state."""
        full_key = f"{category.value}:{key}"
        entry = StateEntry(
            key=full_key,
            category=category,
            value=value,
            ttl_seconds=ttl_seconds,
        )
        return await self._backend.set(entry)

    async def delete(self, category: StateCategory, key: str) -> bool:
        """Delete a value from state."""
        full_key = f"{category.value}:{key}"
        return await self._backend.delete(full_key)

    async def exists(self, category: StateCategory, key: str) -> bool:
        """Check if a key exists."""
        full_key = f"{category.value}:{key}"
        return await self._backend.exists(full_key)

    async def list_keys(self, category: StateCategory) -> list[str]:
        """List all keys in a category."""
        pattern = f"{category.value}:*"
        keys = await self._backend.keys(pattern)
        # Remove category prefix
        prefix_len = len(category.value) + 1
        return [k[prefix_len:] for k in keys]

    async def get_all(self, category: StateCategory) -> dict[str, Any]:
        """Get all values in a category."""
        entries = await self._backend.get_by_category(category)
        prefix_len = len(category.value) + 1
        return {e.key[prefix_len:]: e.value for e in entries}

    async def clear(self, category: StateCategory) -> int:
        """Clear all values in a category."""
        return await self._backend.clear_category(category)

    async def stats(self) -> dict[str, Any]:
        """Get state manager statistics."""
        return await self._backend.stats()

    # ========================================================================
    # CATEGORY-SPECIFIC HELPERS
    # ========================================================================

    async def get_theme_build(self, build_id: str) -> dict[str, Any] | None:
        """Get theme build status."""
        return await self.get(StateCategory.THEME_BUILDS, build_id)

    async def set_theme_build(self, build_id: str, data: dict[str, Any]) -> bool:
        """Set theme build status."""
        return await self.set(StateCategory.THEME_BUILDS, build_id, data, ttl_seconds=3600)

    async def get_product(self, product_id: str) -> dict[str, Any] | None:
        """Get product from catalog."""
        return await self.get(StateCategory.PRODUCT_CATALOG, product_id)

    async def set_product(self, product_id: str, data: dict[str, Any]) -> bool:
        """Set product in catalog."""
        return await self.set(StateCategory.PRODUCT_CATALOG, product_id, data)

    async def get_agent_task(self, task_id: str) -> dict[str, Any] | None:
        """Get agent task."""
        return await self.get(StateCategory.AGENT_TASKS, task_id)

    async def set_agent_task(self, task_id: str, data: dict[str, Any]) -> bool:
        """Set agent task."""
        return await self.set(StateCategory.AGENT_TASKS, task_id, data, ttl_seconds=86400)

    async def get_rag_document(self, doc_id: str) -> dict[str, Any] | None:
        """Get RAG document metadata."""
        return await self.get(StateCategory.RAG_DOCUMENTS, doc_id)

    async def set_rag_document(self, doc_id: str, data: dict[str, Any]) -> bool:
        """Set RAG document metadata."""
        return await self.set(StateCategory.RAG_DOCUMENTS, doc_id, data)


# Global state manager instance
state_manager = MCPStateManager()


# ============================================================================
# CONTEXT MANAGER FOR STATE TRANSACTIONS
# ============================================================================


@asynccontextmanager
async def state_transaction(category: StateCategory) -> AsyncIterator[dict[str, Any]]:
    """
    Context manager for state transactions.

    Provides a dict that is automatically persisted on exit.

    Usage:
        async with state_transaction(StateCategory.THEME_BUILDS) as builds:
            builds["build_123"] = {"status": "complete"}
    """
    # Load current state
    current = await state_manager.get_all(category)
    transaction_data = dict(current)

    try:
        yield transaction_data
    finally:
        # Persist changes
        for key, value in transaction_data.items():
            if key not in current or current[key] != value:
                await state_manager.set(category, key, value)

        # Delete removed keys
        for key in current:
            if key not in transaction_data:
                await state_manager.delete(category, key)
