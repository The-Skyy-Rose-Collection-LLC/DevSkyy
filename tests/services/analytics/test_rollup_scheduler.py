# tests/services/analytics/test_rollup_scheduler.py
"""
Unit tests for RollupScheduler.

Tests cover:
- Rollup scheduling and execution
- Hourly, daily, weekly aggregations
- Event cleanup after retention period
- Statistics tracking
- Error handling
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest

from services.analytics.rollup_scheduler import (
    RollupDimension,
    RollupGranularity,
    RollupResult,
    RollupScheduler,
    RollupSchedulerError,
)

# =============================================================================
# Fixtures
# =============================================================================


class MockSession:
    """Mock async session for testing."""

    def __init__(self) -> None:
        self.executed: list[tuple[Any, Any]] = []
        self.committed = False
        self.rowcount = 0
        self._results: list[Any] = []

    async def execute(self, query: Any, params: Any = None) -> MockResult:
        self.executed.append((query, params))
        return MockResult(self._results, self.rowcount)

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass

    def set_results(self, results: list[Any]) -> None:
        self._results = results


class MockResult:
    """Mock result object."""

    def __init__(self, results: list[Any], rowcount: int = 0) -> None:
        self._results = results
        self.rowcount = rowcount

    def fetchall(self) -> list[Any]:
        return self._results


class MockRow:
    """Mock row from database result."""

    def __init__(
        self,
        dimension: str,
        dimension_value: str,
        count: int,
        sum_value: float | None = None,
        avg_value: float | None = None,
        min_value: float | None = None,
        max_value: float | None = None,
        p50_value: float | None = None,
        p95_value: float | None = None,
        p99_value: float | None = None,
    ) -> None:
        self.dimension = dimension
        self.dimension_value = dimension_value
        self.count = count
        self.sum_value = sum_value
        self.avg_value = avg_value
        self.min_value = min_value
        self.max_value = max_value
        self.p50_value = p50_value
        self.p95_value = p95_value
        self.p99_value = p99_value


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


@pytest.fixture
def mock_session() -> MockSession:
    """Create a mock database session."""
    return MockSession()


@pytest.fixture
def mock_session_factory(mock_session: MockSession) -> MockSessionFactory:
    """Create a mock session factory."""
    return MockSessionFactory(mock_session)


@pytest.fixture
def scheduler(mock_session_factory: MockSessionFactory) -> RollupScheduler:
    """Create a rollup scheduler for testing."""
    return RollupScheduler(
        mock_session_factory,
        retention_days=7,
        hourly_interval=0.1,  # Fast interval for testing
    )


# =============================================================================
# RollupResult Model Tests
# =============================================================================


class TestRollupResult:
    """Tests for RollupResult model."""

    def test_create_result_with_defaults(self) -> None:
        """Test creating rollup result with minimal fields."""
        result = RollupResult(
            metric_name="events.event_type",
            dimension="event_type",
            granularity=RollupGranularity.HOUR,
            period_start=datetime.now(UTC),
            period_end=datetime.now(UTC) + timedelta(hours=1),
        )

        assert result.id is not None
        assert result.metric_name == "events.event_type"
        assert result.dimension == "event_type"
        assert result.count == 0
        assert result.metadata == {}

    def test_create_result_with_all_fields(self) -> None:
        """Test creating rollup result with all fields."""
        now = datetime.now(UTC)
        result = RollupResult(
            metric_name="events.source",
            dimension="source",
            dimension_value="api",
            granularity=RollupGranularity.DAY,
            period_start=now,
            period_end=now + timedelta(days=1),
            count=100,
            sum_value=Decimal("5000.50"),
            avg_value=Decimal("50.005"),
            min_value=Decimal("1.00"),
            max_value=Decimal("500.00"),
            p50_value=Decimal("25.00"),
            p95_value=Decimal("450.00"),
            p99_value=Decimal("495.00"),
            metadata={"tags": ["production"]},
        )

        assert result.count == 100
        assert result.sum_value == Decimal("5000.50")
        assert result.p95_value == Decimal("450.00")

    def test_granularity_enum_values(self) -> None:
        """Test all granularity enum values."""
        assert RollupGranularity.MINUTE.value == "minute"
        assert RollupGranularity.HOUR.value == "hour"
        assert RollupGranularity.DAY.value == "day"
        assert RollupGranularity.WEEK.value == "week"
        assert RollupGranularity.MONTH.value == "month"

    def test_dimension_enum_values(self) -> None:
        """Test all dimension enum values."""
        assert RollupDimension.EVENT_TYPE.value == "event_type"
        assert RollupDimension.EVENT_NAME.value == "event_name"
        assert RollupDimension.SOURCE.value == "source"
        assert RollupDimension.GEO_COUNTRY.value == "geo_country"


# =============================================================================
# RollupScheduler Tests
# =============================================================================


class TestRollupScheduler:
    """Tests for RollupScheduler."""

    @pytest.mark.asyncio
    async def test_start_creates_tasks(
        self,
        scheduler: RollupScheduler,
    ) -> None:
        """Test that start creates the background tasks."""
        await scheduler.start()
        try:
            assert scheduler._running
            assert scheduler._hourly_task is not None
            assert scheduler._daily_task is not None
            assert scheduler._weekly_task is not None
            assert scheduler._cleanup_task is not None
        finally:
            await scheduler.stop()

    @pytest.mark.asyncio
    async def test_start_when_already_running(
        self,
        scheduler: RollupScheduler,
    ) -> None:
        """Test that start is idempotent."""
        await scheduler.start()
        try:
            first_hourly_task = scheduler._hourly_task
            await scheduler.start()  # Should not create new tasks
            assert scheduler._hourly_task is first_hourly_task
        finally:
            await scheduler.stop()

    @pytest.mark.asyncio
    async def test_stop_cleans_up_tasks(
        self,
        scheduler: RollupScheduler,
    ) -> None:
        """Test that stop cancels all tasks."""
        await scheduler.start()
        await scheduler.stop()

        assert not scheduler._running
        assert scheduler._hourly_task is None
        assert scheduler._daily_task is None
        assert scheduler._weekly_task is None
        assert scheduler._cleanup_task is None

    @pytest.mark.asyncio
    async def test_stop_when_not_running(
        self,
        scheduler: RollupScheduler,
    ) -> None:
        """Test that stop is safe when not running."""
        await scheduler.stop()  # Should not raise
        assert not scheduler._running

    @pytest.mark.asyncio
    async def test_stats_tracking(
        self,
        scheduler: RollupScheduler,
    ) -> None:
        """Test that stats are tracked correctly."""
        stats = scheduler.stats

        assert stats["hourly_rollups_completed"] == 0
        assert stats["daily_rollups_completed"] == 0
        assert stats["weekly_rollups_completed"] == 0
        assert stats["events_cleaned"] == 0
        assert stats["rollup_errors"] == 0
        assert stats["last_hourly_run"] is None
        assert stats["running"] is False

    @pytest.mark.asyncio
    async def test_run_hourly_rollup(
        self,
        scheduler: RollupScheduler,
        mock_session: MockSession,
    ) -> None:
        """Test running hourly rollup manually."""
        # Set up mock results (empty for simplicity)
        mock_session.set_results([])

        results = await scheduler.run_hourly_rollup()

        # Should have run queries for each dimension
        assert len(mock_session.executed) > 0
        assert mock_session.committed
        assert scheduler.stats["hourly_rollups_completed"] == 1
        assert scheduler.stats["last_hourly_run"] is not None

    @pytest.mark.asyncio
    async def test_run_daily_rollup(
        self,
        scheduler: RollupScheduler,
        mock_session: MockSession,
    ) -> None:
        """Test running daily rollup manually."""
        mock_session.set_results([])

        results = await scheduler.run_daily_rollup()

        assert mock_session.committed
        assert scheduler.stats["daily_rollups_completed"] == 1
        assert scheduler.stats["last_daily_run"] is not None

    @pytest.mark.asyncio
    async def test_run_weekly_rollup(
        self,
        scheduler: RollupScheduler,
        mock_session: MockSession,
    ) -> None:
        """Test running weekly rollup manually."""
        mock_session.set_results([])

        results = await scheduler.run_weekly_rollup()

        assert mock_session.committed
        assert scheduler.stats["weekly_rollups_completed"] == 1
        assert scheduler.stats["last_weekly_run"] is not None

    @pytest.mark.asyncio
    async def test_cleanup_old_events(
        self,
        scheduler: RollupScheduler,
        mock_session: MockSession,
    ) -> None:
        """Test cleaning up old events."""
        mock_session.rowcount = 50
        mock_session.set_results([])

        deleted = await scheduler.cleanup_old_events()

        assert deleted == 50
        assert scheduler.stats["events_cleaned"] == 50
        assert scheduler.stats["last_cleanup_run"] is not None

    @pytest.mark.asyncio
    async def test_run_hourly_rollup_with_target_hour(
        self,
        scheduler: RollupScheduler,
        mock_session: MockSession,
    ) -> None:
        """Test running hourly rollup for specific hour."""
        mock_session.set_results([])
        target_hour = datetime.now(UTC) - timedelta(hours=5)

        results = await scheduler.run_hourly_rollup(target_hour=target_hour)

        assert scheduler.stats["hourly_rollups_completed"] == 1


class TestRollupSchedulerError:
    """Tests for RollupSchedulerError."""

    def test_error_creation(self) -> None:
        """Test creating a RollupSchedulerError."""
        error = RollupSchedulerError(
            "Test error message",
            correlation_id="corr_123",
            context={"key": "value"},
        )

        assert error.message == "Test error message"
        assert error.correlation_id == "corr_123"
        assert error.context == {"key": "value"}
        assert "Test error message" in str(error)

    def test_error_without_optional_fields(self) -> None:
        """Test creating error without optional fields."""
        error = RollupSchedulerError("Simple error")

        assert error.message == "Simple error"
        assert "Simple error" in str(error)


# =============================================================================
# Integration-style Tests
# =============================================================================


class TestRollupSchedulerIntegration:
    """Integration-style tests for rollup scheduler."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(
        self,
        mock_session_factory: MockSessionFactory,
    ) -> None:
        """Test full scheduler lifecycle."""
        scheduler = RollupScheduler(
            mock_session_factory,
            retention_days=7,
            hourly_interval=10.0,  # Long interval to avoid auto-run
        )

        await scheduler.start()

        try:
            assert scheduler._running
            assert scheduler.stats["running"] is True
        finally:
            await scheduler.stop()

        assert not scheduler._running
        assert scheduler.stats["running"] is False

    @pytest.mark.asyncio
    async def test_concurrent_rollups_are_serialized(
        self,
        scheduler: RollupScheduler,
        mock_session: MockSession,
    ) -> None:
        """Test that concurrent rollups are serialized via lock."""
        mock_session.set_results([])

        # Run multiple rollups concurrently
        tasks = [
            scheduler.run_hourly_rollup(),
            scheduler.run_daily_rollup(),
            scheduler.run_weekly_rollup(),
        ]

        results = await asyncio.gather(*tasks)

        # All should complete successfully
        assert scheduler.stats["hourly_rollups_completed"] == 1
        assert scheduler.stats["daily_rollups_completed"] == 1
        assert scheduler.stats["weekly_rollups_completed"] == 1
