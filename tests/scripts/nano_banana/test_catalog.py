"""Unit tests for scripts/nano_banana/catalog.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from nano_banana.catalog import (
    get_material_spec,
    load_catalog,
    load_products,
    load_specs,
)

# ---------------------------------------------------------------------------
# TestLoadCatalog
# ---------------------------------------------------------------------------


class TestLoadCatalog:
    """Tests for load_catalog() — raw CSV loading."""

    def test_load_catalog_returns_all_skus(self, sample_csv: Path) -> None:
        catalog = load_catalog()
        assert len(catalog) == 4
        assert set(catalog.keys()) == {"br-001", "lh-004", "sg-001", "kids-001"}

    def test_load_catalog_fields(self, sample_csv: Path) -> None:
        catalog = load_catalog()
        br = catalog["br-001"]
        assert br["name"] == "BLACK Rose Crewneck"
        assert br["collection"] == "black-rose"
        assert br["is_preorder"] is False
        assert br["output_slug"] == "black-rose-crewneck"
        assert br["is_tech_flat"] is True
        assert br["is_accessory"] is False

        lh = catalog["lh-004"]
        assert lh["is_preorder"] is True

    def test_load_catalog_source_override(self, sample_csv: Path) -> None:
        catalog = load_catalog()
        br = catalog["br-001"]
        assert "source_override" in br
        assert br["source_override"] == "black-rose-crewneck-techflat-v4.jpg"

        # lh-004 has no override — key should be absent
        lh = catalog["lh-004"]
        assert "source_override" not in lh


# ---------------------------------------------------------------------------
# TestLoadProducts
# ---------------------------------------------------------------------------


class TestLoadProducts:
    """Tests for load_products() — filtered product list building."""

    @pytest.fixture(autouse=True)
    def _setup_catalog(self, sample_csv: Path) -> None:
        """Pre-load catalog for every test in this class."""
        self.catalog = load_catalog()

    def _stub_source(self, *_args, **_kwargs) -> None:
        """Stub find_source_image to avoid filesystem hits."""
        return None

    def test_no_filter_returns_all(self) -> None:
        with patch("nano_banana.catalog.find_source_image", self._stub_source):
            products = load_products(self.catalog)
        assert len(products) == 4

    def test_sku_filter(self) -> None:
        with patch("nano_banana.catalog.find_source_image", self._stub_source):
            products = load_products(self.catalog, sku_filter="br-001")
        assert len(products) == 1
        assert products[0]["sku"] == "br-001"

    def test_collection_filter_black_rose(self) -> None:
        with patch("nano_banana.catalog.find_source_image", self._stub_source):
            products = load_products(self.catalog, collection_filter="black-rose")
        assert len(products) == 1
        assert products[0]["collection"] == "black-rose"

    def test_collection_filter_signature(self) -> None:
        with patch("nano_banana.catalog.find_source_image", self._stub_source):
            products = load_products(self.catalog, collection_filter="signature")
        assert len(products) == 1
        assert products[0]["sku"] == "sg-001"

    def test_sku_plus_collection_match(self) -> None:
        with patch("nano_banana.catalog.find_source_image", self._stub_source):
            products = load_products(
                self.catalog,
                sku_filter="br-001",
                collection_filter="black-rose",
            )
        assert len(products) == 1

    def test_sku_plus_collection_mismatch(self) -> None:
        with patch("nano_banana.catalog.find_source_image", self._stub_source):
            products = load_products(
                self.catalog,
                sku_filter="br-001",
                collection_filter="signature",
            )
        assert len(products) == 0

    def test_unknown_collection(self) -> None:
        with patch("nano_banana.catalog.find_source_image", self._stub_source):
            products = load_products(
                self.catalog,
                collection_filter="does-not-exist",
            )
        assert len(products) == 0


# ---------------------------------------------------------------------------
# TestLoadSpecs
# ---------------------------------------------------------------------------


class TestLoadSpecs:
    """Tests for load_specs() — JSON spec loading."""

    def test_load_specs(self, sample_specs_json: Path) -> None:
        specs = load_specs()
        assert len(specs) == 4
        assert "br-001" in specs
        assert specs["br-001"]["fabric"] == "heavyweight cotton fleece"

    def test_load_specs_missing_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import nano_banana.catalog as catalog_mod

        monkeypatch.setattr(catalog_mod, "SPECS_JSON", tmp_path / "nonexistent.json")
        specs = load_specs()
        assert specs == {}


# ---------------------------------------------------------------------------
# TestGetMaterialSpec
# ---------------------------------------------------------------------------


class TestGetMaterialSpec:
    """Tests for get_material_spec() — prompt injection string."""

    def test_material_spec_returns_string(self, sample_specs_json: Path) -> None:
        result = get_material_spec("br-001")
        assert "Material:" in result
        assert "heavyweight cotton fleece" in result
        assert "Texture:" in result
        assert "embossed rose-gold metallic" in result

    def test_material_spec_unknown_sku(self, sample_specs_json: Path) -> None:
        result = get_material_spec("zzz-999")
        assert result == ""
