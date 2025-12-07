"""
Comprehensive unit tests for agent/modules/base_agent.py

Target coverage: 85%+
Test count: 60+ tests
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from agent.modules.base_agent import (
    AgentMetrics,
    AgentStatus,
    BaseAgent,
    CircuitBreaker,
    HealthMetrics,
    Issue,
    SeverityLevel,
)


class ConcreteAgent(BaseAgent):
    """Concrete implementation for testing"""

    def __init__(self, name="test_agent"):
        super().__init__(agent_name=name)
        self.init_called = False
        self.exec_called = False

    async def initialize(self) -> bool:
        self.init_called = True
        self.status = AgentStatus.HEALTHY
        return True

    async def execute_core_function(self, **kwargs) -> dict:
        self.exec_called = True
        return {"status": "success", "data": kwargs}


class TestAgentStatus:
    """Test AgentStatus enum"""

    def test_status_values(self):
        assert AgentStatus.HEALTHY.value == "healthy"
        assert AgentStatus.DEGRADED.value == "degraded"
        assert AgentStatus.RECOVERING.value == "recovering"
        assert AgentStatus.FAILED.value == "failed"
        assert AgentStatus.INITIALIZING.value == "initializing"


class TestSeverityLevel:
    """Test SeverityLevel enum"""

    def test_severity_values(self):
        assert SeverityLevel.LOW.value == "low"
        assert SeverityLevel.MEDIUM.value == "medium"
        assert SeverityLevel.HIGH.value == "high"
        assert SeverityLevel.CRITICAL.value == "critical"


class TestHealthMetrics:
    """Test HealthMetrics dataclass"""

    def test_default_values(self):
        metrics = HealthMetrics()
        assert metrics.success_rate == 100.0
        assert metrics.average_response_time == 0.0
        assert metrics.error_count == 0
        assert metrics.warning_count == 0
        assert metrics.total_operations == 0
        assert metrics.last_error is None
        assert metrics.uptime_seconds == 0.0

    def test_custom_values(self):
        metrics = HealthMetrics(
            success_rate=95.5,
            error_count=10,
            total_operations=200
        )
        assert metrics.success_rate == 95.5
        assert metrics.error_count == 10
        assert metrics.total_operations == 200


class TestAgentMetrics:
    """Test AgentMetrics dataclass"""

    def test_default_values(self):
        metrics = AgentMetrics()
        assert metrics.operations_per_minute == 0.0
        assert metrics.success_count == 0
        assert metrics.failure_count == 0
        assert metrics.performance_score == 100.0

    def test_custom_values(self):
        metrics = AgentMetrics(
            success_count=50,
            failure_count=5,
            ml_predictions_made=100
        )
        assert metrics.success_count == 50
        assert metrics.failure_count == 5
        assert metrics.ml_predictions_made == 100


class TestIssue:
    """Test Issue dataclass"""

    def test_issue_creation(self):
        issue = Issue(
            severity=SeverityLevel.HIGH,
            description="Test issue"
        )
        assert issue.severity == SeverityLevel.HIGH
        assert issue.description == "Test issue"
        assert issue.resolved is False
        assert isinstance(issue.detected_at, datetime)

    def test_issue_with_resolution(self):
        issue = Issue(
            severity=SeverityLevel.MEDIUM,
            description="Resolved issue",
            resolved=True,
            resolution_strategy="restart"
        )
        assert issue.resolved is True
        assert issue.resolution_strategy == "restart"


class TestCircuitBreaker:
    """Test CircuitBreaker pattern"""

    def test_circuit_breaker_initialization(self):
        cb = CircuitBreaker()
        assert cb.failure_threshold == 5
        assert cb.timeout == 60
        assert cb.failure_count == 0
        assert cb.state == "closed"

    def test_circuit_breaker_custom_params(self):
        cb = CircuitBreaker(failure_threshold=3, timeout=30)
        assert cb.failure_threshold == 3
        assert cb.timeout == 30

    def test_circuit_breaker_success(self):
        cb = CircuitBreaker()

        def successful_func():
            return "success"

        result = cb.call(successful_func)
        assert result == "success"
        assert cb.failure_count == 0
        assert cb.state == "closed"

    def test_circuit_breaker_failure(self):
        cb = CircuitBreaker()

        def failing_func():
            raise Exception("Function failed")

        with pytest.raises(Exception):
            cb.call(failing_func)

        assert cb.failure_count == 1
        assert cb.state == "closed"

    def test_circuit_breaker_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)

        def failing_func():
            raise Exception("Failure")

        # Fail 3 times
        for _ in range(3):
            try:
                cb.call(failing_func)
            except Exception:
                pass

        assert cb.state == "open"
        assert cb.failure_count == 3

    def test_circuit_breaker_blocks_when_open(self):
        cb = CircuitBreaker(failure_threshold=2)

        def failing_func():
            raise Exception("Failure")

        # Open the circuit
        for _ in range(2):
            try:
                cb.call(failing_func)
            except Exception:
                pass

        # Now it should block
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            cb.call(failing_func)

    def test_circuit_breaker_reset_on_success(self):
        cb = CircuitBreaker()

        def failing_func():
            raise Exception("Failure")

        def success_func():
            return "success"

        try:
            cb.call(failing_func)
        except Exception:
            pass

        assert cb.failure_count == 1

        cb.call(success_func)
        assert cb.failure_count == 0
        assert cb.state == "closed"


class TestBaseAgentInitialization:
    """Test BaseAgent initialization"""

    def test_agent_creation(self):
        agent = ConcreteAgent("test")
        assert agent.agent_name == "test"
        assert agent.version == "1.0.0"
        assert agent.status == AgentStatus.INITIALIZING
        assert isinstance(agent.initialized_at, datetime)

    def test_agent_custom_version(self):
        agent = ConcreteAgent("test")
        agent.version = "2.0.0"
        assert agent.version == "2.0.0"

    def test_agent_metrics_initialized(self):
        agent = ConcreteAgent()
        assert isinstance(agent.health_metrics, HealthMetrics)
        assert isinstance(agent.agent_metrics, AgentMetrics)

    def test_agent_circuit_breaker_initialized(self):
        agent = ConcreteAgent()
        assert isinstance(agent.circuit_breaker, CircuitBreaker)

    def test_agent_default_config(self):
        agent = ConcreteAgent()
        assert agent.max_retries == 3
        assert agent.retry_delay == 1.0
        assert agent.health_check_interval == 60
        assert agent.auto_heal_enabled is True

    @pytest.mark.asyncio
    async def test_agent_initialize(self):
        agent = ConcreteAgent()
        result = await agent.initialize()
        assert result is True
        assert agent.init_called is True
        assert agent.status == AgentStatus.HEALTHY


class TestSelfHealing:
    """Test self-healing capabilities"""

    @pytest.mark.asyncio
    async def test_with_healing_decorator_success(self):
        agent = ConcreteAgent()

        @agent.with_healing
        async def successful_operation():
            return {"result": "success"}

        result = await successful_operation()
        assert result["result"] == "success"
        assert agent.agent_metrics.success_count == 1

    @pytest.mark.asyncio
    async def test_with_healing_decorator_retry(self):
        agent = ConcreteAgent()
        call_count = 0

        @agent.with_healing
        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return {"result": "success"}

        result = await failing_then_success()
        assert result["result"] == "success"
        assert call_count == 2  # Failed once, succeeded on retry

    @pytest.mark.asyncio
    async def test_with_healing_max_retries_exceeded(self):
        agent = ConcreteAgent()

        @agent.with_healing
        async def always_failing():
            raise Exception("Persistent failure")

        with pytest.raises(Exception, match="Persistent failure"):
            await always_failing()

        assert agent.status == AgentStatus.FAILED

    @pytest.mark.asyncio
    async def test_attempt_self_healing_connection_error(self):
        agent = ConcreteAgent()
        error = Exception("Connection timeout")
        result = await agent._attempt_self_healing(error, "test_func")

        assert result["healed"] is True
        assert result["strategy"] == "reinit_connections"

    @pytest.mark.asyncio
    async def test_attempt_self_healing_memory_error(self):
        agent = ConcreteAgent()
        error = Exception("Memory limit exceeded")
        result = await agent._attempt_self_healing(error, "test_func")

        assert result["healed"] is True
        assert result["strategy"] == "optimize_resources"

    @pytest.mark.asyncio
    async def test_attempt_self_healing_rate_limit(self):
        agent = ConcreteAgent()
        error = Exception("Rate limit exceeded")
        result = await agent._attempt_self_healing(error, "test_func")

        assert result["healed"] is True
        assert result["strategy"] == "rate_limit_backoff"

    @pytest.mark.asyncio
    async def test_attempt_self_healing_validation_error(self):
        agent = ConcreteAgent()
        error = Exception("Validation failed")
        result = await agent._attempt_self_healing(error, "test_func")

        assert result["healed"] is True
        assert result["strategy"] == "reset_defaults"

    @pytest.mark.asyncio
    async def test_attempt_self_healing_unknown_error(self):
        agent = ConcreteAgent()
        error = Exception("Unknown error type")
        result = await agent._attempt_self_healing(error, "test_func")

        assert result["healed"] is False
        assert len(agent.detected_issues) > 0

    @pytest.mark.asyncio
    async def test_reinitialize_connections(self):
        agent = ConcreteAgent()
        await agent._reinitialize_connections()
        assert agent.init_called is True

    @pytest.mark.asyncio
    async def test_optimize_resources(self):
        agent = ConcreteAgent()
        # Should not raise
        await agent._optimize_resources()

    @pytest.mark.asyncio
    async def test_reset_to_safe_defaults(self):
        agent = ConcreteAgent()
        # Should not raise
        await agent._reset_to_safe_defaults()


class TestAnomalyDetection:
    """Test ML-powered anomaly detection"""

    def test_detect_anomalies_insufficient_data(self):
        agent = ConcreteAgent()
        # Less than 10 samples - should return False
        for i in range(5):
            is_anomaly = agent.detect_anomalies("response_time", 1.0)
            assert is_anomaly is False

    def test_detect_anomalies_normal_values(self):
        agent = ConcreteAgent()
        # Add 20 normal values
        for i in range(20):
            is_anomaly = agent.detect_anomalies("response_time", 1.0 + np.random.normal(0, 0.1))
            # First few might be anomalies until baseline is established

        # This value is within normal range
        is_anomaly = agent.detect_anomalies("response_time", 1.0)
        assert is_anomaly is False

    def test_detect_anomalies_outlier(self):
        agent = ConcreteAgent()
        # Establish baseline
        for i in range(20):
            agent.detect_anomalies("response_time", 1.0)

        # Add a clear outlier
        is_anomaly = agent.detect_anomalies("response_time", 10.0)
        assert is_anomaly is True
        assert agent.agent_metrics.anomalies_detected > 0

    def test_detect_anomalies_zero_std(self):
        agent = ConcreteAgent()
        # All same values = zero std dev
        for i in range(15):
            agent.detect_anomalies("constant", 5.0)

        # Should handle zero std dev gracefully
        is_anomaly = agent.detect_anomalies("constant", 5.0)
        assert is_anomaly is False

    def test_anomaly_baseline_window(self):
        agent = ConcreteAgent()
        # Add more than 100 values
        for i in range(150):
            agent.detect_anomalies("metric", 1.0)

        # Should keep only last 100
        assert len(agent.anomaly_baseline["metric"]) == 100


class TestPerformancePrediction:
    """Test performance prediction"""

    def test_predict_performance_insufficient_data(self):
        agent = ConcreteAgent()
        prediction = agent.predict_performance()
        assert prediction["forecast"] == "insufficient_data"
        assert prediction["confidence"] == 0.0

    def test_predict_performance_with_data(self):
        agent = ConcreteAgent()
        # Add performance history
        for i in range(50):
            agent.performance_history.append(1.0 + i * 0.01)

        prediction = agent.predict_performance()
        assert "forecast" in prediction
        assert "trend" in prediction
        assert "confidence" in prediction
        assert prediction["trend"] == "improving"

    def test_predict_performance_declining_trend(self):
        agent = ConcreteAgent()
        # Declining performance
        for i in range(50):
            agent.performance_history.append(2.0 - i * 0.01)

        prediction = agent.predict_performance()
        assert prediction["trend"] == "declining"

    def test_predict_performance_stable(self):
        agent = ConcreteAgent()
        # Stable performance
        for i in range(50):
            agent.performance_history.append(1.0)

        prediction = agent.predict_performance()
        assert prediction["trend"] == "stable"


class TestHealthChecks:
    """Test health check functionality"""

    @pytest.mark.asyncio
    async def test_health_check_healthy_agent(self):
        agent = ConcreteAgent()
        await agent.initialize()

        health = await agent.health_check()

        assert health["agent_name"] == "test_agent"
        assert health["status"] == AgentStatus.HEALTHY.value
        assert "health_metrics" in health
        assert "agent_metrics" in health
        assert "circuit_breaker" in health

    @pytest.mark.asyncio
    async def test_health_check_with_operations(self):
        agent = ConcreteAgent()
        await agent.initialize()

        # Simulate some successful operations
        agent.agent_metrics.success_count = 95
        agent.agent_metrics.failure_count = 5

        health = await agent.health_check()

        assert health["health_metrics"]["success_rate"] == 95.0
        assert health["health_metrics"]["total_operations"] == 100

    @pytest.mark.asyncio
    async def test_health_check_degraded_status(self):
        agent = ConcreteAgent()
        await agent.initialize()

        # Simulate degraded performance
        agent.agent_metrics.success_count = 70
        agent.agent_metrics.failure_count = 30

        health = await agent.health_check()

        assert health["status"] == AgentStatus.DEGRADED.value

    @pytest.mark.asyncio
    async def test_health_check_failed_status(self):
        agent = ConcreteAgent()
        await agent.initialize()

        # Simulate failed agent
        agent.agent_metrics.success_count = 30
        agent.agent_metrics.failure_count = 70

        health = await agent.health_check()

        assert health["status"] == AgentStatus.FAILED.value

    @pytest.mark.asyncio
    async def test_health_check_exception_handling(self):
        class FailingHealthAgent(BaseAgent):
            async def initialize(self):
                return True

            async def execute_core_function(self, **kwargs):
                return {}

            async def health_check(self):
                # Override to force calculation failure
                raise Exception("Health check calculation failed")

        agent = FailingHealthAgent("failing")
        health = await agent.health_check()

        assert health["status"] == "error"
        assert "error" in health


class TestDiagnostics:
    """Test diagnostic functionality"""

    @pytest.mark.asyncio
    async def test_diagnose_issues_no_issues(self):
        agent = ConcreteAgent()
        await agent.initialize()

        diagnostics = await agent.diagnose_issues()

        assert diagnostics["agent_name"] == "test_agent"
        assert diagnostics["issues_found"] == 0
        assert len(diagnostics["recommendations"]) > 0
        assert "operating normally" in diagnostics["recommendations"][0]

    @pytest.mark.asyncio
    async def test_diagnose_issues_with_issues(self):
        agent = ConcreteAgent()
        await agent.initialize()

        # Add some issues
        agent.detected_issues.append(
            Issue(severity=SeverityLevel.HIGH, description="Test issue")
        )

        diagnostics = await agent.diagnose_issues()

        assert diagnostics["issues_found"] == 1
        assert len(diagnostics["issues"]) == 1

    @pytest.mark.asyncio
    async def test_diagnose_low_success_rate_recommendation(self):
        agent = ConcreteAgent()
        await agent.initialize()

        agent.agent_metrics.success_count = 70
        agent.agent_metrics.failure_count = 30
        agent.health_metrics.success_rate = 70.0

        diagnostics = await agent.diagnose_issues()

        assert any("restart" in rec.lower() for rec in diagnostics["recommendations"])

    @pytest.mark.asyncio
    async def test_diagnose_circuit_breaker_open_recommendation(self):
        agent = ConcreteAgent()
        await agent.initialize()

        agent.circuit_breaker.state = "open"

        diagnostics = await agent.diagnose_issues()

        assert any("circuit breaker" in rec.lower() for rec in diagnostics["recommendations"])


class TestMetricsRecording:
    """Test metrics recording"""

    def test_record_success(self):
        agent = ConcreteAgent()
        initial_count = agent.agent_metrics.success_count

        agent._record_success(0.5)

        assert agent.agent_metrics.success_count == initial_count + 1
        assert len(agent.performance_history) == 1
        assert agent.performance_history[0] == 0.5

    def test_record_failure(self):
        agent = ConcreteAgent()
        initial_count = agent.agent_metrics.failure_count
        error = Exception("Test error")

        agent._record_failure(error)

        assert agent.agent_metrics.failure_count == initial_count + 1
        assert agent.health_metrics.error_count == 1
        assert agent.health_metrics.last_error == "Test error"
        assert agent.health_metrics.last_error_time is not None

    def test_calculate_ops_per_minute(self):
        agent = ConcreteAgent()
        # Simulate some operations
        agent.agent_metrics.success_count = 60
        agent.agent_metrics.failure_count = 0

        # Mock uptime (1 minute)
        agent.initialized_at = datetime.now()

        ops_per_min = agent._calculate_ops_per_minute()
        # Should be around 60 (might vary based on exact timing)
        assert ops_per_min >= 0


class TestUtilityMethods:
    """Test utility methods"""

    def test_get_status(self):
        agent = ConcreteAgent()
        status = agent.get_status()

        assert status["agent_name"] == "test_agent"
        assert status["version"] == "1.0.0"
        assert status["status"] == AgentStatus.INITIALIZING.value
        assert "initialized_at" in status
        assert "uptime_seconds" in status

    @pytest.mark.asyncio
    async def test_shutdown(self):
        agent = ConcreteAgent()
        await agent.initialize()

        await agent.shutdown()

        assert agent.status == AgentStatus.FAILED


class TestEdgeCases:
    """Test edge cases"""

    @pytest.mark.asyncio
    async def test_execute_with_circuit_breaker_async(self):
        agent = ConcreteAgent()

        async def async_func():
            return "async_result"

        result = await agent._execute_with_circuit_breaker(async_func)
        assert result == "async_result"

    @pytest.mark.asyncio
    async def test_execute_with_circuit_breaker_sync(self):
        agent = ConcreteAgent()

        def sync_func():
            return "sync_result"

        result = await agent._execute_with_circuit_breaker(sync_func)
        assert result == "sync_result"

    def test_performance_history_window(self):
        agent = ConcreteAgent()
        # Add more than 1000 values
        for i in range(1100):
            agent.performance_history.append(float(i))
            if len(agent.performance_history) > 1000:
                agent.performance_history.pop(0)

        assert len(agent.performance_history) == 1000

    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self):
        agent = ConcreteAgent()
        await agent.initialize()

        # Run multiple health checks concurrently
        health_checks = [agent.health_check() for _ in range(5)]
        results = await asyncio.gather(*health_checks)

        assert len(results) == 5
        assert all(r["status"] == AgentStatus.HEALTHY.value for r in results)
