"""Smoke tests for skyyrose/elite_studio/fashion/context.py canonical path (INFRA-03)."""

from __future__ import annotations

from pathlib import Path


def test_catalog_path_resolves_to_canonical_csv() -> None:
    """_CATALOG_PATH must equal the canonical CATALOG_CSV (or resolve to same file)."""
    import skyyrose.elite_studio.fashion.context as ctx_mod
    from skyyrose.core.catalog_loader import CATALOG_CSV

    assert Path(str(ctx_mod._CATALOG_PATH)).resolve() == Path(str(CATALOG_CSV)).resolve()


def test_catalog_path_exists_on_disk() -> None:
    """The resolved path must be an actual file (not the stale /Users/theceo/data/... path)."""
    import skyyrose.elite_studio.fashion.context as ctx_mod

    assert Path(
        str(ctx_mod._CATALOG_PATH)
    ).is_file(), f"catalog path {ctx_mod._CATALOG_PATH} does not exist on disk"


def test_load_catalog_returns_dict_keyed_by_sku() -> None:
    """_load_catalog() must read the canonical CSV and key by SKU."""
    import skyyrose.elite_studio.fashion.context as ctx_mod

    # Reset cache so this test reads the real CSV, not a stale in-memory dict
    ctx_mod._catalog_cache = None
    catalog = ctx_mod._load_catalog()
    assert isinstance(catalog, dict)
    assert "br-001" in catalog
    assert catalog["br-001"]["name"] == "BLACK Rose Crewneck"


def test_context_reads_collection_column_not_collection_slug() -> None:
    """fashion/context.py must use 'collection' column (canonical), not 'collection_slug' (retired)."""
    import skyyrose.elite_studio.fashion.context as ctx_mod

    src = Path(ctx_mod.__file__).read_text(encoding="utf-8")
    assert (
        "collection_slug" not in src
    ), "fashion/context.py still references retired collection_slug column"
