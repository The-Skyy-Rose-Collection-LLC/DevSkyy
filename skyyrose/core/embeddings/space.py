"""``EmbeddingSpace`` — the identity of an embedding vector's coordinate system.

Two vectors are only comparable if they share a space: same model, same
dimensionality, same preprocessing, same normalization. Stamping this on every
centroid/record and asserting compatibility before any cosine is what prevents
the silent-garbage failure mode (a 768-d DINOv2 centroid scored in the 512-d
CLIP gate returns a confident, meaningless number).

Revision policy: ``revision`` (the pinned HF weight SHA) is folded into
``key()`` so a cache keyed by space busts when weights are re-pinned. It is NOT
part of ``is_compatible`` — a re-pin produces *slightly* different vectors, not a
dimension crash, and legacy centroids saved before pinning carry ``revision=None``;
hard-blocking those would break loads with no safety win. The hard guard is
model/dim/preprocess/normalized, which is what actually corrupts a score.

@package SkyyRose
"""

from __future__ import annotations

from dataclasses import dataclass

from skyyrose.core.embeddings.errors import EmbeddingSpaceMismatch


@dataclass(frozen=True)
class EmbeddingSpace:
    """Immutable fingerprint of an embedding's coordinate system."""

    model_id: str
    dim: int
    preprocess_version: str
    normalized: bool = True
    revision: str | None = None

    def key(self) -> str:
        """Stable namespace key for caches and stores (includes the weight revision)."""
        rev = self.revision or "unpinned"
        return f"{self.model_id}@{rev}:{self.dim}"

    def is_compatible(self, other: EmbeddingSpace) -> bool:
        """True if a cosine between vectors of the two spaces is meaningful."""
        return (
            self.model_id == other.model_id
            and self.dim == other.dim
            and self.preprocess_version == other.preprocess_version
            and self.normalized == other.normalized
        )

    def assert_compatible(self, other: EmbeddingSpace) -> None:
        """Raise :class:`EmbeddingSpaceMismatch` if the two spaces are incompatible."""
        if not self.is_compatible(other):
            raise EmbeddingSpaceMismatch(
                f"incompatible embedding spaces: {self.key()} vs {other.key()}"
            )
