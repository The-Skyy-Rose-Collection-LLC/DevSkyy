"""Analytics services for DevSkyy admin dashboard."""

from services.analytics.event_collector import (
    AnalyticsEvent,
    AnalyticsEventCollector,
    EventCollectorError,
    EventType,
)

__all__ = [
    "AnalyticsEvent",
    "AnalyticsEventCollector",
    "EventCollectorError",
    "EventType",
]
