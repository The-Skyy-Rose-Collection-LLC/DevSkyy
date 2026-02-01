# services/analytics/rollup_scheduler.py
"""
Rollup Scheduler for DevSkyy Analytics.

Scheduled service for aggregating analytics data into rollup tables.
Supports hourly, daily, and weekly aggregation with automatic cleanup.

Features:
- Async scheduled rollup tasks
- Hourly aggregation by event_type, event_name, source
- Daily and weekly aggregations for dashboards
- Automatic cleanup of raw events after retention period
- Correlation ID tracking for debugging

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
from datetime import UTC, datetime, timedelta
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

DEFAULT_RETENTION_DAYS = 7
DEFAULT_HOURLY_INTERVAL_SECONDS = 3600  # 1 hour
DEFAULT_DAILY_CHECK_INTERVAL_SECONDS = 60  # Check every minute for midnight
DEFAULT_WEEKLY_CHECK_INTERVAL_SECONDS = 60  # Check every minute for Sunday midnight


# =============================================================================
# Models
# =============================================================================


class RollupGranularity(str, Enum):
    """Granularity levels for rollup aggregations."""

    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class RollupDimension(str, Enum):
    """Dimensions for rollup aggregations."""

    EVENT_TYPE = "event_type"
    EVENT_NAME = "event_name"
    SOURCE = "source"
    GEO_COUNTRY = "geo_country"


class RollupResult(BaseModel):
    """Model for a rollup aggregation result."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    metric_name: str
    dimension: str
    dimension_value: str | None = None
    granularity: RollupGranularity
    period_start: datetime
    period_end: datetime
    count: int = 0
    sum_value: Decimal | None = None
    avg_value: Decimal | None = None
    min_value: Decimal | None = None
    max_value: Decimal | None = None
    p50_value: Decimal | None = None
    p95_value: Decimal | None = None
    p99_value: Decimal | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        use_enum_values = True


class RollupSchedulerError(DevSkyError):
    """Error raised by the rollup scheduler."""

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
# Rollup Scheduler
# =============================================================================


class RollupScheduler:
    """
    Scheduled rollup aggregation service for analytics data.

    Usage:
        scheduler = RollupScheduler(session_factory)
        await scheduler.start()

        # Runs automatically on schedule
        # Or trigger manually:
        await scheduler.run_hourly_rollup()
        await scheduler.run_daily_rollup()
        await scheduler.run_weekly_rollup()
        await scheduler.cleanup_old_events()

        # Shutdown gracefully
        await scheduler.stop()
    """

    def __init__(
        self,
        session_factory: Any,
        *,
        retention_days: int = DEFAULT_RETENTION_DAYS,
        hourly_interval: float = DEFAULT_HOURLY_INTERVAL_SECONDS,
    ) -> None:
        """
        Initialize the rollup scheduler.

        Args:
            session_factory: SQLAlchemy async session factory.
            retention_days: Number of days to retain raw events.
            hourly_interval: Seconds between hourly rollup runs.
        """
        self._session_factory = session_factory
        self._retention_days = retention_days
        self._hourly_interval = hourly_interval
        self._running = False
        self._hourly_task: asyncio.Task[None] | None = None
        self._daily_task: asyncio.Task[None] | None = None
        self._weekly_task: asyncio.Task[None] | None = None
        self._cleanup_task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

        # Statistics
        self._hourly_rollups_completed = 0
        self._daily_rollups_completed = 0
        self._weekly_rollups_completed = 0
        self._events_cleaned = 0
        self._rollup_errors = 0
        self._last_hourly_run: datetime | None = None
        self._last_daily_run: datetime | None = None
        self._last_weekly_run: datetime | None = None
        self._last_cleanup_run: datetime | None = None

    @property
    def stats(self) -> dict[str, Any]:
        """Return scheduler statistics."""
        return {
            "hourly_rollups_completed": self._hourly_rollups_completed,
            "daily_rollups_completed": self._daily_rollups_completed,
            "weekly_rollups_completed": self._weekly_rollups_completed,
            "events_cleaned": self._events_cleaned,
            "rollup_errors": self._rollup_errors,
            "last_hourly_run": (
                self._last_hourly_run.isoformat() if self._last_hourly_run else None
            ),
            "last_daily_run": (self._last_daily_run.isoformat() if self._last_daily_run else None),
            "last_weekly_run": (
                self._last_weekly_run.isoformat() if self._last_weekly_run else None
            ),
            "last_cleanup_run": (
                self._last_cleanup_run.isoformat() if self._last_cleanup_run else None
            ),
            "running": self._running,
        }

    async def start(self) -> None:
        """Start all scheduled rollup tasks."""
        if self._running:
            return

        self._running = True
        self._hourly_task = asyncio.create_task(self._hourly_loop())
        self._daily_task = asyncio.create_task(self._daily_loop())
        self._weekly_task = asyncio.create_task(self._weekly_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info(
            "Rollup scheduler started",
            extra={
                "retention_days": self._retention_days,
                "hourly_interval": self._hourly_interval,
            },
        )

    async def stop(self) -> None:
        """Stop all scheduled tasks."""
        if not self._running:
            return

        self._running = False

        tasks = [
            self._hourly_task,
            self._daily_task,
            self._weekly_task,
            self._cleanup_task,
        ]

        for task in tasks:
            if task:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

        self._hourly_task = None
        self._daily_task = None
        self._weekly_task = None
        self._cleanup_task = None

        logger.info(
            "Rollup scheduler stopped",
            extra={"stats": self.stats},
        )

    async def _hourly_loop(self) -> None:
        """Background task for hourly rollups."""
        while self._running:
            try:
                await asyncio.sleep(self._hourly_interval)
                await self.run_hourly_rollup()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Error in hourly rollup loop: %s", e)
                self._rollup_errors += 1

    async def _daily_loop(self) -> None:
        """Background task for daily rollups at midnight UTC."""
        while self._running:
            try:
                await asyncio.sleep(DEFAULT_DAILY_CHECK_INTERVAL_SECONDS)
                now = datetime.now(UTC)
                # Run at midnight UTC (hour 0, minute 0)
                if now.hour == 0 and now.minute == 0:
                    # Avoid duplicate runs within the same minute
                    if (
                        self._last_daily_run is None
                        or (now - self._last_daily_run).total_seconds() > 3600
                    ):
                        await self.run_daily_rollup()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Error in daily rollup loop: %s", e)
                self._rollup_errors += 1

    async def _weekly_loop(self) -> None:
        """Background task for weekly rollups at Sunday midnight UTC."""
        while self._running:
            try:
                await asyncio.sleep(DEFAULT_WEEKLY_CHECK_INTERVAL_SECONDS)
                now = datetime.now(UTC)
                # Run on Sunday (weekday 6) at midnight UTC
                if now.weekday() == 6 and now.hour == 0 and now.minute == 0:
                    # Avoid duplicate runs within the same minute
                    if (
                        self._last_weekly_run is None
                        or (now - self._last_weekly_run).total_seconds() > 3600
                    ):
                        await self.run_weekly_rollup()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Error in weekly rollup loop: %s", e)
                self._rollup_errors += 1

    async def _cleanup_loop(self) -> None:
        """Background task for cleanup, runs daily."""
        while self._running:
            try:
                # Run cleanup once per day (24 hours)
                await asyncio.sleep(86400)
                await self.cleanup_old_events()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Error in cleanup loop: %s", e)
                self._rollup_errors += 1

    async def run_hourly_rollup(
        self,
        *,
        target_hour: datetime | None = None,
    ) -> list[RollupResult]:
        """
        Run hourly rollup aggregation.

        Args:
            target_hour: Specific hour to aggregate. Defaults to the previous hour.

        Returns:
            List of rollup results created.

        Raises:
            RollupSchedulerError: If rollup fails.
        """
        async with self._lock:
            now = datetime.now(UTC)
            if target_hour is None:
                # Aggregate the previous hour
                target_hour = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)

            period_start = target_hour.replace(minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(hours=1)

            logger.info(
                "Running hourly rollup",
                extra={
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat(),
                },
            )

            try:
                results = await self._run_rollup(
                    granularity=RollupGranularity.HOUR,
                    period_start=period_start,
                    period_end=period_end,
                )
                self._hourly_rollups_completed += 1
                self._last_hourly_run = now

                logger.info(
                    "Hourly rollup completed",
                    extra={"rollup_count": len(results)},
                )
                return results
            except Exception as e:
                self._rollup_errors += 1
                raise RollupSchedulerError(
                    f"Hourly rollup failed: {e}",
                    context={
                        "period_start": period_start.isoformat(),
                        "period_end": period_end.isoformat(),
                    },
                ) from e

    async def run_daily_rollup(
        self,
        *,
        target_date: datetime | None = None,
    ) -> list[RollupResult]:
        """
        Run daily rollup aggregation.

        Args:
            target_date: Specific date to aggregate. Defaults to yesterday.

        Returns:
            List of rollup results created.

        Raises:
            RollupSchedulerError: If rollup fails.
        """
        async with self._lock:
            now = datetime.now(UTC)
            if target_date is None:
                # Aggregate yesterday
                target_date = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
                    days=1
                )

            period_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)

            logger.info(
                "Running daily rollup",
                extra={
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat(),
                },
            )

            try:
                results = await self._run_rollup(
                    granularity=RollupGranularity.DAY,
                    period_start=period_start,
                    period_end=period_end,
                )
                self._daily_rollups_completed += 1
                self._last_daily_run = now

                logger.info(
                    "Daily rollup completed",
                    extra={"rollup_count": len(results)},
                )
                return results
            except Exception as e:
                self._rollup_errors += 1
                raise RollupSchedulerError(
                    f"Daily rollup failed: {e}",
                    context={
                        "period_start": period_start.isoformat(),
                        "period_end": period_end.isoformat(),
                    },
                ) from e

    async def run_weekly_rollup(
        self,
        *,
        target_week_start: datetime | None = None,
    ) -> list[RollupResult]:
        """
        Run weekly rollup aggregation.

        Args:
            target_week_start: Start of the week to aggregate. Defaults to last week.

        Returns:
            List of rollup results created.

        Raises:
            RollupSchedulerError: If rollup fails.
        """
        async with self._lock:
            now = datetime.now(UTC)
            if target_week_start is None:
                # Find last Sunday
                days_since_sunday = (now.weekday() + 1) % 7
                last_sunday = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
                    days=days_since_sunday + 7
                )
                target_week_start = last_sunday

            period_start = target_week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(weeks=1)

            logger.info(
                "Running weekly rollup",
                extra={
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat(),
                },
            )

            try:
                results = await self._run_rollup(
                    granularity=RollupGranularity.WEEK,
                    period_start=period_start,
                    period_end=period_end,
                )
                self._weekly_rollups_completed += 1
                self._last_weekly_run = now

                logger.info(
                    "Weekly rollup completed",
                    extra={"rollup_count": len(results)},
                )
                return results
            except Exception as e:
                self._rollup_errors += 1
                raise RollupSchedulerError(
                    f"Weekly rollup failed: {e}",
                    context={
                        "period_start": period_start.isoformat(),
                        "period_end": period_end.isoformat(),
                    },
                ) from e

    async def cleanup_old_events(self) -> int:
        """
        Clean up raw events older than the retention period.

        Returns:
            Number of events deleted.

        Raises:
            RollupSchedulerError: If cleanup fails.
        """
        async with self._lock:
            now = datetime.now(UTC)
            cutoff = now - timedelta(days=self._retention_days)

            logger.info(
                "Running cleanup of old events",
                extra={
                    "retention_days": self._retention_days,
                    "cutoff": cutoff.isoformat(),
                },
            )

            try:
                async with self._session_factory() as session:
                    result = await session.execute(
                        text("""
                            DELETE FROM analytics_events
                            WHERE event_timestamp < :cutoff
                        """),
                        {"cutoff": cutoff.isoformat()},
                    )
                    deleted_rows = result.rowcount or 0
                    await session.commit()

                self._events_cleaned += deleted_rows
                self._last_cleanup_run = now

                logger.info(
                    "Cleanup completed",
                    extra={"events_deleted": deleted_rows},
                )
                return deleted_rows
            except Exception as e:
                self._rollup_errors += 1
                raise RollupSchedulerError(
                    f"Cleanup failed: {e}",
                    context={
                        "retention_days": self._retention_days,
                        "cutoff": cutoff.isoformat(),
                    },
                ) from e

    async def _run_rollup(
        self,
        granularity: RollupGranularity,
        period_start: datetime,
        period_end: datetime,
    ) -> list[RollupResult]:
        """
        Execute rollup aggregation for a given period.

        Args:
            granularity: Rollup granularity (hour, day, week).
            period_start: Start of the aggregation period.
            period_end: End of the aggregation period.

        Returns:
            List of rollup results.
        """
        results: list[RollupResult] = []

        async with self._session_factory() as session:
            # Aggregate by each dimension
            for dimension in RollupDimension:
                rollups = await self._aggregate_by_dimension(
                    session=session,
                    dimension=dimension,
                    granularity=granularity,
                    period_start=period_start,
                    period_end=period_end,
                )
                results.extend(rollups)

            # Insert rollups into database (upsert)
            await self._upsert_rollups(session, results)
            await session.commit()

        return results

    async def _aggregate_by_dimension(
        self,
        session: AsyncSession,
        dimension: RollupDimension,
        granularity: RollupGranularity,
        period_start: datetime,
        period_end: datetime,
    ) -> list[RollupResult]:
        """
        Aggregate events by a specific dimension.

        Args:
            session: Database session.
            dimension: Dimension to group by.
            granularity: Rollup granularity.
            period_start: Start of period.
            period_end: End of period.

        Returns:
            List of rollup results for this dimension.
        """
        # SQL query for aggregation with percentiles
        query = text(f"""
            SELECT
                '{dimension.value}' as dimension,
                {dimension.value} as dimension_value,
                COUNT(*) as count,
                SUM(numeric_value) as sum_value,
                AVG(numeric_value) as avg_value,
                MIN(numeric_value) as min_value,
                MAX(numeric_value) as max_value,
                PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY numeric_value) as p50_value,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY numeric_value) as p95_value,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY numeric_value) as p99_value
            FROM analytics_events
            WHERE event_timestamp >= :period_start
              AND event_timestamp < :period_end
            GROUP BY {dimension.value}
        """)

        result = await session.execute(
            query,
            {
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
            },
        )

        rollups: list[RollupResult] = []
        for row in result.fetchall():
            rollup = RollupResult(
                metric_name=f"events.{dimension.value}",
                dimension=dimension.value,
                dimension_value=row.dimension_value,
                granularity=granularity,
                period_start=period_start,
                period_end=period_end,
                count=row.count or 0,
                sum_value=(Decimal(str(row.sum_value)) if row.sum_value is not None else None),
                avg_value=(Decimal(str(row.avg_value)) if row.avg_value is not None else None),
                min_value=(Decimal(str(row.min_value)) if row.min_value is not None else None),
                max_value=(Decimal(str(row.max_value)) if row.max_value is not None else None),
                p50_value=(Decimal(str(row.p50_value)) if row.p50_value is not None else None),
                p95_value=(Decimal(str(row.p95_value)) if row.p95_value is not None else None),
                p99_value=(Decimal(str(row.p99_value)) if row.p99_value is not None else None),
            )
            rollups.append(rollup)

        return rollups

    async def _upsert_rollups(
        self,
        session: AsyncSession,
        rollups: list[RollupResult],
    ) -> None:
        """
        Upsert rollup results into the database.

        Uses ON CONFLICT to update existing rollups.

        Args:
            session: Database session.
            rollups: List of rollups to insert/update.
        """
        if not rollups:
            return

        upsert_sql = text("""
            INSERT INTO analytics_rollups (
                id, metric_name, dimension, dimension_value, granularity,
                period_start, period_end, count, sum_value, avg_value,
                min_value, max_value, p50_value, p95_value, p99_value, metadata
            ) VALUES (
                :id::uuid, :metric_name, :dimension, :dimension_value, :granularity,
                :period_start::timestamptz, :period_end::timestamptz, :count,
                :sum_value::decimal, :avg_value::decimal, :min_value::decimal,
                :max_value::decimal, :p50_value::decimal, :p95_value::decimal,
                :p99_value::decimal, :metadata::jsonb
            )
            ON CONFLICT ON CONSTRAINT uq_analytics_rollups_metric_dimension_period
            DO UPDATE SET
                count = EXCLUDED.count,
                sum_value = EXCLUDED.sum_value,
                avg_value = EXCLUDED.avg_value,
                min_value = EXCLUDED.min_value,
                max_value = EXCLUDED.max_value,
                p50_value = EXCLUDED.p50_value,
                p95_value = EXCLUDED.p95_value,
                p99_value = EXCLUDED.p99_value,
                updated_at = CURRENT_TIMESTAMP
        """)

        for rollup in rollups:
            await session.execute(
                upsert_sql,
                {
                    "id": str(rollup.id),
                    "metric_name": rollup.metric_name,
                    "dimension": rollup.dimension,
                    "dimension_value": rollup.dimension_value,
                    "granularity": rollup.granularity,
                    "period_start": rollup.period_start.isoformat(),
                    "period_end": rollup.period_end.isoformat(),
                    "count": rollup.count,
                    "sum_value": (str(rollup.sum_value) if rollup.sum_value is not None else None),
                    "avg_value": (str(rollup.avg_value) if rollup.avg_value is not None else None),
                    "min_value": (str(rollup.min_value) if rollup.min_value is not None else None),
                    "max_value": (str(rollup.max_value) if rollup.max_value is not None else None),
                    "p50_value": (str(rollup.p50_value) if rollup.p50_value is not None else None),
                    "p95_value": (str(rollup.p95_value) if rollup.p95_value is not None else None),
                    "p99_value": (str(rollup.p99_value) if rollup.p99_value is not None else None),
                    "metadata": json.dumps(rollup.metadata),
                },
            )
