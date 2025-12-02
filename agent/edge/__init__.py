"""
Edge Agent Module - Hybrid-aware edge-backend architecture for DevSkyy

This module provides edge-side agents that work in coordination with backend agents
to deliver ultra-low latency (<50ms), offline-capable, and privacy-preserving operations.

Architecture:
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         EDGE LAYER (Client)                                      │
│                                                                                  │
│   • Instant feedback (<50ms)        • Privacy-preserving                        │
│   • Offline-capable                 • Bandwidth-efficient                       │
│   • Predictive pre-computation      • User-specific personalization             │
│                                                                                  │
│   AGENTS: EdgeRouter, CacheAgent, PredictiveAgent, ValidationAgent              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      ▲
                                      │ Sync Layer
                                      │ • Delta updates
                                      │ • Conflict resolution
                                      │ • Offline queue
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       BACKEND LAYER (Server/Cloud)                               │
│                                                                                  │
│   • Heavy computation (LLM, GPU)    • Cross-user learning                       │
│   • Authoritative state             • Complex orchestration                     │
│   • Long-running jobs               • External integrations                     │
│                                                                                  │
│   AGENTS: All 50+ DevSkyy agents with full capabilities                         │
└─────────────────────────────────────────────────────────────────────────────────┘

Usage:
    from agent.edge import EdgeBackendOrchestrator, ExecutionRequest

    # Initialize orchestrator
    orchestrator = EdgeBackendOrchestrator(node_id="client_1")
    await orchestrator.initialize()

    # Execute with automatic routing
    response = await orchestrator.execute(ExecutionRequest(
        operation="quick_scan",
        agent_type="Scanner",
        parameters={"target": "example.com"},
        require_validation=True,
        use_cache=True,
    ))

    # Check if executed on edge or backend
    print(f"Executed on: {response.execution_location}")

Components:
- BaseEdgeAgent: Foundation for all edge agents
- EdgeRouter: Intelligent routing between edge and backend
- CacheAgent: Edge-side caching with delta sync
- PredictiveAgent: Prefetching and behavior prediction
- ValidationAgent: Client-side input validation
- SyncLayer: Delta synchronization with conflict resolution
- HybridAwareMixin: Add edge awareness to backend agents
- EdgeBackendOrchestrator: Unified edge-backend management
- ResilienceLayer: Circuit breaker, timeout, retry, bulkhead patterns
"""

# Base classes and types
from agent.edge.base_edge_agent import (
    BaseEdgeAgent,
    EdgeHealthMetrics,
    EdgeMetrics,
    ExecutionLocation,
    OfflineCapability,
    OperationContext,
    SyncItem,
    SyncPriority,
)

# Edge agents
from agent.edge.cache_agent import (
    CacheAgent,
    CacheEntry,
    CacheLevel,
    CachePolicy,
    CacheStats,
    DeltaChange,
    SyncStrategy,
)
from agent.edge.edge_router import (
    AgentCapabilityProfile,
    EdgeRouter,
    RoutingDecision,
    RoutingMetrics,
    RoutingRequest,
    RoutingStrategy,
)
from agent.edge.predictive_agent import (
    PatternMatcher,
    Prediction,
    PredictiveAgent,
    PredictiveMetrics,
    PredictionRequest,
    PredictionType,
    PrefetchedItem,
    PrefetchStrategy,
)
from agent.edge.validation_agent import (
    SanitizationType,
    ValidationAgent,
    ValidationIssue,
    ValidationMetrics,
    ValidationRequest,
    ValidationResult,
    ValidationSeverity,
    ValidationType,
)

# Sync layer
from agent.edge.sync_layer import (
    ConflictInfo,
    ConflictResolution,
    DeltaOperation,
    SyncBatch,
    SyncDelta,
    SyncDirection,
    SyncLayer,
    SyncMetrics,
    SyncStatus,
    VersionVector,
)

# Hybrid awareness mixin
from agent.edge.hybrid_aware_mixin import (
    EdgeCapability,
    EdgeOffloadStatus,
    EdgeOptimizedMixin,
    HybridAwareMixin,
    HybridExecutionResult,
    HybridMetrics,
    hybrid_operation,
)

# Orchestrator
from agent.edge.edge_backend_orchestrator import (
    EdgeBackendOrchestrator,
    ExecutionRequest,
    ExecutionResponse,
    OrchestratorMetrics,
    OrchestratorStatus,
)

# Resilience Layer
from agent.edge.resilience import (
    Bulkhead,
    BulkheadConfig,
    BulkheadFullError,
    CachedFallback,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerMetrics,
    CircuitState,
    DefaultValueFallback,
    FallbackStrategy,
    GracefulDegradationFallback,
    ResilienceConfig,
    ResilienceLayer,
    ResilienceRegistry,
    RetryConfig,
    RetryHandler,
    RetryStrategy,
    TimeoutConfig,
    TimeoutError,
    TimeoutHandler,
    resilience_registry,
)

__all__ = [
    # Base
    "BaseEdgeAgent",
    "EdgeHealthMetrics",
    "EdgeMetrics",
    "ExecutionLocation",
    "OfflineCapability",
    "OperationContext",
    "SyncItem",
    "SyncPriority",
    # EdgeRouter
    "EdgeRouter",
    "RoutingRequest",
    "RoutingDecision",
    "RoutingStrategy",
    "RoutingMetrics",
    "AgentCapabilityProfile",
    "Prediction",
    # CacheAgent
    "CacheAgent",
    "CacheEntry",
    "CacheLevel",
    "CachePolicy",
    "CacheStats",
    "DeltaChange",
    "SyncStrategy",
    # PredictiveAgent
    "PredictiveAgent",
    "PredictionRequest",
    "PredictionType",
    "PrefetchStrategy",
    "PrefetchedItem",
    "PredictiveMetrics",
    "PatternMatcher",
    # ValidationAgent
    "ValidationAgent",
    "ValidationRequest",
    "ValidationResult",
    "ValidationIssue",
    "ValidationSeverity",
    "ValidationType",
    "SanitizationType",
    "ValidationMetrics",
    # SyncLayer
    "SyncLayer",
    "SyncDelta",
    "SyncBatch",
    "SyncDirection",
    "SyncStatus",
    "DeltaOperation",
    "ConflictInfo",
    "ConflictResolution",
    "VersionVector",
    "SyncMetrics",
    # HybridAwareMixin
    "HybridAwareMixin",
    "EdgeOptimizedMixin",
    "EdgeCapability",
    "EdgeOffloadStatus",
    "HybridExecutionResult",
    "HybridMetrics",
    "hybrid_operation",
    # Orchestrator
    "EdgeBackendOrchestrator",
    "ExecutionRequest",
    "ExecutionResponse",
    "OrchestratorStatus",
    "OrchestratorMetrics",
    # Resilience
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerError",
    "CircuitBreakerMetrics",
    "CircuitState",
    "RetryHandler",
    "RetryConfig",
    "RetryStrategy",
    "TimeoutHandler",
    "TimeoutConfig",
    "TimeoutError",
    "Bulkhead",
    "BulkheadConfig",
    "BulkheadFullError",
    "FallbackStrategy",
    "CachedFallback",
    "DefaultValueFallback",
    "GracefulDegradationFallback",
    "ResilienceLayer",
    "ResilienceConfig",
    "ResilienceRegistry",
    "resilience_registry",
]
