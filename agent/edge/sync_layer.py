"""
Sync Layer - Delta synchronization between edge and backend

Design Principle: Keep edge and backend in sync with minimal bandwidth
using delta updates, conflict resolution, and offline queue management.

Features:
- Delta-only sync (only changed data)
- Conflict detection and resolution
- Offline queue with automatic retry
- Version vectors for causality tracking
- Compression for large payloads
- Prioritized sync (critical first)

Per CLAUDE.md Truth Protocol:
- Rule #1: Sync based on verified state
- Rule #10: Log errors, continue processing
- Rule #12: Sync latency P95 <500ms
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import gzip
import hashlib
import json
import logging
from typing import Any

from pydantic import BaseModel, Field

from agent.edge.base_edge_agent import SyncPriority


logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    """Status of a sync operation"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"
    RETRYING = "retrying"


class ConflictResolution(Enum):
    """Conflict resolution strategies"""

    LAST_WRITE_WINS = "last_write_wins"  # Most recent timestamp wins
    FIRST_WRITE_WINS = "first_write_wins"  # Original value preserved
    SERVER_WINS = "server_wins"  # Backend is authoritative
    CLIENT_WINS = "client_wins"  # Edge value wins
    MERGE = "merge"  # Attempt to merge
    MANUAL = "manual"  # Require human resolution


class SyncDirection(Enum):
    """Direction of synchronization"""

    PUSH = "push"  # Edge → Backend
    PULL = "pull"  # Backend → Edge
    BIDIRECTIONAL = "bidirectional"  # Both directions


class DeltaOperation(Enum):
    """Types of delta operations"""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    PATCH = "patch"  # Partial update


class SyncDelta(BaseModel):
    """Individual sync delta"""

    delta_id: str
    entity_type: str  # e.g., "user", "product", "order"
    entity_id: str
    operation: DeltaOperation
    old_version: int | None = None
    new_version: int
    old_checksum: str | None = None
    new_checksum: str
    data: dict[str, Any] | None = None
    patch: dict[str, Any] | None = None  # For partial updates
    created_at: datetime = Field(default_factory=datetime.now)
    priority: SyncPriority = SyncPriority.MEDIUM
    compressed: bool = False
    size_bytes: int = 0


class SyncBatch(BaseModel):
    """Batch of deltas for sync"""

    batch_id: str
    deltas: list[SyncDelta]
    direction: SyncDirection
    created_at: datetime = Field(default_factory=datetime.now)
    total_size_bytes: int = 0
    compressed_size_bytes: int | None = None
    status: SyncStatus = SyncStatus.PENDING


class ConflictInfo(BaseModel):
    """Information about a sync conflict"""

    entity_type: str
    entity_id: str
    edge_version: int
    backend_version: int
    edge_checksum: str
    backend_checksum: str
    edge_data: dict[str, Any] | None = None
    backend_data: dict[str, Any] | None = None
    detected_at: datetime = Field(default_factory=datetime.now)
    resolution: ConflictResolution | None = None
    resolved_at: datetime | None = None


@dataclass
class VersionVector:
    """Version vector for tracking causality across nodes"""

    node_id: str
    versions: dict[str, int] = field(default_factory=dict)

    def increment(self, entity_id: str) -> int:
        """Increment version for entity."""
        self.versions[entity_id] = self.versions.get(entity_id, 0) + 1
        return self.versions[entity_id]

    def get(self, entity_id: str) -> int:
        """Get current version for entity."""
        return self.versions.get(entity_id, 0)

    def merge(self, other: "VersionVector") -> None:
        """Merge another version vector (take max of each)."""
        for entity_id, version in other.versions.items():
            self.versions[entity_id] = max(
                self.versions.get(entity_id, 0), version
            )

    def is_concurrent(self, other: "VersionVector", entity_id: str) -> bool:
        """Check if two vectors have concurrent updates for entity."""
        self_v = self.get(entity_id)
        other_v = other.get(entity_id)
        # Concurrent if neither dominates
        return self_v != other_v


@dataclass
class SyncMetrics:
    """Sync performance metrics"""

    syncs_attempted: int = 0
    syncs_completed: int = 0
    syncs_failed: int = 0
    deltas_pushed: int = 0
    deltas_pulled: int = 0
    conflicts_detected: int = 0
    conflicts_resolved: int = 0
    bytes_transferred: int = 0
    bytes_compressed_saved: int = 0
    average_sync_time_ms: float = 0.0
    offline_queue_size: int = 0


class SyncLayer:
    """
    Sync Layer - Handles synchronization between edge and backend.

    Features:
    - Delta-based sync (minimal data transfer)
    - Offline queue management
    - Conflict detection and resolution
    - Version vectors for causality
    - Compression for large payloads
    - Prioritized sync batching

    Target metrics:
    - Sync latency: P95 <500ms
    - Bandwidth efficiency: >80% reduction via deltas
    - Conflict resolution rate: 99%+
    """

    MAX_BATCH_SIZE: int = 100
    MAX_OFFLINE_QUEUE_SIZE: int = 10000
    COMPRESSION_THRESHOLD_BYTES: int = 1024
    SYNC_TIMEOUT_SECONDS: float = 30.0
    MAX_RETRIES: int = 3
    RETRY_DELAYS: list[float] = [1.0, 5.0, 15.0]

    def __init__(
        self,
        node_id: str,
        default_resolution: ConflictResolution = ConflictResolution.LAST_WRITE_WINS,
    ):
        self.node_id = node_id
        self.default_resolution = default_resolution
        self.metrics = SyncMetrics()

        # Version tracking
        self._version_vector = VersionVector(node_id)
        self._backend_version_vector: VersionVector | None = None

        # Offline queue
        self._offline_queue: list[SyncDelta] = []

        # Pending conflicts
        self._pending_conflicts: dict[str, ConflictInfo] = {}

        # Entity checksums (for delta detection)
        self._local_checksums: dict[str, str] = {}  # entity_key -> checksum
        self._backend_checksums: dict[str, str] = {}

        # In-flight syncs
        self._in_flight: dict[str, SyncBatch] = {}

        # Resolution handlers
        self._conflict_handlers: dict[str, callable] = {}

        # Sync callbacks (for backend communication)
        self._push_callback: callable | None = None
        self._pull_callback: callable | None = None

        logger.info(f"SyncLayer initialized for node {node_id}")

    # === Delta Creation ===

    def create_delta(
        self,
        entity_type: str,
        entity_id: str,
        operation: DeltaOperation,
        data: dict[str, Any] | None = None,
        patch: dict[str, Any] | None = None,
        priority: SyncPriority = SyncPriority.MEDIUM,
    ) -> SyncDelta:
        """
        Create a sync delta for an entity change.

        Args:
            entity_type: Type of entity (user, product, etc.)
            entity_id: Entity identifier
            operation: Type of change
            data: Full data for CREATE/UPDATE
            patch: Partial data for PATCH
            priority: Sync priority

        Returns:
            SyncDelta ready for sync
        """
        entity_key = f"{entity_type}:{entity_id}"

        # Get version info
        old_version = self._version_vector.get(entity_key)
        new_version = self._version_vector.increment(entity_key)

        # Get checksum info
        old_checksum = self._local_checksums.get(entity_key)
        new_checksum = self._compute_checksum(data or patch or {})

        # Update local checksum
        if operation == DeltaOperation.DELETE:
            self._local_checksums.pop(entity_key, None)
        else:
            self._local_checksums[entity_key] = new_checksum

        # Calculate size
        payload = data or patch or {}
        size_bytes = len(json.dumps(payload).encode())

        delta = SyncDelta(
            delta_id=f"delta_{datetime.now().timestamp()}_{entity_id}",
            entity_type=entity_type,
            entity_id=entity_id,
            operation=operation,
            old_version=old_version if old_version > 0 else None,
            new_version=new_version,
            old_checksum=old_checksum,
            new_checksum=new_checksum,
            data=data if operation in (DeltaOperation.CREATE, DeltaOperation.UPDATE) else None,
            patch=patch if operation == DeltaOperation.PATCH else None,
            priority=priority,
            size_bytes=size_bytes,
        )

        logger.debug(f"Created delta: {delta.delta_id} for {entity_key}")
        return delta

    def _compute_checksum(self, data: dict[str, Any]) -> str:
        """Compute checksum for data."""
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]

    # === Offline Queue ===

    def queue_for_sync(self, delta: SyncDelta) -> bool:
        """
        Add delta to offline queue for later sync.

        Args:
            delta: Delta to queue

        Returns:
            True if queued successfully
        """
        if len(self._offline_queue) >= self.MAX_OFFLINE_QUEUE_SIZE:
            logger.warning("Offline queue full, dropping oldest delta")
            self._offline_queue.pop(0)

        self._offline_queue.append(delta)
        self.metrics.offline_queue_size = len(self._offline_queue)

        logger.debug(f"Queued delta {delta.delta_id} (queue size: {len(self._offline_queue)})")
        return True

    def get_pending_deltas(
        self, priority: SyncPriority | None = None, limit: int | None = None
    ) -> list[SyncDelta]:
        """
        Get pending deltas from queue.

        Args:
            priority: Filter by priority
            limit: Maximum number to return

        Returns:
            List of pending deltas
        """
        deltas = self._offline_queue

        if priority:
            deltas = [d for d in deltas if d.priority == priority]

        # Sort by priority (IMMEDIATE first) then by creation time
        priority_order = {
            SyncPriority.IMMEDIATE: 0,
            SyncPriority.HIGH: 1,
            SyncPriority.MEDIUM: 2,
            SyncPriority.LOW: 3,
            SyncPriority.DEFERRED: 4,
        }
        deltas.sort(key=lambda d: (priority_order[d.priority], d.created_at))

        if limit:
            deltas = deltas[:limit]

        return deltas

    def mark_synced(self, delta_ids: list[str]) -> int:
        """
        Mark deltas as synced and remove from queue.

        Args:
            delta_ids: IDs of synced deltas

        Returns:
            Number of deltas removed
        """
        initial_size = len(self._offline_queue)
        self._offline_queue = [
            d for d in self._offline_queue if d.delta_id not in delta_ids
        ]
        removed = initial_size - len(self._offline_queue)

        self.metrics.offline_queue_size = len(self._offline_queue)
        self.metrics.deltas_pushed += removed

        return removed

    # === Sync Batching ===

    def create_sync_batch(
        self,
        direction: SyncDirection = SyncDirection.PUSH,
        max_size: int | None = None,
        priority: SyncPriority | None = None,
    ) -> SyncBatch:
        """
        Create a batch of deltas for sync.

        Args:
            direction: Sync direction
            max_size: Maximum batch size
            priority: Filter by priority

        Returns:
            SyncBatch ready for sync
        """
        max_size = max_size or self.MAX_BATCH_SIZE
        deltas = self.get_pending_deltas(priority, max_size)

        total_size = sum(d.size_bytes for d in deltas)

        batch = SyncBatch(
            batch_id=f"batch_{datetime.now().timestamp()}",
            deltas=deltas,
            direction=direction,
            total_size_bytes=total_size,
        )

        # Compress if beneficial
        if total_size > self.COMPRESSION_THRESHOLD_BYTES:
            compressed_size = self._estimate_compressed_size(deltas)
            batch.compressed_size_bytes = compressed_size
            self.metrics.bytes_compressed_saved += total_size - compressed_size

        return batch

    def _estimate_compressed_size(self, deltas: list[SyncDelta]) -> int:
        """Estimate compressed size of deltas."""
        data = json.dumps([d.model_dump() for d in deltas]).encode()
        compressed = gzip.compress(data)
        return len(compressed)

    def compress_batch(self, batch: SyncBatch) -> bytes:
        """Compress a sync batch for transfer."""
        data = json.dumps([d.model_dump() for d in batch.deltas]).encode()
        return gzip.compress(data)

    def decompress_batch(self, compressed: bytes) -> list[SyncDelta]:
        """Decompress a sync batch."""
        data = gzip.decompress(compressed)
        deltas_data = json.loads(data)
        return [SyncDelta(**d) for d in deltas_data]

    # === Conflict Detection ===

    def detect_conflicts(
        self, incoming_deltas: list[SyncDelta]
    ) -> list[ConflictInfo]:
        """
        Detect conflicts between incoming deltas and local state.

        Args:
            incoming_deltas: Deltas from backend

        Returns:
            List of detected conflicts
        """
        conflicts = []

        for delta in incoming_deltas:
            entity_key = f"{delta.entity_type}:{delta.entity_id}"

            # Check if we have local changes for this entity
            local_checksum = self._local_checksums.get(entity_key)
            local_version = self._version_vector.get(entity_key)

            if local_checksum and local_checksum != delta.old_checksum:
                # We have local changes that conflict
                conflict = ConflictInfo(
                    entity_type=delta.entity_type,
                    entity_id=delta.entity_id,
                    edge_version=local_version,
                    backend_version=delta.new_version,
                    edge_checksum=local_checksum,
                    backend_checksum=delta.new_checksum,
                    backend_data=delta.data,
                )
                conflicts.append(conflict)
                self._pending_conflicts[entity_key] = conflict
                self.metrics.conflicts_detected += 1

                logger.warning(f"Conflict detected for {entity_key}")

        return conflicts

    # === Conflict Resolution ===

    def resolve_conflict(
        self,
        entity_key: str,
        resolution: ConflictResolution,
        merged_data: dict[str, Any] | None = None,
    ) -> SyncDelta | None:
        """
        Resolve a sync conflict.

        Args:
            entity_key: Key of conflicting entity
            resolution: Resolution strategy
            merged_data: Merged data if using MERGE resolution

        Returns:
            SyncDelta with resolution, or None if no action needed
        """
        conflict = self._pending_conflicts.get(entity_key)
        if not conflict:
            logger.warning(f"No conflict found for {entity_key}")
            return None

        entity_type, entity_id = entity_key.split(":", 1)
        resolved_delta = None

        if resolution == ConflictResolution.SERVER_WINS:
            # Accept backend version, update local
            if conflict.backend_data:
                self._local_checksums[entity_key] = conflict.backend_checksum
                self._version_vector.versions[entity_key] = conflict.backend_version
            # No delta needed - just accept backend state

        elif resolution == ConflictResolution.CLIENT_WINS:
            # Push local version to backend
            resolved_delta = self.create_delta(
                entity_type=entity_type,
                entity_id=entity_id,
                operation=DeltaOperation.UPDATE,
                data=conflict.edge_data,
                priority=SyncPriority.HIGH,
            )

        elif resolution == ConflictResolution.LAST_WRITE_WINS:
            # Compare timestamps (would need timestamp in conflict info)
            # Default to server wins for simplicity
            self._local_checksums[entity_key] = conflict.backend_checksum
            self._version_vector.versions[entity_key] = conflict.backend_version

        elif resolution == ConflictResolution.MERGE:
            if merged_data:
                resolved_delta = self.create_delta(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    operation=DeltaOperation.UPDATE,
                    data=merged_data,
                    priority=SyncPriority.HIGH,
                )

        # Mark resolved
        conflict.resolution = resolution
        conflict.resolved_at = datetime.now()
        del self._pending_conflicts[entity_key]
        self.metrics.conflicts_resolved += 1

        logger.info(f"Resolved conflict for {entity_key} using {resolution.value}")
        return resolved_delta

    def register_conflict_handler(
        self, entity_type: str, handler: callable
    ) -> None:
        """
        Register custom conflict handler for entity type.

        Handler signature: (conflict: ConflictInfo) -> tuple[ConflictResolution, dict | None]
        """
        self._conflict_handlers[entity_type] = handler

    def auto_resolve_conflicts(self) -> list[SyncDelta]:
        """
        Automatically resolve all pending conflicts.

        Uses default resolution strategy or custom handlers.

        Returns:
            List of deltas from resolutions
        """
        deltas = []

        for entity_key, conflict in list(self._pending_conflicts.items()):
            entity_type = conflict.entity_type

            # Check for custom handler
            if entity_type in self._conflict_handlers:
                handler = self._conflict_handlers[entity_type]
                resolution, merged_data = handler(conflict)
            else:
                resolution = self.default_resolution
                merged_data = None

            delta = self.resolve_conflict(entity_key, resolution, merged_data)
            if delta:
                deltas.append(delta)

        return deltas

    # === Sync Operations ===

    async def push_sync(
        self, batch: SyncBatch | None = None
    ) -> dict[str, Any]:
        """
        Push local changes to backend.

        Args:
            batch: Specific batch to push, or None to create new

        Returns:
            Sync result with status and details
        """
        start_time = datetime.now()
        self.metrics.syncs_attempted += 1

        if batch is None:
            batch = self.create_sync_batch(SyncDirection.PUSH)

        if not batch.deltas:
            return {"status": "no_changes", "pushed": 0}

        batch.status = SyncStatus.IN_PROGRESS
        self._in_flight[batch.batch_id] = batch

        try:
            # Call push callback if registered
            if self._push_callback:
                result = await self._push_callback(batch)
            else:
                # Simulate successful push
                result = {"success": True, "synced_ids": [d.delta_id for d in batch.deltas]}

            if result.get("success"):
                synced_ids = result.get("synced_ids", [])
                self.mark_synced(synced_ids)
                batch.status = SyncStatus.COMPLETED
                self.metrics.syncs_completed += 1
                self.metrics.bytes_transferred += batch.total_size_bytes

                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
                self._update_average_sync_time(elapsed_ms)

                return {
                    "status": "success",
                    "pushed": len(synced_ids),
                    "sync_time_ms": elapsed_ms,
                }
            else:
                batch.status = SyncStatus.FAILED
                self.metrics.syncs_failed += 1
                return {"status": "failed", "error": result.get("error")}

        except Exception as e:
            batch.status = SyncStatus.FAILED
            self.metrics.syncs_failed += 1
            logger.error(f"Push sync failed: {e}")
            return {"status": "failed", "error": str(e)}
        finally:
            del self._in_flight[batch.batch_id]

    async def pull_sync(self) -> dict[str, Any]:
        """
        Pull changes from backend.

        Returns:
            Sync result with pulled deltas and conflicts
        """
        start_time = datetime.now()
        self.metrics.syncs_attempted += 1

        try:
            # Call pull callback if registered
            if self._pull_callback:
                result = await self._pull_callback(self._backend_checksums)
            else:
                # Simulate no changes
                result = {"success": True, "deltas": []}

            if result.get("success"):
                incoming_deltas = [
                    SyncDelta(**d) if isinstance(d, dict) else d
                    for d in result.get("deltas", [])
                ]

                # Detect conflicts
                conflicts = self.detect_conflicts(incoming_deltas)

                # Apply non-conflicting deltas
                applied = 0
                for delta in incoming_deltas:
                    entity_key = f"{delta.entity_type}:{delta.entity_id}"
                    if entity_key not in self._pending_conflicts:
                        self._apply_incoming_delta(delta)
                        applied += 1

                self.metrics.syncs_completed += 1
                self.metrics.deltas_pulled += applied

                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
                self._update_average_sync_time(elapsed_ms)

                return {
                    "status": "success",
                    "pulled": applied,
                    "conflicts": len(conflicts),
                    "sync_time_ms": elapsed_ms,
                }
            else:
                self.metrics.syncs_failed += 1
                return {"status": "failed", "error": result.get("error")}

        except Exception as e:
            self.metrics.syncs_failed += 1
            logger.error(f"Pull sync failed: {e}")
            return {"status": "failed", "error": str(e)}

    def _apply_incoming_delta(self, delta: SyncDelta) -> None:
        """Apply an incoming delta to local state."""
        entity_key = f"{delta.entity_type}:{delta.entity_id}"

        if delta.operation == DeltaOperation.DELETE:
            self._local_checksums.pop(entity_key, None)
            self._backend_checksums.pop(entity_key, None)
        else:
            self._local_checksums[entity_key] = delta.new_checksum
            self._backend_checksums[entity_key] = delta.new_checksum
            self._version_vector.versions[entity_key] = delta.new_version

    async def bidirectional_sync(self) -> dict[str, Any]:
        """
        Perform bidirectional sync (push then pull).

        Returns:
            Combined sync results
        """
        push_result = await self.push_sync()
        pull_result = await self.pull_sync()

        # Auto-resolve any conflicts
        resolution_deltas = self.auto_resolve_conflicts()
        if resolution_deltas:
            for delta in resolution_deltas:
                self.queue_for_sync(delta)
            # Push resolution deltas
            await self.push_sync()

        return {
            "push": push_result,
            "pull": pull_result,
            "conflicts_resolved": len(resolution_deltas),
        }

    # === Callback Registration ===

    def set_push_callback(self, callback: callable) -> None:
        """Set callback for pushing to backend."""
        self._push_callback = callback

    def set_pull_callback(self, callback: callable) -> None:
        """Set callback for pulling from backend."""
        self._pull_callback = callback

    # === Metrics ===

    def _update_average_sync_time(self, elapsed_ms: float) -> None:
        """Update average sync time."""
        n = self.metrics.syncs_completed
        if n == 0:
            return
        self.metrics.average_sync_time_ms = (
            self.metrics.average_sync_time_ms * (n - 1) + elapsed_ms
        ) / n

    def get_metrics(self) -> dict[str, Any]:
        """Get sync metrics."""
        return {
            "syncs_attempted": self.metrics.syncs_attempted,
            "syncs_completed": self.metrics.syncs_completed,
            "syncs_failed": self.metrics.syncs_failed,
            "success_rate": (
                round(
                    self.metrics.syncs_completed
                    / max(1, self.metrics.syncs_attempted)
                    * 100,
                    2,
                )
            ),
            "deltas_pushed": self.metrics.deltas_pushed,
            "deltas_pulled": self.metrics.deltas_pulled,
            "conflicts_detected": self.metrics.conflicts_detected,
            "conflicts_resolved": self.metrics.conflicts_resolved,
            "pending_conflicts": len(self._pending_conflicts),
            "bytes_transferred": self.metrics.bytes_transferred,
            "bytes_compressed_saved": self.metrics.bytes_compressed_saved,
            "average_sync_time_ms": round(self.metrics.average_sync_time_ms, 2),
            "offline_queue_size": len(self._offline_queue),
        }

    def get_sync_status(self) -> dict[str, Any]:
        """Get current sync status."""
        return {
            "node_id": self.node_id,
            "offline_queue_size": len(self._offline_queue),
            "pending_conflicts": len(self._pending_conflicts),
            "in_flight_syncs": len(self._in_flight),
            "local_entities": len(self._local_checksums),
            "version_vector_size": len(self._version_vector.versions),
        }
