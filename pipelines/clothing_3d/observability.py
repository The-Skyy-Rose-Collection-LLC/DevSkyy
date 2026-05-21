"""Observability — structured logging + Prometheus metrics.

Three concrete deliverables:

1. :func:`configure_logging` — JSON-formatted stdlib logger that includes
   correlation IDs on every record. Idempotent; safe to call repeatedly.
2. :class:`PipelineMetrics` — Prometheus counters/histograms for the
   pipeline. Exposed via :func:`render_metrics` which returns the
   text/plain payload for ``/metrics`` endpoints.
3. :func:`metrics_event_subscriber` — drop-in subscriber for
   :class:`PipelineEventBus` that wires pipeline events into the metrics.

All Prometheus imports are lazy so the module loads with a friendly fallback
(no-op metric impls) when ``prometheus_client`` isn't installed.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import json
import logging
import logging.config
import os
import sys
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from pipelines.clothing_3d.events import PipelineEvent

# =============================================================================
# Logging
# =============================================================================


class _JsonFormatter(logging.Formatter):
    """Minimal JSON log formatter — one JSON object per line."""

    _RESERVED = {
        "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "message", "asctime",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)

        # Surface any custom kwargs (logger.info(msg, extra={...}))
        for key, value in record.__dict__.items():
            if key not in self._RESERVED and not key.startswith("_"):
                try:
                    json.dumps(value)
                    payload[key] = value
                except (TypeError, ValueError):
                    payload[key] = repr(value)

        return json.dumps(payload, separators=(",", ":"), default=str)


def configure_logging(
    *,
    level: str | int = "INFO",
    json_format: bool | None = None,
) -> None:
    """Install the JSON formatter on the root logger.

    Args:
        level: Stdlib log level (string or int).
        json_format: Force JSON ``True``/``False``. ``None`` → JSON when stdout
            isn't a TTY (i.e. running under k8s / systemd / Docker).
    """
    if json_format is None:
        json_format = not sys.stdout.isatty()

    root = logging.getLogger()
    # Idempotency: clear our own handlers, leave others alone.
    for h in list(root.handlers):
        if getattr(h, "_clothing_3d_owned", False):
            root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    if json_format:
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
    handler._clothing_3d_owned = True  # type: ignore[attr-defined]
    root.addHandler(handler)
    root.setLevel(level)


# =============================================================================
# Prometheus metrics
# =============================================================================


class _NoopMetric:
    """Stand-in when prometheus_client isn't installed."""

    def labels(self, *_args: Any, **_kw: Any) -> _NoopMetric:
        return self

    def inc(self, *_args: Any, **_kw: Any) -> None:
        pass

    def observe(self, *_args: Any, **_kw: Any) -> None:
        pass

    def set(self, *_args: Any, **_kw: Any) -> None:
        pass


class PipelineMetrics:
    """Prometheus metrics for the clothing 3D pipeline.

    Each instance owns its own metric registrations, so multiple test runs in
    one process don't trip the "duplicated timeseries" guard. In production,
    use the singleton :func:`get_metrics`.
    """

    def __init__(self, *, namespace: str = "clothing_3d") -> None:
        self.namespace = namespace
        try:
            from prometheus_client import (  # type: ignore[import-not-found]
                CollectorRegistry,
                Counter,
                Gauge,
                Histogram,
            )
        except ImportError:
            self._registry = None
            self.runs_total = _NoopMetric()
            self.run_duration_seconds = _NoopMetric()
            self.stage_duration_seconds = _NoopMetric()
            self.stage_failures_total = _NoopMetric()
            self.queue_depth = _NoopMetric()
            self.backend_cost_usd = _NoopMetric()
            self.cache_total = _NoopMetric()
            return

        self._registry = CollectorRegistry()
        self.runs_total = Counter(
            "runs_total",
            "Pipeline runs by terminal status",
            labelnames=("status", "backend"),
            namespace=namespace,
            registry=self._registry,
        )
        self.run_duration_seconds = Histogram(
            "run_duration_seconds",
            "End-to-end pipeline duration",
            labelnames=("status", "backend"),
            namespace=namespace,
            buckets=(0.5, 1, 2, 5, 10, 30, 60, 120, 300, 600),
            registry=self._registry,
        )
        self.stage_duration_seconds = Histogram(
            "stage_duration_seconds",
            "Per-stage duration",
            labelnames=("stage",),
            namespace=namespace,
            buckets=(0.05, 0.1, 0.5, 1, 5, 10, 30, 60, 300),
            registry=self._registry,
        )
        self.stage_failures_total = Counter(
            "stage_failures_total",
            "Stage failures",
            labelnames=("stage",),
            namespace=namespace,
            registry=self._registry,
        )
        self.queue_depth = Gauge(
            "queue_depth",
            "Queued jobs awaiting a worker",
            namespace=namespace,
            registry=self._registry,
        )
        self.backend_cost_usd = Counter(
            "backend_cost_usd_total",
            "Cumulative paid backend spend (USD)",
            labelnames=("backend",),
            namespace=namespace,
            registry=self._registry,
        )
        self.cache_total = Counter(
            "cache_total",
            "Idempotency cache lookups",
            labelnames=("outcome",),  # hit | miss
            namespace=namespace,
            registry=self._registry,
        )

    def render(self) -> tuple[bytes, str]:
        """Return ``(body, content_type)`` for a Prometheus scrape endpoint."""
        try:
            from prometheus_client import (  # type: ignore[import-not-found]
                CONTENT_TYPE_LATEST,
                generate_latest,
            )
        except ImportError:
            return b"", "text/plain"
        if self._registry is None:
            return b"", "text/plain"
        return generate_latest(self._registry), CONTENT_TYPE_LATEST


# =============================================================================
# Singleton
# =============================================================================


_default_metrics: PipelineMetrics | None = None


def get_metrics() -> PipelineMetrics:
    global _default_metrics
    if _default_metrics is None:
        namespace = os.getenv("CLOTHING_3D_METRICS_NS", "clothing_3d")
        _default_metrics = PipelineMetrics(namespace=namespace)
    return _default_metrics


def render_metrics() -> tuple[bytes, str]:
    return get_metrics().render()


# =============================================================================
# Event-bus integration
# =============================================================================


def metrics_event_subscriber(
    metrics: PipelineMetrics | None = None,
) -> Callable[[PipelineEvent], Awaitable[None]]:
    """Build a :class:`PipelineEventBus` subscriber that updates metrics."""
    m = metrics or get_metrics()

    stage_start: dict[tuple[str, str], float] = {}

    async def _sub(event: PipelineEvent) -> None:
        ts = event.timestamp.timestamp()

        if event.name == "stage.started" and event.stage is not None:
            stage_start[(event.correlation_id, event.stage.value)] = ts
            return

        if event.name == "stage.finished" and event.stage is not None:
            start = stage_start.pop((event.correlation_id, event.stage.value), None)
            if start is not None:
                m.stage_duration_seconds.labels(stage=event.stage.value).observe(ts - start)
            return

        if event.name == "pipeline.succeeded":
            duration = event.payload.get("duration", 0.0)
            backend = event.payload.get("backend") or "unknown"
            m.run_duration_seconds.labels(status="succeeded", backend=backend).observe(duration)
            m.runs_total.labels(status="succeeded", backend=backend).inc()
            return

        if event.name in {"pipeline.failed", "pipeline.rejected"}:
            status = event.name.removeprefix("pipeline.")
            backend = event.payload.get("backend") or "unknown"
            m.runs_total.labels(status=status, backend=backend).inc()
            return

    return _sub


__all__ = [
    "PipelineMetrics",
    "configure_logging",
    "get_metrics",
    "metrics_event_subscriber",
    "render_metrics",
]
