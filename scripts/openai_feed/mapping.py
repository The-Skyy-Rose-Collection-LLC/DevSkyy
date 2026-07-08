"""Pure mapping functions: WooCommerce product JSON -> OpenAI feed item dict.

No network calls here — everything takes plain dicts (as returned by the WC
REST API, or a fixture sampled from one) so this module is unit-testable
without a live store.
"""

from __future__ import annotations

import html
import re
from typing import Any

from scripts.openai_feed.constants import FeedConstants

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

# WooCommerce stock_status -> OpenAI feed availability enum.
_STOCK_STATUS_MAP = {
    "instock": "in_stock",
    "outofstock": "out_of_stock",
    "onbackorder": "backorder",
}

DESCRIPTION_MAX_CHARS = 5000
TITLE_MAX_CHARS = 150


def clean_text(raw: str | None) -> str:
    """Strip HTML tags, unescape entities, collapse whitespace."""
    if not raw:
        return ""
    stripped = _TAG_RE.sub(" ", raw)
    unescaped = html.unescape(stripped)
    return _WS_RE.sub(" ", unescaped).strip()


def _primary_image_url(product: dict[str, Any]) -> str:
    images = product.get("images") or []
    if not images:
        return ""
    return images[0].get("src", "") or ""


def _additional_image_urls(product: dict[str, Any]) -> str:
    images = product.get("images") or []
    if len(images) <= 1:
        return ""
    return ",".join(img.get("src", "") for img in images[1:] if img.get("src"))


def _product_category(product: dict[str, Any]) -> str:
    cats = [c.get("name", "") for c in (product.get("categories") or [])]
    cats = [c for c in cats if c and c.lower() != "uncategorized"]
    return " > ".join(cats)


def resolve_availability(
    product: dict[str, Any], catalog_row: dict[str, Any] | None
) -> tuple[str, str]:
    """Return (availability, availability_date).

    The catalog CSV's `is_preorder` column is the canonical source of truth
    for pre-order state (see SOT.md) — WooCommerce's own `stock_status`
    reports "instock" for pre-order items too, so it cannot be trusted alone
    for this determination.

    `availability_date` is always returned empty: neither WooCommerce nor the
    catalog currently carries a release/ship date for pre-order SKUs. Any
    item resolved to `pre_order` will therefore fail required-field
    validation (spec: availability_date is required when availability=
    pre_order) and be excluded — this is intentional, it surfaces a real data
    gap rather than papering over it.
    """
    is_preorder = bool(catalog_row) and str(catalog_row.get("is_preorder", "0")).strip() == "1"
    if is_preorder:
        return "pre_order", ""
    stock_status = str(product.get("stock_status", "")).strip().lower()
    return _STOCK_STATUS_MAP.get(stock_status, "unknown"), ""


def map_simple_product(
    product: dict[str, Any],
    catalog_row: dict[str, Any] | None,
    constants: FeedConstants,
) -> dict[str, Any]:
    """Map a WC "simple" product (no variations) to one feed item."""
    availability, availability_date = resolve_availability(product, catalog_row)
    price = product.get("price") or product.get("regular_price") or ""
    price_str = f"{price} {constants.currency}" if price else ""

    item: dict[str, Any] = {
        "item_id": product.get("sku") or f"wc-{product.get('id')}",
        "title": clean_text(product.get("name"))[:TITLE_MAX_CHARS],
        "description": clean_text(product.get("description") or product.get("short_description"))[
            :DESCRIPTION_MAX_CHARS
        ],
        "url": product.get("permalink", ""),
        "brand": constants.brand,
        "condition": "new",
        "image_url": _primary_image_url(product),
        "additional_image_urls": _additional_image_urls(product),
        "price": price_str,
        "availability": availability,
        "availability_date": availability_date,
        "is_eligible_search": str(constants.is_eligible_search).lower(),
        "is_eligible_checkout": str(constants.is_eligible_checkout).lower(),
        "is_eligible_ads": str(constants.is_eligible_ads).lower(),
        "seller_name": constants.seller_name,
        "seller_url": constants.seller_url,
        "seller_privacy_policy": constants.seller_privacy_policy,
        "seller_tos": constants.seller_tos,
        "return_policy": constants.return_policy,
        "target_countries": constants.target_countries,
        "store_country": constants.store_country,
        "group_id": "",
        "color": "",
        "size": "",
        "product_category": _product_category(product),
    }
    return item


def map_variation(
    parent: dict[str, Any],
    variation: dict[str, Any],
    catalog_row: dict[str, Any] | None,
    constants: FeedConstants,
) -> dict[str, Any]:
    """Map one WC product variation to a feed item.

    Variations don't carry their own images/categories/status reliably, so
    those fall back to the parent product. `group_id` links every variation
    back to the parent SKU per the spec's Variants schema object.
    """
    availability, availability_date = resolve_availability(variation, catalog_row)
    if availability == "unknown" and str(variation.get("stock_status", "")).strip().lower() == "":
        # Variation didn't report its own stock_status — inherit the parent's.
        availability, availability_date = resolve_availability(parent, catalog_row)

    price = variation.get("price") or variation.get("regular_price") or parent.get("price") or ""
    price_str = f"{price} {constants.currency}" if price else ""

    attrs = {
        a.get("name", "").lower(): a.get("option", "") for a in (variation.get("attributes") or [])
    }
    color = attrs.get("color", "")
    size = attrs.get("size", "")

    var_images = variation.get("image")
    image_url = (var_images or {}).get("src", "") if isinstance(var_images, dict) else ""
    if not image_url:
        image_url = _primary_image_url(parent)

    parent_title = clean_text(parent.get("name"))
    variant_bits = " ".join(filter(None, [color, size]))
    title = f"{parent_title} — {variant_bits}" if variant_bits else parent_title

    item: dict[str, Any] = {
        "item_id": variation.get("sku") or f"wc-{variation.get('id')}",
        "title": title[:TITLE_MAX_CHARS],
        "description": clean_text(
            variation.get("description")
            or parent.get("description")
            or parent.get("short_description")
        )[:DESCRIPTION_MAX_CHARS],
        "url": parent.get("permalink", ""),
        "brand": constants.brand,
        "condition": "new",
        "image_url": image_url,
        "additional_image_urls": _additional_image_urls(parent),
        "price": price_str,
        "availability": availability,
        "availability_date": availability_date,
        "is_eligible_search": str(constants.is_eligible_search).lower(),
        "is_eligible_checkout": str(constants.is_eligible_checkout).lower(),
        "is_eligible_ads": str(constants.is_eligible_ads).lower(),
        "seller_name": constants.seller_name,
        "seller_url": constants.seller_url,
        "seller_privacy_policy": constants.seller_privacy_policy,
        "seller_tos": constants.seller_tos,
        "return_policy": constants.return_policy,
        "target_countries": constants.target_countries,
        "store_country": constants.store_country,
        "group_id": parent.get("sku") or f"wc-{parent.get('id')}",
        "color": color,
        "size": size,
        "product_category": _product_category(parent),
    }
    return item


def map_product_to_feed_items(
    product: dict[str, Any],
    catalog_row: dict[str, Any] | None,
    constants: FeedConstants,
) -> list[dict[str, Any]]:
    """Map one WC product to one-or-more feed items.

    Variable products emit one item per variation (each variation is its own
    feed item per the spec); simple products emit exactly one item.
    """
    variations = product.get("_variations_data") or []
    if product.get("type") == "variable" and variations:
        return [map_variation(product, v, catalog_row, constants) for v in variations]
    return [map_simple_product(product, catalog_row, constants)]
