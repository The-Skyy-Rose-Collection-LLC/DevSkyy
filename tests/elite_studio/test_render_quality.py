"""Tests for skyyrose.elite_studio.quality.render_quality.

The combined render gate fuses three signals into a single verdict:
  - Brand centroid cosine similarity (image vs centroid of approved shots)
  - CLIP text-image alignment (prompt vs render)
  - Resolution + file sanity check

Verdict buckets:
  SHIP     — passes both centroid AND alignment thresholds
  REVIEW   — passes centroid but alignment is borderline (human eye welcome)
  KILL     — fails centroid (off-brand by construction; don't ship)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from skyyrose.elite_studio.quality.brand_centroid import BrandCentroid
from skyyrose.elite_studio.quality.render_quality import (
    RenderVerdict,
    Verdict,
    evaluate_render,
)


@pytest.fixture
def fake_centroid(tmp_path: Path) -> Path:
    rng = np.random.default_rng(123)
    v = rng.standard_normal(512).astype(np.float32)
    v = v / np.linalg.norm(v)
    centroid = BrandCentroid(centroid=v, threshold=0.65, sample_count=20, model_id="test")
    out = tmp_path / "centroid.npz"
    from skyyrose.elite_studio.quality.brand_centroid import save_centroid

    save_centroid(centroid, out)
    return out


@pytest.fixture
def render_image(tmp_path: Path) -> Path:
    Image.new("RGB", (512, 512), color=(40, 40, 40)).save(tmp_path / "render.png")
    return tmp_path / "render.png"


def test_evaluate_render_returns_verdict(
    fake_centroid: Path, render_image: Path, monkeypatch
) -> None:
    """Happy path: returns a RenderVerdict with all signals populated."""
    from skyyrose.elite_studio.quality import render_quality

    monkeypatch.setattr(render_quality, "_score_centroid", lambda *_a, **_kw: 0.78)
    monkeypatch.setattr(render_quality, "_score_alignment_safe", lambda *_a, **_kw: 0.32)

    result = evaluate_render(
        render_path=render_image,
        prompt="a black hoodie on a model",
        centroid_path=fake_centroid,
    )
    assert isinstance(result, RenderVerdict)
    assert result.brand_centroid_score == pytest.approx(0.78)
    assert result.alignment_score == pytest.approx(0.32)
    assert result.verdict == Verdict.SHIP


def test_kill_verdict_when_below_centroid_threshold(
    fake_centroid: Path, render_image: Path, monkeypatch
) -> None:
    """Off-brand by construction => KILL regardless of alignment."""
    from skyyrose.elite_studio.quality import render_quality

    monkeypatch.setattr(render_quality, "_score_centroid", lambda *_a, **_kw: 0.40)
    monkeypatch.setattr(render_quality, "_score_alignment_safe", lambda *_a, **_kw: 0.50)

    result = evaluate_render(
        render_path=render_image,
        prompt="a black hoodie on a model",
        centroid_path=fake_centroid,
    )
    assert result.verdict == Verdict.KILL
    assert "below brand threshold" in result.reason.lower()


def test_review_verdict_when_centroid_passes_but_alignment_weak(
    fake_centroid: Path, render_image: Path, monkeypatch
) -> None:
    """On-brand but prompt drift => REVIEW (human eyes wanted)."""
    from skyyrose.elite_studio.quality import render_quality

    monkeypatch.setattr(render_quality, "_score_centroid", lambda *_a, **_kw: 0.80)
    monkeypatch.setattr(render_quality, "_score_alignment_safe", lambda *_a, **_kw: 0.10)

    result = evaluate_render(
        render_path=render_image,
        prompt="a black hoodie on a model",
        centroid_path=fake_centroid,
    )
    assert result.verdict == Verdict.REVIEW
    assert "alignment" in result.reason.lower()


def test_kill_verdict_when_resolution_too_small(fake_centroid: Path, tmp_path: Path) -> None:
    """Tiny renders are KILL — won't look right on the live site."""
    from skyyrose.elite_studio.quality import render_quality

    tiny = tmp_path / "tiny.png"
    Image.new("RGB", (128, 128), color=(40, 40, 40)).save(tiny)

    result = evaluate_render(
        render_path=tiny,
        prompt="a black hoodie on a model",
        centroid_path=fake_centroid,
        min_dimension=512,
    )
    assert result.verdict == Verdict.KILL
    assert "resolution" in result.reason.lower() or "too small" in result.reason.lower()


def test_evaluate_render_with_no_prompt_skips_alignment(
    fake_centroid: Path, render_image: Path, monkeypatch
) -> None:
    """No prompt => alignment is 0.0, verdict driven purely by centroid."""
    from skyyrose.elite_studio.quality import render_quality

    monkeypatch.setattr(render_quality, "_score_centroid", lambda *_a, **_kw: 0.78)

    result = evaluate_render(
        render_path=render_image,
        prompt=None,
        centroid_path=fake_centroid,
    )
    # No prompt => alignment is 0, so SHIP only if alignment_min_threshold is 0,
    # otherwise REVIEW. Either way it's not KILL since centroid is fine.
    assert result.verdict in (Verdict.SHIP, Verdict.REVIEW)
    assert result.alignment_score == 0.0


def test_combined_score_property() -> None:
    """combined_score is a normalized 0..100 number for ranking."""
    v = RenderVerdict(
        verdict=Verdict.SHIP,
        brand_centroid_score=0.85,
        alignment_score=0.30,
        threshold_centroid=0.65,
        threshold_alignment=0.20,
        width=512,
        height=512,
        reason="ship",
    )
    # Combined = 60% centroid + 40% alignment, both scaled to 0..100.
    # 0.85 * 100 * 0.6 + 0.30 * 100 * 0.4 = 51 + 12 = 63
    assert v.combined_score == pytest.approx(63.0, abs=0.01)
