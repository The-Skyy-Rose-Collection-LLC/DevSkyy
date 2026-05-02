"""Tests for skyyrose.elite_studio.quality.clip_alignment."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from skyyrose.elite_studio.quality import clip_alignment


@pytest.fixture
def red_circle_image(tmp_path: Path) -> Path:
    img = Image.new("RGB", (224, 224), color="white")
    draw = ImageDraw.Draw(img)
    draw.ellipse((40, 40, 184, 184), fill="red")
    p = tmp_path / "red_circle.png"
    img.save(p)
    return p


def test_score_alignment_returns_float_in_range(red_circle_image: Path) -> None:
    score = clip_alignment.score_alignment("a red circle on a white background", red_circle_image)
    assert -1.0 <= score <= 1.0


def test_aligned_prompt_scores_higher_than_misaligned(red_circle_image: Path) -> None:
    aligned = clip_alignment.score_alignment("a red circle on a white background", red_circle_image)
    misaligned = clip_alignment.score_alignment(
        "a green triangle on a black background", red_circle_image
    )
    assert aligned > misaligned


def test_score_batch_returns_one_score_per_prompt(red_circle_image: Path) -> None:
    scores = clip_alignment.score_alignment_batch(
        ["a red circle", "a red shape", "a blue square"],
        red_circle_image,
    )
    assert len(scores) == 3
    # red circle prompt closer to red circle than blue square
    assert scores[0] >= scores[2]
