---
phase: 10-accessibility-html-aria
plan: 01
subsystem: ui
tags: [accessibility, html, aria, wordpress, buttons, duplicate-ids, wp-enqueue]

# Dependency graph
requires:
  - phase: 09-theme-quality
    provides: WordPress theme structure and template files
provides:
  - Explicit type attributes on all 43 buttons across 12 theme files
  - Resolved wp_enqueue handle collision (CSS/JS no longer share handle)
  - Verified zero duplicate element IDs across all template parts
affects: [10-accessibility-html-aria, theme-review]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "All buttons must have explicit type attribute (type='button' or type='submit')"
    - "wp_enqueue handles must be unique across CSS and JS registrations"
    - "Template parts loaded in loops must not contain hardcoded static IDs"

key-files:
  created: []
  modified:
    - wordpress-theme/skyyrose-flagship/inc/accessibility-seo.php
    - wordpress-theme/skyyrose-flagship/template-love-hurts.php
    - wordpress-theme/skyyrose-flagship/skyyrose-canvas.php
    - wordpress-theme/skyyrose-flagship/template-collection-kids-capsule.php
    - wordpress-theme/skyyrose-flagship/template-style-quiz.php
    - wordpress-theme/skyyrose-flagship/front-page.php
    - wordpress-theme/skyyrose-flagship/woocommerce/single-product.php
    - wordpress-theme/skyyrose-flagship/inc/woocommerce.php
    - wordpress-theme/skyyrose-flagship/template-parts/collection-page-v4.php
    - wordpress-theme/skyyrose-flagship/template-parts/brand-ambassador.php
    - wordpress-theme/skyyrose-flagship/template-parts/mascot.php
    - wordpress-theme/skyyrose-flagship/template-parts/size-guide-modal.php

key-decisions:
  - "Renamed enqueue handles to skyyrose-a11y-css and skyyrose-a11y-js to resolve collision"
  - "Duplicate ID audit found no issues -- template parts use dynamic IDs or appear on separate page views"

patterns-established:
  - "Button type audit: grep for <button without type= before committing new templates"
  - "Enqueue handles: prefix with purpose (a11y-css, a11y-js) not shared names"

requirements-completed: [A11Y-01, A11Y-02, A11Y-08]

# Metrics
duration: 42min
completed: 2026-03-11
---

# Phase 10 Plan 01: Button Types & Duplicate IDs Summary

**Added explicit type attributes to 43 buttons across 12 theme files, fixed wp_enqueue handle collision, and verified zero duplicate element IDs**

## Performance

- **Duration:** 42 min
- **Started:** 2026-03-11T14:50:03Z
- **Completed:** 2026-03-11T15:32:09Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments
- Fixed enqueue handle collision where CSS and JS both used `'skyyrose-accessibility'`, causing WordPress to silently skip the JS enqueue
- Added `type="button"` to all 43 buttons missing explicit type attributes across 12 PHP template files, preventing unintended form submissions
- Audited all template parts for duplicate element IDs -- confirmed zero issues (loop templates use no static IDs, ARIA live regions hooked exactly once, nonce IDs only appear on separate page views)

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix enqueue collision + button type attributes** - `3371e9c3` (fix)
2. **Task 2: Duplicate ID audit** - No commit (audit passed with zero issues, no code changes required)

## Files Created/Modified
- `inc/accessibility-seo.php` - Renamed CSS handle to `skyyrose-a11y-css`, JS handle to `skyyrose-a11y-js`
- `template-love-hurts.php` - Added `type="button"` to 8 buttons (nav, audio, modal-close, add-to-cart, view-details)
- `skyyrose-canvas.php` - Added `type="button"` to 4 shop-tab buttons
- `template-collection-kids-capsule.php` - Added `type="button"` to 1 size-guide-trigger button
- `template-style-quiz.php` - Added `type="button"` to 4 buttons (quiz-start, share, download, retake)
- `front-page.php` - Added `type="button"` to 1 back-to-top button
- `woocommerce/single-product.php` - Added `type="button"` to 6 buttons (2 thumbnails, 4 accordion triggers)
- `inc/woocommerce.php` - Added `type="button"` to 1 view-3d-model button in sprintf output
- `template-parts/collection-page-v4.php` - Added `type="button"` to 6 buttons (size filter, size-guide, newsletter join, modal close/add/back)
- `template-parts/brand-ambassador.php` - Added `type="button"` to 3 buttons (fab, greeting-close, close)
- `template-parts/mascot.php` - Added `type="button"` to 4 buttons (character, panel-close, recall, minimize)
- `template-parts/size-guide-modal.php` - Added `type="button"` to 5 buttons (3 tabs, 2 unit toggles)

## Decisions Made
- Renamed enqueue handles to `skyyrose-a11y-css` and `skyyrose-a11y-js` rather than renaming just one, ensuring both handles clearly indicate their purpose
- Determined that `skyyrose_newsletter_nonce` ID appearing in multiple template files is not a duplicate ID issue because those templates are separate page views that never load simultaneously

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Tab vs space indentation mismatches when editing template files required careful whitespace matching with the Edit tool
- macOS `cat -A` unavailable; used `od -c` to inspect exact whitespace characters in files

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All button type attributes are in place for WCAG compliance
- Enqueue handles are unique and both CSS/JS load correctly
- Ready for Plan 02 (ARIA attributes and landmark audit)

## Self-Check: PASSED

All files verified present. Commit `3371e9c3` confirmed in git log. All 12 modified PHP files exist on disk.

---
*Phase: 10-accessibility-html-aria*
*Completed: 2026-03-11*
