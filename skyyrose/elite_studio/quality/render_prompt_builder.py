"""CLIP-friendly render prompt builder for PIPELINE 1 (product cards / gallery).

Pipeline 1 produces clean product photography — no models, no Oakland
scenes, no editorial storytelling. Just the garment, well-lit, on a
studio backdrop, optionally with a per-collection accent tint.

For Pipeline 2 (lifestyle / editorial / model in scene), see the
compositor agent which uses richer brand-voice scenes.

Schema:
  GARMENT:  short, CLIP-grounded description of the actual product
            (the SCORING surface — what evaluate_render compares against)
  SCENE:    neutral studio backdrop with collection accent lighting
  FIDELITY: instruction-following directives (copy reference exactly)

The CLIP scorer scores the GARMENT block alone against the rendered
output. The full prompt is what goes to the generator.

@package SkyyRose
@since 1.1.0
"""

from __future__ import annotations

from dataclasses import dataclass

# Per-collection scene templates for PRODUCT CARDS (Pipeline 1).
# Neutral studio backdrop with one collection-accent lighting cue.
# The garment is the only subject; nothing else competes for attention.
_SCENE_TEMPLATES: dict[str, str] = {
    "black-rose": (
        "SCENE: Studio product photography. Deep matte black backdrop. "
        "Silver key light upper-left, soft fill, thin rim light along the edge. "
        "Garment fills 70% of frame. No model, no props, no scene elements."
    ),
    "love-hurts": (
        "SCENE: Studio product photography. Deep charcoal backdrop with subtle "
        "crimson rim accent. Soft key light from above, controlled shadows. "
        "Garment fills 70% of frame. No model, no props."
    ),
    "signature": (
        "SCENE: Studio product photography. Warm neutral backdrop. "
        "Soft golden key light upper-left, subtle gold rim accent. "
        "Garment fills 70% of frame. No model, no props."
    ),
    "kids-capsule": (
        "SCENE: Studio product photography. Clean white backdrop. "
        "Even soft lighting, no harsh shadows. Garment fills 70% of frame. "
        "No model, no props."
    ),
}

_FIDELITY_BLOCK = (
    "FIDELITY: The reference photo is the ONLY source of truth for the garment. "
    "Reproduce every logo, color, panel, and stitch exactly. "
    "Do not add patterns, text, or details that are not in the reference."
)


@dataclass
class RenderPrompt:
    """Three-block render prompt with the GARMENT extracted for CLIP scoring."""

    garment: str  # CLIP-friendly garment description (used for scoring)
    scene: str  # environmental + lighting + brand voice
    fidelity: str  # instruction-following directives
    view: str  # "front" | "back" | "branding"

    @property
    def full(self) -> str:
        return f"GARMENT: {self.garment}\n\n{self.scene}\n\n{self.fidelity}"

    def to_dict(self) -> dict:
        return {
            "view": self.view,
            "garment": self.garment,
            "scene": self.scene,
            "fidelity": self.fidelity,
            "full": self.full,
        }


# Heuristic mapping: try to identify the garment type from the SKU name.
# CLIP grounds the right-hand-side terms strongly.
_GARMENT_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("crewneck", "a crewneck sweatshirt"),
    ("hoodie", "a hoodie"),
    ("sherpa", "a sherpa jacket"),
    ("bomber", "a bomber jacket"),
    ("windbreaker", "a windbreaker jacket"),
    ("jersey", "a sports jersey"),
    ("baseball", "a baseball jersey"),
    ("basketball", "basketball shorts"),
    ("football", "a football jersey"),
    ("hockey", "a hockey jersey"),
    ("joggers", "athletic joggers"),
    ("sweatpants", "sweatpants"),
    ("shorts", "athletic shorts"),
    ("beanie", "a knit beanie"),
    ("fanny", "a fanny pack"),
    ("shirt", "a graphic t-shirt"),
    ("tee", "a graphic t-shirt"),
    ("set", "a matching apparel set"),
)


def _infer_garment_type(name: str) -> str:
    """Pull the CLIP-grounded garment word out of a noisy product name."""
    n = name.lower()
    for kw, generic in _GARMENT_KEYWORDS:
        if kw in n:
            return generic
    return "a fashion garment"


def _infer_color(name: str) -> str:
    """Best-effort color extraction. Empty if uncertain."""
    n = name.lower()
    for color in ("black", "white", "red", "purple", "mint", "lavender", "orchid", "navy"):
        if color in n:
            return color
    return ""


def _splice_color(garment_phrase: str, color: str) -> str:
    """Insert color in the right place: 'a hoodie' + 'black' -> 'a black hoodie'.

    Handles:
      'a hoodie'         + 'black' -> 'a black hoodie'
      'an eye mask'      + 'red'   -> 'a red eye mask'   (article re-articled)
      'athletic joggers' + 'black' -> 'black athletic joggers'   (no article)
      'a hoodie'         + ''      -> 'a hoodie'
    """
    if not color:
        return garment_phrase
    parts = garment_phrase.split(" ", 1)
    if not parts:
        return garment_phrase
    first = parts[0].lower()
    rest = parts[1] if len(parts) > 1 else ""
    if first in ("a", "an"):
        # English: "a" before consonant, "an" before vowel — color words start with consonants here.
        return f"a {color} {rest}".strip()
    return f"{color} {garment_phrase}"


def build_garment_block(product: dict, view: str) -> str:
    """Compact, CLIP-friendly garment description for one product.

    Examples:
      br-001 BLACK Rose Crewneck (front)  -> "front view of a black crewneck sweatshirt on a model"
      sg-007 The Signature Beanie         -> "a knit beanie on a flat surface"
      lh-002 Love Hurts Joggers (back)    -> "back view of black athletic joggers on a model"
    """
    name = product.get("name", "")
    is_accessory = bool(product.get("is_accessory"))
    garment_type = _infer_garment_type(name)
    color = _infer_color(name)
    phrase = _splice_color(garment_type, color)

    if is_accessory:
        return f"{phrase} on a flat surface"

    if view == "back":
        return f"back view of {phrase} on a model"
    return f"front view of {phrase} on a model"


def build_render_prompt(product: dict, view: str = "front") -> RenderPrompt:
    """Produce a three-block render prompt for nano-banana / FLUX.

    The GARMENT block is what we score against the render in CLIP. The
    full prompt is what we send to the generator.
    """
    collection = product.get("collection", "signature")
    scene = _SCENE_TEMPLATES.get(collection, _SCENE_TEMPLATES["signature"])
    return RenderPrompt(
        garment=build_garment_block(product, view),
        scene=scene,
        fidelity=_FIDELITY_BLOCK,
        view=view,
    )
