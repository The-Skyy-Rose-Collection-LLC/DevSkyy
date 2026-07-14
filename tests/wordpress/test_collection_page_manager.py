"""Tests for wordpress.collection_page_manager — verifies SSoT migration.

The module is a thin adapter that reads from brand.yaml + catalog.yaml.
These tests confirm:
  - All 4 collections resolve (including KIDS, which was missing pre-migration)
  - Product SKU lists come from catalog (not hardcoded)
  - Colors come from brand.yaml palette
  - Tagline on every collection is the ACTIVE brand tagline (not retired)
  - No hardcoded "Where Love Meets Luxury" can appear
"""

from __future__ import annotations

import pytest

from skyyrose.elite_studio.brand import BrandConfig
from skyyrose.elite_studio.catalog import Catalog
from tests.sparse_guard import requires_tree
from wordpress.collection_page_manager import (
    CollectionDesignTemplates,
    CollectionTemplate,
    CollectionType,
)

pytest.importorskip("yaml")

# BrandConfig.load()/Catalog.load() read assets/brand/*.yaml — sparse worktrees
# exclude assets/ by design; full checkouts and CI still fail closed if missing.
pytestmark = requires_tree("assets/brand")


def test_all_four_collections_resolve() -> None:
    templates = CollectionDesignTemplates.get_all_templates()
    assert set(templates.keys()) == {
        CollectionType.BLACK_ROSE,
        CollectionType.LOVE_HURTS,
        CollectionType.SIGNATURE,
        CollectionType.KIDS,
    }


def test_product_lists_come_from_catalog() -> None:
    """Product SKUs must match catalog.products_in_collection, NOT a hardcoded list."""
    cat = Catalog.load()
    for ct in CollectionType:
        t = CollectionDesignTemplates.get_template(ct)
        catalog_skus = [p.sku for p in cat.products_in_collection(ct.value, active_only=True)]
        assert t.metadata["products"] == catalog_skus, (
            f"{ct.value}: template product list {t.metadata['products']} "
            f"does not match catalog {catalog_skus}"
        )


def test_tagline_is_always_active_brand_tagline() -> None:
    """Every collection template exposes the ACTIVE tagline, never a stale one."""
    brand = BrandConfig.load()
    for ct in CollectionType:
        t = CollectionDesignTemplates.get_template(ct)
        assert t.metadata["tagline"] == brand.tagline_active


def test_colors_come_from_brand_palette() -> None:
    """Colors dict must come from brand.yaml collection palette."""
    brand = BrandConfig.load()
    for ct in CollectionType:
        t = CollectionDesignTemplates.get_template(ct)
        cb = brand.collection(ct.value)
        assert t.colors == dict(cb.palette), f"{ct.value}: colors drifted from brand.yaml palette"


def test_no_retired_tagline_anywhere_in_templates() -> None:
    """Enforcement: retired taglines must never appear in rendered templates."""
    brand = BrandConfig.load()
    for ct in CollectionType:
        t = CollectionDesignTemplates.get_template(ct)
        as_dict = t.to_dict()
        serialized = str(as_dict)
        for retired in brand.retired_taglines:
            assert (
                retired not in serialized
            ), f"{ct.value}: retired tagline {retired!r} leaked into template"


def test_to_agent_reference_includes_recovery_steps() -> None:
    ref = CollectionDesignTemplates.to_agent_reference(CollectionType.BLACK_ROSE)
    assert ref["collection"] == "black-rose"
    assert "recovery_steps" in ref
    assert len(ref["recovery_steps"]) >= 4


def test_kids_collection_included() -> None:
    """Regression: KIDS was missing from the enum pre-migration."""
    kids = CollectionDesignTemplates.get_template(CollectionType.KIDS)
    assert isinstance(kids, CollectionTemplate)
    assert "kids" in kids.html_file_path.lower()
