"""device: select_device, resolve_dtype, dtype_load_kwargs.

Model-free: queries torch availability + dtype mapping only, never loads a model."""

from __future__ import annotations

import pytest
import torch

from skyyrose.core.embeddings.device import dtype_load_kwargs, resolve_dtype, select_device
from skyyrose.core.embeddings.errors import EmbedError


def test_returns_valid_device_string():
    assert select_device() in {"cuda", "mps", "cpu"}


def test_resolve_dtype_valid():
    assert resolve_dtype("float32") is torch.float32
    assert resolve_dtype("float16") is torch.float16


def test_resolve_dtype_unknown_raises():
    with pytest.raises(EmbedError):
        resolve_dtype("not_a_dtype")


def test_resolve_dtype_rejects_non_dtype_attr():
    # torch.nn exists but is a module, not a dtype — must still fail loudly.
    with pytest.raises(EmbedError):
        resolve_dtype("nn")


def test_dtype_load_kwargs_picks_one_name():
    kw = dtype_load_kwargs(torch.float32)
    # Exactly one of the two kwarg names is present (version-dependent), value pinned.
    assert ("dtype" in kw) ^ ("torch_dtype" in kw)
    assert list(kw.values()) == [torch.float32]
