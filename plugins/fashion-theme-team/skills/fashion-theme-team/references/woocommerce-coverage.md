# WooCommerce Coverage

## Compatibility and architecture

Declare marketplace, WordPress/WooCommerce/PHP versions, HPOS support, classic
and block coverage, browser matrix, payment/shipping dependencies, and optional
extension behavior. Prefer hooks. Inventory overrides with upstream versions and
hooks with callback, priority, arguments, conditions, and owner.

## Required state matrices

- Products: simple, variable, grouped, external, virtual, downloadable, unknown extension types.
- Inventory: in stock, out, backorder, managed stock, sold individually, restricted.
- Pricing: regular, sale, scheduled sale, zero, tax display, unavailable price.
- Catalog: archives, categories, tags, search, filters, sort, pagination, sparse/dense, missing optional media.
- Cart/checkout: empty/populated, quantities, coupons, shipping, tax, guest/auth,
  validation, payment failure recovery, session persistence, confirmation.
- Account/orders: login, registration, reset, dashboard, orders, downloads,
  addresses, payment methods, endpoints, guest lookup, authorization failures,
  cancelled, failed, and refunded orders.

## Engineering rules

Preserve fragments and block behavior. Load assets conditionally through
WordPress APIs. Settings have sanitizers, capabilities, defaults, migration, and
invalid-value recovery. Use context escaping, validated persistence, nonces,
capability/ownership checks, safe CRUD/prepared access, REST/AJAX permissions,
safe redirects/uploads, direct-access guards, and customer/order/session privacy.

Tests cover hooks, sanitizers, permissions, helpers, product/order/account
states, missing WooCommerce, malformed settings, absent optional plugins,
override versions, markup accessibility, and every fixed defect.
