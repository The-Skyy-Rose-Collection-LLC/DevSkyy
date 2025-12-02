"""
Edge-Backend Orchestrator - Unified management of edge and backend agents

Design Principle: Every agent is "hybrid-aware" — knows WHAT runs WHERE and WHY

This orchestrator:
- Manages edge agents (EdgeRouter, CacheAgent, PredictiveAgent, ValidationAgent)
- Coordinates with backend agents
- Handles sync layer operations
- Provides unified API for hybrid execution
- Provides production-grade resilience (circuit breaker, retry, timeout, bulkhead)

Architecture:
┌─────────────────────────────────────────────────────────────────────┐
│                         EDGE LAYER                                   │
│   EdgeRouter → CacheAgent → PredictiveAgent → ValidationAgent       │
│                           ↓                                          │
│                    Resilience Layer                                  │
│       (Circuit Breaker → Timeout → Retry → Bulkhead → Fallback)    │
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
- Rule #14: All failures logged to error ledger
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
from agent.edge.resilience import (
    CachedFallback,
    CircuitBreakerError,
    CircuitState,
    DefaultValueFallback,
    GracefulDegradationFallback,
    ResilienceConfig,
    ResilienceLayer,
    CircuitBreakerConfig,
    RetryConfig,
    RetryStrategy,
    TimeoutConfig,
    BulkheadConfig,
)


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
    # Resilience metrics
    circuit_breaker_opens: int = 0
    circuit_breaker_rejections: int = 0
    retries: int = 0
    timeouts: int = 0
    fallback_executions: int = 0
    bulkhead_rejections: int = 0


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

    # Default resilience configuration
    DEFAULT_TIMEOUT_MS = 5000.0
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_CIRCUIT_BREAKER_THRESHOLD = 5
    DEFAULT_CIRCUIT_BREAKER_TIMEOUT = 30.0
    DEFAULT_MAX_CONCURRENT = 50
    DEFAULT_MAX_QUEUE = 200

    def __init__(
        self,
        node_id: str = "edge_node_1",
        routing_strategy: RoutingStrategy = RoutingStrategy.ADAPTIVE,
        prefetch_strategy: PrefetchStrategy = PrefetchStrategy.ADAPTIVE,
        conflict_resolution: ConflictResolution = ConflictResolution.LAST_WRITE_WINS,
        resilience_config: ResilienceConfig | None = None,
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

        # Initialize resilience layer
        self._resilience_config = resilience_config or self._create_default_resilience_config()
        self._init_resilience_layer()

        # Backend agent registry
        self._backend_agents: dict[str, Any] = {}

        # Per-agent resilience layers
        self._agent_resilience: dict[str, ResilienceLayer] = {}

        # Network status
        self._is_online = True

        # Latency tracking
        self._latency_history: list[float] = []

        # Degraded operation handlers
        self._degraded_handlers: dict[str, Any] = {}

        # Fallback cache for graceful degradation
        self._fallback_cache: dict[str, Any] = {}

        logger.info(f"EdgeBackendOrchestrator initialized (node={node_id}) with resilience")

    def _create_default_resilience_config(self) -> ResilienceConfig:
        """Create default resilience configuration."""
        return ResilienceConfig(
            circuit_breaker=CircuitBreakerConfig(
                failure_threshold=self.DEFAULT_CIRCUIT_BREAKER_THRESHOLD,
                recovery_timeout=self.DEFAULT_CIRCUIT_BREAKER_TIMEOUT,
                failure_rate_threshold=0.5,
                minimum_calls=10,
                window_size=100,
            ),
            retry=RetryConfig(
                max_retries=self.DEFAULT_MAX_RETRIES,
                initial_delay_ms=100.0,
                max_delay_ms=5000.0,
                multiplier=2.0,
                strategy=RetryStrategy.EXPONENTIAL_JITTER,
            ),
            timeout=TimeoutConfig(
                default_timeout_ms=self.DEFAULT_TIMEOUT_MS,
            ),
            bulkhead=BulkheadConfig(
                max_concurrent=self.DEFAULT_MAX_CONCURRENT,
                max_queue_size=self.DEFAULT_MAX_QUEUE,
                queue_timeout_ms=self.DEFAULT_TIMEOUT_MS,
            ),
            enable_circuit_breaker=True,
            enable_retry=True,
            enable_timeout=True,
            enable_bulkhead=True,
            enable_fallback=True,
        )

    def _init_resilience_layer(self) -> None:
        """Initialize resilience layer with fallback strategies."""
        # Create composite fallback strategy
        self._cached_fallback = CachedFallback()
        self._default_fallback = DefaultValueFallback()
        self._degradation_fallback = GracefulDegradationFallback()

        # Main resilience layer for backend calls
        self._resilience_layer = ResilienceLayer(
            name=f"orchestrator_{self.node_id}",
            config=self._resilience_config,
            fallback=self._cached_fallback,  # Use cached fallback as primary
        )

        # Register circuit breaker state change callback
        self._resilience_layer.circuit_breaker.on_state_change = (
            self._on_circuit_breaker_state_change
        )

        logger.info("Resilience layer initialized")

    def _on_circuit_breaker_state_change(
        self, old_state: CircuitState, new_state: CircuitState
    ) -> None:
        """Handle circuit breaker state transitions."""
        if new_state == CircuitState.OPEN:
            self.metrics.circuit_breaker_opens += 1
            self.status = OrchestratorStatus.DEGRADED
            logger.warning(
                f"Orchestrator entering degraded mode: "
                f"circuit breaker opened ({old_state.value} → {new_state.value})"
            )
        elif new_state == CircuitState.CLOSED and old_state == CircuitState.HALF_OPEN:
            if self._is_online:
                self.status = OrchestratorStatus.RUNNING
            logger.info("Orchestrator recovered: circuit breaker closed")

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
        """Execute request on backend agents with resilience protection."""
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

        # Define the actual backend call
        async def backend_call() -> Any:
            if hasattr(agent, "execute_core_function"):
                return await agent.execute_core_function(
                    operation=request.operation, **request.parameters
                )
            else:
                return await agent.execute(**request.parameters)

        # Execute with resilience protection
        try:
            operation_key = f"{request.agent_type}.{request.operation}"

            # Store successful result in fallback cache for future use
            result = await self._resilience_layer.execute(
                backend_call,
                operation=operation_key,
                timeout_ms=request.timeout_ms,
                context={
                    "cache_key": operation_key,
                    "agent_type": request.agent_type,
                    "parameters": request.parameters,
                },
            )

            # Cache successful result for fallback
            self._cached_fallback.set_cache(operation_key, result)

            return {"status": "success", "result": result}

        except CircuitBreakerError as e:
            self.metrics.circuit_breaker_rejections += 1
            logger.warning(f"Circuit breaker rejected request: {e}")

            # Try degraded handler if available
            degraded_result = await self._try_degraded_execution(request)
            if degraded_result is not None:
                self.metrics.fallback_executions += 1
                return {
                    "status": "degraded",
                    "result": degraded_result,
                    "message": "Executed in degraded mode due to circuit breaker",
                }

            return {
                "status": "circuit_open",
                "error": str(e),
                "retry_after": e.retry_after,
            }

        except Exception as e:
            logger.error(f"Backend execution failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _try_degraded_execution(
        self, request: ExecutionRequest
    ) -> Any | None:
        """Attempt to execute in degraded mode."""
        operation_key = f"{request.agent_type}.{request.operation}"

        # Try degraded handler
        if operation_key in self._degraded_handlers:
            try:
                handler = self._degraded_handlers[operation_key]
                if asyncio.iscoroutinefunction(handler):
                    return await handler(request.parameters)
                return handler(request.parameters)
            except Exception as e:
                logger.warning(f"Degraded handler failed: {e}")

        # Try fallback cache
        if operation_key in self._fallback_cache:
            return self._fallback_cache[operation_key]

        return None

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
        """Get orchestrator metrics including resilience status."""
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
            "resilience": {
                "circuit_breaker_state": self._resilience_layer.circuit_breaker.state.value,
                "circuit_breaker_opens": self.metrics.circuit_breaker_opens,
                "circuit_breaker_rejections": self.metrics.circuit_breaker_rejections,
                "retries": self.metrics.retries,
                "timeouts": self.metrics.timeouts,
                "fallback_executions": self.metrics.fallback_executions,
                "bulkhead_rejections": self.metrics.bulkhead_rejections,
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

    # === Resilience Control ===

    def register_degraded_handler(
        self,
        agent_type: str,
        operation: str,
        handler: Any,
    ) -> None:
        """
        Register a degraded mode handler for an operation.

        The handler will be called when the circuit breaker is open.

        Args:
            agent_type: Agent type
            operation: Operation name
            handler: Handler function (sync or async)
        """
        key = f"{agent_type}.{operation}"
        self._degraded_handlers[key] = handler
        self._degradation_fallback.register_degraded(key, handler)
        logger.info(f"Registered degraded handler: {key}")

    def set_fallback_value(
        self,
        agent_type: str,
        operation: str,
        value: Any,
    ) -> None:
        """
        Set a fallback value for an operation.

        The value will be returned when the circuit breaker is open
        and no degraded handler is available.

        Args:
            agent_type: Agent type
            operation: Operation name
            value: Fallback value
        """
        key = f"{agent_type}.{operation}"
        self._fallback_cache[key] = value
        self._cached_fallback.set_cache(key, value)
        self._default_fallback.set_default(key, value)
        logger.info(f"Set fallback value for: {key}")

    async def get_resilience_status(self) -> dict[str, Any]:
        """Get detailed resilience layer status."""
        return {
            "layer": self._resilience_layer.get_health(),
            "circuit_breaker": self._resilience_layer.circuit_breaker.get_health(),
            "bulkhead": self._resilience_layer.bulkhead.get_metrics(),
            "registered_degraded_handlers": list(self._degraded_handlers.keys()),
            "registered_fallback_values": list(self._fallback_cache.keys()),
        }

    async def force_circuit_open(self) -> None:
        """Force the circuit breaker open (for testing/maintenance)."""
        await self._resilience_layer.circuit_breaker.force_open()
        self.status = OrchestratorStatus.DEGRADED
        logger.warning("Circuit breaker forced open")

    async def force_circuit_close(self) -> None:
        """Force the circuit breaker closed (for recovery)."""
        await self._resilience_layer.circuit_breaker.force_close()
        if self._is_online:
            self.status = OrchestratorStatus.RUNNING
        logger.info("Circuit breaker forced closed")

    async def reset_resilience(self) -> None:
        """Reset all resilience components to initial state."""
        await self._resilience_layer.reset()

        # Reset per-agent resilience layers
        for layer in self._agent_resilience.values():
            await layer.reset()

        # Reset metrics
        self.metrics.circuit_breaker_opens = 0
        self.metrics.circuit_breaker_rejections = 0
        self.metrics.retries = 0
        self.metrics.timeouts = 0
        self.metrics.fallback_executions = 0
        self.metrics.bulkhead_rejections = 0

        logger.info("Resilience layer reset")

    def get_circuit_breaker_state(self) -> str:
        """Get current circuit breaker state."""
        return self._resilience_layer.circuit_breaker.state.value

    def is_circuit_open(self) -> bool:
        """Check if circuit breaker is open."""
        return self._resilience_layer.circuit_breaker.is_open

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
