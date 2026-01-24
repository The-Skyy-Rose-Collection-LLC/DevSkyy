# services/analytics/alert_engine.py
"""
Alert Evaluation Engine for DevSkyy Analytics.

Scheduled service for evaluating alert conditions and triggering notifications.
Supports threshold-based alerts with cooldown management.

Features:
- Async scheduled alert evaluation
- Multiple condition operators: gt, lt, gte, lte, eq, neq
- Cooldown tracking to prevent notification spam
- Alert history recording
- Custom metric provider support
- Correlation ID tracking for debugging

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol

from pydantic import BaseModel, Field
from sqlalchemy import text

from errors.production_errors import (
    DevSkyError,
    DevSkyErrorCode,
    DevSkyErrorSeverity,
)

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

DEFAULT_EVALUATION_INTERVAL_SECONDS = 60
DEFAULT_COOLDOWN_SECONDS = 300


# =============================================================================
# Enums
# =============================================================================


class ConditionType(str, Enum):
    """Types of alert conditions."""

    THRESHOLD = "threshold"
    ANOMALY = "anomaly"
    RATE = "rate"


class ConditionOperator(str, Enum):
    """Operators for condition evaluation."""

    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"
    EQ = "eq"
    NEQ = "neq"


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status values."""

    TRIGGERED = "triggered"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"


# =============================================================================
# Protocols
# =============================================================================


class MetricProvider(Protocol):
    """Protocol for custom metric providers."""

    async def get_metric(
        self,
        metric_name: str,
        window_seconds: int,
        filters: dict[str, Any],
    ) -> Decimal | None:
        """Get metric value for alert evaluation."""
        ...


# =============================================================================
# Models
# =============================================================================


class AlertConfig(BaseModel):
    """Model for an alert configuration."""

    id: uuid.UUID
    name: str
    description: str | None = None
    metric_name: str
    condition_type: ConditionType
    condition_operator: ConditionOperator
    threshold_value: Decimal | None = None
    threshold_unit: str | None = None
    window_duration_seconds: int = 300
    evaluation_interval_seconds: int = 60
    cooldown_seconds: int = 300
    severity: AlertSeverity = AlertSeverity.WARNING
    is_enabled: bool = True
    notification_channels: list[str] = Field(default_factory=list)
    notification_config: dict[str, Any] = Field(default_factory=dict)
    filters: dict[str, Any] = Field(default_factory=dict)
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        """Pydantic config."""

        use_enum_values = True


class AlertTrigger(BaseModel):
    """Model for an alert trigger event."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    alert_config_id: uuid.UUID
    status: AlertStatus = AlertStatus.TRIGGERED
    severity: AlertSeverity
    title: str
    message: str | None = None
    metric_value: Decimal | None = None
    threshold_value: Decimal | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    triggered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        """Pydantic config."""

        use_enum_values = True


class MetricValue(BaseModel):
    """Model for a metric measurement."""

    metric_name: str
    value: Decimal
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    dimensions: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Errors
# =============================================================================


class AlertEngineError(DevSkyError):
    """Error raised by the alert engine."""

    def __init__(
        self,
        message: str,
        *,
        correlation_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=DevSkyErrorCode.INTERNAL_ERROR,
            severity=DevSkyErrorSeverity.ERROR,
            correlation_id=correlation_id,
            context=context or {},
        )


class AlertConfigNotFoundError(AlertEngineError):
    """Error when alert config is not found."""

    def __init__(
        self,
        config_id: str,
        *,
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(
            message=f"Alert config not found: {config_id}",
            correlation_id=correlation_id,
            context={"alert_config_id": config_id},
        )


# =============================================================================
# Alert Evaluation Engine
# =============================================================================


class AlertEvaluationEngine:
    """
    Async service for evaluating alert conditions.

    Features:
    - Scheduled evaluation loop
    - All threshold operators (gt, lt, gte, lte, eq, neq)
    - Cooldown tracking per alert config
    - Alert history recording
    - Custom metric provider support
    """

    def __init__(
        self,
        session_factory: Callable[[], Any],
        *,
        evaluation_interval: float = DEFAULT_EVALUATION_INTERVAL_SECONDS,
        metric_provider: MetricProvider | None = None,
    ) -> None:
        """
        Initialize the alert evaluation engine.

        Args:
            session_factory: Factory for creating database sessions.
            evaluation_interval: Seconds between evaluation runs.
            metric_provider: Optional custom metric provider.
        """
        self._session_factory = session_factory
        self._evaluation_interval = evaluation_interval
        self._metric_provider = metric_provider
        self._running = False
        self._evaluation_task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()
        self._cooldown_tracker: dict[uuid.UUID, datetime] = {}
        self._stats = {
            "evaluations_run": 0,
            "alerts_triggered": 0,
            "alerts_skipped_cooldown": 0,
            "evaluation_errors": 0,
            "last_evaluation_run": None,
        }

    @property
    def stats(self) -> dict[str, Any]:
        """Get current engine statistics."""
        return {
            **self._stats,
            "running": self._running,
        }

    async def start(self) -> None:
        """Start the evaluation loop."""
        if self._running:
            logger.debug("Alert engine already running")
            return

        self._running = True
        self._evaluation_task = asyncio.create_task(self._evaluation_loop())
        logger.info("Alert evaluation engine started")

    async def stop(self) -> None:
        """Stop the evaluation loop."""
        if not self._running:
            return

        self._running = False

        if self._evaluation_task:
            self._evaluation_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._evaluation_task
            self._evaluation_task = None

        logger.info("Alert evaluation engine stopped")

    async def _evaluation_loop(self) -> None:
        """Background task for scheduled evaluation."""
        while self._running:
            try:
                await asyncio.sleep(self._evaluation_interval)
                if self._running:
                    await self.run_evaluation()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Error in evaluation loop: %s", e)
                self._stats["evaluation_errors"] += 1

    async def run_evaluation(
        self,
        *,
        correlation_id: str | None = None,
    ) -> list[AlertTrigger]:
        """
        Run alert evaluation for all enabled configs.

        Args:
            correlation_id: Optional correlation ID for tracing.

        Returns:
            List of triggered alerts.
        """
        async with self._lock:
            triggered: list[AlertTrigger] = []

            try:
                configs = await self._load_enabled_configs()

                for config in configs:
                    try:
                        trigger = await self._evaluate_config(
                            config,
                            correlation_id=correlation_id,
                        )
                        if trigger:
                            triggered.append(trigger)
                    except Exception as e:
                        logger.exception(
                            "Error evaluating config %s: %s",
                            config.id,
                            e,
                        )
                        self._stats["evaluation_errors"] += 1

                self._stats["evaluations_run"] += 1
                self._stats["last_evaluation_run"] = datetime.now(UTC)

            except Exception as e:
                logger.exception("Error loading configs: %s", e)
                self._stats["evaluation_errors"] += 1

            return triggered

    async def _load_enabled_configs(self) -> list[AlertConfig]:
        """Load all enabled alert configurations from database."""
        configs: list[AlertConfig] = []

        async with self._session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT id, name, description, metric_name, condition_type,
                           condition_operator, threshold_value, threshold_unit,
                           window_duration_seconds, evaluation_interval_seconds,
                           cooldown_seconds, severity, is_enabled,
                           notification_channels, notification_config, filters,
                           created_by, updated_by, created_at, updated_at
                    FROM alert_configs
                    WHERE is_enabled = true
                """)
            )
            rows = result.fetchall()

            for row in rows:
                configs.append(
                    AlertConfig(
                        id=row[0] if isinstance(row[0], uuid.UUID) else uuid.UUID(str(row[0])),
                        name=row[1],
                        description=row[2],
                        metric_name=row[3],
                        condition_type=ConditionType(row[4]),
                        condition_operator=ConditionOperator(row[5]),
                        threshold_value=row[6],
                        threshold_unit=row[7],
                        window_duration_seconds=row[8] or 300,
                        evaluation_interval_seconds=row[9] or 60,
                        cooldown_seconds=row[10] or 300,
                        severity=AlertSeverity(row[11]) if row[11] else AlertSeverity.WARNING,
                        is_enabled=row[12],
                        notification_channels=row[13] or [],
                        notification_config=row[14] if isinstance(row[14], dict) else {},
                        filters=row[15] if isinstance(row[15], dict) else {},
                        created_by=row[16],
                        updated_by=row[17],
                        created_at=row[18],
                        updated_at=row[19],
                    )
                )

        return configs

    async def _evaluate_config(
        self,
        config: AlertConfig,
        *,
        correlation_id: str | None = None,
    ) -> AlertTrigger | None:
        """
        Evaluate a single alert configuration.

        Args:
            config: Alert configuration to evaluate.
            correlation_id: Optional correlation ID.

        Returns:
            AlertTrigger if alert should fire, None otherwise.
        """
        # Check cooldown
        if self.is_in_cooldown(config.id, config.cooldown_seconds):
            self._stats["alerts_skipped_cooldown"] += 1
            return None

        # Get metric value
        async with self._session_factory() as session:
            metric_value = await self._get_metric_value(
                session,
                config.metric_name,
                config.window_duration_seconds,
                config.filters,
            )

        if metric_value is None:
            return None

        # Evaluate condition
        should_trigger = self._evaluate_condition(
            metric_value=metric_value,
            condition_type=config.condition_type,
            operator=config.condition_operator,
            threshold=config.threshold_value,
        )

        if not should_trigger:
            return None

        # Create trigger
        trigger = AlertTrigger(
            alert_config_id=config.id,
            severity=AlertSeverity(config.severity) if isinstance(config.severity, str) else config.severity,
            title=self._build_alert_title(config, metric_value),
            message=self._build_alert_message(config, metric_value),
            metric_value=metric_value,
            threshold_value=config.threshold_value,
            context={
                "correlation_id": correlation_id,
                "metric_name": config.metric_name,
                "window_seconds": config.window_duration_seconds,
            },
        )

        # Record in database
        await self._record_alert(trigger)

        # Set cooldown
        self._cooldown_tracker[config.id] = datetime.now(UTC)
        self._stats["alerts_triggered"] += 1

        logger.warning(
            "Alert triggered: %s (config_id=%s, value=%s, threshold=%s)",
            config.name,
            config.id,
            metric_value,
            config.threshold_value,
        )

        return trigger

    async def _get_metric_value(
        self,
        session: Any,
        metric_name: str,
        window_seconds: int,
        filters: dict[str, Any],
    ) -> Decimal | None:
        """Get metric value for evaluation."""
        # Use custom provider if available
        if self._metric_provider:
            return await self._metric_provider.get_metric(
                metric_name,
                window_seconds,
                filters,
            )

        # Default: query from analytics_events
        cutoff = datetime.now(UTC) - timedelta(seconds=window_seconds)

        result = await session.execute(
            text("""
                SELECT COALESCE(SUM(numeric_value), 0) as value
                FROM analytics_events
                WHERE event_name = :metric_name
                AND event_timestamp >= :cutoff
            """),
            {"metric_name": metric_name, "cutoff": cutoff},
        )
        row = result.first()
        return Decimal(str(row.value)) if row and row.value is not None else None

    def _evaluate_condition(
        self,
        metric_value: Decimal,
        condition_type: ConditionType | str,
        operator: ConditionOperator | str,
        threshold: Decimal | None,
    ) -> bool:
        """
        Evaluate alert condition.

        Args:
            metric_value: Current metric value.
            condition_type: Type of condition.
            operator: Comparison operator.
            threshold: Threshold value.

        Returns:
            True if condition is met.
        """
        if threshold is None:
            return False

        # Normalize operator to string
        op = operator.value if isinstance(operator, ConditionOperator) else operator

        if op == "gt":
            return metric_value > threshold
        elif op == "lt":
            return metric_value < threshold
        elif op == "gte":
            return metric_value >= threshold
        elif op == "lte":
            return metric_value <= threshold
        elif op == "eq":
            return metric_value == threshold
        elif op == "neq":
            return metric_value != threshold

        return False

    def _build_alert_title(
        self,
        config: AlertConfig,
        metric_value: Decimal,
    ) -> str:
        """Build alert title."""
        severity = config.severity.upper() if isinstance(config.severity, str) else config.severity.value.upper()
        op = config.condition_operator if isinstance(config.condition_operator, str) else config.condition_operator.value

        if op in ("gt", "gte"):
            action = "exceeded"
        elif op in ("lt", "lte"):
            action = "dropped below"
        else:
            action = "triggered"

        return f"[{severity}] {config.name}: {action} {config.threshold_value}"

    def _build_alert_message(
        self,
        config: AlertConfig,
        metric_value: Decimal,
    ) -> str:
        """Build detailed alert message."""
        severity = config.severity if isinstance(config.severity, str) else config.severity.value
        return (
            f"Alert '{config.name}' triggered.\n"
            f"Metric: {config.metric_name}\n"
            f"Current Value: {metric_value}\n"
            f"Threshold: {config.threshold_value}\n"
            f"Severity: {severity}"
        )

    async def _record_alert(self, trigger: AlertTrigger) -> None:
        """Record alert trigger in database."""
        async with self._session_factory() as session:
            await session.execute(
                text("""
                    INSERT INTO alert_history (
                        id, alert_config_id, status, severity, title, message,
                        metric_value, threshold_value, context, triggered_at
                    ) VALUES (
                        :id, :config_id, :status, :severity, :title, :message,
                        :metric_value, :threshold_value, :context::jsonb, :triggered_at
                    )
                """),
                {
                    "id": str(trigger.id),
                    "config_id": str(trigger.alert_config_id),
                    "status": trigger.status if isinstance(trigger.status, str) else trigger.status.value,
                    "severity": trigger.severity if isinstance(trigger.severity, str) else trigger.severity.value,
                    "title": trigger.title,
                    "message": trigger.message,
                    "metric_value": float(trigger.metric_value) if trigger.metric_value else None,
                    "threshold_value": float(trigger.threshold_value) if trigger.threshold_value else None,
                    "context": str(trigger.context).replace("'", '"') if trigger.context else "{}",
                    "triggered_at": trigger.triggered_at,
                },
            )
            await session.commit()

    def is_in_cooldown(
        self,
        config_id: uuid.UUID,
        cooldown_seconds: int,
    ) -> bool:
        """Check if an alert config is in cooldown period."""
        last_trigger = self._cooldown_tracker.get(config_id)
        if not last_trigger:
            return False

        elapsed = (datetime.now(UTC) - last_trigger).total_seconds()
        return elapsed < cooldown_seconds

    def clear_cooldown(self, config_id: uuid.UUID) -> None:
        """Clear cooldown for an alert config."""
        self._cooldown_tracker.pop(config_id, None)


# =============================================================================
# Module Singleton
# =============================================================================

_alert_engine: AlertEvaluationEngine | None = None


def get_alert_engine(
    session_factory: Callable[[], Any] | None = None,
    *,
    metric_provider: MetricProvider | None = None,
) -> AlertEvaluationEngine:
    """Get or create the alert engine singleton."""
    global _alert_engine
    if _alert_engine is None and session_factory is not None:
        _alert_engine = AlertEvaluationEngine(
            session_factory,
            metric_provider=metric_provider,
        )
    if _alert_engine is None:
        raise AlertEngineError("Alert engine not initialized")
    return _alert_engine


__all__ = [
    "AlertConfig",
    "AlertConfigNotFoundError",
    "AlertEngineError",
    "AlertEvaluationEngine",
    "AlertSeverity",
    "AlertStatus",
    "AlertTrigger",
    "ConditionOperator",
    "ConditionType",
    "MetricProvider",
    "MetricValue",
    "get_alert_engine",
]
