"""CI gate — every active SKU must have a schema-valid dossier.

Reads the canonical CSV at
``wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`` and asserts
that every row's ``dossier_slug`` resolves to a markdown file that parses
cleanly through ``DossierSchema``. Schema failures fail CI loudly.

Hex/Pantone color coverage is **warned, not enforced**, in this first pass.
After Corey's hex backfill PR ships, promote the hex-coverage assertion
to required (uncomment the block at the bottom).
"""

from __future__ import annotations

import warnings

import pytest

from skyyrose.core.catalog_loader import read_catalog_rows
from skyyrose.core.dossier_loader import DossierMissingError
from skyyrose.core.dossier_schema import (
    DossierSchemaError,
    coverage_for,
    load_validated_for_sku,
)

# Materialize the catalog once at module load so each parametrized test gets
# its own row without re-reading the CSV per test.
_ACTIVE_SKUS = [row["sku"] for row in read_catalog_rows() if row.get("sku")]


def test_catalog_has_active_skus():
    """Sanity check — the catalog should have at least 30 active SKUs."""
    assert len(_ACTIVE_SKUS) >= 30, (
        f"expected ≥30 active SKUs in canonical CSV, got {len(_ACTIVE_SKUS)}"
    )


@pytest.mark.parametrize("sku", _ACTIVE_SKUS)
def test_dossier_schema_valid(sku: str):
    """Every active SKU's dossier passes schema validation."""
    try:
        schema = load_validated_for_sku(sku)
    except DossierMissingError as exc:
        pytest.fail(f"{sku}: dossier missing — {exc}")
    except DossierSchemaError as exc:
        pytest.fail(f"{sku}: schema validation failed — {exc}")

    # Sanity invariants
    assert schema.branding, f"{sku}: schema produced 0 branding regions"
    assert schema.negative, f"{sku}: schema produced 0 negative items"
    assert schema.garment_type_lock, f"{sku}: garment_type_lock empty"


@pytest.mark.parametrize("sku", _ACTIVE_SKUS)
def test_dossier_warnings_logged(sku: str):
    """Per-SKU coverage report — warns on missing hex/Pantone (not a failure)."""
    schema = load_validated_for_sku(sku)
    cov = coverage_for(schema)
    if cov.warnings:
        # We surface warnings via pytest's capture so CI logs flag the gap
        # without failing the build. After hex backfill, the assertion below
        # can replace this warning block.
        warnings.warn(
            f"{sku}: dossier coverage warnings — {'; '.join(cov.warnings)}",
            UserWarning,
            stacklevel=1,
        )

    # Lower bound: every dossier must declare at least one branding region.
    # This is the actual hard contract the compositor depends on.
    assert cov.region_count >= 1, f"{sku}: 0 branding regions parsed"


# Promote to enforced when hex backfill is complete:
#
# @pytest.mark.parametrize("sku", _ACTIVE_SKUS)
# def test_dossier_hex_coverage_at_least_50pct(sku: str):
#     schema = load_validated_for_sku(sku)
#     cov = coverage_for(schema)
#     assert cov.hex_coverage_pct >= 50.0, (
#         f"{sku}: hex coverage {cov.hex_coverage_pct}% (target ≥50%)"
#     )
