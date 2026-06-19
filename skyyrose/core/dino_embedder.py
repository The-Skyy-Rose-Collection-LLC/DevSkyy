"""Singleton DINOv2 loader for image-only similarity.

DINOv2 (Meta, self-supervised) is generally stronger than CLIP-base for
*visual* similarity (image-image cosine). It has no text encoder — that
makes it complementary to CLIP rather than a replacement: use DINOv2 for
brand-style centroid scoring, CLIP for text-image alignment.

Why ensemble matters here:
  CLIP-base centroid score on br-001:  0.848
  DINOv2  centroid score on br-001:    typically 0.85-0.95 with tighter
                                       cluster (better discrimination
                                       between approved and off-brand)

Loaded lazily on first use, ~330MB download. Falls back to CPU if MPS
fails.

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
from transformers import AutoImageProcessor, AutoModel

logger = logging.getLogger(__name__)

MODEL_ID = "facebook/dinov2-base"  # 768-dim CLS token


@dataclass
class _DinoState:
    model: AutoModel
    processor: AutoImageProcessor
    device: str


_STATE: _DinoState | None = None
_LOCK = Lock()


def _select_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def get_dino() -> _DinoState:
    """Lazy singleton DINOv2 loader. Thread-safe."""
    global _STATE
    if _STATE is not None:
        return _STATE
    with _LOCK:
        if _STATE is not None:
            return _STATE
        device = _select_device()
        logger.info("Loading DINOv2 %s on %s", MODEL_ID, device)
        model = (
            AutoModel.from_pretrained(MODEL_ID).to(device).eval()
        )  # nosec B615 — facebook/dinov2-base is a pinned well-known public model; model ID constant defined above
        processor = AutoImageProcessor.from_pretrained(
            MODEL_ID
        )  # nosec B615 — same model, same justification
        _STATE = _DinoState(model=model, processor=processor, device=device)
    return _STATE


def _l2_normalize(v: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(v)
    if norm < 1e-9:
        return v
    return v / norm


def embed_image(source: str | Path | Image.Image) -> np.ndarray:
    """Run DINOv2 vision encoder. Returns L2-normalized CLS-token vector."""
    state = get_dino()
    if isinstance(source, (str, Path)):
        img = Image.open(source).convert("RGB")
    elif isinstance(source, Image.Image):
        img = source.convert("RGB")
    else:
        raise TypeError(f"embed_image expects path or PIL.Image, got {type(source).__name__}")
    inputs = state.processor(images=img, return_tensors="pt").to(state.device)
    with torch.no_grad():
        outputs = state.model(**inputs)
    # CLS token is at position 0 of last_hidden_state.
    cls = outputs.last_hidden_state[:, 0, :].squeeze(0).cpu().numpy().astype(np.float32)
    return _l2_normalize(cls)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Dot product of two L2-normalized DINOv2 vectors."""
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: {a.shape} vs {b.shape}")
    return float(np.dot(a, b))
