"""Error hierarchy: every typed error rolls up to EmbeddingError; the per-image
ones roll up to EmbedError so a caller can `except EmbedError` to skip a render."""

from __future__ import annotations

from skyyrose.core.embeddings.errors import (
    EmbeddingError,
    EmbeddingSpaceMismatch,
    EmbedError,
    ZeroNormEmbeddingError,
)


def test_hierarchy_rolls_up_to_embedding_error():
    assert issubclass(EmbedError, EmbeddingError)
    assert issubclass(ZeroNormEmbeddingError, EmbedError)
    assert issubclass(EmbeddingSpaceMismatch, EmbeddingError)


def test_zeronorm_is_recoverable_per_image():
    # ZeroNorm is an EmbedError so `except EmbedError` catches it (skip this image).
    assert issubclass(ZeroNormEmbeddingError, EmbedError)


def test_space_mismatch_is_not_per_image_recoverable():
    # A space mismatch is a config bug, not a per-image skip — it is NOT an EmbedError.
    assert not issubclass(EmbeddingSpaceMismatch, EmbedError)
