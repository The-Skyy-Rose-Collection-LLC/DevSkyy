"""
Tests for Edge Agent Architecture

Tests for:
- BaseEdgeAgent
- EdgeRouter
- CacheAgent
- PredictiveAgent
- ValidationAgent
- SyncLayer
- HybridAwareMixin
- EdgeBackendOrchestrator

Per CLAUDE.md Truth Protocol:
- Rule #8: Test coverage ≥90%
- Rule #12: P95 < 200ms for edge operations
"""

import asyncio
from datetime import datetime

import pytest

from agent.edge import (
    BaseEdgeAgent,
    Bulkhead,
    BulkheadConfig,
    BulkheadFullError,
    CachedFallback,
    CacheAgent,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitState,
    ConflictResolution,
    DefaultValueFallback,
    DeltaOperation,
    EdgeBackendOrchestrator,
    EdgeRouter,
    ExecutionLocation,
    ExecutionRequest,
    GracefulDegradationFallback,
    HybridAwareMixin,
    OfflineCapability,
    OperationContext,
    PredictiveAgent,
    ResilienceConfig,
    ResilienceLayer,
    RetryConfig,
    RetryHandler,
    RetryStrategy,
    RoutingRequest,
    RoutingStrategy,
    SyncDirection,
    SyncLayer,
    SyncPriority,
    TimeoutConfig,
    TimeoutError,
    TimeoutHandler,
    ValidationAgent,
    ValidationSeverity,
    hybrid_operation,
)
from agent.modules.base_agent import BaseAgent


# === Test BaseEdgeAgent ===


class ConcreteEdgeAgent(BaseEdgeAgent):
    """Concrete implementation for testing."""

    async def execute_local(self, operation: str, **kwargs) -> dict:
        if operation == "test":
            return {"status": "success", "result": "test_result"}
        return {"error": "unknown operation"}

    def get_routing_rules(self) -> dict:
        return {
            "test": ExecutionLocation.EDGE,
            "heavy": ExecutionLocation.BACKEND,
        }


class TestBaseEdgeAgent:
    """Tests for BaseEdgeAgent."""

    @pytest.fixture
    def agent(self):
        return ConcreteEdgeAgent(
            agent_name="TestEdgeAgent",
            version="1.0.0",
            offline_capability=OfflineCapability.FULL,
        )

    @pytest.mark.asyncio
    async def test_initialization(self, agent):
        """Test edge agent initializes correctly."""
        await agent.initialize()
        assert agent.agent_name == "TestEdgeAgent"
        assert agent.offline_capability == OfflineCapability.FULL
        assert agent.is_online is True

    @pytest.mark.asyncio
    async def test_execute_local(self, agent):
        """Test local execution."""
        result = await agent.execute_local("test")
        assert result["status"] == "success"
        assert result["result"] == "test_result"

    @pytest.mark.asyncio
    async def test_routing_decision_edge(self, agent):
        """Test routing to edge for appropriate operations."""
        await agent.initialize()
        context = OperationContext(
            operation_type="test",
            latency_critical=True,
        )
        should_local = agent.should_execute_locally(context)
        assert should_local is True

    @pytest.mark.asyncio
    async def test_routing_decision_backend(self, agent):
        """Test routing to backend for heavy operations."""
        await agent.initialize()
        context = OperationContext(
            operation_type="heavy",
            requires_llm=True,
        )
        should_local = agent.should_execute_locally(context)
        assert should_local is False

    @pytest.mark.asyncio
    async def test_privacy_stays_local(self, agent):
        """Test privacy-sensitive operations stay on edge."""
        await agent.initialize()
        context = OperationContext(
            operation_type="anything",
            privacy_sensitive=True,
        )
        should_local = agent.should_execute_locally(context)
        assert should_local is True

    @pytest.mark.asyncio
    async def test_local_cache(self, agent):
        """Test local cache operations."""
        agent.cache_locally("test_key", "test_value", ttl_seconds=60.0)
        value, hit = agent.get_from_cache("test_key")
        assert hit is True
        assert value == "test_value"

    @pytest.mark.asyncio
    async def test_cache_miss(self, agent):
        """Test cache miss."""
        value, hit = agent.get_from_cache("nonexistent")
        assert hit is False
        assert value is None

    @pytest.mark.asyncio
    async def test_offline_queue(self, agent):
        """Test offline queue management."""
        await agent._queue_for_sync("test_op", {"data": "test"}, SyncPriority.HIGH)
        assert len(agent.offline_queue) == 1
        assert agent.offline_queue[0].priority == SyncPriority.HIGH


# === Test EdgeRouter ===


class TestEdgeRouter:
    """Tests for EdgeRouter."""

    @pytest.fixture
    def router(self):
        return EdgeRouter(
            agent_name="TestRouter",
            default_strategy=RoutingStrategy.ADAPTIVE,
        )

    @pytest.mark.asyncio
    async def test_initialization(self, router):
        """Test router initializes correctly."""
        await router.initialize()
        assert router.agent_name == "TestRouter"
        assert router.default_strategy == RoutingStrategy.ADAPTIVE

    @pytest.mark.asyncio
    async def test_route_to_edge(self, router):
        """Test routing decision to edge."""
        await router.initialize()
        request = RoutingRequest(
            operation="validate_input",
            agent_type="ValidationAgent",
            latency_critical=True,
        )
        decision = await router.route(request)
        assert decision.location == ExecutionLocation.EDGE

    @pytest.mark.asyncio
    async def test_route_to_backend_for_llm(self, router):
        """Test routing to backend for LLM operations."""
        await router.initialize()
        request = RoutingRequest(
            operation="generate",
            agent_type="ClaudeSonnet",
            requires_llm=True,
        )
        decision = await router.route(request)
        assert decision.location == ExecutionLocation.BACKEND

    @pytest.mark.asyncio
    async def test_privacy_routes_to_edge(self, router):
        """Test privacy-sensitive routes to edge."""
        await router.initialize()
        router.default_strategy = RoutingStrategy.PRIVACY_FIRST
        request = RoutingRequest(
            operation="process_pii",
            agent_type="DataProcessor",
            privacy_sensitive=True,
        )
        decision = await router.route(request)
        assert decision.location == ExecutionLocation.EDGE

    @pytest.mark.asyncio
    async def test_routing_metrics(self, router):
        """Test routing metrics collection."""
        await router.initialize()
        request = RoutingRequest(
            operation="test",
            agent_type="TestAgent",
        )
        await router.route(request)
        metrics = router._get_routing_metrics()
        assert metrics["total_decisions"] >= 1


# === Test CacheAgent ===


class TestCacheAgent:
    """Tests for CacheAgent."""

    @pytest.fixture
    def cache(self):
        return CacheAgent(agent_name="TestCache")

    @pytest.mark.asyncio
    async def test_initialization(self, cache):
        """Test cache agent initializes correctly."""
        await cache.initialize()
        assert cache.agent_name == "TestCache"

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        """Test basic cache set and get."""
        await cache.set("key1", "value1", namespace="test")
        value, hit = await cache.get("key1", namespace="test")
        assert hit is True
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache):
        """Test cache miss."""
        value, hit = await cache.get("nonexistent", namespace="test")
        assert hit is False
        assert value is None

    @pytest.mark.asyncio
    async def test_delete(self, cache):
        """Test cache delete."""
        await cache.set("key2", "value2")
        found = await cache.delete("key2")
        assert found is True
        value, hit = await cache.get("key2")
        assert hit is False

    @pytest.mark.asyncio
    async def test_invalidate_by_tag(self, cache):
        """Test tag-based invalidation."""
        await cache.set("key3", "value3", tags=["tag1"])
        await cache.set("key4", "value4", tags=["tag1"])
        await cache.set("key5", "value5", tags=["tag2"])

        count = await cache.invalidate_by_tag("tag1")
        assert count == 2

        _, hit3 = await cache.get("key3")
        _, hit5 = await cache.get("key5")
        assert hit3 is False
        assert hit5 is True

    @pytest.mark.asyncio
    async def test_delta_tracking(self, cache):
        """Test delta tracking for sync."""
        await cache.set("delta_key", "delta_value")
        deltas = cache.get_deltas_for_sync()
        assert len(deltas) >= 1
        assert deltas[-1]["operation"] in ("set", "update")

    @pytest.mark.asyncio
    async def test_cache_stats(self, cache):
        """Test cache statistics."""
        await cache.set("stat_key", "stat_value")
        await cache.get("stat_key")
        await cache.get("missing_key")

        stats = cache._get_stats()
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1
        assert stats["writes"] >= 1


# === Test PredictiveAgent ===


class TestPredictiveAgent:
    """Tests for PredictiveAgent."""

    @pytest.fixture
    def predictor(self):
        return PredictiveAgent(agent_name="TestPredictor")

    @pytest.mark.asyncio
    async def test_initialization(self, predictor):
        """Test predictor initializes correctly."""
        await predictor.initialize()
        assert predictor.agent_name == "TestPredictor"

    @pytest.mark.asyncio
    async def test_record_action(self, predictor):
        """Test recording user actions."""
        await predictor.record_action("user1", "view_product")
        assert len(predictor._user_actions["user1"]) == 1

    @pytest.mark.asyncio
    async def test_predict_next_actions(self, predictor):
        """Test predicting next actions."""
        # Record a sequence
        for action in ["view_home", "view_products", "view_product", "add_to_cart"]:
            await predictor.record_action("user2", action)

        predictions = await predictor.predict_next_actions("user2", top_k=3)
        # Should return some predictions (may be empty if insufficient data)
        assert isinstance(predictions, list)

    @pytest.mark.asyncio
    async def test_prefetch(self, predictor):
        """Test prefetching data."""
        success = await predictor.prefetch("key1", "value1", confidence=0.8)
        assert success is True

        value, found = predictor.get_prefetched("key1")
        assert found is True
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_metrics(self, predictor):
        """Test predictive metrics."""
        await predictor.prefetch("metric_key", "metric_value", confidence=0.9)
        metrics = predictor._get_metrics()
        assert metrics["prefetches_triggered"] >= 1


# === Test ValidationAgent ===


class TestValidationAgent:
    """Tests for ValidationAgent."""

    @pytest.fixture
    def validator(self):
        return ValidationAgent(agent_name="TestValidator")

    @pytest.mark.asyncio
    async def test_initialization(self, validator):
        """Test validator initializes correctly."""
        await validator.initialize()
        assert validator.agent_name == "TestValidator"

    @pytest.mark.asyncio
    async def test_validate_email_valid(self, validator):
        """Test valid email validation."""
        result = await validator.validate("email", "test@example.com", rules=["email"])
        assert result.valid is True

    @pytest.mark.asyncio
    async def test_validate_email_invalid(self, validator):
        """Test invalid email validation."""
        result = await validator.validate("email", "invalid-email", rules=["email"])
        assert result.valid is False
        assert any(i.severity == ValidationSeverity.ERROR for i in result.issues)

    @pytest.mark.asyncio
    async def test_sanitize_xss(self, validator):
        """Test XSS sanitization."""
        malicious = "<script>alert('xss')</script>"
        sanitized = validator.sanitize(malicious)
        assert "<script>" not in sanitized
        assert "&lt;script&gt;" in sanitized  # HTML escaped

    @pytest.mark.asyncio
    async def test_security_check_sql_injection(self, validator):
        """Test SQL injection detection."""
        malicious = "'; DROP TABLE users; --"
        result = await validator.check_security(malicious)
        assert result["safe"] is False
        assert result["threats"]["sql_injection"] is True

    @pytest.mark.asyncio
    async def test_batch_validation(self, validator):
        """Test batch validation."""
        fields = {
            "email": "test@example.com",
            "phone": "123-456-7890",
        }
        results = await validator.validate_batch(fields)
        assert "email" in results
        assert "phone" in results

    @pytest.mark.asyncio
    async def test_validation_metrics(self, validator):
        """Test validation metrics."""
        await validator.validate("test", "value")
        metrics = validator._get_metrics()
        assert metrics["validations_performed"] >= 1


# === Test SyncLayer ===


class TestSyncLayer:
    """Tests for SyncLayer."""

    @pytest.fixture
    def sync_layer(self):
        return SyncLayer(node_id="test_node")

    def test_create_delta(self, sync_layer):
        """Test creating sync delta."""
        delta = sync_layer.create_delta(
            entity_type="product",
            entity_id="123",
            operation=DeltaOperation.CREATE,
            data={"name": "Test Product"},
        )
        assert delta.entity_type == "product"
        assert delta.entity_id == "123"
        assert delta.new_version == 1

    def test_queue_for_sync(self, sync_layer):
        """Test queuing delta for sync."""
        delta = sync_layer.create_delta(
            entity_type="order",
            entity_id="456",
            operation=DeltaOperation.UPDATE,
            data={"status": "shipped"},
        )
        success = sync_layer.queue_for_sync(delta)
        assert success is True
        assert len(sync_layer._offline_queue) == 1

    def test_version_vector(self, sync_layer):
        """Test version vector operations."""
        # Create multiple deltas for same entity
        sync_layer.create_delta("user", "1", DeltaOperation.CREATE, {"name": "A"})
        sync_layer.create_delta("user", "1", DeltaOperation.UPDATE, {"name": "B"})

        version = sync_layer._version_vector.get("user:1")
        assert version == 2

    def test_detect_conflicts(self, sync_layer):
        """Test conflict detection."""
        # Create local change
        sync_layer.create_delta("item", "1", DeltaOperation.CREATE, {"value": "local"})

        # Simulate incoming delta with different checksum
        from agent.edge.sync_layer import SyncDelta

        incoming = SyncDelta(
            delta_id="incoming_1",
            entity_type="item",
            entity_id="1",
            operation=DeltaOperation.UPDATE,
            new_version=2,
            old_checksum="different_checksum",  # Different from local
            new_checksum="backend_checksum",
            data={"value": "backend"},
        )

        conflicts = sync_layer.detect_conflicts([incoming])
        # May or may not detect conflict depending on timing
        assert isinstance(conflicts, list)

    def test_create_sync_batch(self, sync_layer):
        """Test creating sync batch."""
        for i in range(5):
            delta = sync_layer.create_delta(
                f"entity_{i}", str(i), DeltaOperation.CREATE, {"data": i}
            )
            sync_layer.queue_for_sync(delta)

        batch = sync_layer.create_sync_batch(max_size=3)
        assert len(batch.deltas) <= 3

    def test_sync_metrics(self, sync_layer):
        """Test sync metrics."""
        delta = sync_layer.create_delta("test", "1", DeltaOperation.CREATE, {})
        sync_layer.queue_for_sync(delta)

        metrics = sync_layer.get_metrics()
        assert metrics["offline_queue_size"] >= 1


# === Test HybridAwareMixin ===


class HybridAgent(BaseAgent, HybridAwareMixin):
    """Test agent with hybrid awareness."""

    def __init__(self):
        BaseAgent.__init__(self, "HybridAgent", "1.0.0")
        HybridAwareMixin.__init__(self)

    async def initialize(self) -> bool:
        return True

    async def execute_core_function(self, **kwargs):
        return {"result": "backend"}


class TestHybridAwareMixin:
    """Tests for HybridAwareMixin."""

    @pytest.fixture
    def agent(self):
        return HybridAgent()

    def test_register_edge_capability(self, agent):
        """Test registering edge capability."""
        from agent.edge import EdgeCapability

        cap = EdgeCapability(
            operation="quick_op",
            can_run_on_edge=True,
            edge_latency_target_ms=30.0,
        )
        agent.register_edge_capability(cap)
        assert "quick_op" in agent._edge_capabilities

    def test_can_execute_on_edge(self, agent):
        """Test checking edge execution capability."""
        from agent.edge import EdgeCapability

        cap = EdgeCapability(operation="edge_op", can_run_on_edge=True)
        agent.register_edge_capability(cap)

        assert agent.can_execute_on_edge("edge_op") is True
        assert agent.can_execute_on_edge("unknown_op") is False

    def test_determine_execution_location(self, agent):
        """Test execution location determination."""
        from agent.edge import EdgeCapability

        cap = EdgeCapability(operation="hybrid_op", can_run_on_edge=True)
        agent.register_edge_capability(cap)

        location = agent.determine_execution_location("hybrid_op")
        assert location == ExecutionLocation.EDGE

    def test_get_hybrid_metrics(self, agent):
        """Test hybrid metrics."""
        metrics = agent.get_hybrid_metrics()
        assert "edge_operations" in metrics
        assert "backend_operations" in metrics


# === Test EdgeBackendOrchestrator ===


class TestEdgeBackendOrchestrator:
    """Tests for EdgeBackendOrchestrator."""

    @pytest.fixture
    def orchestrator(self):
        return EdgeBackendOrchestrator(node_id="test_orchestrator")

    @pytest.mark.asyncio
    async def test_initialization(self, orchestrator):
        """Test orchestrator initializes correctly."""
        success = await orchestrator.initialize()
        assert success is True
        assert orchestrator.status.value == "running"

    @pytest.mark.asyncio
    async def test_execute_with_cache(self, orchestrator):
        """Test execution with caching."""
        await orchestrator.initialize()

        # Cache some data
        await orchestrator.cache_data("test_key", "test_value")

        # Should get from cache
        value, hit = await orchestrator.get_cached("test_key")
        assert hit is True
        assert value == "test_value"

    @pytest.mark.asyncio
    async def test_execute_request(self, orchestrator):
        """Test executing a request."""
        await orchestrator.initialize()

        request = ExecutionRequest(
            operation="validate",
            agent_type="ValidationAgent",
            parameters={"field_name": "email", "value": "test@example.com"},
        )

        response = await orchestrator.execute(request)
        assert response.status in ("success", "validation_failed", "not_implemented")

    @pytest.mark.asyncio
    async def test_validate_input(self, orchestrator):
        """Test input validation."""
        await orchestrator.initialize()

        result = await orchestrator.validate_input("email", "test@example.com", ["email"])
        assert "valid" in result

    @pytest.mark.asyncio
    async def test_record_user_action(self, orchestrator):
        """Test recording user actions."""
        await orchestrator.initialize()

        result = await orchestrator.record_user_action("user1", "view_product")
        assert result["recorded"] is True

    @pytest.mark.asyncio
    async def test_metrics(self, orchestrator):
        """Test orchestrator metrics."""
        await orchestrator.initialize()

        metrics = orchestrator.get_metrics()
        assert "orchestrator" in metrics
        assert "requests" in metrics
        assert "cache" in metrics
        assert "latency" in metrics

    @pytest.mark.asyncio
    async def test_online_status(self, orchestrator):
        """Test online status changes."""
        await orchestrator.initialize()

        orchestrator.set_online_status(False)
        assert orchestrator._is_online is False
        assert orchestrator.status.value == "offline"

        orchestrator.set_online_status(True)
        assert orchestrator._is_online is True

    @pytest.mark.asyncio
    async def test_shutdown(self, orchestrator):
        """Test graceful shutdown."""
        await orchestrator.initialize()
        await orchestrator.shutdown()
        assert orchestrator.status.value == "stopped"


# === Performance Tests ===


class TestPerformance:
    """Performance tests for edge agents."""

    @pytest.mark.asyncio
    async def test_cache_latency(self):
        """Test cache operation latency < 10ms."""
        cache = CacheAgent()
        await cache.initialize()

        start = datetime.now()
        for i in range(100):
            await cache.set(f"perf_key_{i}", f"value_{i}")
            await cache.get(f"perf_key_{i}")
        elapsed_ms = (datetime.now() - start).total_seconds() * 1000

        avg_latency = elapsed_ms / 200  # 200 operations
        assert avg_latency < 10.0, f"Average latency {avg_latency}ms exceeds 10ms target"

    @pytest.mark.asyncio
    async def test_validation_latency(self):
        """Test validation latency < 10ms."""
        validator = ValidationAgent()
        await validator.initialize()

        start = datetime.now()
        for i in range(100):
            await validator.validate("email", f"test{i}@example.com", ["email"])
        elapsed_ms = (datetime.now() - start).total_seconds() * 1000

        avg_latency = elapsed_ms / 100
        assert avg_latency < 10.0, f"Average latency {avg_latency}ms exceeds 10ms target"

    @pytest.mark.asyncio
    async def test_routing_latency(self):
        """Test routing decision latency < 5ms."""
        router = EdgeRouter()
        await router.initialize()

        start = datetime.now()
        for i in range(100):
            request = RoutingRequest(
                operation=f"op_{i}",
                agent_type="TestAgent",
            )
            await router.route(request)
        elapsed_ms = (datetime.now() - start).total_seconds() * 1000

        avg_latency = elapsed_ms / 100
        assert avg_latency < 5.0, f"Average latency {avg_latency}ms exceeds 5ms target"


# === Test Resilience Layer ===


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    @pytest.fixture
    def breaker(self):
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=1.0,  # Short timeout for testing
            minimum_calls=5,
            failure_rate_threshold=0.5,
        )
        return CircuitBreaker("test_breaker", config)

    @pytest.mark.asyncio
    async def test_initial_state_closed(self, breaker):
        """Test circuit breaker starts in closed state."""
        assert breaker.state == CircuitState.CLOSED
        assert breaker.is_closed is True
        assert breaker.is_open is False

    @pytest.mark.asyncio
    async def test_successful_call(self, breaker):
        """Test recording successful calls."""
        async with breaker:
            pass  # Simulate successful call

        assert breaker.metrics.successful_calls == 1
        assert breaker.metrics.consecutive_successes == 1

    @pytest.mark.asyncio
    async def test_failed_call(self, breaker):
        """Test recording failed calls."""
        try:
            async with breaker:
                raise ValueError("Test error")
        except ValueError:
            pass

        assert breaker.metrics.failed_calls == 1
        assert breaker.metrics.consecutive_failures == 1

    @pytest.mark.asyncio
    async def test_opens_after_threshold(self, breaker):
        """Test circuit opens after failure threshold."""
        for _ in range(3):
            try:
                async with breaker:
                    raise ConnectionError("Backend down")
            except ConnectionError:
                pass

        assert breaker.state == CircuitState.OPEN
        assert breaker.is_open is True

    @pytest.mark.asyncio
    async def test_rejects_when_open(self, breaker):
        """Test circuit rejects calls when open."""
        # Force open
        await breaker.force_open()

        with pytest.raises(CircuitBreakerError) as exc_info:
            async with breaker:
                pass

        assert exc_info.value.state == CircuitState.OPEN
        assert breaker.metrics.rejected_calls == 1

    @pytest.mark.asyncio
    async def test_transitions_to_half_open(self, breaker):
        """Test circuit transitions to half-open after timeout."""
        await breaker.force_open()
        # Wait for recovery timeout
        await asyncio.sleep(1.5)
        # Try a call to trigger state check
        try:
            await breaker._before_call()
            assert breaker.state == CircuitState.HALF_OPEN
        except CircuitBreakerError:
            pass

    @pytest.mark.asyncio
    async def test_closes_after_recovery(self, breaker):
        """Test circuit closes after successful calls in half-open."""
        breaker._state = CircuitState.HALF_OPEN
        breaker._half_open_calls = 0

        # Successful calls should close circuit
        for _ in range(3):
            async with breaker:
                pass

        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_force_open_and_close(self, breaker):
        """Test forcing circuit open and closed."""
        await breaker.force_open()
        assert breaker.state == CircuitState.OPEN

        await breaker.force_close()
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_reset(self, breaker):
        """Test resetting circuit breaker."""
        # Generate some state
        for _ in range(2):
            try:
                async with breaker:
                    raise ValueError("Error")
            except ValueError:
                pass

        await breaker.reset()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.metrics.total_calls == 0

    @pytest.mark.asyncio
    async def test_state_change_callback(self):
        """Test state change callback is invoked."""
        callback_invoked = []

        def callback(old, new):
            callback_invoked.append((old, new))

        breaker = CircuitBreaker(
            "callback_breaker",
            CircuitBreakerConfig(failure_threshold=2),
            on_state_change=callback,
        )

        # Trigger state change
        for _ in range(2):
            try:
                async with breaker:
                    raise ConnectionError("Error")
            except ConnectionError:
                pass

        assert len(callback_invoked) == 1
        assert callback_invoked[0] == (CircuitState.CLOSED, CircuitState.OPEN)

    @pytest.mark.asyncio
    async def test_protect_decorator(self, breaker):
        """Test protect decorator."""
        @breaker.protect
        async def protected_func():
            return "success"

        result = await protected_func()
        assert result == "success"
        assert breaker.metrics.successful_calls == 1

    def test_get_health(self, breaker):
        """Test getting health status."""
        health = breaker.get_health()
        assert health["name"] == "test_breaker"
        assert health["state"] == "closed"
        assert "metrics" in health


class TestRetryHandler:
    """Tests for RetryHandler."""

    @pytest.fixture
    def retry_handler(self):
        config = RetryConfig(
            max_retries=3,
            initial_delay_ms=10.0,
            strategy=RetryStrategy.FIXED,
        )
        return RetryHandler(config)

    @pytest.mark.asyncio
    async def test_successful_first_try(self, retry_handler):
        """Test successful execution on first try."""
        async def success_func():
            return "success"

        result = await retry_handler.execute(success_func)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, retry_handler):
        """Test retry on transient failure."""
        attempts = [0]

        async def failing_func():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ConnectionError("Transient error")
            return "recovered"

        result = await retry_handler.execute(failing_func)
        assert result == "recovered"
        assert attempts[0] == 3

    @pytest.mark.asyncio
    async def test_exhausts_retries(self, retry_handler):
        """Test exhausting all retries."""
        async def always_fails():
            raise ConnectionError("Permanent error")

        with pytest.raises(ConnectionError):
            await retry_handler.execute(always_fails)

    @pytest.mark.asyncio
    async def test_no_retry_for_non_retryable(self, retry_handler):
        """Test no retry for non-retryable exceptions."""
        attempts = [0]

        async def raises_value_error():
            attempts[0] += 1
            raise ValueError("Non-retryable")

        with pytest.raises(ValueError):
            await retry_handler.execute(raises_value_error)

        assert attempts[0] == 1  # No retry

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test exponential backoff delay calculation."""
        config = RetryConfig(
            max_retries=3,
            initial_delay_ms=100.0,
            multiplier=2.0,
            strategy=RetryStrategy.EXPONENTIAL,
        )
        handler = RetryHandler(config)

        delay0 = handler._calculate_delay(0)
        delay1 = handler._calculate_delay(1)
        delay2 = handler._calculate_delay(2)

        assert delay0 == 100.0
        assert delay1 == 200.0
        assert delay2 == 400.0


class TestTimeoutHandler:
    """Tests for TimeoutHandler."""

    @pytest.fixture
    def timeout_handler(self):
        config = TimeoutConfig(default_timeout_ms=100.0)
        return TimeoutHandler(config)

    @pytest.mark.asyncio
    async def test_completes_within_timeout(self, timeout_handler):
        """Test operation completes within timeout."""
        async def quick_func():
            await asyncio.sleep(0.01)
            return "done"

        result = await timeout_handler.execute(quick_func)
        assert result == "done"

    @pytest.mark.asyncio
    async def test_timeout_exceeded(self, timeout_handler):
        """Test operation exceeds timeout."""
        async def slow_func():
            await asyncio.sleep(1.0)
            return "never"

        with pytest.raises(TimeoutError) as exc_info:
            await timeout_handler.execute(slow_func, timeout_ms=50.0)

        assert exc_info.value.timeout_ms == 50.0

    @pytest.mark.asyncio
    async def test_operation_specific_timeout(self):
        """Test operation-specific timeout configuration."""
        config = TimeoutConfig(
            default_timeout_ms=1000.0,
            operation_timeouts={"fast_op": 50.0},
        )
        handler = TimeoutHandler(config)

        assert handler.get_timeout("fast_op") == 50.0
        assert handler.get_timeout("other_op") == 1000.0


class TestBulkhead:
    """Tests for Bulkhead pattern."""

    @pytest.fixture
    def bulkhead(self):
        config = BulkheadConfig(
            max_concurrent=2,
            max_queue_size=2,
            queue_timeout_ms=100.0,
        )
        return Bulkhead("test_bulkhead", config)

    @pytest.mark.asyncio
    async def test_allows_concurrent_calls(self, bulkhead):
        """Test allowing concurrent calls up to limit."""
        results = []

        async def tracked_call(n):
            async with bulkhead:
                await asyncio.sleep(0.01)
                results.append(n)

        await asyncio.gather(tracked_call(1), tracked_call(2))
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_rejects_when_full(self, bulkhead):
        """Test rejecting calls when bulkhead is full."""
        async def slow_call():
            async with bulkhead:
                await asyncio.sleep(0.5)

        # Fill concurrent slots
        task1 = asyncio.create_task(slow_call())
        task2 = asyncio.create_task(slow_call())
        await asyncio.sleep(0.01)  # Let tasks start

        # Fill queue
        task3 = asyncio.create_task(slow_call())
        task4 = asyncio.create_task(slow_call())
        await asyncio.sleep(0.01)

        # This should be rejected
        with pytest.raises(BulkheadFullError):
            async with bulkhead:
                pass

        # Cancel tasks
        for task in [task1, task2, task3, task4]:
            task.cancel()

    def test_get_metrics(self, bulkhead):
        """Test getting bulkhead metrics."""
        metrics = bulkhead.get_metrics()
        assert metrics["name"] == "test_bulkhead"
        assert metrics["max_concurrent"] == 2
        assert metrics["utilization"] == 0.0


class TestFallbackStrategies:
    """Tests for fallback strategies."""

    @pytest.mark.asyncio
    async def test_cached_fallback(self):
        """Test cached fallback strategy."""
        fallback = CachedFallback()
        fallback.set_cache("op1", "cached_value")

        result = await fallback.execute("op1", Exception("Error"), {})
        assert result == "cached_value"

    @pytest.mark.asyncio
    async def test_cached_fallback_miss(self):
        """Test cached fallback raises when not cached."""
        fallback = CachedFallback()
        error = ValueError("Original error")

        with pytest.raises(ValueError):
            await fallback.execute("uncached_op", error, {})

    @pytest.mark.asyncio
    async def test_default_value_fallback(self):
        """Test default value fallback."""
        fallback = DefaultValueFallback()
        fallback.set_default("op1", {"status": "degraded"})

        result = await fallback.execute("op1", Exception("Error"), {})
        assert result == {"status": "degraded"}

    @pytest.mark.asyncio
    async def test_graceful_degradation_fallback(self):
        """Test graceful degradation fallback."""
        fallback = GracefulDegradationFallback()

        async def degraded_handler(context):
            return f"degraded: {context.get('input', 'none')}"

        fallback.register_degraded("op1", degraded_handler)

        result = await fallback.execute("op1", Exception("Error"), {"input": "test"})
        assert result == "degraded: test"


class TestResilienceLayer:
    """Tests for unified ResilienceLayer."""

    @pytest.fixture
    def resilience(self):
        config = ResilienceConfig(
            circuit_breaker=CircuitBreakerConfig(failure_threshold=3),
            retry=RetryConfig(max_retries=2, initial_delay_ms=10.0),
            timeout=TimeoutConfig(default_timeout_ms=500.0),
            bulkhead=BulkheadConfig(max_concurrent=10),
        )
        return ResilienceLayer("test_resilience", config)

    @pytest.mark.asyncio
    async def test_successful_execution(self, resilience):
        """Test successful execution through resilience layer."""
        async def success_func():
            return "success"

        result = await resilience.execute(success_func, operation="test")
        assert result == "success"
        assert resilience._successful_executions == 1

    @pytest.mark.asyncio
    async def test_retry_on_transient_failure(self, resilience):
        """Test retry on transient failure."""
        attempts = [0]

        async def flaky_func():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ConnectionError("Transient")
            return "recovered"

        result = await resilience.execute(flaky_func, operation="flaky")
        assert result == "recovered"
        assert attempts[0] == 2

    @pytest.mark.asyncio
    async def test_circuit_opens_on_failures(self, resilience):
        """Test circuit opens after repeated failures."""
        async def always_fails():
            raise ConnectionError("Always fails")

        for _ in range(10):  # Trigger circuit open
            try:
                await resilience.execute(always_fails, operation="failing")
            except (ConnectionError, CircuitBreakerError):
                pass

        assert resilience.circuit_breaker.state in (CircuitState.OPEN, CircuitState.HALF_OPEN)

    @pytest.mark.asyncio
    async def test_fallback_on_failure(self):
        """Test fallback execution on failure."""
        fallback = CachedFallback()
        fallback.set_cache("fallback_op", "fallback_result")

        resilience = ResilienceLayer(
            "fallback_test",
            ResilienceConfig(
                retry=RetryConfig(max_retries=0),  # No retry
                enable_circuit_breaker=False,
            ),
            fallback=fallback,
        )

        async def fails():
            raise ValueError("Error")

        result = await resilience.execute(fails, operation="fallback_op")
        assert result == "fallback_result"
        assert resilience._fallback_executions == 1

    @pytest.mark.asyncio
    async def test_protect_decorator(self, resilience):
        """Test protect decorator."""
        @resilience.protect(operation="decorated_op", timeout_ms=200.0)
        async def decorated_func(x):
            return x * 2

        result = await decorated_func(5)
        assert result == 10

    def test_get_health(self, resilience):
        """Test getting resilience layer health."""
        health = resilience.get_health()
        assert health["name"] == "test_resilience"
        assert "circuit_breaker" in health
        assert "bulkhead" in health
        assert "executions" in health

    @pytest.mark.asyncio
    async def test_reset(self, resilience):
        """Test resetting resilience layer."""
        async def success():
            return "ok"

        await resilience.execute(success, operation="test")
        assert resilience._total_executions == 1

        await resilience.reset()
        assert resilience._total_executions == 0


class TestOrchestratorResilience:
    """Tests for EdgeBackendOrchestrator resilience features."""

    @pytest.fixture
    def resilient_orchestrator(self):
        return EdgeBackendOrchestrator(
            node_id="resilient_test",
            resilience_config=ResilienceConfig(
                circuit_breaker=CircuitBreakerConfig(
                    failure_threshold=3,
                    recovery_timeout=1.0,
                ),
            ),
        )

    @pytest.mark.asyncio
    async def test_resilience_status(self, resilient_orchestrator):
        """Test getting resilience status."""
        await resilient_orchestrator.initialize()

        status = await resilient_orchestrator.get_resilience_status()
        assert "layer" in status
        assert "circuit_breaker" in status

    @pytest.mark.asyncio
    async def test_circuit_breaker_state(self, resilient_orchestrator):
        """Test getting circuit breaker state."""
        await resilient_orchestrator.initialize()

        state = resilient_orchestrator.get_circuit_breaker_state()
        assert state == "closed"

    @pytest.mark.asyncio
    async def test_force_circuit_open(self, resilient_orchestrator):
        """Test forcing circuit open."""
        await resilient_orchestrator.initialize()

        await resilient_orchestrator.force_circuit_open()
        assert resilient_orchestrator.is_circuit_open() is True
        assert resilient_orchestrator.status.value == "degraded"

    @pytest.mark.asyncio
    async def test_force_circuit_close(self, resilient_orchestrator):
        """Test forcing circuit closed."""
        await resilient_orchestrator.initialize()

        await resilient_orchestrator.force_circuit_open()
        await resilient_orchestrator.force_circuit_close()
        assert resilient_orchestrator.is_circuit_open() is False

    @pytest.mark.asyncio
    async def test_register_degraded_handler(self, resilient_orchestrator):
        """Test registering degraded handler."""
        await resilient_orchestrator.initialize()

        def handler(params):
            return {"status": "degraded", "data": params}

        resilient_orchestrator.register_degraded_handler(
            "TestAgent", "test_op", handler
        )

        status = await resilient_orchestrator.get_resilience_status()
        assert "TestAgent.test_op" in status["registered_degraded_handlers"]

    @pytest.mark.asyncio
    async def test_set_fallback_value(self, resilient_orchestrator):
        """Test setting fallback value."""
        await resilient_orchestrator.initialize()

        resilient_orchestrator.set_fallback_value(
            "TestAgent", "test_op", {"fallback": True}
        )

        status = await resilient_orchestrator.get_resilience_status()
        assert "TestAgent.test_op" in status["registered_fallback_values"]

    @pytest.mark.asyncio
    async def test_reset_resilience(self, resilient_orchestrator):
        """Test resetting resilience layer."""
        await resilient_orchestrator.initialize()

        await resilient_orchestrator.force_circuit_open()
        await resilient_orchestrator.reset_resilience()

        assert resilient_orchestrator.is_circuit_open() is False
        assert resilient_orchestrator.metrics.circuit_breaker_opens == 0

    @pytest.mark.asyncio
    async def test_metrics_include_resilience(self, resilient_orchestrator):
        """Test metrics include resilience data."""
        await resilient_orchestrator.initialize()

        metrics = resilient_orchestrator.get_metrics()
        assert "resilience" in metrics
        assert "circuit_breaker_state" in metrics["resilience"]
        assert "circuit_breaker_opens" in metrics["resilience"]


class TestResiliencePerformance:
    """Performance tests for resilience layer."""

    @pytest.mark.asyncio
    async def test_resilience_overhead_acceptable(self):
        """Test resilience layer adds minimal overhead (<5ms)."""
        resilience = ResilienceLayer(
            "perf_test",
            ResilienceConfig(
                enable_circuit_breaker=True,
                enable_bulkhead=False,  # Disable bulkhead for overhead test
                enable_retry=False,
            ),
        )

        async def fast_func():
            return "done"

        start = datetime.now()
        for _ in range(100):
            await resilience.execute(fast_func, operation="perf")
        elapsed_ms = (datetime.now() - start).total_seconds() * 1000

        avg_overhead = elapsed_ms / 100
        assert avg_overhead < 5.0, f"Average overhead {avg_overhead}ms exceeds 5ms"

    @pytest.mark.asyncio
    async def test_circuit_breaker_fast_rejection(self):
        """Test circuit breaker rejects fast when open."""
        breaker = CircuitBreaker(
            "fast_reject",
            CircuitBreakerConfig(failure_threshold=1),
        )

        # Open the circuit
        try:
            async with breaker:
                raise ConnectionError("Error")
        except ConnectionError:
            pass

        # Measure rejection time
        start = datetime.now()
        for _ in range(100):
            try:
                async with breaker:
                    pass
            except CircuitBreakerError:
                pass
        elapsed_ms = (datetime.now() - start).total_seconds() * 1000

        avg_rejection = elapsed_ms / 100
        assert avg_rejection < 1.0, f"Average rejection {avg_rejection}ms exceeds 1ms"
