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

import numpy as np
from PIL import Image

from skyyrose.core import clip_embedder, dino_embedder
from skyyrose.elite_studio.quality.brand_centroid import BrandCentroid, is_dino_model


@dataclass
class GateVerdict:
    accepted: bool
    score: float
    threshold: float
    reason: str


def score_against_centroid(image: Path | str | Image.Image, centroid: BrandCentroid) -> float:
    """Cosine similarity between image embedding and brand centroid.

    Dispatches the encoder by the centroid's ``model_id`` so a DINOv2 centroid is
    scored with DINOv2 embeddings and a CLIP centroid with CLIP — never
    cross-encoder, which would yield a confident but meaningless cosine
    (E-encoder-gate). Mirrors ``render_quality._score_centroid``.
    """
    if is_dino_model(centroid.model_id):
        embedding = dino_embedder.embed_image(image)
    else:
        embedding = clip_embedder.embed_image(image)
    # Both encoders L2-normalize, so cosine == dot.
    return float(np.dot(embedding, centroid.centroid))


def evaluate(image: Path | str | Image.Image, centroid: BrandCentroid) -> GateVerdict:
    """Decide whether `image` is on-brand enough to proceed to paid QA.

    Emits the verdict score to the token tracker (Track-OBS) so ``EmbeddingObserver`` can
    compute PSI drift over the gate-score distribution. Emission is the single chokepoint
    every gate site funnels through, and never affects the returned verdict.
    """
    score = score_against_centroid(image, centroid)
    if score >= centroid.threshold:
        verdict = GateVerdict(
            accepted=True,
            score=score,
            threshold=centroid.threshold,
            reason=f"on-brand (score {score:.3f} >= threshold {centroid.threshold:.3f})",
        )
    else:
        verdict = GateVerdict(
            accepted=False,
            score=score,
            threshold=centroid.threshold,
            reason=f"below brand threshold (score {score:.3f} < threshold {centroid.threshold:.3f})",
        )
    _emit_gate_score(centroid.model_id, verdict)
    return verdict


def _emit_gate_score(model_id: str, verdict: GateVerdict) -> None:
    """Record the gate verdict's score for PSI-drift observability (Track-OBS).

    Telemetry must NEVER break the gate, so both the import and the call are guarded — the
    verdict is returned regardless of the tracker's availability or failure.
    """
    try:
        from core.token_tracker import record_gate_score

        record_gate_score(
            model=model_id,
            score=verdict.score,
            accepted=verdict.accepted,
            threshold=verdict.threshold,
        )
    except Exception:  # noqa: BLE001 — observability must not affect gating
        pass
