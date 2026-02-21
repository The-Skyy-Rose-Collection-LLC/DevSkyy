"""
Tests for Real-Time Analytics StreamProcessor
===============================================

Tests event dispatching and aggregation logic directly by calling
process_event() — no Kafka connection required.
"""

import pytest

from analytics.stream_processor import AnalyticsState, StreamProcessor


def _make_processor() -> StreamProcessor:
    return StreamProcessor(bootstrap_servers="localhost:9092")


@pytest.mark.unit
@pytest.mark.asyncio
class TestStreamProcessorEventDispatch:
    """Tests for event routing and processing"""

    async def test_page_view_increments_counter(self):
        """
        page_view events increment the per-page counter in state.
        """
        p = _make_processor()
        await p.process_event({"type": "page_view", "page": "/homepage"})
        await p.process_event({"type": "page_view", "page": "/homepage"})
        await p.process_event({"type": "page_view", "page": "/collections/black-rose"})

        stats = p.get_stats()
        assert stats["page_views"]["/homepage"] == 2
        assert stats["page_views"]["/collections/black-rose"] == 1
        assert stats["events_processed"] == 3

    async def test_product_interaction_tracks_by_type(self):
        """
        product_interaction events create nested counters:
        product_interest[product_id][interaction_type]
        """
        p = _make_processor()
        await p.process_event({"type": "product_interaction", "product_id": "br-001", "interaction_type": "view"})
        await p.process_event({"type": "product_interaction", "product_id": "br-001", "interaction_type": "add_to_cart"})
        await p.process_event({"type": "product_interaction", "product_id": "br-001", "interaction_type": "view"})

        stats = p.get_stats()
        br001 = stats["product_interest"]["br-001"]
        assert br001["view"] == 2
        assert br001["add_to_cart"] == 1

    async def test_order_completed_accumulates_revenue_by_hour(self):
        """
        order_completed events aggregate revenue into hour-level buckets.
        """
        p = _make_processor()
        await p.process_event({
            "type": "order_completed",
            "order_id": "ord-1",
            "amount": 79.99,
            "timestamp": "2026-02-20T14:35:00",
        })
        await p.process_event({
            "type": "order_completed",
            "order_id": "ord-2",
            "amount": 120.00,
            "timestamp": "2026-02-20T14:50:00",
        })

        stats = p.get_stats()
        hour_14 = stats["revenue_by_hour"]["2026-02-20T14"]
        assert abs(hour_14 - 199.99) < 0.01

    async def test_search_query_normalizes_and_counts(self):
        """
        search_query events normalize to lowercase and count frequency.
        """
        p = _make_processor()
        await p.process_event({"type": "search_query", "query": "Black Rose Hoodie"})
        await p.process_event({"type": "search_query", "query": "black rose hoodie"})
        await p.process_event({"type": "search_query", "query": "  BLACK ROSE HOODIE  "})

        stats = p.get_stats()
        assert stats["search_queries"]["black rose hoodie"] == 3

    async def test_unknown_event_type_is_skipped(self):
        """
        Events with unknown types are counted as skipped, not processed.
        Forward-compatible: new event types won't crash old processors.
        """
        p = _make_processor()
        result = await p.process_event({"type": "unknown_future_event", "data": {}})

        assert result is False
        stats = p.get_stats()
        assert stats["events_skipped"] == 1
        assert stats["events_processed"] == 0

    async def test_duplicate_events_are_deduped(self):
        """
        Events with the same event_id are processed only once.
        Critical for Kafka at-least-once delivery guarantee.
        """
        p = _make_processor()
        event = {"type": "page_view", "page": "/homepage", "event_id": "evt-abc-123"}

        await p.process_event(event)
        await p.process_event(event)  # Duplicate
        await p.process_event(event)  # Duplicate again

        stats = p.get_stats()
        assert stats["page_views"]["/homepage"] == 1  # Only counted once
        assert stats["events_processed"] == 1
        assert stats["events_skipped"] == 2

    async def test_malformed_event_is_handled_gracefully(self):
        """
        Events missing required fields use safe defaults rather than crashing.
        """
        p = _make_processor()
        # page_view without "page" key — defaults to "unknown"
        await p.process_event({"type": "page_view"})

        stats = p.get_stats()
        assert stats["page_views"]["unknown"] == 1


@pytest.mark.unit
class TestStreamProcessorAggregations:
    """Tests for aggregation helpers"""

    def test_get_top_products_sorted_by_total(self):
        """get_top_products returns products ranked by total interaction count."""
        p = _make_processor()
        p._state.product_interest = {
            "br-001": {"view": 100, "add_to_cart": 10},
            "sg-001": {"view": 50},
            "lh-001": {"view": 200, "wishlist": 5},
        }

        top = p.get_top_products(n=2)

        assert len(top) == 2
        assert top[0]["product_id"] == "lh-001"  # 205 total
        assert top[1]["product_id"] == "br-001"  # 110 total

    def test_get_top_pages_sorted_by_views(self):
        """get_top_pages returns pages ranked by view count."""
        p = _make_processor()
        p._state.page_views = {"/homepage": 500, "/about": 20, "/collections": 300}

        top = p.get_top_pages(n=2)

        assert top[0]["page"] == "/homepage"
        assert top[0]["views"] == 500
        assert len(top) == 2

    def test_reset_stats_clears_all_counters(self):
        """reset_stats() clears all aggregations to zero."""
        p = _make_processor()
        p._state.page_views = {"/homepage": 999}
        p._state.events_processed = 50

        p.reset_stats()

        stats = p.get_stats()
        assert stats["page_views"] == {}
        assert stats["events_processed"] == 0

    def test_analytics_state_to_dict_serializes_correctly(self):
        """AnalyticsState.to_dict() produces a clean dict without dataclass overhead."""
        state = AnalyticsState()
        state.page_views = {"page1": 5}
        state.events_processed = 10

        d = state.to_dict()

        assert d["page_views"] == {"page1": 5}
        assert d["events_processed"] == 10
        assert isinstance(d, dict)
