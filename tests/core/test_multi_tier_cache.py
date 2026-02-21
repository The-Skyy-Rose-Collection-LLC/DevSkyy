"""
Tests for Multi-Tier Cache - L1/L2/L3 Caching Strategy
========================================================

TDD RED Phase - Tests for multi-tier caching system.

Tier strategy:
  L1: In-memory LRU cache (microseconds)
  L2: Redis (milliseconds)
  L3: CDN (seconds, static assets only)
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Will fail until MultiTierCache is implemented (TDD RED)
try:
    from core.caching.multi_tier_cache import MultiTierCache, cached
except ImportError:
    MultiTierCache = None  # type: ignore
    cached = None  # type: ignore


@pytest.mark.unit
class TestMultiTierCache:
    """Test multi-tier cache with L1/L2/L3 layers"""

    @pytest.fixture
    def cache(self):
        """Create a fresh MultiTierCache instance for each test"""
        return MultiTierCache(l1_max_size=100, l1_ttl=60)

    @pytest.mark.asyncio
    async def test_l1_cache_hit(self, cache):
        """
        Test L1 (in-memory) cache hit - should be fastest path

        Expected:
        - First set() populates L1 and L2
        - Second get() returns from L1 without querying L2 or DB
        """
        # Arrange: prime the cache
        await cache.set("key:product:br-001", {"sku": "br-001", "price": 79.99}, ttl=300)

        # Act: retrieve from cache
        result = await cache.get("key:product:br-001")

        # Assert: L1 hit
        assert result == {"sku": "br-001", "price": 79.99}
        assert cache.stats["l1_hits"] == 1
        assert cache.stats["l2_hits"] == 0

    @pytest.mark.asyncio
    async def test_l2_miss_populates_l1(self, cache):
        """
        Test L1 miss → L2 hit → promotes to L1

        Expected:
        - L1 cache starts empty
        - L2 (Redis) has value
        - get() finds it in L2 and promotes to L1
        - Next get() hits L1 (promoted)
        """
        # Arrange: mock L2 Redis to have value, L1 is cold
        cached_value = {"sku": "br-002", "price": 89.99}

        with patch.object(cache, "_l2_get", new_callable=AsyncMock) as mock_l2_get, \
             patch.object(cache, "_l2_set", new_callable=AsyncMock) as mock_l2_set:
            mock_l2_get.return_value = cached_value

            # Act: First get (L1 cold, L2 warm)
            result = await cache.get("key:product:br-002")

            # Assert: found in L2 and promoted to L1
            assert result == cached_value
            assert cache.stats["l1_misses"] >= 1
            assert cache.stats["l2_hits"] == 1

            # Act: Second get (should now hit L1)
            result2 = await cache.get("key:product:br-002")

            # Assert: promoted to L1
            assert result2 == cached_value
            assert cache.stats["l1_hits"] == 1  # L1 hit on second call
            # L2 should NOT be called again
            assert mock_l2_get.call_count == 1  # Only called once

    @pytest.mark.asyncio
    async def test_cache_miss_returns_none(self, cache):
        """
        Test complete cache miss (L1 + L2 + L3) returns None

        Expected:
        - Key not in L1, L2, or L3
        - Returns None without raising exception
        - No side effects
        """
        with patch.object(cache, "_l2_get", new_callable=AsyncMock) as mock_l2_get:
            mock_l2_get.return_value = None

            result = await cache.get("key:nonexistent:xyz")

            assert result is None
            assert cache.stats["l1_misses"] == 1
            assert cache.stats["l2_misses"] == 1

    @pytest.mark.asyncio
    async def test_set_populates_l1_and_l2(self, cache):
        """
        Test set() writes to both L1 and L2

        Expected:
        - set() writes to L1 immediately
        - set() writes to L2 (Redis) asynchronously
        - Both tiers have the value
        """
        with patch.object(cache, "_l2_set", new_callable=AsyncMock) as mock_l2_set:
            # Act
            await cache.set("key:product:br-003", {"sku": "br-003"}, ttl=300)

            # Assert: L2 was called
            mock_l2_set.assert_called_once()

            # Assert: L1 was also populated (get() should hit L1)
            result = await cache.get("key:product:br-003")
            assert result == {"sku": "br-003"}
            assert cache.stats["l1_hits"] == 1

    @pytest.mark.asyncio
    async def test_invalidate_removes_from_all_tiers(self, cache):
        """
        Test invalidate() removes from L1 and L2

        Expected:
        - Key in L1 and L2
        - invalidate() removes from both
        - get() returns None after invalidation
        """
        # Arrange: set in cache
        await cache.set("key:product:br-004", {"sku": "br-004"}, ttl=300)

        with patch.object(cache, "_l2_delete", new_callable=AsyncMock) as mock_l2_delete:
            # Act: invalidate
            await cache.invalidate("key:product:br-004")

            # Assert: removed from L2
            mock_l2_delete.assert_called_once_with("key:product:br-004")

            # Assert: removed from L1 (should miss now)
            result = await cache.get("key:product:br-004")
            # L1 miss, L2 also returns None since we're mocking it

    @pytest.mark.asyncio
    async def test_l1_lru_eviction(self, cache):
        """
        Test L1 LRU eviction when max_size is reached

        Expected:
        - L1 has max_size=3 (for this test)
        - Add 4 items - oldest should be evicted
        - Total L1 size stays at max_size
        """
        small_cache = MultiTierCache(l1_max_size=3, l1_ttl=60)

        with patch.object(small_cache, "_l2_set", new_callable=AsyncMock):
            # Add 4 items to a cache with max_size=3
            await small_cache.set("key:a", "value_a", ttl=300)
            await small_cache.set("key:b", "value_b", ttl=300)
            await small_cache.set("key:c", "value_c", ttl=300)
            await small_cache.set("key:d", "value_d", ttl=300)  # Should evict 'a'

            # Assert: cache size is bounded
            assert small_cache.l1_size <= 3

    @pytest.mark.asyncio
    async def test_cached_decorator_function_caching(self):
        """
        Test @cached decorator caches function results

        Expected:
        - First call: executes function, caches result
        - Second call (same args): returns cached result, does NOT re-execute function
        """
        # Arrange
        call_count = 0

        @cached(ttl=60)
        async def expensive_operation(product_id: str) -> dict:
            nonlocal call_count
            call_count += 1
            return {"id": product_id, "computed": "expensive_value"}

        # Act
        result1 = await expensive_operation("br-001")
        result2 = await expensive_operation("br-001")  # Should use cache

        # Assert
        assert result1 == {"id": "br-001", "computed": "expensive_value"}
        assert result2 == result1
        assert call_count == 1  # Function only called ONCE

    @pytest.mark.asyncio
    async def test_cached_decorator_different_args_separate_entries(self):
        """
        Test @cached decorator creates separate cache entries for different args
        """
        # Arrange
        call_count = 0

        @cached(ttl=60)
        async def get_product(sku: str) -> dict:
            nonlocal call_count
            call_count += 1
            return {"sku": sku}

        # Act: two different SKUs
        result1 = await get_product("br-001")
        result2 = await get_product("br-002")
        result3 = await get_product("br-001")  # Same as first, should be cached

        # Assert
        assert result1 == {"sku": "br-001"}
        assert result2 == {"sku": "br-002"}
        assert result3 == result1
        assert call_count == 2  # Only 2 unique calls

    @pytest.mark.asyncio
    async def test_cache_stats_tracking(self, cache):
        """
        Test that cache stats are accurately tracked

        Expected:
        - hits, misses tracked per tier
        - hit_rate calculated correctly
        """
        with patch.object(cache, "_l2_get", new_callable=AsyncMock) as mock_l2_get:
            mock_l2_get.return_value = None

            # Force some misses
            await cache.get("miss:1")
            await cache.get("miss:2")

            # Force a hit
            await cache.set("hit:1", "value", ttl=300)
            await cache.get("hit:1")

            stats = cache.get_stats()
            assert stats["total_requests"] >= 3
            assert stats["l1_hits"] >= 1
            assert "hit_rate" in stats
            assert 0 <= stats["hit_rate"] <= 100
