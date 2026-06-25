"""Fast, model-free tests for brand_centroid save/load IO guards (E-space, E-store).

The companion test_brand_centroid.py is @slow (real CLIP). These exercise
load_centroid's dim guard + corruption handling and the atomic save WITHOUT
loading any model — by writing .npz files directly with np.savez.
"""

from __future__ import annotations

import numpy as np
import pytest

from skyyrose.core.embeddings.errors import EmbeddingError, EmbeddingSpaceMismatch
from skyyrose.elite_studio.quality.brand_centroid import (
    BrandCentroid,
    is_dino_model,
    load_centroid,
    save_centroid,
)


def _unit(n: int) -> np.ndarray:
    v = np.random.default_rng(0).standard_normal(n).astype(np.float32)
    return v / np.linalg.norm(v)


def _write_npz(path, *, centroid, model_id, threshold=0.5, sample_count=3):
    np.savez(
        path,
        centroid=centroid,
        threshold=np.array(threshold, dtype=np.float32),
        sample_count=np.array(sample_count, dtype=np.int64),
        model_id=np.array(model_id),
    )


def test_roundtrip_synthetic(tmp_path):
    c = BrandCentroid(centroid=_unit(512), threshold=0.5, sample_count=3, model_id="test")
    out = tmp_path / "c.npz"
    save_centroid(c, out)
    assert out.exists()
    loaded = load_centroid(out)
    assert loaded.model_id == "test"
    assert loaded.sample_count == 3
    assert loaded.sample_paths == []  # not persisted by design
    np.testing.assert_allclose(loaded.centroid, c.centroid, atol=1e-6)


def test_atomic_save_leaves_no_tmp(tmp_path):
    c = BrandCentroid(centroid=_unit(512), threshold=0.5, sample_count=3, model_id="test")
    out = tmp_path / "c.npz"
    save_centroid(c, out)
    assert out.exists()
    assert not (tmp_path / "c.npz.tmp").exists()  # tmp renamed away atomically


def test_dim_mismatch_dino_label_clip_array_raises(tmp_path):
    out = tmp_path / "bad.npz"
    _write_npz(out, centroid=_unit(512), model_id="facebook/dinov2-base")  # implies 768
    with pytest.raises(EmbeddingSpaceMismatch):
        load_centroid(out)


def test_dim_mismatch_clip_label_dino_array_raises(tmp_path):
    out = tmp_path / "bad.npz"
    _write_npz(out, centroid=_unit(768), model_id="openai/clip-vit-base-patch32")  # implies 512
    with pytest.raises(EmbeddingSpaceMismatch):
        load_centroid(out)


def test_corrupt_npz_raises_embedding_error(tmp_path):
    out = tmp_path / "corrupt.npz"
    out.write_bytes(b"this is not a valid npz archive")
    with pytest.raises(EmbeddingError):
        load_centroid(out)


def test_missing_key_raises_embedding_error(tmp_path):
    out = tmp_path / "partial.npz"
    np.savez(out, centroid=_unit(512))  # no model_id / threshold / sample_count
    with pytest.raises(EmbeddingError):
        load_centroid(out)


def test_synthetic_model_skips_dim_guard(tmp_path):
    # model_id "test" -> _expected_dim None -> any dim loads fine.
    out = tmp_path / "ok.npz"
    _write_npz(out, centroid=_unit(123), model_id="test")
    loaded = load_centroid(out)
    assert loaded.centroid.shape == (123,)


def test_matching_dim_loads(tmp_path):
    out = tmp_path / "good.npz"
    _write_npz(out, centroid=_unit(512), model_id="openai/clip-vit-base-patch32")
    loaded = load_centroid(out)
    assert loaded.centroid.shape == (512,)
    assert loaded.model_id == "openai/clip-vit-base-patch32"


def test_is_dino_model():
    assert is_dino_model("facebook/dinov2-base") is True
    assert is_dino_model("facebook/dino-vitb16") is True
    assert is_dino_model("openai/clip-vit-base-patch32") is False
    assert is_dino_model(None) is False
