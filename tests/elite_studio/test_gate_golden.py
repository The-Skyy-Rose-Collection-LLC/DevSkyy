"""Golden characterization of the embedding-gate decision logic.

Model-free: monkeypatches clip_embedder.embed_image to a fixed seeded vector, so
the REAL score_against_centroid (cosine_similarity) + evaluate (threshold compare,
GateVerdict construction) run deterministically. Pins the gate's behavior so the
embeddings reframe (Phase 2) cannot silently change the score math, the accept/
reject branches, or the verdict shape.

Oracle: clip_embedder.cosine_similarity is `float(np.dot(a, b))` for L2-normalized
inputs, so `float(np.dot(e, c))` is an independent (non-circular) expected value.
"""

from __future__ import annotations

import numpy as np
import pytest

from skyyrose.core import clip_embedder
from skyyrose.elite_studio.quality import embedding_gate
from skyyrose.elite_studio.quality.brand_centroid import BrandCentroid

pytestmark = pytest.mark.unit


def _unit_vec(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(512).astype(np.float32)
    return v / np.linalg.norm(v)


def _centroid(threshold: float) -> BrandCentroid:
    return BrandCentroid(
        centroid=_unit_vec(7),
        threshold=threshold,
        sample_count=10,
        model_id="test",
    )


def test_gate_score_equals_cosine_oracle(monkeypatch) -> None:
    e = _unit_vec(11)
    monkeypatch.setattr(clip_embedder, "embed_image", lambda *_a, **_kw: e)

    verdict = embedding_gate.evaluate("ignored.png", _centroid(threshold=0.0))

    expected = float(np.dot(e, _unit_vec(7)))
    assert verdict.score == pytest.approx(expected, abs=1e-6)
    assert isinstance(verdict, embedding_gate.GateVerdict)


def test_gate_accepts_at_or_above_threshold(monkeypatch) -> None:
    e = _unit_vec(11)
    monkeypatch.setattr(clip_embedder, "embed_image", lambda *_a, **_kw: e)
    expected = float(np.dot(e, _unit_vec(7)))

    verdict = embedding_gate.evaluate("ignored.png", _centroid(threshold=expected - 0.01))

    assert verdict.accepted is True
    assert "on-brand" in verdict.reason.lower()


def test_gate_rejects_below_threshold(monkeypatch) -> None:
    e = _unit_vec(11)
    monkeypatch.setattr(clip_embedder, "embed_image", lambda *_a, **_kw: e)
    expected = float(np.dot(e, _unit_vec(7)))

    verdict = embedding_gate.evaluate("ignored.png", _centroid(threshold=expected + 0.01))

    assert verdict.accepted is False
    assert "below brand threshold" in verdict.reason.lower()
