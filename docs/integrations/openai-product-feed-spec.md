# OpenAI ChatGPT Product Feed — Specification Reference

**Source:** https://developers.openai.com/commerce/specs/file-upload/products (redirects from
`/commerce/specs/feed/`) — "Stable" schema view.
Related pages consulted: `/commerce/specs/file-upload/overview` (delivery/format requirements),
`/commerce/guides/get-started` (integration path, prohibited-products policy).
**Fetched:** 2026-07-08 (via `curl` against the live page + cross-checked with an AI-summarized
`WebFetch` pass; both agreed field-for-field).

> This file is our working reference for `docs/integrations/openai-feed-compliance-report.md` and
> `scripts/openai_product_feed.py`. If the upstream spec changes, re-fetch and diff before trusting
> this doc.

## Integration model

- Feed data can be delivered via **file upload** (this spec) or **API**. File upload is recommended
  for the full daily catalog snapshot; the API is for intraday upserts. Promotions data is API-only.
- Feed-file onboarding is **currently gated to approved partners** (apply via the linked form on the
  get-started page) — we are not delivering to OpenAI yet, this doc/generator produces the artifact.
- **Delivery model:** push via SFTP, one stable filename, overwritten on every publish (never a new
  filename per run). Full snapshot at least daily; keep shard sets stable if sharding.
- **Formats:** parquet (ideally zstd-compressed) is *preferred*; `jsonl.gz`, `csv.gz`, `tsv.gz` are
  also explicitly supported.
- **Encoding:** UTF-8.
- **Shard sizing:** recommended ≤500k items/shard, target <500MB per shard file (irrelevant at our
  scale — 33 SKUs).
- **Common ingestion failures called out by OpenAI:** missing required fields, outdated/non-spec
  field names, malformed field values.
- **Removal:** set `is_eligible_search=false` or drop the record from the next full snapshot.
- **Prohibited products policy:** no adult content, age-restricted goods, weapons, prescription
  meds, etc. — not applicable to SkyyRose apparel.

## Field reference (Stable schema)

Grouped by schema object exactly as published. "Requirement" values are copied verbatim from the
spec page (`Required`, `Optional`, `Recommended`, or conditional wording).

### 1. OpenAI Flags

| Field | Type | Requirement | Values / Constraints |
|---|---|---|---|
| `is_eligible_search` | Boolean | **Required** | `true`/`false`, lower-case string |
| `is_eligible_checkout` | Boolean | **Required** | `true`/`false`; requires `is_eligible_search=true` |
| `is_eligible_ads` | Boolean | Optional | `true`/`false` |

### 2. Basic Product Data

| Field | Type | Requirement | Constraints |
|---|---|---|---|
| `item_id` | String (alphanumeric) | **Required** | Max 100 chars; unique per variant; must remain stable over time |
| `gtin` | String (numeric) | Optional | 8–14 digits, no dashes/spaces |
| `mpn` | String | Optional | Max 70 chars |
| `title` | String (UTF-8) | **Required** | Max 150 chars; avoid all-caps |
| `description` | String (UTF-8) | **Required** | Max 5,000 chars; plain text only |
| `url` | URL (RFC 1738) | **Required** | Must resolve HTTP 200; HTTPS preferred |

### 3. Item Information

| Field | Type | Requirement | Constraints |
|---|---|---|---|
| `brand` | String | **Required** | Max 70 chars |
| `condition` | String | Optional | e.g. `new` (lower-case) |
| `product_category` | String | Optional | `>`-separated taxonomy path |
| `material` | String | Optional | Max 100 chars |
| `dimensions` | String | Optional | `LxWxH unit`; unit required if provided |
| `length` / `width` / `height` | String | Optional | Provide all three together; needs `dimensions_unit` |
| `dimensions_unit` | String | Optional | Required if length/width/height provided |
| `weight` | String | Optional | Needs `item_weight_unit` |
| `item_weight_unit` | String | Optional | Required if `weight` provided |
| `age_group` | Enum | Optional | `newborn`, `infant`, `toddler`, `kids`, `adult` |
| `ads_metadata` | Object | Optional | JSON object, string keys/values |

### 4. Media

| Field | Type | Requirement | Constraints |
|---|---|---|---|
| `image_url` | URL | **Required** | JPEG/PNG; HTTPS preferred |
| `additional_image_urls` | String | Optional | Comma-separated list |
| `video_url` | URL | Optional | Publicly accessible |
| `model_3d_url` | URL | Optional | GLB/GLTF preferred |

### 5. Price & Promotions

| Field | Type | Requirement | Constraints |
|---|---|---|---|
| `price` | Number + currency | **Required** | Must include ISO 4217 currency code |
| `sale_price` | Number + currency | Optional | Must be ≤ `price` |
| `sale_price_start_date` | Date (ISO 8601) | Optional | — |
| `sale_price_end_date` | Date (ISO 8601) | Optional | — |
| `unit_pricing_measure` / `base_measure` | Number + unit | Optional | Both required together |
| `pricing_trend` | String | Optional | Max 80 chars |

### 6. Availability & Inventory

| Field | Type | Requirement | Constraints |
|---|---|---|---|
| `availability` | Enum | **Required** | `in_stock`, `out_of_stock`, `pre_order`, `backorder`, `unknown`; lower-case |
| `availability_date` | Date (ISO 8601) | **Required if `availability=pre_order`** | Must be a future date |
| `expiration_date` | Date (ISO 8601) | Optional | Future date; product removed after |
| `pickup_method` | Enum | Optional | `in_store`, `reserve`, `not_supported` |
| `pickup_sla` | Number + duration | Optional | Requires `pickup_method` |

> No `inventory_quantity` / stock-count field exists anywhere in this spec. Availability is a
> status enum only — WC's `manage_stock=false` (quantity not tracked) does not block compliance.

### 7. Variants

| Field | Type | Requirement | Constraints |
|---|---|---|---|
| `group_id` | String | Recommended if listing has variants | Stable across related variants |
| `listing_has_variations` | Boolean | Recommended | Lower-case |
| `variant_dict` | Object | Recommended if listing has variants | JSON map of option→value |
| `item_group_title` | String | Optional | Max 150 chars |
| `color` | String | Optional | Max 40 chars |
| `size` | String | Recommended (apparel) | Max 20 chars |
| `size_system` | Country code (ISO 3166) | Recommended (apparel) | 2-letter code |
| `gender` | String | Optional | Lower-case |
| `offer_id` | String | Optional | Unique within feed |
| `custom_variant1-3_category` / `_option` | String | **Deprecated** | Use `variant_dict` instead |

### 8. Fulfillment

| Field | Type | Requirement | Constraints |
|---|---|---|---|
| `shipping` | String | Optional | `country:region:service_class:price:min_handling_days:max_handling_days:min_transit_days:max_transit_days`; fields may be omitted, colons kept |
| `is_digital` | Boolean | Optional | Lower-case |

### 9. Merchant Info

| Field | Type | Requirement | Constraints |
|---|---|---|---|
| `seller_name` | String | **Required / Display** | Max 70 chars |
| `marketplace_seller` | String | Optional | Max 70 chars — for 3P/marketplace fulfillment |
| `seller_url` | URL | **Required** | HTTPS preferred |
| `seller_privacy_policy` | URL | **Required if `is_eligible_checkout=true`** | HTTPS preferred |
| `seller_tos` | URL | **Required if `is_eligible_checkout=true`** | HTTPS preferred |

### 10. Returns

| Field | Type | Requirement | Constraints |
|---|---|---|---|
| `accepts_returns` | Boolean | Optional | Lower-case |
| `return_deadline_in_days` | Integer | Optional | Positive integer; canonical return-window field |
| `accepts_exchanges` | Boolean | Optional | Lower-case |
| `return_policy` | URL | **Required** | HTTPS preferred |

### 11. Performance Signals

| Field | Type | Requirement | Constraints |
|---|---|---|---|
| `popularity_score` | Number | Optional | 0–5 or merchant-defined |
| `return_rate` | Number (%) | Optional | 0–100 |

### 12. Compliance

| Field | Type | Requirement | Constraints |
|---|---|---|---|
| `warning` / `warning_url` | String / URL | Recommended for checkout | URL must resolve HTTP 200 |
| `age_restriction` | Number | Recommended | Positive integer |

### 13. Reviews & Q&A

| Field | Type | Requirement | Constraints |
|---|---|---|---|
| `review_count` | Integer | Optional | Non-negative |
| `star_rating` | String | Optional | 0–5 scale |
| `store_review_count` | Integer | Optional | Non-negative |
| `store_star_rating` | String | Optional | 0–5 scale |
| `q_and_a` | List[Object] | Recommended | Objects with `q`, `a` string fields |
| `reviews` | List[Object] | Recommended | Objects with `title`, `content`, `minRating`, `maxRating`, `rating` |

### 14. Related Products

| Field | Type | Requirement | Constraints |
|---|---|---|---|
| `related_product_id` | String | Recommended | Comma-separated IDs allowed |
| `relationship_type` | Enum | Recommended | `part_of_set`, `required_part`, `often_bought_with`, `substitute`, `different_brand`, `accessory` |

### 15. Geo Tagging

| Field | Type | Requirement | Constraints |
|---|---|---|---|
| `target_countries` | List | **Required** | ISO 3166-1 alpha-2 codes; first entry used |
| `store_country` | String | **Required** | ISO 3166-1 alpha-2 code |
| `geo_price` | Number + currency | Optional | ISO 4217 |
| `geo_availability` | String | Optional | Region + ISO 3166 status |

## Required-field summary (drives the compliance verdict)

For a **search-only** feed (`is_eligible_checkout=false`, the default we ship — see compliance
report §1 for rationale), the binding required set is:

`is_eligible_search`, `is_eligible_checkout`, `item_id`, `title`, `description`, `url`, `brand`,
`image_url`, `price` (+currency), `availability` (+`availability_date` when `pre_order`),
`seller_name`, `seller_url`, `return_policy`, `target_countries`, `store_country`.

If/when `is_eligible_checkout=true` is turned on, `seller_privacy_policy` and `seller_tos` join the
required set.

Everything in groups 3 (partial), 7 (variants), 11–14 is optional/recommended enrichment with no
data source in our stack today — see the compliance report for the gap list.
