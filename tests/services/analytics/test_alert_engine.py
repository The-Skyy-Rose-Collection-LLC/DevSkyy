# tests/services/analytics/test_alert_engine.py
"""
Unit tests for AlertEvaluationEngine.

Tests cover:
- Alert condition evaluation (all operators)
- Cooldown management to prevent spam
- Alert history recording
- Scheduled evaluation loop
- Custom metric provider support
- Error handling and recovery

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest

from services.analytics.alert_engine import (
    AlertConfig,
    AlertConfigNotFoundError,
    AlertEngineError,
    AlertEvaluationEngine,
    AlertSeverity,
    AlertStatus,
    AlertTrigger,
    ConditionOperator,
    ConditionType,
    MetricValue,
)

# =============================================================================
# Fixtures
# =============================================================================


class MockSession:
    """Mock async session for testing."""

    def __init__(self) -> None:
        self.executed: list[tuple[Any, Any]] = []
        self.committed = False
        self.rolled_back = False
        self._mock_configs: list[tuple[Any, ...]] = []
        self._mock_metric_value: Decimal | None = None

    async def execute(self, query: Any, params: Any = None) -> MockResult:
        self.executed.append((query, params))
        return MockResult(self._mock_configs, self._mock_metric_value)

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True

    def set_mock_configs(self, configs: list[tuple[Any, ...]]) -> None:
        self._mock_configs = configs

    def set_mock_metric_value(self, value: Decimal | None) -> None:
        self._mock_metric_value = value


class MockResult:
    """Mock query result."""

    def __init__(
        self,
        mock_configs: list[tuple[Any, ...]],
        mock_metric_value: Decimal | None = None,
    ) -> None:
        self._mock_configs = mock_configs
        self._mock_metric_value = mock_metric_value

    def fetchall(self) -> list[tuple[Any, ...]]:
        return self._mock_configs

    def first(self) -> MockRow | None:
        if self._mock_metric_value is not None:
            return MockRow(self._mock_metric_value)
        return None


class MockRow:
    """Mock row with value attribute."""

    def __init__(self, value: Decimal) -> None:
        self.value = value


class MockSessionFactory:
    """Mock session factory for testing."""

    def __init__(self, session: MockSession | None = None) -> None:
        self.session = session or MockSession()
        self.call_count = 0

    def __call__(self) -> MockSessionContextManager:
        self.call_count += 1
        return MockSessionContextManager(self.session)


class MockSessionContextManager:
    """Context manager wrapper for mock session."""

    def __init__(self, session: MockSession) -> None:
        self.session = session

    async def __aenter__(self) -> MockSession:
        return self.session

    async def __aexit__(self, *args: Any) -> None:
        pass


class MockMetricProvider:
    """Mock metric provider for testing."""

    def __init__(self, default_value: Decimal | None = None) -> None:
        self._values: dict[str, Decimal] = {}
        self._default_value = default_value

    def set_metric(self, metric_name: str, value: Decimal) -> None:
        self._values[metric_name] = value

    async def get_metric(
        self,
        metric_name: str,
        window_seconds: int,
        filters: dict[str, Any],
    ) -> Decimal | None:
        return self._values.get(metric_name, self._default_value)


@pytest.fixture
def mock_session() -> MockSession:
    """Create a mock database session."""
    return MockSession()


@pytest.fixture
def mock_session_factory(mock_session: MockSession) -> MockSessionFactory:
    """Create a mock session factory."""
    return MockSessionFactory(mock_session)


@pytest.fixture
def engine(mock_session_factory: MockSessionFactory) -> AlertEvaluationEngine:
    """Create an alert evaluation engine for testing."""
    return AlertEvaluationEngine(
        mock_session_factory,
        evaluation_interval=0.1,  # 100ms for testing
    )


@pytest.fixture
def sample_alert_config() -> AlertConfig:
    """Create a sample alert configuration."""
    return AlertConfig(
        id=uuid.uuid4(),
        name="High Error Rate",
        description="Alert when error rate exceeds threshold",
        metric_name="error_count",
        condition_type=ConditionType.THRESHOLD,
        condition_operator=ConditionOperator.GT,
        threshold_value=Decimal("100"),
        threshold_unit="errors/min",
        window_duration_seconds=300,
        evaluation_interval_seconds=60,
        cooldown_seconds=300,
        severity=AlertSeverity.CRITICAL,
        is_enabled=True,
    )


# =============================================================================
# AlertConfig Model Tests
# =============================================================================


class TestAlertConfig:
    """Tests for AlertConfig model."""

    def test_create_config_with_required_fields(self) -> None:
        """Test creating config with required fields."""
        config = AlertConfig(
            id=uuid.uuid4(),
            name="Test Alert",
            metric_name="test_metric",
            condition_type=ConditionType.THRESHOLD,
            condition_operator=ConditionOperator.GT,
        )

        assert config.name == "Test Alert"
        assert config.metric_name == "test_metric"
        assert config.condition_type == ConditionType.THRESHOLD
        assert config.is_enabled is True
        assert config.severity == AlertSeverity.WARNING

    def test_create_config_with_all_fields(self) -> None:
        """Test creating config with all fields."""
        config_id = uuid.uuid4()
        user_id = uuid.uuid4()

        config = AlertConfig(
            id=config_id,
            name="Critical Alert",
            description="This is a critical alert",
            metric_name="error_rate",
            condition_type=ConditionType.THRESHOLD,
            condition_operator=ConditionOperator.GTE,
            threshold_value=Decimal("95.5"),
            threshold_unit="percent",
            window_duration_seconds=600,
            evaluation_interval_seconds=30,
            cooldown_seconds=600,
            severity=AlertSeverity.CRITICAL,
            is_enabled=True,
            notification_channels=["email", "slack"],
            notification_config={"email": "admin@example.com"},
            filters={"source": "api"},
            created_by=user_id,
        )

        assert config.id == config_id
        assert config.threshold_value == Decimal("95.5")
        assert config.cooldown_seconds == 600
        assert len(config.notification_channels) == 2


class TestAlertTrigger:
    """Tests for AlertTrigger model."""

    def test_create_trigger_with_defaults(self) -> None:
        """Test creating trigger with default values."""
        config_id = uuid.uuid4()

        trigger = AlertTrigger(
            alert_config_id=config_id,
            severity=AlertSeverity.WARNING,
            title="Test Alert Triggered",
        )

        assert trigger.id is not None
        assert trigger.alert_config_id == config_id
        assert trigger.status == AlertStatus.TRIGGERED
        assert trigger.triggered_at is not None

    def test_create_trigger_with_context(self) -> None:
        """Test creating trigger with context."""
        config_id = uuid.uuid4()

        trigger = AlertTrigger(
            alert_config_id=config_id,
            severity=AlertSeverity.CRITICAL,
            title="Critical Error Rate",
            message="Error rate exceeded 100 errors/min",
            metric_value=Decimal("150"),
            threshold_value=Decimal("100"),
            context={
                "correlation_id": "test-123",
                "metric_name": "error_count",
            },
        )

        assert trigger.metric_value == Decimal("150")
        assert trigger.context["correlation_id"] == "test-123"


# =============================================================================
# Condition Evaluation Tests
# =============================================================================


class TestConditionEvaluation:
    """Tests for condition evaluation logic."""

    def test_greater_than_true(self, engine: AlertEvaluationEngine) -> None:
        """Test GT operator when condition is met."""
        result = engine._evaluate_condition(
            metric_value=Decimal("150"),
            condition_type=ConditionType.THRESHOLD,
            operator=ConditionOperator.GT,
            threshold=Decimal("100"),
        )
        assert result is True

    def test_greater_than_false(self, engine: AlertEvaluationEngine) -> None:
        """Test GT operator when condition is not met."""
        result = engine._evaluate_condition(
            metric_value=Decimal("50"),
            condition_type=ConditionType.THRESHOLD,
            operator=ConditionOperator.GT,
            threshold=Decimal("100"),
        )
        assert result is False

    def test_greater_than_equal_boundary(self, engine: AlertEvaluationEngine) -> None:
        """Test GT operator with equal values returns false."""
        result = engine._evaluate_condition(
            metric_value=Decimal("100"),
            condition_type=ConditionType.THRESHOLD,
            operator=ConditionOperator.GT,
            threshold=Decimal("100"),
        )
        assert result is False

    def test_less_than_true(self, engine: AlertEvaluationEngine) -> None:
        """Test LT operator when condition is met."""
        result = engine._evaluate_condition(
            metric_value=Decimal("50"),
            condition_type=ConditionType.THRESHOLD,
            operator=ConditionOperator.LT,
            threshold=Decimal("100"),
        )
        assert result is True

    def test_less_than_false(self, engine: AlertEvaluationEngine) -> None:
        """Test LT operator when condition is not met."""
        result = engine._evaluate_condition(
            metric_value=Decimal("150"),
            condition_type=ConditionType.THRESHOLD,
            operator=ConditionOperator.LT,
            threshold=Decimal("100"),
        )
        assert result is False

    def test_greater_than_or_equal_true(self, engine: AlertEvaluationEngine) -> None:
        """Test GTE operator with equal values."""
        result = engine._evaluate_condition(
            metric_value=Decimal("100"),
            condition_type=ConditionType.THRESHOLD,
            operator=ConditionOperator.GTE,
            threshold=Decimal("100"),
        )
        assert result is True

    def test_less_than_or_equal_true(self, engine: AlertEvaluationEngine) -> None:
        """Test LTE operator with equal values."""
        result = engine._evaluate_condition(
            metric_value=Decimal("100"),
            condition_type=ConditionType.THRESHOLD,
            operator=ConditionOperator.LTE,
            threshold=Decimal("100"),
        )
        assert result is True

    def test_equal_true(self, engine: AlertEvaluationEngine) -> None:
        """Test EQ operator when values match."""
        result = engine._evaluate_condition(
            metric_value=Decimal("100"),
            condition_type=ConditionType.THRESHOLD,
            operator=ConditionOperator.EQ,
            threshold=Decimal("100"),
        )
        assert result is True

    def test_not_equal_true(self, engine: AlertEvaluationEngine) -> None:
        """Test NEQ operator when values differ."""
        result = engine._evaluate_condition(
            metric_value=Decimal("150"),
            condition_type=ConditionType.THRESHOLD,
            operator=ConditionOperator.NEQ,
            threshold=Decimal("100"),
        )
        assert result is True

    def test_null_threshold_returns_false(self, engine: AlertEvaluationEngine) -> None:
        """Test that null threshold always returns false."""
        result = engine._evaluate_condition(
            metric_value=Decimal("100"),
            condition_type=ConditionType.THRESHOLD,
            operator=ConditionOperator.GT,
            threshold=None,
        )
        assert result is False

    def test_string_operator_values(self, engine: AlertEvaluationEngine) -> None:
        """Test that string operator values work correctly."""
        result = engine._evaluate_condition(
            metric_value=Decimal("150"),
            condition_type="threshold",
            operator="gt",
            threshold=Decimal("100"),
        )
        assert result is True


# =============================================================================
# Cooldown Tests
# =============================================================================


class TestCooldown:
    """Tests for cooldown management."""

    def test_not_in_cooldown_initially(self, engine: AlertEvaluationEngine) -> None:
        """Test that alerts are not in cooldown initially."""
        config_id = uuid.uuid4()
        assert engine.is_in_cooldown(config_id, 300) is False

    def test_in_cooldown_after_trigger(self, engine: AlertEvaluationEngine) -> None:
        """Test that cooldown is set after trigger."""
        config_id = uuid.uuid4()

        # Simulate trigger by setting cooldown
        engine._cooldown_tracker[config_id] = datetime.now(UTC)

        assert engine.is_in_cooldown(config_id, 300) is True

    def test_cooldown_expires(self, engine: AlertEvaluationEngine) -> None:
        """Test that cooldown expires after period."""
        config_id = uuid.uuid4()

        # Set cooldown to past time
        engine._cooldown_tracker[config_id] = datetime.now(UTC) - timedelta(seconds=400)

        # 300 second cooldown should have expired
        assert engine.is_in_cooldown(config_id, 300) is False

    def test_clear_cooldown(self, engine: AlertEvaluationEngine) -> None:
        """Test clearing cooldown."""
        config_id = uuid.uuid4()
        engine._cooldown_tracker[config_id] = datetime.now(UTC)

        assert engine.is_in_cooldown(config_id, 300) is True

        engine.clear_cooldown(config_id)

        assert engine.is_in_cooldown(config_id, 300) is False

    def test_clear_nonexistent_cooldown(self, engine: AlertEvaluationEngine) -> None:
        """Test clearing cooldown that doesn't exist doesn't raise."""
        config_id = uuid.uuid4()
        # Should not raise
        engine.clear_cooldown(config_id)
        assert config_id not in engine._cooldown_tracker


# =============================================================================
# Engine Lifecycle Tests
# =============================================================================


class TestEngineLifecycle:
    """Tests for engine start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_creates_task(self, engine: AlertEvaluationEngine) -> None:
        """Test that start creates the evaluation task."""
        await engine.start()
        try:
            assert engine._running is True
            assert engine._evaluation_task is not None
        finally:
            await engine.stop()

    @pytest.mark.asyncio
    async def test_stop_cancels_task(self, engine: AlertEvaluationEngine) -> None:
        """Test that stop cancels the evaluation task."""
        await engine.start()
        await engine.stop()

        assert engine._running is False

    @pytest.mark.asyncio
    async def test_double_start_is_idempotent(
        self,
        engine: AlertEvaluationEngine,
    ) -> None:
        """Test that calling start twice doesn't create duplicate tasks."""
        await engine.start()
        task1 = engine._evaluation_task

        await engine.start()
        task2 = engine._evaluation_task

        try:
            assert task1 is task2
        finally:
            await engine.stop()

    @pytest.mark.asyncio
    async def test_double_stop_is_idempotent(
        self,
        engine: AlertEvaluationEngine,
    ) -> None:
        """Test that calling stop twice doesn't raise."""
        await engine.start()
        await engine.stop()
        await engine.stop()  # Should not raise

        assert engine._running is False


# =============================================================================
# Statistics Tests
# =============================================================================


class TestStatistics:
    """Tests for engine statistics."""

    def test_initial_stats(self, engine: AlertEvaluationEngine) -> None:
        """Test initial statistics values."""
        stats = engine.stats

        assert stats["evaluations_run"] == 0
        assert stats["alerts_triggered"] == 0
        assert stats["alerts_skipped_cooldown"] == 0
        assert stats["evaluation_errors"] == 0
        assert stats["running"] is False

    @pytest.mark.asyncio
    async def test_stats_after_start(self, engine: AlertEvaluationEngine) -> None:
        """Test statistics after starting engine."""
        await engine.start()
        try:
            assert engine.stats["running"] is True
        finally:
            await engine.stop()


# =============================================================================
# Alert Title/Message Building Tests
# =============================================================================


class TestAlertMessageBuilding:
    """Tests for alert title and message building."""

    def test_build_alert_title_gt(
        self,
        engine: AlertEvaluationEngine,
        sample_alert_config: AlertConfig,
    ) -> None:
        """Test building alert title for GT operator."""
        title = engine._build_alert_title(sample_alert_config, Decimal("150"))

        assert "CRITICAL" in title
        assert "High Error Rate" in title
        assert "exceeded" in title
        assert "100" in title

    def test_build_alert_title_lt(
        self,
        engine: AlertEvaluationEngine,
    ) -> None:
        """Test building alert title for LT operator."""
        config = AlertConfig(
            id=uuid.uuid4(),
            name="Low Response Time",
            metric_name="response_time",
            condition_type=ConditionType.THRESHOLD,
            condition_operator=ConditionOperator.LT,
            threshold_value=Decimal("10"),
            threshold_unit="ms",
            severity=AlertSeverity.WARNING,
        )

        title = engine._build_alert_title(config, Decimal("5"))

        assert "WARNING" in title
        assert "dropped below" in title

    def test_build_alert_message(
        self,
        engine: AlertEvaluationEngine,
        sample_alert_config: AlertConfig,
    ) -> None:
        """Test building detailed alert message."""
        message = engine._build_alert_message(sample_alert_config, Decimal("150"))

        assert "High Error Rate" in message
        assert "error_count" in message
        assert "150" in message
        assert "100" in message
        assert "critical" in message


# =============================================================================
# Custom Metric Provider Tests
# =============================================================================


class TestCustomMetricProvider:
    """Tests for custom metric provider support."""

    @pytest.mark.asyncio
    async def test_uses_custom_provider(
        self,
        mock_session_factory: MockSessionFactory,
    ) -> None:
        """Test that custom metric provider is used when set."""
        provider = MockMetricProvider()
        provider.set_metric("error_count", Decimal("150"))

        engine = AlertEvaluationEngine(
            mock_session_factory,
            metric_provider=provider,
        )

        async with mock_session_factory() as session:
            value = await engine._get_metric_value(
                session,
                "error_count",
                300,
                {},
            )

        assert value == Decimal("150")

    @pytest.mark.asyncio
    async def test_provider_returns_none(
        self,
        mock_session_factory: MockSessionFactory,
    ) -> None:
        """Test handling when provider returns None."""
        provider = MockMetricProvider(default_value=None)

        engine = AlertEvaluationEngine(
            mock_session_factory,
            metric_provider=provider,
        )

        async with mock_session_factory() as session:
            value = await engine._get_metric_value(
                session,
                "nonexistent_metric",
                300,
                {},
            )

        assert value is None


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    def test_alert_engine_error_creation(self) -> None:
        """Test creating AlertEngineError."""
        error = AlertEngineError(
            "Test error",
            correlation_id="test-123",
            context={"key": "value"},
        )

        assert error.message == "Test error"
        assert error.correlation_id == "test-123"
        assert error.context == {"key": "value"}

    def test_alert_config_not_found_error(self) -> None:
        """Test creating AlertConfigNotFoundError."""
        config_id = str(uuid.uuid4())
        error = AlertConfigNotFoundError(
            config_id,
            correlation_id="test-456",
        )

        assert config_id in error.message
        assert error.context["alert_config_id"] == config_id


# =============================================================================
# Enum Tests
# =============================================================================


class TestEnums:
    """Tests for enum values."""

    def test_condition_type_values(self) -> None:
        """Test ConditionType enum values."""
        assert ConditionType.THRESHOLD.value == "threshold"
        assert ConditionType.ANOMALY.value == "anomaly"
        assert ConditionType.RATE.value == "rate"

    def test_condition_operator_values(self) -> None:
        """Test ConditionOperator enum values."""
        assert ConditionOperator.GT.value == "gt"
        assert ConditionOperator.LT.value == "lt"
        assert ConditionOperator.GTE.value == "gte"
        assert ConditionOperator.LTE.value == "lte"
        assert ConditionOperator.EQ.value == "eq"
        assert ConditionOperator.NEQ.value == "neq"

    def test_alert_severity_values(self) -> None:
        """Test AlertSeverity enum values."""
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.CRITICAL.value == "critical"

    def test_alert_status_values(self) -> None:
        """Test AlertStatus enum values."""
        assert AlertStatus.TRIGGERED.value == "triggered"
        assert AlertStatus.RESOLVED.value == "resolved"
        assert AlertStatus.ACKNOWLEDGED.value == "acknowledged"


# =============================================================================
# MetricValue Model Tests
# =============================================================================


class TestMetricValue:
    """Tests for MetricValue model."""

    def test_create_metric_value(self) -> None:
        """Test creating a MetricValue."""
        metric = MetricValue(
            metric_name="error_count",
            value=Decimal("150"),
        )

        assert metric.metric_name == "error_count"
        assert metric.value == Decimal("150")
        assert metric.timestamp is not None
        assert metric.dimensions == {}

    def test_create_metric_value_with_dimensions(self) -> None:
        """Test creating MetricValue with dimensions."""
        metric = MetricValue(
            metric_name="api_latency",
            value=Decimal("45.5"),
            dimensions={"endpoint": "/api/users", "method": "GET"},
        )

        assert metric.dimensions["endpoint"] == "/api/users"
        assert len(metric.dimensions) == 2
