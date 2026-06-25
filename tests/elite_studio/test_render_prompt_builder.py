"""Tests for render_prompt_builder."""

from __future__ import annotations

from skyyrose.elite_studio.quality.render_prompt_builder import (
    RenderPrompt,
    build_garment_block,
    build_render_prompt,
)


def test_garment_block_extracts_hoodie() -> None:
    p = {"name": "BLACK Rose Hoodie", "collection": "black-rose"}
    block = build_garment_block(p, "front")
    assert "hoodie" in block.lower()
    assert "front view" in block
    assert "model" in block


def test_garment_block_extracts_color() -> None:
    p = {"name": "BLACK Rose Crewneck", "collection": "black-rose"}
    block = build_garment_block(p, "front")
    assert "black" in block.lower()


def test_garment_block_back_view() -> None:
    p = {"name": "Love Hurts Joggers", "collection": "love-hurts"}
    block = build_garment_block(p, "back")
    assert "back view" in block.lower()
    assert "joggers" in block.lower()


def test_garment_block_accessory_skips_model() -> None:
    p = {"name": "The Signature Beanie", "collection": "signature", "is_accessory": True}
    block = build_garment_block(p, "front")
    assert "model" not in block.lower()
    assert "beanie" in block.lower()


def test_garment_block_unknown_garment_falls_back() -> None:
    p = {"name": "The Mystery Item", "collection": "signature"}
    block = build_garment_block(p, "front")
    # Falls back to generic "fashion garment" but still includes model.
    assert "garment" in block.lower()
    assert "model" in block.lower()


def test_build_render_prompt_returns_three_blocks() -> None:
    p = {"name": "BLACK Rose Crewneck", "collection": "black-rose"}
    rp = build_render_prompt(p)
    assert isinstance(rp, RenderPrompt)
    assert rp.garment
    # Pipeline 1 scenes are studio product photography, not Oakland editorial.
    assert "studio" in rp.scene.lower()
    assert "no model, no props" in rp.scene.lower()
    assert "FIDELITY" in rp.fidelity
    assert rp.view == "front"


def test_full_prompt_includes_all_three_blocks() -> None:
    p = {"name": "Love Hurts Bomber Jacket", "collection": "love-hurts"}
    rp = build_render_prompt(p, view="front")
    assert "GARMENT:" in rp.full
    assert "SCENE:" in rp.full
    assert "FIDELITY:" in rp.full


def test_collection_drives_scene_choice() -> None:
    """Each collection has its own accent lighting on the same neutral studio."""
    sig = build_render_prompt({"name": "Foo", "collection": "signature"})
    br = build_render_prompt({"name": "Foo", "collection": "black-rose"})
    lh = build_render_prompt({"name": "Foo", "collection": "love-hurts"})
    kids = build_render_prompt({"name": "Foo", "collection": "kids-capsule"})
    # All four are unique.
    assert len({sig.scene, br.scene, lh.scene, kids.scene}) == 4
    # Each carries its accent cue.
    assert "gold" in sig.scene.lower()
    assert "silver" in br.scene.lower()
    assert "crimson" in lh.scene.lower()
    assert "white" in kids.scene.lower()


def test_to_dict_serializes() -> None:
    rp = build_render_prompt({"name": "BLACK Rose Hoodie", "collection": "black-rose"})
    d = rp.to_dict()
    assert "garment" in d and "scene" in d and "fidelity" in d and "full" in d
    assert d["view"] == "front"
