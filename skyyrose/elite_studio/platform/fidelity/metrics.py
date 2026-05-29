"""Visible-face fidelity metric: compose DINOv2 + CLIP + SSIM into a composite.

Reuses existing scorers — no new model deps:
  - DINOv2 (skyyrose.core.dino_embedder): strongest image-image similarity.
  - CLIP   (skyyrose.core.clip_embedder): secondary perceptual signal.
  - SSIM   (VisualRegressionTester): structural / embellishment placement.
A view scores only against a real golden reference; no reference => no score
(the view is 'inferred', handled by validate.py + human).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Composite weights — DINOv2 dominates (best visual discriminator per its docstring).
W_DINO, W_CLIP, W_SSIM = 0.5, 0.2, 0.3


def composite_score(*, dino: float, clip: float, ssim: float) -> float:
    return round(W_DINO * dino + W_CLIP * clip + W_SSIM * ssim, 6)


@dataclass(frozen=True)
class VisibleScore:
    angle: str
    dino: float
    clip: float
    ssim: float
    composite: float

    def passes(self, threshold: float) -> bool:
        return self.composite >= threshold


def score_view(render_path: Path, reference_path: Path, *, sku: str, angle: str) -> VisibleScore:
    """Score one rendered view against its golden reference."""
    from skyyrose.core import clip_embedder, dino_embedder
    from skyyrose.elite_studio.quality.visual_regression import VisualRegressionTester

    dino = dino_embedder.cosine_similarity(
        dino_embedder.embed_image(render_path), dino_embedder.embed_image(reference_path)
    )
    clip = clip_embedder.cosine_similarity(
        clip_embedder.embed_image(render_path), clip_embedder.embed_image(reference_path)
    )
    ssim = VisualRegressionTester().compare(str(render_path), sku, angle=angle).ssim_score
    return VisibleScore(
        angle=angle,
        dino=float(dino),
        clip=float(clip),
        ssim=float(ssim),
        composite=composite_score(dino=float(dino), clip=float(clip), ssim=float(ssim)),
    )
