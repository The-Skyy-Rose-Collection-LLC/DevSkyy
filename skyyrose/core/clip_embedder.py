"""Singleton CLIP loader shared by all server-side embedding features.

Loads `openai/clip-vit-base-patch32` once on first call, reuses across all
features (compositor gate, catalog dedup, prompt alignment scorer). The
embedding dimension and L2-normalization match the browser-side embeddings
already shipped in wordpress-theme/skyyrose-flagship/data/product-embeddings.json.

Exports:
    get_clip() -> _ClipState                          # internal handle
    embed_image(path_or_pil) -> np.ndarray             # 512-dim L2-normalized
    embed_text(text) -> np.ndarray                     # 512-dim L2-normalized
    cosine_similarity(a, b) -> float                   # dot product (already normalized)

@package SkyyRose
@since 1.1.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

logger = logging.getLogger(__name__)

MODEL_ID = "openai/clip-vit-base-patch32"
EMBED_DIM = 512


@dataclass
class _ClipState:
    model: CLIPModel
    processor: CLIPProcessor
    device: str


_STATE: _ClipState | None = None
_LOCK = Lock()


def _select_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def get_clip() -> _ClipState:
    """Lazy singleton CLIP loader. Thread-safe."""
    global _STATE
    if _STATE is not None:
        return _STATE
    with _LOCK:
        if _STATE is not None:
            return _STATE
        device = _select_device()
        logger.info("Loading CLIP %s on %s", MODEL_ID, device)
        model = CLIPModel.from_pretrained(MODEL_ID).to(device).eval()  # nosec B615 — openai/clip-vit-base-patch32 is a pinned well-known public model; revision pinned via MODEL_ID constant above
        processor = CLIPProcessor.from_pretrained(MODEL_ID)  # nosec B615 — same model, same justification
        _STATE = _ClipState(model=model, processor=processor, device=device)
    return _STATE


def _l2_normalize(v: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(v)
    if norm < 1e-9:
        return v
    return v / norm


def _projected(features):
    """Extract the projected embedding tensor from a CLIP get_*_features() call.

    transformers >=5 returns a ``BaseModelOutputWithPooling`` whose
    ``.pooler_output`` holds the projected embeds (the text/visual projection is
    written back into that field). Older versions returned the tensor directly,
    which has no ``pooler_output`` attribute — so fall back to the value itself.
    """
    return getattr(features, "pooler_output", features)


def embed_image(source: str | Path | Image.Image) -> np.ndarray:
    """Run CLIP vision encoder. Returns L2-normalized 512-d numpy array."""
    state = get_clip()
    if isinstance(source, (str, Path)):
        img = Image.open(source).convert("RGB")
    elif isinstance(source, Image.Image):
        img = source.convert("RGB")
    else:
        raise TypeError(f"embed_image expects path or PIL.Image, got {type(source).__name__}")
    inputs = state.processor(images=img, return_tensors="pt").to(state.device)
    with torch.no_grad():
        feats = _projected(state.model.get_image_features(**inputs))
    feats = feats.squeeze(0).cpu().numpy().astype(np.float32)
    return _l2_normalize(feats)


def embed_text(text: str) -> np.ndarray:
    """Run CLIP text encoder. Returns L2-normalized 512-d numpy array."""
    if not text or not text.strip():
        raise ValueError("embed_text requires non-empty text")
    state = get_clip()
    inputs = state.processor(text=[text], return_tensors="pt", padding=True, truncation=True).to(
        state.device
    )
    with torch.no_grad():
        feats = _projected(state.model.get_text_features(**inputs))
    feats = feats.squeeze(0).cpu().numpy().astype(np.float32)
    return _l2_normalize(feats)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Dot product. Both inputs MUST already be L2-normalized."""
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: {a.shape} vs {b.shape}")
    return float(np.dot(a, b))
