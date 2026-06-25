"""ClipEncoder: verifies revision/dtype/safetensors are actually passed to
from_pretrained (E-revpin, E-determinism) and that encode normalizes — all
model-free by monkeypatching transformers' loaders. No HF download."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from skyyrose.core.embeddings import clip as clip_mod
from skyyrose.core.embeddings.clip import ClipEncoder
from skyyrose.core.embeddings.config import EmbeddingConfig
from skyyrose.core.embeddings.device import dtype_load_kwargs
from skyyrose.core.embeddings.errors import EmbedError


class _Batch(dict):
    def to(self, device):  # processor output already a dict; **inputs unpacks it
        return self


class _FakeProcessor:
    def __call__(self, images=None, text=None, return_tensors=None, **kw):
        if images is not None:
            n = len(images) if isinstance(images, list) else 1
            return _Batch({"pixel_values": torch.zeros(n, 3, 4, 4)})
        n = len(text) if isinstance(text, list) else 1
        return _Batch({"input_ids": torch.zeros(n, 5, dtype=torch.long)})


class _FakeClipModel:
    dim = 512

    def to(self, device):
        return self

    def eval(self):
        return self

    def get_image_features(self, **inputs):
        n = inputs["pixel_values"].shape[0]
        # distinct non-zero rows so normalization is well-defined
        return torch.arange(1, n * self.dim + 1, dtype=torch.float32).reshape(n, self.dim)

    def get_text_features(self, **inputs):
        n = inputs["input_ids"].shape[0]
        return torch.full((n, self.dim), 2.0, dtype=torch.float32)


@pytest.fixture
def patched(monkeypatch):
    calls: dict[str, dict] = {}

    def fake_model_fp(model_id, **kwargs):
        calls["model"] = {"model_id": model_id, **kwargs}
        return _FakeClipModel()

    def fake_proc_fp(model_id, **kwargs):
        calls["proc"] = {"model_id": model_id, **kwargs}
        return _FakeProcessor()

    monkeypatch.setattr(clip_mod.CLIPModel, "from_pretrained", fake_model_fp)
    monkeypatch.setattr(clip_mod.CLIPProcessor, "from_pretrained", fake_proc_fp)
    return calls


def test_space_matches_config():
    enc = ClipEncoder(EmbeddingConfig())
    assert enc.space.dim == 512
    assert enc.space.model_id == "openai/clip-vit-base-patch32"
    assert enc.space.revision == "3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268"


def test_load_passes_pinned_revision_safetensors_dtype(patched):
    enc = ClipEncoder(EmbeddingConfig())
    enc.embed_image(_img())
    model_call = patched["model"]
    assert model_call["revision"] == "3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268"
    # CLIP ships only pytorch_model.bin at the pinned SHA -> cannot force safetensors.
    assert model_call["use_safetensors"] is False
    # E-determinism: the dtype kwarg is passed; its NAME is version-dependent
    # ("dtype" on transformers >=5, "torch_dtype" on 4.x), so derive it from the
    # same helper the loader uses instead of hardcoding the v5 name.
    dtype_key = next(iter(dtype_load_kwargs(torch.float32)))
    assert model_call[dtype_key] == torch.float32
    # Processor is pinned to the same revision.
    assert patched["proc"]["revision"] == "3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268"


def test_embed_image_normalized_512(patched):
    enc = ClipEncoder(EmbeddingConfig())
    vec = enc.embed_image(_img())
    assert vec.shape == (512,)
    np.testing.assert_allclose(np.linalg.norm(vec), 1.0, atol=1e-5)


def test_embed_text_normalized_512(patched):
    enc = ClipEncoder(EmbeddingConfig())
    vec = enc.embed_text("rose gold hoodie")
    assert vec.shape == (512,)
    np.testing.assert_allclose(np.linalg.norm(vec), 1.0, atol=1e-5)


def test_embed_text_rejects_empty(patched):
    enc = ClipEncoder(EmbeddingConfig())
    with pytest.raises(EmbedError):
        enc.embed_text("   ")


def test_batch_one_forward_pass(patched):
    enc = ClipEncoder(EmbeddingConfig())
    out = enc.embed_images([_img(), _img(), _img()], batch_size=8)
    assert out.shape == (3, 512)


def _img():
    from PIL import Image

    return Image.new("RGB", (4, 4), (1, 2, 3))
