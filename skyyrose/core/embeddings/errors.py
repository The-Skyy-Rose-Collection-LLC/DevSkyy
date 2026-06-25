"""Typed exceptions for the embeddings package.

A single typed hierarchy so callers on the paid render path can distinguish a
recoverable image problem (skip this render) from a configuration bug (stop the
run) — instead of a raw ``PIL.UnidentifiedImageError`` / ``numpy`` shape error
propagating with no context.

@package SkyyRose
"""

from __future__ import annotations


class EmbeddingError(Exception):
    """Base class for every error raised by ``skyyrose.core.embeddings``."""


class EmbedError(EmbeddingError):
    """An image could not be loaded or encoded.

    Wraps the underlying cause (missing file, corrupt/unreadable image,
    decompression-bomb refusal, wrong input type). Recoverable per-image: the
    caller can skip this render rather than aborting the batch.
    """


class ZeroNormEmbeddingError(EmbedError):
    """An embedding has a near-zero L2 norm (blank/black/degenerate image).

    Returning such a vector would let a blank render score cosine ``0.0`` and be
    silently accepted by the brand gate. We fail closed instead.
    """


class EmbeddingSpaceMismatch(EmbeddingError):
    """Two embeddings (or an embedding and a centroid) come from different spaces.

    e.g. a 768-d DINOv2 centroid scored against 512-d CLIP image vectors. The
    cosine would be a confident, meaningless number — raise before scoring.
    """
