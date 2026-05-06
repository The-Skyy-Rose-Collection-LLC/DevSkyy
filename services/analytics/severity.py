# services/analytics/severity.py
"""Shared alert severity enum for analytics services.

Single source of truth for AlertSeverity used by both alert_engine.py and
alert_notifier.py.  Having two separate definitions caused a KeyError whenever
an alert persisted with HIGH/MEDIUM/LOW (notifier levels) was loaded or routed
through the engine (which only knew INFO, WARNING, CRITICAL).

Severity order (lowest → highest):
    INFO < LOW < MEDIUM < HIGH < CRITICAL (maps to SEVERITY_ORDER in alert_notifier)
"""

from __future__ import annotations

from enum import StrEnum


class AlertSeverity(StrEnum):
    """Alert severity levels — shared across engine and notifier.

    Canonical five-level scale (lowest → highest):
        INFO < LOW < MEDIUM < HIGH < CRITICAL

    WARNING is a legacy alias for MEDIUM kept for backward compatibility with
    alert_engine.py defaults and existing test assertions.  New code should
    use MEDIUM directly.
    """

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    WARNING = "medium"  # legacy alias → same value as MEDIUM
    HIGH = "high"
    CRITICAL = "critical"
