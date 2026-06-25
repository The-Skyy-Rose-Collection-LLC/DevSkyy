"""Backward-compatible facade over the unified embeddings package.

The CLIP implementation moved into ``skyyrose.core.embeddings`` (Phase 2,
embeddings reframe): revision-pinned, space-aware, decompression-bomb-guarded,
fd-safe, and deduplicated with DINOv2. This module preserves the historical
module-level function API so existing call sites — and the ``capability.py``
``importlib.import_module`` string-probe — keep working unchanged.

New code should prefer ``skyyrose.core.embeddings.clip.ClipEncoder`` directly.

@package SkyyRose
@since 1.2.0
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

from skyyrose.core.embeddings.clip import ClipEncoder
from skyyrose.core.embeddings.config import get_config

_cfg = get_config()
MODEL_ID = _cfg.clip_model_id
EMBED_DIM = _cfg.clip_dim


@lru_cache(maxsize=1)
def _encoder() -> ClipEncoder:
    """Process-wide lazy CLIP encoder singleton."""
    return ClipEncoder()


def embed_image(source: str | Path | Image.Image) -> np.ndarray:
    """Run CLIP vision encoder. Returns an L2-normalized 512-d float32 array."""
    return _encoder().embed_image(source)


def embed_text(text: str) -> np.ndarray:
    """Run CLIP text encoder. Returns an L2-normalized 512-d float32 array."""
    return _encoder().embed_text(text)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Dot product. Both inputs MUST already be L2-normalized."""
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: {a.shape} vs {b.shape}")
    return float(np.dot(a, b))
