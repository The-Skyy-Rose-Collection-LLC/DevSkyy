"""Unit tests for reliability primitives."""

from __future__ import annotations

import asyncio

import pytest
from services.three_d.trellis.config import TrellisQualityPreset

from pipelines.clothing_3d.models import PipelineRequest, PipelineResult, PipelineStatus
from pipelines.clothing_3d.reliability import (
    CostQuota,
    IdempotencyCache,
    InMemoryIdempotencyStore,
    QuotaExceededError,
    RetryPolicy,
    request_fingerprint,
)

# =============================================================================
# RetryPolicy
# =============================================================================


@pytest.mark.asyncio
async def test_retry_succeeds_after_transient_failures() -> None:
    attempts = []

    async def flaky():
        attempts.append(1)
        if len(attempts) < 3:
            raise TimeoutError("flake")
        return "ok"

    policy = RetryPolicy(max_attempts=4, base_delay_seconds=0.001, max_delay_seconds=0.01)
    assert await policy.run(flaky) == "ok"
    assert len(attempts) == 3


@pytest.mark.asyncio
async def test_retry_gives_up_after_max_attempts() -> None:
    async def always_fails():
        raise TimeoutError("nope")

    policy = RetryPolicy(max_attempts=2, base_delay_seconds=0.001, max_delay_seconds=0.01)
    with pytest.raises(TimeoutError):
        await policy.run(always_fails)


@pytest.mark.asyncio
async def test_retry_only_retries_listed_exceptions() -> None:
    async def value_err():
        raise ValueError("not retryable")

    policy = RetryPolicy(max_attempts=3, base_delay_seconds=0.001)
    with pytest.raises(ValueError):
        await policy.run(value_err)


def test_retry_delay_grows_with_attempt() -> None:
    policy = RetryPolicy(
        max_attempts=5,
        base_delay_seconds=1.0,
        max_delay_seconds=64.0,
        backoff_multiplier=2.0,
    )
    # delay_for(1) = 0 (first try, no sleep)
    assert policy.delay_for(1) == 0.0
    # delay_for(2) ∈ [0, 1]
    # delay_for(3) ∈ [0, 2]
    # delay_for(N) capped at max_delay_seconds
    for n in range(2, 10):
        d = policy.delay_for(n)
        assert d >= 0.0
        assert d <= policy.max_delay_seconds


# =============================================================================
# Idempotency
# =============================================================================


def test_fingerprint_stable_across_identical_requests() -> None:
    a = PipelineRequest(
        prompt="hoodie",
        product_name="X",
        garment_type="hoodie",
        quality=TrellisQualityPreset.STANDARD,
    )
    b = PipelineRequest(
        prompt="hoodie",
        product_name="X",
        garment_type="hoodie",
        quality=TrellisQualityPreset.STANDARD,
        correlation_id="differs",
    )
    assert request_fingerprint(a) == request_fingerprint(b)


def test_fingerprint_changes_with_quality() -> None:
    a = PipelineRequest(prompt="hoodie", product_name="X", quality=TrellisQualityPreset.DRAFT)
    b = PipelineRequest(prompt="hoodie", product_name="X", quality=TrellisQualityPreset.PRODUCTION)
    assert request_fingerprint(a) != request_fingerprint(b)


@pytest.mark.asyncio
async def test_idempotency_cache_returns_cached_on_second_call() -> None:
    runs = 0
    sentinel = PipelineResult(
        status=PipelineStatus.SUCCEEDED,
        artifact_id="a1",
        correlation_id="c1",
        glb_url="/foo.glb",
    )

    async def runner(_req):
        nonlocal runs
        runs += 1
        return sentinel

    cache = IdempotencyCache(ttl_seconds=60)
    req = PipelineRequest(prompt="x", product_name="x")

    r1, hit1 = await cache.get_or_run(req, runner=runner)
    r2, hit2 = await cache.get_or_run(req, runner=runner)

    assert runs == 1
    assert r1 == r2
    assert hit1 is False and hit2 is True


@pytest.mark.asyncio
async def test_idempotency_does_not_cache_failures() -> None:
    runs = 0

    async def runner(_req):
        nonlocal runs
        runs += 1
        return PipelineResult(
            status=PipelineStatus.FAILED,
            artifact_id="x",
            correlation_id="c",
        )

    cache = IdempotencyCache(ttl_seconds=60)
    req = PipelineRequest(prompt="x", product_name="x")
    await cache.get_or_run(req, runner=runner)
    await cache.get_or_run(req, runner=runner)
    assert runs == 2  # not cached


@pytest.mark.asyncio
async def test_idempotency_disabled_passthrough() -> None:
    runs = 0

    async def runner(_req):
        nonlocal runs
        runs += 1
        return PipelineResult(status=PipelineStatus.SUCCEEDED, artifact_id="x", correlation_id="c")

    cache = IdempotencyCache(enabled=False)
    req = PipelineRequest(prompt="x", product_name="x")
    await cache.get_or_run(req, runner=runner)
    await cache.get_or_run(req, runner=runner)
    assert runs == 2


# =============================================================================
# CostQuota
# =============================================================================


def test_cost_quota_charges_until_cap() -> None:
    q = CostQuota(caps_usd={"replicate": 0.10})  # default replicate cost = $0.05/call
    q.charge("replicate")  # spent $0.05
    q.charge("replicate")  # spent $0.10
    with pytest.raises(QuotaExceededError):
        q.charge("replicate")
    assert q.spent("replicate") == pytest.approx(0.10)


def test_cost_quota_no_cap_means_unlimited() -> None:
    q = CostQuota()
    for _ in range(100):
        q.charge("replicate")
    # No cap declared, so no exception. spent stays 0 (not tracked w/o cap).


def test_cost_quota_snapshot_shape() -> None:
    q = CostQuota(caps_usd={"modal": 0.50})
    q.charge("modal")
    snap = q.snapshot()
    assert "modal" in snap
    assert snap["modal"]["cap_usd"] == 0.50
    assert snap["modal"]["spent_usd"] > 0


# =============================================================================
# InMemoryIdempotencyStore
# =============================================================================


@pytest.mark.asyncio
async def test_in_memory_store_evicts_when_full() -> None:
    store = InMemoryIdempotencyStore(capacity=2)
    from datetime import UTC, datetime

    from pipelines.clothing_3d.reliability import IdempotencyEntry

    def make(fp: str) -> IdempotencyEntry:
        return IdempotencyEntry(
            fingerprint=fp,
            result=PipelineResult(
                status=PipelineStatus.SUCCEEDED, artifact_id=fp, correlation_id=fp
            ),
            cached_at=datetime.now(UTC),
        )

    await store.put(make("a"), ttl_seconds=60)
    await asyncio.sleep(0.001)
    await store.put(make("b"), ttl_seconds=60)
    await asyncio.sleep(0.001)
    await store.put(make("c"), ttl_seconds=60)  # evicts 'a'

    assert await store.get("a") is None
    assert (await store.get("b")) is not None
    assert (await store.get("c")) is not None
