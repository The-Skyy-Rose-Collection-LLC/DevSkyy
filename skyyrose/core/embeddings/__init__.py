"""Unified server-side image/text embedding package.

One configurable, revision-pinned, space-aware home for the CLIP and DINOv2
encoders that the elite-studio quality pipeline depends on. Replaces the two
copy-pasted module singletons (``skyyrose/core/clip_embedder.py`` and
``dino_embedder.py``, now thin facades over this package) and the disconnected
``scripts/image_embeddings/`` duplicate.

Encoders are imported from their submodules (``.clip`` / ``.dino``) rather than
re-exported here, so importing this package does not pull torch/transformers into
the import graph until an encoder is actually instantiated.

@package SkyyRose
@since 1.2.0
"""

from __future__ import annotations

from PIL import Image

from skyyrose.core.embeddings.config import EmbeddingConfig, get_config
from skyyrose.core.embeddings.errors import (
    EmbeddingError,
    EmbeddingSpaceMismatch,
    EmbedError,
    ZeroNormEmbeddingError,
)
from skyyrose.core.embeddings.space import EmbeddingSpace

# E-bomb: cap PIL's decode size process-wide the moment this package is imported,
# so the decompression-bomb guard holds even when only the package (not base.py)
# is imported first. base.py sets the same cap; both are idempotent.
Image.MAX_IMAGE_PIXELS = get_config().max_image_pixels

__all__ = [
    "EmbeddingConfig",
    "get_config",
    "EmbeddingSpace",
    "EmbeddingError",
    "EmbedError",
    "ZeroNormEmbeddingError",
    "EmbeddingSpaceMismatch",
]
