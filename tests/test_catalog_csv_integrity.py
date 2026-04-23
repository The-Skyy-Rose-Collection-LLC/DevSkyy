"""Integrity smoke tests for the canonical product catalog CSV.

Covers the schema, row count, and hard rules that must never regress:
  - 30 active SKUs
  - No duplicate SKU codes
  - Every product has a name, collection, and price > 0
  - No retired SKU code appears as an active row
  - Every image path referenced actually exists on disk
  - Both Python loaders (nano_banana + elite_studio) agree on the SKU set
"""

from __future__ import annotations

import pytest

from skyyrose.core.catalog_loader import (
    CATALOG_CSV,
    PRODUCT_STATUS,
    bool_col,
    int_col,
    read_catalog_rows,
    status_from_row,
)

EXPECTED_SKU_COUNT = 30

EXPECTED_COLUMNS = {
    "sku",
    "name",
    "price",
    "collection",
    "description",
    "badge",
    "image",
    "front_model_image",
    "back_image",
    "back_model_image",
    "sizes",
    "color",
    "edition_size",
    "published",
    "is_preorder",
    "branding_spec",
    "render_output_slug",
    "render_source_override",
    "render_back_source_override",
    "render_is_tech_flat",
    "render_is_accessory",
    "garment_type_lock",
}

VALID_COLLECTIONS = {"black-rose", "love-hurts", "signature", "kids-capsule"}

RETIRED_SKU_CODES = {
    "lh-001",
    "sg-004",
    "sg-008",
    "sg-010",
    "br-d01",
    "br-d02",
    "br-d03",
    "br-d04",
    "sg-d01",
    "sg-d02",
    "sg-d03",
    "sg-d04",
}


@pytest.fixture(scope="module")
def rows() -> list[dict[str, str]]:
    return read_catalog_rows(CATALOG_CSV)


def test_canonical_csv_exists() -> None:
    assert CATALOG_CSV.is_file(), f"canonical CSV not found at {CATALOG_CSV}"


def test_schema_has_all_expected_columns() -> None:
    with CATALOG_CSV.open(newline="", encoding="utf-8") as f:
        header_line = f.readline().rstrip("\n")
    header_cols = {c.strip() for c in header_line.split(",")}
    missing = EXPECTED_COLUMNS - header_cols
    assert not missing, f"canonical CSV missing required columns: {sorted(missing)}"


def test_row_count_matches_expected(rows: list[dict[str, str]]) -> None:
    assert len(rows) == EXPECTED_SKU_COUNT, f"expected {EXPECTED_SKU_COUNT} rows, got {len(rows)}"


def test_skus_are_unique(rows: list[dict[str, str]]) -> None:
    skus = [r["sku"].strip() for r in rows]
    duplicates = {sku for sku in skus if skus.count(sku) > 1}
    assert not duplicates, f"duplicate SKUs: {sorted(duplicates)}"


def test_no_retired_sku_is_active(rows: list[dict[str, str]]) -> None:
    offenders = [r["sku"] for r in rows if r["sku"].strip() in RETIRED_SKU_CODES]
    assert not offenders, f"retired SKU codes must not appear as active rows: {offenders}"


@pytest.mark.parametrize("field", ["name", "collection"])
def test_required_text_fields_non_empty(rows: list[dict[str, str]], field: str) -> None:
    empty = [r["sku"] for r in rows if not (r.get(field) or "").strip()]
    assert not empty, f"SKUs with empty {field}: {empty}"


def test_collections_are_valid(rows: list[dict[str, str]]) -> None:
    for r in rows:
        slug = r["collection"].strip()
        assert slug in VALID_COLLECTIONS, (
            f"{r['sku']}: unknown collection {slug!r} (valid: {sorted(VALID_COLLECTIONS)})"
        )


def test_prices_are_positive(rows: list[dict[str, str]]) -> None:
    for r in rows:
        price = float(r.get("price") or 0)
        assert price > 0, f"{r['sku']}: price must be > 0, got {price}"


def test_edition_size_is_positive_when_set(rows: list[dict[str, str]]) -> None:
    for r in rows:
        size = int_col(r, "edition_size")
        if size is not None:
            assert size >= 1, f"{r['sku']}: edition_size must be >= 1, got {size}"


def test_status_derivation_produces_valid_enum(rows: list[dict[str, str]]) -> None:
    for r in rows:
        status = status_from_row(r)
        assert status in PRODUCT_STATUS, (
            f"{r['sku']}: status {status!r} not in {sorted(PRODUCT_STATUS)}"
        )


def test_boolean_columns_are_one_or_zero(rows: list[dict[str, str]]) -> None:
    bool_cols = ["published", "is_preorder", "render_is_tech_flat", "render_is_accessory"]
    for r in rows:
        for col in bool_cols:
            raw = (r.get(col) or "").strip()
            assert raw in ("", "0", "1"), f"{r['sku']}: {col} must be blank / 0 / 1, got {raw!r}"


def test_primary_image_paths_resolve(rows: list[dict[str, str]]) -> None:
    theme_root = CATALOG_CSV.parent.parent  # wordpress-theme/skyyrose-flagship/
    missing: list[str] = []
    for r in rows:
        rel = r["image"].strip()
        if not rel:
            continue
        path = theme_root / rel
        if not path.is_file():
            missing.append(f"{r['sku']} → {rel}")
    assert not missing, f"primary image paths do not exist: {missing[:5]}"


def test_python_loaders_agree_on_sku_set() -> None:
    """nano_banana.load_catalog() and elite_studio.Catalog.load() must see the same SKUs."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    from nano_banana.catalog import load_catalog

    from skyyrose.elite_studio.catalog import Catalog

    nano_skus = set(load_catalog().keys())
    elite_skus = set(Catalog.load().products_by_sku.keys())

    only_in_nano = nano_skus - elite_skus
    only_in_elite = elite_skus - nano_skus
    assert not only_in_nano and not only_in_elite, (
        f"SKU mismatch — nano-only: {only_in_nano}, elite-only: {only_in_elite}"
    )


def test_bool_col_helper_parses_1_as_true() -> None:
    assert bool_col({"flag": "1"}, "flag") is True
    assert bool_col({"flag": "0"}, "flag") is False
    assert bool_col({"flag": ""}, "flag") is False
    assert bool_col({}, "flag") is False
    assert bool_col({"flag": "  1  "}, "flag") is True


def test_int_col_helper_parses_positive_ints() -> None:
    assert int_col({"n": "150"}, "n") == 150
    assert int_col({"n": "0"}, "n") is None
    assert int_col({"n": ""}, "n") is None
    assert int_col({"n": "not-a-number"}, "n") is None
    assert int_col({}, "n") is None


ALLOWED_GARMENT_TYPES = {
    "crewneck",
    "joggers",
    "jersey",
    "hoodie",
    "jacket",
    "bomber jacket",
    "shorts",
    "shirt",
    "sweatpants",
    "set",
}


def test_garment_type_lock_non_empty_for_garment_skus(rows: list[dict[str, str]]) -> None:
    """Every non-accessory row has a non-empty garment_type_lock (INFRA-04)."""
    missing = [
        r["sku"]
        for r in rows
        if not bool_col(r, "render_is_accessory") and not (r.get("garment_type_lock") or "").strip()
    ]
    assert not missing, f"garment rows with empty garment_type_lock: {missing}"


def test_garment_type_lock_empty_for_accessories(rows: list[dict[str, str]]) -> None:
    """Accessory rows (sg-007, lh-005) have empty garment_type_lock."""
    for r in rows:
        if bool_col(r, "render_is_accessory"):
            val = (r.get("garment_type_lock") or "").strip()
            assert not val, f"{r['sku']}: accessory must have empty garment_type_lock, got {val!r}"


def test_garment_type_lock_values_are_in_allowed_set(rows: list[dict[str, str]]) -> None:
    """All non-empty garment_type_lock values belong to the allowed set."""
    for r in rows:
        val = (r.get("garment_type_lock") or "").strip()
        if val:
            assert val in ALLOWED_GARMENT_TYPES, (
                f"{r['sku']}: garment_type_lock {val!r} not in {ALLOWED_GARMENT_TYPES}"
            )


def test_all_28_in_scope_garments_have_garment_type_lock(rows: list[dict[str, str]]) -> None:
    """Every non-accessory row has a non-empty garment_type_lock.

    Count is derived from render_is_accessory flag (not hardcoded) so adding
    a new garment to the catalog without filling garment_type_lock is caught.
    """
    garment_rows = [r for r in rows if not bool_col(r, "render_is_accessory")]
    missing = [r["sku"] for r in garment_rows if not (r.get("garment_type_lock") or "").strip()]
    assert not missing, f"{len(missing)} garment row(s) with empty garment_type_lock: {missing}"
    # Cross-check: total with values must equal total non-accessory rows
    count_with_value = sum(1 for r in rows if (r.get("garment_type_lock") or "").strip())
    assert count_with_value == len(garment_rows), (
        f"expected {len(garment_rows)} garment_type_lock values, got {count_with_value}"
    )
