# OpenAI ChatGPT Product Feed — Compliance Report

**Audited:** 2026-07-08 · **Store:** https://skyyrose.co (WooCommerce REST v3)
**Snapshot:** `data/audits/openai-feed/wc-products-2026-07-08.json` (35 WC products, pretty-printed, reproducible via `python scripts/openai_product_feed.py --dry-run`)
**Spec reference:** `docs/integrations/openai-product-feed-spec.md`
**Generator:** `scripts/openai_product_feed.py` (+ `scripts/openai_feed/` package)

---

## 1. Executive summary

**CONDITIONAL YES — 18 of 33 catalog SKUs pass every required field today, but one cross-cutting
risk (image format) needs a decision before calling any of them unconditionally shippable.**

A live dry-run (`python scripts/openai_product_feed.py --dry-run`, read-only against
WooCommerce) maps all 33 published, catalog-registered SKUs to feed items and validates them
against the spec's required fields:

| | Count |
|---|---|
| Live WC products (all statuses) | 35 |
| Published + catalog-registered (feed candidates) | 33 |
| **Valid — feed-ready today** | **18** |
| **Excluded — fail a required field** | **15** |

**Blocker #1 is a real data gap, not a WC configuration problem, and is a business trade-off, not a
hard wall:** all 15 excluded items are the catalog's `is_preorder=1` SKUs. Per spec,
`availability=pre_order` requires a future `availability_date`, and **no system in our stack (WC
product, WC meta, or the catalog CSV) carries a release/ship date for any pre-order SKU.** Confirmed
by direct inspection of WC `meta_data` for all 15 (see §3) — zero date-like keys exist. **This
exclusion is a consequence of our choice to map `is_preorder=1 → pre_order`** (the semantically
honest mapping); mapping those SKUs to `backorder` instead (no `availability_date` dependency, and
they are in fact orderable now) would ship all 33/33 immediately. Whether to hold out for accurate
`pre_order` semantics (needs a release-date source) or ship 33/33 today under `backorder` is a
founder call — see §5.

**Blocker #2 (found during this audit, not yet resolved) — `image_url` format is Accept-header
dependent, and we don't control the requester:** every image asset is stored at origin as native
WebP (confirmed: `curl -I` on the raw upload URL returns `content-type: image/webp`). We emit the
Jetpack Photon proxy URL (`i0.wp.com/...`), which content-negotiates the response format:

```
curl -I "<image_url>"                                        -> content-type: image/jpeg  (default/generic Accept)
curl -I -H "Accept: image/webp,..." "<image_url>"             -> content-type: image/webp  (Accept explicitly lists webp)
```

The spec's Media row for `image_url` reads: *"Required — JPEG/PNG; HTTPS preferred."* Read
literally, "HTTPS preferred" is soft (HTTP tolerated) but "JPEG/PNG" carries no such qualifier —
i.e. format is plausibly a hard constraint, and the spec's overall field-naming/enum/shipping-format
conventions track Google Merchant Center closely enough (which explicitly does **not** accept WebP
for `image_link`) that this reads as a real constraint, not decorative. **We could not find an
OpenAI-published statement of what Accept header their feed-ingestion crawler sends**, so whether
any given `image_url` actually violates the spec in practice is genuinely unresolved — this is not
a confirmed failure, but a verified, real risk that affects **all 33 mapped items** (both the 18
valid and the 15 excluded), not just a subset. The generator does not currently exclude items over
this (see §5 for why, and the fix options).

Everything else required by the spec (`item_id`, `title`, `description`, `url`, `price` +currency,
`availability` enum mapping, `brand`, `seller_name`/`seller_url`, `return_policy`,
`target_countries`/`store_country`) is either sourced cleanly from WooCommerce or supplied as a
verified merchant-level constant. No WC configuration change (manage_stock, brand taxonomy, etc.)
is required to ship the 18 in-stock/backorder SKUs.

**Top blockers, by count:**

1. **15/33 SKUs (all pre-order) missing `availability_date`** — real data gap **and** a business
   trade-off (see above): founder decision needed on whether to source release dates (unlocks true
   `pre_order` semantics) or accept `backorder` mapping (ships 33/33 today, one-line generator
   change).
2. **33/33 SKUs' `image_url` resolves to WebP or JPEG depending on the requester's Accept header**
   — verified via curl, mechanism understood, but whether this violates the spec in OpenAI's actual
   ingestion path is unresolved. Founder/eng decision: confirm with OpenAI, or build a
   guaranteed-JPEG asset path (see §5) — the origin store has no JPEG derivative today.
3. **0/33 SKUs have GTIN/MPN** — **not a blocker** (both optional). Enrichment opportunity only.
4. **Checkout (ACP) not evaluated** — `is_eligible_checkout` is shipped `false` by default. Turning
   it on requires `seller_privacy_policy` + `seller_tos` (both already resolvable, see §2) **and**
   OpenAI partner approval, which is gated per their get-started guide — founder decision, not a
   data problem.
5. **WC-native `brand` taxonomy is empty on all 35 products** — not a feed blocker (we inject
   `brand="SkyyRose"` as a constant), but worth fixing in WC directly for other integrations
   (Google Merchant Center, etc. commonly read WC's `brands` field).
6. **`product_category` populated for only 2/33 SKUs** (Kids Capsule) — 31/33 sit in WC's default
   "Uncategorized" bucket. Optional field, filtered out rather than emitting "Uncategorized" (see
   `mapping.py::_product_category`), but real WC category hygiene would improve search relevance.

**Verdict qualifier:** this is a **search-only** feed. Checkout eligibility is a separate founder
decision (see §5).

---

## 2. Field matrix

**R** = Required · **O** = Optional · **C** = Conditionally required (see Notes) · **OK** = every
candidate item has a valid value · **GAP** = no source exists anywhere in our stack · **PARTIAL** =
some items OK, some not, or partially populated · **CONST** = merchant-level constant, not
per-product (correctly not a "gap" — WC/CSV have no per-product record for this fact).

| Spec field | Req? | Our source | Status | Fix |
|---|---|---|---|---|
| `is_eligible_search` | R | Generator constant (`true`) | OK | — |
| `is_eligible_checkout` | R | Generator constant (`false`, default) | OK | Founder decision to flip (see §5) |
| `is_eligible_ads` | O | Generator constant (`false`) | OK | Founder decision if ads desired |
| `item_id` | R | WC `sku` | OK (33/33) | — |
| `gtin` | O | *(none)* | GAP | No UPC/GTIN data exists anywhere in our stack; would need manual entry per SKU |
| `mpn` | O | *(none)* | GAP | Same as GTIN |
| `title` | R | WC `name` (HTML-unescaped) | OK (33/33, all ≤150 chars, no all-caps) | — |
| `description` | R | WC `description` (HTML-stripped) | OK (33/33, all ≤5000 chars, none empty) | — |
| `url` | R | WC `permalink` | OK (33/33, HTTPS, resolves) | — |
| `brand` | R | Generator constant (`SkyyRose`) | CONST/OK | WC `brands` taxonomy is empty on all products — separate hygiene fix, not a feed blocker |
| `condition` | O | Generator constant (`new`) | OK | — |
| `product_category` | O | WC `categories` (joined, "Uncategorized" filtered) | PARTIAL (2/33 populated) | Assign real WC categories to the other 31 SKUs |
| `material`, `dimensions`, `weight`, `age_group` | O | *(none)* | GAP | No WC field or CSV column carries these; low priority enrichment |
| `image_url` | R | WC `images[0].src` | **AT-RISK (33/33)** — HTTPS resolves 200 on all, but format is Accept-header-dependent (verified: generic request → `image/jpeg`, webp-signaling request → `image/webp`); origin asset is native WebP with no JPEG derivative | Confirm with OpenAI what Accept header their crawler sends, or build a guaranteed-JPEG/PNG asset path for feed use — see §1 blocker #2, §5 |
| `additional_image_urls` | O | WC `images[1:]` | PARTIAL (populated when >1 image exists) | — |
| `video_url`, `model_3d_url` | O | *(none)* | GAP | No video/3D-model URLs published per-product today |
| `price` (+currency) | R | WC `price` + store currency (`USD`, verified via `/wc/v3/data/currencies/current`) | OK (33/33, all >0) | — |
| `sale_price` + dates | O | *(none populated — no products currently on sale)* | GAP (currently) | Would map from WC `sale_price`/`date_on_sale_from`/`_to` if/when a sale runs; generator doesn't populate this yet |
| `availability` | R | WC `stock_status`, **overridden by catalog `is_preorder`** | OK for enum values (33/33 map to a valid enum) | — |
| `availability_date` | C (if `pre_order`) | *(none)* | **GAP — real blocker, 15/33 SKUs** | Founder decision: add a release-date field (WC meta or CSV column) |
| `seller_name` | R | Generator constant (`SkyyRose`) | CONST/OK | — |
| `seller_url` | R | Generator constant (`https://skyyrose.co`) | CONST/OK | — |
| `seller_privacy_policy` | C (if checkout) | Generator constant (`https://skyyrose.co/privacy-policy/`, verified HTTP 200) | CONST/OK, unused while checkout=false | — |
| `seller_tos` | C (if checkout) | Generator constant (`https://skyyrose.co/terms-of-service/`, verified HTTP 200) | CONST/OK, unused while checkout=false | — |
| `return_policy` | R | Generator constant (`https://skyyrose.co/shipping-returns/`, verified HTTP 200) | CONST/OK | — |
| `accepts_returns`, `return_deadline_in_days`, `accepts_exchanges` | O | *(none populated — policy text exists on the page but not as a structured value)* | GAP | Founder/ops to confirm exact return window in days for structured field |
| `target_countries` | R | Generator constant (`US`) | CONST/OK | — |
| `store_country` | R | Generator constant (`US`) | CONST/OK | — |
| `geo_price`, `geo_availability` | O | *(none — single-region store)* | GAP (not applicable) | — |
| `group_id`, `variant_dict`, `color`, `size`, `size_system` | Recommended (apparel) | Would come from WC variations | GAP (structurally — see below) | No WC variable products exist today; sizes are handled as a descriptive CSV column (`sizes`), not WC attributes/variations. Generator supports the variation path (tested against a synthetic fixture) but has nothing live to map yet |
| `shipping` | O | *(none)* | GAP | Not populated; would need shipping-zone data from WC |
| `is_digital` | O | Implicit (`false` for all — physical apparel) | OK (not emitted, but universally false) | Could add as constant if OpenAI ingestion requires the explicit field |
| `popularity_score`, `return_rate`, `review_count`, `star_rating`, `q_and_a`, `reviews` | O | *(none)* | GAP | No review/rating system wired to WC for these SKUs currently |
| `related_product_id`, `relationship_type` | O | *(none)* | GAP | Could derive from WC `upsell_ids`/`cross_sell_ids` (present in the API response but empty on all sampled products) |
| `warning`/`warning_url`, `age_restriction` | O | *(not applicable — no restricted products)* | N/A | — |

---

## 3. Per-product issue list (required-field failures only)

All 15 failures are the same root cause — `availability=pre_order` with no `availability_date`
source. Verified by direct inspection of each product's WC `meta_data` array: zero keys matching
`date`, `release`, or `availab` exist on any of them.

Note: the image-format risk (§1 blocker #2) is **not** a required-field validation failure — the
generator's validator only checks that `image_url` is a well-formed HTTPS URL, which all 33 items
satisfy — so it does not appear in this table. It's listed separately because it's a real,
unresolved risk that applies uniformly across all 33 items regardless of pre-order status.

| SKU | Product name | Collection | Failure |
|---|---|---|---|
| br-003 | BLACK is Beautiful Jersey Series: 0. Baseball Classic (Black) | Black Rose | Missing `availability_date` |
| br-006 | BLACK Rose Sherpa Jacket | Black Rose | Missing `availability_date` |
| br-008 | BLACK is Beautiful Jersey Series: 1. SF Inspired (Football) | Black Rose | Missing `availability_date` |
| br-009 | BLACK is Beautiful Jersey Series: 2. Last Oakland (Football) | Black Rose | Missing `availability_date` |
| br-010 | BLACK is Beautiful Jersey Series: 3. The Bay (Basketball) | Black Rose | Missing `availability_date` |
| br-011 | BLACK is Beautiful Jersey Series: 4. The Rose (Hockey) | Black Rose | Missing `availability_date` |
| br-012 | BLACK is Beautiful Jersey Series: 5. Baseball Classic (Last Oakland) | Black Rose | Missing `availability_date` |
| br-014 | BLACK is Beautiful Jersey Series: 0. Baseball Classic (Giants) | Black Rose | Missing `availability_date` |
| br-015 | BLACK is Beautiful Jersey Series: 0. Baseball Classic (White) | Black Rose | Missing `availability_date` |
| lh-005 | The Fannie | Love Hurts | Missing `availability_date` |
| sg-001 | The Bridge Series 'The Bay Bridge' Shorts | Signature | Missing `availability_date` |
| sg-002 | The Bridge Series 'Stay Golden' Shirt | Signature | Missing `availability_date` |
| sg-003 | The Bridge Series 'Stay Golden' Shorts | Signature | Missing `availability_date` |
| sg-005 | The Bridge Series 'The Bay Bridge' Shirt | Signature | Missing `availability_date` |
| sg-015 | The Windbreaker Set | Signature | Missing `availability_date` |

The remaining 18 SKUs (all non-preorder: br-001, br-002, br-004, br-005, br-007, lh-002, lh-003,
lh-004, lh-006, sg-006, sg-007, sg-009, sg-011, sg-012, sg-013, sg-014, kids-001, kids-002) pass
every required field with zero errors.

---

## 4. Live-store vs. catalog-CSV drift (informational)

- **All 33 catalog CSV SKUs exist live in WooCommerce with `status=publish`.** No CSV SKU is
  missing from the store, and no catalog-registered SKU has an unexpected WC status. Clean.
- **2 WC products exist that are NOT in the catalog CSV** — both `status=draft` (never public,
  never purchasable, excluded from the feed by the generator's own filter):
  - `br-012-legacy` — "BLACK is Beautiful Jersey Series: 5. Last Oakland (Baseball)" — reads as an
    earlier draft of the now-canonical `br-012`.
  - `sg-004` — "The Signature Hoodie" — no equivalent SKU in the catalog CSV at all.
  - Per the Deletion Policy in `CLAUDE.md` (repoint-first / census-gated), these are flagged for
    founder review, not deleted by this audit — draft WC products carry no live risk but are dead
    weight in the admin product list.
- **WC `manage_stock=false` on all 35 products** — inventory quantity isn't tracked at the WC
  level. This is **not a spec compliance issue** (the OpenAI feed schema has no
  `inventory_quantity` field at all — confirmed by full field-table review), but it does mean WC's
  `stock_status` is manually maintained rather than quantity-derived; worth knowing if `in_stock`
  ever drifts from reality.
- **WC `brands` taxonomy is empty** on every product (see §2) — not a feed blocker (constant
  substitutes), but a real content gap for any other integration that reads WC-native brand data.
- **WC categories are "Uncategorized" for 31/33 products** — only the 2 Kids Capsule SKUs carry a
  real WC category. `sizes` in the catalog CSV is a free-text column, not modeled as WC product
  attributes/variations — so every live product is WC type `simple`, never `variable`. The
  generator's variation-mapping path (group_id/color/size) is implemented and unit-tested against
  a synthetic fixture but has nothing live to exercise it.

---

## 5. Prioritized remediation list

**Founder decisions (not data entry — policy/product calls):**

1. **Pre-order handling — pick one:**
   - (a) Source `availability_date` per SKU (new WC meta field vs. new catalog CSV column, e.g.
     `release_date`) → unlocks true `pre_order` semantics for all 15, 33/33 feed-ready.
   - (b) Map `is_preorder=1 → backorder` instead of `pre_order` (one-line change in
     `resolve_availability()`, `scripts/openai_feed/mapping.py`) → ships all 33/33 **today**, at the
     cost of losing pre-order-specific semantics/messaging in ChatGPT's product display.
   Recommendation: (a) if launch timing matters to the pre-order story; (b) if catalog coverage
   matters more than semantic precision. Either is defensible — this is a business call, not purely
   a data gap.
2. **Image format for OpenAI ingestion** — confirm whether the spec's "JPEG/PNG" is a hard
   constraint in practice (their get-started/best-practices guides don't state their crawler's
   Accept header). Two paths if confirmed strict:
   - Ask OpenAI directly (they gate feed onboarding to approved partners — this question fits
     naturally into that application/onboarding conversation).
   - Build a guaranteed-JPEG/PNG asset path for feed use: the origin store has no JPEG derivative of
     any product image today (all native WebP) — this would mean either a Photon URL parameter that
     reliably forces JPEG regardless of Accept header (not found in two attempts during this audit;
     needs Jetpack/WordPress.com support or docs), or generating and hosting JPEG copies
     specifically for the feed.
   Do NOT skip this — it affects all 33 mapped items, not just the pre-order-excluded ones.
3. **Checkout (ACP) eligibility** — decide whether to pursue OpenAI's approved-partner checkout
   program. If yes: apply via the link on their get-started guide, then flip
   `is_eligible_checkout=true` in `scripts/openai_feed/constants.py` (privacy/TOS URLs are already
   wired and verified). If no: leave as-is, ship search-only.
4. **Ads eligibility (`is_eligible_ads`)** — currently `false`; decide if SkyyRose wants ChatGPT ad
   surfacing.
5. **Structured return window** — confirm the exact `return_deadline_in_days` value (e.g. 30) to
   populate the optional field; policy text exists on `/shipping-returns/` but isn't captured as a
   number anywhere in code.

**Data entry (no founder call needed, straightforward hygiene):**

6. Assign real WC categories to the 31 SKUs currently in "Uncategorized" (improves the optional
   `product_category` field and general WC admin hygiene).
7. Populate WC's native `brands` taxonomy field with "SkyyRose" (benefits Google Merchant Center
   and other integrations that read it directly, not just this feed).
8. Resolve the 2 draft WC products not in the catalog CSV (`br-012-legacy`, `sg-004`) — confirm
   dead and clean up, or register them in the catalog if still relevant.

**What the feed generator already derives — no action needed:**

- All required per-product fields for non-preorder SKUs (item_id, title, description, url, brand,
  image_url, price, availability) — noting the image-format risk in item #2 above applies
  regardless of preorder status.
- All merchant-level constants (brand, seller_name, seller_url, return_policy, target_countries,
  store_country) — sourced from verified live URLs and WC store settings, not guesses.
- GTIN/MPN/reviews/Q&A/related-products/shipping-rate fields — genuinely absent from our stack;
  listed as enrichment opportunities in §2, not blockers, since all are spec-optional.

---

## 6. Real run output (2026-07-08)

```
$ python scripts/openai_product_feed.py --dry-run
Fetched 35 WooCommerce products.
Mapped 33 feed items from published, catalog-registered SKUs.
  Valid (feed-ready):  18
  Excluded (invalid):  15

Dry-run mode (default) — no files written. Pass --write to emit the feed.

$ python scripts/openai_product_feed.py --write
Fetched 35 WooCommerce products.
Mapped 33 feed items from published, catalog-registered SKUs.
  Valid (feed-ready):  18
  Excluded (invalid):  15

Wrote 18 items to feeds/openai-product-feed.csv.gz
Wrote exclusions report to feeds/openai-feed-exclusions.json
```

`feeds/openai-feed-exclusions.json` lists all 15 excluded SKUs with the exact validation error
(`availability=pre_order requires availability_date ...`) per item — see §3 for the full list.

## 7. Image-format evidence (reproducibility)

Commands used to verify the §1 blocker #2 finding, runnable against any emitted `image_url`:

```
$ curl -sI "https://i0.wp.com/skyyrose.co/wp-content/uploads/2026/06/mint-lavender-sweatpants-front-model.webp?fit=1024%2C1024&ssl=1" | grep -i content-type
content-type: image/jpeg

$ curl -sI -H "Accept: image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8" \
    "https://i0.wp.com/skyyrose.co/wp-content/uploads/2026/06/mint-lavender-sweatpants-front-model.webp?fit=1024%2C1024&ssl=1" | grep -i content-type
content-type: image/webp

$ curl -sI "https://skyyrose.co/wp-content/uploads/2026/06/mint-lavender-sweatpants-front-model.webp" | grep -i content-type
content-type: image/webp
```

Two Photon query-parameter guesses to force a fixed output format (`fmt=jpg`, `format=jpg`) did
**not** override Accept-header negotiation in a quick test — a real fix, if needed, requires either
confirmation from Jetpack/WordPress.com support of the correct override parameter, or a
feed-specific JPEG asset pipeline (see §5 item 2).
