"""
Tests for Elite Studio Prometheus metrics (monitoring/elite_studio_metrics.py).

Uses a fresh CollectorRegistry per test to avoid duplicate-registration
conflicts between test runs.
"""

from __future__ import annotations

import pytest
from prometheus_client import CollectorRegistry
from prometheus_client import Counter as PCounter
from prometheus_client import Gauge as PGauge
from prometheus_client import Histogram as PHistogram


# ---------------------------------------------------------------------------
# Fixtures: isolated registry per test
# ---------------------------------------------------------------------------


@pytest.fixture()
def registry():
    """Return a fresh, isolated Prometheus registry."""
    return CollectorRegistry()


@pytest.fixture()
def jobs_counter(registry):
    return PCounter(
        "t_elite_studio_jobs_total",
        "Test job counter",
        ["status"],
        registry=registry,
    )


@pytest.fixture()
def stage_histogram(registry):
    return PHistogram(
        "t_elite_studio_stage_duration_s",
        "Test stage histogram",
        ["stage"],
        buckets=(0.1, 1.0, 10.0),
        registry=registry,
    )


@pytest.fixture()
def cost_counter(registry):
    return PCounter(
        "t_elite_studio_cost_dollars_total",
        "Test cost counter",
        ["provider"],
        registry=registry,
    )


@pytest.fixture()
def qc_histogram(registry):
    return PHistogram(
        "t_elite_studio_qc_score",
        "Test QC histogram",
        [],
        buckets=(0.25, 0.5, 0.75, 1.0),
        registry=registry,
    )


@pytest.fixture()
def active_gauge(registry):
    return PGauge(
        "t_elite_studio_active_jobs",
        "Test active jobs gauge",
        registry=registry,
    )


@pytest.fixture()
def queue_gauge(registry):
    return PGauge(
        "t_elite_studio_queue_depth",
        "Test queue depth gauge",
        registry=registry,
    )


@pytest.fixture()
def retry_counter(registry):
    return PCounter(
        "t_elite_studio_retry_total",
        "Test retry counter",
        ["stage"],
        registry=registry,
    )


# ---------------------------------------------------------------------------
# Counter tests
# ---------------------------------------------------------------------------


class TestJobsCounter:
    def test_increments_by_status(self, jobs_counter, registry):
        jobs_counter.labels(status="success").inc()
        jobs_counter.labels(status="success").inc()
        jobs_counter.labels(status="error").inc()

        from prometheus_client import generate_latest

        output = generate_latest(registry).decode()
        assert 't_elite_studio_jobs_total{status="success"} 2.0' in output
        assert 't_elite_studio_jobs_total{status="error"} 1.0' in output

    def test_skipped_status(self, jobs_counter, registry):
        jobs_counter.labels(status="skipped").inc()
        from prometheus_client import generate_latest

        output = generate_latest(registry).decode()
        assert 't_elite_studio_jobs_total{status="skipped"} 1.0' in output


class TestCostCounter:
    def test_accumulates_fractional(self, cost_counter, registry):
        cost_counter.labels(provider="gemini").inc(0.001)
        cost_counter.labels(provider="gemini").inc(0.002)
        cost_counter.labels(provider="openai").inc(0.005)

        from prometheus_client import generate_latest

        output = generate_latest(registry).decode()
        assert 't_elite_studio_cost_dollars_total{provider="gemini"}' in output
        assert 't_elite_studio_cost_dollars_total{provider="openai"}' in output


class TestRetryCounter:
    def test_retry_by_stage(self, retry_counter, registry):
        retry_counter.labels(stage="vision").inc(3)
        retry_counter.labels(stage="generation").inc(1)

        from prometheus_client import generate_latest

        output = generate_latest(registry).decode()
        assert 't_elite_studio_retry_total{stage="vision"} 3.0' in output
        assert 't_elite_studio_retry_total{stage="generation"} 1.0' in output


# ---------------------------------------------------------------------------
# Histogram tests
# ---------------------------------------------------------------------------


class TestStageDurationHistogram:
    def test_observe_records_sample(self, stage_histogram, registry):
        stage_histogram.labels(stage="vision").observe(0.5)
        stage_histogram.labels(stage="generation").observe(2.1)

        from prometheus_client import generate_latest

        output = generate_latest(registry).decode()
        assert 't_elite_studio_stage_duration_s_count{stage="vision"} 1.0' in output
        assert 't_elite_studio_stage_duration_s_count{stage="generation"} 1.0' in output

    def test_multiple_observations(self, stage_histogram, registry):
        for _ in range(5):
            stage_histogram.labels(stage="quality").observe(0.8)

        from prometheus_client import generate_latest

        output = generate_latest(registry).decode()
        assert 't_elite_studio_stage_duration_s_count{stage="quality"} 5.0' in output


class TestQCHistogram:
    def test_observe_qc_score(self, qc_histogram, registry):
        for score in [0.3, 0.7, 0.9, 0.95]:
            qc_histogram.observe(score)

        from prometheus_client import generate_latest

        output = generate_latest(registry).decode()
        assert "t_elite_studio_qc_score_count 4.0" in output

    def test_sum_is_correct(self, qc_histogram, registry):
        qc_histogram.observe(0.5)
        qc_histogram.observe(0.5)

        from prometheus_client import generate_latest

        output = generate_latest(registry).decode()
        assert "t_elite_studio_qc_score_sum 1.0" in output


# ---------------------------------------------------------------------------
# Gauge tests
# ---------------------------------------------------------------------------


class TestGauges:
    def test_active_jobs_set(self, active_gauge, registry):
        active_gauge.set(3)
        from prometheus_client import generate_latest

        output = generate_latest(registry).decode()
        assert "t_elite_studio_active_jobs 3.0" in output

    def test_queue_depth_set(self, queue_gauge, registry):
        queue_gauge.set(42)
        from prometheus_client import generate_latest

        output = generate_latest(registry).decode()
        assert "t_elite_studio_queue_depth 42.0" in output

    def test_gauge_can_go_up_and_down(self, active_gauge, registry):
        active_gauge.set(10)
        active_gauge.set(5)

        from prometheus_client import generate_latest

        output = generate_latest(registry).decode()
        assert "t_elite_studio_active_jobs 5.0" in output


# ---------------------------------------------------------------------------
# Helper function tests (using module-level metrics with try/except guard)
# ---------------------------------------------------------------------------


class TestHelperFunctions:
    def test_record_job_completed_does_not_raise(self):
        from monitoring.elite_studio_metrics import record_job_completed

        # Should not raise even if prometheus_client has issues
        record_job_completed("success")
        record_job_completed("error")
        record_job_completed("skipped")

    def test_record_stage_duration_does_not_raise(self):
        from monitoring.elite_studio_metrics import record_stage_duration

        record_stage_duration("vision", 1.23)
        record_stage_duration("generation", 4.56)

    def test_record_cost_does_not_raise(self):
        from monitoring.elite_studio_metrics import record_cost

        record_cost("gemini", 0.001)
        record_cost("openai", 0.005)

    def test_record_qc_score_does_not_raise(self):
        from monitoring.elite_studio_metrics import record_qc_score

        record_qc_score(0.87)

    def test_set_active_jobs_does_not_raise(self):
        from monitoring.elite_studio_metrics import set_active_jobs

        set_active_jobs(0)
        set_active_jobs(5)

    def test_set_queue_depth_does_not_raise(self):
        from monitoring.elite_studio_metrics import set_queue_depth

        set_queue_depth(0)
        set_queue_depth(100)

    def test_record_retry_does_not_raise(self):
        from monitoring.elite_studio_metrics import record_retry

        record_retry("vision")
        record_retry("generation")
