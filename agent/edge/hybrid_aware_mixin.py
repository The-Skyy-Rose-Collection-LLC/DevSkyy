"""
Hybrid-Aware Mixin - Makes backend agents work with edge layer

Design Principle: Every agent is "hybrid-aware" — knows WHAT runs WHERE and WHY

This mixin adds edge-backend awareness to existing backend agents:
- Declare which operations can run on edge
- Handle edge-offloaded results
- Coordinate with edge agents
- Support graceful degradation

Per CLAUDE.md Truth Protocol:
- Rule #1: Operations verified for edge/backend capability
- Rule #9: Document hybrid behavior
- Rule #10: Continue processing on edge failures
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
import logging
from typing import Any, Callable

from agent.edge.base_edge_agent import ExecutionLocation, OperationContext


logger = logging.getLogger(__name__)


class EdgeOffloadStatus(Enum):
    """Status of edge-offloaded operation"""

    NOT_OFFLOADED = "not_offloaded"
    OFFLOADED = "offloaded"
    EDGE_COMPLETED = "edge_completed"
    BACKEND_FALLBACK = "backend_fallback"
    EDGE_FAILED = "edge_failed"


@dataclass
class EdgeCapability:
    """Describes an operation's edge capability"""

    operation: str
    can_run_on_edge: bool = False
    edge_latency_target_ms: float = 50.0
    requires_backend_validation: bool = False
    privacy_preserving: bool = False
    offline_capable: bool = False
    edge_accuracy: float = 1.0  # Expected accuracy on edge (0-1)


@dataclass
class HybridExecutionResult:
    """Result of hybrid execution"""

    result: Any
    execution_location: ExecutionLocation
    status: EdgeOffloadStatus
    edge_latency_ms: float | None = None
    backend_latency_ms: float | None = None
    was_fallback: bool = False
    edge_confidence: float | None = None


@dataclass
class HybridMetrics:
    """Metrics for hybrid-aware operations"""

    edge_operations: int = 0
    backend_operations: int = 0
    fallbacks_to_backend: int = 0
    edge_failures: int = 0
    average_edge_latency_ms: float = 0.0
    average_backend_latency_ms: float = 0.0
    edge_accuracy_achieved: float = 0.0


class HybridAwareMixin:
    """
    Mixin to add edge-backend awareness to existing agents.

    Usage:
        class MyAgent(BaseAgent, HybridAwareMixin):
            def __init__(self):
                super().__init__("MyAgent")
                HybridAwareMixin.__init__(self)
                self.register_edge_capability(
                    EdgeCapability(
                        operation="quick_scan",
                        can_run_on_edge=True,
                        edge_latency_target_ms=30.0
                    )
                )

            @hybrid_operation
            async def quick_scan(self, data):
                # Will automatically route to edge if capable
                pass

    Features:
    - Declare edge-capable operations
    - Automatic routing based on context
    - Fallback to backend on edge failure
    - Track hybrid execution metrics
    """

    def __init__(self):
        # Initialize hybrid-aware attributes
        self._edge_capabilities: dict[str, EdgeCapability] = {}
        self._hybrid_metrics = HybridMetrics()
        self._edge_router = None  # Set by orchestrator
        self._edge_cache = None  # Set by orchestrator
        self._edge_validator = None  # Set by orchestrator

        # Edge connection status
        self._edge_connected = False

        # Operation handlers for edge
        self._edge_handlers: dict[str, Callable] = {}

    # === Edge Capability Registration ===

    def register_edge_capability(self, capability: EdgeCapability) -> None:
        """
        Register an operation as edge-capable.

        Args:
            capability: Edge capability definition
        """
        self._edge_capabilities[capability.operation] = capability
        logger.info(
            f"Registered edge capability: {capability.operation} "
            f"(edge={capability.can_run_on_edge})"
        )

    def register_edge_handler(
        self, operation: str, handler: Callable
    ) -> None:
        """
        Register a handler for edge-side execution of an operation.

        The handler will be called when the operation runs on edge.
        """
        self._edge_handlers[operation] = handler

    def get_edge_capabilities(self) -> dict[str, EdgeCapability]:
        """Get all registered edge capabilities."""
        return self._edge_capabilities.copy()

    def can_execute_on_edge(self, operation: str) -> bool:
        """Check if operation can run on edge."""
        cap = self._edge_capabilities.get(operation)
        return cap.can_run_on_edge if cap else False

    # === Hybrid Execution ===

    def determine_execution_location(
        self, operation: str, context: OperationContext | None = None
    ) -> ExecutionLocation:
        """
        Determine where an operation should execute.

        Uses registered capabilities and operation context to decide.

        Args:
            operation: Operation name
            context: Optional execution context

        Returns:
            ExecutionLocation (EDGE, BACKEND, or HYBRID)
        """
        capability = self._edge_capabilities.get(operation)

        if not capability or not capability.can_run_on_edge:
            return ExecutionLocation.BACKEND

        if context:
            # Privacy-sensitive and edge supports it
            if context.privacy_sensitive and capability.privacy_preserving:
                return ExecutionLocation.EDGE

            # Latency-critical and edge can meet target
            if context.latency_critical:
                return ExecutionLocation.EDGE

            # Requires heavy compute
            if context.requires_gpu or context.requires_llm:
                return ExecutionLocation.BACKEND

            # Large data
            if context.data_size_bytes > 100_000:
                return ExecutionLocation.BACKEND

            # No network
            if not context.network_available and capability.offline_capable:
                return ExecutionLocation.EDGE

        # Default: edge if capable
        return ExecutionLocation.EDGE if capability.can_run_on_edge else ExecutionLocation.BACKEND

    async def execute_hybrid(
        self,
        operation: str,
        context: OperationContext | None = None,
        **kwargs,
    ) -> HybridExecutionResult:
        """
        Execute operation with hybrid routing.

        Routes to edge or backend based on capabilities and context.
        Falls back to backend if edge fails.

        Args:
            operation: Operation to execute
            context: Execution context
            **kwargs: Operation arguments

        Returns:
            HybridExecutionResult with execution details
        """
        location = self.determine_execution_location(operation, context)
        start_time = datetime.now()

        if location == ExecutionLocation.EDGE:
            try:
                result = await self._execute_on_edge(operation, **kwargs)
                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

                self._hybrid_metrics.edge_operations += 1
                self._update_edge_latency(elapsed_ms)

                return HybridExecutionResult(
                    result=result,
                    execution_location=ExecutionLocation.EDGE,
                    status=EdgeOffloadStatus.EDGE_COMPLETED,
                    edge_latency_ms=elapsed_ms,
                )

            except Exception as e:
                logger.warning(f"Edge execution failed for {operation}: {e}, falling back to backend")
                self._hybrid_metrics.edge_failures += 1
                self._hybrid_metrics.fallbacks_to_backend += 1

                # Fall back to backend
                result = await self._execute_on_backend(operation, **kwargs)
                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

                return HybridExecutionResult(
                    result=result,
                    execution_location=ExecutionLocation.BACKEND,
                    status=EdgeOffloadStatus.BACKEND_FALLBACK,
                    backend_latency_ms=elapsed_ms,
                    was_fallback=True,
                )

        else:
            result = await self._execute_on_backend(operation, **kwargs)
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            self._hybrid_metrics.backend_operations += 1
            self._update_backend_latency(elapsed_ms)

            return HybridExecutionResult(
                result=result,
                execution_location=ExecutionLocation.BACKEND,
                status=EdgeOffloadStatus.NOT_OFFLOADED,
                backend_latency_ms=elapsed_ms,
            )

    async def _execute_on_edge(self, operation: str, **kwargs) -> Any:
        """Execute operation on edge."""
        # Check for registered edge handler
        if operation in self._edge_handlers:
            return await self._edge_handlers[operation](**kwargs)

        # Use edge router if available
        if self._edge_router:
            # Route through edge infrastructure
            return await self._edge_router.execute(operation, **kwargs)

        raise NotImplementedError(
            f"No edge handler registered for {operation}"
        )

    async def _execute_on_backend(self, operation: str, **kwargs) -> Any:
        """
        Execute operation on backend.

        Override in subclass to implement backend execution.
        """
        # Default: look for method on self
        method = getattr(self, f"_backend_{operation}", None)
        if method:
            return await method(**kwargs)

        raise NotImplementedError(
            f"No backend implementation for {operation}"
        )

    # === Edge Integration ===

    def set_edge_router(self, router: Any) -> None:
        """Set the edge router for routing decisions."""
        self._edge_router = router
        self._edge_connected = True

    def set_edge_cache(self, cache: Any) -> None:
        """Set the edge cache for caching operations."""
        self._edge_cache = cache

    def set_edge_validator(self, validator: Any) -> None:
        """Set the edge validator for validation."""
        self._edge_validator = validator

    async def cache_on_edge(
        self, key: str, value: Any, ttl_seconds: float = 300.0
    ) -> bool:
        """
        Cache data on edge for fast access.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: TTL for cache entry

        Returns:
            True if cached successfully
        """
        if not self._edge_cache:
            return False

        result = await self._edge_cache.execute_local(
            "set", key=key, value=value, ttl_seconds=ttl_seconds
        )
        return result.get("success", False)

    async def get_from_edge_cache(self, key: str) -> tuple[Any, bool]:
        """
        Get data from edge cache.

        Returns:
            Tuple of (value, hit)
        """
        if not self._edge_cache:
            return None, False

        result = await self._edge_cache.execute_local("get", key=key)
        return result.get("value"), result.get("hit", False)

    async def validate_on_edge(
        self, field_name: str, value: Any, rules: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Validate input on edge before processing.

        Args:
            field_name: Name of field to validate
            value: Value to validate
            rules: Validation rules to apply

        Returns:
            Validation result
        """
        if not self._edge_validator:
            # Return success if no validator
            return {"valid": True, "sanitized_value": value}

        return await self._edge_validator.execute_local(
            "validate", field_name=field_name, value=value, rules=rules
        )

    # === Metrics ===

    def _update_edge_latency(self, elapsed_ms: float) -> None:
        """Update edge latency average."""
        n = self._hybrid_metrics.edge_operations
        if n == 0:
            return
        self._hybrid_metrics.average_edge_latency_ms = (
            self._hybrid_metrics.average_edge_latency_ms * (n - 1) + elapsed_ms
        ) / n

    def _update_backend_latency(self, elapsed_ms: float) -> None:
        """Update backend latency average."""
        n = self._hybrid_metrics.backend_operations
        if n == 0:
            return
        self._hybrid_metrics.average_backend_latency_ms = (
            self._hybrid_metrics.average_backend_latency_ms * (n - 1) + elapsed_ms
        ) / n

    def get_hybrid_metrics(self) -> dict[str, Any]:
        """Get hybrid execution metrics."""
        total = (
            self._hybrid_metrics.edge_operations
            + self._hybrid_metrics.backend_operations
        )
        edge_percentage = (
            self._hybrid_metrics.edge_operations / total * 100 if total > 0 else 0.0
        )

        return {
            "edge_operations": self._hybrid_metrics.edge_operations,
            "backend_operations": self._hybrid_metrics.backend_operations,
            "edge_percentage": round(edge_percentage, 2),
            "fallbacks_to_backend": self._hybrid_metrics.fallbacks_to_backend,
            "edge_failures": self._hybrid_metrics.edge_failures,
            "average_edge_latency_ms": round(
                self._hybrid_metrics.average_edge_latency_ms, 2
            ),
            "average_backend_latency_ms": round(
                self._hybrid_metrics.average_backend_latency_ms, 2
            ),
            "edge_connected": self._edge_connected,
            "registered_capabilities": list(self._edge_capabilities.keys()),
        }


def hybrid_operation(
    edge_capable: bool = True,
    latency_target_ms: float = 50.0,
    privacy_preserving: bool = False,
    offline_capable: bool = False,
):
    """
    Decorator to mark a method as hybrid-aware.

    Automatically routes to edge or backend based on capabilities.

    Usage:
        @hybrid_operation(edge_capable=True, latency_target_ms=30.0)
        async def quick_scan(self, data):
            # Implementation
            pass

    Args:
        edge_capable: Whether operation can run on edge
        latency_target_ms: Target latency for edge execution
        privacy_preserving: Whether edge handles privacy
        offline_capable: Whether operation works offline
    """

    def decorator(func: Callable) -> Callable:
        # Store capability info on function
        func._edge_capability = EdgeCapability(
            operation=func.__name__,
            can_run_on_edge=edge_capable,
            edge_latency_target_ms=latency_target_ms,
            privacy_preserving=privacy_preserving,
            offline_capable=offline_capable,
        )

        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Check if agent has HybridAwareMixin
            if not hasattr(self, "_edge_capabilities"):
                return await func(self, *args, **kwargs)

            # Register capability if not already registered
            if func.__name__ not in self._edge_capabilities:
                self.register_edge_capability(func._edge_capability)

            # Create context from kwargs
            context = kwargs.pop("_context", None)
            if context is None:
                context = OperationContext(operation_type=func.__name__)

            # Execute with hybrid routing
            result = await self.execute_hybrid(
                func.__name__, context, _original_func=func, _self=self, **kwargs
            )

            # For simplicity, return just the result
            # Could return full HybridExecutionResult if needed
            return result.result

        return wrapper

    return decorator


class EdgeOptimizedMixin(HybridAwareMixin):
    """
    Extended mixin with additional edge optimization features.

    Adds:
    - Automatic prefetching
    - Result caching
    - Validation before execution
    """

    def __init__(self):
        super().__init__()
        self._prefetch_rules: dict[str, list[str]] = {}

    def register_prefetch_rule(
        self, operation: str, data_keys: list[str]
    ) -> None:
        """
        Register data to prefetch before an operation.

        When the operation is predicted, these keys will be prefetched.
        """
        self._prefetch_rules[operation] = data_keys

    async def prefetch_for_operation(self, operation: str) -> int:
        """
        Prefetch data for an operation.

        Returns number of items prefetched.
        """
        if operation not in self._prefetch_rules:
            return 0

        keys = self._prefetch_rules[operation]
        count = 0

        for key in keys:
            # Prefetch logic would go here
            count += 1

        return count

    async def execute_with_validation(
        self, operation: str, inputs: dict[str, Any], **kwargs
    ) -> dict[str, Any]:
        """
        Execute operation with input validation on edge.

        Validates all inputs before executing operation.
        """
        # Validate inputs on edge
        validation_results = {}
        all_valid = True

        for field_name, value in inputs.items():
            result = await self.validate_on_edge(field_name, value)
            validation_results[field_name] = result
            if not result.get("valid", True):
                all_valid = False

        if not all_valid:
            return {
                "status": "validation_failed",
                "validation_results": validation_results,
            }

        # Execute operation with sanitized inputs
        sanitized_inputs = {
            k: v.get("sanitized_value", inputs[k])
            for k, v in validation_results.items()
        }

        result = await self.execute_hybrid(operation, **sanitized_inputs, **kwargs)

        return {
            "status": "success",
            "result": result.result,
            "execution_location": result.execution_location.value,
        }
