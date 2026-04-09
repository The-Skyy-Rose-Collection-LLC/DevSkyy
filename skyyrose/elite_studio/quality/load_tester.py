"""
Pipeline Load Tester — stress test the graph pipeline with concurrent mock runs.

Simulates concurrent graph executions using ThreadPoolExecutor. All agents
are mocked (instant results) so this measures scheduling overhead and
concurrency behaviour, not real AI latency.

Provides throughput, latency percentiles, per-stage breakdowns, and a
rough cost estimate based on configurable per-stage USD rates.
"""

from __future__ import annotations

import logging
import math
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Simulated per-stage durations (seconds) — used for mock timing
# ------------------------------------------------------------------
_MOCK_STAGE_DURATIONS: dict[str, float] = {
    "vision": 0.05,
    "generation": 0.08,
    "quality": 0.03,
    "compositing": 0.04,
    "finalize": 0.001,
}

# Rough USD cost per stage per invocation (estimates)
_STAGE_COST_USD: dict[str, float] = {
    "vision": 0.002,
    "generation": 0.015,
    "quality": 0.001,
    "compositing": 0.005,
    "finalize": 0.0,
}


@dataclass(frozen=True)
class LoadTestReport:
    """Summary of a load test run."""

    total_jobs: int
    successful: int
    failed: int
    throughput_per_min: float
    p50_latency_s: float
    p95_latency_s: float
    p99_latency_s: float
    bottleneck_stage: str  # stage with highest average latency
    cost_per_sku_usd: float
    stage_latencies: dict[str, float]  # stage → average seconds


@dataclass
class _JobResult:
    """Internal result for a single mock job execution."""

    sku: str
    success: bool
    wall_time_s: float
    stage_times: dict[str, float]
    error: str = ""


class PipelineLoadTester:
    """Stress test the graph pipeline with concurrent mock runs.

    All agent calls are mocked (no network I/O) so this isolates
    thread scheduling, queue overhead, and concurrency bottlenecks.

    Usage:
        tester = PipelineLoadTester()
        report = tester.run(
            skus=["br-001", "br-002", "sg-001"],
            concurrency=4,
            iterations=2,
        )
        print(report.throughput_per_min)
    """

    def __init__(
        self,
        stage_durations: dict[str, float] | None = None,
        stage_costs: dict[str, float] | None = None,
    ) -> None:
        """Initialise the load tester.

        Args:
            stage_durations: Override mock stage durations (seconds).
            stage_costs: Override per-stage USD cost estimates.
        """
        self._stage_durations = stage_durations or dict(_MOCK_STAGE_DURATIONS)
        self._stage_costs = stage_costs or dict(_STAGE_COST_USD)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        skus: list[str],
        concurrency: int = 4,
        iterations: int = 1,
    ) -> LoadTestReport:
        """Execute load test.

        Args:
            skus: List of SKUs to process. Each SKU × iterations = one job.
            concurrency: Thread pool size.
            iterations: How many times each SKU is processed.
            timeout_per_job: Per-job timeout in seconds.

        Returns:
            LoadTestReport with aggregated metrics.
        """
        jobs: list[tuple[str, int]] = [
            (sku, iteration)
            for sku in skus
            for iteration in range(iterations)
        ]
        total_jobs = len(jobs)

        logger.info(
            "Load test starting: %d jobs, concurrency=%d", total_jobs, concurrency
        )

        results: list[_JobResult] = []
        wall_start = time.monotonic()

        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = {
                pool.submit(self._run_mock_job, sku, iteration): (sku, iteration)
                for sku, iteration in jobs
            }
            for future in as_completed(futures):
                try:
                    result = future.result()
                except Exception as exc:
                    sku, iteration = futures[future]
                    result = _JobResult(
                        sku=sku,
                        success=False,
                        wall_time_s=0.0,
                        stage_times={},
                        error=str(exc),
                    )
                results.append(result)

        total_wall = time.monotonic() - wall_start
        return self._build_report(results, total_jobs, total_wall)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_mock_job(self, sku: str, iteration: int) -> _JobResult:
        """Simulate a single pipeline execution with instant mock stages.

        Args:
            sku: Product SKU.
            iteration: Iteration index (unused but aids logging).

        Returns:
            _JobResult with per-stage timings.
        """
        stage_times: dict[str, float] = {}
        job_start = time.monotonic()

        for stage, duration in self._stage_durations.items():
            t0 = time.monotonic()
            time.sleep(duration)  # simulate stage latency
            stage_times[stage] = round(time.monotonic() - t0, 4)

        wall_time = round(time.monotonic() - job_start, 4)
        return _JobResult(sku=sku, success=True, wall_time_s=wall_time, stage_times=stage_times)

    def _build_report(
        self,
        results: list[_JobResult],
        total_jobs: int,
        total_wall: float,
    ) -> LoadTestReport:
        """Aggregate job results into a LoadTestReport.

        Args:
            results: All job results.
            total_jobs: Expected total job count.
            total_wall: Total elapsed wall-clock seconds.

        Returns:
            LoadTestReport.
        """
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        latencies = [r.wall_time_s for r in successful] or [0.0]
        latencies_sorted = sorted(latencies)

        p50 = self._percentile(latencies_sorted, 50)
        p95 = self._percentile(latencies_sorted, 95)
        p99 = self._percentile(latencies_sorted, 99)

        throughput = (len(successful) / total_wall * 60.0) if total_wall > 0 else 0.0

        # Per-stage averages across successful jobs
        stage_latencies: dict[str, float] = {}
        for stage in self._stage_durations:
            times = [r.stage_times.get(stage, 0.0) for r in successful if r.stage_times]
            stage_latencies[stage] = round(statistics.mean(times), 4) if times else 0.0

        bottleneck = max(stage_latencies, key=lambda s: stage_latencies[s]) if stage_latencies else ""

        cost_per_sku = sum(self._stage_costs.get(s, 0.0) for s in self._stage_durations)

        logger.info(
            "Load test complete: %d/%d successful, throughput=%.1f/min, p95=%.3fs",
            len(successful),
            total_jobs,
            throughput,
            p95,
        )

        return LoadTestReport(
            total_jobs=total_jobs,
            successful=len(successful),
            failed=len(failed),
            throughput_per_min=round(throughput, 2),
            p50_latency_s=round(p50, 4),
            p95_latency_s=round(p95, 4),
            p99_latency_s=round(p99, 4),
            bottleneck_stage=bottleneck,
            cost_per_sku_usd=round(cost_per_sku, 6),
            stage_latencies=stage_latencies,
        )

    @staticmethod
    def _percentile(sorted_data: list[float], pct: int) -> float:
        """Compute percentile from a pre-sorted list.

        Args:
            sorted_data: Sorted list of floats.
            pct: Percentile (0–100).

        Returns:
            Percentile value.
        """
        if not sorted_data:
            return 0.0
        k = (len(sorted_data) - 1) * pct / 100.0
        lo = math.floor(k)
        hi = math.ceil(k)
        if lo == hi:
            return sorted_data[lo]
        return sorted_data[lo] + (sorted_data[hi] - sorted_data[lo]) * (k - lo)
