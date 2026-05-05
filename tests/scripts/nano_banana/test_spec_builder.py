"""Tests for the canonical-dossier spec builder.

The bug this prevents: ad-hoc DNA construction loses signal that the
canonical dossier carries — per-element trim color, technique
distinctions (embossed vs embroidered), and the negative list. The
2026-05-04 Layer 1 validation tried to refine away the legitimately-
specified white ribbed trim on br-001 because the inferred DNA didn't
mention it. Loading from the dossier is the only correct path.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))

from nano_banana.spec_builder import (
    augment_prompt_with_dossier_negatives,
    build_dna_from_sku,
    build_judge_spec_from_dossier,
)
from nano_banana.tournament import _dna_to_spec

from skyyrose.core.dossier_loader import Dossier


def _make_dossier(
    *,
    sku: str = "br-001",
    name: str = "BLACK Rose Crewneck",
    garment_type_lock: str = "Crewneck sweatshirt — upper body only.",
    branding_block: str = "Front: tonal embossed rose.",
    negative_block: str = "NO printed graphics.",
    scene_pose: str = "",
    scene_setting: str = "",
) -> Dossier:
    return Dossier(
        sku=sku,
        name=name,
        collection="black-rose",
        slug=name.lower().replace(" ", "-"),
        garment_type_lock=garment_type_lock,
        branding_block=branding_block,
        negative_block=negative_block,
        scene_pose=scene_pose,
        scene_setting=scene_setting,
    )


def test_spec_includes_all_dossier_sections():
    """Every populated section appears verbatim in the output spec."""
    dossier = _make_dossier(
        garment_type_lock="LOCK_TEXT_HERE",
        branding_block="BRANDING_TEXT_HERE",
        negative_block="NEGATIVE_TEXT_HERE",
        scene_pose="POSE_TEXT_HERE",
        scene_setting="SETTING_TEXT_HERE",
    )
    spec = build_judge_spec_from_dossier(dossier)
    assert "BLACK Rose Crewneck" in spec
    assert "br-001" in spec
    assert "LOCK_TEXT_HERE" in spec
    assert "BRANDING_TEXT_HERE" in spec
    assert "NEGATIVE_TEXT_HERE" in spec
    assert "POSE_TEXT_HERE" in spec
    assert "SETTING_TEXT_HERE" in spec


def test_spec_section_headers_are_explicit():
    """Sections have explicit heading lines so judges can structure their reasoning."""
    dossier = _make_dossier()
    spec = build_judge_spec_from_dossier(dossier)
    assert "GARMENT TYPE LOCK:" in spec
    assert "BRANDING — exactly what IS on this product:" in spec
    assert "NEGATIVE — what is NOT on this product (DO NOT render):" in spec


def test_spec_skips_empty_scene_section():
    """If pose+setting are both empty, no SCENE: header is emitted."""
    dossier = _make_dossier(scene_pose="", scene_setting="")
    spec = build_judge_spec_from_dossier(dossier)
    assert "SCENE:" not in spec


def test_spec_emits_scene_when_only_pose_set():
    """Partial scene direction (pose without setting) still emits a SCENE block."""
    dossier = _make_dossier(scene_pose="standing facing forward", scene_setting="")
    spec = build_judge_spec_from_dossier(dossier)
    assert "SCENE:" in spec
    assert "Pose: standing facing forward" in spec
    assert "Setting:" not in spec  # not set


def test_dna_to_spec_honors_spec_override():
    """When dna has a `spec` string, _dna_to_spec returns it verbatim,
    bypassing the lossy flat-field prose synthesis."""
    canonical = "CANONICAL_SPEC_FROM_DOSSIER"
    dna = {"spec": canonical, "garment_type": "this should be ignored"}
    assert _dna_to_spec(dna) == canonical


def test_dna_to_spec_falls_back_when_spec_empty():
    """Empty/missing spec falls back to flat-field prose construction."""
    dna_no_spec = {"garment_type": "crewneck sweatshirt", "base_color": "#000000"}
    dna_empty_spec = {"spec": "", **dna_no_spec}
    dna_whitespace_spec = {"spec": "   \n  ", **dna_no_spec}

    for d in (dna_no_spec, dna_empty_spec, dna_whitespace_spec):
        out = _dna_to_spec(d)
        assert "Garment: crewneck sweatshirt" in out
        assert "Base color: #000000" in out


def test_build_dna_from_sku_real_br001(monkeypatch):
    """End-to-end: br-001 loads, the spec mentions WHITE trim and the
    NO-black-trim negative. This is the regression check for the
    2026-05-04 bug — if the spec ever stops mentioning white trim, the
    validator will silently re-introduce the same defect."""
    dna = build_dna_from_sku("br-001")
    assert "spec" in dna
    spec = dna["spec"]
    # White trim IS the design
    assert "White ribbed" in spec or "white ribbed" in spec.lower()
    # And the negative explicitly forbids black trim
    assert "NO black ribbed neckband" in spec or "rib trim is WHITE" in spec
    # Tonal embossed callout for the front rose (not multi-tone color)
    assert "embossed" in spec.lower()
    # Negative list items
    assert "NO printed" in spec or "no printed" in spec.lower()


def test_build_dna_from_sku_raises_on_unknown():
    """Unknown SKU raises KeyError — pipeline must hard-fail."""
    import pytest

    with pytest.raises(KeyError):
        build_dna_from_sku("does-not-exist-xyz-9999")


# ── augment_prompt_with_dossier_negatives ──────────────────────────────────


def test_augment_prompt_appends_dossier_negatives():
    """When dna has a dossier with a negative_block, it's appended to the prompt."""
    dossier = _make_dossier(negative_block="NO printed graphics. NO sleeve text.")
    prompt = "Generate a black sweatshirt."
    out = augment_prompt_with_dossier_negatives(prompt, {"_dossier": dossier, "spec": "..."})
    assert "Generate a black sweatshirt." in out
    assert "DO NOT RENDER" in out
    assert "NO printed graphics." in out
    assert "NO sleeve text." in out


def test_augment_prompt_no_dossier_returns_unchanged():
    """Prompts pass through untouched when no dossier in dna."""
    prompt = "Generate a black sweatshirt."
    assert augment_prompt_with_dossier_negatives(prompt, {}) == prompt
    assert augment_prompt_with_dossier_negatives(prompt, {"spec": "..."}) == prompt


def test_augment_prompt_empty_negative_block_returns_unchanged():
    """Dossier with empty negative_block doesn't add empty headers."""
    dossier = _make_dossier(negative_block="")
    prompt = "Generate a black sweatshirt."
    out = augment_prompt_with_dossier_negatives(prompt, {"_dossier": dossier})
    assert out == prompt
    assert "DO NOT RENDER" not in out


def test_augment_prompt_whitespace_only_negative_returns_unchanged():
    """Whitespace-only negative_block treated as empty."""
    dossier = _make_dossier(negative_block="   \n  \n  ")
    prompt = "Generate a black sweatshirt."
    out = augment_prompt_with_dossier_negatives(prompt, {"_dossier": dossier})
    assert out == prompt
