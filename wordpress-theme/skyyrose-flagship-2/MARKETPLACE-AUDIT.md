# Marketplace audit

## Verified in source

- The theme has a valid classic-theme stylesheet header, screenshot,
  GPL-2.0 license text, WooCommerce declarations, and version `2.3.3`.
- PHP syntax passes for all 20 bundled PHP files. JavaScript syntax passes for
  source, committed minified bundles, and the self-hosted 3D viewer runtime.
- Product 3D models fail closed: only manifest-approved, local, self-contained
  GLB v2 files under `assets/sot/3d/models/` can resolve. The resolver verifies
  path confinement, file size, GLB structure, SHA-256, five reference hashes,
  provenance, policy, founder approval, and a no-compression/no-external-URI
  profile before emitting a public URL.
- The product viewer has poster and no-JavaScript fallbacks, Save-Data and
  reduced-motion handling, keyboard-accessible controls, and no remote runtime
  fallback. No approved models are bundled yet, so viewer code is not enqueued
  for products until an asset passes the manifest gate.
- `/collections/` and the four approved collection routes are virtual theme
  routes. A versioned rewrite migration flushes rules once after an upgrade;
  unknown collection slugs remain 404 responses.
- Every local visual path referenced by PHP resolves to a bundled SOT or Scroll
  World asset. The installable archive is built from tracked files only by
  `scripts/package-theme.sh`.
- Public trust roots for founder, build attestor, and policy collector are
  configured in the repository's signed-evidence verifier.

## Hardened during closeout

- Removed arbitrary HTTPS model resolution and prohibited manifest-supplied
  public URLs.
- Replaced CDN model-viewer fallbacks with a pinned, self-hosted runtime and
  disabled unused remote decoder paths.
- Added mutation and external-URI rejection tests for the product GLB resolver.
- Added upgrade-safe rewrite migration and a virtual collections parent route.
- Rebuilt committed production CSS/JavaScript bundles with cached local tools;
  source and minified viewer bundles reproduce byte-for-byte.
- Added a zero-cost closeout auditor that reports `BLOCK`, `VERIFY`, and `DONE`
  without network or paid provider calls.

## Release verification still required

These are external release gates, not source-code blockers:

1. Install the exact generated archive on staging WordPress with WooCommerce
   and execute product, variable-product, cart, coupon, shipping, tax, payment
   gateway, and order-receipt journeys.
2. Run WordPress Theme Check, WPCS, and PHPStan when the declared development
   tooling is available.
3. Run browser accessibility, responsive, visual/SOT, and Lighthouse checks on
   desktop and mobile against the installed archive.
4. Complete the redistribution-rights ledger for every bundled font, image,
   video, vendor runtime, and brand element.
5. Produce and verify founder, build-attestor, and policy-collector signatures
   over the final release evidence and package digest.

## Scope

This is a portable WordPress/WooCommerce theme package. It can be installed on
compatible WordPress hosts; it is not executable on Shopify, a generic static
host, or a headless commerce platform without a separate frontend adapter.
