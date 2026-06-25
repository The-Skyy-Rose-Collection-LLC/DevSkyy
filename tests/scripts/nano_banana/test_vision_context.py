"""Unit tests for the VisionContext typed container (Phase 3).

Locks in the dict-shim contract that lets ~30 read-side consumers
(`tournament._dna_to_spec`, `router.route_product`, etc.) treat
VisionContext like a dict without code changes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))

from nano_banana.spec_builder import augment_prompt_with_dossier_negatives  # noqa: E402
from nano_banana.tournament import _dna_to_spec  # noqa: E402
from nano_banana.vision_context import VisionContext  # noqa: E402

from skyyrose.core.dossier_loader import Dossier  # noqa: E402


def _make_dossier(*, negative_block: str = "NO printed graphics.") -> Dossier:
    return Dossier(
        sku="br-001",
        name="Test Crewneck",
        collection="black-rose",
        slug="test-crewneck",
        garment_type_lock="Crewneck — upper body only.",
        branding_block="Front: tonal embossed rose.",
        negative_block=negative_block,
        scene_pose="",
        scene_setting="",
    )


# ── Construction ───────────────────────────────────────────────────────────


def test_default_construction_is_empty():
    """Empty VisionContext defaults — used as the empty-vision fallback path."""
    ctx = VisionContext()
    assert ctx.inferred == {}
    assert ctx.catalog == {}
    assert ctx.spec is None
    assert ctx.dossier is None


def test_construction_with_inferred_only():
    """Mirrors `_get_or_cache_vision` path before dossier merge."""
    ctx = VisionContext(inferred={"garment_type": "crewneck", "fabric_appearance": "fleece"})
    assert ctx.inferred["garment_type"] == "crewneck"
    assert ctx.spec is None
    assert ctx.dossier is None


def test_construction_full_canonical():
    """Mirrors `build_dna_from_sku` path with all four sources populated."""
    dossier = _make_dossier()
    ctx = VisionContext(
        inferred={"garment_type": "inferred-type"},
        catalog={"sku": "br-001", "name": "Test"},
        spec="CANONICAL SPEC",
        dossier=dossier,
    )
    assert ctx.spec == "CANONICAL SPEC"
    assert ctx.dossier is dossier


def test_post_init_rejects_spec_without_dossier():
    """Invariant: spec set without dossier means a derivation came from nowhere."""
    with pytest.raises(ValueError, match="spec must be None when dossier is None"):
        VisionContext(spec="orphan spec", dossier=None)


def test_post_init_allows_dossier_with_no_spec():
    """A dossier with all-empty fields legitimately produces an empty spec."""
    # Dossier present but spec None — allowed (the spec_builder may emit "")
    ctx = VisionContext(dossier=_make_dossier(), spec=None)
    assert ctx.dossier is not None


# ── __getitem__ ────────────────────────────────────────────────────────────


def test_getitem_returns_spec_when_set():
    ctx = VisionContext(spec="MY SPEC", dossier=_make_dossier())
    assert ctx["spec"] == "MY SPEC"


def test_getitem_raises_keyerror_for_spec_when_none():
    """spec=None must KeyError (matching `dict.get` semantics for missing keys)."""
    ctx = VisionContext(inferred={"garment_type": "x"})
    with pytest.raises(KeyError):
        _ = ctx["spec"]


def test_getitem_returns_dossier_via_underscore_key():
    """Legacy underscore-prefixed key `_dossier` resolves to the dossier attribute."""
    dossier = _make_dossier()
    ctx = VisionContext(spec="...", dossier=dossier)
    assert ctx["_dossier"] is dossier


def test_getitem_raises_keyerror_for_dossier_when_none():
    ctx = VisionContext(inferred={"garment_type": "x"})
    with pytest.raises(KeyError):
        _ = ctx["_dossier"]


def test_getitem_catalog_wins_over_inferred():
    """Catalog data is more authoritative than inferred — collisions favor catalog."""
    ctx = VisionContext(
        inferred={"name": "guessed name"},
        catalog={"name": "canonical name"},
    )
    assert ctx["name"] == "canonical name"


def test_getitem_falls_through_to_inferred_when_not_in_catalog():
    ctx = VisionContext(
        inferred={"fabric_appearance": "heavyweight fleece"},
        catalog={"sku": "br-001"},
    )
    assert ctx["fabric_appearance"] == "heavyweight fleece"


def test_getitem_raises_keyerror_for_unknown():
    ctx = VisionContext()
    with pytest.raises(KeyError):
        _ = ctx["nonexistent_field"]


# ── __contains__ ───────────────────────────────────────────────────────────


def test_contains_true_for_inferred_keys():
    ctx = VisionContext(inferred={"garment_type": "crewneck"})
    assert "garment_type" in ctx


def test_contains_true_for_catalog_keys():
    ctx = VisionContext(catalog={"sku": "br-001"})
    assert "sku" in ctx


def test_contains_true_for_spec_when_set():
    ctx = VisionContext(spec="...", dossier=_make_dossier())
    assert "spec" in ctx
    assert "_dossier" in ctx


def test_contains_false_for_spec_when_none():
    """Missing spec presents as absent in dict semantics, mirroring real dict behavior."""
    ctx = VisionContext()
    assert "spec" not in ctx
    assert "_dossier" not in ctx


def test_contains_false_for_unknown_key():
    ctx = VisionContext(inferred={"x": 1})
    assert "y" not in ctx


# ── get() ──────────────────────────────────────────────────────────────────


def test_get_returns_value_when_present():
    ctx = VisionContext(inferred={"garment_type": "shorts"})
    assert ctx.get("garment_type") == "shorts"


def test_get_returns_default_when_absent():
    ctx = VisionContext()
    assert ctx.get("nonexistent") is None
    assert ctx.get("nonexistent", "fallback") == "fallback"


def test_get_returns_default_for_none_spec():
    """`get('spec')` on no-dossier ctx returns the default — used by `_dna_to_spec`."""
    ctx = VisionContext(inferred={"garment_type": "x"})
    assert ctx.get("spec") is None
    assert ctx.get("spec", "DEFAULT") == "DEFAULT"


def test_get_returns_default_for_none_dossier():
    ctx = VisionContext(inferred={"garment_type": "x"})
    assert ctx.get("_dossier") is None


# ── to_dict() ──────────────────────────────────────────────────────────────


def test_to_dict_includes_inferred_and_catalog():
    ctx = VisionContext(
        inferred={"garment_type": "crewneck"},
        catalog={"sku": "br-001", "name": "Test"},
    )
    d = ctx.to_dict()
    assert d["garment_type"] == "crewneck"
    assert d["sku"] == "br-001"
    assert d["name"] == "Test"


def test_to_dict_includes_spec_when_set():
    ctx = VisionContext(spec="MY SPEC", dossier=_make_dossier())
    assert ctx.to_dict()["spec"] == "MY SPEC"


def test_to_dict_omits_spec_when_none():
    """No spec → no `spec` key in output (matches `'spec' not in ctx` semantics)."""
    ctx = VisionContext(inferred={"x": 1})
    assert "spec" not in ctx.to_dict()


def test_to_dict_always_omits_dossier_object():
    """The Dossier object is intentionally excluded — large + not JSON-safe."""
    ctx = VisionContext(spec="...", dossier=_make_dossier())
    d = ctx.to_dict()
    assert "_dossier" not in d
    assert "dossier" not in d


def test_to_dict_catalog_overrides_inferred_on_collision():
    ctx = VisionContext(
        inferred={"name": "inferred"},
        catalog={"name": "canonical"},
    )
    assert ctx.to_dict()["name"] == "canonical"


def test_to_dict_is_json_serializable():
    """to_dict() output round-trips through json.dumps without Dossier leakage."""
    ctx = VisionContext(
        inferred={"garment_type": "crewneck", "graphics": []},
        catalog={"sku": "br-001"},
        spec="THE SPEC",
        dossier=_make_dossier(),
    )
    serialized = json.dumps(ctx.to_dict())
    reloaded = json.loads(serialized)
    assert reloaded["spec"] == "THE SPEC"
    assert reloaded["sku"] == "br-001"


# ── Mutation (the pipeline mid-flow merge pattern) ────────────────────────


def test_attribute_writes_after_construction():
    """pipeline.run_single does `vision_desc.spec = ...; vision_desc.dossier = ...`."""
    ctx = VisionContext(inferred={"garment_type": "crewneck"})
    assert ctx.spec is None

    ctx.spec = "NEWLY SET SPEC"
    ctx.dossier = _make_dossier()

    assert ctx["spec"] == "NEWLY SET SPEC"
    assert ctx["_dossier"] is not None
    assert "spec" in ctx


# ── Integration with downstream consumers ─────────────────────────────────


def test_dna_to_spec_consumer_reads_via_shim():
    """tournament._dna_to_spec uses `dna.get('spec')` — works on VisionContext."""
    ctx = VisionContext(spec="CANONICAL DOSSIER SPEC", dossier=_make_dossier())
    assert _dna_to_spec(ctx) == "CANONICAL DOSSIER SPEC"


def test_dna_to_spec_falls_through_to_flat_fields_when_no_spec():
    """No-spec VisionContext falls through to `_dna_to_spec`'s prose synthesis path."""
    ctx = VisionContext(
        inferred={"garment_type": "varsity jacket", "base_color": "#0a0a0a"},
    )
    out = _dna_to_spec(ctx)
    assert "Garment: varsity jacket" in out
    assert "Base color: #0a0a0a" in out


def test_augment_prompt_consumer_reads_via_shim():
    """spec_builder.augment_prompt_with_dossier_negatives reads `dna.get('_dossier')`."""
    ctx = VisionContext(
        spec="...",
        dossier=_make_dossier(negative_block="NO white trim. NO patches."),
    )
    out = augment_prompt_with_dossier_negatives("Generate a crewneck.", ctx)
    assert "DO NOT RENDER" in out
    assert "NO white trim." in out
    assert "NO patches." in out


def test_augment_prompt_no_dossier_returns_unchanged():
    """No dossier → no augmentation, even though `_dossier` raises KeyError on []."""
    ctx = VisionContext(inferred={"garment_type": "x"})
    out = augment_prompt_with_dossier_negatives("base prompt", ctx)
    assert out == "base prompt"
