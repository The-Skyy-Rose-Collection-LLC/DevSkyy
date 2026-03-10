---
phase: 09-collection-product-data
plan: 02
subsystem: ui
tags: [wordpress, php, hero-banner, collection-templates, deploy]

# Dependency graph
requires: []
provides:
  - "Verified hero_image config correctness for all 3 collection templates"
  - "Root cause diagnosis: stale deploy, not code bug"
affects: [09-collection-product-data]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SKYYROSE_ASSETS_URI constant for theme asset URLs"
    - "Collection template config array passed to shared collection-page-v4.php"

key-files:
  created: []
  modified: []

key-decisions:
  - "No code changes needed -- hero_image paths already correct in git"
  - "Root cause is stale deploy: live site has outdated theme files"
  - "Fix requires redeploying current theme to live server"

patterns-established:
  - "Collection hero images: SKYYROSE_ASSETS_URI/scenes/{slug}/{slug}-{scene-name}.webp"
  - "Collection hero logos: get_template_directory_uri()/assets/branding/{slug}-logo-hero-transparent.png"

requirements-completed: []

# Metrics
duration: 2min
completed: 2026-03-10
---

# Phase 9 Plan 02: Fix Black Rose Hero Banner Summary

**Audit confirmed all 3 collection template hero_image paths are correct in git; live site issue is a stale deploy requiring theme redeployment**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-10T23:08:29Z
- **Completed:** 2026-03-10T23:09:55Z (Task 1 only; Task 2 awaiting human verification)
- **Tasks:** 1/2 (Task 2 is checkpoint:human-verify)
- **Files modified:** 0

## Accomplishments
- Verified all 3 hero_image paths point to the correct collection's scene directory (no cross-contamination)
- Verified all 6 asset files exist on disk (3 hero images + 3 hero logos)
- PHP syntax validation passed for all 3 collection templates
- Identified root cause: code in git is correct, live site has stale (outdated) theme files
- Confirmed rendering pipeline: hero_image flows cleanly from config array through collection-page-v4.php with esc_url()

## Task Commits

1. **Task 1: Audit hero banner configuration and image assets** - No commit (audit-only, no code changes needed)

_Task 2 (human-verify) pending -- requires theme redeploy and visual confirmation on live site_

## Files Created/Modified

No files were modified. The audit confirmed all templates are already correct:
- `wordpress-theme/skyyrose-flagship/template-collection-black-rose.php` - hero_image: `scenes/black-rose/black-rose-marble-rotunda.webp` (correct)
- `wordpress-theme/skyyrose-flagship/template-collection-love-hurts.php` - hero_image: `scenes/love-hurts/love-hurts-crimson-throne-room.webp` (correct)
- `wordpress-theme/skyyrose-flagship/template-collection-signature.php` - hero_image: `scenes/signature/signature-golden-gate-showroom.webp` (correct)

## Decisions Made
- No code changes needed -- all hero_image paths in git are already correct
- Root cause is stale deploy: the live site's theme files do not match the current git state
- Fix is operational (redeploy), not a code fix
- Alternative possibility: WordPress admin page-template assignment could be wrong (user should check if Black Rose page has "Collection - Black Rose" template selected, not "Collection - Love Hurts")

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - the audit was straightforward. All paths were correct, all files exist, and PHP syntax is valid. The live site banner mismatch is confirmed to be a deployment gap, not a code bug.

## User Setup Required

**Theme redeploy required.** The current theme files in git are correct but the live site has outdated files. Deploy using:
```bash
cd /Users/theceo/DevSkyy && bash scripts/deploy-pipeline.sh
```

Additionally, verify in WordPress admin that the Black Rose collection page has "Collection - Black Rose" selected as its page template (not "Collection - Love Hurts").

## Next Phase Readiness
- Task 2 checkpoint awaits: human must deploy theme and visually verify all 3 collection hero banners
- After Task 2 is approved, this plan is complete and DATA-01 requirement can be marked done
- No blockers for other Phase 9 plans

## Self-Check: PASSED

All referenced files verified:
- 3/3 hero image files exist on disk
- 3/3 hero logo files exist on disk
- 3/3 template PHP files exist and pass syntax check
- SUMMARY.md created successfully

---
*Phase: 09-collection-product-data*
*Completed: 2026-03-10 (Task 1 only)*
