"""Tests for skyyrose.elite_studio.quality.embedding_gate."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from skyyrose.elite_studio.quality import embedding_gate
from skyyrose.elite_studio.quality.brand_centroid import BrandCentroid


@pytest.fixture
def fake_centroid() -> BrandCentroid:
    rng = np.random.default_rng(42)
    raw = rng.standard_normal(512).astype(np.float32)
    centroid = raw / np.linalg.norm(raw)
    return BrandCentroid(centroid=centroid, threshold=0.65, sample_count=10, model_id="test")


@pytest.fixture
def render_image(tmp_path: Path) -> Path:
    Image.new("RGB", (224, 224), color=(30, 30, 30)).save(tmp_path / "render.png")
    return tmp_path / "render.png"


@pytest.mark.integration
def test_score_returns_cosine_in_range(fake_centroid: BrandCentroid, render_image: Path) -> None:
    score = embedding_gate.score_against_centroid(render_image, fake_centroid)
    assert -1.0 <= score <= 1.0


@pytest.mark.unit
def test_evaluate_accepts_when_above_threshold(
    fake_centroid: BrandCentroid, render_image: Path, monkeypatch
) -> None:
    monkeypatch.setattr(embedding_gate, "score_against_centroid", lambda *_a, **_kw: 0.80)
    verdict = embedding_gate.evaluate(render_image, fake_centroid)
    assert verdict.accepted is True
    assert verdict.score == pytest.approx(0.80)
    assert verdict.threshold == pytest.approx(0.65)


@pytest.mark.unit
def test_evaluate_rejects_below_threshold(
    fake_centroid: BrandCentroid, render_image: Path, monkeypatch
) -> None:
    monkeypatch.setattr(embedding_gate, "score_against_centroid", lambda *_a, **_kw: 0.40)
    verdict = embedding_gate.evaluate(render_image, fake_centroid)
    assert verdict.accepted is False
    assert "below" in verdict.reason.lower()


@pytest.mark.unit
def test_evaluate_emits_gate_score_to_tracker(
    fake_centroid: BrandCentroid, render_image: Path, monkeypatch
) -> None:
    # Track-OBS: every evaluate records its verdict score for PSI-drift observability.
    from core import token_tracker

    monkeypatch.setattr(embedding_gate, "score_against_centroid", lambda *_a, **_kw: 0.80)
    token_tracker.get_token_tracker().clear()
    embedding_gate.evaluate(render_image, fake_centroid)
    assert token_tracker.gate_scores() == [pytest.approx(0.80)]
    row = token_tracker.get_token_tracker().records()[-1]
    assert row.task_type is token_tracker.TaskType.GATE
    assert row.model == "test"  # centroid.model_id
    assert row.metadata["accepted"] is True
    assert row.metadata["threshold"] == pytest.approx(0.65)


@pytest.mark.unit
def test_evaluate_telemetry_failure_does_not_break_gate(
    fake_centroid: BrandCentroid, render_image: Path, monkeypatch
) -> None:
    # A broken tracker must never break the gate verdict.
    from core import token_tracker

    monkeypatch.setattr(embedding_gate, "score_against_centroid", lambda *_a, **_kw: 0.80)
    monkeypatch.setattr(
        token_tracker,
        "record_gate_score",
        lambda **_k: (_ for _ in ()).throw(RuntimeError("telemetry down")),
    )
    verdict = embedding_gate.evaluate(render_image, fake_centroid)
    assert verdict.accepted is True and verdict.score == pytest.approx(0.80)
