"""Tests for skyyrose.elite_studio.quality.brand_centroid."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from skyyrose.elite_studio.quality import brand_centroid

# CLIP cold-load exceeds the default 10s pytest-timeout. These tests
# are correct but slow; opt out of the fast suite via the `slow` marker
# (excluded by default in pyproject.toml addopts).
pytestmark = pytest.mark.slow


@pytest.fixture
def approved_dir(tmp_path: Path) -> Path:
    d = tmp_path / "approved"
    d.mkdir()
    for i, color in enumerate([(20, 20, 20), (40, 40, 40), (10, 10, 10)]):
        Image.new("RGB", (224, 224), color=color).save(d / f"shot_{i}.png")
    return d


def test_build_centroid_returns_normalized_vector(approved_dir: Path) -> None:
    result = brand_centroid.build_centroid(approved_dir)
    assert result.centroid.shape == (512,)
    assert pytest.approx(float(np.linalg.norm(result.centroid)), abs=1e-4) == 1.0
    assert result.sample_count == 3


def test_build_centroid_records_threshold(approved_dir: Path) -> None:
    result = brand_centroid.build_centroid(approved_dir, threshold_percentile=10)
    # Threshold is the 10th percentile of in-cluster similarities — bounded.
    assert 0.0 < result.threshold < 1.0


def test_save_and_load_centroid_roundtrip(approved_dir: Path, tmp_path: Path) -> None:
    built = brand_centroid.build_centroid(approved_dir)
    out = tmp_path / "centroid.npz"
    brand_centroid.save_centroid(built, out)
    assert out.exists()
    loaded = brand_centroid.load_centroid(out)
    assert np.allclose(loaded.centroid, built.centroid, atol=1e-6)
    assert loaded.threshold == pytest.approx(built.threshold, abs=1e-6)
    assert loaded.sample_count == built.sample_count


def test_build_centroid_empty_dir_raises(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError, match="no image"):
        brand_centroid.build_centroid(empty)
