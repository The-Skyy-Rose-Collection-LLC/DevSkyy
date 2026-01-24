# services/analytics/event_collector.py
"""
Analytics Event Collector for DevSkyy.

Collects and stores analytics events for the admin dashboard.
Supports buffered batch inserts for performance optimization.

Features:
- Async event ingestion with buffering
- Batch insert to PostgreSQL for performance
- Correlation ID tracking for request tracing
- Multiple event types: api_request, ml_job, order, error, alert

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from errors.production_errors import (
    DevSkyError,
    DevSkyErrorCode,
    DevSkyErrorSeverity,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

DEFAULT_BUFFER_SIZE = 100
DEFAULT_FLUSH_INTERVAL_SECONDS = 5.0
MAX_BUFFER_SIZE = 1000
MAX_BUFFER_OVERFLOW = 5000  # Hard limit to prevent memory exhaustion on flush failures


# =============================================================================
# Models
# =============================================================================


class EventType(str, Enum):
    """Types of analytics events."""

    API_REQUEST = "api_request"
    ML_JOB = "ml_job"
    ORDER = "order"
    ERROR = "error"
    ALERT = "alert"


class AnalyticsEvent(BaseModel):
    """Model for an analytics event."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: EventType
    event_name: str
    source: str
    user_id: uuid.UUID | None = None
    session_id: str | None = None
    correlation_id: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    numeric_value: Decimal | None = None
    string_value: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    geo_country: str | None = None
    geo_region: str | None = None
    event_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        """Pydantic config."""

        use_enum_values = True


class EventCollectorError(DevSkyError):
    """Error raised by the event collector."""

    def __init__(
        self,
        message: str,
        *,
        correlation_id: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=DevSkyErrorCode.INTERNAL_ERROR,
            severity=DevSkyErrorSeverity.ERROR,
            correlation_id=correlation_id,
            context=dict(context) if context else None,
        )


# =============================================================================
# Event Collector
# =============================================================================


class AnalyticsEventCollector:
    """
    Async analytics event collector with buffering and batch inserts.

    Usage:
        collector = AnalyticsEventCollector(db_session)
        await collector.start()

        # Track events
        await collector.track(
            event_type=EventType.API_REQUEST,
            event_name="user.login",
            source="auth_service",
            correlation_id="abc123",
            properties={"method": "POST", "status": 200},
        )

        # Shutdown gracefully
        await collector.stop()
    """

    def __init__(
        self,
        session_factory: Any,
        *,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        flush_interval: float = DEFAULT_FLUSH_INTERVAL_SECONDS,
    ) -> None:
        """
        Initialize the event collector.

        Args:
            session_factory: SQLAlchemy async session factory.
            buffer_size: Number of events to buffer before auto-flush.
            flush_interval: Seconds between automatic flushes.
        """
        self._session_factory = session_factory
        self._buffer_size = min(buffer_size, MAX_BUFFER_SIZE)
        self._flush_interval = flush_interval
        self._buffer: list[AnalyticsEvent] = []
        self._lock = asyncio.Lock()
        self._flush_task: asyncio.Task[None] | None = None
        self._running = False
        self._events_collected = 0
        self._events_flushed = 0
        self._events_dropped = 0
        self._flush_errors = 0

    @property
    def stats(self) -> dict[str, int]:
        """Return collector statistics."""
        return {
            "events_collected": self._events_collected,
            "events_flushed": self._events_flushed,
            "events_dropped": self._events_dropped,
            "buffer_size": len(self._buffer),
            "flush_errors": self._flush_errors,
        }

    async def start(self) -> None:
        """Start the background flush task."""
        if self._running:
            return

        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
        logger.info(
            "Analytics event collector started",
            extra={
                "buffer_size": self._buffer_size,
                "flush_interval": self._flush_interval,
            },
        )

    async def stop(self) -> None:
        """Stop the collector and flush remaining events."""
        if not self._running:
            return

        self._running = False

        if self._flush_task:
            self._flush_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._flush_task
            self._flush_task = None

        # Final flush
        await self._flush()
        logger.info(
            "Analytics event collector stopped",
            extra={"stats": self.stats},
        )

    async def track(
        self,
        event_type: EventType,
        event_name: str,
        source: str,
        *,
        user_id: uuid.UUID | None = None,
        session_id: str | None = None,
        correlation_id: str | None = None,
        properties: dict[str, Any] | None = None,
        numeric_value: Decimal | float | None = None,
        string_value: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        geo_country: str | None = None,
        geo_region: str | None = None,
    ) -> uuid.UUID:
        """
        Track an analytics event.

        Args:
            event_type: Type of event (api_request, ml_job, order, error, alert).
            event_name: Name/identifier for the event.
            source: Source system/service that generated the event.
            user_id: Optional user ID associated with the event.
            session_id: Optional session ID.
            correlation_id: Optional correlation ID for request tracing.
            properties: Optional dict of additional properties.
            numeric_value: Optional numeric value (e.g., duration, count).
            string_value: Optional string value.
            ip_address: Optional IP address.
            user_agent: Optional user agent string.
            geo_country: Optional 2-letter country code.
            geo_region: Optional region/state.

        Returns:
            The event ID.

        Raises:
            EventCollectorError: If event tracking fails.
        """
        event = AnalyticsEvent(
            event_type=event_type,
            event_name=event_name,
            source=source,
            user_id=user_id,
            session_id=session_id,
            correlation_id=correlation_id,
            properties=properties or {},
            numeric_value=Decimal(str(numeric_value)) if numeric_value is not None else None,
            string_value=string_value,
            ip_address=ip_address,
            user_agent=user_agent,
            geo_country=geo_country,
            geo_region=geo_region,
        )

        async with self._lock:
            self._buffer.append(event)
            self._events_collected += 1

            if len(self._buffer) >= self._buffer_size:
                await self._flush()

        logger.debug(
            "Event tracked",
            extra={
                "event_id": str(event.id),
                "event_type": event_type.value,
                "event_name": event_name,
                "correlation_id": correlation_id,
            },
        )

        return event.id

    async def track_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float,
        *,
        correlation_id: str | None = None,
        user_id: uuid.UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> uuid.UUID:
        """Convenience method to track an API request."""
        return await self.track(
            event_type=EventType.API_REQUEST,
            event_name=f"{method} {endpoint}",
            source="api",
            correlation_id=correlation_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            numeric_value=duration_ms,
            properties={
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
            },
        )

    async def track_ml_job(
        self,
        job_type: str,
        provider: str,
        status: str,
        duration_ms: float,
        *,
        correlation_id: str | None = None,
        cost: Decimal | None = None,
        error_message: str | None = None,
    ) -> uuid.UUID:
        """Convenience method to track an ML job."""
        properties: dict[str, Any] = {
            "job_type": job_type,
            "provider": provider,
            "status": status,
        }
        if cost:
            properties["cost"] = str(cost)
        if error_message:
            properties["error_message"] = error_message

        return await self.track(
            event_type=EventType.ML_JOB,
            event_name=f"ml.{job_type}",
            source=provider,
            correlation_id=correlation_id,
            numeric_value=duration_ms,
            properties=properties,
        )

    async def track_order(
        self,
        order_id: str,
        action: str,
        amount: Decimal,
        *,
        user_id: uuid.UUID | None = None,
        correlation_id: str | None = None,
        properties: dict[str, Any] | None = None,
    ) -> uuid.UUID:
        """Convenience method to track an order event."""
        return await self.track(
            event_type=EventType.ORDER,
            event_name=f"order.{action}",
            source="woocommerce",
            user_id=user_id,
            correlation_id=correlation_id,
            numeric_value=amount,
            string_value=order_id,
            properties=properties or {},
        )

    async def track_error(
        self,
        error_type: str,
        message: str,
        source: str,
        *,
        correlation_id: str | None = None,
        stack_trace: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> uuid.UUID:
        """Convenience method to track an error."""
        properties: dict[str, Any] = {"error_type": error_type}
        if stack_trace:
            properties["stack_trace"] = stack_trace[:2000]  # Truncate

        return await self.track(
            event_type=EventType.ERROR,
            event_name=f"error.{error_type}",
            source=source,
            correlation_id=correlation_id,
            user_id=user_id,
            string_value=message[:500],  # Truncate
            properties=properties,
        )

    async def _flush_loop(self) -> None:
        """Background task to periodically flush the buffer."""
        while self._running:
            try:
                await asyncio.sleep(self._flush_interval)
                async with self._lock:
                    if self._buffer:
                        await self._flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Error in flush loop: %s", e)
                self._flush_errors += 1

    async def _flush(self) -> None:
        """Flush buffered events to the database."""
        if not self._buffer:
            return

        events_to_flush = self._buffer.copy()
        self._buffer.clear()

        try:
            async with self._session_factory() as session:
                await self._batch_insert(session, events_to_flush)
                await session.commit()

            self._events_flushed += len(events_to_flush)
            logger.debug(
                "Flushed events to database",
                extra={"count": len(events_to_flush)},
            )
        except Exception as e:
            # Put events back in buffer on failure, respecting overflow limit
            available_space = MAX_BUFFER_OVERFLOW - len(self._buffer)
            restore_count = min(len(events_to_flush), available_space)
            if restore_count > 0:
                self._buffer = events_to_flush[:restore_count] + self._buffer
            dropped = len(events_to_flush) - restore_count
            if dropped > 0:
                self._events_dropped += dropped
                logger.warning(
                    "Dropped %d events due to buffer overflow",
                    dropped,
                    extra={"dropped": dropped, "buffer_size": len(self._buffer)},
                )
            self._flush_errors += 1
            logger.exception("Failed to flush events: %s", e)
            raise EventCollectorError(
                f"Failed to flush {len(events_to_flush)} events: {e}",
                context={"event_count": len(events_to_flush), "dropped": dropped},
            ) from e

    async def _batch_insert(
        self,
        session: AsyncSession,
        events: list[AnalyticsEvent],
    ) -> None:
        """Batch insert events into the database."""
        if not events:
            return

        # Use raw SQL for performance with batch insert
        values = []
        for event in events:
            values.append(
                {
                    "id": str(event.id),
                    "event_type": event.event_type,
                    "event_name": event.event_name,
                    "source": event.source,
                    "user_id": str(event.user_id) if event.user_id else None,
                    "session_id": event.session_id,
                    "correlation_id": event.correlation_id,
                    "properties": json.dumps(event.properties),
                    "numeric_value": str(event.numeric_value) if event.numeric_value else None,
                    "string_value": event.string_value,
                    "ip_address": event.ip_address,
                    "user_agent": event.user_agent,
                    "geo_country": event.geo_country,
                    "geo_region": event.geo_region,
                    "event_timestamp": event.event_timestamp.isoformat(),
                }
            )

        # Build parameterized query for batch insert
        insert_sql = text("""
            INSERT INTO analytics_events (
                id, event_type, event_name, source, user_id, session_id,
                correlation_id, properties, numeric_value, string_value,
                ip_address, user_agent, geo_country, geo_region, event_timestamp
            ) VALUES (
                :id::uuid, :event_type, :event_name, :source, :user_id::uuid,
                :session_id, :correlation_id, :properties::jsonb, :numeric_value::decimal,
                :string_value, :ip_address, :user_agent, :geo_country, :geo_region,
                :event_timestamp::timestamptz
            )
        """)

        for value in values:
            await session.execute(insert_sql, value)
