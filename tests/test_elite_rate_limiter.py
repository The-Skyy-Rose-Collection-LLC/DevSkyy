"""
Tests for ProviderRateLimiter.

Uses fakeredis to simulate Redis sorted set operations.
"""

from __future__ import annotations

from datetime import UTC, datetime

import fakeredis
import pytest

from skyyrose.elite_studio.queue.rate_limiter import (
    ProviderRateLimiter,
    RateLimitExceeded,
)

_WINDOW_SECONDS = ProviderRateLimiter._WINDOW_SECONDS


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
def limiter(fake_redis):
    rl = ProviderRateLimiter()
    rl._redis = fake_redis
    return rl


# ---------------------------------------------------------------------------
# acquire() — basic behaviour
# ---------------------------------------------------------------------------


def test_acquire_returns_true_for_known_provider(limiter):
    assert limiter.acquire("gemini") is True


def test_acquire_adds_entry_to_sorted_set(limiter, fake_redis):
    limiter.acquire("gemini")
    key = f"{ProviderRateLimiter._KEY_PREFIX}gemini"
    assert fake_redis.zcard(key) == 1


def test_acquire_multiple_slots_within_limit(limiter):
    for _ in range(10):
        assert limiter.acquire("openai") is True


def test_acquire_unknown_provider_allows_by_default(limiter):
    assert limiter.acquire("unknown_provider") is True


def test_acquire_degrades_when_redis_unavailable():
    """acquire() must return True (allow) when Redis is down."""
    rl = ProviderRateLimiter()
    rl._redis = None
    assert rl.acquire("gemini") is True


# ---------------------------------------------------------------------------
# Rate limit enforcement
# ---------------------------------------------------------------------------


def test_acquire_blocks_when_limit_reached(fake_redis):
    """When the window is full, acquire() with a short timeout must raise."""
    rl = ProviderRateLimiter()
    rl._redis = fake_redis

    # Fill the gemini window (limit=60) with 60 fake entries
    key = f"{ProviderRateLimiter._KEY_PREFIX}gemini"
    now = datetime.now(UTC).timestamp()
    members = {f"fake-{i}": now for i in range(60)}
    fake_redis.zadd(key, members)

    with pytest.raises(RateLimitExceeded) as exc_info:
        rl.acquire("gemini", timeout=0.1)

    assert exc_info.value.provider == "gemini"


def test_rate_limit_exceeded_message_contains_provider():
    exc = RateLimitExceeded(provider="anthropic", timeout=30.0)
    assert "anthropic" in str(exc)
    assert exc.provider == "anthropic"


def test_acquire_succeeds_after_window_expires(fake_redis):
    """Old entries (> 60s) are pruned — acquire should succeed."""
    rl = ProviderRateLimiter()
    rl._redis = fake_redis

    key = f"{ProviderRateLimiter._KEY_PREFIX}gemini"
    # Insert 60 entries with timestamps 2 minutes ago (expired)
    old_ts = datetime.now(UTC).timestamp() - 120
    members = {f"old-{i}": old_ts for i in range(60)}
    fake_redis.zadd(key, members)

    # Should succeed because all entries are outside the sliding window
    result = rl.acquire("gemini", timeout=1.0)
    assert result is True


# ---------------------------------------------------------------------------
# release()
# ---------------------------------------------------------------------------


def test_release_removes_oldest_entry(limiter, fake_redis):
    key = f"{ProviderRateLimiter._KEY_PREFIX}gemini"
    now = datetime.now(UTC).timestamp()
    fake_redis.zadd(key, {"entry-old": now - 10, "entry-new": now})

    limiter.release("gemini")

    remaining = fake_redis.zrange(key, 0, -1)
    assert "entry-old" not in remaining
    assert "entry-new" in remaining


def test_release_on_empty_key_does_not_raise(limiter):
    """release() on a provider with no entries must be a no-op."""
    limiter.release("anthropic")  # Should not raise


def test_release_degrades_when_redis_unavailable():
    rl = ProviderRateLimiter()
    rl._redis = None
    rl.release("gemini")  # Must not raise


# ---------------------------------------------------------------------------
# Sliding window pruning
# ---------------------------------------------------------------------------


def test_acquire_prunes_expired_entries(limiter, fake_redis):
    key = f"{ProviderRateLimiter._KEY_PREFIX}anthropic"
    old_ts = datetime.now(UTC).timestamp() - (_WINDOW_SECONDS + 5)
    fake_redis.zadd(key, {"stale-entry": old_ts})

    limiter.acquire("anthropic")

    remaining = fake_redis.zrange(key, 0, -1, withscores=True)
    # stale-entry should have been removed by the pruning step
    member_names = [m for m, _ in remaining]
    assert "stale-entry" not in member_names


# ---------------------------------------------------------------------------
# LIMITS constant
# ---------------------------------------------------------------------------


def test_limits_constant_contains_all_providers():
    limits = ProviderRateLimiter.LIMITS
    assert "gemini" in limits
    assert "openai" in limits
    assert "anthropic" in limits


def test_limits_are_positive_integers():
    for provider, limit in ProviderRateLimiter.LIMITS.items():
        assert isinstance(limit, int), f"{provider} limit must be int"
        assert limit > 0, f"{provider} limit must be positive"
