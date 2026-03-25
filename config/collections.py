"""Canonical collection registry for SkyyRose.

Single source of truth for collection names, aesthetics, and copy.
All pipeline code MUST import from here rather than defining local dicts.

Fixes:
  - C-2: No more silent aesthetic fallback in luxury_photography
  - H-3/H-4: No more silent copy fallback in orchestrators
  - C-3: No more silent style fallback in lora_generator
"""

from __future__ import annotations

from enum import StrEnum
from typing import TypedDict


class Collection(StrEnum):
    """Exhaustive set of SkyyRose collections. Adding a new collection requires
    a matching entry in _REGISTRY below — the registry check is enforced at
    module load time."""

    BLACK_ROSE = "BLACK_ROSE"
    LOVE_HURTS = "LOVE_HURTS"
    SIGNATURE = "SIGNATURE"


class CollectionMeta(TypedDict):
    """Typed metadata bucket for a collection."""

    aesthetic: str
    price_range: tuple[float, float]
    target_customer: str
    vibe: str
    intro: str  # short_description used in WooCommerce / stage_wordpress
    copy_voice: str  # single-sentence brand voice line for fallback copy


_REGISTRY: dict[Collection, CollectionMeta] = {
    Collection.BLACK_ROSE: {
        "aesthetic": ("dark elegance, limited edition mystique, moody lighting, noir aesthetic"),
        "price_range": (165, 285),
        "target_customer": "artistic rebels, collectors, exclusivity seekers",
        "vibe": "mysterious, sophisticated, rebellious luxury",
        "intro": (
            "From the BLACK ROSE collection: where darkness meets elegance in limited edition form."
        ),
        "copy_voice": "Where darkness becomes wearable art.",
    },
    Collection.LOVE_HURTS: {
        "aesthetic": (
            "emotional depth, vulnerable strength, romantic rebellion, artistic expression"
        ),
        "price_range": (145, 245),
        "target_customer": "emotionally expressive, authentic, artistic souls",
        "vibe": "passionate, authentic, artistically refined",
        "intro": (
            "From the LOVE HURTS collection: emotional expression through wearable art, "
            "bearing the Hurts family legacy."
        ),
        "copy_voice": "Emotional expression through luxury craft.",
    },
    Collection.SIGNATURE: {
        "aesthetic": (
            "refined sophistication, timeless elegance, versatile luxury, rose gold accents"
        ),
        "price_range": (125, 195),
        "target_customer": "style conscious, quality focused, everyday luxury",
        "vibe": "confident, understated luxury, essential excellence",
        "intro": (
            "From the SIGNATURE collection: refined essentials that form the foundation "
            "of elevated everyday wear."
        ),
        "copy_voice": "Essential luxury for everyday excellence.",
    },
}

# ── Integrity check: every enum value must have a registry entry ──────────────
_missing = [c for c in Collection if c not in _REGISTRY]
if _missing:
    raise RuntimeError(  # pragma: no cover — caught at import time during dev
        f"Collection registry is incomplete. Missing entries for: {_missing}"
    )


# ── Public API ────────────────────────────────────────────────────────────────


def get_collection(key: str) -> Collection:
    """Resolve a string key to a canonical :class:`Collection` enum value.

    Accepts the canonical uppercase form (BLACK_ROSE, LOVE_HURTS, SIGNATURE).

    Raises:
        ValueError: If *key* does not match any registered collection.
    """
    try:
        return Collection(key.upper())
    except ValueError:
        valid = [c.value for c in Collection]
        raise ValueError(f"Unknown collection {key!r}. Valid collections are: {valid}") from None


def get_meta(collection: Collection) -> CollectionMeta:
    """Return the full metadata dict for *collection*."""
    return _REGISTRY[collection]


def get_aesthetic(collection: Collection) -> str:
    """Return the photography-aesthetic string for *collection*."""
    return _REGISTRY[collection]["aesthetic"]


def get_intro(collection: Collection) -> str:
    """Return the WooCommerce short-description intro line for *collection*."""
    return _REGISTRY[collection]["intro"]


def get_copy_voice(collection: Collection) -> str:
    """Return the single-sentence brand-voice line for *collection*."""
    return _REGISTRY[collection]["copy_voice"]


__all__ = [
    "Collection",
    "CollectionMeta",
    "get_collection",
    "get_meta",
    "get_aesthetic",
    "get_intro",
    "get_copy_voice",
]
