"""
Edge Router Agent - Intelligent routing between edge and backend layers

Design Principle: Route operations to optimal execution location based on:
- Latency requirements (<50ms for edge)
- Privacy constraints (sensitive data stays local)
- Compute requirements (GPU/LLM → backend)
- Network conditions (offline → queue)
- Cost optimization (minimize backend calls)

Per CLAUDE.md Truth Protocol:
- Rule #1: Routing decisions based on verified metrics
- Rule #7: Pydantic validation for routing requests
- Rule #12: P95 < 200ms for routing decisions
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from typing import Any

from pydantic import BaseModel, Field

from agent.edge.base_edge_agent import (
    BaseEdgeAgent,
    ExecutionLocation,
    OfflineCapability,
    OperationContext,
    SyncPriority,
)


logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Available routing strategies"""

    LATENCY_FIRST = "latency_first"  # Prioritize speed
    COST_FIRST = "cost_first"  # Minimize backend calls
    PRIVACY_FIRST = "privacy_first"  # Keep data local when possible
    QUALITY_FIRST = "quality_first"  # Best results (often backend)
    ADAPTIVE = "adaptive"  # Learn from results


class RoutingRequest(BaseModel):
    """Request for routing decision (Pydantic validated per Rule #7)"""

    operation: str = Field(..., min_length=1, max_length=256)
    agent_type: str = Field(..., min_length=1, max_length=128)
    data_size_bytes: int = Field(default=0, ge=0)
    requires_gpu: bool = False
    requires_llm: bool = False
    privacy_sensitive: bool = False
    latency_critical: bool = False
    quality_critical: bool = False
    user_id: str | None = None
    session_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RoutingDecision(BaseModel):
    """Result of routing decision"""

    request_id: str
    location: ExecutionLocation
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    estimated_latency_ms: float
    fallback_location: ExecutionLocation | None = None
    routing_strategy: RoutingStrategy
    timestamp: datetime = Field(default_factory=datetime.now)


@dataclass
class AgentCapabilityProfile:
    """Profile of an agent's edge/backend capabilities"""

    agent_type: str
    edge_operations: set[str] = field(default_factory=set)
    backend_only_operations: set[str] = field(default_factory=set)
    edge_latency_ms: float = 10.0
    backend_latency_ms: float = 200.0
    edge_accuracy: float = 0.9
    backend_accuracy: float = 0.99
    supports_offline: bool = True
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class RoutingMetrics:
    """Metrics for routing performance tracking"""

    total_decisions: int = 0
    edge_routes: int = 0
    backend_routes: int = 0
    fallback_triggered: int = 0
    average_decision_time_ms: float = 0.0
    routing_accuracy: float = 1.0


class EdgeRouter(BaseEdgeAgent):
    """
    Edge Router Agent - Routes operations between edge and backend.

    Features:
    - Intelligent routing based on multiple factors
    - Adaptive learning from routing outcomes
    - Agent capability profiling
    - Network-aware decisions
    - Cost optimization

    Target: <5ms routing decision time (well under 50ms edge target)
    """

    ROUTING_DECISION_TARGET_MS: float = 5.0  # Ultra-fast routing

    def __init__(
        self,
        agent_name: str = "EdgeRouter",
        version: str = "1.0.0",
        default_strategy: RoutingStrategy = RoutingStrategy.ADAPTIVE,
    ):
        super().__init__(
            agent_name=agent_name,
            version=version,
            offline_capability=OfflineCapability.FULL,
        )

        self.default_strategy = default_strategy
        self.metrics = RoutingMetrics()

        # Agent capability profiles
        self._agent_profiles: dict[str, AgentCapabilityProfile] = {}

        # Historical routing outcomes for learning
        self._routing_history: dict[str, list[dict[str, Any]]] = defaultdict(list)

        # Network quality tracking
        self._backend_latency_samples: list[float] = []
        self._backend_available = True

        # Cost tracking (backend calls)
        self._daily_backend_calls: int = 0
        self._daily_call_limit: int = 10000
        self._day_start: datetime = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        self._initialize_default_profiles()

    def _initialize_default_profiles(self) -> None:
        """Initialize default agent capability profiles."""
        # Validation agent - mostly edge
        self._agent_profiles["ValidationAgent"] = AgentCapabilityProfile(
            agent_type="ValidationAgent",
            edge_operations={
                "validate_input",
                "validate_schema",
                "validate_format",
                "sanitize_input",
            },
            backend_only_operations={"validate_against_database"},
            edge_latency_ms=5.0,
            backend_latency_ms=100.0,
            supports_offline=True,
        )

        # Cache agent - edge-first
        self._agent_profiles["CacheAgent"] = AgentCapabilityProfile(
            agent_type="CacheAgent",
            edge_operations={
                "get_cached",
                "set_cached",
                "invalidate",
                "get_ttl",
            },
            backend_only_operations={"sync_to_backend", "full_refresh"},
            edge_latency_ms=2.0,
            backend_latency_ms=50.0,
            supports_offline=True,
        )

        # Predictive agent - hybrid
        self._agent_profiles["PredictiveAgent"] = AgentCapabilityProfile(
            agent_type="PredictiveAgent",
            edge_operations={
                "predict_simple",
                "preload_likely",
                "get_prefetched",
            },
            backend_only_operations={
                "predict_complex",
                "train_model",
                "analyze_patterns",
            },
            edge_latency_ms=20.0,
            backend_latency_ms=300.0,
            supports_offline=True,
        )

        # Scanner - backend for deep analysis
        self._agent_profiles["Scanner"] = AgentCapabilityProfile(
            agent_type="Scanner",
            edge_operations={"quick_scan", "check_format"},
            backend_only_operations={
                "deep_scan",
                "security_scan",
                "vulnerability_scan",
            },
            edge_latency_ms=30.0,
            backend_latency_ms=500.0,
            supports_offline=False,
        )

        # Claude/LLM agents - backend only
        self._agent_profiles["ClaudeSonnet"] = AgentCapabilityProfile(
            agent_type="ClaudeSonnet",
            edge_operations=set(),  # No edge operations
            backend_only_operations={
                "generate",
                "analyze",
                "reason",
                "chat",
            },
            edge_latency_ms=float("inf"),
            backend_latency_ms=2000.0,
            supports_offline=False,
        )

    async def execute_local(self, operation: str, **kwargs) -> dict[str, Any]:
        """Execute routing operation locally."""
        if operation == "route":
            return await self._handle_route(kwargs)
        elif operation == "register_agent":
            return self._register_agent_profile(kwargs)
        elif operation == "get_metrics":
            return self._get_routing_metrics()
        elif operation == "update_network_status":
            return await self._update_network_status(kwargs)
        else:
            return {"error": f"Unknown operation: {operation}"}

    def get_routing_rules(self) -> dict[str, ExecutionLocation]:
        """Define routing rules for EdgeRouter operations."""
        return {
            "route": ExecutionLocation.EDGE,
            "register_agent": ExecutionLocation.EDGE,
            "get_metrics": ExecutionLocation.EDGE,
            "update_network_status": ExecutionLocation.EDGE,
            "sync_profiles": ExecutionLocation.BACKEND,
        }

    async def route(self, request: RoutingRequest) -> RoutingDecision:
        """
        Main routing decision method.

        Makes intelligent routing decisions based on:
        1. Agent capability profile
        2. Operation requirements
        3. Network conditions
        4. Cost constraints
        5. Historical performance

        Args:
            request: Routing request with operation details

        Returns:
            RoutingDecision with location and metadata
        """
        start_time = datetime.now()
        request_id = f"route_{start_time.timestamp()}"

        # Get agent profile
        profile = self._agent_profiles.get(request.agent_type)

        # Check daily limits
        self._check_daily_reset()
        cost_constrained = self._daily_backend_calls >= self._daily_call_limit * 0.9

        # Make routing decision
        location, confidence, reason = self._compute_routing_decision(
            request, profile, cost_constrained
        )

        # Determine fallback
        fallback = (
            ExecutionLocation.EDGE
            if location == ExecutionLocation.BACKEND
            else ExecutionLocation.BACKEND
        )

        # Estimate latency
        if profile:
            estimated_latency = (
                profile.edge_latency_ms
                if location == ExecutionLocation.EDGE
                else profile.backend_latency_ms
            )
        else:
            estimated_latency = (
                self.EDGE_LATENCY_TARGET_MS
                if location == ExecutionLocation.EDGE
                else 200.0
            )

        decision = RoutingDecision(
            request_id=request_id,
            location=location,
            confidence=confidence,
            reason=reason,
            estimated_latency_ms=estimated_latency,
            fallback_location=fallback if self._backend_available else None,
            routing_strategy=self.default_strategy,
        )

        # Record metrics
        decision_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        self._record_routing_decision(request, decision, decision_time_ms)

        return decision

    def _compute_routing_decision(
        self,
        request: RoutingRequest,
        profile: AgentCapabilityProfile | None,
        cost_constrained: bool,
    ) -> tuple[ExecutionLocation, float, str]:
        """
        Compute where to route the request.

        Returns:
            Tuple of (location, confidence, reason)
        """
        # Strategy-specific routing
        if self.default_strategy == RoutingStrategy.PRIVACY_FIRST:
            if request.privacy_sensitive:
                return (
                    ExecutionLocation.EDGE,
                    0.99,
                    "Privacy-sensitive data must stay local",
                )

        if self.default_strategy == RoutingStrategy.LATENCY_FIRST:
            if request.latency_critical:
                return (ExecutionLocation.EDGE, 0.95, "Latency-critical operation")

        if self.default_strategy == RoutingStrategy.QUALITY_FIRST:
            if request.quality_critical:
                return (
                    ExecutionLocation.BACKEND,
                    0.95,
                    "Quality-critical requires backend processing",
                )

        if self.default_strategy == RoutingStrategy.COST_FIRST or cost_constrained:
            if cost_constrained:
                return (
                    ExecutionLocation.EDGE,
                    0.80,
                    "Cost limit approaching, routing to edge",
                )

        # Check if operation is edge-capable
        if profile:
            if request.operation in profile.edge_operations:
                return (
                    ExecutionLocation.EDGE,
                    0.90,
                    f"Operation '{request.operation}' supported on edge",
                )

            if request.operation in profile.backend_only_operations:
                return (
                    ExecutionLocation.BACKEND,
                    0.95,
                    f"Operation '{request.operation}' requires backend",
                )

        # Check compute requirements
        if request.requires_llm:
            return (ExecutionLocation.BACKEND, 0.99, "LLM operations require backend")

        if request.requires_gpu:
            return (
                ExecutionLocation.BACKEND,
                0.99,
                "GPU operations require backend",
            )

        # Check data size
        if request.data_size_bytes > self.BACKEND_THRESHOLD_SIZE_BYTES:
            return (
                ExecutionLocation.BACKEND,
                0.85,
                f"Large data ({request.data_size_bytes} bytes) better on backend",
            )

        # Check network availability
        if not self._backend_available:
            return (
                ExecutionLocation.EDGE,
                0.70,
                "Backend unavailable, routing to edge",
            )

        # Adaptive: use historical data
        if self.default_strategy == RoutingStrategy.ADAPTIVE:
            return self._adaptive_routing(request, profile)

        # Default: edge for speed
        return (ExecutionLocation.EDGE, 0.75, "Default routing to edge for low latency")

    def _adaptive_routing(
        self, request: RoutingRequest, profile: AgentCapabilityProfile | None
    ) -> tuple[ExecutionLocation, float, str]:
        """
        Adaptive routing based on historical outcomes.

        Learns from past routing decisions to optimize future ones.
        """
        history_key = f"{request.agent_type}:{request.operation}"
        history = self._routing_history.get(history_key, [])

        if len(history) < 10:
            # Not enough data, default to edge
            return (
                ExecutionLocation.EDGE,
                0.70,
                "Insufficient history, defaulting to edge",
            )

        # Analyze recent outcomes
        recent = history[-50:]  # Last 50 decisions
        edge_success_rate = sum(
            1 for h in recent if h["location"] == "edge" and h["success"]
        ) / max(1, sum(1 for h in recent if h["location"] == "edge"))

        backend_success_rate = sum(
            1 for h in recent if h["location"] == "backend" and h["success"]
        ) / max(1, sum(1 for h in recent if h["location"] == "backend"))

        # Average latencies
        edge_latencies = [h["latency_ms"] for h in recent if h["location"] == "edge"]
        backend_latencies = [
            h["latency_ms"] for h in recent if h["location"] == "backend"
        ]

        avg_edge_latency = sum(edge_latencies) / len(edge_latencies) if edge_latencies else float("inf")
        avg_backend_latency = (
            sum(backend_latencies) / len(backend_latencies)
            if backend_latencies
            else float("inf")
        )

        # Score locations
        edge_score = edge_success_rate * 0.6 + (1 - min(avg_edge_latency / 100, 1)) * 0.4
        backend_score = (
            backend_success_rate * 0.6
            + (1 - min(avg_backend_latency / 500, 1)) * 0.4
        )

        if edge_score > backend_score:
            return (
                ExecutionLocation.EDGE,
                min(0.95, edge_score),
                f"Adaptive: edge scored {edge_score:.2f} vs backend {backend_score:.2f}",
            )
        else:
            return (
                ExecutionLocation.BACKEND,
                min(0.95, backend_score),
                f"Adaptive: backend scored {backend_score:.2f} vs edge {edge_score:.2f}",
            )

    def _record_routing_decision(
        self,
        request: RoutingRequest,
        decision: RoutingDecision,
        decision_time_ms: float,
    ) -> None:
        """Record routing decision for metrics and learning."""
        self.metrics.total_decisions += 1
        if decision.location == ExecutionLocation.EDGE:
            self.metrics.edge_routes += 1
        else:
            self.metrics.backend_routes += 1
            self._daily_backend_calls += 1

        # Update average decision time
        n = self.metrics.total_decisions
        self.metrics.average_decision_time_ms = (
            self.metrics.average_decision_time_ms * (n - 1) + decision_time_ms
        ) / n

        # Log if exceeding target
        if decision_time_ms > self.ROUTING_DECISION_TARGET_MS:
            logger.warning(
                f"Routing decision exceeded target: {decision_time_ms:.2f}ms > "
                f"{self.ROUTING_DECISION_TARGET_MS}ms"
            )

    def record_outcome(
        self,
        request_id: str,
        agent_type: str,
        operation: str,
        location: str,
        success: bool,
        latency_ms: float,
    ) -> None:
        """
        Record outcome of a routed operation for adaptive learning.

        Called after operation completes to improve future routing.
        """
        history_key = f"{agent_type}:{operation}"
        self._routing_history[history_key].append(
            {
                "request_id": request_id,
                "location": location,
                "success": success,
                "latency_ms": latency_ms,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Keep history bounded
        if len(self._routing_history[history_key]) > 1000:
            self._routing_history[history_key] = self._routing_history[history_key][-500:]

    async def _handle_route(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Handle route operation."""
        request = RoutingRequest(**kwargs)
        decision = await self.route(request)
        return decision.model_dump()

    def _register_agent_profile(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Register or update an agent capability profile."""
        profile = AgentCapabilityProfile(**kwargs)
        self._agent_profiles[profile.agent_type] = profile
        return {"status": "registered", "agent_type": profile.agent_type}

    def _get_routing_metrics(self) -> dict[str, Any]:
        """Get current routing metrics."""
        return {
            "total_decisions": self.metrics.total_decisions,
            "edge_routes": self.metrics.edge_routes,
            "backend_routes": self.metrics.backend_routes,
            "edge_percentage": (
                round(
                    self.metrics.edge_routes / max(1, self.metrics.total_decisions) * 100,
                    2,
                )
            ),
            "average_decision_time_ms": round(
                self.metrics.average_decision_time_ms, 2
            ),
            "daily_backend_calls": self._daily_backend_calls,
            "daily_limit": self._daily_call_limit,
            "backend_available": self._backend_available,
            "registered_agents": list(self._agent_profiles.keys()),
        }

    async def _update_network_status(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Update backend network status."""
        available = kwargs.get("available", True)
        latency_ms = kwargs.get("latency_ms")

        self._backend_available = available

        if latency_ms is not None:
            self._backend_latency_samples.append(latency_ms)
            if len(self._backend_latency_samples) > 100:
                self._backend_latency_samples.pop(0)

        return {
            "backend_available": self._backend_available,
            "average_latency_ms": (
                sum(self._backend_latency_samples) / len(self._backend_latency_samples)
                if self._backend_latency_samples
                else None
            ),
        }

    def _check_daily_reset(self) -> None:
        """Reset daily counters if new day."""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if today_start > self._day_start:
            self._day_start = today_start
            self._daily_backend_calls = 0
            logger.info("Daily backend call counter reset")
