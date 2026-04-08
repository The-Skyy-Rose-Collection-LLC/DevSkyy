"""
Tests for CostTracker.

Uses fakeredis to avoid requiring a live Redis instance.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

import fakeredis
import pytest

from skyyrose.elite_studio.queue.cost_tracker import (
    PRICING_PER_1K,
    CostTracker,
    _COST_KEY_PREFIX,
    _TOTAL_COST_SORTED_SET,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_redis_server():
    return fakeredis.FakeServer()


@pytest.fixture()
def fake_redis(fake_redis_server):
    return fakeredis.FakeRedis(server=fake_redis_server, decode_responses=True)


@pytest.fixture()
def tracker(fake_redis):
    ct = CostTracker()
    ct._redis = fake_redis
    return ct


# ---------------------------------------------------------------------------
# record()
# ---------------------------------------------------------------------------


def test_record_stores_token_count(tracker, fake_redis):
    tracker.record("job-1", "gemini", 1000, 0.075)

    val = fake_redis.hget(f"{_COST_KEY_PREFIX}job-1", "gemini_tokens")
    assert float(val) == 1000.0


def test_record_accumulates_total_usd(tracker, fake_redis):
    tracker.record("job-1", "gemini", 1000, 0.075)
    tracker.record("job-1", "openai", 500, 2.50)

    total = float(fake_redis.hget(f"{_COST_KEY_PREFIX}job-1", "total_usd"))
    assert abs(total - 2.575) < 1e-6


def test_record_multiple_providers(tracker, fake_redis):
    tracker.record("job-2", "gemini", 2000, 0.15)
    tracker.record("job-2", "anthropic", 1000, 3.0)
    tracker.record("job-2", "openai", 500, 2.5)

    total = float(fake_redis.hget(f"{_COST_KEY_PREFIX}job-2", "total_usd"))
    assert abs(total - 5.65) < 1e-5


def test_record_sets_ttl(tracker, fake_redis):
    tracker.record("job-ttl", "gemini", 100, 0.01)
    ttl = fake_redis.ttl(f"{_COST_KEY_PREFIX}job-ttl")
    assert ttl > 0


def test_record_adds_to_timeline(tracker, fake_redis):
    tracker.record("job-tl", "openai", 200, 1.0)
    count = fake_redis.zcard(_TOTAL_COST_SORTED_SET)
    assert count >= 1


def test_record_degrades_when_redis_unavailable():
    """record() must not raise when Redis is down."""
    ct = CostTracker()
    ct._redis = None
    # Should log a warning but not raise
    ct.record("job-x", "gemini", 100, 0.01)


# ---------------------------------------------------------------------------
# get_job_cost()
# ---------------------------------------------------------------------------


def test_get_job_cost_returns_accumulated_total(tracker):
    tracker.record("job-gc", "gemini", 1000, 0.5)
    tracker.record("job-gc", "anthropic", 500, 1.5)

    cost = tracker.get_job_cost("job-gc")
    assert abs(cost - 2.0) < 1e-6


def test_get_job_cost_returns_zero_for_unknown_job(tracker):
    assert tracker.get_job_cost("nonexistent-job") == 0.0


def test_get_job_cost_returns_zero_when_redis_unavailable():
    ct = CostTracker()
    ct._redis = None
    assert ct.get_job_cost("job-x") == 0.0


# ---------------------------------------------------------------------------
# get_total_cost()
# ---------------------------------------------------------------------------


def test_get_total_cost_sums_within_window(tracker, fake_redis):
    tracker.record("job-tc1", "gemini", 1000, 1.0)
    tracker.record("job-tc2", "openai", 500, 2.0)

    total = tracker.get_total_cost(since_hours=24)
    assert total >= 3.0


def test_get_total_cost_excludes_old_entries(tracker, fake_redis):
    # Insert a timeline entry with an old timestamp (25 hours ago)
    old_score = (datetime.now(UTC) - timedelta(hours=25)).timestamp()
    fake_redis.zadd(_TOTAL_COST_SORTED_SET, {"old-job:gemini:9.99": old_score})

    # Only add a fresh entry
    tracker.record("job-fresh", "anthropic", 100, 0.30)

    total = tracker.get_total_cost(since_hours=24)
    assert total < 9.99 + 0.30 + 0.01  # old entry must be excluded


def test_get_total_cost_returns_zero_when_redis_unavailable():
    ct = CostTracker()
    ct._redis = None
    assert ct.get_total_cost() == 0.0


def test_get_total_cost_empty_timeline_returns_zero(tracker):
    assert tracker.get_total_cost(since_hours=1) == 0.0


# ---------------------------------------------------------------------------
# estimate_cost() — static helper
# ---------------------------------------------------------------------------


def test_estimate_cost_gemini():
    cost = CostTracker.estimate_cost("gemini", 1000)
    assert abs(cost - PRICING_PER_1K["gemini"]) < 1e-9


def test_estimate_cost_openai():
    cost = CostTracker.estimate_cost("openai", 1000)
    assert abs(cost - PRICING_PER_1K["openai"]) < 1e-9


def test_estimate_cost_anthropic():
    cost = CostTracker.estimate_cost("anthropic", 1000)
    assert abs(cost - PRICING_PER_1K["anthropic"]) < 1e-9


def test_estimate_cost_unknown_provider_returns_zero():
    cost = CostTracker.estimate_cost("unknown_provider", 1000)
    assert cost == 0.0


def test_estimate_cost_zero_tokens():
    assert CostTracker.estimate_cost("gemini", 0) == 0.0
