"""
Cache Agent - Edge-side caching with delta synchronization

Design Principle: Keep frequently accessed data at the edge for <50ms access
while maintaining consistency with backend through delta sync.

Features:
- Multi-tier caching (memory → local storage → backend)
- Delta synchronization (only sync changes)
- TTL management with intelligent refresh
- Cache warming and prefetching
- Conflict detection and resolution

Per CLAUDE.md Truth Protocol:
- Rule #7: Pydantic validation for cache operations
- Rule #10: Log errors, continue processing
- Rule #12: Cache hit target >80%, P95 <50ms
"""

import asyncio
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import logging
from typing import Any

from pydantic import BaseModel, Field

from agent.edge.base_edge_agent import (
    BaseEdgeAgent,
    ExecutionLocation,
    OfflineCapability,
    SyncPriority,
)


logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Cache storage levels"""

    MEMORY = "memory"  # Fastest, volatile
    LOCAL = "local"  # Persistent local storage
    BACKEND = "backend"  # Authoritative source


class CachePolicy(Enum):
    """Cache eviction policies"""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out
    TTL = "ttl"  # Time-based expiration only


class SyncStrategy(Enum):
    """Synchronization strategies with backend"""

    WRITE_THROUGH = "write_through"  # Immediate sync on write
    WRITE_BACK = "write_back"  # Delayed batch sync
    WRITE_AROUND = "write_around"  # Skip cache, write to backend


class CacheRequest(BaseModel):
    """Cache operation request (Pydantic validated)"""

    key: str = Field(..., min_length=1, max_length=512)
    namespace: str = Field(default="default", max_length=128)
    ttl_seconds: float = Field(default=300.0, ge=0)
    priority: int = Field(default=0, ge=0, le=100)
    tags: list[str] = Field(default_factory=list)


class CacheEntry(BaseModel):
    """Individual cache entry"""

    key: str
    value: Any
    namespace: str = "default"
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed: datetime = Field(default_factory=datetime.now)
    ttl_seconds: float = 300.0
    access_count: int = 0
    checksum: str = ""
    version: int = 1
    tags: list[str] = Field(default_factory=list)

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl_seconds

    def compute_checksum(self) -> str:
        """Compute checksum of value for delta detection."""
        return hashlib.sha256(str(self.value).encode()).hexdigest()[:16]


@dataclass
class DeltaChange:
    """Represents a change for delta synchronization"""

    key: str
    namespace: str
    operation: str  # 'set', 'delete', 'update'
    old_checksum: str | None
    new_checksum: str | None
    timestamp: datetime = field(default_factory=datetime.now)
    synced: bool = False


@dataclass
class CacheStats:
    """Cache performance statistics"""

    hits: int = 0
    misses: int = 0
    writes: int = 0
    deletes: int = 0
    evictions: int = 0
    sync_operations: int = 0
    conflicts_detected: int = 0
    conflicts_resolved: int = 0
    average_access_time_ms: float = 0.0
    memory_entries: int = 0
    local_entries: int = 0


class LRUCache(OrderedDict):
    """LRU Cache implementation with size limit."""

    def __init__(self, max_size: int = 10000):
        super().__init__()
        self.max_size = max_size

    def get(self, key: str) -> Any | None:
        if key not in self:
            return None
        self.move_to_end(key)
        return self[key]

    def set(self, key: str, value: Any) -> None:
        if key in self:
            self.move_to_end(key)
        self[key] = value
        if len(self) > self.max_size:
            oldest = next(iter(self))
            del self[oldest]


class CacheAgent(BaseEdgeAgent):
    """
    Cache Agent - High-performance edge caching with delta sync.

    Provides:
    - Ultra-fast cache access (<10ms target)
    - Multi-namespace support
    - Delta synchronization with backend
    - Intelligent prefetching
    - Cache warming capabilities

    Target metrics:
    - Cache hit ratio: >80%
    - P95 access latency: <10ms
    - Sync efficiency: >90% delta-only
    """

    CACHE_ACCESS_TARGET_MS: float = 10.0
    DEFAULT_TTL_SECONDS: float = 300.0
    MAX_MEMORY_ENTRIES: int = 50000
    MAX_LOCAL_ENTRIES: int = 500000
    SYNC_BATCH_SIZE: int = 100

    def __init__(
        self,
        agent_name: str = "CacheAgent",
        version: str = "1.0.0",
        policy: CachePolicy = CachePolicy.LRU,
        sync_strategy: SyncStrategy = SyncStrategy.WRITE_BACK,
    ):
        super().__init__(
            agent_name=agent_name,
            version=version,
            offline_capability=OfflineCapability.FULL,
        )

        self.policy = policy
        self.sync_strategy = sync_strategy
        self.stats = CacheStats()

        # Multi-tier cache storage
        self._memory_cache: LRUCache = LRUCache(max_size=self.MAX_MEMORY_ENTRIES)
        self._local_cache: dict[str, CacheEntry] = {}  # Simulates persistent storage

        # Delta tracking for sync
        self._pending_deltas: list[DeltaChange] = []
        self._backend_checksums: dict[str, str] = {}  # Last known backend state

        # Namespace management
        self._namespace_ttls: dict[str, float] = {}

        # Tag-based invalidation index
        self._tag_index: dict[str, set[str]] = {}  # tag -> set of keys

        logger.info(
            f"CacheAgent initialized (policy={policy.value}, sync={sync_strategy.value})"
        )

    async def execute_local(self, operation: str, **kwargs) -> dict[str, Any]:
        """Execute cache operation locally."""
        start_time = datetime.now()

        try:
            if operation == "get":
                result = await self._handle_get(kwargs)
            elif operation == "set":
                result = await self._handle_set(kwargs)
            elif operation == "delete":
                result = await self._handle_delete(kwargs)
            elif operation == "invalidate_by_tag":
                result = await self._handle_invalidate_by_tag(kwargs)
            elif operation == "get_stats":
                result = self._get_stats()
            elif operation == "warm_cache":
                result = await self._handle_warm_cache(kwargs)
            elif operation == "get_pending_deltas":
                result = self._get_pending_deltas()
            elif operation == "clear_namespace":
                result = await self._handle_clear_namespace(kwargs)
            else:
                result = {"error": f"Unknown operation: {operation}"}

            # Track access time
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            self._update_access_time(elapsed_ms)

            return result

        except Exception as e:
            logger.error(f"Cache operation {operation} failed: {e}")
            return {"error": str(e), "operation": operation}

    def get_routing_rules(self) -> dict[str, ExecutionLocation]:
        """Define routing rules for CacheAgent operations."""
        return {
            "get": ExecutionLocation.EDGE,
            "set": ExecutionLocation.EDGE,
            "delete": ExecutionLocation.EDGE,
            "invalidate_by_tag": ExecutionLocation.EDGE,
            "get_stats": ExecutionLocation.EDGE,
            "warm_cache": ExecutionLocation.HYBRID,
            "sync_to_backend": ExecutionLocation.BACKEND,
            "full_refresh": ExecutionLocation.BACKEND,
            "get_pending_deltas": ExecutionLocation.EDGE,
            "clear_namespace": ExecutionLocation.EDGE,
        }

    # === Core Cache Operations ===

    async def get(
        self, key: str, namespace: str = "default"
    ) -> tuple[Any, bool]:
        """
        Get value from cache.

        Checks memory cache first, then local cache.

        Args:
            key: Cache key
            namespace: Cache namespace

        Returns:
            Tuple of (value, hit) where hit is True if found
        """
        full_key = self._make_key(key, namespace)

        # Check memory cache first (fastest)
        entry = self._memory_cache.get(full_key)
        if entry and not entry.is_expired():
            entry.last_accessed = datetime.now()
            entry.access_count += 1
            self.stats.hits += 1
            return entry.value, True

        # Check local cache (persistent)
        if full_key in self._local_cache:
            entry = self._local_cache[full_key]
            if not entry.is_expired():
                # Promote to memory cache
                self._memory_cache.set(full_key, entry)
                entry.last_accessed = datetime.now()
                entry.access_count += 1
                self.stats.hits += 1
                return entry.value, True
            else:
                # Expired, remove
                del self._local_cache[full_key]

        self.stats.misses += 1
        return None, False

    async def set(
        self,
        key: str,
        value: Any,
        namespace: str = "default",
        ttl_seconds: float | None = None,
        tags: list[str] | None = None,
    ) -> bool:
        """
        Set value in cache.

        Stores in both memory and local cache, tracks delta for sync.

        Args:
            key: Cache key
            value: Value to cache
            namespace: Cache namespace
            ttl_seconds: Optional TTL override
            tags: Optional tags for grouped invalidation

        Returns:
            True if successful
        """
        full_key = self._make_key(key, namespace)
        ttl = ttl_seconds or self._namespace_ttls.get(namespace, self.DEFAULT_TTL_SECONDS)

        # Get old checksum for delta tracking
        old_checksum = None
        if full_key in self._local_cache:
            old_checksum = self._local_cache[full_key].checksum

        # Create entry
        entry = CacheEntry(
            key=key,
            value=value,
            namespace=namespace,
            ttl_seconds=ttl,
            tags=tags or [],
        )
        entry.checksum = entry.compute_checksum()

        # Store in both tiers
        self._memory_cache.set(full_key, entry)
        self._local_cache[full_key] = entry
        self.stats.writes += 1

        # Update tag index
        if tags:
            for tag in tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = set()
                self._tag_index[tag].add(full_key)

        # Track delta for sync
        self._track_delta(
            full_key,
            namespace,
            "set" if old_checksum is None else "update",
            old_checksum,
            entry.checksum,
        )

        # Handle sync strategy
        if self.sync_strategy == SyncStrategy.WRITE_THROUGH:
            await self._queue_for_sync(
                "cache_sync",
                {"key": full_key, "value": value, "checksum": entry.checksum},
                SyncPriority.IMMEDIATE,
            )

        return True

    async def delete(self, key: str, namespace: str = "default") -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key
            namespace: Cache namespace

        Returns:
            True if deleted, False if not found
        """
        full_key = self._make_key(key, namespace)

        found = False
        old_checksum = None

        if full_key in self._memory_cache:
            old_checksum = self._memory_cache[full_key].checksum
            del self._memory_cache[full_key]
            found = True

        if full_key in self._local_cache:
            if old_checksum is None:
                old_checksum = self._local_cache[full_key].checksum
            # Remove from tag index
            for tag in self._local_cache[full_key].tags:
                if tag in self._tag_index:
                    self._tag_index[tag].discard(full_key)
            del self._local_cache[full_key]
            found = True

        if found:
            self.stats.deletes += 1
            self._track_delta(full_key, namespace, "delete", old_checksum, None)

        return found

    async def invalidate_by_tag(self, tag: str) -> int:
        """
        Invalidate all entries with a specific tag.

        Args:
            tag: Tag to invalidate

        Returns:
            Number of entries invalidated
        """
        if tag not in self._tag_index:
            return 0

        keys_to_invalidate = list(self._tag_index[tag])
        count = 0

        for full_key in keys_to_invalidate:
            if full_key in self._memory_cache:
                del self._memory_cache[full_key]
                count += 1
            if full_key in self._local_cache:
                entry = self._local_cache[full_key]
                self._track_delta(
                    full_key, entry.namespace, "delete", entry.checksum, None
                )
                del self._local_cache[full_key]

        del self._tag_index[tag]
        self.stats.evictions += count

        logger.info(f"Invalidated {count} entries with tag '{tag}'")
        return count

    # === Delta Synchronization ===

    def _track_delta(
        self,
        key: str,
        namespace: str,
        operation: str,
        old_checksum: str | None,
        new_checksum: str | None,
    ) -> None:
        """Track a change for delta synchronization."""
        delta = DeltaChange(
            key=key,
            namespace=namespace,
            operation=operation,
            old_checksum=old_checksum,
            new_checksum=new_checksum,
        )
        self._pending_deltas.append(delta)

        # Keep bounded
        if len(self._pending_deltas) > 10000:
            # Remove oldest synced deltas
            self._pending_deltas = [d for d in self._pending_deltas if not d.synced][-5000:]

    def get_deltas_for_sync(self) -> list[dict[str, Any]]:
        """
        Get pending deltas for synchronization.

        Returns only unsynced changes, optimized for bandwidth.
        """
        unsynced = [d for d in self._pending_deltas if not d.synced]

        # Optimize: collapse multiple updates to same key
        latest_by_key: dict[str, DeltaChange] = {}
        for delta in unsynced:
            if delta.key in latest_by_key:
                prev = latest_by_key[delta.key]
                # Merge: if prev was 'set' and this is 'delete', just 'delete'
                if prev.operation == "set" and delta.operation == "delete":
                    delta.old_checksum = prev.old_checksum
                elif prev.operation in ("set", "update") and delta.operation in (
                    "set",
                    "update",
                ):
                    # Keep original old_checksum, update new_checksum
                    delta.old_checksum = prev.old_checksum
                    delta.operation = "update" if prev.old_checksum else "set"
            latest_by_key[delta.key] = delta

        return [
            {
                "key": d.key,
                "namespace": d.namespace,
                "operation": d.operation,
                "old_checksum": d.old_checksum,
                "new_checksum": d.new_checksum,
                "timestamp": d.timestamp.isoformat(),
            }
            for d in latest_by_key.values()
        ]

    def mark_deltas_synced(self, keys: list[str]) -> int:
        """Mark deltas as synced."""
        count = 0
        for delta in self._pending_deltas:
            if delta.key in keys:
                delta.synced = True
                count += 1
        self.stats.sync_operations += count
        return count

    def detect_conflicts(
        self, backend_checksums: dict[str, str]
    ) -> list[dict[str, Any]]:
        """
        Detect conflicts between local and backend state.

        Args:
            backend_checksums: Current checksums from backend

        Returns:
            List of conflicting keys with details
        """
        conflicts = []

        for key, backend_checksum in backend_checksums.items():
            if key in self._local_cache:
                local_entry = self._local_cache[key]
                if local_entry.checksum != backend_checksum:
                    # Check if we expected this checksum
                    expected = self._backend_checksums.get(key)
                    if expected and expected != backend_checksum:
                        # Backend changed independently - conflict!
                        conflicts.append(
                            {
                                "key": key,
                                "local_checksum": local_entry.checksum,
                                "backend_checksum": backend_checksum,
                                "expected_checksum": expected,
                                "local_version": local_entry.version,
                            }
                        )
                        self.stats.conflicts_detected += 1

        return conflicts

    def resolve_conflict(
        self, key: str, resolution: str, backend_value: Any | None = None
    ) -> bool:
        """
        Resolve a cache conflict.

        Args:
            key: Conflicting key
            resolution: 'keep_local', 'use_backend', or 'merge'
            backend_value: Backend value if using backend or merging

        Returns:
            True if resolved
        """
        if key not in self._local_cache:
            return False

        entry = self._local_cache[key]

        if resolution == "keep_local":
            # Re-queue for sync with force flag
            entry.version += 1
            entry.checksum = entry.compute_checksum()
            self._track_delta(key, entry.namespace, "update", None, entry.checksum)

        elif resolution == "use_backend":
            if backend_value is not None:
                entry.value = backend_value
                entry.checksum = entry.compute_checksum()
                entry.version += 1
                self._memory_cache.set(key, entry)
            else:
                # Delete local
                del self._local_cache[key]
                if key in self._memory_cache:
                    del self._memory_cache[key]

        elif resolution == "merge":
            # Application-specific merge would go here
            # Default: newer wins (local, since we're modifying)
            entry.version += 1
            entry.checksum = entry.compute_checksum()
            self._track_delta(key, entry.namespace, "update", None, entry.checksum)

        self.stats.conflicts_resolved += 1
        logger.info(f"Resolved conflict for {key} using '{resolution}'")
        return True

    # === Cache Warming ===

    async def warm_cache(
        self, keys: list[tuple[str, str]], values: list[Any], ttl_seconds: float = 300.0
    ) -> int:
        """
        Warm cache with multiple entries.

        Args:
            keys: List of (key, namespace) tuples
            values: Corresponding values
            ttl_seconds: TTL for warmed entries

        Returns:
            Number of entries warmed
        """
        count = 0
        for (key, namespace), value in zip(keys, values):
            await self.set(key, value, namespace, ttl_seconds)
            count += 1

        logger.info(f"Warmed cache with {count} entries")
        return count

    # === Helper Methods ===

    def _make_key(self, key: str, namespace: str) -> str:
        """Create full cache key with namespace."""
        return f"{namespace}:{key}"

    def _update_access_time(self, elapsed_ms: float) -> None:
        """Update average access time metric."""
        total = self.stats.hits + self.stats.misses
        if total > 0:
            self.stats.average_access_time_ms = (
                self.stats.average_access_time_ms * (total - 1) + elapsed_ms
            ) / total

    def _get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        self.stats.memory_entries = len(self._memory_cache)
        self.stats.local_entries = len(self._local_cache)

        total = self.stats.hits + self.stats.misses
        hit_ratio = (self.stats.hits / total * 100) if total > 0 else 0.0

        return {
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "hit_ratio": round(hit_ratio, 2),
            "writes": self.stats.writes,
            "deletes": self.stats.deletes,
            "evictions": self.stats.evictions,
            "memory_entries": self.stats.memory_entries,
            "local_entries": self.stats.local_entries,
            "average_access_time_ms": round(self.stats.average_access_time_ms, 2),
            "pending_deltas": len([d for d in self._pending_deltas if not d.synced]),
            "sync_operations": self.stats.sync_operations,
            "conflicts_detected": self.stats.conflicts_detected,
            "conflicts_resolved": self.stats.conflicts_resolved,
        }

    def _get_pending_deltas(self) -> dict[str, Any]:
        """Get pending deltas for sync."""
        deltas = self.get_deltas_for_sync()
        return {"count": len(deltas), "deltas": deltas[:self.SYNC_BATCH_SIZE]}

    # === Request Handlers ===

    async def _handle_get(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Handle get request."""
        key = kwargs.get("key")
        namespace = kwargs.get("namespace", "default")

        if not key:
            return {"error": "key is required"}

        value, hit = await self.get(key, namespace)
        return {"value": value, "hit": hit}

    async def _handle_set(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Handle set request."""
        key = kwargs.get("key")
        value = kwargs.get("value")
        namespace = kwargs.get("namespace", "default")
        ttl = kwargs.get("ttl_seconds")
        tags = kwargs.get("tags")

        if not key:
            return {"error": "key is required"}

        success = await self.set(key, value, namespace, ttl, tags)
        return {"success": success}

    async def _handle_delete(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Handle delete request."""
        key = kwargs.get("key")
        namespace = kwargs.get("namespace", "default")

        if not key:
            return {"error": "key is required"}

        found = await self.delete(key, namespace)
        return {"deleted": found}

    async def _handle_invalidate_by_tag(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Handle invalidate by tag request."""
        tag = kwargs.get("tag")

        if not tag:
            return {"error": "tag is required"}

        count = await self.invalidate_by_tag(tag)
        return {"invalidated": count}

    async def _handle_warm_cache(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Handle cache warming request."""
        keys = kwargs.get("keys", [])
        values = kwargs.get("values", [])
        ttl = kwargs.get("ttl_seconds", 300.0)

        if len(keys) != len(values):
            return {"error": "keys and values must have same length"}

        count = await self.warm_cache(keys, values, ttl)
        return {"warmed": count}

    async def _handle_clear_namespace(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Handle clear namespace request."""
        namespace = kwargs.get("namespace")

        if not namespace:
            return {"error": "namespace is required"}

        prefix = f"{namespace}:"
        count = 0

        # Clear from memory cache
        keys_to_remove = [k for k in self._memory_cache if k.startswith(prefix)]
        for key in keys_to_remove:
            del self._memory_cache[key]
            count += 1

        # Clear from local cache
        keys_to_remove = [k for k in self._local_cache if k.startswith(prefix)]
        for key in keys_to_remove:
            entry = self._local_cache[key]
            self._track_delta(key, namespace, "delete", entry.checksum, None)
            del self._local_cache[key]

        self.stats.evictions += count
        return {"cleared": count}

    def set_namespace_ttl(self, namespace: str, ttl_seconds: float) -> None:
        """Set default TTL for a namespace."""
        self._namespace_ttls[namespace] = ttl_seconds
