"""
Elite Studio Prometheus Metrics

Counters, histograms, and gauges for the Elite Studio image pipeline.
Registered once at module level with duplicate-registration guards.

Usage:
    from monitoring.elite_studio_metrics import (
        record_job_completed,
        record_stage_duration,
        record_cost,
        record_qc_score,
        set_active_jobs,
        set_queue_depth,
        record_retry,
    )
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy metric construction — guards against duplicate registration when the
# module is reloaded or imported in multiple test processes.
# ---------------------------------------------------------------------------


def _make_counter(name: str, doc: str, labels: list[str]):
    from prometheus_client import Counter

    try:
        return Counter(name, doc, labels)
    except ValueError:
        # Already registered — pull from the collector registry.
        from prometheus_client import REGISTRY

        return REGISTRY._names_to_collectors.get(name)


def _make_histogram(name: str, doc: str, labels: list[str], buckets=None):
    from prometheus_client import Histogram

    kwargs: dict = {"labelnames": labels}
    if buckets is not None:
        kwargs["buckets"] = buckets
    try:
        return Histogram(name, doc, **kwargs)
    except ValueError:
        from prometheus_client import REGISTRY

        return REGISTRY._names_to_collectors.get(name)


def _make_gauge(name: str, doc: str, labels: list[str] | None = None):
    from prometheus_client import Gauge

    try:
        return Gauge(name, doc, labels or [])
    except ValueError:
        from prometheus_client import REGISTRY

        return REGISTRY._names_to_collectors.get(name)


# ---------------------------------------------------------------------------
# Metric definitions
# ---------------------------------------------------------------------------

elite_studio_jobs_total = _make_counter(
    "elite_studio_jobs_total",
    "Total Elite Studio render jobs by final status",
    ["status"],  # success | error | skipped
)

elite_studio_stage_duration_s = _make_histogram(
    "elite_studio_stage_duration_s",
    "Time spent in each pipeline stage (seconds)",
    ["stage"],  # vision | generation | quality | compositing | finalize
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0),
)

elite_studio_cost_dollars = _make_counter(
    "elite_studio_cost_dollars_total",
    "Cumulative API cost in USD by provider",
    ["provider"],  # gemini | openai | anthropic
)

elite_studio_qc_score = _make_histogram(
    "elite_studio_qc_score",
    "Quality-control score for generated images (0.0–1.0)",
    [],
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)

elite_studio_active_jobs = _make_gauge(
    "elite_studio_active_jobs",
    "Number of Elite Studio jobs currently running",
)

elite_studio_queue_depth = _make_gauge(
    "elite_studio_queue_depth",
    "Number of jobs waiting in the Elite Studio queue",
)

elite_studio_retry_total = _make_counter(
    "elite_studio_retry_total",
    "Total number of pipeline stage retries",
    ["stage"],
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def record_job_completed(status: str) -> None:
    """Increment job counter for a terminal status."""
    try:
        elite_studio_jobs_total.labels(status=status).inc()
    except Exception as exc:  # noqa: BLE001
        logger.debug("elite_studio_jobs_total increment skipped: %s", exc)


def record_stage_duration(stage: str, duration_s: float) -> None:
    """Observe a stage timing sample."""
    try:
        elite_studio_stage_duration_s.labels(stage=stage).observe(duration_s)
    except Exception as exc:  # noqa: BLE001
        logger.debug("elite_studio_stage_duration_s observe skipped: %s", exc)


def record_cost(provider: str, cost_usd: float) -> None:
    """Add to cumulative cost counter for a provider."""
    try:
        elite_studio_cost_dollars.labels(provider=provider).inc(cost_usd)
    except Exception as exc:  # noqa: BLE001
        logger.debug("elite_studio_cost_dollars increment skipped: %s", exc)


def record_qc_score(score: float) -> None:
    """Observe a QC score sample."""
    try:
        elite_studio_qc_score.observe(score)
    except Exception as exc:  # noqa: BLE001
        logger.debug("elite_studio_qc_score observe skipped: %s", exc)


def set_active_jobs(count: int) -> None:
    """Set the active-jobs gauge."""
    try:
        elite_studio_active_jobs.set(count)
    except Exception as exc:  # noqa: BLE001
        logger.debug("elite_studio_active_jobs set skipped: %s", exc)


def set_queue_depth(depth: int) -> None:
    """Set the queue-depth gauge."""
    try:
        elite_studio_queue_depth.set(depth)
    except Exception as exc:  # noqa: BLE001
        logger.debug("elite_studio_queue_depth set skipped: %s", exc)


def record_retry(stage: str) -> None:
    """Increment retry counter for a stage."""
    try:
        elite_studio_retry_total.labels(stage=stage).inc()
    except Exception as exc:  # noqa: BLE001
        logger.debug("elite_studio_retry_total increment skipped: %s", exc)
