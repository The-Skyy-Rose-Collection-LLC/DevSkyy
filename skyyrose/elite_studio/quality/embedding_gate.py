"""Pre-QA embedding gate: cosine similarity vs brand centroid.

Sits between Compositor stage 5 (shadows) and stage 6 (Gemini visual QA).
If a render's CLIP embedding is too far from the brand centroid, we mark it
failed before paying for Gemini QA. Saves ~$0.025 per rejected render.

Typical brand centroid threshold sits around 0.65-0.75. Tune via
build_brand_centroid.py --threshold-percentile.

@package SkyyRose
@since 1.1.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from skyyrose.core import clip_embedder, dino_embedder
from skyyrose.elite_studio.quality.brand_centroid import BrandCentroid


@dataclass
class GateVerdict:
    accepted: bool
    score: float
    threshold: float
    reason: str


def score_against_centroid(image: Path | str | Image.Image, centroid: BrandCentroid) -> float:
    """Cosine similarity between image embedding and brand centroid.

    Picks the encoder from the centroid's `model_id` so a DINOv2 centroid is
    scored with DINOv2 embeddings (768-d) and a CLIP centroid with CLIP
    embeddings (512-d). Cross-encoder scoring would crash on shape mismatch.
    """
    if "dinov2" in (centroid.model_id or "").lower():
        embedding = dino_embedder.embed_image(image)
    else:
        embedding = clip_embedder.embed_image(image)
    # Both encoders return L2-normalized vectors, so cosine == dot product.
    import numpy as np

    return float(np.dot(embedding, centroid.centroid))


def evaluate(image: Path | str | Image.Image, centroid: BrandCentroid) -> GateVerdict:
    """Decide whether `image` is on-brand enough to proceed to paid QA."""
    score = score_against_centroid(image, centroid)
    if score >= centroid.threshold:
        return GateVerdict(
            accepted=True,
            score=score,
            threshold=centroid.threshold,
            reason=f"on-brand (score {score:.3f} >= threshold {centroid.threshold:.3f})",
        )
    return GateVerdict(
        accepted=False,
        score=score,
        threshold=centroid.threshold,
        reason=(f"below brand threshold (score {score:.3f} < threshold {centroid.threshold:.3f})"),
    )
