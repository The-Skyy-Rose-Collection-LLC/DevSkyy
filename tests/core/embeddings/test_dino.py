"""DinoEncoder: revision/dtype/safetensors wiring + CLS-token extraction, model-free."""

from __future__ import annotations

import numpy as np
import pytest
import torch
from PIL import Image

# Skip these tests if torchvision is unavailable (transformers AutoImageProcessor requires it)
pytest.importorskip("torchvision")

from transformers import AutoImageProcessor, AutoModel

from skyyrose.core.embeddings.config import EmbeddingConfig
from skyyrose.core.embeddings.device import dtype_load_kwargs
from skyyrose.core.embeddings.dino import DinoEncoder


class _Batch(dict):
    def to(self, device):
        return self


class _FakeProcessor:
    def __call__(self, images=None, return_tensors=None, **kw):
        n = len(images) if isinstance(images, list) else 1
        return _Batch({"pixel_values": torch.zeros(n, 3, 4, 4)})


class _FakeOutput:
    def __init__(self, t):
        self.last_hidden_state = t


class _FakeDinoModel:
    def to(self, device):
        return self

    def eval(self):
        return self

    def __call__(self, **inputs):
        n = inputs["pixel_values"].shape[0]
        # seq len 5, dim 768; CLS at position 0 set to a distinct non-zero value
        t = torch.zeros(n, 5, 768)
        t[:, 0, :] = torch.arange(1, n * 768 + 1, dtype=torch.float32).reshape(n, 768)
        return _FakeOutput(t)


@pytest.fixture
def patched(monkeypatch):
    calls: dict[str, dict] = {}

    def fake_model_fp(model_id, **kwargs):
        calls["model"] = {"model_id": model_id, **kwargs}
        return _FakeDinoModel()

    def fake_proc_fp(model_id, **kwargs):
        calls["proc"] = {"model_id": model_id, **kwargs}
        return _FakeProcessor()

    monkeypatch.setattr(AutoModel, "from_pretrained", fake_model_fp)
    monkeypatch.setattr(AutoImageProcessor, "from_pretrained", fake_proc_fp)
    return calls


def _img():
    return Image.new("RGB", (4, 4), (1, 2, 3))


def test_space_matches_config():
    enc = DinoEncoder(EmbeddingConfig())
    assert enc.space.dim == 768
    assert enc.space.model_id == "facebook/dinov2-base"
    assert enc.space.revision == "f9e44c814b77203eaa57a6bdbbd535f21ede1415"


def test_load_passes_pinned_revision_safetensors_dtype(patched):
    enc = DinoEncoder(EmbeddingConfig())
    enc.embed_image(_img())
    assert patched["model"]["revision"] == "f9e44c814b77203eaa57a6bdbbd535f21ede1415"
    assert patched["model"]["use_safetensors"] is True
    dtype_key = next(iter(dtype_load_kwargs(torch.float32)))
    assert patched["model"][dtype_key] == torch.float32
    assert patched["proc"]["revision"] == "f9e44c814b77203eaa57a6bdbbd535f21ede1415"


def test_embed_image_normalized_768(patched):
    enc = DinoEncoder(EmbeddingConfig())
    vec = enc.embed_image(_img())
    assert vec.shape == (768,)
    np.testing.assert_allclose(np.linalg.norm(vec), 1.0, atol=1e-5)


def test_batch_shape(patched):
    enc = DinoEncoder(EmbeddingConfig())
    out = enc.embed_images([_img(), _img()], batch_size=8)
    assert out.shape == (2, 768)
