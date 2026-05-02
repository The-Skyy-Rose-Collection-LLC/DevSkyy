"""Brand-style centroid: mean CLIP embedding of approved hero shots.

The compositor pre-QA gate scores each new render's cosine similarity to
this centroid. A shot far from the centroid is off-brand and skipped before
the paid Gemini QA stage.

@package SkyyRose
@since 1.1.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from skyyrose.core import clip_embedder

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


@dataclass
class BrandCentroid:
    centroid: np.ndarray  # (512,) L2-normalized
    threshold: float  # cosine score below which renders fail the gate
    sample_count: int  # number of approved images that built it
    model_id: str  # CLIP model used (for compatibility checking)


def _list_images(directory: Path) -> list[Path]:
    return sorted(p for p in directory.iterdir() if p.suffix.lower() in IMAGE_EXTS)


def build_centroid(approved_dir: Path, threshold_percentile: float = 10.0) -> BrandCentroid:
    """Compute centroid + a robust threshold from approved hero shots.

    Threshold is the `threshold_percentile`-th percentile of in-cluster
    cosine similarities (each approved image vs centroid). Setting it to
    10 means we accept renders at least as similar to the centroid as 90%
    of our approved set already is.
    """
    paths = _list_images(approved_dir)
    if not paths:
        raise ValueError(f"no image files in {approved_dir}")

    embeddings = np.stack([clip_embedder.embed_image(p) for p in paths])
    raw_centroid = embeddings.mean(axis=0)
    norm = np.linalg.norm(raw_centroid)
    if norm < 1e-9:
        raise ValueError("degenerate centroid (zero magnitude)")
    centroid = (raw_centroid / norm).astype(np.float32)

    # In-cluster similarity distribution -> robust threshold.
    sims = embeddings @ centroid
    threshold = float(np.percentile(sims, threshold_percentile))

    return BrandCentroid(
        centroid=centroid,
        threshold=threshold,
        sample_count=len(paths),
        model_id=clip_embedder.MODEL_ID,
    )


def save_centroid(c: BrandCentroid, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        path,
        centroid=c.centroid,
        threshold=np.array(c.threshold, dtype=np.float32),
        sample_count=np.array(c.sample_count, dtype=np.int64),
        model_id=np.array(c.model_id),
    )


def load_centroid(path: Path) -> BrandCentroid:
    data = np.load(path, allow_pickle=False)
    return BrandCentroid(
        centroid=data["centroid"],
        threshold=float(data["threshold"]),
        sample_count=int(data["sample_count"]),
        model_id=str(data["model_id"]),
    )
