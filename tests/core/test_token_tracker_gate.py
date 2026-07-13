"""Track-OBS: brand-centroid gate-score telemetry in token_tracker.

The embedding gate (``embedding_gate.evaluate``) produces a cosine score per render
but emitted nothing, so ``EmbeddingObserver`` (PSI drift) had no signal. These rows
(``TaskType.GATE``) carry the score/accepted/threshold; ``gate_scores()`` is the read
path the observer consumes.
"""

from __future__ import annotations

import pytest

from core import token_tracker
from core.token_tracker import (
    TaskType,
    gate_scores,
    get_token_tracker,
    record_embedding_usage,
    record_gate_score,
)


def _fresh():
    t = get_token_tracker()
    t.clear()
    return t


def test_record_gate_score_adds_zero_cost_gate_row():
    t = _fresh()
    record_gate_score(model="test", score=0.72, accepted=True, threshold=0.65, subject="br-001")
    rows = t.records()
    assert len(rows) == 1
    r = rows[0]
    assert r.task_type == TaskType.GATE
    assert r.provider == "embeddings"
    assert r.metadata["score"] == pytest.approx(0.72)
    assert r.metadata["accepted"] is True
    assert r.metadata["threshold"] == pytest.approx(0.65)
    assert r.metadata["subject"] == "br-001"
    # gate scoring uses local weights — no token cost
    assert r.input_tokens == 0 and r.output_tokens == 0 and r.calculate_cost() == 0.0


def test_gate_scores_returns_only_gate_rows():
    _fresh()
    record_gate_score(model="test", score=0.50, accepted=False, threshold=0.65)
    record_gate_score(model="test", score=0.90, accepted=True, threshold=0.65)
    # an embedding ENCODE row must not pollute the gate-score stream
    record_embedding_usage(model="test")
    assert gate_scores() == [pytest.approx(0.50), pytest.approx(0.90)]


def test_gate_scores_since_filter():
    t = _fresh()
    record_gate_score(model="test", score=0.10, accepted=False, threshold=0.65)
    cutoff = t.records()[-1].timestamp
    record_gate_score(model="test", score=0.95, accepted=True, threshold=0.65)
    after = gate_scores(since=cutoff)
    # only scores at/after the cutoff timestamp
    assert 0.95 in [pytest.approx(s) for s in after] or after == [pytest.approx(0.95)]


def test_record_gate_score_never_raises(monkeypatch):
    # telemetry must NEVER break the gate: a tracker failure is swallowed.
    _fresh()

    class Boom:
        def record(self, *_a, **_k):
            raise RuntimeError("tracker down")

    monkeypatch.setattr(token_tracker, "get_token_tracker", lambda: Boom())
    # must not raise
    record_gate_score(model="test", score=0.5, accepted=True, threshold=0.65)
