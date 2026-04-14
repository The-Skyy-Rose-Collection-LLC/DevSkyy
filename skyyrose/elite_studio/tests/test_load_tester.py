"""
Tests for PipelineLoadTester — concurrent stress test of the pipeline.

Tests cover:
- run() produces a LoadTestReport with all required fields
- Throughput and latency percentiles are computed correctly
- Bottleneck stage detection
- Concurrency: multiple workers without data races
- cost_per_sku_usd matches sum of stage costs
- Custom stage durations / costs
"""

from __future__ import annotations

from skyyrose.elite_studio.quality.load_tester import (
    LoadTestReport,
    PipelineLoadTester,
    _MOCK_STAGE_DURATIONS,
    _STAGE_COST_USD,
)


# ---------------------------------------------------------------------------
# LoadTestReport data class
# ---------------------------------------------------------------------------


class TestLoadTestReport:
    def test_frozen(self):
        import pytest

        r = LoadTestReport(
            total_jobs=1,
            successful=1,
            failed=0,
            throughput_per_min=60.0,
            p50_latency_s=0.1,
            p95_latency_s=0.2,
            p99_latency_s=0.3,
            bottleneck_stage="generation",
            cost_per_sku_usd=0.023,
            stage_latencies={"vision": 0.05},
        )
        with pytest.raises((AttributeError, TypeError)):
            r.total_jobs = 2  # type: ignore[misc]

    def test_all_fields_present(self):
        r = LoadTestReport(
            total_jobs=5,
            successful=4,
            failed=1,
            throughput_per_min=120.0,
            p50_latency_s=0.1,
            p95_latency_s=0.18,
            p99_latency_s=0.2,
            bottleneck_stage="vision",
            cost_per_sku_usd=0.015,
            stage_latencies={"vision": 0.1, "generation": 0.05},
        )
        assert r.total_jobs == 5
        assert r.successful == 4
        assert r.failed == 1
        assert r.bottleneck_stage == "vision"


# ---------------------------------------------------------------------------
# Basic run — single SKU, single iteration
# ---------------------------------------------------------------------------


class TestBasicRun:
    def test_run_single_sku(self):
        tester = PipelineLoadTester()
        report = tester.run(skus=["br-001"], concurrency=1, iterations=1)

        assert report.total_jobs == 1
        assert report.successful == 1
        assert report.failed == 0
        assert isinstance(report.throughput_per_min, float)
        assert report.throughput_per_min > 0

    def test_run_returns_load_test_report(self):
        tester = PipelineLoadTester()
        report = tester.run(skus=["br-001"], concurrency=1, iterations=1)
        assert isinstance(report, LoadTestReport)

    def test_run_multiple_skus(self):
        tester = PipelineLoadTester()
        report = tester.run(skus=["br-001", "sg-001", "lh-002"], concurrency=2, iterations=1)
        assert report.total_jobs == 3
        assert report.successful == 3


# ---------------------------------------------------------------------------
# Iterations multiply jobs
# ---------------------------------------------------------------------------


class TestIterations:
    def test_iterations_multiply_jobs(self):
        tester = PipelineLoadTester()
        report = tester.run(skus=["br-001", "br-002"], concurrency=2, iterations=3)
        assert report.total_jobs == 6  # 2 SKUs × 3 iterations
        assert report.successful == 6

    def test_single_sku_multiple_iterations(self):
        tester = PipelineLoadTester()
        report = tester.run(skus=["sg-005"], concurrency=1, iterations=5)
        assert report.total_jobs == 5
        assert report.successful == 5


# ---------------------------------------------------------------------------
# Latency percentiles
# ---------------------------------------------------------------------------


class TestLatencyPercentiles:
    def test_percentiles_non_negative(self):
        tester = PipelineLoadTester()
        report = tester.run(skus=["br-001", "br-002"], concurrency=2, iterations=2)
        assert report.p50_latency_s >= 0.0
        assert report.p95_latency_s >= 0.0
        assert report.p99_latency_s >= 0.0

    def test_percentiles_ordered(self):
        tester = PipelineLoadTester()
        report = tester.run(skus=["br-001", "br-002", "sg-001"], concurrency=2, iterations=2)
        # p50 ≤ p95 ≤ p99 (within floating point tolerance)
        assert report.p50_latency_s <= report.p95_latency_s + 1e-6
        assert report.p95_latency_s <= report.p99_latency_s + 1e-6

    def test_single_job_percentiles_equal(self):
        tester = PipelineLoadTester()
        report = tester.run(skus=["br-001"], concurrency=1, iterations=1)
        # With one data point, all percentiles should be equal
        assert abs(report.p50_latency_s - report.p99_latency_s) < 1e-3


# ---------------------------------------------------------------------------
# Bottleneck detection
# ---------------------------------------------------------------------------


class TestBottleneckDetection:
    def test_bottleneck_stage_in_known_stages(self):
        tester = PipelineLoadTester()
        report = tester.run(skus=["br-001"], concurrency=1, iterations=1)
        assert report.bottleneck_stage in _MOCK_STAGE_DURATIONS

    def test_bottleneck_is_highest_latency_stage(self):
        # Override durations so generation is clearly slowest
        custom_durations = {
            "vision": 0.001,
            "generation": 0.05,
            "quality": 0.001,
            "compositing": 0.001,
            "finalize": 0.001,
        }
        tester = PipelineLoadTester(stage_durations=custom_durations)
        report = tester.run(skus=["br-001", "br-002"], concurrency=1, iterations=2)
        assert report.bottleneck_stage == "generation"


# ---------------------------------------------------------------------------
# Stage latencies dict
# ---------------------------------------------------------------------------


class TestStageLatencies:
    def test_stage_latencies_contains_all_stages(self):
        tester = PipelineLoadTester()
        report = tester.run(skus=["br-001"], concurrency=1, iterations=1)
        for stage in _MOCK_STAGE_DURATIONS:
            assert stage in report.stage_latencies

    def test_stage_latencies_are_floats(self):
        tester = PipelineLoadTester()
        report = tester.run(skus=["br-001"], concurrency=1, iterations=1)
        for stage, latency in report.stage_latencies.items():
            assert isinstance(latency, float)
            assert latency >= 0.0


# ---------------------------------------------------------------------------
# Cost calculation
# ---------------------------------------------------------------------------


class TestCostCalculation:
    def test_cost_matches_sum_of_stage_costs(self):
        tester = PipelineLoadTester()
        report = tester.run(skus=["br-001"], concurrency=1, iterations=1)
        expected_cost = round(sum(_STAGE_COST_USD.values()), 6)
        assert abs(report.cost_per_sku_usd - expected_cost) < 1e-6

    def test_custom_costs(self):
        custom_durations = {"vision": 0.001, "generation": 0.001}
        custom_costs = {"vision": 0.01, "generation": 0.02}
        tester = PipelineLoadTester(stage_durations=custom_durations, stage_costs=custom_costs)
        report = tester.run(skus=["br-001"], concurrency=1, iterations=1)
        assert abs(report.cost_per_sku_usd - 0.03) < 1e-6


# ---------------------------------------------------------------------------
# Concurrency
# ---------------------------------------------------------------------------


class TestConcurrency:
    def test_high_concurrency_all_succeed(self):
        tester = PipelineLoadTester()
        report = tester.run(
            skus=["br-001", "br-002", "sg-001", "lh-002"], concurrency=8, iterations=2
        )
        assert report.failed == 0
        assert report.successful == 8

    def test_throughput_is_positive(self):
        tester = PipelineLoadTester()
        report = tester.run(skus=["br-001", "br-002"], concurrency=2, iterations=1)
        assert report.throughput_per_min > 0.0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_skus_list(self):
        tester = PipelineLoadTester()
        report = tester.run(skus=[], concurrency=2, iterations=1)
        assert report.total_jobs == 0
        assert report.successful == 0
        assert report.failed == 0

    def test_percentile_empty_latencies(self):
        result = PipelineLoadTester._percentile([], 95)
        assert result == 0.0

    def test_percentile_single_value(self):
        result = PipelineLoadTester._percentile([0.5], 99)
        assert result == 0.5

    def test_percentile_two_values(self):
        vals = [0.1, 0.9]
        p50 = PipelineLoadTester._percentile(vals, 50)
        assert 0.1 <= p50 <= 0.9
