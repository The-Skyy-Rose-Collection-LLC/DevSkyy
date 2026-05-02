"""CLIP text-to-image alignment scoring.

Quantifies "did this render match the prompt?" objectively. CLIP's text and
image encoders share a 512-d embedding space; cosine similarity between
embed_text(prompt) and embed_image(render) is the alignment score.

Typical scores:
    > 0.30   strong alignment
    0.20-0.30 moderate alignment (typical for well-prompted Stable Diffusion / FLUX)
    < 0.20   weak alignment, prompt mostly ignored

Use as a post-render gate in nano-banana and as a tiebreaker in the 3D
round-table judging.

@package SkyyRose
@since 1.1.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from PIL import Image

from skyyrose.core import clip_embedder


def score_alignment(prompt: str, image: Union[Path, str, Image.Image]) -> float:
    """Cosine similarity between prompt and image embeddings."""
    text_vec = clip_embedder.embed_text(prompt)
    image_vec = clip_embedder.embed_image(image)
    return clip_embedder.cosine_similarity(text_vec, image_vec)


def score_alignment_batch(prompts: list[str], image: Union[Path, str, Image.Image]) -> list[float]:
    """Score multiple prompts against the same image. Embeds image once."""
    image_vec = clip_embedder.embed_image(image)
    return [
        clip_embedder.cosine_similarity(clip_embedder.embed_text(p), image_vec) for p in prompts
    ]
