# tests/services/analytics/test_event_collector.py
"""
Unit tests for AnalyticsEventCollector.

Tests cover:
- Event tracking with all event types
- Buffer management and auto-flush
- Batch insert performance
- Correlation ID tracking
- Error handling and recovery
"""

from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal
from typing import Any

import pytest

from services.analytics.event_collector import (
    AnalyticsEvent,
    AnalyticsEventCollector,
    EventCollectorError,
    EventType,
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

    async def execute(self, query: Any, params: Any = None) -> None:
        self.executed.append((query, params))

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True


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
def collector(mock_session_factory: MockSessionFactory) -> AnalyticsEventCollector:
    """Create an event collector for testing."""
    return AnalyticsEventCollector(
        mock_session_factory,
        buffer_size=5,
        flush_interval=0.1,
    )


# =============================================================================
# AnalyticsEvent Model Tests
# =============================================================================


class TestAnalyticsEvent:
    """Tests for AnalyticsEvent model."""

    def test_create_event_with_defaults(self) -> None:
        """Test creating event with minimal fields."""
        event = AnalyticsEvent(
            event_type=EventType.API_REQUEST,
            event_name="test.event",
            source="test",
        )

        assert event.id is not None
        assert event.event_type == EventType.API_REQUEST
        assert event.event_name == "test.event"
        assert event.source == "test"
        assert event.properties == {}
        assert event.event_timestamp is not None

    def test_create_event_with_all_fields(self) -> None:
        """Test creating event with all fields."""
        user_id = uuid.uuid4()
        event = AnalyticsEvent(
            event_type=EventType.ML_JOB,
            event_name="ml.inference",
            source="replicate",
            user_id=user_id,
            session_id="sess_123",
            correlation_id="corr_456",
            properties={"model": "flux", "duration": 1500},
            numeric_value=Decimal("1.50"),
            string_value="completed",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            geo_country="US",
            geo_region="California",
        )

        assert event.user_id == user_id
        assert event.session_id == "sess_123"
        assert event.correlation_id == "corr_456"
        assert event.properties["model"] == "flux"
        assert event.numeric_value == Decimal("1.50")

    def test_event_type_enum_values(self) -> None:
        """Test all event type values."""
        assert EventType.API_REQUEST.value == "api_request"
        assert EventType.ML_JOB.value == "ml_job"
        assert EventType.ORDER.value == "order"
        assert EventType.ERROR.value == "error"
        assert EventType.ALERT.value == "alert"


# =============================================================================
# AnalyticsEventCollector Tests
# =============================================================================


class TestAnalyticsEventCollector:
    """Tests for AnalyticsEventCollector."""

    @pytest.mark.asyncio
    async def test_track_event_returns_id(
        self,
        collector: AnalyticsEventCollector,
    ) -> None:
        """Test that tracking an event returns an event ID."""
        event_id = await collector.track(
            event_type=EventType.API_REQUEST,
            event_name="test.event",
            source="test",
        )

        assert isinstance(event_id, uuid.UUID)

    @pytest.mark.asyncio
    async def test_track_event_adds_to_buffer(
        self,
        collector: AnalyticsEventCollector,
    ) -> None:
        """Test that tracked events are added to buffer."""
        await collector.track(
            event_type=EventType.API_REQUEST,
            event_name="test.event",
            source="test",
        )

        assert collector.stats["events_collected"] == 1
        assert collector.stats["buffer_size"] == 1

    @pytest.mark.asyncio
    async def test_auto_flush_when_buffer_full(
        self,
        collector: AnalyticsEventCollector,
        mock_session: MockSession,
    ) -> None:
        """Test that buffer flushes automatically when full."""
        # Buffer size is 5, so track 5 events
        for i in range(5):
            await collector.track(
                event_type=EventType.API_REQUEST,
                event_name=f"test.event.{i}",
                source="test",
            )

        # Buffer should have flushed
        assert collector.stats["events_flushed"] == 5
        assert collector.stats["buffer_size"] == 0
        assert mock_session.committed

    @pytest.mark.asyncio
    async def test_track_with_correlation_id(
        self,
        collector: AnalyticsEventCollector,
    ) -> None:
        """Test tracking event with correlation ID."""
        correlation_id = "req_abc123"
        await collector.track(
            event_type=EventType.API_REQUEST,
            event_name="test.event",
            source="test",
            correlation_id=correlation_id,
        )

        # Verify event is in buffer with correlation_id
        assert len(collector._buffer) == 1
        assert collector._buffer[0].correlation_id == correlation_id

    @pytest.mark.asyncio
    async def test_track_api_request_convenience_method(
        self,
        collector: AnalyticsEventCollector,
    ) -> None:
        """Test the track_api_request convenience method."""
        event_id = await collector.track_api_request(
            endpoint="/api/v1/users",
            method="GET",
            status_code=200,
            duration_ms=45.5,
            correlation_id="req_123",
        )

        assert isinstance(event_id, uuid.UUID)
        event = collector._buffer[0]
        assert event.event_type == "api_request"
        assert event.event_name == "GET /api/v1/users"
        assert event.properties["status_code"] == 200

    @pytest.mark.asyncio
    async def test_track_ml_job_convenience_method(
        self,
        collector: AnalyticsEventCollector,
    ) -> None:
        """Test the track_ml_job convenience method."""
        event_id = await collector.track_ml_job(
            job_type="3d_generation",
            provider="tripo",
            status="completed",
            duration_ms=5000.0,
            cost=Decimal("0.15"),
        )

        assert isinstance(event_id, uuid.UUID)
        event = collector._buffer[0]
        assert event.event_type == "ml_job"
        assert event.source == "tripo"
        assert event.properties["cost"] == "0.15"

    @pytest.mark.asyncio
    async def test_track_order_convenience_method(
        self,
        collector: AnalyticsEventCollector,
    ) -> None:
        """Test the track_order convenience method."""
        user_id = uuid.uuid4()
        event_id = await collector.track_order(
            order_id="ORD-12345",
            action="created",
            amount=Decimal("149.99"),
            user_id=user_id,
        )

        assert isinstance(event_id, uuid.UUID)
        event = collector._buffer[0]
        assert event.event_type == "order"
        assert event.event_name == "order.created"
        assert event.string_value == "ORD-12345"

    @pytest.mark.asyncio
    async def test_track_error_convenience_method(
        self,
        collector: AnalyticsEventCollector,
    ) -> None:
        """Test the track_error convenience method."""
        event_id = await collector.track_error(
            error_type="ValidationError",
            message="Invalid email format",
            source="auth_service",
            correlation_id="req_456",
        )

        assert isinstance(event_id, uuid.UUID)
        event = collector._buffer[0]
        assert event.event_type == "error"
        assert event.event_name == "error.ValidationError"

    @pytest.mark.asyncio
    async def test_start_creates_flush_task(
        self,
        collector: AnalyticsEventCollector,
    ) -> None:
        """Test that start creates the background flush task."""
        await collector.start()
        try:
            assert collector._running
            assert collector._flush_task is not None
        finally:
            await collector.stop()

    @pytest.mark.asyncio
    async def test_stop_flushes_remaining_events(
        self,
        collector: AnalyticsEventCollector,
        mock_session: MockSession,
    ) -> None:
        """Test that stop flushes any remaining buffered events."""
        await collector.start()

        # Track some events (less than buffer size)
        await collector.track(
            event_type=EventType.API_REQUEST,
            event_name="test.event.1",
            source="test",
        )
        await collector.track(
            event_type=EventType.API_REQUEST,
            event_name="test.event.2",
            source="test",
        )

        # Events should be in buffer
        assert collector.stats["buffer_size"] == 2

        # Stop should flush them
        await collector.stop()

        assert collector.stats["buffer_size"] == 0
        assert collector.stats["events_flushed"] == 2

    @pytest.mark.asyncio
    async def test_stats_tracking(
        self,
        collector: AnalyticsEventCollector,
    ) -> None:
        """Test that stats are tracked correctly."""
        initial_stats = collector.stats
        assert initial_stats["events_collected"] == 0
        assert initial_stats["events_flushed"] == 0
        assert initial_stats["buffer_size"] == 0
        assert initial_stats["flush_errors"] == 0

        # Track some events
        for i in range(3):
            await collector.track(
                event_type=EventType.API_REQUEST,
                event_name=f"test.{i}",
                source="test",
            )

        stats = collector.stats
        assert stats["events_collected"] == 3
        assert stats["buffer_size"] == 3

    @pytest.mark.asyncio
    async def test_concurrent_tracking(
        self,
        collector: AnalyticsEventCollector,
    ) -> None:
        """Test that concurrent tracking is thread-safe."""

        async def track_event(n: int) -> uuid.UUID:
            return await collector.track(
                event_type=EventType.API_REQUEST,
                event_name=f"concurrent.event.{n}",
                source="test",
            )

        # Track 20 events concurrently
        tasks = [track_event(i) for i in range(20)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 20
        assert all(isinstance(r, uuid.UUID) for r in results)
        # Some may have been flushed (buffer size is 5)
        assert collector.stats["events_collected"] == 20

    @pytest.mark.asyncio
    async def test_numeric_value_conversion(
        self,
        collector: AnalyticsEventCollector,
    ) -> None:
        """Test that numeric values are converted to Decimal."""
        await collector.track(
            event_type=EventType.API_REQUEST,
            event_name="test.event",
            source="test",
            numeric_value=123.45,  # float input
        )

        event = collector._buffer[0]
        assert isinstance(event.numeric_value, Decimal)
        assert event.numeric_value == Decimal("123.45")


class TestEventCollectorError:
    """Tests for EventCollectorError."""

    def test_error_creation(self) -> None:
        """Test creating an EventCollectorError."""
        error = EventCollectorError(
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
        error = EventCollectorError("Simple error")

        assert error.message == "Simple error"
        assert "Simple error" in str(error)


# =============================================================================
# Integration-style Tests (with mock DB)
# =============================================================================


class TestEventCollectorIntegration:
    """Integration-style tests for event collector."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(
        self,
        mock_session_factory: MockSessionFactory,
    ) -> None:
        """Test full collector lifecycle: start, track, flush, stop."""
        collector = AnalyticsEventCollector(
            mock_session_factory,
            buffer_size=3,
            flush_interval=10.0,  # Long interval to avoid auto-flush
        )

        await collector.start()

        try:
            # Track events
            await collector.track(
                event_type=EventType.API_REQUEST,
                event_name="lifecycle.test.1",
                source="test",
            )
            await collector.track(
                event_type=EventType.ML_JOB,
                event_name="lifecycle.test.2",
                source="test",
            )

            assert collector.stats["events_collected"] == 2
            assert collector.stats["buffer_size"] == 2

        finally:
            await collector.stop()

        # After stop, all events should be flushed
        assert collector.stats["buffer_size"] == 0
        assert collector.stats["events_flushed"] == 2
        assert not collector._running

    @pytest.mark.asyncio
    async def test_periodic_flush(
        self,
        mock_session_factory: MockSessionFactory,
    ) -> None:
        """Test that periodic flush works."""
        collector = AnalyticsEventCollector(
            mock_session_factory,
            buffer_size=100,  # High buffer to avoid auto-flush
            flush_interval=0.05,  # 50ms flush interval
        )

        await collector.start()

        try:
            await collector.track(
                event_type=EventType.API_REQUEST,
                event_name="periodic.test",
                source="test",
            )

            # Wait for periodic flush
            await asyncio.sleep(0.1)

            # Event should have been flushed
            assert collector.stats["events_flushed"] == 1
            assert collector.stats["buffer_size"] == 0

        finally:
            await collector.stop()
