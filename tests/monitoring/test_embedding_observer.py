"""EmbeddingObserver + PSI drift (OBS-gate / OBS-psi) — pure, model-free.

Acceptance (spec §9): PSI == 0 on identical distributions and rises on a shift;
the observer is pure-read (never mutates the threshold).
"""

import pytest

from monitoring.embedding_observer import (
    PSI_PAGE,
    EmbeddingObserver,
    PSIReference,
    format_gate_report,
    psi,
)
from monitoring.fleet_observer import AlertSeverity


def test_psi_zero_on_identical_distribution():
    scores = [0.1, 0.3, 0.5, 0.7, 0.9, 0.5, 0.5, 0.6]
    ref = PSIReference.from_scores(scores)
    assert psi(ref, scores) == pytest.approx(0.0, abs=1e-9)


def test_psi_rises_on_shift():
    ref = PSIReference.from_scores([0.9, 0.92, 0.88, 0.95, 0.9, 0.91])
    drifted = [0.1, 0.15, 0.2, 0.12, 0.18, 0.1]
    assert psi(ref, drifted) > psi(ref, [0.9, 0.92, 0.88, 0.95, 0.9, 0.91])
    assert psi(ref, drifted) > PSI_PAGE  # a gross shift clears the PAGE band


def test_psi_bins_live_with_reference_edges_not_rebinned():
    # Two disjoint clusters would look "identical" if each were re-binned on its
    # own range. Binning live with the REFERENCE edges keeps them apart -> PSI > 0.
    ref = PSIReference.from_scores([0.1, 0.1, 0.1, 0.1])  # all in the low bucket
    live = [0.9, 0.9, 0.9, 0.9]  # all in the high bucket
    assert psi(ref, live) > 0.0


def test_observer_clean_distribution_has_no_alert():
    ref = PSIReference.from_scores([0.9, 0.91, 0.92, 0.9, 0.93, 0.9])
    rep = EmbeddingObserver(reference=ref).evaluate([0.9, 0.91, 0.9, 0.92])
    assert rep.alerts == ()
    assert rep.psi == pytest.approx(0.0, abs=1e-9)


def test_observer_pages_on_gross_drift():
    ref = PSIReference.from_scores([0.9, 0.91, 0.92, 0.9, 0.93, 0.9])
    rep = EmbeddingObserver(reference=ref).evaluate([0.1, 0.05, 0.12, 0.08])
    assert any(a.rule == "psi_drift" and a.severity == AlertSeverity.PAGE for a in rep.alerts)


def test_observer_is_pure_read_never_mutates():
    ref = PSIReference.from_scores([0.5, 0.6, 0.7, 0.4])
    obs = EmbeddingObserver(reference=ref)
    before_props, before_edges = ref.proportions, ref.edges
    before_thresholds = (obs._psi_ticket, obs._psi_page)
    live = [0.1, 0.2, 0.9, 0.95]

    r1 = obs.evaluate(live)
    r2 = obs.evaluate(live)

    assert ref.proportions == before_props and ref.edges == before_edges  # reference frozen
    assert (obs._psi_ticket, obs._psi_page) == before_thresholds  # thresholds untouched
    assert live == [0.1, 0.2, 0.9, 0.95]  # input not mutated
    assert r1 == r2  # idempotent — no hidden state


def test_observer_accept_ratio_and_low_accept_alert():
    obs = EmbeddingObserver(min_accept_ratio=0.5)
    rep = obs.evaluate([0.9, 0.2, 0.1, 0.1], accepted=[True, False, False, False])
    assert rep.accept_ratio == pytest.approx(0.25)
    assert any(a.rule == "low_accept_ratio" for a in rep.alerts)


def test_observer_without_reference_reports_no_psi():
    rep = EmbeddingObserver().evaluate([0.5, 0.6])
    assert rep.psi is None and rep.alerts == ()


def test_format_gate_report_renders_markdown():
    ref = PSIReference.from_scores([0.9, 0.9, 0.9])
    rep = EmbeddingObserver(reference=ref).evaluate([0.1, 0.1, 0.1])
    out = format_gate_report(rep)
    assert "Embedding Gate Health" in out
    assert "psi_drift" in out  # the drift alert is rendered


def test_gate_scores_feed_observer_end_to_end():
    # The wire Track-OBS closes: gate verdicts recorded via record_gate_score are read by
    # gate_scores() and consumed by EmbeddingObserver as the live PSI distribution. Before
    # this, the observer was built (#640) but had NO signal source.
    from core import token_tracker
    from core.token_tracker import gate_scores, record_gate_score

    token_tracker.get_token_tracker().clear()
    reference = PSIReference.from_scores([0.80, 0.82, 0.85, 0.83, 0.81, 0.84])  # on-brand
    for s in [0.30, 0.32, 0.28, 0.35, 0.31, 0.29]:  # a drifted-off-brand run
        record_gate_score(model="test", score=s, accepted=s >= 0.65, threshold=0.65)

    live = gate_scores()
    assert len(live) == 6
    rep = EmbeddingObserver(reference=reference).evaluate(live, accepted=[False] * 6)
    assert rep.n_scores == 6
    assert rep.psi is not None and rep.psi > PSI_PAGE
    assert any(a.rule == "psi_drift" and a.severity == AlertSeverity.PAGE for a in rep.alerts)
