"""Collection data integrity tests — DATA-02 and DATA-03.

Verifies that the canonical catalog CSV satisfies:
  - DATA-02: Named pre-order SKUs are flagged with pre_order=1 in the CSV.
  - DATA-03: No SKU appears in a collection that does not match its SKU prefix.

These requirements are already marked [x] in REQUIREMENTS.md.  This suite
provides a regression gate that catches any future CSV drift.

Run: python -m pytest tests/test_collection_data_integrity.py -v
"""

from __future__ import annotations

import pytest

from skyyrose.core.catalog_loader import (
    CATALOG_CSV,
    bool_col,
    read_catalog_rows,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_COLLECTIONS = {"black-rose", "love-hurts", "signature", "kids-capsule"}

SKU_PREFIX_TO_COLLECTION: dict[str, str] = {
    "br-": "black-rose",
    "lh-": "love-hurts",
    "sg-": "signature",
    "kc-": "kids-capsule",
}

# Only SKUs confirmed present in the CSV as pre-order rows.
# Retired SKUs (lh-001, sg-d01, br-d01..d04) are absent from the CSV
# and must NOT appear here — asserting their pre_order flag would KeyError.
# br-004 and br-005 are available (not pre-order) — excluded intentionally.
PRE_ORDER_SKUS: frozenset[str] = frozenset({"br-003", "br-006", "sg-001"})


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def rows() -> list[dict[str, str]]:
    return read_catalog_rows(CATALOG_CSV)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_preorder_skus_flagged(rows: list[dict[str, str]]) -> None:
    """DATA-02: Named pre-order SKUs must be flagged pre-order in catalog CSV.

    Checks both 'pre_order' and 'is_preorder' column names to be resilient
    against minor header naming differences.
    """
    catalog: dict[str, dict[str, str]] = {r["sku"]: r for r in rows}

    for sku in PRE_ORDER_SKUS:
        assert sku in catalog, (
            f"SKU {sku!r} not found in catalog — was it retired? "
            f"Update PRE_ORDER_SKUS in this test file."
        )
        row = catalog[sku]
        flagged = bool_col(row, "pre_order") or bool_col(row, "is_preorder")
        assert flagged, (
            f"SKU {sku!r} expected to be flagged pre-order in catalog CSV "
            f"(pre_order={row.get('pre_order')!r}, is_preorder={row.get('is_preorder')!r})"
        )


def test_no_cross_collection_sku_leakage(rows: list[dict[str, str]]) -> None:
    """DATA-03: Each SKU's collection column must match its SKU prefix.

    SKUs with no known prefix are skipped — they are not a leakage case.
    """
    for row in rows:
        sku = (row.get("sku") or "").strip()
        if not sku:
            continue
        declared = (row.get("collection") or "").strip()
        for prefix, expected_collection in SKU_PREFIX_TO_COLLECTION.items():
            if sku.startswith(prefix):
                assert declared == expected_collection, (
                    f"SKU {sku!r} has prefix {prefix!r} implying collection "
                    f"{expected_collection!r} but collection column is {declared!r}"
                )
                break  # prefix matched — no need to check remaining prefixes


def test_collections_are_valid(rows: list[dict[str, str]]) -> None:
    """Every non-empty collection value must be one of the four known slugs."""
    for row in rows:
        collection = (row.get("collection") or "").strip()
        if not collection:
            continue
        assert collection in VALID_COLLECTIONS, (
            f"SKU {row.get('sku', '?')!r} has unknown collection {collection!r}; "
            f"expected one of {sorted(VALID_COLLECTIONS)}"
        )
