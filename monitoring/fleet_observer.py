"""Fleet-health observability consumer.

Closes the observability gap: core/token_tracker.py records per-agent LLM telemetry but had
zero consumers. FleetObserver reads that telemetry over a look-back window and emits alerts
when an agent or the fleet breaches a threshold.

ALERT + RECOMMEND ONLY. evaluate() is pure-read: it never restarts an agent, clears the
tracker, or calls any write API. Callers (an MCP tool, a cron) surface the report; all
remediation is human-initiated. Mirrors evaluation/observer.py's philosophy.

AlertSeverity is a local copy of evaluation.contracts.Severity (identical values) on purpose:
monitoring/ must not depend on the evaluation/ (QC) package — that would invert the dependency
direction and risk circular imports. Four lines is cheaper than a coupling.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import IntEnum

from core.token_tracker import TokenUsage, get_token_tracker


class AlertSeverity(IntEnum):
    """Alert routing: DASHBOARD (info), TICKET (actionable), PAGE (blocking)."""

    DASHBOARD = 1
    TICKET = 2
    PAGE = 3


@dataclass(frozen=True)
class FleetAlert:
    rule: str
    agent_id: str | None  # None = fleet-wide
    severity: AlertSeverity
    message: str
    value: float
    threshold: float


@dataclass(frozen=True)
class HealthReport:
    snapshot_at: datetime
    window_seconds: int
    alerts: tuple[FleetAlert, ...]
    per_agent: dict[str, dict]
    fleet_cost_usd: float
    fleet_requests: int


def _p95(values: list[float]) -> float:
    """95th percentile via nearest-rank (floor-biased for small N — fine for alerting)."""
    ordered = sorted(values)
    idx = min(int(0.95 * len(ordered)), len(ordered) - 1)
    return ordered[idx]


def _max_consecutive_failures(recs: list[TokenUsage]) -> int:
    """Longest run of consecutive failed calls, ordered by timestamp (retry-storm proxy)."""
    streak = best = 0
    for usage in sorted(recs, key=lambda u: u.timestamp):
        if usage.success:
            streak = 0
        else:
            streak += 1
            best = max(best, streak)
    return best


class FleetObserver:
    """Reads the token tracker and reports fleet/agent health alerts (read-only)."""

    def __init__(
        self,
        *,
        budget_usd: float = 10.0,  # fleet-wide cost cap per window
        cost_per_agent_usd: float = 2.0,  # per-agent cost cap per window
        error_rate_pct: float = 10.0,  # % of an agent's calls that failed
        p95_latency_ms: float = 5000.0,  # p95 latency gate
        stale_agent_secs: int = 300,  # no activity for N seconds
        consecutive_failures: int = 3,  # retry-storm proxy
        window_seconds: int = 3600,  # look-back window for every check
    ) -> None:
        self.budget_usd = budget_usd
        self.cost_per_agent_usd = cost_per_agent_usd
        self.error_rate_pct = error_rate_pct
        self.p95_latency_ms = p95_latency_ms
        self.stale_agent_secs = stale_agent_secs
        self.consecutive_failures = consecutive_failures
        self.window_seconds = window_seconds

    def evaluate(self) -> HealthReport:
        tracker = get_token_tracker()
        now = datetime.now(UTC)
        since = now - timedelta(seconds=self.window_seconds)

        by_agent = tracker.get_usage_by_agent(since=since)
        fleet_cost = tracker.get_total_cost(since=since)
        fleet_requests = sum(agg["requests"] for agg in by_agent.values())

        records_by_agent: dict[str, list[TokenUsage]] = {}
        for usage in tracker.records(since=since):
            records_by_agent.setdefault(usage.agent_id or "unknown", []).append(usage)

        alerts: list[FleetAlert] = []
        if fleet_cost > self.budget_usd:
            alerts.append(
                FleetAlert(
                    rule="budget_overrun",
                    agent_id=None,
                    severity=AlertSeverity.TICKET,
                    message=f"Fleet cost ${fleet_cost:.4f} exceeds ${self.budget_usd:.4f}",
                    value=fleet_cost,
                    threshold=self.budget_usd,
                )
            )
        for agent_id, agg in by_agent.items():
            alerts.extend(
                self._agent_alerts(agent_id, agg, records_by_agent.get(agent_id, []), now)
            )

        return HealthReport(
            snapshot_at=now,
            window_seconds=self.window_seconds,
            alerts=tuple(alerts),
            per_agent=dict(by_agent),
            fleet_cost_usd=fleet_cost,
            fleet_requests=fleet_requests,
        )

    def _agent_alerts(
        self, agent_id: str, agg: dict, recs: list[TokenUsage], now: datetime
    ) -> list[FleetAlert]:
        alerts: list[FleetAlert] = []

        if agg["cost_usd"] > self.cost_per_agent_usd:
            alerts.append(
                FleetAlert(
                    "agent_cost_overrun",
                    agent_id,
                    AlertSeverity.TICKET,
                    f"{agent_id} cost ${agg['cost_usd']:.4f} exceeds "
                    f"${self.cost_per_agent_usd:.4f}",
                    agg["cost_usd"],
                    self.cost_per_agent_usd,
                )
            )

        if not recs:
            return alerts

        errors = sum(1 for u in recs if not u.success)
        rate = 100.0 * errors / len(recs)
        if rate > self.error_rate_pct:
            alerts.append(
                FleetAlert(
                    "error_rate",
                    agent_id,
                    AlertSeverity.PAGE if rate > 50.0 else AlertSeverity.TICKET,
                    f"{agent_id} error rate {rate:.1f}% exceeds {self.error_rate_pct:.1f}%",
                    rate,
                    self.error_rate_pct,
                )
            )

        p95 = _p95([u.latency_ms for u in recs])
        if p95 > self.p95_latency_ms:
            alerts.append(
                FleetAlert(
                    "p95_latency",
                    agent_id,
                    AlertSeverity.TICKET,
                    f"{agent_id} p95 latency {p95:.0f}ms exceeds {self.p95_latency_ms:.0f}ms",
                    p95,
                    self.p95_latency_ms,
                )
            )

        streak = _max_consecutive_failures(recs)
        if streak >= self.consecutive_failures:
            alerts.append(
                FleetAlert(
                    "consecutive_failures",
                    agent_id,
                    (
                        AlertSeverity.PAGE
                        if streak >= 2 * self.consecutive_failures
                        else AlertSeverity.TICKET
                    ),
                    f"{agent_id} had {streak} consecutive failures "
                    f"(threshold {self.consecutive_failures})",
                    float(streak),
                    float(self.consecutive_failures),
                )
            )

        age_secs = (now - max(u.timestamp for u in recs)).total_seconds()
        if age_secs > self.stale_agent_secs:
            alerts.append(
                FleetAlert(
                    "stale_agent",
                    agent_id,
                    AlertSeverity.DASHBOARD,
                    f"{agent_id} last seen {age_secs:.0f}s ago "
                    f"(threshold {self.stale_agent_secs}s)",
                    age_secs,
                    float(self.stale_agent_secs),
                )
            )

        return alerts


def format_health_report(report: HealthReport) -> str:
    """Render a HealthReport as a markdown summary (used by the MCP fleet-health tool)."""
    lines = [
        f"## Fleet Health ({report.snapshot_at.strftime('%Y-%m-%d %H:%M:%S UTC')})",
        f"Window: {report.window_seconds}s | Cost: ${report.fleet_cost_usd:.4f} | "
        f"Requests: {report.fleet_requests}",
        "",
    ]
    if not report.alerts:
        lines.append("**No alerts. All agents within thresholds.**")
        return "\n".join(lines)

    lines.append("| Severity | Rule | Agent | Value | Threshold | Message |")
    lines.append("|----------|------|-------|-------|-----------|---------|")
    for alert in sorted(report.alerts, key=lambda a: -int(a.severity)):
        lines.append(
            f"| {alert.severity.name} | {alert.rule} | {alert.agent_id or 'fleet'} | "
            f"{alert.value:.2f} | {alert.threshold:.2f} | {alert.message} |"
        )
    return "\n".join(lines)


__all__ = [
    "AlertSeverity",
    "FleetAlert",
    "FleetObserver",
    "HealthReport",
    "format_health_report",
]
