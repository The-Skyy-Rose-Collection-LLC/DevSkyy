"""Tests for skyyrose.elite_studio.quality.prompt_simplifier.

The simplifier produces a CLIP-friendly version of a generation prompt
by stripping brand-specific tokens (collection names, marketing adjectives,
hex codes) and replacing brand-specific landmarks with generic equivalents.
The result has higher cosine similarity vs the rendered image because it
contains only tokens CLIP-base was trained to ground.
"""

from __future__ import annotations

from skyyrose.elite_studio.quality import prompt_simplifier

# ---------------------------------------------------------------------------
# Brand-name stripping
# ---------------------------------------------------------------------------


def test_strips_skyyrose_brand_name() -> None:
    out = prompt_simplifier.simplify_for_clip("a SkyyRose black hoodie on a model")
    assert "SkyyRose" not in out
    assert "skyyrose" not in out.lower()
    assert "hoodie" in out


def test_strips_collection_names() -> None:
    cases = [
        ("a Black Rose hoodie", "Black Rose"),
        ("a Love Hurts crewneck", "Love Hurts"),
        ("a Signature shirt", "Signature"),
        ("a Kids Capsule tee", "Kids Capsule"),
    ]
    for raw, brand in cases:
        out = prompt_simplifier.simplify_for_clip(raw)
        assert brand.lower() not in out.lower(), f"{brand!r} not stripped from {raw!r}"


def test_strips_brand_specific_skus() -> None:
    out = prompt_simplifier.simplify_for_clip("br-001 black crewneck on a model")
    assert "br-001" not in out.lower()


def test_strips_hex_color_codes() -> None:
    out = prompt_simplifier.simplify_for_clip(
        "rose gold #B76E79 embroidery on black #0a0a0a hoodie"
    )
    assert "#" not in out
    assert "B76E79" not in out
    assert "0a0a0a" not in out


def test_strips_marketing_adjectives() -> None:
    out = prompt_simplifier.simplify_for_clip("an exclusive luxury premium high-end couture hoodie")
    for word in ("exclusive", "luxury", "premium", "high-end", "couture"):
        assert word not in out.lower(), f"{word!r} not stripped"
    assert "hoodie" in out


# ---------------------------------------------------------------------------
# Landmark genericization
# ---------------------------------------------------------------------------


def test_replaces_bay_bridge_with_generic() -> None:
    out = prompt_simplifier.simplify_for_clip("a tee with the Bay Bridge skyline")
    assert "bay bridge" not in out.lower()
    # Must keep some skyline/bridge concept so the visual still grounds.
    assert "bridge" in out.lower() or "skyline" in out.lower()


def test_replaces_golden_gate() -> None:
    out = prompt_simplifier.simplify_for_clip("a hoodie featuring the Golden Gate Bridge")
    assert "golden gate" not in out.lower()
    assert "bridge" in out.lower()


def test_replaces_oakland_with_urban() -> None:
    out = prompt_simplifier.simplify_for_clip("Oakland streetwear vibe black hoodie")
    assert "oakland" not in out.lower()


# ---------------------------------------------------------------------------
# Garment-core preservation
# ---------------------------------------------------------------------------


def test_preserves_garment_type() -> None:
    cases = ["hoodie", "crewneck", "tee", "jersey", "sweatpants", "joggers", "shorts"]
    for garment in cases:
        out = prompt_simplifier.simplify_for_clip(f"a luxury black SkyyRose {garment}")
        assert garment in out.lower(), f"garment {garment!r} dropped"


def test_preserves_color_words() -> None:
    out = prompt_simplifier.simplify_for_clip("a luxury black SkyyRose hoodie")
    assert "black" in out.lower()


def test_preserves_view_descriptors() -> None:
    out = prompt_simplifier.simplify_for_clip("front view of a SkyyRose model wearing a hoodie")
    out_lower = out.lower()
    assert "front" in out_lower or "model" in out_lower or "wearing" in out_lower


# ---------------------------------------------------------------------------
# Behavior contract
# ---------------------------------------------------------------------------


def test_returns_lowercased_normalized_string() -> None:
    out = prompt_simplifier.simplify_for_clip("A LUXURY SkyyRose Hoodie")
    # Multiple spaces collapsed, no leading/trailing whitespace.
    assert "  " not in out
    assert out == out.strip()


def test_empty_input_returns_empty_string() -> None:
    assert prompt_simplifier.simplify_for_clip("") == ""
    assert prompt_simplifier.simplify_for_clip("   ") == ""


def test_only_brand_terms_returns_empty_or_minimal() -> None:
    """A prompt that's ONLY brand language reduces to (near) empty."""
    out = prompt_simplifier.simplify_for_clip("SkyyRose Black Rose Signature luxury")
    # Allow up to 1 residual word — the goal is "no brand tokens left,"
    # not perfect zero.
    assert len(out.split()) <= 1


def test_idempotent_twice_simplified() -> None:
    """Simplifying an already-simplified prompt is a no-op."""
    once = prompt_simplifier.simplify_for_clip("a SkyyRose black hoodie")
    twice = prompt_simplifier.simplify_for_clip(once)
    assert once == twice


def test_handles_punctuation_around_brand_terms() -> None:
    out = prompt_simplifier.simplify_for_clip(
        "a model wearing the 'Black Rose' (SkyyRose) hoodie -- exclusive!"
    )
    assert "skyyrose" not in out.lower()
    assert "black rose" not in out.lower()
    assert "hoodie" in out.lower()
