---
name: wc-pdp-correctness
description: WooCommerce product-detail-page correctness checklist for theme work — AJAX add-to-cart, variations, stock, button states, cart fragments. Use when building, changing, or reviewing single-product templates, product cards, or any add-to-cart surface in skyyrose-flagship.
---

# WooCommerce PDP Correctness

Core-contribution style guides don't cover this. This checklist is for THEME add-to-cart surfaces — where a broken button = zero revenue and no error log.

## AJAX add-to-cart contract (simple products)

- Button needs BOTH: class `ajax_add_to_cart` AND `data-product_id="<id>"` — `wc-add-to-cart.js` binds on the class, reads the data attr. Missing either = silent nav-to-nothing.
- `add-to-cart` handle: `WC_Frontend_Scripts::register_scripts()` registers it; `wc_add_to_cart_params` is auto-localized via `localize_printed_scripts()` — if you enqueue custom cart JS, depend on `wc-add-to-cart`, don't re-implement.
- Also required on the anchor/button: `data-quantity`, `aria-label` naming the product, and `rel="nofollow"` on anchors.
- After AJAX success WC fires `added_to_cart` event with fragments — custom mini-cart/count badges must listen to it AND `wc_fragments_refreshed`, or counts go stale.

## Variable products

- Variation forms canNOT AJAX-add via the simple-product path: the form posts `variation_id` + attribute fields. A themed "quick add" for variable products must either open the variation form or use `?add-to-cart=<id>&variation_id=<vid>&attribute_pa_size=<v>` with ALL required attributes — partial attributes = WC error notice.
- `data-product_variations` JSON on the form drives the picker; if a template strips it, the picker dies silently. Verify `woocommerce_variation_add_to_cart` hooks stay intact when restyling.
- Out-of-stock variations: form shows but button must disable on `found_variation`/`hide_variation` events — test one OOS combo explicitly.

## Stock, quantity, states

- Respect `$product->is_purchasable()` and `is_in_stock()` — pre-order/launch-mode products may be non-purchasable BY DESIGN (Kids Capsule launch mode shows 0 cards intentionally; don't "fix" it).
- Quantity input: min/max/step from `woocommerce_quantity_input_args` — a custom stepper that ignores `max` oversells.
- Button states to verify (each with visible styling): default → loading (`.loading`) → added (`.added`) → View-cart link appears. WC toggles these classes; custom CSS must style all three or the button appears dead during the round-trip.

## Verification battery (run all, live or staging)

1. Simple product: click add → network shows `?wc-ajax=add_to_cart` 200 → cart count increments WITHOUT page reload.
2. Variable product: select full attribute set → add → cart shows correct variation meta.
3. OOS variation combo → button disabled, no add possible.
4. Quantity >1 respected in cart line.
5. Logged-out CLEAN session (incognito) — nonce/session edge: first-ever add works. (Batcache/edge-cached pages can serve stale nonces — CommerceKit nonce corruption was a real production incident here.)
6. Cart fragments refresh: badge/mini-cart updates on add AND on browser-back after add.
7. `php -l` + PHPCS on touched templates; escape everything (`esc_url(add_query_arg(...))`, `esc_attr` on data attrs).

## Known local landmines

- WP.com Atomic: `/wp-json/` may 401 — REST via `?rest_route=` or wc/v3 with BasicAuth.
- Ally/accessibility plugins can corrupt CommerceKit nonces (bug fixed via MU-plugin `option_active_plugins` guard) — if add-to-cart 403s appear, check plugin interference before blaming the theme.
