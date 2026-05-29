import pytest

from skyyrose.elite_studio.platform.catalog_source import (
    CatalogSource,
    ProductRecord,
    SkyyRoseCatalogSource,
)


def test_skyyrose_source_satisfies_protocol():
    assert isinstance(SkyyRoseCatalogSource(), CatalogSource)


def test_get_br001_returns_record_with_dossier():
    rec = SkyyRoseCatalogSource().get("br-001")
    assert isinstance(rec, ProductRecord)
    assert rec.sku == "br-001"
    assert rec.dossier  # non-empty dossier dict
    assert rec.garment_type_lock  # pulled from dossier


def test_get_missing_sku_raises_keyerror():
    with pytest.raises(KeyError):
        SkyyRoseCatalogSource().get("zz-999")


def test_references_returns_existing_views_only():
    src = SkyyRoseCatalogSource()
    refs = src.references("br-001")
    # br-001 has front only (no back.jpg) -> exactly the views that exist on disk
    assert "front" in refs
    assert "back" not in refs  # br-001 has no back golden
    assert all(p.exists() for p in refs.values())
