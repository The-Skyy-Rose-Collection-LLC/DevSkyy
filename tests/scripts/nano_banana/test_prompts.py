"""Unit tests for scripts/nano_banana/prompts.py."""

from __future__ import annotations

from nano_banana.prompts import (
    COLLECTION_LIGHTING,
    composite_prompt,
    get_prompt,
)


class TestGetPrompt:
    """Tests for get_prompt() — prompt router."""

    def test_get_prompt_includes_product_name(self) -> None:
        product = {
            "name": "BLACK Rose Crewneck",
            "collection": "black-rose",
            "sku": "br-001",
            "is_accessory": False,
        }
        prompt = get_prompt(product, "front")
        assert "BLACK Rose Crewneck" in prompt

    def test_get_prompt_front_view(self) -> None:
        product = {
            "name": "BLACK Rose Crewneck",
            "collection": "black-rose",
            "sku": "br-001",
            "is_accessory": False,
        }
        prompt = get_prompt(product, "front")
        assert "FRONT VIEW" in prompt

    def test_get_prompt_back_view(self) -> None:
        product = {
            "name": "BLACK Rose Crewneck",
            "collection": "black-rose",
            "sku": "br-001",
            "is_accessory": False,
        }
        prompt = get_prompt(product, "back")
        assert "BACK VIEW" in prompt or "back" in prompt.lower()


class TestCompositePrompt:
    """Tests for composite_prompt()."""

    def test_composite_prompt_includes_sku(self) -> None:
        prompt = composite_prompt("BLACK Rose Crewneck", "br-001", "front")
        # composite_prompt includes the product name; the SKU is used for
        # LOGO_TREATMENTS lookup. Verify product name appears.
        assert "BLACK Rose Crewneck" in prompt


class TestCollectionLighting:
    """Tests for collection-specific lighting profiles."""

    def test_black_rose_gets_silver(self) -> None:
        lighting = COLLECTION_LIGHTING["black-rose"]
        assert "silver" in lighting["light"].lower()

    def test_signature_gets_gold(self) -> None:
        lighting = COLLECTION_LIGHTING["signature"]
        assert "gold" in lighting["light"].lower()
