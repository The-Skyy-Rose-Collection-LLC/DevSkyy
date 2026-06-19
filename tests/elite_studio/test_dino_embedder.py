"""Tests for skyyrose.core.dino_embedder.

DINOv2 (Meta's self-supervised vision transformer) is a stronger
image-only encoder than CLIP-base for visual similarity tasks. Same
shape (512-d after pooling), L2-normalized for direct cosine comparison.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from skyyrose.core import dino_embedder

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
    vec = dino_embedder.embed_image(red_image)
    assert isinstance(vec, np.ndarray)
    assert vec.ndim == 1
    assert vec.shape[0] >= 384  # DINOv2-base is 768; small variants ~384
    assert pytest.approx(float(np.linalg.norm(vec)), abs=1e-4) == 1.0


def test_self_similarity_is_one(red_image: Path) -> None:
    vec = dino_embedder.embed_image(red_image)
    assert pytest.approx(float(np.dot(vec, vec)), abs=1e-5) == 1.0


def test_different_images_below_one(red_image: Path, blue_image: Path) -> None:
    a = dino_embedder.embed_image(red_image)
    b = dino_embedder.embed_image(blue_image)
    sim = float(np.dot(a, b))
    assert -1.0 <= sim < 1.0


def test_singleton_does_not_reload(red_image: Path) -> None:
    dino_embedder.get_dino()
    state = dino_embedder._STATE
    first_id = id(state.model)
    dino_embedder.embed_image(red_image)
    assert id(state.model) == first_id
