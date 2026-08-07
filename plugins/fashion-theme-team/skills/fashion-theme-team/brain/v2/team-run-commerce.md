# V2 Commerce / Component Audit — SkyyRose

**Run:** 2026-08-06 · component-commerce lane  
**Scope:** V2 page plan, page blueprints, merchandising/conversion and theme-engineering knowledge, interactive feature scaffold, showcase readers, and the current `wordpress-theme/skyyrose-flagship` WooCommerce wiring.  
**Artifact status:** `team-run-commerce.md` is an audit only. Existing plans, readers, theme files, and generated assets were not modified. The plugin path is outside `/Users/theceo/DevSkyy`, so repository `git status/diff` cannot report this file; existence and content were verified directly.

## Executive verdict

V2 is a strong **planned** commerce contract, but the current theme is only **partially commerce-complete**. The canonical product-card/grid and most classic WooCommerce purchase hooks exist; the account, post-purchase, extension and error-state surfaces are not implemented to the V2 contract. The largest product-truth risks are:

1. `template-parts/product-card-holo.php` exposes hard-coded `S/M/L/XL` radio-like controls instead of the product's real variation/stock data. A static catalog fallback has no Woo product ID, so its disabled Add to Cart state is truthful but not an explicit “View product” recovery.
2. The custom PDP currently has only technical-flat + main image slots and maps every non-`instock` status to “Pre-Order” (`woocommerce/single-product.php:164-170`). Out-of-stock, backorder, pending, and variation-specific state are therefore not safely distinguished.
3. Shop/archive and collection surfaces do not expose the V2 filter, sort, active-filter, shareable URL, pagination/no-results, or scheduled/prelaunch contracts as one reusable component.
4. The custom four-step checkout is not proven against server-side validation, dynamic shipping/payment updates, block/Store API behavior, duplicate submission, or focus/error-summary recovery. It is a classic template override while the theme declares `cart_checkout_blocks` compatibility.
5. There are no theme-owned Woo account endpoint templates, returns/exchanges workflow, compare, quick-view dialog, store appointment, gift-card, loyalty, or waitlist management surfaces. The order confirmation handles success and failed payment only; pending/cancelled/guest-help/track-return paths remain gaps.

Release disposition: **BLOCKED for V2 commerce acceptance** until the page matrix below is implemented or explicitly marked out of scope and every acceptance check is run against one candidate snapshot.

## Evidence and authority

### Repository evidence read

- `/Users/theceo/plugins/fashion-theme-team/skills/fashion-theme-team/brain/v2/v2-page-plan.json` — 28 pages, page CTAs, responsive order, media policy, and `planned-not-implemented` status.
- `/Users/theceo/plugins/fashion-theme-team/skills/fashion-theme-team/brain/pages/page-blueprints.json` — route sections, classic/block mappings, and required global states (`loading`, `empty`, `error`, `success`, `unavailable`, `long-content`, missing media, keyboard, reduced motion, mobile/tablet/desktop).
- `brain/knowledge/merchandising-and-conversion.md` — product decision sequence, truthful recommendations, cart/checkout and service promise.
- `brain/knowledge/theme-engineering.md` — classic/block declaration, Woo hooks/blocks, product-type/state coverage, accessibility, security and performance contract.
- `brain/interactive/feature-scaffold.json` — 22 feature contracts, fallbacks and proof requirements; status `scaffolded-not-implemented`.
- Showcase readers (`brain/showcase/index.html`, `v2-page-plan.html`, `v2-page-atlas.html`, `interactive-feature-scaffold.html`, `brain-reader.html`) — all are readers of plans, not implementation evidence; the V2 reader explicitly says “Planned, not implemented.”
- Current canonical wiring: `template-parts/product-grid.php`, `template-parts/product-card-holo.php`, `inc/product-catalog*.php`, `inc/woocommerce*.php`, `woocommerce/archive-product.php`, `content-product.php`, `single-product.php`, `cart/*`, `checkout/*`, `page-wishlist.php`, and `assets/js/{product-card-holo,single-product,woocommerce,wishlist}.js`.

### Official platform contract consulted

The current WooCommerce developer documentation says to prefer hooks over broad template copies where possible, preserve Store API/block extensibility, and use the supported block templates for catalog, Cart, Checkout, and Order Confirmation. The Store API contract requires product/variation IDs and variation attributes for variable products and exposes cart item, quantity, coupon, customer/address, shipping-rate and checkout draft/payment state. References: [WooCommerce classic theme development](https://developer.woocommerce.com/docs/theming/theme-development/classic-theme-developer-handbook), [WooCommerce Store API](https://developer.woocommerce.com/docs/apis/store-api/), [Store API cart items](https://developer.woocommerce.com/docs/apis/store-api/resources-endpoints/cart-items), [Store API products/variations](https://developer.woocommerce.com/docs/apis/store-api/resources-endpoints/products), and [WooCommerce block template guidance](https://developer.woocommerce.com/docs/llms-full.txt).

These references are guidance for acceptance, not proof that the current candidate implements the behavior.

## Canonical component inventory and contracts

Reuse these existing pieces before creating a new component. Names below are implementation contracts to make gaps testable; they are not permission to add duplicate systems.

| Component / current source | Anatomy and slots | Required variants / sizes | Required state coverage | Data contract and boundary |
|---|---|---|---|---|
| Global shell (`header.php`, `template-parts/mobile-bottom-nav.php`, `assets/js/navigation.js`) | skip link; announcement; masthead; primary nav; search; account; bag badge; notices; drawers/dialogs; footer | desktop/tablet/mobile; menu closed/open; account guest/auth; bag 0/>0; locale supported/unknown | default, hover, focus-visible, active/current, loading search, no results, network error, drawer open/close, reduced motion | `route`, nav items, `accountUrl`, `cartUrl`, `cartCount`, `search endpoint`, nonce. Cart count must come from WC/Store API and be announced; shell owns navigation only, not product decisions. |
| Product card (`template-parts/product-card-holo.php`, optional `product-card-v7-lookbook.php`) | media front/back; collection; name; price; badge; variation trigger; wishlist; purchase/view CTA; status/live region | simple/variable/preorder/unavailable; S/M/L/etc from SOT (never fixed list); compact/rail/grid; eager first-row vs lazy | default, hover, focus, selected variation, disabled, loading, success, error, out-of-stock, backorder, coming soon, missing media | `sku`, WC product/variation IDs, SOT media manifest, price HTML, currency, stock/backorder, purchasable, attributes, permalink, collection. Static card may render only view CTA and must carry `fallbackReason`; no `#` purchase URL. |
| Product grid (`template-parts/product-grid.php`, Woo archive) | heading/subheading; controls slot; active filters; grid; editorial insert; pagination; empty/recovery | 4→2 columns; collection/search/shop; sort/filter modes; dense/sparse; curated list | loading skeleton, partial media, empty, no-results, query error, unavailable products, pagination loading/error | catalog query + WC live projection; URL query state; counts; cursor/page; SOT provenance. Grid must not silently fall through to featured products when explicit list is empty (current helper does this correctly). |
| PDP decision zone (`woocommerce/single-product.php`, `product-detail-editorial.php`) | identity; price; media gallery; variation controls; size/fit; availability; fulfillment; returns; add-to-bag; notices | simple/variable/grouped/external/virtual/downloadable; in-stock/backorder/preorder/out; sale/regular; desktop sticky/mobile inline | default, loading variation, selected/unselected, invalid combination, unavailable, stock race, add success/error, network retry | product ID/SKU, variation matrix, selected attributes, SOT frame IDs, price/regular/sale, stock quantities/status, preorder terms/date, shipping/returns facts. PDP owns decision facts; editorial modules cannot replace them. |
| Quick view (not yet implemented; card drawer is not a dialog) | modal/sheet; media; identity/price; variation/size; availability; purchase; full PDP link; notices | desktop side sheet/mobile full sheet; simple/variable; reduced-motion | closed/open, focus trap/restore, loading, invalid variation, unavailable, add success/error, close/network error | product ID + variation attributes; must use real WC add-to-cart contract and preserve collection context. No hover-only or fake size controls. |
| Lookbook/shoppable chapter (`template-parts/collection/film-spine.php`, landing templates) | scene; chapter label; hotspot/annotation; ordered product ledger; credits/rights; fallback | desktop hotspot/mobile ordered list; motion/static; one/many products | media loading/error, hotspot unavailable, product out, no-JS, reduced motion | approved media ID/rights, hotspot coordinates, ordered SKU IDs, availability and fallback links. Hotspot cannot be the only product fact. |
| Wishlist (`page-wishlist.php`, `inc/wishlist-functions.php`) | saved summary; product rows; change notices; remove; move-to-cart; share; empty recovery | guest/session vs authenticated/merge; simple vs variable; compact/mobile rows | loading, saved, duplicate, removed, full (50 cap), expired/invalid product, out, variation required, move success/partial failure | product/variation ID, selected size/color, session/user ownership, nonce, expiry, privacy/share token. Current move-to-cart sends only product ID and cannot truthfully move a variable item without selected attributes. |
| Cart (`woocommerce/cart/cart.php`, `cart-empty.php`) | notices; line item; thumbnail; variation/meta; quantity; remove; coupon; shipping/tax; totals; cross-sell; checkout; empty recovery | empty/single/multi; sold individually; backorder; coupon; mobile/desktop | loading, live update, stale stock, coupon success/error, remove/undo, session expiry, network error, totals recalculation | cart item key, product/variation IDs, quantity min/max, price/subtotal, tax/shipping, notices, nonce, cart hash. Current custom cart deliberately omits `woocommerce_cart_collaterals`; document equivalent cross-sell decision and preserve extension boundary. |
| Checkout (`woocommerce/checkout/form-checkout.php`) | focused header; error summary; contact; addresses; shipping; order summary; coupon/gift card; payment; terms; place order; recovery | guest/auth; physical/virtual; one/multi package; gateways; mobile collapsed summary | field invalid, server validation, shipping refresh, payment loading/failure/redirect, stock/session race, duplicate submit, success/pending/failure | checkout draft/order ID, billing/shipping, shipping package/rate, payment gateway state, nonce, idempotency key, totals. UI must not invent fields or hide gateway markup. |
| Order confirmation (`woocommerce/checkout/thankyou.php`, standard order details) | status; reference; items/totals; delivery/payment; track; return/help; account invite; continue shopping | paid/pending/on-hold/failed/cancelled; guest/auth; downloadable | loading refresh, success, pending, failed/retry, unauthorized, missing order, privacy-safe guest view | order key + permission, status, line items, totals, payment result, fulfillment/tracking, returns URL. Current template only clearly covers `$order` success and `failed`. |
| Account/auth (no theme-owned Woo account templates) | login/register/reset; dashboard; orders/detail; downloads; addresses; payment; preferences/privacy; logout | guest/auth; empty history; endpoint unsupported; mobile task list | loading, validation, auth error, unauthorized, empty, destructive confirm, logout success/error | WP/WC customer identity, endpoint capabilities, order ownership, nonce, password-manager-compatible fields. Do not expose order data by email alone. |
| Service / returns / policy (`template-contact.php`, `template-shipping-returns.php`, `template-policy.php`) | FAQ/search; contact route; order context; return eligibility; policy document; escalation | guest/auth; region; final-sale/preorder; attachments optional | validation, loading, success, spam/network error, ineligible, expired, policy version | order ID + ownership/guest token, item/variation, region, policy version/effective date, consent. Current returns page is informational and contact form is not an order workflow. |

### Stateful CTA matrix

Every CTA uses a native `<button>`/`<a>` with a stable `data-component-id` and `data-action`, at least a 44px target, visible focus, and a live status region for asynchronous changes. Purchase/service actions do not use magnetic movement or delayed animation.

| CTA family | Default / hover / focus / active | Loading | Success | Warning / unavailable | Error / recovery |
|---|---|---|---|---|---|
| View product / story | explicit link, underline draw only on hover/focus | n/a | route changes with focus to main heading | unavailable product routes to archive/PDP with reason | route failure preserves context and offers search/home |
| Add to bag / pre-order | rose-gold fill, label includes product name | `aria-busy=true`, disabled duplicate submit, label remains in accessible name | “Added …” announcement; cart badge and totals refresh | variation required, out-of-stock, backorder/preorder terms shown before submit | WC error notice associated with CTA; retry and PDP path |
| Move to cart / checkout / place order | stable explicit action | idempotency key, spinner/status, disabled only during request | cart/order state and next action announced | stock/tax/shipping changed: require acknowledgement before continuing | server summary + field links; never just color or toast |
| Join waitlist / contact / return | consent and terms adjacent | submission lock | confirmation reference and expected response | duplicate, ineligible, unavailable | inline field errors, retry without losing answers |

## Shared data/API contracts

The implementation should normalize one read model and one action model. PHP templates may render server-side, but all asynchronous paths emit the same shape.

```json
{
  "product": {
    "id": 123,
    "sku": "br-001",
    "name": "Black Rose Crewneck",
    "media": [{"id":"br-001-front","src":"…","alt":"…","rights":"sot"}],
    "price": {"currency":"USD","regular":"…","sale":"…","display":"…"},
    "type":"variable",
    "attributes": [{"name":"size","options":[{"value":"m","label":"M","available":true}]}],
    "selectedVariationId": null,
    "availability": {"status":"in_stock|backorder|preorder|out_of_stock|coming_soon","quantity":null,"shipDate":null},
    "fulfillment": {"shippingText":"…","returnsText":"…"},
    "provenance": {"catalogSku":"br-001","mediaManifest":"…"}
  },
  "cta": {"action":"add_to_cart","state":"idle","requestId":"…","fallbackHref":"…"}
}
```

Action responses must be `{ok, state, message, cartHash/orderId?, fieldErrors?, notices?, retryable, source}`. For variable products, the action includes `productId`, `variationId`, `variation` attribute map, and quantity. A product card may only show “Add to bag” when an unambiguous purchasable product/variation is known; otherwise it shows “View product”.

Platform mappings to verify:

- Classic add-to-cart: WooCommerce add-to-cart action/filter and fragments, with `wc_get_product()` as the live price/stock authority.
- Store API add item: `POST /wp-json/wc/store/v1/cart/items` with product ID, quantity, and variation attributes; update/remove/coupon/customer/shipping endpoints must return and re-render notices/totals.
- Checkout: draft checkout data, customer/address updates, shipping selection, gateway payload, payment result and redirect URL; never treat a client-side four-step transition as validation.
- Order confirmation/account: order key/ownership and order status are the authorization boundary; guest views must not reveal private email/address/payment details.

## Page-by-page gap and acceptance matrix

`P` means the V2 plan/blueprint contract. `C` means current candidate observation. Every row needs the listed CTA/data contract and the exact acceptance IDs below before it can be called complete.

| V2 page | Current C | Gap against P | CTA/data contract to close | Exact acceptance checks |
|---|---|---|---|---|
| Global shell | Header has account URL, cart count and search; mobile nav exists. | No single shell notice/live-region contract; cart count is not proven announced; dialog focus/reduced-motion coverage is fragmented. | `cartCount`, `searchQuery`, loading/error/empty suggestions, drawer return focus. | `AC-01,02,03,04,05,06` |
| Home | `front-page.php` and shared catalog/product grid; media is SOT-gated in helpers. | Curated rail lacks explicit live stock/variation state and unavailable fallback; shoppable editorial lacks shared product ledger contract. | `shopCollection`, `exploreStory`, each SKU/media/provenance/availability. | `AC-07,08,09,10` |
| Shop / all products | Woo archive and canonical product card. | No V2 category shortcuts, filters, active chips, shareable query, sort persistence, editorial insert contract or custom no-results recovery. | URL `{q,category,attributes,sort,page}`; counts; card view-vs-add decision. | `AC-11,12,13,14,15` |
| Collection | Four collection templates and catalog-based grids exist. | Scheduled/prelaunch/sold-out archive/taxonomy fallback/deep-linked chapter states not unified; collection claims may diverge from live stock. | `collectionId`, chapter IDs, SKU order, schedule timezone, availability fallback. | `AC-08,11,13,16` |
| Search | `search.php` has escaped query, product/content sections and empty suggestions. | No filter/sort/scope controls or keyboard suggestion state contract; product result and content result pagination are separate and no network retry. | escaped query, result type, suggestion request ID, privacy-safe event payload. | `AC-01,11,14,17` |
| PDP | Custom `single-product.php` plus editorial template, WC add-to-cart, size guide. | Two-image gallery vs ten-frame plan; no review/complete-look contract; non-`instock` rendered as Pre-Order; variation/stock/price updates not candidate-proven; no explicit shipping/returns facts in decision zone. | product/variation/media manifest, stock status enum, price context, fit/fulfillment/return facts. | `AC-18,19,20,21,22,23` |
| Quick view | No dedicated dialog; holo drawer has hard-coded S/M/L/XL and no variation ID. | Missing dialog semantics, focus trap/restore, mobile sheet, loading/error/unavailable and full-PDP contract. | real product form + variation map; fallback full PDP. | `AC-24,25,26` |
| Compare | No `compare` template or component found. | Entire extension surface missing, including missing-data and mobile transformation. | selected SKU list, normalized attributes, availability, remove/view/add actions. | `AC-27` |
| Lookbook | Landing/film-spine links products and has mobile/scroll fallbacks in places. | No stable hotspot IDs/ordered mobile product ledger/availability fallback/rights ledger across chapters. | chapter → exact SKU IDs + hotspot coords + credits + status. | `AC-08,28,29` |
| Campaign / drop launch | Preorder gateway exists; campaign templates/scaffold exist. | Timezone-safe schedule, queue rules, terms-first mobile order, sold-out archive and fair participation are not proven; avoid static/fake countdown. | launch timestamp/timezone, release facts, terms, queue/preorder/waitlist state, payment/cancel terms. | `AC-16,30,31,32` |
| About | `template-about.php` and parts are editorial. | Story CTAs are not tied to a verified collection/product context; claims/provenance and service contact need machine IDs. | claim/source IDs, collection CTA, contact CTA, approved media rights. | `AC-08,33` |
| Journal index | `archive.php`/content parts provide article archive. | Featured/category/search/pagination empty state not aligned to a content contract; no related product provenance. | article IDs, topic filters, pagination, featured SKU IDs where present. | `AC-11,14,34` |
| Journal article | `single.php` exists. | No explicit related-products ledger, commerce label, corrections/share contract or media embed fallback. | article schema, credits, related SKU IDs with live availability, correction version. | `AC-08,34` |
| Size & fit | `template-size-guide.php` and `size-guide-modal.php` exist; modal has focus handling. | Static tables are not proven to carry product overrides, localized units, recommendation disclosure, model references, or no-false-precision states. | category, unit, product/variation override, measurements, model worn size, confidence/disclosure. | `AC-20,35` |
| Wishlist | Custom guest/session + user persistence and AJAX actions exist. | No account merge/expiry/share privacy contract; variable products cannot move to cart without selected variation; max-50 failure needs visible state. | user/session key, variation attrs, expiry, share token, partial move result. | `AC-36,37,38` |
| Cart | Custom cart preserves many core hooks, nonce, variation/meta, coupon and totals; empty template exists. | No explicit live region/undo/session-expiry/network recovery; cross-sell hook intentionally omitted; shipping progress is a custom promise requiring configuration proof; Store API/block parity unknown. | cart hash/items/notices/totals/shipping/tax/coupon; update idempotency and retry. | `AC-39,40,41,42,43` |
| Checkout | Custom four-step classic checkout with fields, gateway list, terms and order submit. | Server validation and dynamic checkout refresh are not mapped to step errors; duplicate prevention/idempotency, payment redirect/failure, stock/session race, block parity and order-review hooks need proof. | checkout draft, addresses, package/rate, gateway, payment result, idempotency key, field error map. | `AC-44,45,46,47,48,49` |
| Order confirmation | Custom thank-you handles success and failed payment, calls standard order details/actions. | Pending/on-hold/cancelled/missing/unauthorized states, track-order, return/help and continue-shopping CTAs are incomplete; privacy-safe guest refresh unproven. | order key/ownership, status, totals/items, tracking, returns URL, account invite. | `AC-50,51,52` |
| Account/auth | Header links to Woo My Account, but no account templates are in theme. | Login/register/reset, endpoint navigation, empty order history, auth failure, address/payment preferences, privacy/destructive/logout states unreviewed and likely default Woo markup. | authenticated customer context, endpoint capability/ownership, redirect and nonce. | `AC-53,54,55,56` |
| Returns/exchanges | `template-shipping-returns.php` is policy content; FAQ promises email workflow. | No guided order/item eligibility, final-sale/preorder/regional rules, exchange availability, label/status or confirmation flow. | order/guest auth token, item IDs, policy version, reason, resolution, logistics state. | `AC-57,58,59` |
| Service/contact/FAQ | Contact form has nonce, field errors and AJAX status; FAQ content exists. | No route-first service navigation, response expectation, attachments/order context/escalation contract; form success must be candidate-proven. | subject/order ID/preferred channel, consent, attachment policy, response SLA, nonce. | `AC-60,61` |
| Stores/appointments | No store/appointment page or booking integration found. | Entire extension missing, including non-map list, timezone, permission fallback and cancel/reschedule. | location/service/slot/timezone, customer identity, confirmation/cancel token. | `AC-62` |
| Gift card | No gift-card page/component found. | Amount/design/recipient/delivery/terms/preview, balance, invalid recipient/delivery failure and regional/refund states missing. | amount/currency, recipient validation, schedule, terms, provider/balance response. | `AC-63` |
| Loyalty/membership | Referral credit code exists in preorder Woo integration; no member surface/ledger found. | Benefits/eligibility/earning/redemption/consent/expiry/leave/close and account integration missing. Referral credit is not a loyalty UI contract. | member ID, consent separation, points ledger, expiry, terms, close action. | `AC-64` |
| Preorder/waitlist | `woocommerce-preorder.php` stores product meta and changes price/button; preorder gateway lists catalog items. | Variation-aware inventory race, exact timing/timezone, cancellation, waitlist consent/duplicate handling/delay communication/unsubscribe are absent or unproven. | SKU/variation, preorder status/date/price/edition, payment/cancel terms, consent and notification ID. | `AC-16,21,65,66` |
| Coming soon/password | `template-coming-soon.php` contains email form and nonce. | Scaffold requires real schedule/countdown, customer/admin access, cache status, form errors and legal/privacy; current JS fallback countdown must not invent a launch time. | schedule/timezone, access token, notification consent, cache state, privacy URL. | `AC-30,67` |
| 404/empty/error | `404.php`, search empty, cart empty and product-grid optional empty copy exist. | Correct HTTP status, error classification, network retry, preserved query/category context and consistent recovery component not proven on every route. | error ID/class, safe reference, retry action, search/category/service URLs. | `AC-01,68,69` |
| Legal/policy | `template-policy.php` and shipping/returns pages exist. | Effective date, owner/version history, regional disclosures, print and preference controls are not machine-bound; policy promises conflict in places and need one SOT. | policy ID/version/effective date/region, owner-approved copy, contact/escalation. | `AC-70,71` |

## Exact acceptance checks

The following checks are deliberately executable and candidate-bound. A skipped or unavailable check is `UNVERIFIED`, never pass.

### Component, accessibility and responsive checks

- **AC-01 Shell keyboard:** Tab from skip link through nav/search/account/bag; open/close every drawer/dialog with Enter/Space/Escape; focus returns to trigger; no focus enters hidden panel.
- **AC-02 Names and targets:** Every interactive element has an accessible name; visible label is included in its name; purchase/service targets are at least 44×44 CSS px.
- **AC-03 Status announcements:** Add, remove, cart update, search loading/error/empty, checkout validation, payment result and contact/return submission update one polite/assertive live region without duplicate announcements.
- **AC-04 Motion:** `prefers-reduced-motion: reduce` removes reveal/scroll-jacking/magnetic behavior while preserving order and CTA reachability; no purchase action waits for animation.
- **AC-05 Responsive:** Render all core pages at 320px, 375px, 768px and 1440px; no horizontal overflow; product, price, fit, availability, terms and primary action precede atmosphere on mobile.
- **AC-06 Forced colors/zoom:** At 200% zoom and forced-colors mode, focus, selected, disabled, stock and error states remain discernible without color-only cues.

### Product truth and merchandising checks

- **AC-07 Catalog/WC parity:** For every surfaced SKU, assert catalog SKU → WC product ID → permalink and SOT media manifest. Unknown SKU or missing media cannot produce a purchase CTA.
- **AC-08 Media provenance:** Every product image has a source ID and exact SKU/variation binding; wrong-SKU media test fails the build; missing optional media renders the documented static fallback.
- **AC-09 Price/stock:** Fixture matrix covers regular, sale, zero/preorder, out-of-stock, backorder, sold-individually and unavailable; rendered label and CTA match WC authority, including variation-level price/stock.
- **AC-10 Card CTA:** Simple purchasable item can add once; variable item cannot add until a real available variation is selected; static fallback exposes View Product, not a dead `#` or fake size selector.
- **AC-11 Query state:** Shop, collection and search filters/sort/page are encoded in shareable URL, restored on back navigation, keyboard-operable, announced and resettable; counts match the result set.
- **AC-12 No-results recovery:** Empty product/content/search grids retain query/category context and offer Browse all, relevant collection, clear filters and service/search recovery.
- **AC-13 Availability fallback:** Sold-out, scheduled, unpublished, missing, or expired product states show reason, next truthful action and no fabricated scarcity/countdown.
- **AC-14 Recommendation truth:** Related/complete-look/cross-sell items exclude current/duplicate/incompatible/unavailable items unless an explicit recovery path exists; each relation has provenance and event ID.
- **AC-15 Product type matrix:** Simple, variable, grouped, external, virtual and downloadable behavior is tested or explicitly disabled with a documented fallback; no template assumes a simple product.
- **AC-16 Schedule/timezone:** Campaign, preorder and coming-soon schedule tests use an explicit timezone and server time; before/live/ended states render deterministic facts and terms; no client-only fake default.
- **AC-17 Search safety:** Query is escaped on render and analytics is privacy-safe; keyboard suggestion loading, empty, error, cancel and Enter-to-full-results all work without leaking raw personal data.
- **AC-18 PDP gallery:** At least ten approved media slots (or a documented per-SKU minimum) map to the exact SKU/variation; poster/video/zoom failure falls back without shifting CTA; first content is eager and below-fold media lazy.
- **AC-19 Variation contract:** Selecting every valid/invalid attribute combination updates image, price, SKU, availability and add button from WC variation data; reset clears selected state; no hard-coded sizes survive.
- **AC-20 Fit evidence:** Size guide opens as an accessible dialog, provides category/unit/product override/model evidence, discloses recommendation limits and works without JS.
- **AC-21 Fulfillment/returns:** PDP and checkout show truthful ship/preorder/backorder timing, cancellation, regional shipping and returns/final-sale terms tied to current policy version.
- **AC-22 PDP stock enum:** `instock`, `onbackorder`, `outofstock`, preorder and unavailable produce distinct visual, text and CTA states; no non-`instock` value renders “Pre-Order” by default.
- **AC-23 PDP purchase:** Add-to-cart request sends product/variation/attributes/quantity, prevents duplicate submit, handles WC notices/errors, refreshes cart fragments/hash and returns focus to the CTA/status.
- **AC-24 Quick-view dialog:** Dialog has labelled title, `aria-modal`, focus trap/restore, Escape close, mobile sheet layout, no-JS full PDP link and no background scroll/focus leak.
- **AC-25 Quick-view variation:** Same AC-19/22/23 matrix applies inside quick view; closing/reopening resets or preserves state by documented policy.
- **AC-26 Quick-view failure:** Missing product, media, network or unavailable variation gives a visible recovery to full PDP; no stale product remains in the sheet.
- **AC-27 Compare:** Add/remove two or more SKUs, highlight factual differences, show missing data explicitly, preserve matched crop/scale, and transform to one-baseline swipe/stack on mobile.
- **AC-28 Lookbook ledger:** Every hotspot has keyboard label and ordered mobile equivalent; exact SKU, current availability and View Product recovery are visible below the image.
- **AC-29 Rights/credits:** Lookbook/campaign/article media has rights/credit metadata and no product claim is inferred from an unverified editorial frame.

### Cart, checkout, account and service checks

- **AC-30 Campaign fairness:** Purchase is never gated by a game/animation; skip-to-shop, transcript, terms, queue rule and sold-out archive are present; countdown is server-sourced and timezone-safe.
- **AC-31 Preorder terms:** Preorder CTA displays edition, current available quantity only when WC-authoritative, price, estimated ship date/timezone, charge timing and cancellation/refund terms before submission.
- **AC-32 Queue/inventory race:** Two concurrent add/reserve attempts produce one authoritative success or a clear unavailable error; no stale “remaining” count is trusted for purchase.
- **AC-33 About claims:** Founder/Oakland/value/press claims have source IDs, approved media rights and a working collection/service CTA; no unsupported metric is presented as fact.
- **AC-34 Editorial commerce:** Article related-product modules use canonical card data, disclose “Shop featured piece,” and handle unavailable SKU without breaking reading flow.
- **AC-35 Fit table accessibility:** Tables have captions/headers/scope, units persist through interaction, zoom/reflow works, and no recommendation claims false precision.
- **AC-36 Wishlist persistence:** Guest add/remove survives reload only within documented session/expiry; auth state uses user-owned storage; no cross-user leakage.
- **AC-37 Wishlist variable move:** Variable wishlist item requires a selected real variation or routes to PDP; move-all returns per-item success/failure, preserves failed items, and announces result.
- **AC-38 Wishlist privacy:** Share uses revocable, non-guessable token with explicit consent; clear/expiry/full-capacity and unavailable states are reversible or explain loss.
- **AC-39 Cart core:** Add/remove/update/coupon preserve cart nonce, cart item key, variation/meta, totals, notices and fragments; update failure does not erase user input.
- **AC-40 Cart state:** Empty/single/multi/backorder/out-of-stock/session-expired/network-error states have explicit recovery and live announcements; remove has undo where feasible.
- **AC-41 Cart totals:** Subtotal, discounts, tax, shipping and grand total match WC/Store API after every mutation; custom free-shipping progress is clearly informational and uses configured threshold/currency.
- **AC-42 Cart extensions:** Document and test the intentional omission/replacement of `woocommerce_cart_collaterals`; compatible cross-sell path cannot destabilize totals/focus and excludes incompatible items.
- **AC-43 Cart block parity:** If Cart block is enabled, test block Store API behavior separately from classic template; no private-markup selector is the only integration path.
- **AC-44 Checkout server validation:** Invalid email/address/required field/server notice appears in an error summary linked to field, focus moves to first error, and step navigation cannot bypass it.
- **AC-45 Checkout dynamic refresh:** Address changes recalculate shipping/tax/order total; shipping method selection persists; gateway fields survive `updated_checkout` and are not duplicated.
- **AC-46 Payment states:** Gateway loading, inline error, redirect, cancellation, 3DS/verification, no available gateway and retry all have explicit status and recovery; no invented “secure” claim substitutes provider state.
- **AC-47 Duplicate prevention:** Place-order double click/retry uses a request/idempotency guard; one customer action cannot create two orders; refresh after redirect is safe.
- **AC-48 Stock/session race:** Checkout rejects stale stock/session with actionable cart/PDP recovery, preserves safe fields, and recalculates totals before payment.
- **AC-49 Checkout block parity:** Test classic and Checkout block/Store API paths when declared compatible; extension fields and notices appear in both or compatibility is explicitly withdrawn.
- **AC-50 Order status:** Paid, pending/on-hold, failed, cancelled, missing/invalid key and unauthorized guest cases show distinct copy, status and next CTA; never disclose private order data.
- **AC-51 Order next steps:** Confirmation exposes reference, items, totals, delivery/payment, track-order/help, returns eligibility, account invitation and continue-shopping according to actual integrations.
- **AC-52 Idempotent confirmation:** Reload/back/duplicate webhook does not duplicate analytics/order actions; order details respect order key/ownership and downloadable permissions.
- **AC-53 Auth flow:** Login/register/reset supports password managers, server validation, error summary, redirect intent, focus and rate-limit/lockout messaging; no account data appears before auth.
- **AC-54 Account endpoints:** Dashboard/orders/order detail/downloads/addresses/payment/preferences/privacy/logout each have loading, empty, error, unauthorized and destructive-confirm states; mobile task navigation is operable.
- **AC-55 Account order truth:** Order history and detail use current WC/HPOS-safe APIs, correct status/totals/items, ownership checks and no stale catalog price/media.
- **AC-56 Logout/privacy:** Logout clears session-facing private data, returns focus/context, and privacy controls explain consent/retention; destructive account actions require confirmation.
- **AC-57 Returns eligibility:** Select order/item/quantity; enforce delivery date, final sale, preorder, regional and window rules from one policy/version; show reason and resolution choices.
- **AC-58 Returns authorization:** Authenticated and guest order access is ownership/guest-token protected; ineligible/expired/duplicate states preserve explanation and service escalation.
- **AC-59 Returns status:** Label/logistics/submission/confirmation/status and exchange stock states are explicit, retryable and privacy-safe.
- **AC-60 Service routing:** FAQ/search routes the issue before form; channel response expectation is visible; order context is optional and permission-checked.
- **AC-61 Service form:** Required-field errors, nonce/spam failure, attachment policy, network retry, success reference and escalation are all announced without losing entered data.
- **AC-62 Store appointment:** Accessible list works without map/location permission; slot timezone, availability, booking confirmation, cancel/reschedule and failure are tested.
- **AC-63 Gift card:** Amount/recipient/delivery/terms validation, provider failure, balance check, refund/regional constraints and confirmation are tested with exact currency.
- **AC-64 Loyalty:** Benefits/terms precede enrollment, marketing consent is separate, points/expiry ledger is accurate, immediate-value experiment is labelled and leave/close works.
- **AC-65 Waitlist:** Duplicate signup, variation binding, consent/unsubscribe, unavailable/ended state, delay communication and confirmation ID are tested.
- **AC-66 Preorder payment:** Charge timing, cancellation/refund, mixed cart shipping, variation availability and inventory race match the configured Woo extension; no static copy can override it.
- **AC-67 Coming soon:** Before/live/ended/admin/customer access, notification consent/error, cache status and legal/privacy links are tested; no arbitrary fallback countdown.
- **AC-68 HTTP/error classification:** 404 returns HTTP 404; empty catalog/search is not 404; network/WC error has retry and safe reference; error page preserves route/query context.
- **AC-69 Empty-state consistency:** Cart, wishlist, search, shop, collection, account, related products and downloads use canonical empty component with useful next action and no filler product/media.
- **AC-70 Policy governance:** Policy ID, owner, effective date, region, version history, print and contact/escalation are rendered; all shipping/returns/preorder copy resolves from one approved source.
- **AC-71 Security/escaping:** Product/query/order/user inputs are escaped by context; forms use nonces/capability/ownership checks; no credentials/customer data in fixtures or browser events.

## Escape-hatch policy

1. **Canonical first:** Extend `product-card-holo`, `product-grid`, the shared catalog/WC resolver, Woo hooks/blocks, and the stateful CTA contract before creating a bespoke component.
2. **Allowed escape hatches:** a page may supply a named slot or adapter when its semantics genuinely differ (editorial hotspot, campaign terms, account endpoint, provider payment field). It must still consume the normalized product/action model, emit `data-component-id`/`data-action`, preserve keyboard/reduced-motion/error semantics, and document its owner.
3. **Not allowed:** private Woo markup selectors as the only integration, direct catalog price/stock in a purchase CTA, hard-coded variation options, fake scarcity/countdowns, dead `#` purchase links, unlabelled AI/provider output, or a visual-only success toast.
4. **Compatibility boundary:** If a classic override cannot support the declared Cart/Checkout blocks or Store API, fail closed and document the unsupported mode; do not silently claim compatibility. Prefer hooks/block extensions over copying upstream templates, and record the upstream template version whenever an override remains.
5. **Evidence requirement:** Each escape hatch requires source authority, desktop/mobile captures, keyboard/screen-reader trace, reduced-motion/fallback result, performance result, and commerce-truth payload attached to the same candidate snapshot. A missing artifact is `UNVERIFIED`.

## Handoff to the V2 lead

Treat this report as a commerce gate, not a build authorization. The next implementation plan should prioritize: (1) normalized product/variation/availability contract and card/PDP state machine, (2) filter/search/quick-view/compare and shoppable ledger primitives, (3) cart/checkout classic + Store API parity and error/idempotency evidence, then (4) account/order/returns/service surfaces. Keep all 28 pages in the acceptance ledger; a polished home/PDP with default account, empty, checkout or post-purchase states is not V2 complete.
