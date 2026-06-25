"""Backward-compatible facade over the unified embeddings package.

The DINOv2 implementation moved into ``skyyrose.core.embeddings`` (Phase 2,
embeddings reframe): revision-pinned, space-aware, decompression-bomb-guarded,
fd-safe, and deduplicated with CLIP. This module preserves the historical
module-level function API so existing call sites — and the ``capability.py``
``importlib.import_module`` string-probe — keep working unchanged.

New code should prefer ``skyyrose.core.embeddings.dino.DinoEncoder`` directly.

@package SkyyRose
@since 1.2.0
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

from skyyrose.core.embeddings.config import get_config
from skyyrose.core.embeddings.dino import DinoEncoder

_cfg = get_config()
MODEL_ID = _cfg.dino_model_id
EMBED_DIM = _cfg.dino_dim


@lru_cache(maxsize=1)
def _encoder() -> DinoEncoder:
    """Process-wide lazy DINOv2 encoder singleton."""
    return DinoEncoder()


def embed_image(source: str | Path | Image.Image) -> np.ndarray:
    """Run DINOv2 vision encoder. Returns an L2-normalized 768-d CLS-token array."""
    return _encoder().embed_image(source)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Dot product of two L2-normalized DINOv2 vectors."""
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: {a.shape} vs {b.shape}")
    return float(np.dot(a, b))
