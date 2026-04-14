"""
Tests for PipelineLoadTester — concurrent mock pipeline stress tester.

All stage durations are set to near-zero so the test suite runs quickly.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from skyyrose.elite_studio.quality.load_tester import LoadTestReport, PipelineLoadTester

# Fast stage durations for tests (sub-millisecond)
_FAST_STAGES = {
    "vision": 0.0001,
    "generation": 0.0002,
    "quality": 0.0001,
    "compositing": 0.0001,
    "finalize": 0.00001,
}

_FAST_COSTS = {
    "vision": 0.002,
    "generation": 0.015,
    "quality": 0.001,
    "compositing": 0.005,
    "finalize": 0.0,
}


# ---------------------------------------------------------------------------
# LoadTestReport dataclass
# ---------------------------------------------------------------------------


class TestLoadTestReport:
    def test_frozen(self):
        report = LoadTestReport(
            total_jobs=1,
            successful=1,
            failed=0,
            throughput_per_min=60.0,
            p50_latency_s=0.1,
            p95_latency_s=0.2,
            p99_latency_s=0.3,
            bottleneck_stage="generation",
            cost_per_sku_usd=0.023,
            stage_latencies={},
        )
        with pytest.raises((FrozenInstanceError, AttributeError)):
            report.total_jobs = 99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Basic run scenarios
# ---------------------------------------------------------------------------


class TestPipelineLoadTester:
    def _make_tester(self) -> PipelineLoadTester:
        return PipelineLoadTester(
            stage_durations=dict(_FAST_STAGES),
            stage_costs=dict(_FAST_COSTS),
        )

    def test_run_single_sku_single_iteration(self):
        tester = self._make_tester()
        report = tester.run(skus=["br-001"], concurrency=1, iterations=1)

        assert report.total_jobs == 1
        assert report.successful == 1
        assert report.failed == 0

    def test_run_multiple_skus(self):
        tester = self._make_tester()
        skus = ["br-001", "br-002", "sg-001"]
        report = tester.run(skus=skus, concurrency=2, iterations=1)

        assert report.total_jobs == 3
        assert report.successful == 3
        assert report.failed == 0

    def test_run_multiple_iterations(self):
        tester = self._make_tester()
        report = tester.run(skus=["br-001"], concurrency=1, iterations=3)

        assert report.total_jobs == 3
        assert report.successful == 3

    def test_run_with_concurrency_4(self):
        tester = self._make_tester()
        report = tester.run(
            skus=["br-001", "br-002", "sg-001", "sg-002"],
            concurrency=4,
            iterations=1,
        )

        assert report.successful == 4
        assert report.total_jobs == 4

    def test_throughput_positive(self):
        tester = self._make_tester()
        report = tester.run(skus=["br-001", "br-002"], concurrency=2, iterations=1)

        assert report.throughput_per_min > 0.0

    def test_latency_percentiles_ordered(self):
        tester = self._make_tester()
        report = tester.run(skus=["br-001"] * 5, concurrency=2, iterations=2)

        assert report.p50_latency_s <= report.p95_latency_s <= report.p99_latency_s

    def test_latency_percentiles_non_negative(self):
        tester = self._make_tester()
        report = tester.run(skus=["br-001"], concurrency=1, iterations=1)

        assert report.p50_latency_s >= 0.0
        assert report.p95_latency_s >= 0.0
        assert report.p99_latency_s >= 0.0

    def test_bottleneck_stage_is_valid_stage(self):
        tester = self._make_tester()
        report = tester.run(skus=["br-001", "sg-001"], concurrency=2, iterations=1)

        assert report.bottleneck_stage in _FAST_STAGES

    def test_cost_per_sku_matches_sum_of_stage_costs(self):
        tester = self._make_tester()
        report = tester.run(skus=["br-001"], concurrency=1, iterations=1)

        expected_cost = sum(_FAST_COSTS.values())
        assert report.cost_per_sku_usd == pytest.approx(expected_cost, abs=1e-6)

    def test_stage_latencies_keys_match_stages(self):
        tester = self._make_tester()
        report = tester.run(skus=["br-001"], concurrency=1, iterations=1)

        assert set(report.stage_latencies.keys()) == set(_FAST_STAGES.keys())

    def test_stage_latencies_all_non_negative(self):
        tester = self._make_tester()
        report = tester.run(skus=["br-001", "br-002"], concurrency=2, iterations=1)

        for stage, latency in report.stage_latencies.items():
            assert latency >= 0.0, f"Stage {stage} has negative latency {latency}"

    def test_empty_skus_returns_zero_jobs(self):
        tester = self._make_tester()
        report = tester.run(skus=[], concurrency=1, iterations=1)

        assert report.total_jobs == 0
        assert report.successful == 0
        assert report.failed == 0
        assert report.throughput_per_min == 0.0


# ---------------------------------------------------------------------------
# Percentile helper
# ---------------------------------------------------------------------------


class TestPercentileHelper:
    def test_empty_list_returns_zero(self):
        assert PipelineLoadTester._percentile([], 50) == 0.0

    def test_single_element(self):
        assert PipelineLoadTester._percentile([0.5], 50) == 0.5
        assert PipelineLoadTester._percentile([0.5], 0) == 0.5
        assert PipelineLoadTester._percentile([0.5], 100) == 0.5

    def test_known_median(self):
        data = sorted([1.0, 2.0, 3.0, 4.0, 5.0])
        assert PipelineLoadTester._percentile(data, 50) == pytest.approx(3.0)

    def test_p100_returns_max(self):
        data = sorted([0.1, 0.5, 1.0, 2.0])
        assert PipelineLoadTester._percentile(data, 100) == pytest.approx(2.0)

    def test_p0_returns_min(self):
        data = sorted([0.1, 0.5, 1.0, 2.0])
        assert PipelineLoadTester._percentile(data, 0) == pytest.approx(0.1)
