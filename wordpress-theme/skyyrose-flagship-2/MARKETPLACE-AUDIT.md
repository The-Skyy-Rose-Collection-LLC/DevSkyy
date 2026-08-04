# Marketplace audit

## Verified

- The theme has a valid classic-theme stylesheet header, a screenshot, GPL-2.0
  license text, and WooCommerce support declarations.
- PHP syntax passed for all 11 PHP files.
- JavaScript syntax passed for both source and committed minified JavaScript
  files.
- Every local visual path referenced by PHP resolves to a bundled SOT or
  Scroll World asset.
- The installable archive is built only from tracked files by
  `scripts/package-theme.sh`.

## Corrected during audit

- The missing Black Rose hero reference now resolves to the bundled approved
  Black Rose scene.
- `SCRIPT_DEBUG` no longer requests a missing mascot source stylesheet; it
  safely uses the committed minified asset until a maintainable source file is
  supplied.
- Committed `.min.css` and `.min.js` assets are explicitly exempted from the
  repository's general generated-file ignore rules.
- An unused duplicate mascot bundle was removed.

## Release gates still open

1. Install the generated archive on staging WordPress with WooCommerce and
   execute product, variable-product, cart, coupon, shipping, tax, Stripe
   gateway, and order-receipt journeys.
2. Run WPCS and PHPStan after installing the declared development tooling.
3. Run browser accessibility and responsive checks on desktop and mobile.
4. Confirm redistribution rights for every bundled font, image, video, and
   brand element before offering a third-party marketplace download.
5. Provide the mascot stylesheet source and reproducible minification step if
   downstream purchasers must customize that component.

## Scope

This is a portable WordPress/WooCommerce theme package. It can be installed on
compatible WordPress hosts; it is not executable on Shopify, a generic static
host, or a headless commerce platform without a separate frontend adapter.
