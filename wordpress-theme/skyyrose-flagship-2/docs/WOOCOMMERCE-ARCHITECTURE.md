# Flagship WooCommerce Architecture

## Decision

SkyyRose Flagship 2 remains a classic PHP theme with a hook-first WooCommerce
integration. The theme owns presentation; WooCommerce owns product, variation,
price, inventory, tax, shipping, cart, checkout, account, order, and payment
truth.

The release baseline is WooCommerce 10.9.1. Template `@version` values are the
upstream template versions shipped by that release, not the plugin release
number.

## Override budget

The theme carries four structural overrides and no `woocommerce.php` catch-all:

| Override | Why it remains structural | Upstream template version |
| --- | --- | --- |
| `archive-product.php` | House heading, collection-world navigation, and builder archive ownership | 8.6.0 |
| `single-product.php` | Collection breadcrumb, pre-order truth, verified 3D gate, and collection epilogue | 1.6.4 |
| `content-product.php` | One semantic commerce card contract shared by Woo loops and editorial surfaces | 9.4.0 |
| `cart/cart.php` | Editorial bag layout while preserving every current cart hook and filter | 10.8.0 |

Everything else uses WooCommerce templates and public hooks. Checkout, account,
notices, forms, emails, totals, payment methods, and order states are not copied
into the theme.

## Compatibility contract

- `inc/woocommerce-integration.php` replaces only the default wrapper,
  breadcrumb, archive-header, and sidebar callbacks. Their public actions still
  fire for extensions.
- The archive fires `woocommerce_shop_loop_header` in addition to the complete
  product-loop contract.
- The single-product template fires before/after-main and sidebar actions around
  WooCommerce's unmodified `content-single-product` template.
- The cart preserves current item, price, quantity, subtotal, backorder, coupon,
  action, and collateral extension points.
- `scripts/verify-woocommerce-contracts.php` fails packaging when an override
  loses a required hook/filter or drifts from the pinned upstream version.

Source checks prove contract presence only. The exact installable archive must
still pass an execution smoke on staging before visual, accessibility,
performance, or marketplace claims begin.

## SWOT converted to execution

### Strengths become protected primitives

- Four collection worlds remain presentation modes over one WooCommerce data
  contract.
- Product cards consume real `WC_Product` objects and attached/SOT-approved
  media; missing media fails visibly instead of substituting another garment.
- Pre-order language derives from product taxonomy and stock state.
- 3D remains absent until the approved-model resolver validates an exact SKU.

### Weaknesses become release controls

- Narrow merchant control becomes curated house settings and section presets,
  not an unlimited option panel.
- Template maintenance becomes a four-file override budget plus a pinned
  contract verifier.
- Builder support becomes explicit ownership: builders may replace an assigned
  page/location, while native commerce fallbacks remain complete.
- Field performance becomes context loading and budgets, never stacked optimizer
  plugins.

### Opportunities become build lanes

1. **House section system:** Runway Rail, Collection Manifesto, Product Hotspot,
   Pre-Order Salon, Founder Film, and Verified 3D View.
2. **Four card modes:** Signature / The Flagship; Black Rose / The Beauty of
   Black; Love Hurts / Enchanted Rose; Kids / Heir to the Throne. Each mode may
   add one collection-specific premium interaction without changing commerce
   truth.
3. **Commerce state system:** product, cart, checkout, account, notices, empty,
   error, loading, and success states share design tokens and accessibility
   behavior.
4. **Curated editor layer:** expose house tokens and approved compositions to
   Gutenberg and supported builders without allowing product/SOT mutation.
5. **Performance preset:** load collection motion, 3D, film, and builder assets
   only on the routes that use them.

### Threats become fail-closed gates

- No generated or placeholder product image can enter a commerce card.
- No unverified GLB is rendered or packaged.
- No builder template silently replaces WooCommerce business state.
- No new WooCommerce override is accepted without structural justification,
  upstream version pinning, hook parity, and an installed-candidate test.
- No readiness claim is made from source checks or a local preview alone.

## Execution order

1. Package the exact clean commit and pin its digest as the next-install
   candidate.
2. Install and activate on staging; prove no fatal error and render home, shop,
   product, cart, checkout, account, and all collection routes.
3. Build commerce states and house sections against that executing baseline.
4. Run browser, keyboard, screen-reader, responsive, variation, coupon, tax,
   shipping, payment-sandbox, and order-state checks.
5. Run performance and visual/SOT gates on the same immutable candidate.

## Maintenance rule

At every WooCommerce update, compare these four files with the exact plugin
version installed on staging. Prefer moving customization to hooks whenever an
upstream hook can preserve the same flagship structure. Delete an override when
it no longer earns its maintenance cost.
