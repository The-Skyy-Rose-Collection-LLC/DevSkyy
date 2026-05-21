"""AOS MetricsCollector — lightweight in-process counters and gauges."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetricSample:
    """A single recorded metric observation."""

    name: str
    value: float
    labels: dict[str, str]
    recorded_at: float = field(default_factory=time.time)


class MetricsCollector:
    """Fire-and-forget in-process counter and gauge store.

    All methods are synchronous and never raise — suitable for call sites that
    cannot afford to handle metric failures (e.g. hot execution paths).

    Usage::

        metrics = MetricsCollector()
        metrics.increment("spawn.count", labels={"agent_type": "worker"})
        metrics.gauge("budget.remaining_usd", 87.50)
        metrics.timing("execute.duration_ms", 142.3)

        all_samples = metrics.samples("spawn.count")
        current = metrics.current("budget.remaining_usd")
    """

    def __init__(self) -> None:
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._history: list[MetricSample] = []

    # ---------------------------------------------------------------- counters

    def increment(
        self,
        name: str,
        by: float = 1.0,
        *,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Increment a named counter."""
        self._counters[name] = self._counters.get(name, 0.0) + by
        self._history.append(MetricSample(name=name, value=by, labels=labels or {}))

    def count(self, name: str) -> float:
        """Return the cumulative counter value (0.0 if never incremented)."""
        return self._counters.get(name, 0.0)

    # ----------------------------------------------------------------- gauges

    def gauge(
        self,
        name: str,
        value: float,
        *,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Set a gauge to an absolute value."""
        self._gauges[name] = value
        self._history.append(MetricSample(name=name, value=value, labels=labels or {}))

    def timing(
        self,
        name: str,
        duration_ms: float,
        *,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Record a timing observation (stored as a gauge sample)."""
        self.gauge(name, duration_ms, labels=labels)

    def current(self, name: str) -> float | None:
        """Return the latest gauge value, or None if the gauge was never set."""
        return self._gauges.get(name)

    # ----------------------------------------------------------------- history

    def samples(self, name: str) -> tuple[MetricSample, ...]:
        """Return all recorded samples for a metric name, oldest first."""
        return tuple(s for s in self._history if s.name == name)

    def all_metric_names(self) -> frozenset[str]:
        """Return every metric name that has been recorded."""
        return frozenset(s.name for s in self._history)

    def snapshot(self) -> dict[str, Any]:
        """Return a point-in-time snapshot of all counters and gauges."""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "sample_count": len(self._history),
        }

    def reset(self) -> None:
        """Clear all state — primarily useful between tests."""
        self._counters.clear()
        self._gauges.clear()
        self._history.clear()
