"""Tests for skyyrose.core.clip_embedder."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from skyyrose.core import clip_embedder

# Network/model-download integration tests — these pull CLIP/DINO weights from
# HF Hub at runtime. Excluded from the fast gate (CI runs `-m "not slow and not
# integration"`) so a transient HF outage cannot flake main red; run on demand
# with `-m integration`.
pytestmark = pytest.mark.integration


@pytest.fixture
def red_image(tmp_path: Path) -> Path:
    img = Image.new("RGB", (224, 224), color=(220, 20, 20))
    p = tmp_path / "red.png"
    img.save(p)
    return p


@pytest.fixture
def blue_image(tmp_path: Path) -> Path:
    img = Image.new("RGB", (224, 224), color=(20, 20, 220))
    p = tmp_path / "blue.png"
    img.save(p)
    return p


def test_embed_image_returns_normalized_vector(red_image: Path) -> None:
    vec = clip_embedder.embed_image(red_image)
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (512,)
    assert pytest.approx(float(np.linalg.norm(vec)), abs=1e-4) == 1.0


def test_embed_text_returns_normalized_vector() -> None:
    vec = clip_embedder.embed_text("a black hoodie on a moody street")
    assert vec.shape == (512,)
    assert pytest.approx(float(np.linalg.norm(vec)), abs=1e-4) == 1.0


def test_cosine_similarity_self_is_one(red_image: Path) -> None:
    vec = clip_embedder.embed_image(red_image)
    assert pytest.approx(clip_embedder.cosine_similarity(vec, vec), abs=1e-5) == 1.0


def test_cosine_similarity_different_images_below_one(red_image: Path, blue_image: Path) -> None:
    a = clip_embedder.embed_image(red_image)
    b = clip_embedder.embed_image(blue_image)
    sim = clip_embedder.cosine_similarity(a, b)
    assert -1.0 <= sim < 1.0


def test_singleton_does_not_reload_model(red_image: Path) -> None:
    clip_embedder.get_clip()
    state = clip_embedder._STATE  # internal access for test only
    first_model_id = id(state.model)
    clip_embedder.embed_image(red_image)
    assert id(state.model) == first_model_id
