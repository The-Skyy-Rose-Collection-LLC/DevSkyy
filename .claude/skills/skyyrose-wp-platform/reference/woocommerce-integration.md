# WooCommerce Integration — Selling Four Collections, Not a Generic Catalog

Every product that reaches skyyrose.co represents a real, founder-approved SKU across
Signature, Black Rose, Love Hurts, or Kids Capsule — this file exists so the WooCommerce
plumbing never becomes the thing that lets a wrong or invented product slip past that. It
replaces what `wp-rest-api`, `woocommerce`, `woocommerce-backend-dev`,
`woocommerce-code-review`, and `woocommerce-webhooks` covered as generic API mechanics.
`wc-pdp-correctness` stays a standalone deep-dive for PDP-specific work; this file is the
stack-specific entry point that routes you there.

## The one rule that matters more than any API detail

**The catalog CSV (`skyyrose-catalog.csv` + per-SKU dossiers, registered in root `SOT.md`) is
the source of truth. The live WooCommerce store conforms to the CSV, never the reverse.**
Never create a WooCommerce product that doesn't already exist in the catalog CSV. This is the
same "real products only" discipline that governs imagery on this project (no hallucinated,
never-made renders) applied to the store's product data — a phantom product in WooCommerce is
the same class of failure as a phantom render, just on the commerce side instead of the visual
side. It has been violated before (catalog/store drift incidents) and cost real cleanup time —
don't re-derive this the hard way.

## Auth and connectivity

- Keys live in `.env.wordpress` (never hardcoded, never committed).
- WooCommerce REST v3 uses BasicAuth — `index.php?rest_route=/wc/v3/...` per this project's
  REST convention (see `build-and-templates.md`); a bare `/wp-json/wc/v3` path 401s on this
  WordPress.com hosting setup.
- Webhook signature verification is HMAC SHA256 — verify the signature before trusting any
  inbound webhook payload, no exceptions for "it's probably fine, it's our own site."

## Where this touches the Python backend

- `integrations/wordpress_com_client.py` — WordPress.com API client
- `integrations/wordpress_product_sync.py` — catalog → WooCommerce sync logic
- `database/seed_catalog.py` — Python-side DB mirror of the catalog
- `api/v1/wordpress_integration.py` — webhook sync-back endpoint

A catalog/schema-mapping task touches CSV field ↔ PHP field (`inc/product-catalog.php`) ↔
WooCommerce field — three representations of the same product, not one. Changing one without
checking the other two is how drift happens.

## Product imagery — do not resolve this yourself

Product imagery resolves **only** via `data/sot-images.json` / `skyyrose.core.sot_images`
(front-first). Never invent an image path from a filename pattern or a WooCommerce media ID
alone — this is a locked project rule, not a style preference, because filename/manifest
mismatches have shipped wrong-garment imagery before.

## Domain-specific verification

- **A catalog claim is true** → read the CSV + dossier directly, not memory of a prior
  session's catalog state — the CSV changes over time and memory rots.
- **A live product's actual state** → a real WooCommerce REST v3 GET against the live store
  (BasicAuth via `.env.wordpress`), not an assumption from the CSV alone — CSV is what
  *should* be true, REST is what *is* live right now. A sync bug means these can disagree.
  A stage-review reconcile pattern already exists for exactly this cross-check (WC × CSV ×
  render/stage/approve) — use it rather than hand-rolling a new comparison.
- **A webhook payload is legitimate** → the HMAC SHA256 signature check passing, not merely
  "the request hit our endpoint."
- **Product imagery is the correct garment for its SKU** → read the actual pixels (vision),
  not the filename or manifest — this is a MANDATORY gate before any product image touches
  skyyrose.co, per this project's standing rule; wrong-garment imagery is the most-repeated
  defect class on this project.
