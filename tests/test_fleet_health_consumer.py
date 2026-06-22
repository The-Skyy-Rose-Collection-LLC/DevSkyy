"""Tests for the fleet-health observability consumer (monitoring/fleet_observer.py).

Closes the Tier-1 observability gap: core/token_tracker.py records per-agent telemetry but
had zero consumers. FleetObserver reads that telemetry and emits alerts (budget, per-agent
cost, error rate, p95 latency, stale agent, consecutive failures). It is alert+recommend
only — it never mutates the tracker or acts on any agent.
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta

import pytest

from core.token_tracker import TaskType, TokenUsage, get_token_tracker
from monitoring.fleet_observer import (
    AlertSeverity,
    FleetObserver,
    HealthReport,
    format_health_report,
)


@pytest.fixture(autouse=True)
def _reset_token_tracker():
    """Isolate the module-global tracker per test (mirrors tests/orchestration pattern)."""
    import sys

    _tt = sys.modules["core.token_tracker"]
    _tt._global_tracker = None
    yield
    _tt.get_token_tracker().clear()


def _usage(
    agent_id: str | None = "agentA",
    *,
    model: str = "gpt-4o",
    input_tokens: int = 0,
    output_tokens: int = 0,
    latency_ms: float = 0.0,
    success: bool = True,
    error: str | None = None,
    ts: datetime | None = None,
) -> TokenUsage:
    return TokenUsage(
        provider="openai",
        model=model,
        task_type=TaskType.CHAT,
        agent_id=agent_id,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        success=success,
        error=error,
        timestamp=ts or datetime.now(UTC),
    )


def _record(*usages: TokenUsage) -> None:
    tracker = get_token_tracker()
    for u in usages:
        tracker.record(u)


def _observer(**overrides: float) -> FleetObserver:
    """Permissive observer (every threshold off) so a test can isolate one rule."""
    cfg = dict(
        budget_usd=1e9,
        cost_per_agent_usd=1e9,
        error_rate_pct=1e9,
        p95_latency_ms=1e12,
        stale_agent_secs=10**9,
        consecutive_failures=10**9,
        window_seconds=3600,
    )
    cfg.update(overrides)
    return FleetObserver(**cfg)


# --- TokenTracker.records() accessor (added for the consumer) -------------------


def test_records_returns_snapshot_copy():
    _record(_usage(), _usage())
    recs = get_token_tracker().records()
    assert len(recs) == 2
    recs.append("mutation")  # mutating the returned list must not affect the tracker
    assert len(get_token_tracker().records()) == 2


def test_records_since_filters_old():
    now = datetime.now(UTC)
    _record(_usage(ts=now - timedelta(hours=2)), _usage(ts=now))
    assert len(get_token_tracker().records(since=now - timedelta(minutes=30))) == 1


# --- FleetObserver alert rules -------------------------------------------------


def test_no_usages_produces_no_alerts():
    report = _observer().evaluate()
    assert report.alerts == ()
    assert report.fleet_cost_usd == 0.0
    assert report.fleet_requests == 0


def test_budget_overrun_fires_ticket():
    _record(_usage(input_tokens=1000))  # gpt-4o input = $2.50/1M -> $0.0025
    report = _observer(budget_usd=0.001).evaluate()
    fired = [a for a in report.alerts if a.rule == "budget_overrun"]
    assert len(fired) == 1
    assert fired[0].agent_id is None
    assert fired[0].severity == AlertSeverity.TICKET


def test_agent_cost_overrun_fires_for_named_agent():
    _record(_usage(agent_id="spendy", input_tokens=1000))
    report = _observer(cost_per_agent_usd=0.001).evaluate()
    fired = [a for a in report.alerts if a.rule == "agent_cost_overrun"]
    assert len(fired) == 1
    assert fired[0].agent_id == "spendy"


def test_error_rate_below_50_is_ticket():
    _record(
        *[_usage(agent_id="qa", success=True) for _ in range(4)],
        _usage(agent_id="qa", success=False),
    )
    report = _observer(error_rate_pct=10.0).evaluate()
    fired = [a for a in report.alerts if a.rule == "error_rate"]
    assert len(fired) == 1
    assert fired[0].severity == AlertSeverity.TICKET  # 20% < 50%


def test_error_rate_above_50_is_page():
    _record(_usage(agent_id="qa", success=False), _usage(agent_id="qa", success=False))
    report = _observer(error_rate_pct=10.0).evaluate()
    fired = [a for a in report.alerts if a.rule == "error_rate"]
    assert len(fired) == 1
    assert fired[0].severity == AlertSeverity.PAGE  # 100% > 50%


def test_p95_latency_fires_ticket():
    _record(*[_usage(agent_id="slow", latency_ms=6000.0) for _ in range(20)])
    report = _observer(p95_latency_ms=5000.0).evaluate()
    fired = [a for a in report.alerts if a.rule == "p95_latency"]
    assert len(fired) == 1
    assert fired[0].value >= 5000.0


def test_stale_agent_fires_dashboard():
    _record(_usage(agent_id="idle", ts=datetime.now(UTC) - timedelta(seconds=400)))
    report = _observer(stale_agent_secs=300).evaluate()
    fired = [a for a in report.alerts if a.rule == "stale_agent"]
    assert len(fired) == 1
    assert fired[0].severity == AlertSeverity.DASHBOARD


def test_active_agent_no_stale_alert():
    _record(_usage(agent_id="active", ts=datetime.now(UTC) - timedelta(seconds=30)))
    report = _observer(stale_agent_secs=300).evaluate()
    assert [a for a in report.alerts if a.rule == "stale_agent"] == []


def test_consecutive_failures_at_threshold_is_ticket():
    base = datetime.now(UTC)
    _record(
        *[
            _usage(agent_id="flaky", success=False, ts=base - timedelta(seconds=3 - i))
            for i in range(3)
        ]
    )
    report = _observer(consecutive_failures=3, error_rate_pct=1e9).evaluate()
    fired = [a for a in report.alerts if a.rule == "consecutive_failures"]
    assert len(fired) == 1
    assert fired[0].value == 3.0
    assert fired[0].severity == AlertSeverity.TICKET  # 3 < 2*3


def test_consecutive_failures_at_double_threshold_is_page():
    base = datetime.now(UTC)
    _record(
        *[
            _usage(agent_id="flaky", success=False, ts=base - timedelta(seconds=6 - i))
            for i in range(6)
        ]
    )
    report = _observer(consecutive_failures=3, error_rate_pct=1e9).evaluate()
    fired = [a for a in report.alerts if a.rule == "consecutive_failures"]
    assert len(fired) == 1
    assert fired[0].value == 6.0
    assert fired[0].severity == AlertSeverity.PAGE  # 6 >= 2*3


def test_window_seconds_excludes_old_usage():
    _record(_usage(input_tokens=1000, ts=datetime.now(UTC) - timedelta(hours=2)))
    report = _observer(window_seconds=3600, budget_usd=0.0001).evaluate()
    assert report.fleet_requests == 0
    assert report.fleet_cost_usd == 0.0
    assert report.alerts == ()


def test_healthy_agent_produces_no_alerts():
    _record(*[_usage(agent_id="good", input_tokens=1, latency_ms=10.0) for _ in range(5)])
    # real-ish thresholds; nothing should fire
    report = FleetObserver().evaluate()
    assert report.alerts == ()


# --- contracts: immutability + read-only ---------------------------------------


def test_report_and_alert_are_frozen():
    _record(_usage(input_tokens=1000))
    report = _observer(budget_usd=0.001).evaluate()
    assert isinstance(report, HealthReport)
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.fleet_cost_usd = 5.0  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.alerts[0].value = 1.0  # type: ignore[misc]


def test_evaluate_never_mutates_tracker():
    _record(_usage(agent_id="a", input_tokens=10), _usage(agent_id="b", input_tokens=20))
    before = get_token_tracker().get_usage_by_agent()
    obs = _observer(budget_usd=0.0)  # would alert, but must not mutate
    obs.evaluate()
    obs.evaluate()
    assert get_token_tracker().get_usage_by_agent() == before
    assert len(get_token_tracker().records()) == 2


# --- formatter -----------------------------------------------------------------


def test_format_health_report_no_alerts():
    out = format_health_report(_observer().evaluate())
    assert "No alerts" in out


def test_format_health_report_lists_alert():
    _record(_usage(agent_id="spendy", input_tokens=1000))
    out = format_health_report(_observer(cost_per_agent_usd=0.001).evaluate())
    assert "agent_cost_overrun" in out
    assert "spendy" in out
    assert "TICKET" in out
