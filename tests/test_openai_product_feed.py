"""Tests for the OpenAI product feed generator (scripts/openai_feed/).

Pure-function tests only — no network calls. Fixture dicts below are trimmed
samples pulled from the real WooCommerce snapshot at
data/audits/openai-feed/wc-products-2026-07-08.json (fetched 2026-07-08), plus
one hand-built synthetic variable-product fixture (labeled below) to exercise
the variant-mapping path, since the live store currently has zero variable
products.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.openai_feed.catalog import DEFAULT_CATALOG_PATH, load_catalog
from scripts.openai_feed.constants import DEFAULT_CONSTANTS, FeedConstants
from scripts.openai_feed.mapping import (
    clean_text,
    map_product_to_feed_items,
    map_simple_product,
    resolve_availability,
)
from scripts.openai_feed.validation import partition_items, validate_feed_item
from scripts.openai_feed.writer import write_csv_feed, write_exclusions

# --- Fixtures sampled from data/audits/openai-feed/wc-products-2026-07-08.json ---

WC_SIMPLE_IN_STOCK = {
    "id": 9954,
    "sku": "sg-014",
    "type": "simple",
    "status": "publish",
    "name": "Mint &amp; Lavender Sweatpants",
    "permalink": "https://skyyrose.co/product/sg-014/",
    "description": "<p>Pastel luxury meets streetwear comfort. Mint and lavender sweatpants with signature rose detail.</p>\n",
    "short_description": "<p>Pastel luxury meets streetwear comfort.</p>\n",
    "price": "45",
    "regular_price": "45",
    "stock_status": "instock",
    "images": [
        {
            "src": "https://i0.wp.com/skyyrose.co/wp-content/uploads/2026/06/mint-lavender-sweatpants-front-model.webp?fit=1024%2C1024&ssl=1"
        },
        {
            "src": "https://i0.wp.com/skyyrose.co/wp-content/uploads/2026/06/mint-lavender-sweatpants-back-model.webp"
        },
    ],
    "categories": [{"name": "Uncategorized"}],
    "variations": [],
}

WC_SIMPLE_PREORDER = {
    "id": 9866,
    "sku": "br-003",
    "type": "simple",
    "status": "publish",
    "name": "BLACK is Beautiful Jersey Series: 0. Baseball Classic (Black)",
    "permalink": "https://skyyrose.co/product/br-003/",
    "description": "<p>Limited edition jersey.</p>\n",
    "short_description": "",
    "price": "120",
    "regular_price": "120",
    "stock_status": "instock",  # WC reports instock even for preorder SKUs — see mapping.py docstring
    "images": [
        {
            "src": "https://i0.wp.com/skyyrose.co/wp-content/uploads/2026/03/br-003-baseball-classic.jpeg"
        }
    ],
    "categories": [{"name": "Black Rose"}],
    "variations": [],
}

WC_NO_IMAGES_OUT_OF_STOCK = {
    "id": 1,
    "sku": "test-no-image",
    "type": "simple",
    "status": "publish",
    "name": "Test Item",
    "permalink": "https://skyyrose.co/product/test-no-image/",
    "description": "<p>Test description.</p>",
    "short_description": "",
    "price": "10",
    "regular_price": "10",
    "stock_status": "outofstock",
    "images": [],
    "categories": [],
    "variations": [],
}

# Synthetic (hand-built, not sampled — the live store has no variable products
# today) fixture to exercise the variation-mapping code path.
WC_VARIABLE_PARENT = {
    "id": 555,
    "sku": "syn-parent",
    "type": "variable",
    "status": "publish",
    "name": "Synthetic Variable Tee",
    "permalink": "https://skyyrose.co/product/syn-parent/",
    "description": "<p>A synthetic variable product for tests.</p>",
    "short_description": "",
    "price": "50",
    "regular_price": "50",
    "stock_status": "instock",
    "images": [{"src": "https://skyyrose.co/wp-content/uploads/parent.webp"}],
    "categories": [{"name": "Signature"}],
    "variations": [601, 602],
    "_variations_data": [
        {
            "id": 601,
            "sku": "syn-parent-blue-s",
            "price": "50",
            "regular_price": "50",
            "stock_status": "instock",
            "attributes": [{"name": "Color", "option": "Blue"}, {"name": "Size", "option": "S"}],
            "image": {"src": "https://skyyrose.co/wp-content/uploads/variant-blue.webp"},
        },
        {
            "id": 602,
            "sku": "syn-parent-red-m",
            "price": "55",
            "regular_price": "55",
            "stock_status": "outofstock",
            "attributes": [{"name": "Color", "option": "Red"}, {"name": "Size", "option": "M"}],
            "image": None,
        },
    ],
}

CATALOG_ROW_NON_PREORDER = {"sku": "sg-014", "is_preorder": "0"}
CATALOG_ROW_PREORDER = {"sku": "br-003", "is_preorder": "1"}


# --- clean_text ---


def test_clean_text_unescapes_entities_and_strips_tags():
    assert clean_text("Mint &amp; Lavender Sweatpants") == "Mint & Lavender Sweatpants"
    assert (
        clean_text("<p>Pastel luxury meets streetwear comfort.</p>\n")
        == "Pastel luxury meets streetwear comfort."
    )


def test_clean_text_handles_none_and_empty():
    assert clean_text(None) == ""
    assert clean_text("") == ""


# --- resolve_availability ---


def test_resolve_availability_maps_in_stock():
    availability, availability_date = resolve_availability(
        WC_SIMPLE_IN_STOCK, CATALOG_ROW_NON_PREORDER
    )
    assert availability == "in_stock"
    assert availability_date == ""


def test_resolve_availability_maps_out_of_stock():
    availability, _ = resolve_availability(WC_NO_IMAGES_OUT_OF_STOCK, None)
    assert availability == "out_of_stock"


def test_resolve_availability_catalog_preorder_overrides_wc_stock_status():
    # WC reports "instock" for this SKU, but the catalog CSV's is_preorder=1
    # is canonical (see mapping.py docstring) and must win.
    availability, availability_date = resolve_availability(WC_SIMPLE_PREORDER, CATALOG_ROW_PREORDER)
    assert availability == "pre_order"
    assert availability_date == ""  # no release-date source exists anywhere in our stack


def test_resolve_availability_defaults_to_unknown_for_unrecognized_status():
    product = {"stock_status": "some_future_wc_status"}
    availability, _ = resolve_availability(product, None)
    assert availability == "unknown"


# --- map_simple_product ---


def test_map_simple_product_happy_path():
    item = map_simple_product(WC_SIMPLE_IN_STOCK, CATALOG_ROW_NON_PREORDER, DEFAULT_CONSTANTS)
    assert item["item_id"] == "sg-014"
    assert item["title"] == "Mint & Lavender Sweatpants"
    assert (
        item["description"]
        == "Pastel luxury meets streetwear comfort. Mint and lavender sweatpants with signature rose detail."
    )
    assert item["url"] == "https://skyyrose.co/product/sg-014/"
    assert item["brand"] == "SkyyRose"
    assert item["image_url"].startswith("https://i0.wp.com/")
    assert item["additional_image_urls"] != ""
    assert item["price"] == "45 USD"
    assert item["availability"] == "in_stock"
    assert item["is_eligible_search"] == "true"
    assert item["is_eligible_checkout"] == "false"
    assert item["seller_name"] == "SkyyRose"
    assert item["return_policy"] == "https://skyyrose.co/shipping-returns/"
    assert item["target_countries"] == "US"
    assert item["store_country"] == "US"
    # "Uncategorized" is filtered out — it's WC's default, not a real category.
    assert item["product_category"] == ""


def test_map_simple_product_preorder_has_no_availability_date():
    item = map_simple_product(WC_SIMPLE_PREORDER, CATALOG_ROW_PREORDER, DEFAULT_CONSTANTS)
    assert item["availability"] == "pre_order"
    assert item["availability_date"] == ""


def test_map_simple_product_no_images_yields_empty_image_url():
    item = map_simple_product(WC_NO_IMAGES_OUT_OF_STOCK, None, DEFAULT_CONSTANTS)
    assert item["image_url"] == ""
    assert item["availability"] == "out_of_stock"


def test_map_simple_product_populates_category_when_present():
    item = map_simple_product(WC_SIMPLE_PREORDER, CATALOG_ROW_PREORDER, DEFAULT_CONSTANTS)
    assert item["product_category"] == "Black Rose"


# --- map_product_to_feed_items (dispatch + variants) ---


def test_map_product_to_feed_items_simple_product_yields_one_item():
    items = map_product_to_feed_items(
        WC_SIMPLE_IN_STOCK, CATALOG_ROW_NON_PREORDER, DEFAULT_CONSTANTS
    )
    assert len(items) == 1
    assert items[0]["item_id"] == "sg-014"


def test_map_product_to_feed_items_variable_product_yields_one_item_per_variation():
    items = map_product_to_feed_items(WC_VARIABLE_PARENT, None, DEFAULT_CONSTANTS)
    assert len(items) == 2
    ids = {item["item_id"] for item in items}
    assert ids == {"syn-parent-blue-s", "syn-parent-red-m"}

    blue = next(i for i in items if i["item_id"] == "syn-parent-blue-s")
    assert blue["group_id"] == "syn-parent"
    assert blue["color"] == "Blue"
    assert blue["size"] == "S"
    assert blue["availability"] == "in_stock"
    assert blue["price"] == "50 USD"
    assert blue["image_url"] == "https://skyyrose.co/wp-content/uploads/variant-blue.webp"

    red = next(i for i in items if i["item_id"] == "syn-parent-red-m")
    assert red["availability"] == "out_of_stock"
    assert red["price"] == "55 USD"
    # No per-variation image -> falls back to parent image.
    assert red["image_url"] == "https://skyyrose.co/wp-content/uploads/parent.webp"


# --- validate_feed_item ---


def test_validate_feed_item_valid_item_has_no_errors():
    item = map_simple_product(WC_SIMPLE_IN_STOCK, CATALOG_ROW_NON_PREORDER, DEFAULT_CONSTANTS)
    assert validate_feed_item(item) == []


def test_validate_feed_item_flags_missing_required_field():
    item = map_simple_product(WC_SIMPLE_IN_STOCK, CATALOG_ROW_NON_PREORDER, DEFAULT_CONSTANTS)
    item["title"] = ""
    errors = validate_feed_item(item)
    assert any("title" in e for e in errors)


def test_validate_feed_item_flags_preorder_missing_availability_date():
    item = map_simple_product(WC_SIMPLE_PREORDER, CATALOG_ROW_PREORDER, DEFAULT_CONSTANTS)
    errors = validate_feed_item(item)
    assert any("availability_date" in e for e in errors)


def test_validate_feed_item_flags_malformed_price():
    item = map_simple_product(WC_SIMPLE_IN_STOCK, CATALOG_ROW_NON_PREORDER, DEFAULT_CONSTANTS)
    item["price"] = "not-a-number USD"
    errors = validate_feed_item(item)
    assert any("not numeric" in e for e in errors)


def test_validate_feed_item_flags_price_without_currency():
    item = map_simple_product(WC_SIMPLE_IN_STOCK, CATALOG_ROW_NON_PREORDER, DEFAULT_CONSTANTS)
    item["price"] = "45"
    errors = validate_feed_item(item)
    assert any("currency" in e for e in errors)


def test_validate_feed_item_optional_field_absence_never_fails_item():
    # GTIN/MPN/reviews/etc. are optional and have no source in our stack —
    # their absence must never exclude an otherwise-valid item.
    item = map_simple_product(WC_SIMPLE_IN_STOCK, CATALOG_ROW_NON_PREORDER, DEFAULT_CONSTANTS)
    assert "gtin" not in item or not item.get("gtin")
    assert validate_feed_item(item) == []


def test_validate_feed_item_checkout_enabled_requires_privacy_and_tos():
    constants = FeedConstants(is_eligible_checkout=True, seller_privacy_policy="", seller_tos="")
    item = map_simple_product(WC_SIMPLE_IN_STOCK, CATALOG_ROW_NON_PREORDER, constants)
    errors = validate_feed_item(item)
    assert any("seller_privacy_policy" in e for e in errors)
    assert any("seller_tos" in e for e in errors)


# --- partition_items ---


def test_partition_items_splits_valid_and_excluded():
    items = [
        map_simple_product(WC_SIMPLE_IN_STOCK, CATALOG_ROW_NON_PREORDER, DEFAULT_CONSTANTS),
        map_simple_product(WC_SIMPLE_PREORDER, CATALOG_ROW_PREORDER, DEFAULT_CONSTANTS),
    ]
    valid, excluded = partition_items(items)
    assert len(valid) == 1
    assert valid[0]["item_id"] == "sg-014"
    assert len(excluded) == 1
    assert excluded[0]["item_id"] == "br-003"
    assert excluded[0]["errors"]


# --- writer ---


def test_write_csv_feed_and_read_back(tmp_path: Path):
    item = map_simple_product(WC_SIMPLE_IN_STOCK, CATALOG_ROW_NON_PREORDER, DEFAULT_CONSTANTS)
    feed_path = tmp_path / "feed.csv.gz"
    write_csv_feed([item], feed_path)

    import csv
    import gzip

    with gzip.open(feed_path, "rt", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 1
    assert rows[0]["item_id"] == "sg-014"
    assert rows[0]["price"] == "45 USD"


def test_write_exclusions_report(tmp_path: Path):
    excluded = [
        {
            "item_id": "br-003",
            "title": "BLACK is Beautiful Jersey Series: 0",
            "errors": ["some error"],
        }
    ]
    exclusions_path = tmp_path / "exclusions.json"
    write_exclusions(excluded, exclusions_path)

    import json

    with exclusions_path.open() as fh:
        loaded = json.load(fh)
    assert loaded == excluded


# --- catalog loader (filesystem only, no network) ---


def test_load_catalog_from_real_sot_csv():
    if not DEFAULT_CATALOG_PATH.exists():
        pytest.skip(f"Canonical catalog CSV not present at {DEFAULT_CATALOG_PATH} in this checkout")
    catalog = load_catalog()
    assert "br-003" in catalog
    assert catalog["br-003"]["is_preorder"] == "1"
    assert "sg-014" in catalog
    assert catalog["sg-014"]["is_preorder"] == "0"
