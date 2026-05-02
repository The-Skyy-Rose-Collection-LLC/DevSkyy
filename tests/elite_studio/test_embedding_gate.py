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


def test_score_returns_cosine_in_range(fake_centroid: BrandCentroid, render_image: Path) -> None:
    score = embedding_gate.score_against_centroid(render_image, fake_centroid)
    assert -1.0 <= score <= 1.0


def test_evaluate_accepts_when_above_threshold(
    fake_centroid: BrandCentroid, render_image: Path, monkeypatch
) -> None:
    monkeypatch.setattr(embedding_gate, "score_against_centroid", lambda *_a, **_kw: 0.80)
    verdict = embedding_gate.evaluate(render_image, fake_centroid)
    assert verdict.accepted is True
    assert verdict.score == pytest.approx(0.80)
    assert verdict.threshold == pytest.approx(0.65)


def test_evaluate_rejects_below_threshold(
    fake_centroid: BrandCentroid, render_image: Path, monkeypatch
) -> None:
    monkeypatch.setattr(embedding_gate, "score_against_centroid", lambda *_a, **_kw: 0.40)
    verdict = embedding_gate.evaluate(render_image, fake_centroid)
    assert verdict.accepted is False
    assert "below" in verdict.reason.lower()
