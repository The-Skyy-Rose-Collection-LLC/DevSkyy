"""
Integration Tests: GraphQL Resolver + Multi-Tier Cache + DataLoader
====================================================================

Verifies that the three layers work correctly together:

  GraphQL schema.execute()
       ↓
  products() resolver (schema.py)
       ↓
  get_products_from_db() decorated with @cached (product_resolver.py)
       ↓
  MultiTierCache L1 → L2 → DB
       ↓
  DatabaseManager (mocked at this boundary)

Distinct from unit tests (test_graphql_products.py) which mock
get_products_from_db entirely.  These tests let the cache run and
verify the interaction — catching bugs like mismatched key lengths
between cache.set() and cache_invalidate().

DataLoader tests follow the same pattern: only _batch_load_fn is
replaced; the DataLoader's dedup and scheduling logic runs for real.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from api.graphql.schema import schema
from api.graphql.resolvers.product_resolver import get_products_from_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_product(
    sku: str,
    collection: str = "black-rose",
    price: float = 79.99,
) -> MagicMock:
    """Create a mock Product ORM object with all required attributes."""
    p = MagicMock()
    p.id = f"id-{sku}"
    p.sku = sku
    p.name = f"Product {sku}"
    p.price = price
    p.collection = collection
    p.description = "Luxury streetwear"
    p.compare_price = None
    p.is_active = True
    p.images_json = "[]"
    return p


def _make_mock_db(products: list) -> tuple[MagicMock, AsyncMock]:
    """
    Build a mocked DatabaseManager that returns `products` from session.execute().

    Returns (mock_db_instance, mock_session) so callers can inspect call counts.
    """
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = products

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    mock_db = MagicMock()
    mock_db.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_db.session.return_value.__aexit__ = AsyncMock(return_value=False)

    return mock_db, mock_session


# ---------------------------------------------------------------------------
# Tests: products() resolver + @cached decorator
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
class TestGraphQLCacheIntegration:
    """
    Integration tests: GraphQL resolver ↔ Multi-Tier Cache.

    We patch only at the database boundary (DatabaseManager), leaving the
    @cached decorator and MultiTierCache fully exercised.  Failing here
    but passing in unit tests means the cache pipeline is broken.
    """

    def setup_method(self) -> None:
        """Reset the per-function L1 cache before each test to prevent state leakage."""
        get_products_from_db.cache._l1.clear()  # type: ignore[attr-defined]
        for key in get_products_from_db.cache.stats:  # type: ignore[attr-defined]
            get_products_from_db.cache.stats[key] = 0  # type: ignore[attr-defined]

    async def test_repeated_identical_query_hits_l1_not_db(self) -> None:
        """
        Executing the same products() query twice should call the DB only once.

        The @cached decorator memoises on (collection=None, limit=10, offset=0).
        The second call is served from L1 (TTLCache) without touching DatabaseManager.
        """
        mock_products = [_make_mock_product("br-001"), _make_mock_product("br-002")]
        mock_db, mock_session = _make_mock_db(mock_products)

        with patch(
            "api.graphql.resolvers.product_resolver.DatabaseManager",
            return_value=mock_db,
        ):
            query = "{ products(limit: 10) { sku name } }"

            result1 = await schema.execute(query)
            result2 = await schema.execute(query)

            assert result1.errors is None, result1.errors
            assert result2.errors is None, result2.errors
            assert len(result1.data["products"]) == 2
            assert len(result2.data["products"]) == 2

            # DB must be called exactly once despite two GraphQL executions
            assert mock_session.execute.call_count == 1, (
                "Expected DB to be called once — second query should hit L1 cache"
            )
            # Cache stats confirm L1 hit on the second call
            assert get_products_from_db.cache.stats["l1_hits"] >= 1  # type: ignore[attr-defined]

    async def test_different_collection_filters_produce_separate_cache_entries(self) -> None:
        """
        products(collection: "black-rose") and products(collection: "love-hurts")
        must not share a cache entry — they return different product subsets.
        Both must reach the DB; a third call with a repeated collection is cached.
        """
        br_products = [_make_mock_product("br-001", "black-rose")]
        lh_products = [_make_mock_product("lh-001", "love-hurts")]
        db_call_count = 0

        async def counting_execute(_q: object) -> MagicMock:
            nonlocal db_call_count
            db_call_count += 1
            result = MagicMock()
            result.scalars.return_value.all.return_value = (
                br_products if db_call_count == 1 else lh_products
            )
            return result

        mock_session = AsyncMock()
        mock_session.execute = counting_execute
        mock_db = MagicMock()
        mock_db.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.session.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "api.graphql.resolvers.product_resolver.DatabaseManager",
            return_value=mock_db,
        ):
            br_result = await schema.execute(
                '{ products(collection: "black-rose") { sku collection } }'
            )
            lh_result = await schema.execute(
                '{ products(collection: "love-hurts") { sku collection } }'
            )

            assert br_result.errors is None
            assert lh_result.errors is None
            # Two distinct cache keys → two DB calls
            assert db_call_count == 2

            # Third call repeats black-rose — should hit cache, not DB
            br_cached = await schema.execute(
                '{ products(collection: "black-rose") { sku collection } }'
            )
            assert br_cached.errors is None
            assert db_call_count == 2, (
                "Third query (repeated collection) should be served from cache, not DB"
            )

    async def test_offset_pagination_creates_distinct_cache_entries(self) -> None:
        """
        products(offset: 0) and products(offset: 20) are different pages.
        They must not collide in the cache even when all other params are equal.
        """
        page1 = [_make_mock_product("br-001")]
        page2 = [_make_mock_product("br-008")]
        db_call_count = 0

        async def counting_execute(_q: object) -> MagicMock:
            nonlocal db_call_count
            db_call_count += 1
            result = MagicMock()
            result.scalars.return_value.all.return_value = (
                page1 if db_call_count == 1 else page2
            )
            return result

        mock_session = AsyncMock()
        mock_session.execute = counting_execute
        mock_db = MagicMock()
        mock_db.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.session.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "api.graphql.resolvers.product_resolver.DatabaseManager",
            return_value=mock_db,
        ):
            r1 = await schema.execute("{ products(limit: 10, offset: 0) { sku } }")
            r2 = await schema.execute("{ products(limit: 10, offset: 20) { sku } }")

            assert r1.errors is None
            assert r2.errors is None
            # Different offsets → different cache keys → two DB calls
            assert db_call_count == 2

    async def test_cache_stats_reflect_hit_miss_pattern(self) -> None:
        """
        After two identical queries, stats must show 1 miss + 1 hit.
        The hit_rate should be > 0, confirming cache is working.
        """
        mock_products = [_make_mock_product("br-001")]
        mock_db, _ = _make_mock_db(mock_products)

        with patch(
            "api.graphql.resolvers.product_resolver.DatabaseManager",
            return_value=mock_db,
        ):
            query = "{ products(limit: 5, offset: 0) { sku } }"
            await schema.execute(query)  # Miss
            await schema.execute(query)  # Hit

            stats = get_products_from_db.cache.get_stats()  # type: ignore[attr-defined]
            assert stats["l1_hits"] >= 1
            assert stats["l1_misses"] >= 1
            assert stats["hit_rate"] > 0, "Expected positive L1 hit rate"

    async def test_limit_clamping_shares_cache_entry(self) -> None:
        """
        products(limit: 999) is clamped to 100 by the resolver before calling
        get_products_from_db(limit=100). products(limit: 100) calls the same function
        with the same args — they share one cache entry.
        """
        mock_products = [_make_mock_product("br-001")]
        mock_db, mock_session = _make_mock_db(mock_products)

        with patch(
            "api.graphql.resolvers.product_resolver.DatabaseManager",
            return_value=mock_db,
        ):
            # Over-limit call — clamped to 100 inside the resolver
            r1 = await schema.execute("{ products(limit: 999) { sku } }")
            # Exact same effective limit — should use cache
            r2 = await schema.execute("{ products(limit: 100) { sku } }")

            assert r1.errors is None
            assert r2.errors is None
            # Both produce get_products_from_db(limit=100) — same cache key
            assert mock_session.execute.call_count == 1, (
                "products(limit: 999) and products(limit: 100) should share a cache entry"
            )

    async def test_cache_invalidate_uses_matching_key_length(self) -> None:
        """
        cache_invalidate() must build the cache key with the same 32-hex-char
        hash as the main wrapper so that invalidation actually removes the entry.

        This was a bug where cache_invalidate used [:16] while set() used [:32],
        causing invalidations to silently no-op (wrong key, nothing removed).
        """
        mock_products = [_make_mock_product("br-001")]
        mock_db, mock_session = _make_mock_db(mock_products)

        with patch(
            "api.graphql.resolvers.product_resolver.DatabaseManager",
            return_value=mock_db,
        ):
            query = "{ products(limit: 10) { sku } }"

            # Prime the cache (1 DB call)
            await schema.execute(query)
            assert mock_session.execute.call_count == 1

            # Invalidate using the exposed cache_invalidate lambda
            # (same call signature as get_products_from_db itself)
            await get_products_from_db.cache_invalidate(  # type: ignore[attr-defined]
                collection=None, limit=10, offset=0
            )

            # After invalidation, same query must hit DB again (not cache)
            await schema.execute(query)
            assert mock_session.execute.call_count == 2, (
                "After cache_invalidate(), query must re-hit the DB. "
                "If still 1, the invalidation used the wrong key length."
            )


# ---------------------------------------------------------------------------
# Tests: DataLoader N+1 prevention
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
class TestDataLoaderBatching:
    """
    Integration tests: DataLoader batches concurrent product(sku: ...) lookups.

    Only _batch_load_fn is replaced; the DataLoader's internal dedup,
    scheduling, and request-level caching all run for real.
    """

    async def test_parallel_product_aliases_batch_into_single_db_call(self) -> None:
        """
        A GraphQL query with two aliased product() fields should trigger exactly
        one _batch_load_fn call containing both SKUs — not two separate calls.

        Strawberry resolves parallel fields concurrently; the DataLoader collects
        all pending load() requests within the same event-loop tick, then calls
        batch_load_fn once with all keys.
        """
        br001 = _make_mock_product("br-001")
        br002 = _make_mock_product("br-002")
        product_map = {"br-001": br001, "br-002": br002}

        batch_calls: list[list[str]] = []

        async def fake_batch_load(skus: list[str]) -> list:
            batch_calls.append(list(skus))
            return [product_map.get(sku) for sku in skus]

        from api.graphql.dataloaders.product_loader import ProductDataLoader

        loader = ProductDataLoader()
        loader.batch_load_fn = fake_batch_load  # type: ignore[assignment]

        query = """
        {
            a: product(sku: "br-001") { sku name }
            b: product(sku: "br-002") { sku name }
        }
        """

        result = await schema.execute(query, context_value={"product_loader": loader})

        assert result.errors is None, result.errors
        assert result.data["a"]["sku"] == "br-001"
        assert result.data["b"]["sku"] == "br-002"
        # DataLoader must have batched both SKUs into ONE call
        assert len(batch_calls) == 1, (
            f"Expected 1 batch call, got {len(batch_calls)}. "
            "DataLoader N+1 prevention is broken."
        )
        assert set(batch_calls[0]) == {"br-001", "br-002"}

    async def test_duplicate_sku_in_query_deduplicated_by_dataloader(self) -> None:
        """
        When the same SKU appears twice in one execution (via aliases),
        the DataLoader's request-level cache deduplicates it: only one load()
        reaches _batch_load_fn, preventing duplicate DB lookups.
        """
        br001 = _make_mock_product("br-001")
        batch_calls: list[list[str]] = []

        async def fake_batch_load(skus: list[str]) -> list:
            batch_calls.append(list(skus))
            return [br001 for _ in skus]

        from api.graphql.dataloaders.product_loader import ProductDataLoader

        loader = ProductDataLoader()
        loader.batch_load_fn = fake_batch_load  # type: ignore[assignment]

        query = """
        {
            first:  product(sku: "br-001") { sku }
            second: product(sku: "br-001") { sku }
        }
        """

        result = await schema.execute(query, context_value={"product_loader": loader})

        assert result.errors is None, result.errors
        assert result.data["first"]["sku"] == "br-001"
        assert result.data["second"]["sku"] == "br-001"
        # One batch call, with "br-001" appearing only once (DataLoader dedup)
        assert len(batch_calls) == 1
        assert batch_calls[0].count("br-001") == 1, (
            "DataLoader should deduplicate identical keys within one request"
        )

    async def test_missing_product_sku_returns_null_not_error(self) -> None:
        """
        product(sku: "xx-999") for a non-existent product should resolve to null.
        The DataLoader must handle None gracefully — no exception, no GraphQL error.
        """

        async def fake_batch_load(skus: list[str]) -> list:
            return [None for _ in skus]  # All lookups return None

        from api.graphql.dataloaders.product_loader import ProductDataLoader

        loader = ProductDataLoader()
        loader.batch_load_fn = fake_batch_load  # type: ignore[assignment]

        result = await schema.execute(
            '{ product(sku: "xx-999") { sku } }',
            context_value={"product_loader": loader},
        )

        assert result.errors is None, result.errors
        assert result.data["product"] is None

    async def test_mixed_found_and_missing_products_in_one_query(self) -> None:
        """
        A batch containing one found + one missing SKU must return results
        in the same order as the requested SKUs, with None for missing entries.

        This validates the ordering contract of _batch_load_fn (critical for
        DataLoader correctness — order mismatch would return wrong product data).
        """
        br001 = _make_mock_product("br-001")
        product_map = {"br-001": br001}

        async def fake_batch_load(skus: list[str]) -> list:
            return [product_map.get(sku) for sku in skus]

        from api.graphql.dataloaders.product_loader import ProductDataLoader

        loader = ProductDataLoader()
        loader.batch_load_fn = fake_batch_load  # type: ignore[assignment]

        query = """
        {
            real:    product(sku: "br-001") { sku }
            missing: product(sku: "xx-999") { sku }
        }
        """

        result = await schema.execute(query, context_value={"product_loader": loader})

        assert result.errors is None, result.errors
        assert result.data["real"]["sku"] == "br-001"
        assert result.data["missing"] is None
