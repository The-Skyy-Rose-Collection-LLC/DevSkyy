"""Pipeline event bus.

Pipelines emit structured events at each stage boundary so external systems
(metrics, audit logs, webhooks, dashboards, the elite studio approval queue)
can react without coupling to the pipeline internals.

The bus is intentionally tiny: a list of async subscribers, no broker. For
cross-process delivery, plug a webhook subscriber that forwards to the
existing :mod:`api.webhooks` infrastructure.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from pipelines.clothing_3d.models import PipelineStage, PipelineStatus

logger = logging.getLogger(__name__)

Subscriber = Callable[["PipelineEvent"], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class PipelineEvent:
    """Event emitted by the pipeline.

    Use :attr:`stage` for stage boundaries (``stage_started`` / ``stage_finished``)
    and :attr:`status` for overall pipeline state transitions.
    """

    correlation_id: str
    timestamp: datetime
    name: str
    stage: PipelineStage | None = None
    status: PipelineStatus | None = None
    payload: dict[str, Any] = field(default_factory=dict)


class PipelineEventBus:
    """In-process pub/sub for pipeline events.

    Subscribers are called concurrently for each event; one failing subscriber
    does not block the others. Subscriber exceptions are logged but never
    propagate.
    """

    def __init__(self) -> None:
        self._subscribers: list[Subscriber] = []

    def subscribe(self, sub: Subscriber) -> None:
        self._subscribers.append(sub)

    def unsubscribe(self, sub: Subscriber) -> None:
        try:
            self._subscribers.remove(sub)
        except ValueError:
            pass

    async def emit(
        self,
        *,
        correlation_id: str,
        name: str,
        stage: PipelineStage | None = None,
        status: PipelineStatus | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        if not self._subscribers:
            return

        event = PipelineEvent(
            correlation_id=correlation_id,
            timestamp=datetime.now(UTC),
            name=name,
            stage=stage,
            status=status,
            payload=payload or {},
        )

        results = await asyncio.gather(
            *(self._safe_invoke(sub, event) for sub in self._subscribers),
            return_exceptions=False,
        )
        del results  # silence linters

    async def _safe_invoke(self, sub: Subscriber, event: PipelineEvent) -> None:
        try:
            await sub(event)
        except Exception:  # noqa: BLE001 — subscriber errors must not bubble
            logger.exception("Pipeline event subscriber failed for event %s", event.name)


# =============================================================================
# Built-in subscribers
# =============================================================================


def log_event_subscriber(level: int = logging.INFO) -> Subscriber:
    """Subscriber that just logs each event — useful as a default."""

    async def _sub(event: PipelineEvent) -> None:
        logger.log(
            level,
            "pipeline.event name=%s stage=%s status=%s corr=%s",
            event.name,
            event.stage.value if event.stage else "",
            event.status.value if event.status else "",
            event.correlation_id,
        )

    return _sub


def webhook_subscriber(
    url: str,
    *,
    timeout_seconds: float = 5.0,
) -> Subscriber:
    """Subscriber that POSTs each event to ``url``.

    Uses :mod:`httpx` if installed; silently no-ops otherwise so the pipeline
    doesn't fail just because httpx is missing in a slim environment.
    """

    async def _sub(event: PipelineEvent) -> None:
        try:
            import httpx
        except ImportError:
            logger.debug("httpx not installed; skipping webhook %s", url)
            return

        payload = {
            "correlation_id": event.correlation_id,
            "timestamp": event.timestamp.isoformat(),
            "name": event.name,
            "stage": event.stage.value if event.stage else None,
            "status": event.status.value if event.status else None,
            "payload": event.payload,
        }
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            await client.post(url, json=payload)

    return _sub


__all__ = [
    "PipelineEvent",
    "PipelineEventBus",
    "Subscriber",
    "log_event_subscriber",
    "webhook_subscriber",
]
