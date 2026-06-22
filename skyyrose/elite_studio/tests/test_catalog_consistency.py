"""Tests for the catalog/registry consistency validator.

Exercises validate_catalog_consistency.py against the live canonical data sources.
All tests are read-only — no writes to disk.

Run:
    pytest skyyrose/elite_studio/tests/test_catalog_consistency.py -v
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import the validator without adding scripts/ to sys.path permanently
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[3]
_VALIDATOR_PATH = _REPO_ROOT / "scripts" / "validate_catalog_consistency.py"


def _import_validator():
    spec = importlib.util.spec_from_file_location("validate_catalog_consistency", _VALIDATOR_PATH)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    # Register in sys.modules BEFORE exec_module — Python 3.14 dataclasses introspect
    # sys.modules.get(cls.__module__).__dict__ during @dataclass decoration; without this
    # registration the lookup returns None and raises AttributeError.
    sys.modules["validate_catalog_consistency"] = mod
    try:
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    except Exception:
        sys.modules.pop("validate_catalog_consistency", None)
        raise
    return mod


@pytest.fixture(scope="module")
def validator():
    """Import the validator module once per test session."""
    if not _VALIDATOR_PATH.exists():
        pytest.skip(f"Validator not found at {_VALIDATOR_PATH}")
    return _import_validator()


# ---------------------------------------------------------------------------
# Foundation: canonical data sources must be readable
# ---------------------------------------------------------------------------


def test_csv_readable(validator) -> None:
    """Catalog CSV must be present and parseable with expected columns."""
    result = validator.check_csv_readable()
    assert result.passed, f"csv_readable failed: {result.message}\n" + "\n".join(result.details)


def test_registry_readable(validator) -> None:
    """logo-registry.json must be present and valid JSON."""
    result = validator.check_registry_readable()
    assert result.passed, f"registry_readable failed: {result.message}\n" + "\n".join(
        result.details
    )


def test_registry_version(validator) -> None:
    """Registry version must be >= 4."""
    result = validator.check_registry_version()
    assert result.passed, result.message


def test_registry_changelog(validator) -> None:
    """All changelog entries must have version, date, author, notes fields."""
    result = validator.check_registry_changelog()
    assert result.passed, f"{result.message}\n" + "\n".join(result.details)


# ---------------------------------------------------------------------------
# Jersey SKU consistency
# ---------------------------------------------------------------------------


def test_jersey_skus_match_csv(validator) -> None:
    """_JERSEY_SKUS frozenset in sku_resolver.py must exactly match CSV jersey rows."""
    result = validator.check_jersey_skus()
    assert result.passed, (
        f"Jersey SKU mismatch detected:\n{result.message}\n"
        + "\n".join(result.details)
        + "\n\nTo fix: python scripts/sync_catalog_downstream.py --dry-run"
    )


def test_jersey_skus_are_8_skus(validator) -> None:
    """Expect exactly 8 jersey SKUs (br-003 + br-008..br-012 + br-014..br-015)."""
    skus = validator._extract_jersey_skus_from_resolver()
    assert skus is not None, "Could not parse _JERSEY_SKUS from sku_resolver.py"
    assert len(skus) == 8, f"Expected 8 jersey SKUs, got {len(skus)}: {sorted(skus)}"


def test_br_013_not_in_jersey_skus(validator) -> None:
    """br-013 was retired 2026-05-25 and must not appear in _JERSEY_SKUS."""
    skus = validator._extract_jersey_skus_from_resolver()
    assert skus is not None
    assert "br-013" not in skus, "Retired SKU br-013 still in _JERSEY_SKUS frozenset"


# ---------------------------------------------------------------------------
# Logo registry checks
# ---------------------------------------------------------------------------


def test_logo_skus_all_in_catalog(validator) -> None:
    """Every SKU in sku_logos must exist in the catalog CSV."""
    result = validator.check_logo_skus()
    assert result.passed, f"{result.message}\n" + "\n".join(result.details)


def test_sku_folders_are_jersey_skus(validator) -> None:
    """Every SKU in sku_folders must be a jersey SKU per the CSV."""
    result = validator.check_sku_folders()
    assert result.passed, f"{result.message}\n" + "\n".join(result.details)


def test_collocated_logos_use_filename_key(validator) -> None:
    """Co-located logos must use 'filename' key, not 'file'."""
    result = validator.check_collocated_keys()
    assert result.passed, f"{result.message}\n" + "\n".join(result.details)


def test_brand_primary_exists_in_logos(validator) -> None:
    """brand_primary logo id must exist in the logos block."""
    result = validator.check_brand_primary()
    assert result.passed, result.message


def test_brand_primary_is_sr_monogram(validator) -> None:
    """brand_primary must be sr-monogram-rose-gold (canonical value)."""
    import json

    reg_path = _REPO_ROOT / "wordpress-theme" / "skyyrose-flagship" / "data" / "logo-registry.json"
    reg = json.loads(reg_path.read_text(encoding="utf-8"))
    assert (
        reg.get("brand_primary") == "sr-monogram-rose-gold"
    ), f"brand_primary = {reg.get('brand_primary')!r}, expected 'sr-monogram-rose-gold'"


# ---------------------------------------------------------------------------
# Product similarities checks
# ---------------------------------------------------------------------------


def test_similarities_skus_all_in_catalog(validator) -> None:
    """Top-level SKU keys in product-similarities.json must all exist in CSV."""
    result = validator.check_similarities_skus()
    assert result.passed, f"{result.message}\n" + "\n".join(result.details)


def test_similarities_refs_all_in_catalog(validator) -> None:
    """All SKUs referenced in similarity arrays must exist in the catalog CSV."""
    result = validator.check_similarities_refs()
    assert result.passed, f"{result.message}\n" + "\n".join(result.details)


def test_br_013_not_in_similarities(validator) -> None:
    """br-013 was retired and must not appear anywhere in product-similarities.json."""

    sim_path = (
        _REPO_ROOT / "wordpress-theme" / "skyyrose-flagship" / "data" / "product-similarities.json"
    )
    if not sim_path.exists():
        pytest.skip("product-similarities.json not present")
    text = sim_path.read_text(encoding="utf-8")
    assert "br-013" not in text, "Retired SKU br-013 still appears in product-similarities.json"


# ---------------------------------------------------------------------------
# Retired SKU guard
# ---------------------------------------------------------------------------


def test_no_retired_skus_in_downstream(validator) -> None:
    """No retired SKUs (br-013) should appear in any checked downstream file."""
    result = validator.check_retired_sku_guard()
    assert result.passed, f"Retired SKU reference(s) found:\n{result.message}\n" + "\n".join(
        result.details
    )


# ---------------------------------------------------------------------------
# Dossier coverage
# ---------------------------------------------------------------------------


def test_dossier_slugs_have_md_files(validator) -> None:
    """Every dossier_slug in the CSV must have a corresponding .md file."""
    result = validator.check_dossier_slugs()
    assert result.passed, f"{result.message}\n" + "\n".join(result.details)


# ---------------------------------------------------------------------------
# Full run: all checks pass together
# ---------------------------------------------------------------------------


def test_full_validator_run_passes(validator) -> None:
    """End-to-end: run all checks and assert zero failures."""
    report = validator.run_checks(quiet=True)
    failed = [r for r in report.results if not r.passed]
    if failed:
        lines = []
        for r in failed:
            lines.append(f"  FAIL [{r.name}]: {r.message}")
            for d in r.details:
                lines.append(f"       {d}")
        pytest.fail(f"{len(failed)} consistency check(s) failed:\n" + "\n".join(lines))
