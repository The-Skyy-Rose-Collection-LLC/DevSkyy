#!/usr/bin/env python3
"""
DevSkyy Performance Benchmark Script
=====================================

Benchmarks the performance optimizations implemented:
- Embedding cache hit/miss latency
- Parallel vs sequential embedding generation
- Reranking cache performance
- Vector search cache performance
- Parallel file ingestion

Usage:
    python scripts/benchmark_performance.py [--full]

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import argparse
import asyncio
import os
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""

    name: str
    iterations: int
    mean_ms: float
    std_ms: float
    min_ms: float
    max_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    extra: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return (
            f"{self.name}:\n"
            f"  Iterations: {self.iterations}\n"
            f"  Mean: {self.mean_ms:.2f}ms\n"
            f"  Std: {self.std_ms:.2f}ms\n"
            f"  Min: {self.min_ms:.2f}ms\n"
            f"  Max: {self.max_ms:.2f}ms\n"
            f"  P50: {self.p50_ms:.2f}ms\n"
            f"  P95: {self.p95_ms:.2f}ms\n"
            f"  P99: {self.p99_ms:.2f}ms"
        )


def calculate_percentile(data: list[float], percentile: float) -> float:
    """Calculate percentile from sorted data."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    index = int(len(sorted_data) * percentile / 100)
    return sorted_data[min(index, len(sorted_data) - 1)]


def create_result(name: str, times_ms: list[float], extra: dict | None = None) -> BenchmarkResult:
    """Create a BenchmarkResult from timing data."""
    return BenchmarkResult(
        name=name,
        iterations=len(times_ms),
        mean_ms=statistics.mean(times_ms) if times_ms else 0,
        std_ms=statistics.stdev(times_ms) if len(times_ms) > 1 else 0,
        min_ms=min(times_ms) if times_ms else 0,
        max_ms=max(times_ms) if times_ms else 0,
        p50_ms=calculate_percentile(times_ms, 50),
        p95_ms=calculate_percentile(times_ms, 95),
        p99_ms=calculate_percentile(times_ms, 99),
        extra=extra or {},
    )


async def benchmark_embedding_cache(iterations: int = 100) -> list[BenchmarkResult]:
    """Benchmark embedding cache performance."""
    print("\n" + "=" * 60)
    print("Benchmarking Embedding Cache")
    print("=" * 60)

    from orchestration.embedding_engine import EmbeddingCache

    cache = EmbeddingCache(maxsize=1024)

    # Test texts
    test_texts = [f"This is test query number {i} for embedding" for i in range(10)]

    # Benchmark cache misses (first access)
    miss_times = []
    for text in test_texts:
        start = time.perf_counter()
        result = await cache.get(text)
        elapsed = (time.perf_counter() - start) * 1000
        miss_times.append(elapsed)
        assert result is None  # Should be a miss

        # Store a mock embedding
        await cache.put(text, [0.1] * 384)

    # Benchmark cache hits (second access)
    hit_times = []
    for _ in range(iterations):
        for text in test_texts:
            start = time.perf_counter()
            result = await cache.get(text)
            elapsed = (time.perf_counter() - start) * 1000
            hit_times.append(elapsed)
            assert result is not None  # Should be a hit

    # Get stats
    stats = cache.get_stats()

    results = [
        create_result("Embedding Cache Miss", miss_times, {"type": "cold_start"}),
        create_result("Embedding Cache Hit", hit_times, {"type": "warm_cache"}),
    ]

    print(f"\nCache Stats: {stats}")
    for r in results:
        print(f"\n{r}")

    return results


async def benchmark_reranking_cache(iterations: int = 50) -> list[BenchmarkResult]:
    """Benchmark reranking cache performance."""
    print("\n" + "=" * 60)
    print("Benchmarking Reranking Cache")
    print("=" * 60)

    from orchestration.reranker import RerankingCache

    cache = RerankingCache(maxsize=512, ttl_seconds=1800)

    # Test data
    test_query = "What is the best product for summer?"
    test_docs = [f"Document {i} about summer fashion trends" for i in range(10)]
    mock_results = [{"index": i, "score": 0.9 - i * 0.05} for i in range(10)]

    top_n = 5

    # Benchmark cache miss
    miss_times = []
    for i in range(5):
        query = f"{test_query} variant {i}"
        start = time.perf_counter()
        result = await cache.get(query, test_docs, top_n)
        elapsed = (time.perf_counter() - start) * 1000
        miss_times.append(elapsed)
        assert result is None

        # Store results
        await cache.put(query, test_docs, top_n, mock_results)

    # Benchmark cache hits
    hit_times = []
    for _ in range(iterations):
        for i in range(5):
            query = f"{test_query} variant {i}"
            start = time.perf_counter()
            result = await cache.get(query, test_docs, top_n)
            elapsed = (time.perf_counter() - start) * 1000
            hit_times.append(elapsed)
            assert result is not None

    stats = cache.get_stats()

    results = [
        create_result("Reranking Cache Miss", miss_times),
        create_result("Reranking Cache Hit", hit_times),
    ]

    print(f"\nCache Stats: {stats}")
    for r in results:
        print(f"\n{r}")

    return results


async def benchmark_vector_search_cache(iterations: int = 50) -> list[BenchmarkResult]:
    """Benchmark vector search cache performance."""
    print("\n" + "=" * 60)
    print("Benchmarking Vector Search Cache")
    print("=" * 60)

    from orchestration.vector_store import VectorSearchCache

    cache = VectorSearchCache(maxsize=256, ttl_seconds=300)

    # Test embeddings (mock 384-dimensional)
    test_embeddings = [[0.1 * i] * 384 for i in range(10)]
    mock_results = [{"id": f"doc_{j}", "score": 0.9} for j in range(5)]

    # Benchmark cache miss
    miss_times = []
    for i, emb in enumerate(test_embeddings):
        start = time.perf_counter()
        result = await cache.get(emb, top_k=5, filter_metadata=None)
        elapsed = (time.perf_counter() - start) * 1000
        miss_times.append(elapsed)
        assert result is None

        await cache.put(emb, 5, None, mock_results)

    # Benchmark cache hits
    hit_times = []
    for _ in range(iterations):
        for emb in test_embeddings:
            start = time.perf_counter()
            result = await cache.get(emb, top_k=5, filter_metadata=None)
            elapsed = (time.perf_counter() - start) * 1000
            hit_times.append(elapsed)
            assert result is not None

    stats = cache.get_stats()

    results = [
        create_result("Vector Search Cache Miss", miss_times),
        create_result("Vector Search Cache Hit", hit_times),
    ]

    print(f"\nCache Stats: {stats}")
    for r in results:
        print(f"\n{r}")

    return results


async def benchmark_parallel_processing(iterations: int = 5) -> list[BenchmarkResult]:
    """Benchmark parallel vs sequential processing."""
    print("\n" + "=" * 60)
    print("Benchmarking Parallel Processing")
    print("=" * 60)

    # Simulate work with async sleep
    async def simulate_api_call(delay: float = 0.05) -> str:
        await asyncio.sleep(delay)
        return "result"

    num_tasks = 10

    # Sequential benchmark
    sequential_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        for _ in range(num_tasks):
            await simulate_api_call()
        elapsed = (time.perf_counter() - start) * 1000
        sequential_times.append(elapsed)

    # Parallel benchmark
    parallel_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        await asyncio.gather(*[simulate_api_call() for _ in range(num_tasks)])
        elapsed = (time.perf_counter() - start) * 1000
        parallel_times.append(elapsed)

    speedup = statistics.mean(sequential_times) / statistics.mean(parallel_times)

    results = [
        create_result(f"Sequential ({num_tasks} tasks)", sequential_times),
        create_result(f"Parallel ({num_tasks} tasks)", parallel_times, {"speedup": f"{speedup:.1f}x"}),
    ]

    print(f"\nSpeedup: {speedup:.1f}x")
    for r in results:
        print(f"\n{r}")

    return results


async def benchmark_semaphore_limiting(iterations: int = 3) -> list[BenchmarkResult]:
    """Benchmark semaphore-limited parallel processing (like file ingestion)."""
    print("\n" + "=" * 60)
    print("Benchmarking Semaphore-Limited Parallel Processing")
    print("=" * 60)

    async def simulate_file_processing(delay: float = 0.1) -> str:
        await asyncio.sleep(delay)
        return "processed"

    num_files = 20
    max_concurrent = int(os.getenv("MAX_PARALLEL_INGESTION", "5"))

    # Unlimited parallel
    unlimited_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        await asyncio.gather(*[simulate_file_processing() for _ in range(num_files)])
        elapsed = (time.perf_counter() - start) * 1000
        unlimited_times.append(elapsed)

    # Semaphore limited parallel
    semaphore = asyncio.Semaphore(max_concurrent)

    async def limited_process():
        async with semaphore:
            return await simulate_file_processing()

    limited_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        await asyncio.gather(*[limited_process() for _ in range(num_files)])
        elapsed = (time.perf_counter() - start) * 1000
        limited_times.append(elapsed)

    # Sequential for comparison
    sequential_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        for _ in range(num_files):
            await simulate_file_processing()
        elapsed = (time.perf_counter() - start) * 1000
        sequential_times.append(elapsed)

    results = [
        create_result(f"Sequential ({num_files} files)", sequential_times),
        create_result(f"Unlimited Parallel ({num_files} files)", unlimited_times),
        create_result(f"Semaphore Limited (max={max_concurrent})", limited_times),
    ]

    print(f"\nSequential vs Limited Speedup: {statistics.mean(sequential_times) / statistics.mean(limited_times):.1f}x")
    for r in results:
        print(f"\n{r}")

    return results


def print_summary(all_results: list[BenchmarkResult]) -> None:
    """Print benchmark summary."""
    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)

    # Group by category
    cache_results = [r for r in all_results if "Cache" in r.name]
    parallel_results = [r for r in all_results if "Cache" not in r.name]

    print("\n📊 Cache Performance:")
    print("-" * 40)
    for r in cache_results:
        hit_miss = "🟢" if "Hit" in r.name else "🔴"
        print(f"  {hit_miss} {r.name}: {r.mean_ms:.3f}ms (p95: {r.p95_ms:.3f}ms)")

    # Calculate cache speedup
    for cache_type in ["Embedding", "Reranking", "Vector"]:
        miss = next((r for r in cache_results if cache_type in r.name and "Miss" in r.name), None)
        hit = next((r for r in cache_results if cache_type in r.name and "Hit" in r.name), None)
        if miss and hit and hit.mean_ms > 0:
            # Note: Cache lookup is fast, real speedup comes from avoiding computation
            print(f"  ⚡ {cache_type} cache lookup: {hit.mean_ms:.3f}ms avg")

    print("\n🚀 Parallel Processing:")
    print("-" * 40)
    for r in parallel_results:
        speedup = r.extra.get("speedup", "")
        speedup_str = f" ({speedup})" if speedup else ""
        print(f"  {r.name}: {r.mean_ms:.1f}ms{speedup_str}")

    print("\n" + "=" * 60)
    print("✅ Benchmark complete!")
    print("=" * 60)


async def main(full: bool = False) -> None:
    """Run all benchmarks."""
    print("=" * 60)
    print("DevSkyy Performance Benchmark")
    print("=" * 60)
    print(f"Mode: {'Full' if full else 'Quick'}")

    iterations = 100 if full else 20
    all_results: list[BenchmarkResult] = []

    # Run benchmarks
    all_results.extend(await benchmark_embedding_cache(iterations))
    all_results.extend(await benchmark_reranking_cache(iterations // 2))
    all_results.extend(await benchmark_vector_search_cache(iterations // 2))
    all_results.extend(await benchmark_parallel_processing(5 if full else 3))
    all_results.extend(await benchmark_semaphore_limiting(3 if full else 2))

    # Print summary
    print_summary(all_results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DevSkyy Performance Benchmark")
    parser.add_argument("--full", action="store_true", help="Run full benchmark (more iterations)")
    args = parser.parse_args()

    asyncio.run(main(full=args.full))
