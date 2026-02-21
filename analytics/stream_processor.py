"""
Real-Time Analytics Stream Processor
======================================

Consumes domain events from Kafka and maintains real-time aggregations
for business intelligence dashboards.

Event types processed:
  - page_view        → increment_page_views(page)
  - product_interaction → track_product_interest(product_id, interaction_type)
  - order_completed  → update_revenue_metrics(order_id, amount)
  - search_query     → track_search_query(query, results_count)

Design principles:
- **Idempotent processing**: each event can be replayed safely
- **At-least-once delivery**: Kafka may deliver duplicates (use event_id dedup)
- **Graceful degradation**: Kafka unavailable → processor exits cleanly
- **In-memory aggregations**: fast writes, periodic flush to DB/Redis

Usage:
    processor = StreamProcessor(bootstrap_servers="localhost:9092")
    await processor.start()       # Begin consuming
    await processor.stop()        # Graceful shutdown

    # Access current aggregations
    stats = processor.get_stats()
    # {"page_views": {"homepage": 1542}, "product_interest": {...}, ...}
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# Default Kafka topic to consume from
DEFAULT_TOPIC = "devskyy-events"
DEFAULT_GROUP_ID = "analytics-processor"


# ---------------------------------------------------------------------------
# Analytics Aggregations (in-memory, flushed periodically)
# ---------------------------------------------------------------------------


@dataclass
class AnalyticsState:
    """
    In-memory aggregation state.

    All fields are incremental counters or dicts. Safe to merge across
    multiple processor instances before flushing to a persistent store.
    """

    page_views: dict[str, int] = field(default_factory=dict)
    product_interest: dict[str, dict[str, int]] = field(default_factory=dict)
    revenue_by_hour: dict[str, float] = field(default_factory=dict)
    search_queries: dict[str, int] = field(default_factory=dict)
    events_processed: int = 0
    events_skipped: int = 0
    last_reset: float = field(default_factory=time.monotonic)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for API responses and DB flush."""
        return {
            "page_views": dict(self.page_views),
            "product_interest": {k: dict(v) for k, v in self.product_interest.items()},
            "revenue_by_hour": dict(self.revenue_by_hour),
            "search_queries": dict(self.search_queries),
            "events_processed": self.events_processed,
            "events_skipped": self.events_skipped,
        }


# ---------------------------------------------------------------------------
# Stream Processor
# ---------------------------------------------------------------------------


class StreamProcessor:
    """
    Kafka consumer that maintains real-time analytics aggregations.

    The processor loop:
    1. Poll Kafka for new messages (batch)
    2. Deserialize each message as a domain event
    3. Route to handler based on event type
    4. Update in-memory aggregations
    5. Periodically flush aggregations to Redis/DB

    Resilience:
    - Unknown event types are silently skipped (forward compatibility)
    - Handler exceptions are logged but don't stop the loop
    - confluent_kafka not installed → processor degrades gracefully
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        topic: str = DEFAULT_TOPIC,
        group_id: str = DEFAULT_GROUP_ID,
        poll_timeout: float = 1.0,
        flush_interval: float = 60.0,
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self.poll_timeout = poll_timeout
        self.flush_interval = flush_interval

        self._state = AnalyticsState()
        self._consumer: Any = None
        self._running = False
        # OrderedDict for FIFO dedup — oldest entries evicted first.
        # set.pop() removes an arbitrary element (non-deterministic), making it
        # possible for recent event IDs to be evicted, allowing replays.
        # OrderedDict.popitem(last=False) always removes the oldest entry.
        self._seen_event_ids: OrderedDict[str, None] = OrderedDict()
        self._max_dedup_size = 10_000

        # Dispatch table — maps event_type → handler method
        self._handlers: dict[str, Callable[[dict[str, Any]], None]] = {
            "page_view": self._handle_page_view,
            "product_interaction": self._handle_product_interaction,
            "order_completed": self._handle_order_completed,
            "search_query": self._handle_search_query,
        }

    # ---------------------------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------------------------

    async def start(self) -> None:
        """
        Initialize Kafka consumer and start the processing loop.

        If confluent_kafka is unavailable, logs a warning and returns.
        """
        try:
            from confluent_kafka import Consumer, KafkaError, KafkaException
        except ImportError:
            logger.warning(
                "confluent_kafka not installed. "
                "Install with: pip install confluent-kafka"
            )
            return

        self._consumer = Consumer(
            {
                "bootstrap.servers": self.bootstrap_servers,
                "group.id": self.group_id,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": True,
                "auto.commit.interval.ms": 5000,
            }
        )
        self._consumer.subscribe([self.topic])
        self._running = True

        logger.info(
            f"StreamProcessor started: topic={self.topic!r}, "
            f"group={self.group_id!r}, servers={self.bootstrap_servers!r}"
        )

        await self._run_loop()

    async def stop(self) -> None:
        """Gracefully stop the processing loop and close the consumer."""
        self._running = False
        if self._consumer is not None:
            self._consumer.close()
            self._consumer = None
        logger.info("StreamProcessor stopped")

    async def _run_loop(self) -> None:
        """Main consumer loop — runs until stop() is called."""
        last_flush = time.monotonic()

        while self._running:
            # Yield to event loop to allow other tasks to run
            await asyncio.sleep(0)

            try:
                msg = self._consumer.poll(self.poll_timeout)
            except Exception as exc:
                logger.error(f"Kafka poll error: {exc}")
                await asyncio.sleep(1.0)
                continue

            if msg is None:
                # No messages — check if flush is due
                if time.monotonic() - last_flush >= self.flush_interval:
                    await self._flush()
                    last_flush = time.monotonic()
                continue

            if msg.error():
                logger.warning(f"Kafka message error: {msg.error()}")
                continue

            await self._process_message(msg.value())

            # Periodic flush
            if time.monotonic() - last_flush >= self.flush_interval:
                await self._flush()
                last_flush = time.monotonic()

    # ---------------------------------------------------------------------------
    # Message Processing
    # ---------------------------------------------------------------------------

    async def process_event(self, event: dict[str, Any]) -> bool:
        """
        Process a single event dict.

        This is the public entry point for direct event injection
        (testing, backfill, or non-Kafka delivery).

        Returns True if event was processed, False if skipped (duplicate or unknown type).
        """
        return await self._dispatch(event)

    async def _process_message(self, raw: bytes) -> None:
        """Deserialize and dispatch a raw Kafka message."""
        try:
            event = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning(f"Failed to deserialize message: {exc}")
            self._state.events_skipped += 1
            return

        await self._dispatch(event)

    async def _dispatch(self, event: dict[str, Any]) -> bool:
        """
        Route event to the appropriate handler.

        Deduplicates by event_id if present — idempotent processing
        is critical since Kafka guarantees at-least-once delivery.
        """
        event_id = event.get("event_id")
        if event_id:
            if event_id in self._seen_event_ids:
                logger.debug(f"Duplicate event {event_id!r} — skipping")
                self._state.events_skipped += 1
                return False
            self._seen_event_ids[event_id] = None
            # FIFO eviction: remove oldest event_id first to prevent
            # recent IDs from being accidentally evicted (security fix —
            # non-deterministic set.pop() could allow event replay attacks)
            while len(self._seen_event_ids) > self._max_dedup_size:
                self._seen_event_ids.popitem(last=False)

        event_type = event.get("type") or event.get("event_type", "")
        handler = self._handlers.get(event_type)

        if handler is None:
            logger.debug(f"No handler for event_type={event_type!r} — skipping")
            self._state.events_skipped += 1
            return False

        try:
            handler(event)
            self._state.events_processed += 1
            return True
        except Exception as exc:
            logger.error(f"Handler error for {event_type!r}: {exc}", exc_info=True)
            self._state.events_skipped += 1
            return False

    # ---------------------------------------------------------------------------
    # Event Handlers
    # ---------------------------------------------------------------------------

    # Limits cap memory usage from attacker-controlled dict keys
    _MAX_PAGES = 10_000
    _MAX_PRODUCTS = 50_000
    _MAX_HOUR_BUCKETS = 8_760   # 1 year of hourly buckets
    _MAX_QUERIES = 50_000
    _MAX_QUERY_LEN = 500

    def _handle_page_view(self, event: dict[str, Any]) -> None:
        """Increment page view counter for the given page."""
        page = str(event.get("page", "unknown"))[:200]  # Cap key length
        if page not in self._state.page_views and len(self._state.page_views) >= self._MAX_PAGES:
            return  # Silently drop — cap prevents memory exhaustion
        self._state.page_views[page] = self._state.page_views.get(page, 0) + 1

    def _handle_product_interaction(self, event: dict[str, Any]) -> None:
        """
        Track product interactions (view, add_to_cart, wishlist, share).

        Groups by product_id, then by interaction_type — creates a heat map
        of which products have most engagement and what kind.
        """
        product_id = str(event.get("product_id", "unknown"))[:50]
        interaction_type = str(event.get("interaction_type", "view"))[:50]

        if product_id not in self._state.product_interest:
            if len(self._state.product_interest) >= self._MAX_PRODUCTS:
                return
            self._state.product_interest[product_id] = {}

        bucket = self._state.product_interest[product_id]
        bucket[interaction_type] = bucket.get(interaction_type, 0) + 1

    def _handle_order_completed(self, event: dict[str, Any]) -> None:
        """
        Accumulate revenue by hour bucket.

        Uses ISO-8601 hour-level bucket (e.g., "2026-02-20T14") so dashboards
        can render hourly revenue charts without querying the DB.
        """
        try:
            amount = float(event.get("amount", 0.0))
        except (TypeError, ValueError):
            logger.warning(f"Invalid amount in order event: {event.get('amount')!r}")
            return
        if amount < 0 or amount > 1_000_000:
            logger.warning(f"Suspicious order amount skipped: {amount}")
            return

        timestamp = str(event.get("timestamp", ""))
        hour_bucket = timestamp[:13] if len(timestamp) >= 13 else "unknown"

        if hour_bucket not in self._state.revenue_by_hour and \
                len(self._state.revenue_by_hour) >= self._MAX_HOUR_BUCKETS:
            return
        self._state.revenue_by_hour[hour_bucket] = (
            self._state.revenue_by_hour.get(hour_bucket, 0.0) + amount
        )

    def _handle_search_query(self, event: dict[str, Any]) -> None:
        """Track search query frequency for autocomplete and SEO insights."""
        query = str(event.get("query", "")).lower().strip()
        if not query or len(query) > self._MAX_QUERY_LEN:
            return
        if query not in self._state.search_queries and \
                len(self._state.search_queries) >= self._MAX_QUERIES:
            return
        self._state.search_queries[query] = (
            self._state.search_queries.get(query, 0) + 1
        )

    # ---------------------------------------------------------------------------
    # Aggregation Access
    # ---------------------------------------------------------------------------

    def get_stats(self) -> dict[str, Any]:
        """Return current aggregation state as a plain dict."""
        return self._state.to_dict()

    def get_top_products(self, n: int = 10) -> list[dict[str, Any]]:
        """
        Return top N products by total interaction count.

        Useful for homepage "trending products" feature.
        """
        products = []
        for product_id, interactions in self._state.product_interest.items():
            total = sum(interactions.values())
            products.append({"product_id": product_id, "total_interactions": total, **interactions})
        return sorted(products, key=lambda x: x["total_interactions"], reverse=True)[:n]

    def get_top_pages(self, n: int = 10) -> list[dict[str, Any]]:
        """Return top N most-viewed pages."""
        sorted_pages = sorted(
            self._state.page_views.items(), key=lambda x: x[1], reverse=True
        )
        return [{"page": page, "views": views} for page, views in sorted_pages[:n]]

    def reset_stats(self) -> None:
        """Reset all aggregations. Call after flushing to persistent store."""
        self._state = AnalyticsState()

    # ---------------------------------------------------------------------------
    # Flush
    # ---------------------------------------------------------------------------

    async def _flush(self) -> None:
        """
        Flush in-memory aggregations to persistent storage.

        In production, writes to Redis sorted sets (for leaderboards) and
        time-series DB (for revenue charts). Currently logs the flush.
        """
        stats = self._state.to_dict()
        logger.info(
            f"Analytics flush: "
            f"processed={stats['events_processed']}, "
            f"page_views={sum(stats['page_views'].values())}, "
            f"products_tracked={len(stats['product_interest'])}"
        )
        # TODO: await redis_client.hincrby("page_views", page, count)
        # TODO: await timeseries_db.insert("revenue", revenue_by_hour)
