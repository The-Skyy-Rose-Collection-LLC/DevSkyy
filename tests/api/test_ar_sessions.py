"""Tests for /api/v1/ar/* product endpoints.

Guards against the fabricated-SKU / wrong-domain regression: AR products
must come from the real catalog CSV via the SOT resolver
(skyyrose.core.sot_images.resolve_image), never a hardcoded sample list.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.ar_sessions import (
    _ar_product_from_row,
    ar_sessions_router,
    get_ar_products_from_catalog,
)

app = FastAPI()
app.include_router(ar_sessions_router, prefix="/api/v1")
client = TestClient(app)


def test_all_image_urls_use_production_domain() -> None:
    products = client.get("/api/v1/ar/products").json()
    assert products, "expected at least one AR product from the real catalog"
    for product in products:
        assert product["image_url"].startswith(
            "https://skyyrose.co/"
        ), f"{product['id']} image_url does not use skyyrose.co: {product['image_url']}"


def test_no_fabricated_skus_appear() -> None:
    products = client.get("/api/v1/ar/products", params={"limit": 200}).json()
    ids = {p["id"] for p in products}
    fabricated = {
        "br-sherpa-001",
        "br-hoodie-002",
        "lh-windbreaker-001",
        "lh-joggers-002",
        "sig-beanie-001",
        "sig-tee-002",
    }
    assert not (ids & fabricated), f"fabricated SKUs leaked into AR products: {ids & fabricated}"


def test_kids_capsule_products_are_included() -> None:
    products = client.get("/api/v1/ar/products/kids_capsule", params={"limit": 100}).json()
    ids = {p["id"] for p in products}
    assert ids, "kids_capsule collection returned no AR products"
    assert ids <= {"kids-001", "kids-002"}
    for product in products:
        assert product["collection"] == "kids_capsule"
        assert product["image_url"].startswith("https://skyyrose.co/")


def test_get_ar_products_from_catalog_matches_real_catalog_skus() -> None:
    from skyyrose.core.sot_images import all_skus

    products = get_ar_products_from_catalog()
    ids = {p.id for p in products}
    # Every returned SKU must be a real, SOT-resolvable SKU.
    assert ids <= set(all_skus())
    assert ids, "expected the real catalog to yield at least one AR product"


class TestRowPolicy:
    """Direct tests of _ar_product_from_row on synthetic rows.

    Guards the published/is_preorder string semantics: the catalog writes
    "1"/"0" but sibling consumers (scripts/batch_flux_collections.py) also
    accept "true"/"false" — a literal "false" must never count as published.
    """

    @staticmethod
    def _row(**overrides: str) -> dict[str, str]:
        from skyyrose.core.sot_images import all_skus, resolve_image

        sku = next(s for s in all_skus() if resolve_image(s, "front"))
        base = {
            "sku": sku,
            "name": "Synthetic Test Row",
            "collection": "black-rose",
            "published": "1",
            "is_preorder": "0",
            "price": "120",
            "garment_type_lock": "hoodie",
        }
        return {**base, **overrides}

    def test_published_false_string_is_skipped(self) -> None:
        assert _ar_product_from_row(self._row(published="false")) is None

    def test_published_zero_and_blank_are_skipped(self) -> None:
        assert _ar_product_from_row(self._row(published="0")) is None
        assert _ar_product_from_row(self._row(published="")) is None

    def test_unknown_published_value_fails_closed(self) -> None:
        assert _ar_product_from_row(self._row(published="banana")) is None

    def test_preorder_true_string_rescues_unpublished_row(self) -> None:
        product = _ar_product_from_row(self._row(published="false", is_preorder="true"))
        assert product is not None

    def test_published_row_is_emitted(self) -> None:
        product = _ar_product_from_row(self._row())
        assert product is not None
        assert product.image_url.startswith("https://skyyrose.co/")

    def test_unparsable_price_defaults_to_zero_and_logs(self, caplog) -> None:
        with caplog.at_level(logging.WARNING, logger="api.ar_sessions"):
            product = _ar_product_from_row(self._row(price="not-a-number"))
        assert product is not None
        assert product.price == 0.0
        assert "unparsable price" in caplog.text
