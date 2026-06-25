"""EmbeddingSpace: compatibility guard (the silent-garbage backstop) + cache key."""

from __future__ import annotations

import dataclasses

import pytest

from skyyrose.core.embeddings.errors import EmbeddingSpaceMismatch
from skyyrose.core.embeddings.space import EmbeddingSpace

CLIP = EmbeddingSpace("openai/clip-vit-base-patch32", 512, "hf-transformers-5", revision="abc123")
DINO = EmbeddingSpace("facebook/dinov2-base", 768, "hf-transformers-5", revision="def456")


def test_is_frozen():
    with pytest.raises(dataclasses.FrozenInstanceError):
        CLIP.model_id = "x"  # type: ignore[misc]


def test_same_space_is_compatible():
    other = EmbeddingSpace("openai/clip-vit-base-patch32", 512, "hf-transformers-5")
    assert CLIP.is_compatible(other)
    CLIP.assert_compatible(other)  # no raise


def test_dim_mismatch_raises():
    with pytest.raises(EmbeddingSpaceMismatch):
        CLIP.assert_compatible(DINO)


def test_model_mismatch_raises():
    same_dim_other_model = EmbeddingSpace("other/model", 512, "hf-transformers-5")
    with pytest.raises(EmbeddingSpaceMismatch):
        CLIP.assert_compatible(same_dim_other_model)


def test_preprocess_version_mismatch_raises():
    old_preprocess = EmbeddingSpace("openai/clip-vit-base-patch32", 512, "hf-transformers-4")
    with pytest.raises(EmbeddingSpaceMismatch):
        CLIP.assert_compatible(old_preprocess)


def test_revision_does_not_affect_compatibility():
    # A re-pin (different SHA) is advisory, not a hard block — legacy centroids
    # carry revision=None and must still load.
    repinned = EmbeddingSpace(
        "openai/clip-vit-base-patch32", 512, "hf-transformers-5", revision="z"
    )
    legacy = EmbeddingSpace("openai/clip-vit-base-patch32", 512, "hf-transformers-5", revision=None)
    assert CLIP.is_compatible(repinned)
    assert CLIP.is_compatible(legacy)


def test_key_includes_revision_for_cache_busting():
    assert CLIP.key() == "openai/clip-vit-base-patch32@abc123:512"
    unpinned = EmbeddingSpace("m", 4, "v1")
    assert unpinned.key() == "m@unpinned:4"
    # A re-pin changes the key so a content-hash cache misses on changed weights.
    repinned = EmbeddingSpace(
        "openai/clip-vit-base-patch32", 512, "hf-transformers-5", revision="z9"
    )
    assert CLIP.key() != repinned.key()
