"""Unit tests for garment knowledge & prompt building."""

from __future__ import annotations

from services.three_d.trellis.garment_aware import (
    GarmentCategory,
    brand_context,
    build_clothing_prompt,
    build_garment_prompt_bundle,
    classify_garment,
    knowledge_for,
)


# =============================================================================
# Classification
# =============================================================================


class TestClassify:
    def test_declared_category_wins(self) -> None:
        result = classify_garment(declared_category="hoodie", product_name="Random Name")
        assert result is GarmentCategory.HOODIE

    def test_invalid_declared_falls_through_to_name(self) -> None:
        result = classify_garment(declared_category="not-a-category", product_name="Black Hoodie")
        assert result is GarmentCategory.HOODIE

    def test_product_name_keyword(self) -> None:
        assert classify_garment(product_name="Silver Sneaker") is GarmentCategory.SHOE
        assert classify_garment(product_name="Long Dress") is GarmentCategory.DRESS
        assert classify_garment(product_name="Denim Jeans") is GarmentCategory.PANTS

    def test_aspect_ratio_fallback(self) -> None:
        # Tall image → dress
        assert classify_garment(image_size=(600, 1200)) is GarmentCategory.DRESS
        # Moderately tall → tee
        assert classify_garment(image_size=(600, 800)) is GarmentCategory.TEE
        # Wide-ish → hat
        assert classify_garment(image_size=(1000, 600)) is GarmentCategory.HAT

    def test_unknown_when_no_signal(self) -> None:
        assert classify_garment() is GarmentCategory.UNKNOWN


# =============================================================================
# Knowledge lookup
# =============================================================================


class TestKnowledge:
    def test_known_category_has_prompt(self) -> None:
        kn = knowledge_for(GarmentCategory.HOODIE)
        assert "hood" in kn.prompt_suffix.lower()
        assert kn.polycount_hint > 50_000
        assert kn.symmetry == "x"

    def test_unknown_returns_neutral(self) -> None:
        kn = knowledge_for(GarmentCategory.UNKNOWN)
        assert kn.category is GarmentCategory.UNKNOWN
        assert kn.polycount_hint > 0


# =============================================================================
# Brand context
# =============================================================================


class TestBrandContext:
    def test_known_collection(self) -> None:
        ctx = brand_context("black_rose")
        assert ctx is not None
        assert "chrome" in (ctx.accent or "").lower()

    def test_hyphen_aliases(self) -> None:
        assert brand_context("black-rose") == brand_context("black_rose")

    def test_none_for_missing(self) -> None:
        assert brand_context(None) is None
        assert brand_context("nonexistent") is None


# =============================================================================
# Prompt construction
# =============================================================================


class TestBuildPrompt:
    def test_includes_product_name_and_user_prompt(self) -> None:
        prompt = build_clothing_prompt(
            product_name="Black Rose Hoodie",
            category=GarmentCategory.HOODIE,
            user_prompt="oversized fit, vintage wash",
        )
        assert "Black Rose Hoodie" in prompt
        assert "vintage wash" in prompt
        assert "hood" in prompt.lower()

    def test_brand_context_applied(self) -> None:
        prompt = build_clothing_prompt(
            product_name="Tee",
            category=GarmentCategory.TEE,
            collection="black_rose",
        )
        assert "chrome" in prompt.lower()
        assert "gothic" in prompt.lower() or "dark" in prompt.lower()

    def test_deduplicates(self) -> None:
        prompt = build_clothing_prompt(
            product_name="Sweatshirt",
            category=GarmentCategory.TEE,
            user_prompt="Sweatshirt",  # duplicate phrase
            extra_keywords=["sweatshirt"],  # duplicate again (case-insensitive)
        )
        # Case-insensitive phrase dedup: the exact phrase appears once.
        parts = [p.strip() for p in prompt.split(",")]
        lowered = [p.lower() for p in parts]
        assert lowered.count("sweatshirt") == 1

    def test_always_appends_render_hint(self) -> None:
        prompt = build_clothing_prompt(
            product_name=None,
            category=GarmentCategory.UNKNOWN,
        )
        assert "studio" in prompt.lower()


# =============================================================================
# Bundle
# =============================================================================


class TestBundle:
    def test_bundle_classifies_and_builds(self) -> None:
        bundle = build_garment_prompt_bundle(
            product_name="Black Rose Hoodie",
            collection="black_rose",
            declared_category="hoodie",
        )
        assert bundle.category is GarmentCategory.HOODIE
        assert "Black Rose Hoodie" in bundle.prompt
        assert bundle.knowledge.polycount_hint > 0
        assert bundle.extra["collection"] == "black_rose"
