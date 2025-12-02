"""
Base Edge Agent Class with Hybrid-Awareness Capabilities
Enterprise-grade foundation for edge-side DevSkyy AI agents

Design Principle: Every agent is "hybrid-aware" — knows WHAT runs WHERE and WHY

Edge Layer Characteristics:
- Instant feedback (<50ms latency target)
- Privacy-preserving (sensitive data stays local)
- Offline-capable (queues operations when disconnected)
- Bandwidth-efficient (delta sync, compression)
- Predictive pre-computation (anticipate user needs)
- User-specific personalization (local preferences)

Per CLAUDE.md Truth Protocol:
- Rule #1: All APIs verified against specifications
- Rule #7: Pydantic validation for all inputs
- Rule #9: Google-style docstrings with type hints
- Rule #10: Errors logged, processing continues
"""

from abc import ABC, abstractmethod
import asyncio
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import logging
from typing import Any

from agent.modules.base_agent import (
    AgentMetrics,
    AgentStatus,
    BaseAgent,
    HealthMetrics,
    Issue,
    SeverityLevel,
)


logger = logging.getLogger(__name__)


class ExecutionLocation(Enum):
    """Where an operation should execute"""

    EDGE = "edge"  # Local execution for speed/privacy
    BACKEND = "backend"  # Cloud execution for heavy compute
    HYBRID = "hybrid"  # Can run on either based on context


class SyncPriority(Enum):
    """Priority for syncing data to backend"""

    IMMEDIATE = "immediate"  # Sync now (critical data)
    HIGH = "high"  # Sync within 1 second
    MEDIUM = "medium"  # Sync within 30 seconds
    LOW = "low"  # Sync when convenient (batch)
    DEFERRED = "deferred"  # Only sync when online


class OfflineCapability(Enum):
    """Agent's ability to work offline"""

    FULL = "full"  # Fully functional offline
    PARTIAL = "partial"  # Some features work offline
    NONE = "none"  # Requires backend connection


@dataclass
class EdgeMetrics(AgentMetrics):
    """Extended metrics for edge agents"""

    local_operations: int = 0
    backend_delegations: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    offline_queue_size: int = 0
    sync_operations: int = 0
    average_latency_ms: float = 0.0
    bandwidth_saved_bytes: int = 0
    privacy_preserving_ops: int = 0


@dataclass
class OperationContext:
    """Context for deciding where to execute an operation"""

    operation_type: str
    data_size_bytes: int = 0
    requires_gpu: bool = False
    requires_llm: bool = False
    privacy_sensitive: bool = False
    latency_critical: bool = False
    user_preference: ExecutionLocation | None = None
    network_available: bool = True
    bandwidth_limited: bool = False


@dataclass
class SyncItem:
    """Item queued for synchronization with backend"""

    item_id: str
    operation: str
    data: dict[str, Any]
    priority: SyncPriority
    created_at: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    max_retries: int = 3
    checksum: str = ""

    def __post_init__(self):
        if not self.checksum:
            self.checksum = hashlib.sha256(str(self.data).encode()).hexdigest()[:16]


@dataclass
class EdgeHealthMetrics(HealthMetrics):
    """Extended health metrics for edge agents"""

    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    latency_p99_ms: float = 0.0
    offline_mode_active: bool = False
    sync_queue_depth: int = 0
    local_storage_mb: float = 0.0


class BaseEdgeAgent(BaseAgent, ABC):
    """
    Base class for edge-side agents with hybrid-awareness.

    Edge agents are designed for:
    - Ultra-low latency (<50ms target)
    - Privacy-preserving local computation
    - Offline-first operation with sync
    - Bandwidth-efficient communication
    - Predictive pre-computation

    All edge agents should inherit from this class to get:
    - Hybrid execution routing (edge vs backend)
    - Offline queue management
    - Delta synchronization
    - Local caching with TTL
    - Privacy-aware data handling
    """

    # Class-level configuration for hybrid routing
    EDGE_LATENCY_TARGET_MS: float = 50.0
    BACKEND_THRESHOLD_SIZE_BYTES: int = 100_000  # 100KB
    MAX_OFFLINE_QUEUE_SIZE: int = 1000
    SYNC_BATCH_SIZE: int = 50

    def __init__(
        self,
        agent_name: str,
        version: str = "1.0.0",
        offline_capability: OfflineCapability = OfflineCapability.PARTIAL,
    ):
        super().__init__(agent_name, version)

        # Edge-specific attributes
        self.offline_capability = offline_capability
        self.is_online = True
        self.edge_metrics = EdgeMetrics()
        self.edge_health = EdgeHealthMetrics()

        # Offline queue for sync
        self.offline_queue: deque[SyncItem] = deque(maxlen=self.MAX_OFFLINE_QUEUE_SIZE)
        self.pending_sync: dict[str, SyncItem] = {}

        # Local cache with TTL
        self._local_cache: dict[str, tuple[Any, datetime, float]] = {}

        # Latency tracking
        self._latency_history: list[float] = []

        # Operation routing rules
        self._routing_rules: dict[str, ExecutionLocation] = {}

        logger.info(
            f"Edge Agent {self.agent_name} v{self.version} initializing "
            f"(offline_capability={offline_capability.value})"
        )

    @abstractmethod
    async def execute_local(self, operation: str, **kwargs) -> dict[str, Any]:
        """
        Execute operation locally on edge.

        Must be implemented by subclasses to define edge-local operations.
        Should complete in <50ms for latency-critical operations.

        Args:
            operation: The operation to perform
            **kwargs: Operation-specific parameters

        Returns:
            Operation result dictionary
        """

    @abstractmethod
    def get_routing_rules(self) -> dict[str, ExecutionLocation]:
        """
        Define routing rules for this agent's operations.

        Must be implemented by subclasses to specify which operations
        should run where.

        Returns:
            Dict mapping operation names to execution locations
        """

    # === Hybrid Routing ===

    def should_execute_locally(self, context: OperationContext) -> bool:
        """
        Determine if operation should execute on edge or delegate to backend.

        Decision factors:
        1. User preference (if specified)
        2. Privacy requirements (sensitive data stays local)
        3. Latency requirements (critical ops stay local)
        4. Network availability (offline = local)
        5. Data size (large = backend)
        6. Compute requirements (GPU/LLM = backend)

        Args:
            context: Operation context with decision factors

        Returns:
            True if should execute locally, False for backend
        """
        # Check routing rules first
        if context.operation_type in self._routing_rules:
            location = self._routing_rules[context.operation_type]
            if location == ExecutionLocation.EDGE:
                return True
            if location == ExecutionLocation.BACKEND:
                return False
            # HYBRID continues to dynamic decision

        # User preference takes priority
        if context.user_preference:
            return context.user_preference == ExecutionLocation.EDGE

        # Privacy-sensitive data must stay local
        if context.privacy_sensitive:
            logger.debug(f"Privacy-sensitive operation: executing locally")
            self.edge_metrics.privacy_preserving_ops += 1
            return True

        # Latency-critical must stay local
        if context.latency_critical:
            logger.debug(f"Latency-critical operation: executing locally")
            return True

        # No network = must be local
        if not context.network_available or not self.is_online:
            logger.debug(f"Offline mode: queuing for later sync")
            return True

        # Heavy compute requirements = backend
        if context.requires_gpu or context.requires_llm:
            logger.debug(f"Heavy compute required: delegating to backend")
            return False

        # Large data = backend
        if context.data_size_bytes > self.BACKEND_THRESHOLD_SIZE_BYTES:
            logger.debug(
                f"Large data ({context.data_size_bytes} bytes): delegating to backend"
            )
            return False

        # Bandwidth-limited = prefer local
        if context.bandwidth_limited:
            return True

        # Default: local for speed
        return True

    async def execute(
        self, operation: str, context: OperationContext | None = None, **kwargs
    ) -> dict[str, Any]:
        """
        Execute operation with hybrid routing.

        Automatically routes to edge or backend based on context.

        Args:
            operation: Operation to perform
            context: Execution context for routing decision
            **kwargs: Operation parameters

        Returns:
            Operation result
        """
        start_time = datetime.now()

        if context is None:
            context = OperationContext(operation_type=operation)

        try:
            if self.should_execute_locally(context):
                result = await self._execute_on_edge(operation, **kwargs)
                self.edge_metrics.local_operations += 1
            else:
                result = await self._delegate_to_backend(operation, context, **kwargs)
                self.edge_metrics.backend_delegations += 1

            # Track latency
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            self._record_latency(elapsed_ms)

            return result

        except Exception as e:
            if not self.is_online and self.offline_capability != OfflineCapability.NONE:
                # Queue for later sync
                await self._queue_for_sync(operation, kwargs, SyncPriority.MEDIUM)
                return {
                    "status": "queued",
                    "message": "Operation queued for sync when online",
                    "queue_size": len(self.offline_queue),
                }
            raise

    async def _execute_on_edge(self, operation: str, **kwargs) -> dict[str, Any]:
        """Execute operation locally with latency tracking."""
        start = datetime.now()
        result = await self.execute_local(operation, **kwargs)
        elapsed = (datetime.now() - start).total_seconds() * 1000

        if elapsed > self.EDGE_LATENCY_TARGET_MS:
            logger.warning(
                f"Edge operation {operation} exceeded latency target: "
                f"{elapsed:.2f}ms > {self.EDGE_LATENCY_TARGET_MS}ms"
            )

        return result

    async def _delegate_to_backend(
        self, operation: str, context: OperationContext, **kwargs
    ) -> dict[str, Any]:
        """
        Delegate operation to backend.

        Override in subclasses to implement actual backend communication.
        """
        raise NotImplementedError(
            "Backend delegation must be implemented by subclass or orchestrator"
        )

    # === Offline Queue Management ===

    async def _queue_for_sync(
        self, operation: str, data: dict[str, Any], priority: SyncPriority
    ) -> str:
        """
        Queue operation for later synchronization with backend.

        Args:
            operation: Operation type
            data: Operation data
            priority: Sync priority

        Returns:
            Queue item ID
        """
        item_id = f"{operation}_{datetime.now().timestamp()}"
        item = SyncItem(
            item_id=item_id, operation=operation, data=data, priority=priority
        )

        self.offline_queue.append(item)
        self.edge_metrics.offline_queue_size = len(self.offline_queue)

        logger.debug(f"Queued operation {item_id} for sync (priority={priority.value})")
        return item_id

    async def process_sync_queue(self) -> dict[str, Any]:
        """
        Process offline queue and sync with backend.

        Should be called when network becomes available.

        Returns:
            Sync results with success/failure counts
        """
        if not self.is_online:
            return {"status": "offline", "processed": 0}

        results = {"processed": 0, "failed": 0, "remaining": len(self.offline_queue)}

        # Process by priority
        priority_order = [
            SyncPriority.IMMEDIATE,
            SyncPriority.HIGH,
            SyncPriority.MEDIUM,
            SyncPriority.LOW,
            SyncPriority.DEFERRED,
        ]

        for priority in priority_order:
            batch = [
                item
                for item in self.offline_queue
                if item.priority == priority
            ][:self.SYNC_BATCH_SIZE]

            for item in batch:
                try:
                    await self._sync_item(item)
                    self.offline_queue.remove(item)
                    results["processed"] += 1
                    self.edge_metrics.sync_operations += 1
                except Exception as e:
                    item.retry_count += 1
                    if item.retry_count >= item.max_retries:
                        self.offline_queue.remove(item)
                        results["failed"] += 1
                        logger.error(f"Sync failed permanently for {item.item_id}: {e}")
                    else:
                        logger.warning(
                            f"Sync retry {item.retry_count}/{item.max_retries} "
                            f"for {item.item_id}"
                        )

        results["remaining"] = len(self.offline_queue)
        self.edge_metrics.offline_queue_size = results["remaining"]
        return results

    async def _sync_item(self, item: SyncItem) -> dict[str, Any]:
        """
        Sync individual item to backend.

        Override in subclasses for actual sync implementation.
        """
        raise NotImplementedError("Sync must be implemented by subclass or orchestrator")

    # === Local Caching ===

    def cache_locally(
        self, key: str, value: Any, ttl_seconds: float = 300.0
    ) -> None:
        """
        Cache data locally with TTL.

        Args:
            key: Cache key
            value: Data to cache
            ttl_seconds: Time-to-live in seconds
        """
        self._local_cache[key] = (value, datetime.now(), ttl_seconds)
        logger.debug(f"Cached {key} locally (TTL={ttl_seconds}s)")

    def get_from_cache(self, key: str) -> tuple[Any, bool]:
        """
        Get data from local cache.

        Args:
            key: Cache key

        Returns:
            Tuple of (value, hit) where hit is True if cache hit
        """
        if key not in self._local_cache:
            self.edge_metrics.cache_misses += 1
            return None, False

        value, cached_at, ttl = self._local_cache[key]
        age = (datetime.now() - cached_at).total_seconds()

        if age > ttl:
            # Expired
            del self._local_cache[key]
            self.edge_metrics.cache_misses += 1
            return None, False

        self.edge_metrics.cache_hits += 1
        return value, True

    def invalidate_cache(self, pattern: str | None = None) -> int:
        """
        Invalidate cached entries.

        Args:
            pattern: Key pattern to match (None = clear all)

        Returns:
            Number of entries invalidated
        """
        if pattern is None:
            count = len(self._local_cache)
            self._local_cache.clear()
            return count

        keys_to_remove = [k for k in self._local_cache if pattern in k]
        for key in keys_to_remove:
            del self._local_cache[key]
        return len(keys_to_remove)

    # === Network Status ===

    async def set_online_status(self, is_online: bool) -> None:
        """
        Update network availability status.

        Triggers sync when coming back online.

        Args:
            is_online: Whether network is available
        """
        was_offline = not self.is_online
        self.is_online = is_online
        self.edge_health.offline_mode_active = not is_online

        if is_online and was_offline:
            logger.info(f"Network restored for {self.agent_name}, processing sync queue")
            await self.process_sync_queue()

    # === Latency Tracking ===

    def _record_latency(self, latency_ms: float) -> None:
        """Record operation latency for percentile calculations."""
        self._latency_history.append(latency_ms)
        if len(self._latency_history) > 1000:
            self._latency_history.pop(0)

        # Update metrics
        if len(self._latency_history) >= 10:
            sorted_latencies = sorted(self._latency_history)
            n = len(sorted_latencies)
            self.edge_health.latency_p50_ms = sorted_latencies[int(n * 0.50)]
            self.edge_health.latency_p95_ms = sorted_latencies[int(n * 0.95)]
            self.edge_health.latency_p99_ms = sorted_latencies[int(n * 0.99)]

        self.edge_metrics.average_latency_ms = sum(self._latency_history) / len(
            self._latency_history
        )

    # === Health & Diagnostics ===

    async def health_check(self) -> dict[str, Any]:
        """
        Comprehensive health check including edge-specific metrics.

        Returns:
            Health status with edge metrics
        """
        base_health = await super().health_check()

        # Add edge-specific health data
        base_health["edge_metrics"] = {
            "local_operations": self.edge_metrics.local_operations,
            "backend_delegations": self.edge_metrics.backend_delegations,
            "cache_hit_ratio": self._calculate_cache_hit_ratio(),
            "offline_queue_size": len(self.offline_queue),
            "sync_pending": len(self.pending_sync),
            "privacy_preserving_ops": self.edge_metrics.privacy_preserving_ops,
        }

        base_health["latency"] = {
            "average_ms": round(self.edge_metrics.average_latency_ms, 2),
            "p50_ms": round(self.edge_health.latency_p50_ms, 2),
            "p95_ms": round(self.edge_health.latency_p95_ms, 2),
            "p99_ms": round(self.edge_health.latency_p99_ms, 2),
            "target_ms": self.EDGE_LATENCY_TARGET_MS,
            "meeting_target": (
                self.edge_health.latency_p95_ms <= self.EDGE_LATENCY_TARGET_MS
            ),
        }

        base_health["network"] = {
            "online": self.is_online,
            "offline_capability": self.offline_capability.value,
        }

        return base_health

    def _calculate_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total = self.edge_metrics.cache_hits + self.edge_metrics.cache_misses
        if total == 0:
            return 0.0
        return round((self.edge_metrics.cache_hits / total) * 100, 2)

    # === BaseAgent Implementation ===

    async def initialize(self) -> bool:
        """Initialize edge agent."""
        try:
            self._routing_rules = self.get_routing_rules()
            self.status = AgentStatus.HEALTHY
            logger.info(f"Edge agent {self.agent_name} initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize edge agent {self.agent_name}: {e}")
            self.status = AgentStatus.FAILED
            return False

    async def execute_core_function(self, **kwargs) -> dict[str, Any]:
        """Execute core function via hybrid routing."""
        operation = kwargs.pop("operation", "default")
        context = kwargs.pop("context", None)
        return await self.execute(operation, context, **kwargs)
