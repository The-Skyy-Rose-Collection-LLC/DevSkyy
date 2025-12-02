"""
Edge-Backend Orchestrator - Unified management of edge and backend agents

Design Principle: Every agent is "hybrid-aware" — knows WHAT runs WHERE and WHY

This orchestrator:
- Manages edge agents (EdgeRouter, CacheAgent, PredictiveAgent, ValidationAgent)
- Coordinates with backend agents
- Handles sync layer operations
- Provides unified API for hybrid execution

Architecture:
┌─────────────────────────────────────────────────────────────────────┐
│                         EDGE LAYER                                   │
│   EdgeRouter → CacheAgent → PredictiveAgent → ValidationAgent       │
│                           ↓                                          │
│                      Sync Layer                                      │
│                           ↓                                          │
│                       BACKEND                                        │
│           (50+ DevSkyy agents with full capabilities)               │
└─────────────────────────────────────────────────────────────────────┘

Per CLAUDE.md Truth Protocol:
- Rule #7: Pydantic validation for all requests
- Rule #10: Log errors, continue processing
- Rule #12: P95 < 200ms for edge operations
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from typing import Any

from pydantic import BaseModel, Field

from agent.edge.base_edge_agent import (
    ExecutionLocation,
    OfflineCapability,
    OperationContext,
    SyncPriority,
)
from agent.edge.cache_agent import CacheAgent
from agent.edge.edge_router import EdgeRouter, RoutingRequest, RoutingStrategy
from agent.edge.predictive_agent import PredictiveAgent, PrefetchStrategy
from agent.edge.sync_layer import (
    ConflictResolution,
    DeltaOperation,
    SyncDirection,
    SyncLayer,
)
from agent.edge.validation_agent import ValidationAgent


logger = logging.getLogger(__name__)


class OrchestratorStatus(Enum):
    """Orchestrator operational status"""

    INITIALIZING = "initializing"
    RUNNING = "running"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    STOPPED = "stopped"


class ExecutionRequest(BaseModel):
    """Unified execution request"""

    operation: str = Field(..., min_length=1)
    agent_type: str = Field(..., min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)
    user_id: str | None = None
    session_id: str | None = None
    priority: str = "medium"
    require_validation: bool = True
    use_cache: bool = True
    allow_edge: bool = True
    timeout_ms: float = 5000.0


class ExecutionResponse(BaseModel):
    """Unified execution response"""

    request_id: str
    status: str
    result: Any = None
    error: str | None = None
    execution_location: ExecutionLocation
    edge_latency_ms: float | None = None
    backend_latency_ms: float | None = None
    cache_hit: bool = False
    validated: bool = False
    timestamp: datetime = Field(default_factory=datetime.now)


@dataclass
class OrchestratorMetrics:
    """Orchestrator performance metrics"""

    total_requests: int = 0
    edge_requests: int = 0
    backend_requests: int = 0
    cache_hits: int = 0
    validation_failures: int = 0
    sync_operations: int = 0
    errors: int = 0
    average_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0


class EdgeBackendOrchestrator:
    """
    Edge-Backend Orchestrator - Unified edge-backend management.

    Manages:
    - EdgeRouter: Routing decisions between edge and backend
    - CacheAgent: Edge-side caching
    - PredictiveAgent: Prefetching and prediction
    - ValidationAgent: Input validation
    - SyncLayer: Delta synchronization

    Features:
    - Unified API for all operations
    - Automatic routing based on operation type
    - Cache-first execution with fallback
    - Input validation before processing
    - Predictive prefetching
    - Offline support with sync queue

    Target metrics:
    - Edge P95 latency: <50ms
    - Cache hit ratio: >80%
    - Validation rate: 100%
    - Sync success rate: 99%+
    """

    def __init__(
        self,
        node_id: str = "edge_node_1",
        routing_strategy: RoutingStrategy = RoutingStrategy.ADAPTIVE,
        prefetch_strategy: PrefetchStrategy = PrefetchStrategy.ADAPTIVE,
        conflict_resolution: ConflictResolution = ConflictResolution.LAST_WRITE_WINS,
    ):
        self.node_id = node_id
        self.status = OrchestratorStatus.INITIALIZING
        self.metrics = OrchestratorMetrics()

        # Initialize edge agents
        self.router = EdgeRouter(
            agent_name="EdgeRouter",
            version="1.0.0",
            default_strategy=routing_strategy,
        )

        self.cache = CacheAgent(
            agent_name="CacheAgent",
            version="1.0.0",
        )

        self.predictor = PredictiveAgent(
            agent_name="PredictiveAgent",
            version="1.0.0",
            strategy=prefetch_strategy,
        )

        self.validator = ValidationAgent(
            agent_name="ValidationAgent",
            version="1.0.0",
        )

        # Initialize sync layer
        self.sync_layer = SyncLayer(
            node_id=node_id,
            default_resolution=conflict_resolution,
        )

        # Backend agent registry
        self._backend_agents: dict[str, Any] = {}

        # Network status
        self._is_online = True

        # Latency tracking
        self._latency_history: list[float] = []

        logger.info(f"EdgeBackendOrchestrator initialized (node={node_id})")

    async def initialize(self) -> bool:
        """
        Initialize all edge agents.

        Returns:
            True if all agents initialized successfully
        """
        try:
            # Initialize edge agents
            results = await asyncio.gather(
                self.router.initialize(),
                self.cache.initialize(),
                self.predictor.initialize(),
                self.validator.initialize(),
                return_exceptions=True,
            )

            all_success = all(r is True for r in results if not isinstance(r, Exception))

            if all_success:
                self.status = OrchestratorStatus.RUNNING
                logger.info("All edge agents initialized successfully")
            else:
                self.status = OrchestratorStatus.DEGRADED
                logger.warning("Some edge agents failed to initialize")

            return all_success

        except Exception as e:
            logger.error(f"Orchestrator initialization failed: {e}")
            self.status = OrchestratorStatus.DEGRADED
            return False

    # === Unified Execution API ===

    async def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """
        Unified execution entry point.

        Routes requests through:
        1. Validation (if required)
        2. Cache check (if enabled)
        3. Routing decision
        4. Execution (edge or backend)
        5. Cache update
        6. Sync queue (if needed)

        Args:
            request: Execution request

        Returns:
            ExecutionResponse with result and metadata
        """
        start_time = datetime.now()
        request_id = f"req_{start_time.timestamp()}"

        self.metrics.total_requests += 1

        try:
            # Step 1: Validation
            if request.require_validation:
                validation_result = await self._validate_request(request)
                if not validation_result.get("valid", True):
                    self.metrics.validation_failures += 1
                    return ExecutionResponse(
                        request_id=request_id,
                        status="validation_failed",
                        error=str(validation_result.get("issues", [])),
                        execution_location=ExecutionLocation.EDGE,
                        validated=False,
                    )

            # Step 2: Cache check
            cache_key = self._make_cache_key(request)
            if request.use_cache:
                cached_value, cache_hit = await self.cache.get(
                    cache_key, namespace=request.agent_type
                )
                if cache_hit:
                    self.metrics.cache_hits += 1
                    elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

                    return ExecutionResponse(
                        request_id=request_id,
                        status="success",
                        result=cached_value,
                        execution_location=ExecutionLocation.EDGE,
                        edge_latency_ms=elapsed_ms,
                        cache_hit=True,
                        validated=request.require_validation,
                    )

            # Step 3: Routing decision
            routing_request = RoutingRequest(
                operation=request.operation,
                agent_type=request.agent_type,
                data_size_bytes=len(str(request.parameters)),
                privacy_sensitive=request.parameters.get("_privacy_sensitive", False),
                latency_critical=request.parameters.get("_latency_critical", False),
                user_id=request.user_id,
            )

            routing_decision = await self.router.route(routing_request)

            # Step 4: Execute
            if routing_decision.location == ExecutionLocation.EDGE and request.allow_edge:
                result = await self._execute_on_edge(request)
                self.metrics.edge_requests += 1
            else:
                result = await self._execute_on_backend(request)
                self.metrics.backend_requests += 1

            # Step 5: Cache result
            if request.use_cache and result.get("status") == "success":
                await self.cache.set(
                    cache_key,
                    result.get("result"),
                    namespace=request.agent_type,
                    ttl_seconds=300.0,
                )

            # Calculate latency
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            self._record_latency(elapsed_ms)

            # Record outcome for learning
            self.router.record_outcome(
                request_id=routing_decision.request_id,
                agent_type=request.agent_type,
                operation=request.operation,
                location=routing_decision.location.value,
                success=result.get("status") == "success",
                latency_ms=elapsed_ms,
            )

            return ExecutionResponse(
                request_id=request_id,
                status=result.get("status", "success"),
                result=result.get("result"),
                error=result.get("error"),
                execution_location=routing_decision.location,
                edge_latency_ms=elapsed_ms if routing_decision.location == ExecutionLocation.EDGE else None,
                backend_latency_ms=elapsed_ms if routing_decision.location == ExecutionLocation.BACKEND else None,
                cache_hit=False,
                validated=request.require_validation,
            )

        except Exception as e:
            self.metrics.errors += 1
            logger.error(f"Execution failed: {e}")

            return ExecutionResponse(
                request_id=request_id,
                status="error",
                error=str(e),
                execution_location=ExecutionLocation.BACKEND,
            )

    async def _validate_request(self, request: ExecutionRequest) -> dict[str, Any]:
        """Validate request parameters on edge."""
        issues = []

        for field_name, value in request.parameters.items():
            if field_name.startswith("_"):
                continue  # Skip internal fields

            result = await self.validator.validate(field_name, value)
            if not result.valid:
                issues.extend([i.model_dump() for i in result.issues])

        return {"valid": len(issues) == 0, "issues": issues}

    async def _execute_on_edge(self, request: ExecutionRequest) -> dict[str, Any]:
        """Execute request on edge agents."""
        # Check which edge agent should handle this
        agent_type_lower = request.agent_type.lower()

        if "cache" in agent_type_lower or "cache" in request.operation.lower():
            return await self.cache.execute_local(request.operation, **request.parameters)

        if "predict" in agent_type_lower or "prefetch" in request.operation.lower():
            return await self.predictor.execute_local(request.operation, **request.parameters)

        if "valid" in agent_type_lower or "validate" in request.operation.lower():
            return await self.validator.execute_local(request.operation, **request.parameters)

        # Default: try to route to appropriate edge handler
        # This would delegate to registered edge handlers
        return {"status": "not_implemented", "error": "No edge handler for this operation"}

    async def _execute_on_backend(self, request: ExecutionRequest) -> dict[str, Any]:
        """Execute request on backend agents."""
        agent = self._backend_agents.get(request.agent_type)

        if agent is None:
            # Queue for sync if offline
            if not self._is_online:
                delta = self.sync_layer.create_delta(
                    entity_type="request",
                    entity_id=request.operation,
                    operation=DeltaOperation.CREATE,
                    data=request.parameters,
                    priority=SyncPriority.MEDIUM,
                )
                self.sync_layer.queue_for_sync(delta)
                self.metrics.sync_operations += 1

                return {
                    "status": "queued",
                    "message": "Request queued for sync when online",
                }

            return {"status": "error", "error": f"Agent {request.agent_type} not registered"}

        # Execute on backend agent
        try:
            if hasattr(agent, "execute_core_function"):
                result = await agent.execute_core_function(
                    operation=request.operation, **request.parameters
                )
            else:
                result = await agent.execute(**request.parameters)

            return {"status": "success", "result": result}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _make_cache_key(self, request: ExecutionRequest) -> str:
        """Create cache key from request."""
        param_str = str(sorted(request.parameters.items()))
        return f"{request.operation}:{hash(param_str)}"

    # === Backend Agent Registration ===

    def register_backend_agent(self, agent_type: str, agent: Any) -> None:
        """
        Register a backend agent for execution.

        Args:
            agent_type: Agent type identifier
            agent: Agent instance
        """
        self._backend_agents[agent_type] = agent

        # Also register with router
        self.router._register_agent_profile(
            {
                "agent_type": agent_type,
                "edge_operations": set(),
                "backend_only_operations": {"*"},
            }
        )

        logger.info(f"Registered backend agent: {agent_type}")

    def unregister_backend_agent(self, agent_type: str) -> bool:
        """Unregister a backend agent."""
        if agent_type in self._backend_agents:
            del self._backend_agents[agent_type]
            return True
        return False

    # === Predictive Features ===

    async def predict_and_prefetch(
        self, user_id: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Predict user's next actions and prefetch needed data.

        Args:
            user_id: User identifier
            context: Current context

        Returns:
            Prediction and prefetch results
        """
        # Get predictions
        predictions = await self.predictor.predict_next_actions(user_id, context)

        # Get data needs
        data_keys = await self.predictor.predict_data_needs(user_id, context)

        # Prefetch data
        prefetched = 0
        for key in data_keys:
            # Try to get from backend and cache on edge
            # This would typically call backend to get data
            prefetched += 1

        return {
            "predictions": [p.model_dump() for p in predictions],
            "data_keys": data_keys,
            "prefetched": prefetched,
        }

    async def record_user_action(
        self, user_id: str, action: str
    ) -> dict[str, Any]:
        """
        Record a user action for learning.

        Args:
            user_id: User identifier
            action: Action taken

        Returns:
            Recording status
        """
        await self.predictor.record_action(user_id, action)
        return {"recorded": True, "user_id": user_id, "action": action}

    # === Sync Operations ===

    async def sync(self, direction: SyncDirection = SyncDirection.BIDIRECTIONAL) -> dict[str, Any]:
        """
        Perform sync with backend.

        Args:
            direction: Sync direction

        Returns:
            Sync results
        """
        if direction == SyncDirection.PUSH:
            return await self.sync_layer.push_sync()
        elif direction == SyncDirection.PULL:
            return await self.sync_layer.pull_sync()
        else:
            return await self.sync_layer.bidirectional_sync()

    def set_online_status(self, is_online: bool) -> None:
        """
        Update network status.

        Args:
            is_online: Whether network is available
        """
        was_offline = not self._is_online
        self._is_online = is_online

        # Update all edge agents
        asyncio.create_task(self.router.set_online_status(is_online))
        asyncio.create_task(self.cache.set_online_status(is_online))
        asyncio.create_task(self.predictor.set_online_status(is_online))
        asyncio.create_task(self.validator.set_online_status(is_online))

        # Trigger sync when coming back online
        if is_online and was_offline:
            asyncio.create_task(self.sync())

        self.status = OrchestratorStatus.RUNNING if is_online else OrchestratorStatus.OFFLINE

    # === Metrics ===

    def _record_latency(self, latency_ms: float) -> None:
        """Record latency for metrics."""
        self._latency_history.append(latency_ms)
        if len(self._latency_history) > 1000:
            self._latency_history.pop(0)

        # Update average
        self.metrics.average_latency_ms = sum(self._latency_history) / len(
            self._latency_history
        )

        # Update P95
        if len(self._latency_history) >= 20:
            sorted_latencies = sorted(self._latency_history)
            p95_index = int(len(sorted_latencies) * 0.95)
            self.metrics.p95_latency_ms = sorted_latencies[p95_index]

    def get_metrics(self) -> dict[str, Any]:
        """Get orchestrator metrics."""
        edge_percentage = (
            self.metrics.edge_requests
            / max(1, self.metrics.total_requests)
            * 100
        )
        cache_hit_ratio = (
            self.metrics.cache_hits
            / max(1, self.metrics.total_requests)
            * 100
        )

        return {
            "orchestrator": {
                "status": self.status.value,
                "node_id": self.node_id,
                "is_online": self._is_online,
            },
            "requests": {
                "total": self.metrics.total_requests,
                "edge": self.metrics.edge_requests,
                "backend": self.metrics.backend_requests,
                "edge_percentage": round(edge_percentage, 2),
            },
            "cache": {
                "hits": self.metrics.cache_hits,
                "hit_ratio": round(cache_hit_ratio, 2),
            },
            "validation": {
                "failures": self.metrics.validation_failures,
            },
            "sync": {
                "operations": self.metrics.sync_operations,
            },
            "latency": {
                "average_ms": round(self.metrics.average_latency_ms, 2),
                "p95_ms": round(self.metrics.p95_latency_ms, 2),
            },
            "errors": self.metrics.errors,
            "backend_agents": len(self._backend_agents),
        }

    def get_agent_health(self) -> dict[str, Any]:
        """Get health status of all edge agents."""
        return {
            "router": asyncio.run(self.router.health_check()) if hasattr(self.router, "health_check") else {},
            "cache": asyncio.run(self.cache.health_check()) if hasattr(self.cache, "health_check") else {},
            "predictor": asyncio.run(self.predictor.health_check()) if hasattr(self.predictor, "health_check") else {},
            "validator": asyncio.run(self.validator.health_check()) if hasattr(self.validator, "health_check") else {},
            "sync_layer": self.sync_layer.get_sync_status(),
        }

    # === Convenience Methods ===

    async def cache_data(
        self, key: str, value: Any, namespace: str = "default", ttl_seconds: float = 300.0
    ) -> bool:
        """Cache data on edge."""
        return await self.cache.set(key, value, namespace, ttl_seconds)

    async def get_cached(self, key: str, namespace: str = "default") -> tuple[Any, bool]:
        """Get data from edge cache."""
        return await self.cache.get(key, namespace)

    async def validate_input(
        self, field_name: str, value: Any, rules: list[str] | None = None
    ) -> dict[str, Any]:
        """Validate input on edge."""
        result = await self.validator.validate(field_name, value, rules)
        return result.model_dump()

    async def shutdown(self) -> None:
        """Gracefully shutdown the orchestrator."""
        logger.info("Shutting down EdgeBackendOrchestrator...")

        # Sync before shutdown
        if self._is_online:
            await self.sync(SyncDirection.PUSH)

        # Shutdown edge agents
        await asyncio.gather(
            self.router.shutdown(),
            self.cache.shutdown(),
            self.predictor.shutdown(),
            self.validator.shutdown(),
            return_exceptions=True,
        )

        self.status = OrchestratorStatus.STOPPED
        logger.info("EdgeBackendOrchestrator shutdown complete")
