"""Tests for Phase-2 catalog-pipeline hardening.

Covers the five new validator invariants added in feat/catalog-hardening:
  - price_positive
  - collection_enum
  - unique_skus
  - dossier_present
  - badge_enum

Each invariant has:
  (a) one PASS test against the real CSV
  (b) one FAIL test against a crafted bad-row tmp CSV

Pattern follows test_v7_cards_generator.py: load the validator by file path,
monkeypatch ``validator._CATALOG_CSV`` to point at the tmp CSV, call
``validator.check_*()`` directly.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _load(mod_name: str, rel_path: str):
    spec = importlib.util.spec_from_file_location(mod_name, _REPO_ROOT / rel_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


# Load the validator module once at import time (same as test_v7_cards_generator.py).
# Each test that needs a tmp CSV will monkeypatch validator._CATALOG_CSV so _load_csv()
# reads the crafted file instead of the real one.
validator = _load(
    "validate_catalog_consistency_hardening", "scripts/validate_catalog_consistency.py"
)


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

# Minimal full-column row factory — covers every column the new checks read.
_ALL_COLS = [
    "sku",
    "name",
    "price",
    "collection",
    "badge",
    "is_preorder",
    "published",
    "dossier_slug",
    "description",
    "image",
    "front_model_image",
    "back_image",
    "back_model_image",
    "sizes",
    "color",
    "edition_size",
    "branding_spec",
    "render_output_slug",
    "render_source_override",
    "render_back_source_override",
    "render_is_tech_flat",
    "render_is_accessory",
    "garment_type_lock",
    "engine_override",
]


def _row(
    sku: str,
    *,
    price: str = "95",
    collection: str = "black-rose",
    badge: str = "",
    is_preorder: str = "0",
    published: str = "1",
    dossier_slug: str = "test-dossier",
    **over,
) -> dict:
    """Minimal CSV row for the columns the new checks read."""
    base: dict[str, str] = dict.fromkeys(_ALL_COLS, "")
    base.update(
        {
            "sku": sku,
            "price": price,
            "collection": collection,
            "badge": badge,
            "is_preorder": is_preorder,
            "published": published,
            "dossier_slug": dossier_slug,
        }
    )
    base.update(over)
    return base


def _write_csv(tmp_path: Path, rows: list[dict]) -> Path:
    """Write rows to a tmp CSV using the canonical column set."""
    cols = _ALL_COLS
    lines = [",".join(cols)]
    for r in rows:
        lines.append(",".join(r.get(c, "") for c in cols))
    p = tmp_path / "catalog.csv"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# check_price_positive
# ---------------------------------------------------------------------------


class TestPricePositive:
    def test_passes_on_real_csv(self):
        """Real CSV: all published SKUs have a price > 0."""
        result = validator.check_price_positive()
        assert result.passed, result.message

    def test_fails_on_published_row_with_zero_price(self, tmp_path, monkeypatch):
        csv_path = _write_csv(tmp_path, [_row("xx-001", price="0", published="1")])
        monkeypatch.setattr(validator, "_CATALOG_CSV", csv_path)
        result = validator.check_price_positive()
        assert not result.passed
        assert any("xx-001" in d for d in result.details)

    def test_passes_when_only_unpublished_row_has_zero_price(self, tmp_path, monkeypatch):
        """Un-published rows with price=0 must NOT trigger a failure."""
        csv_path = _write_csv(
            tmp_path,
            [
                _row("xx-001", price="0", published="0"),
                _row("xx-002", price="75", published="1"),
            ],
        )
        monkeypatch.setattr(validator, "_CATALOG_CSV", csv_path)
        result = validator.check_price_positive()
        assert result.passed, result.message

    def test_fails_on_non_integer_price_for_published(self, tmp_path, monkeypatch):
        csv_path = _write_csv(tmp_path, [_row("xx-001", price="free", published="1")])
        monkeypatch.setattr(validator, "_CATALOG_CSV", csv_path)
        result = validator.check_price_positive()
        assert not result.passed


# ---------------------------------------------------------------------------
# check_collection_enum
# ---------------------------------------------------------------------------


class TestCollectionEnum:
    def test_passes_on_real_csv(self):
        """Real CSV: all rows use one of the four canonical collections."""
        result = validator.check_collection_enum()
        assert result.passed, result.message

    def test_fails_on_invalid_collection(self, tmp_path, monkeypatch):
        csv_path = _write_csv(tmp_path, [_row("xx-001", collection="typo-collection")])
        monkeypatch.setattr(validator, "_CATALOG_CSV", csv_path)
        result = validator.check_collection_enum()
        assert not result.passed
        assert any("xx-001" in d for d in result.details)

    def test_passes_all_four_valid_collections(self, tmp_path, monkeypatch):
        rows = [
            _row("sg-001", collection="signature"),
            _row("br-001", collection="black-rose"),
            _row("lh-001", collection="love-hurts"),
            _row("kc-001", collection="kids-capsule"),
        ]
        csv_path = _write_csv(tmp_path, rows)
        monkeypatch.setattr(validator, "_CATALOG_CSV", csv_path)
        result = validator.check_collection_enum()
        assert result.passed, result.message


# ---------------------------------------------------------------------------
# check_unique_skus
# ---------------------------------------------------------------------------


class TestUniqueSkus:
    def test_passes_on_real_csv(self):
        """Real CSV: all 33 SKUs are unique."""
        result = validator.check_unique_skus()
        assert result.passed, result.message

    def test_fails_on_duplicate_sku(self, tmp_path, monkeypatch):
        csv_path = _write_csv(
            tmp_path,
            [
                _row("br-001"),
                _row("br-001"),  # duplicate
            ],
        )
        monkeypatch.setattr(validator, "_CATALOG_CSV", csv_path)
        result = validator.check_unique_skus()
        assert not result.passed
        assert any("br-001" in d for d in result.details)

    def test_passes_with_distinct_skus(self, tmp_path, monkeypatch):
        csv_path = _write_csv(tmp_path, [_row("a-1"), _row("a-2"), _row("a-3")])
        monkeypatch.setattr(validator, "_CATALOG_CSV", csv_path)
        result = validator.check_unique_skus()
        assert result.passed, result.message


# ---------------------------------------------------------------------------
# check_dossier_present
# ---------------------------------------------------------------------------


class TestDossierPresent:
    def test_passes_on_real_csv(self):
        """Real CSV: all 33 rows have a non-empty dossier_slug."""
        result = validator.check_dossier_present()
        assert result.passed, result.message

    def test_fails_on_row_with_empty_dossier_slug(self, tmp_path, monkeypatch):
        csv_path = _write_csv(tmp_path, [_row("xx-001", dossier_slug="")])
        monkeypatch.setattr(validator, "_CATALOG_CSV", csv_path)
        result = validator.check_dossier_present()
        assert not result.passed
        assert any("xx-001" in d for d in result.details)

    def test_passes_when_all_rows_have_slug(self, tmp_path, monkeypatch):
        csv_path = _write_csv(
            tmp_path,
            [
                _row("a-1", dossier_slug="slug-a"),
                _row("a-2", dossier_slug="slug-b"),
            ],
        )
        monkeypatch.setattr(validator, "_CATALOG_CSV", csv_path)
        result = validator.check_dossier_present()
        assert result.passed, result.message


# ---------------------------------------------------------------------------
# check_badge_enum
# ---------------------------------------------------------------------------


class TestBadgeEnum:
    def test_passes_on_real_csv(self):
        """Real CSV: all badge values are '' or 'Pre-Order'."""
        result = validator.check_badge_enum()
        assert result.passed, result.message

    def test_fails_on_invalid_badge(self, tmp_path, monkeypatch):
        csv_path = _write_csv(tmp_path, [_row("xx-001", badge="New Arrival")])
        monkeypatch.setattr(validator, "_CATALOG_CSV", csv_path)
        result = validator.check_badge_enum()
        assert not result.passed
        assert any("xx-001" in d for d in result.details)

    def test_passes_with_empty_and_preorder_badges(self, tmp_path, monkeypatch):
        csv_path = _write_csv(
            tmp_path,
            [
                _row("a-1", badge=""),
                _row("a-2", badge="Pre-Order", is_preorder="1"),
            ],
        )
        monkeypatch.setattr(validator, "_CATALOG_CSV", csv_path)
        result = validator.check_badge_enum()
        assert result.passed, result.message

    def test_fails_on_lowercase_badge_variant(self, tmp_path, monkeypatch):
        """'pre-order' (lowercase) is NOT in the valid set — the CSV uses 'Pre-Order'."""
        csv_path = _write_csv(tmp_path, [_row("xx-001", badge="pre-order", is_preorder="1")])
        monkeypatch.setattr(validator, "_CATALOG_CSV", csv_path)
        result = validator.check_badge_enum()
        assert not result.passed
