# V2 Commerce Contract Repair Run

**Run:** 2026-08-06 · component-commerce lane  
**Owner:** `fashion-component-commerce-engineer`  
**Contract:** [`commerce-state-contract.json`](./commerce-state-contract.json)  
**Input audit:** [`team-run-commerce.md`](./team-run-commerce.md)  
**Disposition:** `BLOCKED` until the repair waves below produce candidate-bound evidence. This runbook is an implementation handoff, not a claim that the current theme is complete.

## Purpose

The audit found a polished but incomplete funnel: the canonical card and much of classic WooCommerce purchase wiring exist, while variation truth, media provenance, query state, Quick View, compare, Store API parity, checkout idempotency, post-purchase states and service extensions are not proven. This run converts those gaps into executable contracts.

The normalized contract is the only interface between page templates/components and commerce data. WooCommerce is purchase truth; catalog/SOT is identity and media provenance; client state is a projection. A missing, stale or unavailable source is `UNVERIFIED`, never a pass.

## Inputs and authority

- `brain/v2/commerce-state-contract.json` — enums, entities, component APIs, state matrix, action response, API routes, extension surfaces, acceptance IDs and escape-hatch policy.
- `brain/v2/team-run-commerce.md` — current component inventory, page gap matrix and AC-01–AC-71 checks.
- `brain/knowledge/merchandising-and-conversion.md` — product decision sequence, truthful recommendations, cart/checkout and service promise.
- `brain/interactive/feature-scaffold.json` — interactive feature fallbacks and candidate-bound proof requirements.
- `brain/source-registry.json` — source freshness and official platform references.

Official platform references reviewed on 2026-08-06:

- [WooCommerce Store API](https://developer.woocommerce.com/docs/apis/store-api/) — public product/cart/checkout boundary, cookie sessions and nonce/cart-token writes.
- [Store API Products](https://developer.woocommerce.com/docs/apis/store-api/resources-endpoints/products/) — published-product visibility and `type=variation` behavior.
- [Store API Cart](https://developer.woocommerce.com/docs/apis/store-api/resources-endpoints/cart/) and [Cart Items](https://developer.woocommerce.com/docs/apis/store-api/resources-endpoints/cart-items/) — authoritative cart response, item keys, variation attributes and write requirements.
- [Store API Checkout](https://developer.woocommerce.com/docs/apis/store-api/resources-endpoints/checkout) and [Checkout Order](https://developer.woocommerce.com/docs/apis/store-api/resources-endpoints/checkout-order) — draft order, nonce/cart token, order key and payment payload boundary.
- [WooCommerce REST API product variations](https://developer.woocommerce.com/docs/apis/rest-api/v3/product-variations/) — authenticated variation management/read fields.

## Repair waves

### Wave 0 — lock the contract and fixtures

**Owner:** component-commerce + catalog/Woo integrator  
**Dependencies:** none  
**Contract rows:** `entities`, `enums`, `action_contract`, `COM-01`

1. Build one resolver that joins catalog SKU → Woo product ID → variation IDs → SOT media manifest → normalized product entity.
2. Reject unknown SKU, non-published product, missing permalink, wrong-SKU media, stale variation or unverified rights. Downgrade to view-only/unavailable; never fabricate values.
3. Add deterministic fixtures for simple, variable, grouped, external, virtual/downloadable, preorder, backorder, out-of-stock, coming-soon, missing media and missing product.
4. Assert every fixture carries `source`, `checked_at`, enum values and a meaningful fallback.

**Exit evidence:** resolver payload snapshots, parity report, wrong-SKU negative test, and fixture matrix attached to one candidate ID.

### Wave 1 — canonical card, Quick View and PDP decision zone

**Owner:** component-commerce  
**Dependencies:** Wave 0  
**Contract rows:** `component_contracts.product_card`, `quick_view`, `pdp_decision_zone`, `COM-02`

1. Extend `product-card-holo` through named slots; do not create a competing card. Remove hard-coded size lists from purchase paths.
2. Add Quick View as a real labelled dialog/sheet with focus trap/restore, Escape, mobile equivalent, no-JS PDP link and stale-load protection.
3. Ensure card, Quick View and PDP share the same variation resolver and CTA transition: unselected variable → View product/Quick View; selected valid variation → Add to bag; preorder → terms-first Pre-order; out-of-stock → waitlist/View product.
4. Expand PDP gallery to the SOT-approved per-SKU minimum, with verified fallback poster/image, exact variation binding and no CTA shift on media failure.
5. Wire the universal state hooks: `data-component-id`, `data-action`, `data-request-id`, one scoped live region, focus return, 44px targets and reduced-motion/no-JS equivalence.

**Exit evidence:** desktop/mobile screenshots, keyboard/screen-reader trace, variation matrix (valid/invalid/reset), media mismatch test, and CTA request/response trace.

### Wave 2 — query/filter/search and editorial commerce ledger

**Owner:** component-commerce + layout/content  
**Dependencies:** Wave 0  
**Contract rows:** `query_filter_contract`, `component_contracts.product_grid_query`, `COM-03`

1. Allow-list URL keys (`q`, `category`, `collection`, `attributes`, `availability`, `sort`, `page`, `per_page`); escape values and ignore unknown keys.
2. Preserve shareable URL, back-navigation query and scroll position. Server owns result counts, facets and product truth.
3. Add selected chips, clear-all, keyboard-operable controls, loading/error/empty/no-results recovery and request dedupe.
4. Keep editorial inserts in named slots; never replace an explicit empty query with featured products.
5. Require ordered mobile product ledger for every lookbook/hotspot and show exact SKU, availability and View Product recovery beneath imagery.

**Exit evidence:** URL/back-navigation trace, empty/error screenshots, query payload/response fixtures, keyboard announcements and hotspot-to-ledger parity report.

### Wave 3 — cart, checkout and payment idempotency

**Owner:** WooCommerce integrator + component-commerce  
**Dependencies:** Waves 0–2  
**Contract rows:** `cart_checkout_contract`, `action_contract`, `COM-04`

1. Use Store API or server-side Woo functions for price, variation, stock, cart hash, totals, notices and shipping/tax. A client projection never authorizes purchase.
2. Add one `request_id` and one payment `idempotency_key` per intent. Disable duplicate submit; dedupe server-side; persist through redirect/reload.
3. Rehydrate the full current cart after every mutation. On timeout, reconcile by request ID, cart hash or order ID before retry. If outcome remains unknown, fail closed and route to safe support/recovery.
4. Preserve cart item key, variation attributes, quantity limits, notices, nonce/cart token and user input on failures. Add remove/undo, session-expiry and stock-race states.
5. Treat classic and Cart/Checkout block/Store API modes as separate evidence targets. If the classic override cannot support a declared block mode, withdraw compatibility explicitly.
6. Map server field errors to an error summary and first invalid field; preserve gateway fields through `updated_checkout`; cover payment loading, redirect, 3DS/verification, cancellation, no gateway and retry.

**Exit evidence:** concurrent add race, duplicate-submit trace, timeout reconciliation trace, cart totals comparison against Store API, classic/block parity report, and payment-state screenshots. No successful payment may be inferred from an HTTP response without order status.

### Wave 4 — confirmation, account, returns and service surfaces

**Owner:** WooCommerce integrator + service/content  
**Dependencies:** Wave 3  
**Contract rows:** `surface_contracts.order_confirmation`, `account`, `returns`, `service`, `COM-05`, `COM-06`

1. Render distinct paid, pending/on-hold, failed, cancelled, missing-key and unauthorized guest confirmation states. Use order key + ownership; never email-only access.
2. Add account endpoint contracts for dashboard, orders/detail, downloads, addresses, payment methods, preferences/privacy and logout with loading, empty, error, unauthorized and destructive-confirm states.
3. Build returns eligibility and authorization from one policy/version: item/quantity, delivery window, final sale, preorder, regional rule, reason, exchange availability, label/status and service escalation.
4. Service/FAQ routes issue before form; preserve entered data through nonce/spam/network failures; show response expectation and success reference.

**Exit evidence:** status/ownership matrix, authenticated and guest-token traces, WC/HPOS-safe order payloads, policy version fixture and service/return form recovery screenshots.

### Wave 5 — appointments, gift cards, loyalty, waitlist and release gate

**Owner:** component-commerce + approved provider owners  
**Dependencies:** Waves 0 and 4; provider/privacy/legal approval where applicable  
**Contract rows:** `surface_contracts.appointment`, `gift_card`, `loyalty`, `waitlist`, `COM-06`, `COM-07`

1. Appointment list works without map/location permission; slot timezone, hold/booking, confirmation, cancel/reschedule and provider failure are explicit.
2. Gift card amount/recipient/delivery/terms validation, exact currency, balance, provider, refund/regional and delivery failure states are explicit.
3. Loyalty separates benefits/terms and marketing consent; ledger shows source, points and expiry; referral credit alone cannot satisfy the contract; leave/close is reversible or explained.
4. Waitlist binds SKU and variation, dedupes signup, records consent/unsubscribe, communicates delay without inventory promise, and handles ended/unavailable state.
5. Run independent accessibility, responsive, performance, security and visual QA review. Every skip or timeout remains `UNVERIFIED`.

**Exit evidence:** provider contract IDs, privacy/consent review, timezone fixtures, duplicate/waitlist tests, screenshots for all states and independent QA verdict.

## Executable contract checks

The release verifier should fail closed on these assertions:

| Check | Assertion |
|---|---|
| `COM-01` | Every surfaced product has Woo ID/SKU/permalink, verified SOT media and current price/availability. Unknown or mismatched data cannot purchase. |
| `COM-02` | Card, Quick View and PDP use one normalized product/variation model; every CTA state has keyboard/focus/live-region behavior. |
| `COM-03` | URL query is allow-listed, shareable, restorable and server-counted; empty/error has context and recovery. |
| `COM-04` | Cart and checkout writes include nonce/cart token; responses rehydrate server truth; duplicate intents/payment cannot create duplicate line/order. |
| `COM-05` | Order/account status is ownership-protected and reload-safe; private data is not disclosed to unauthorized guests. |
| `COM-06` | Returns/service/appointment/gift/loyalty/waitlist states include consent, policy/provider source, retry and confirmation. |
| `COM-07` | Universal accessibility, reduced-motion, no-JS, error classification, policy and escaping hooks are present; escape hatches preserve canonical model. |

Map each check to the detailed AC-01–AC-71 list in `team-run-commerce.md`. A missing screenshot, trace, payload, source or independent verdict is `UNVERIFIED`.

## Escape-hatch decision record

An exception is allowed only when semantics genuinely differ (editorial hotspot, provider payment field, account endpoint or service workflow). Before implementation, record:

1. owner and reason;
2. named slot/adapter and normalized input/output;
3. `data-component-id`, `data-action`, request/response and server source;
4. all universal states, focus/live-region and reduced-motion/no-JS behavior;
5. desktop/mobile, accessibility, performance, security and commerce-truth evidence.

Hard-coded variation options, catalog-only stock/price, fake scarcity/countdowns, dead purchase links, private Woo markup as the only data source and silent payment retry are never accepted as exceptions. If a classic override cannot support declared block/Store API behavior, fail closed and document the unsupported mode.

## Handoff

The next builder receives this file and `commerce-state-contract.json` as a mandatory contract. Do not mark V2 commerce complete from a homepage/PDP screenshot. Completion requires all waves, all `COM-*` checks, the full page matrix and independent visual/accessibility/performance/security evidence against one candidate snapshot.
