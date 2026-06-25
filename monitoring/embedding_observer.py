"""Embedding-gate observability + PSI drift — ALERT-ONLY, pure-read.

Mirrors ``monitoring/fleet_observer.py``: ``evaluate()`` computes alerts and
NEVER mutates the gate threshold, the PSI reference, or any other state. All
remediation (recalibrating the centroid threshold) is human-initiated.

The brand-centroid gate freezes its accept threshold at build time against the
score distribution it was calibrated on. If the live cosine-score distribution
drifts off that reference, the threshold silently stops meaning what it did.
Population Stability Index (PSI) over the score distribution is the standard
drift signal: <0.1 stable, 0.1-0.2 minor, >0.2 significant. We TICKET at
PSI > 0.2 and PAGE at PSI > 0.25 — and only alert; we never auto-retune.

``AlertSeverity`` is reused from ``fleet_observer`` (same package) rather than the
``evaluation`` package's ``Severity``, keeping ``monitoring/`` free of a QC-package
dependency — the same decoupling rationale documented in ``fleet_observer``.

@package SkyyRose
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from monitoring.fleet_observer import AlertSeverity

# Industry-standard PSI bands. Recalibration is human-initiated; these only route.
PSI_TICKET = 0.2
PSI_PAGE = 0.25
# Laplace smoothing so an empty bucket can't drive a term to ±inf.
_EPS = 1e-6
_DEFAULT_BUCKETS = 10


def _bucket_index(score: float, edges: tuple[float, ...]) -> int:
    """Index of the half-open bucket [edges[i], edges[i+1]) holding ``score``.

    Scores at or below the first edge land in bucket 0; at or above the last edge
    in the final bucket — so out-of-range live scores are clamped, not dropped.
    """
    n = len(edges) - 1
    if score <= edges[0]:
        return 0
    if score >= edges[-1]:
        return n - 1
    for i in range(n):
        if edges[i] <= score < edges[i + 1]:
            return i
    return n - 1  # unreachable given the guards above


def _proportions(scores: list[float], edges: tuple[float, ...]) -> tuple[float, ...]:
    """Fraction of ``scores`` in each bucket defined by ``edges`` (binned with edges)."""
    n = len(edges) - 1
    counts = [0] * n
    for s in scores:
        counts[_bucket_index(s, edges)] += 1
    total = len(scores) or 1
    return tuple(c / total for c in counts)


@dataclass(frozen=True)
class PSIReference:
    """Frozen build-time score distribution: bucket EDGES + reference proportions.

    Edges are fixed at build time; live scores are always binned with THESE edges
    (never re-binned independently) so the PSI comparison is apples-to-apples.
    """

    edges: tuple[float, ...]  # len == n_buckets + 1, ascending
    proportions: tuple[float, ...]  # len == n_buckets, sums to ~1.0

    @staticmethod
    def from_scores(
        scores: list[float], *, n_buckets: int = _DEFAULT_BUCKETS, lo: float = 0.0, hi: float = 1.0
    ) -> PSIReference:
        if n_buckets < 1:
            raise ValueError(f"n_buckets must be >= 1, got {n_buckets}")
        if hi <= lo:
            raise ValueError(f"hi ({hi}) must be > lo ({lo})")
        edges = tuple(lo + (hi - lo) * i / n_buckets for i in range(n_buckets + 1))
        return PSIReference(edges=edges, proportions=_proportions(scores, edges))


def psi(reference: PSIReference, live_scores: list[float]) -> float:
    """Population Stability Index of ``live_scores`` vs the reference.

    Live scores are binned with the reference's own edges. Returns 0.0 on an
    identical distribution and grows as the live distribution shifts. Empty-bucket
    terms are Laplace-smoothed by ``_EPS``.
    """
    live = _proportions(live_scores, reference.edges)
    total = 0.0
    for ref_p, live_p in zip(reference.proportions, live, strict=True):
        r = ref_p + _EPS
        live_p_eps = live_p + _EPS
        total += (live_p_eps - r) * math.log(live_p_eps / r)
    return total


@dataclass(frozen=True)
class GateAlert:
    rule: str
    severity: AlertSeverity
    message: str
    value: float
    threshold: float


@dataclass(frozen=True)
class GateReport:
    n_scores: int
    accept_ratio: float | None  # None when no accept/reject labels were supplied
    psi: float | None  # None when no reference was configured (or no live scores)
    alerts: tuple[GateAlert, ...]


class EmbeddingObserver:
    """Read-only embedding-gate health observer. Never mutates the gate threshold.

    ``evaluate()`` is pure: given the live gate scores (and optional accept/reject
    labels) it returns a :class:`GateReport`. It reads the configured PSI reference
    but never writes it or any gate state — recalibration stays human-initiated.
    """

    def __init__(
        self,
        *,
        reference: PSIReference | None = None,
        psi_ticket: float = PSI_TICKET,
        psi_page: float = PSI_PAGE,
        min_accept_ratio: float | None = None,
    ) -> None:
        self._reference = reference
        self._psi_ticket = psi_ticket
        self._psi_page = psi_page
        self._min_accept_ratio = min_accept_ratio

    def evaluate(
        self, live_scores: list[float], *, accepted: list[bool] | None = None
    ) -> GateReport:
        alerts: list[GateAlert] = []

        psi_value: float | None = None
        if self._reference is not None and live_scores:
            psi_value = psi(self._reference, live_scores)
            if psi_value > self._psi_page:
                alerts.append(
                    GateAlert(
                        "psi_drift",
                        AlertSeverity.PAGE,
                        f"gate score PSI {psi_value:.3f} exceeds PAGE {self._psi_page:.2f} "
                        f"— live distribution has drifted off the calibrated reference",
                        psi_value,
                        self._psi_page,
                    )
                )
            elif psi_value > self._psi_ticket:
                alerts.append(
                    GateAlert(
                        "psi_drift",
                        AlertSeverity.TICKET,
                        f"gate score PSI {psi_value:.3f} exceeds TICKET {self._psi_ticket:.2f}",
                        psi_value,
                        self._psi_ticket,
                    )
                )

        accept_ratio: float | None = None
        if accepted:
            accept_ratio = sum(1 for a in accepted if a) / len(accepted)
            if self._min_accept_ratio is not None and accept_ratio < self._min_accept_ratio:
                alerts.append(
                    GateAlert(
                        "low_accept_ratio",
                        AlertSeverity.TICKET,
                        f"accept ratio {accept_ratio:.2%} below floor {self._min_accept_ratio:.2%}",
                        accept_ratio,
                        self._min_accept_ratio,
                    )
                )

        return GateReport(
            n_scores=len(live_scores),
            accept_ratio=accept_ratio,
            psi=psi_value,
            alerts=tuple(alerts),
        )


def format_gate_report(report: GateReport) -> str:
    """Render a :class:`GateReport` as a markdown summary (for an MCP tool / cron)."""
    ratio = "n/a" if report.accept_ratio is None else f"{report.accept_ratio:.2%}"
    psi_str = "n/a" if report.psi is None else f"{report.psi:.3f}"
    lines = [
        "## Embedding Gate Health",
        f"Scores: {report.n_scores} | Accept ratio: {ratio} | PSI: {psi_str}",
        "",
    ]
    if not report.alerts:
        lines.append("**No alerts. Gate within thresholds.**")
        return "\n".join(lines)
    lines.append("| Severity | Rule | Value | Threshold | Message |")
    lines.append("|----------|------|-------|-----------|---------|")
    for alert in sorted(report.alerts, key=lambda a: -int(a.severity)):
        lines.append(
            f"| {alert.severity.name} | {alert.rule} | {alert.value:.3f} | "
            f"{alert.threshold:.3f} | {alert.message} |"
        )
    return "\n".join(lines)


__all__ = [
    "PSI_TICKET",
    "PSI_PAGE",
    "PSIReference",
    "psi",
    "GateAlert",
    "GateReport",
    "EmbeddingObserver",
    "format_gate_report",
]
