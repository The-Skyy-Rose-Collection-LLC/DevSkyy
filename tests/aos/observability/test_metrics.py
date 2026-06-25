"""Tests for MetricsCollector."""

from __future__ import annotations

import pytest

from aos.observability.metrics import MetricSample, MetricsCollector


@pytest.fixture
def metrics() -> MetricsCollector:
    return MetricsCollector()


class TestIncrement:
    def test_increment_default_by_one(self, metrics):
        metrics.increment("hits")
        assert metrics.count("hits") == 1.0

    def test_increment_accumulates(self, metrics):
        metrics.increment("hits")
        metrics.increment("hits")
        metrics.increment("hits")
        assert metrics.count("hits") == 3.0

    def test_increment_custom_by(self, metrics):
        metrics.increment("bytes", by=512.0)
        assert metrics.count("bytes") == 512.0

    def test_increment_with_labels_recorded(self, metrics):
        metrics.increment("spawn.count", labels={"agent_type": "worker"})
        samples = metrics.samples("spawn.count")
        assert len(samples) == 1
        assert samples[0].labels == {"agent_type": "worker"}

    def test_count_unknown_returns_zero(self, metrics):
        assert metrics.count("does.not.exist") == 0.0

    def test_increment_no_labels_defaults_to_empty_dict(self, metrics):
        metrics.increment("x")
        assert metrics.samples("x")[0].labels == {}


class TestGauge:
    def test_gauge_set_and_read(self, metrics):
        metrics.gauge("budget.remaining_usd", 87.50)
        assert metrics.current("budget.remaining_usd") == 87.50

    def test_gauge_overwrite(self, metrics):
        metrics.gauge("mem", 100.0)
        metrics.gauge("mem", 200.0)
        assert metrics.current("mem") == 200.0

    def test_current_unknown_returns_none(self, metrics):
        assert metrics.current("no.such.gauge") is None

    def test_gauge_with_labels(self, metrics):
        metrics.gauge("cpu", 0.85, labels={"host": "node-1"})
        samples = metrics.samples("cpu")
        assert samples[0].labels == {"host": "node-1"}


class TestTiming:
    def test_timing_stored_as_gauge_sample(self, metrics):
        metrics.timing("execute.duration_ms", 142.3)
        assert metrics.current("execute.duration_ms") == 142.3

    def test_timing_with_labels(self, metrics):
        metrics.timing("latency", 50.0, labels={"op": "read"})
        samples = metrics.samples("latency")
        assert samples[0].labels == {"op": "read"}


class TestHistory:
    def test_samples_oldest_first(self, metrics):
        metrics.increment("ev")
        metrics.increment("ev", by=2.0)
        samples = metrics.samples("ev")
        assert samples[0].value == 1.0
        assert samples[1].value == 2.0

    def test_samples_empty_for_unknown(self, metrics):
        assert metrics.samples("ghost") == ()

    def test_all_metric_names_covers_increments_and_gauges(self, metrics):
        metrics.increment("a")
        metrics.gauge("b", 1.0)
        metrics.timing("c", 10.0)
        assert metrics.all_metric_names() == frozenset({"a", "b", "c"})

    def test_all_metric_names_empty_on_fresh(self, metrics):
        assert metrics.all_metric_names() == frozenset()


class TestSnapshot:
    def test_snapshot_has_counters_and_gauges(self, metrics):
        metrics.increment("req")
        metrics.gauge("mem", 512.0)
        snap = metrics.snapshot()
        assert snap["counters"] == {"req": 1.0}
        assert snap["gauges"] == {"mem": 512.0}
        assert snap["sample_count"] == 2

    def test_snapshot_empty_on_fresh(self, metrics):
        snap = metrics.snapshot()
        assert snap == {"counters": {}, "gauges": {}, "sample_count": 0}


class TestReset:
    def test_reset_clears_all_state(self, metrics):
        metrics.increment("x")
        metrics.gauge("y", 1.0)
        metrics.reset()
        assert metrics.count("x") == 0.0
        assert metrics.current("y") is None
        assert metrics.all_metric_names() == frozenset()
        assert metrics.snapshot()["sample_count"] == 0


class TestMetricSampleType:
    def test_metric_sample_has_recorded_at(self):
        s = MetricSample(name="n", value=1.0, labels={})
        assert s.recorded_at > 0

    def test_metric_sample_fields(self):
        s = MetricSample(name="n", value=3.14, labels={"k": "v"})
        assert s.name == "n"
        assert s.value == 3.14
        assert s.labels == {"k": "v"}
