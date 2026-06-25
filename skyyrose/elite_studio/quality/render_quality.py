"""Combined render quality gate — fuses brand centroid + CLIP alignment.

This is the production decision module: given a candidate render of a
SkyyRose product, return a verdict (SHIP / REVIEW / KILL) plus the
underlying scores so reviewers can sort and triage at scale.

Why three signals fused into one verdict:
  - Brand centroid (image vs centroid):  the *most reliable* signal.
    CLIP-base recognizes visual style cues (lighting, color palette,
    subject framing) very well. Calibrated against your own approved
    hero shots, this discriminates "looks like a SkyyRose product
    photo" from "looks like a generic AI render."

  - CLIP text-image alignment:           a *secondary* signal. Useful
    as a tiebreaker but unreliable in isolation (CLIP-base has weak
    grounding for brand-specific iconography — see prompt_simplifier
    docstring for empirical findings).

  - Resolution sanity:                   a *cheap* hard gate. Renders
    below 512px on the short side won't look right on the live site
    regardless of CLIP score.

@package SkyyRose
@since 1.1.0
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from PIL import Image

from skyyrose.core import clip_embedder, dino_embedder
from skyyrose.elite_studio.quality.brand_centroid import (
    BrandCentroid,
    is_dino_model,
    load_centroid,
)


class Verdict(StrEnum):
    SHIP = "ship"  # Pass both gates — ready for production.
    REVIEW = "review"  # On-brand but alignment uncertain — human eye wanted.
    KILL = "kill"  # Off-brand or broken — do not ship.


@dataclass
class RenderVerdict:
    """Single render's quality verdict with all underlying signals."""

    verdict: Verdict
    brand_centroid_score: float  # 0..1 cosine vs brand centroid
    alignment_score: float  # 0..1 CLIP text-image cosine
    threshold_centroid: float  # the centroid threshold this render was tested against
    threshold_alignment: float  # the alignment threshold this render was tested against
    width: int
    height: int
    reason: str

    @property
    def combined_score(self) -> float:
        """0..100 single number for ranking. 60% centroid + 40% alignment.

        Centroid weighted more because it's the more reliable signal.
        """
        return 100.0 * (0.60 * self.brand_centroid_score + 0.40 * self.alignment_score)

    def to_dict(self) -> dict:
        return {
            "verdict": str(self.verdict),
            "brand_centroid_score": round(self.brand_centroid_score, 4),
            "alignment_score": round(self.alignment_score, 4),
            "combined_score": round(self.combined_score, 2),
            "threshold_centroid": round(self.threshold_centroid, 4),
            "threshold_alignment": round(self.threshold_alignment, 4),
            "width": self.width,
            "height": self.height,
            "reason": self.reason,
        }


def _score_centroid(image: Path | Image.Image, centroid: BrandCentroid) -> float:
    """Cosine vs brand centroid. Module-level so tests can monkeypatch.

    Picks the encoder from the centroid's `model_id` so a DINOv2 centroid
    is scored with DINOv2 embeddings and a CLIP centroid with CLIP
    embeddings — never cross-encoder (would be meaningless).
    """
    if is_dino_model(centroid.model_id):
        embedding = dino_embedder.embed_image(image)
    else:
        embedding = clip_embedder.embed_image(image)
    # Both encoders L2-normalize, so cosine == dot.
    import numpy as np

    return float(np.dot(embedding, centroid.centroid))


def _score_alignment_safe(prompt: str, image: Path | Image.Image) -> float:
    """CLIP text-image cosine. Returns 0.0 on any failure (graceful)."""
    if not prompt or not prompt.strip():
        return 0.0
    try:
        text_vec = clip_embedder.embed_text(prompt)
        image_vec = clip_embedder.embed_image(image)
        return float(clip_embedder.cosine_similarity(text_vec, image_vec))
    except Exception:
        return 0.0


def evaluate_render(
    render_path: str | Path,
    prompt: str | None,
    centroid_path: str | Path,
    *,
    min_dimension: int = 512,
    alignment_threshold: float = 0.20,
) -> RenderVerdict:
    """Score a render and return a verdict.

    Args:
        render_path: Path to the candidate render (PNG/JPG/WebP).
        prompt: Original generation prompt. None => alignment scored as 0.0.
        centroid_path: Path to the brand centroid .npz file.
        min_dimension: Minimum width AND height required for SHIP. Below
            this is hard-KILL regardless of CLIP scores.
        alignment_threshold: Below this, verdict downgrades to REVIEW even
            if centroid passes.

    Verdict logic:
        1. If image dimensions < min_dimension on either axis  -> KILL
        2. If brand centroid score < centroid.threshold        -> KILL
        3. If alignment score < alignment_threshold            -> REVIEW
        4. Otherwise                                            -> SHIP
    """
    centroid = load_centroid(Path(centroid_path))

    img = Image.open(render_path).convert("RGB")
    width, height = img.size

    # Hard gate: resolution.
    if width < min_dimension or height < min_dimension:
        return RenderVerdict(
            verdict=Verdict.KILL,
            brand_centroid_score=0.0,
            alignment_score=0.0,
            threshold_centroid=centroid.threshold,
            threshold_alignment=alignment_threshold,
            width=width,
            height=height,
            reason=f"resolution {width}x{height} below minimum {min_dimension}px",
        )

    centroid_score = _score_centroid(img, centroid)
    alignment_score = _score_alignment_safe(prompt or "", img)

    if centroid_score < centroid.threshold:
        verdict = Verdict.KILL
        reason = f"below brand threshold (centroid {centroid_score:.3f} < {centroid.threshold:.3f})"
    elif alignment_score < alignment_threshold:
        verdict = Verdict.REVIEW
        reason = (
            f"on-brand but alignment weak "
            f"(alignment {alignment_score:.3f} < {alignment_threshold:.3f})"
        )
    else:
        verdict = Verdict.SHIP
        reason = (
            f"on-brand and aligned "
            f"(centroid {centroid_score:.3f} >= {centroid.threshold:.3f}, "
            f"alignment {alignment_score:.3f} >= {alignment_threshold:.3f})"
        )

    return RenderVerdict(
        verdict=verdict,
        brand_centroid_score=centroid_score,
        alignment_score=alignment_score,
        threshold_centroid=centroid.threshold,
        threshold_alignment=alignment_threshold,
        width=width,
        height=height,
        reason=reason,
    )
