"""Pure validation functions for a mapped feed item.

Checks REQUIRED fields only (per the spec's Stable schema — see
docs/integrations/openai-product-feed-spec.md). Missing/invalid OPTIONAL
fields never fail an item; that would exclude every product for lacking a
GTIN, which the spec does not require.
"""

from __future__ import annotations

from typing import Any

from scripts.openai_feed.constants import (
    CHECKOUT_REQUIRED_FIELDS,
    REQUIRED_FIELDS,
    VALID_AVAILABILITY,
)

_TRUE = "true"


def validate_feed_item(item: dict[str, Any]) -> list[str]:
    """Return a list of validation error strings; empty list == valid."""
    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        value = item.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"missing required field: {field}")

    item_id = item.get("item_id", "")
    if item_id and len(item_id) > 100:
        errors.append(f"item_id exceeds 100 chars ({len(item_id)})")

    title = item.get("title", "")
    if title and len(title) > 150:
        errors.append(f"title exceeds 150 chars ({len(title)})")

    description = item.get("description", "")
    if description and len(description) > 5000:
        errors.append(f"description exceeds 5000 chars ({len(description)})")

    url = item.get("url", "")
    if url and not url.startswith("https://") and not url.startswith("http://"):
        errors.append(f"url is not a valid HTTP(S) URL: {url!r}")

    image_url = item.get("image_url", "")
    if image_url and not image_url.startswith("https://") and not image_url.startswith("http://"):
        errors.append(f"image_url is not a valid HTTP(S) URL: {image_url!r}")

    availability = item.get("availability", "")
    if availability and availability not in VALID_AVAILABILITY:
        errors.append(f"availability {availability!r} not in {sorted(VALID_AVAILABILITY)}")

    if availability == "pre_order" and not str(item.get("availability_date", "")).strip():
        errors.append(
            "availability=pre_order requires availability_date (spec: conditional-required); none available"
        )

    price = item.get("price", "")
    if price:
        parts = price.split(" ", 1)
        if len(parts) != 2:
            errors.append(f"price missing currency code: {price!r}")
        else:
            amount, currency = parts
            try:
                if float(amount) <= 0:
                    errors.append(f"price must be positive: {price!r}")
            except ValueError:
                errors.append(f"price is not numeric: {price!r}")
            if len(currency) != 3 or not currency.isalpha():
                errors.append(f"price currency is not a 3-letter ISO 4217 code: {currency!r}")

    if item.get("is_eligible_checkout") == _TRUE:
        for field in CHECKOUT_REQUIRED_FIELDS:
            value = item.get(field)
            if not value:
                errors.append(f"is_eligible_checkout=true requires {field}, which is missing")

    return errors


def partition_items(
    items: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split mapped feed items into (valid, excluded-with-reasons)."""
    valid: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for item in items:
        errors = validate_feed_item(item)
        if errors:
            excluded.append(
                {
                    "item_id": item.get("item_id", ""),
                    "title": item.get("title", ""),
                    "errors": errors,
                }
            )
        else:
            valid.append(item)
    return valid, excluded
