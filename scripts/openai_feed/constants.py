"""Merchant-level constants for the OpenAI product feed.

These are not per-product data — WooCommerce has no native `brand` field and
no per-product seller/returns/geo record, so the spec-required fields in this
module are injected once for the whole feed rather than sourced from WC.

Values sourced from live skyyrose.co pages verified HTTP 200 on 2026-07-08:
  https://skyyrose.co/privacy-policy/
  https://skyyrose.co/terms-of-service/
  https://skyyrose.co/shipping-returns/
and from the WooCommerce store currency setting (GET /wc/v3/data/currencies/current -> USD).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeedConstants:
    """Store-wide values injected into every feed item.

    `is_eligible_checkout` defaults to False: ChatGPT checkout (ACP) onboarding
    is gated to OpenAI-approved partners per
    https://developers.openai.com/commerce/guides/get-started, and enabling it
    pulls `seller_privacy_policy` / `seller_tos` into the required-field set.
    Flip only after a founder decision to pursue checkout approval.
    """

    brand: str = "SkyyRose"
    seller_name: str = "SkyyRose"
    seller_url: str = "https://skyyrose.co"
    seller_privacy_policy: str = "https://skyyrose.co/privacy-policy/"
    seller_tos: str = "https://skyyrose.co/terms-of-service/"
    return_policy: str = "https://skyyrose.co/shipping-returns/"
    target_countries: str = "US"
    store_country: str = "US"
    currency: str = "USD"
    is_eligible_search: bool = True
    is_eligible_checkout: bool = False
    is_eligible_ads: bool = False


DEFAULT_CONSTANTS = FeedConstants()

# Required fields per docs/integrations/openai-product-feed-spec.md, "Required-field
# summary" section, for a search-only feed (is_eligible_checkout=False).
REQUIRED_FIELDS: tuple[str, ...] = (
    "is_eligible_search",
    "is_eligible_checkout",
    "item_id",
    "title",
    "description",
    "url",
    "brand",
    "image_url",
    "price",
    "availability",
    "seller_name",
    "seller_url",
    "return_policy",
    "target_countries",
    "store_country",
)

# Additional fields required only when checkout is enabled.
CHECKOUT_REQUIRED_FIELDS: tuple[str, ...] = (
    "seller_privacy_policy",
    "seller_tos",
)

VALID_AVAILABILITY = frozenset({"in_stock", "out_of_stock", "pre_order", "backorder", "unknown"})

# Feed CSV column order — required fields first, then populated optional fields.
CSV_COLUMNS: tuple[str, ...] = (
    "item_id",
    "title",
    "description",
    "url",
    "brand",
    "condition",
    "image_url",
    "price",
    "availability",
    "availability_date",
    "is_eligible_search",
    "is_eligible_checkout",
    "is_eligible_ads",
    "seller_name",
    "seller_url",
    "seller_privacy_policy",
    "seller_tos",
    "return_policy",
    "target_countries",
    "store_country",
    "group_id",
    "color",
    "size",
    "product_category",
)
