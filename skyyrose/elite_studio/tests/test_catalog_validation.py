"""Tests for Catalog hardening (structural + referential integrity)."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from skyyrose.elite_studio.catalog import Catalog
from skyyrose.elite_studio.validation import IntegrityError

pytest.importorskip("yaml")


# ─── Helper: build minimal catalog YAML with one swappable product ──────


def _catalog_yaml(product_override: str = "", series_skus: str = "[br-001]") -> str:
    """Build a minimal valid catalog with one product (optionally overridden)."""
    default_product = """
  - sku: br-001
    name: Crewneck
    collection: black-rose
    price_usd: 35.00
    status: draft
    aliases: []
    filename_patterns: [br-001]
    color_spec: {primary: "#0A0A0A", accents: ["#B76E79"]}
    text_spec: ["SKYY ROSE"]
    branding_summary: "Embossed rose"
    variants: []
    master: {path: null, hash: null, source: pending}
    source_files: []
    ai_renders: []
    review_flags: []
    notes: ""
"""
    product = product_override or default_product
    return textwrap.dedent(f"""
version: 3
generated_at: "2026-04-17T00:00:00Z"
collections:
  black-rose:
    display_name: BLACK ROSE
    color_palette: {{primary: "#0A0A0A", accents: ["#B76E79"]}}
catalog_rules:
  jerseys:
    sku_to_patch: {{}}
series:
  "Test Series":
    collection: black-rose
    description: "Test"
    skus: {series_skus}
    lookbook_images: []
products:
{product}
unclaimed_legacy_files: {{}}
orphan_brand_files:
  count: 0
  files: []
""").lstrip("\n")


def _load(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, yaml_text: str, **kwargs) -> Catalog:
    p = tmp_path / "catalog.yaml"
    p.write_text(yaml_text)
    monkeypatch.setenv("SKYYROSE_CATALOG_PATH", str(p))
    return Catalog.load(**kwargs)


# ─── Structural (ProductEntry.__post_init__) ────────────────────────────


def test_invalid_status_raises_value_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bad = _catalog_yaml(product_override="""
  - sku: br-001
    name: Crewneck
    collection: black-rose
    price_usd: 35.00
    status: zombie
    aliases: []
    filename_patterns: [br-001]
    color_spec: {primary: "#0A0A0A", accents: []}
    text_spec: []
    branding_summary: "x"
    variants: []
    master: {path: null, hash: null, source: pending}
    source_files: []
    ai_renders: []
    review_flags: []
    notes: ""
""")
    with pytest.raises(ValueError, match="not in allowed values"):
        _load(tmp_path, monkeypatch, bad)


def test_invalid_hex_color_raises_value_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bad = _catalog_yaml(product_override="""
  - sku: br-001
    name: Crewneck
    collection: black-rose
    price_usd: 35.00
    status: draft
    aliases: []
    filename_patterns: [br-001]
    color_spec: {primary: "not-a-color", accents: []}
    text_spec: []
    branding_summary: "x"
    variants: []
    master: {path: null, hash: null, source: pending}
    source_files: []
    ai_renders: []
    review_flags: []
    notes: ""
""")
    with pytest.raises(ValueError, match="invalid hex color"):
        _load(tmp_path, monkeypatch, bad)


def test_negative_price_raises_value_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bad = _catalog_yaml(product_override="""
  - sku: br-001
    name: Crewneck
    collection: black-rose
    price_usd: -5.00
    status: draft
    aliases: []
    filename_patterns: [br-001]
    color_spec: {primary: "#0A0A0A", accents: []}
    text_spec: []
    branding_summary: "x"
    variants: []
    master: {path: null, hash: null, source: pending}
    source_files: []
    ai_renders: []
    review_flags: []
    notes: ""
""")
    with pytest.raises(ValueError, match=">= 0"):
        _load(tmp_path, monkeypatch, bad)


def test_invalid_master_source_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bad = _catalog_yaml(product_override="""
  - sku: br-001
    name: Crewneck
    collection: black-rose
    price_usd: 35.00
    status: draft
    aliases: []
    filename_patterns: [br-001]
    color_spec: {primary: "#0A0A0A", accents: []}
    text_spec: []
    branding_summary: "x"
    variants: []
    master: {path: null, hash: null, source: imagined}
    source_files: []
    ai_renders: []
    review_flags: []
    notes: ""
""")
    with pytest.raises(ValueError, match="not in allowed values"):
        _load(tmp_path, monkeypatch, bad)


def test_invalid_sku_format_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bad = _catalog_yaml(product_override="""
  - sku: BR_001
    name: Crewneck
    collection: black-rose
    price_usd: 35.00
    status: draft
    aliases: []
    filename_patterns: [BR_001]
    color_spec: {primary: "#0A0A0A", accents: []}
    text_spec: []
    branding_summary: "x"
    variants: []
    master: {path: null, hash: null, source: pending}
    source_files: []
    ai_renders: []
    review_flags: []
    notes: ""
""")
    with pytest.raises(ValueError, match="invalid SKU"):
        _load(tmp_path, monkeypatch, bad)


# ─── Referential (Catalog._validate_integrity) ──────────────────────────


def test_series_references_unknown_sku_surfaces_violation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    yaml_text = _catalog_yaml(series_skus="[br-001, br-ghost]")
    cat = _load(tmp_path, monkeypatch, yaml_text)
    codes = {v.code for v in cat.violations}
    assert "series_unknown_sku" in codes


def test_strict_mode_raises_integrity_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    yaml_text = _catalog_yaml(series_skus="[br-001, br-ghost]")
    with pytest.raises(IntegrityError, match="series_unknown_sku"):
        _load(tmp_path, monkeypatch, yaml_text, strict=True)


def test_unknown_collection_surfaces_violation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bad_product = """
  - sku: br-001
    name: X
    collection: ghost-collection
    price_usd: 10.00
    status: draft
    aliases: []
    filename_patterns: [br-001]
    color_spec: {primary: "#0A0A0A", accents: []}
    text_spec: []
    branding_summary: "x"
    variants: []
    master: {path: null, hash: null, source: pending}
    source_files: []
    ai_renders: []
    review_flags: []
    notes: ""
"""
    yaml_text = _catalog_yaml(product_override=bad_product)
    cat = _load(tmp_path, monkeypatch, yaml_text)
    codes = {v.code for v in cat.violations}
    assert "unknown_collection" in codes


def test_alias_collision_surfaces_violation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    two_products = """
  - sku: br-001
    name: A
    collection: black-rose
    price_usd: 10.00
    status: draft
    aliases: [br-d99]
    filename_patterns: [br-001]
    color_spec: {primary: "#0A0A0A", accents: []}
    text_spec: []
    branding_summary: "x"
    variants: []
    master: {path: null, hash: null, source: pending}
    source_files: []
    ai_renders: []
    review_flags: []
    notes: ""
  - sku: br-002
    name: B
    collection: black-rose
    price_usd: 20.00
    status: draft
    aliases: [br-d99]
    filename_patterns: [br-002]
    color_spec: {primary: "#0A0A0A", accents: []}
    text_spec: []
    branding_summary: "y"
    variants: []
    master: {path: null, hash: null, source: pending}
    source_files: []
    ai_renders: []
    review_flags: []
    notes: ""
"""
    yaml_text = _catalog_yaml(product_override=two_products, series_skus="[br-001]")
    cat = _load(tmp_path, monkeypatch, yaml_text)
    codes = {v.code for v in cat.violations}
    assert "alias_collision" in codes


def test_patch_mapping_unknown_sku_surfaces_violation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Override sku_to_patch to reference a missing SKU
    yaml_text = _catalog_yaml()
    yaml_text = yaml_text.replace(
        "sku_to_patch: {}",
        "sku_to_patch: {br-ghost: baseball}",
    )
    cat = _load(tmp_path, monkeypatch, yaml_text)
    codes = {v.code for v in cat.violations}
    assert "patch_sku_missing" in codes


def test_patch_mapping_invalid_sport_surfaces_violation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    yaml_text = _catalog_yaml()
    yaml_text = yaml_text.replace(
        "sku_to_patch: {}",
        "sku_to_patch: {br-001: cricket}",
    )
    cat = _load(tmp_path, monkeypatch, yaml_text)
    codes = {v.code for v in cat.violations}
    assert "patch_sport_invalid" in codes


def test_clean_catalog_has_no_violations(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    yaml_text = _catalog_yaml()
    cat = _load(tmp_path, monkeypatch, yaml_text)
    assert cat.violations == ()


def test_live_catalog_passes_strict_validation() -> None:
    """Sanity: the actual assets/product-masters/catalog.yaml should load strict-clean."""
    from pathlib import Path as P

    repo_root = P(__file__).resolve().parents[3]
    live = repo_root / "assets" / "product-masters" / "catalog.yaml"
    if not live.is_file():
        pytest.skip("Live catalog.yaml not present in test environment")
    cat = Catalog.load(path=live, strict=True)
    assert len(cat.violations) == 0
    assert len(cat.products_by_sku) > 0
