"""Tests for skyyrose.elite_studio.catalog (Wave 1.5 SoT loader)."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from skyyrose.elite_studio.catalog import Catalog, SeriesEntry

pytest.importorskip("yaml")


FIXTURE_YAML = """
version: 3
generated_at: "2026-04-17T00:00:00Z"
collections:
  black-rose:
    display_name: BLACK ROSE
    theme: gothic
    color_palette: {primary: "#0A0A0A", accents: ["#B76E79"]}
  signature:
    display_name: SIGNATURE
    theme: bay-area
    color_palette: {primary: "#0A0A0A", accents: ["#D4AF37"]}
catalog_rules:
  jerseys:
    universal_patch_rule: "Every jersey has a sport patch bottom-left."
    patch_assets:
      baseball: path/to/baseball.jpeg
      hockey: path/to/hockey.jpeg
    sku_to_patch:
      br-003: baseball
      br-011: hockey
series:
  "Jersey Series":
    collection: black-rose
    description: "Limited 4-jersey drop."
    skus: [br-008, br-011]
    lookbook_images: []
  "Mint & Lavender":
    collection: signature
    description: "Mint/lavender capsule."
    skus: [sg-013, sg-014]
    lookbook_images:
      - assets/lookbook/mint-set.jpg
products:
  - sku: br-001
    name: Crewneck
    collection: black-rose
    price_usd: 35.00
    status: draft
    aliases: []
    filename_patterns: [br-001]
    color_spec: {primary: "#0A0A0A", accents: ["#B76E79"]}
    text_spec: ["SKYY ROSE"]
    branding_summary: "Embossed rose logo on front chest."
    variants: []
    master: {path: null, hash: null, source: pending}
    source_files: []
    ai_renders: []
    review_flags: []
    notes: ""
  - sku: br-008
    name: SF Inspired Jersey
    collection: black-rose
    price_usd: 115.00
    status: pre-order
    limited_pieces: 80
    aliases: [br-d02]
    filename_patterns: [br-008, br-d02]
    color_spec: {primary: "#0A0A0A", accents: ["#B76E79"]}
    text_spec: []
    branding_summary: "Red football jersey, number 80."
    variants: []
    master: {path: null, hash: null, source: pending}
    source_files: ["skyyrose/assets/br-008.png"]
    ai_renders: []
    review_flags: []
    notes: ""
  - sku: br-011
    name: SHARKS EDITION Jersey
    collection: black-rose
    price_usd: 115.00
    status: pre-order
    aliases: [br-d01]
    filename_patterns: [br-011, br-d01]
    color_spec: {primary: "#0A0A0A", accents: []}
    text_spec: []
    branding_summary: "Hockey jersey."
    variants: []
    master:
      path: "masters/br-011.png"
      hash: "sha256:deadbeef"
      source: photograph
    source_files: []
    ai_renders: []
    review_flags: []
    notes: ""
  - sku: sg-013
    name: Mint Crewneck
    collection: signature
    price_usd: 40.00
    status: pre-order
    aliases: []
    filename_patterns: [sg-013]
    color_spec: {primary: "#C8E6C9", accents: ["#B39DDB"]}
    text_spec: []
    branding_summary: "Lavender rose on chest."
    variants: []
    master: {path: null, hash: null, source: pending}
    source_files: []
    ai_renders: []
    review_flags: []
    notes: ""
  - sku: sg-014
    name: Mint Sweatpants
    collection: signature
    price_usd: 45.00
    status: pre-order
    aliases: []
    filename_patterns: [sg-014]
    color_spec: {primary: "#C8E6C9", accents: ["#B39DDB"]}
    text_spec: []
    branding_summary: "Embroidered rose on thigh."
    variants: []
    master: {path: null, hash: null, source: pending}
    source_files: []
    ai_renders: []
    review_flags: []
    notes: ""
  - sku: sg-004
    name: Retired Hoodie
    collection: signature
    price_usd: 55.00
    status: retired
    aliases: []
    filename_patterns: [sg-004]
    color_spec: {primary: "#0A0A0A", accents: []}
    text_spec: []
    branding_summary: ""
    variants: []
    master: {path: null, hash: null, source: pending}
    source_files: []
    ai_renders: []
    review_flags: []
    notes: ""
    retirement_note: "Deleted by user."
unclaimed_legacy_files: {}
orphan_brand_files:
  count: 0
  files: []
"""


@pytest.fixture
def catalog(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Catalog:
    p = tmp_path / "catalog.yaml"
    p.write_text(textwrap.dedent(FIXTURE_YAML).lstrip("\n"))
    monkeypatch.setenv("SKYYROSE_CATALOG_PATH", str(p))
    return Catalog.load()


# ─── Loading ────────────────────────────────────────────────────────────


def test_load_parses_version_and_generated_at(catalog: Catalog) -> None:
    assert catalog.version == 3
    assert catalog.generated_at.startswith("2026-04-17")


def test_load_parses_all_products(catalog: Catalog) -> None:
    assert len(catalog.products_by_sku) == 6
    assert set(catalog.products_by_sku.keys()) == {
        "br-001",
        "br-008",
        "br-011",
        "sg-013",
        "sg-014",
        "sg-004",
    }


def test_load_missing_file_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKYYROSE_CATALOG_PATH", str(tmp_path / "nope.yaml"))
    with pytest.raises(FileNotFoundError):
        Catalog.load()


# ─── list_skus / active filtering ───────────────────────────────────────


def test_list_skus_includes_retired_by_default(catalog: Catalog) -> None:
    assert "sg-004" in catalog.list_skus()


def test_list_skus_active_only_excludes_retired(catalog: Catalog) -> None:
    assert "sg-004" not in catalog.list_skus(active_only=True)


# ─── ProductEntry properties ────────────────────────────────────────────


def test_is_active_and_is_locked(catalog: Catalog) -> None:
    assert catalog.require("br-001").is_active is True
    assert catalog.require("sg-004").is_active is False
    # br-011 has both path and hash set
    assert catalog.require("br-011").is_locked is True
    # br-001 has path=null
    assert catalog.require("br-001").is_locked is False


def test_all_filename_keys_includes_aliases(catalog: Catalog) -> None:
    keys = catalog.require("br-008").all_filename_keys
    assert keys == ("br-008", "br-d02")


def test_branding_summary_preserved(catalog: Catalog) -> None:
    assert "Embossed rose logo" in catalog.require("br-001").branding_summary


# ─── Series attribution ────────────────────────────────────────────────


def test_series_auto_attributed_from_series_block(catalog: Catalog) -> None:
    # Products don't declare series directly in fixture; loader derives from series.skus
    assert catalog.require("br-008").series == "Jersey Series"
    assert catalog.require("sg-013").series == "Mint & Lavender"


def test_standalone_sku_has_no_series(catalog: Catalog) -> None:
    assert catalog.require("br-001").series is None


def test_products_in_series_returns_ordered_members(catalog: Catalog) -> None:
    members = catalog.products_in_series("Mint & Lavender")
    assert [p.sku for p in members] == ["sg-013", "sg-014"]


def test_get_series_returns_series_entry_with_lookbook(catalog: Catalog) -> None:
    s = catalog.get_series("Mint & Lavender")
    assert isinstance(s, SeriesEntry)
    assert s.lookbook_images == ("assets/lookbook/mint-set.jpg",)


# ─── Alias resolution ──────────────────────────────────────────────────


def test_resolve_sku_direct_hit(catalog: Catalog) -> None:
    p = catalog.resolve_sku("br-008")
    assert p is not None and p.sku == "br-008"


def test_resolve_sku_via_alias(catalog: Catalog) -> None:
    p = catalog.resolve_sku("br-d02")
    assert p is not None and p.sku == "br-008"


def test_resolve_sku_returns_none_for_unknown(catalog: Catalog) -> None:
    assert catalog.resolve_sku("zz-999") is None


# ─── Catalog rules ────────────────────────────────────────────────────


def test_jersey_patch_lookup(catalog: Catalog) -> None:
    assert catalog.jersey_patch_for("br-003") == "baseball"
    assert catalog.jersey_patch_for("br-011") == "hockey"
    assert catalog.jersey_patch_for("br-001") is None  # not a jersey


# ─── Collection filtering ─────────────────────────────────────────────


def test_products_in_collection_active_only(catalog: Catalog) -> None:
    sig_active = catalog.products_in_collection("signature", active_only=True)
    assert {p.sku for p in sig_active} == {"sg-013", "sg-014"}  # sg-004 retired


# ─── require() error path ─────────────────────────────────────────────


def test_require_raises_on_unknown(catalog: Catalog) -> None:
    with pytest.raises(KeyError, match="not found"):
        catalog.require("zz-999")
