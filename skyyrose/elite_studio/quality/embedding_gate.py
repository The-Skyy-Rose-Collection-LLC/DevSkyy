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

from skyyrose.core import clip_embedder
from skyyrose.elite_studio.quality.brand_centroid import BrandCentroid


@dataclass
class GateVerdict:
    accepted: bool
    score: float
    threshold: float
    reason: str


def score_against_centroid(image: Path | str | Image.Image, centroid: BrandCentroid) -> float:
    """Cosine similarity between image embedding and brand centroid."""
    embedding = clip_embedder.embed_image(image)
    return clip_embedder.cosine_similarity(embedding, centroid.centroid)


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
