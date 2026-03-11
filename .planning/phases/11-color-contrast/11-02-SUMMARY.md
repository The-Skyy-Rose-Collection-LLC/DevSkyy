---
phase: 11-color-contrast
plan: 02
subsystem: ui
tags: [woocommerce, php, pre-order, price-display, accessibility]

# Dependency graph
requires:
  - phase: 10-accessibility-html-aria
    provides: "Finalized HTML structure for templates"
provides:
  - "WooCommerce price_html filter replacing $0.00 with Pre-Order label"
  - "Catalog fallback skyyrose_format_price handles zero-price pre-orders"
  - "WC product loop guards $0 pre-order prices from min/max range"
affects: [12-responsive-typography, deploy]

# Tech tracking
tech-stack:
  added: []
  patterns: ["WooCommerce price_html filter for pre-order products", "Defense-in-depth price display at both WC and catalog layers"]

key-files:
  created: []
  modified:
    - "wordpress-theme/skyyrose-flagship/inc/woocommerce.php"
    - "wordpress-theme/skyyrose-flagship/inc/product-catalog.php"
    - "wordpress-theme/skyyrose-flagship/template-parts/collection-page-v4.php"

key-decisions:
  - "Pre-order price handled at both WC filter and catalog fallback for defense-in-depth"
  - "CSS rebuild skipped -- plan 11-02 only modifies PHP files, not CSS; minified assets from 11-01 are current"

patterns-established:
  - "Pre-order price display: use woocommerce_get_price_html filter for WC path, skyyrose_format_price for catalog path"

requirements-completed: [CNTR-04]

# Metrics
duration: 2min
completed: 2026-03-11
---

# Phase 11 Plan 02: Pre-Order Price Display Summary

**WooCommerce price_html filter and catalog format_price updated to show "Pre-Order" instead of "$0.00" for pre-order products**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-11T16:51:24Z
- **Completed:** 2026-03-11T16:53:09Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- WooCommerce `woocommerce_get_price_html` filter intercepts $0 prices on pre-order products and displays "Pre-Order" (or "Pre-Order -- $XX" if custom pre-order price exists)
- Catalog fallback `skyyrose_format_price()` returns "Pre-Order" for pre-order products with zero or negative price
- WC product loop in collection-page-v4.php excludes $0 pre-order prices from min/max range calculation, preventing "$0 -- $95" display

## Task Commits

Each task was committed atomically:

1. **Task 1: Add WooCommerce price filter and update catalog price formatting** - `fda15a86` (feat)
2. **Task 2: Update WC product loop in collection template** - `bc73c255` (fix)

## Files Created/Modified
- `wordpress-theme/skyyrose-flagship/inc/woocommerce.php` - Added `skyyrose_preorder_price_html` filter function and `woocommerce_get_price_html` hook
- `wordpress-theme/skyyrose-flagship/inc/product-catalog.php` - Updated `skyyrose_format_price()` to handle zero-price pre-orders
- `wordpress-theme/skyyrose-flagship/template-parts/collection-page-v4.php` - Guarded WC loop min/max price tracking to skip $0 pre-order products

## Decisions Made
- Pre-order price display handled at both WC filter level and catalog fallback level for defense-in-depth -- either path alone would fix the issue, but both together ensure coverage regardless of which data source is active
- CSS rebuild skipped because this plan only modifies PHP files; minified CSS assets from plan 11-01 are already current

## Deviations from Plan

None - plan executed exactly as written (CSS rebuild was a no-op since no CSS files were modified in this plan).

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 11 (Color Contrast) is complete with both plans finished
- All WCAG AA contrast fixes and pre-order price display fixes are in place
- Ready for Phase 12 (Responsive & Typography)

## Self-Check: PASSED

All files exist, all commits verified (fda15a86, bc73c255).

---
*Phase: 11-color-contrast*
*Completed: 2026-03-11*
