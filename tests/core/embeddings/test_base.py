"""BaseEncoder: lazy load, fd-safe RGB decode, L2-norm, batching, bomb-guard.

Uses a model-free FakeEncoder so the whole base contract is exercised in CI
without ever downloading CLIP/DINOv2 (HF Hub 429 is the historical CI killer)."""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from skyyrose.core.embeddings import base as base_mod
from skyyrose.core.embeddings.base import BaseEncoder
from skyyrose.core.embeddings.config import get_config
from skyyrose.core.embeddings.errors import EmbedError, ZeroNormEmbeddingError
from skyyrose.core.embeddings.space import EmbeddingSpace


class FakeEncoder(BaseEncoder):
    """Deterministic 4-d encoder: vector = [width, height, 1, 0]. No model."""

    def __init__(self, config=None):
        super().__init__(config)
        self.load_calls = 0
        self.encode_calls = 0

    def _build_space(self) -> EmbeddingSpace:
        return EmbeddingSpace("fake/encoder", 4, "v1")

    def _load(self, device: str):
        self.load_calls += 1
        return ("model", "processor")

    def _encode_pils(self, images):
        self.encode_calls += 1
        return np.array(
            [[float(im.width), float(im.height), 1.0, 0.0] for im in images], dtype=np.float32
        )


class ZeroEncoder(FakeEncoder):
    """Always returns a zero vector — exercises the zero-norm guard."""

    def _encode_pils(self, images):
        return np.zeros((len(images), 4), dtype=np.float32)


def _img(w=8, h=8) -> Image.Image:
    return Image.new("RGB", (w, h), (10, 20, 30))


def test_bomb_guard_set_at_import():
    assert get_config().max_image_pixels == Image.MAX_IMAGE_PIXELS
    # Prove it's an actual cap, not a coincidental match: below PIL's ~89M default.
    assert Image.MAX_IMAGE_PIXELS < 89_478_485


def test_embed_image_returns_normalized_vector():
    enc = FakeEncoder()
    vec = enc.embed_image(_img(3, 4))
    assert vec.shape == (4,)
    assert vec.dtype == np.float32
    np.testing.assert_allclose(np.linalg.norm(vec), 1.0, atol=1e-6)
    # Direction preserved: raw [3,4,1,0] normalized.
    expected = np.array([3, 4, 1, 0], dtype=np.float32)
    np.testing.assert_allclose(vec, expected / np.linalg.norm(expected), atol=1e-6)


def test_lazy_load_once():
    enc = FakeEncoder()
    assert enc.load_calls == 0  # not loaded until first embed
    enc.embed_image(_img())
    enc.embed_image(_img())
    assert enc.load_calls == 1  # loaded exactly once


def test_embed_images_batches_in_one_forward_pass_per_chunk():
    enc = FakeEncoder()
    out = enc.embed_images([_img(1, 1), _img(2, 2), _img(3, 3)], batch_size=10)
    assert out.shape == (3, 4)
    assert enc.encode_calls == 1  # single chunk → single forward pass


def test_embed_images_chunks_by_batch_size():
    enc = FakeEncoder()
    enc.embed_images([_img() for _ in range(5)], batch_size=2)
    assert enc.encode_calls == 3  # ceil(5/2)


def test_embed_images_rejects_empty():
    with pytest.raises(EmbedError):
        FakeEncoder().embed_images([])


def test_embed_images_rejects_bad_batch_size():
    with pytest.raises(EmbedError):
        FakeEncoder().embed_images([_img()], batch_size=0)


def test_open_missing_file_raises_embed_error(tmp_path):
    enc = FakeEncoder()
    with pytest.raises(EmbedError, match="not found"):
        enc.embed_image(tmp_path / "nope.png")


def test_open_corrupt_file_raises_embed_error(tmp_path):
    bad = tmp_path / "bad.png"
    bad.write_text("this is not a PNG")
    enc = FakeEncoder()
    with pytest.raises(EmbedError):
        enc.embed_image(bad)


def test_open_wrong_type_raises_embed_error():
    enc = FakeEncoder()
    with pytest.raises(EmbedError, match="expected path or PIL"):
        enc.embed_image(12345)  # type: ignore[arg-type]


def test_zero_norm_raises():
    enc = ZeroEncoder()
    with pytest.raises(ZeroNormEmbeddingError):
        enc.embed_image(_img())


def test_path_and_pil_round_trip(tmp_path):
    p = tmp_path / "x.png"
    _img(5, 6).save(p)
    enc = FakeEncoder()
    from_path = enc.embed_image(p)
    from_pil = enc.embed_image(_img(5, 6))
    np.testing.assert_allclose(from_path, from_pil, atol=1e-6)


def test_cosine_similarity_shape_guard():
    enc = FakeEncoder()
    with pytest.raises(EmbedError, match="shape mismatch"):
        enc.cosine_similarity(np.zeros(4), np.zeros(3))


def test_cosine_of_identical_normalized_is_one():
    enc = FakeEncoder()
    v = enc.embed_image(_img())
    np.testing.assert_allclose(enc.cosine_similarity(v, v), 1.0, atol=1e-6)


def test_base_encoder_is_abstract():
    with pytest.raises(TypeError):
        BaseEncoder()  # type: ignore[abstract]


def test_module_exports_image_source_alias():
    assert hasattr(base_mod, "ImageSource")
