"""Smoke tests for renders/config.py — import guard and PRODUCT_CATALOG shape (INFRA-03)."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_renders_config_imports_without_error() -> None:
    """renders/config.py must import cleanly (PRODUCT_CATALOG built at import time)."""
    import renders.config as cfg  # noqa: F401

    assert hasattr(cfg, "PRODUCT_CATALOG")
    assert hasattr(cfg, "PRODUCTS_DIR")
    assert hasattr(cfg, "_find_bundle_dir")


def test_product_catalog_is_a_list_of_dicts() -> None:
    from renders.config import PRODUCT_CATALOG

    assert isinstance(PRODUCT_CATALOG, list)
    # Skip length assertion in environments without data/product-bundles/
    # (e.g. stripped CI clones). _build_product_catalog() returns [] there by design.
    if PRODUCT_CATALOG:
        assert len(PRODUCT_CATALOG) == 30, f"expected 30 canonical SKUs, got {len(PRODUCT_CATALOG)}"
        assert all(isinstance(p, dict) for p in PRODUCT_CATALOG)
        assert all("sku" in p for p in PRODUCT_CATALOG)


def test_products_dir_is_a_path_under_wordpress_theme() -> None:
    from renders.config import PRODUCTS_DIR

    assert isinstance(PRODUCTS_DIR, Path)
    assert "wordpress-theme" in str(PRODUCTS_DIR)
    assert str(PRODUCTS_DIR).endswith("products")


def test_find_bundle_dir_resolves_by_sku() -> None:
    """The resolver scans manifest.json SKU field, not directory names."""
    from renders.config import _find_bundle_dir

    result = _find_bundle_dir(sku="br-001")
    assert result is not None
    assert result.is_dir()
    assert (result / "manifest.json").exists()


def test_find_bundle_dir_returns_none_for_unknown_sku() -> None:
    from renders.config import _find_bundle_dir

    result = _find_bundle_dir(sku="xx-999")
    assert result is None
