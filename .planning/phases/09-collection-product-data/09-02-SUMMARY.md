---
phase: "09"
plan: "02"
subsystem: deploy-verification
tags: [verify-live, DATA-01, scrapling, hero-banner, regression-gate]
dependency_graph:
  requires: [scripts/verify_live_structure.py, inc/collection-content.php, assets/branding/sr-collection-black-rose.webp]
  provides: [COLLECTION_HERO_ASSETS, extended collection_assertions()]
  affects: [all 4 collection page verification runs]
tech_stack:
  added: []
  patterns: [CSS attribute substring selector img[src*='...'], COLLECTION_HERO_ASSETS dict, tuple concatenation for optional assertions]
key_files:
  created: []
  modified: [scripts/verify_live_structure.py, .planning/ROADMAP.md]
decisions:
  - "Added COLLECTION_HERO_ASSETS dict for all 4 collections — extensible pattern, not just BR"
  - "Used tuple concatenation (base_assertions + hero_tuple) over inserting mid-tuple — cleaner separation"
  - "DATA-01 checkbox NOT closed — live verification failed (pre-existing collection page regression, not today's code)"
  - "ROADMAP plan checkboxes marked [x] — both plans executed, regression is pre-existing site issue"
metrics:
  duration: "~8 minutes"
  completed: "2026-05-12"
  tasks_completed: 2
  tasks_total: 2
  files_changed: 2
---

# Phase 9 Plan 02: DATA-01 Live Verification + Checkpoint Closure Summary

Extended `scripts/verify_live_structure.py` with hero image assertions for all 4 collections using `img[src*='filename']` CSS attribute substring selectors. Live verification run against skyyrose.co revealed pre-existing collection page regression.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Extend verify_live_structure.py with hero asset assertions | `a598ef359` | scripts/verify_live_structure.py |
| 2 | Update ROADMAP.md plan checkboxes | (included in final metadata commit) | .planning/ROADMAP.md |

## Verification Results

```
$ python scripts/verify_live_structure.py --page black-rose

[PASS] no skyyrose render-error markers
[FAIL] <div class='col-page' data-collection='black-rose'>  (found=0, min=1)
[FAIL] <section class='col-hero'>  (found=0, min=1)
[FAIL] >= 12 <.holo> product cards  (found=8, min=12)
[FAIL] >= 12 <.holo--black-rose> cards  (found=0, min=12)
[PASS] theme CSS enqueued (skyyrose-flagship active)
[FAIL] hero <img src> contains sr-collection-black-rose.webp (DATA-01)  (found=0, min=1)

Result: 0/1 pages passed — exit code 2
```

Same pattern confirmed on signature collection (pre-existing, not today's regression).

## Deviations from Plan

### Pre-existing Live Regression Discovered

**[Deviation - Blocked]** DATA-01 checkbox NOT closed per plan instruction.

- **Found during:** Task 2 (live verification step)
- **Issue:** Live collection pages return 200 but collection-specific markup is absent (`col-page`, `col-hero`, `holo--{slug}` selectors all `found=0`). The hero assertion `img[src*='sr-collection-black-rose.webp']` also returns 0. This is NOT caused by today's changes — we made no PHP/theme changes.
- **Scope:** Affects all 4 collection pages. `col-page`/`col-hero` DOM structure missing from live HTML despite HTTP 200. Pre-existing issue (known: kids-capsule also failed similarly in prior session, obs #2589/#2667).
- **Action per plan:** STOP. Do not run deploy-theme.sh. Document and hand back with diagnostics.
- **DATA-01 status:** Remains `[ ]` in REQUIREMENTS.md — cannot be closed until live assertion passes.
- **ROADMAP checkboxes:** Marked `[x]` — plans executed correctly; regression is site-side, not plan-side.

## Live Regression Diagnostic

The live Black Rose page returns HTTP 200 with 8 holo cards visible, but:
- `div.col-page[data-collection='black-rose']` = 0 found
- `section.col-hero` = 0 found
- `div.holo--black-rose` = 0 found (collection-specific CSS class missing)

Likely cause: collection template is not being served (possibly serving shop/archive template instead), or CDN is serving a stale render that predates the collection template. The theme CSS IS enqueued (23 links found) so WordPress/theme loaded correctly.

**Action needed:** Verify which template is serving `/collection-black-rose/` via WordPress debug or curl+grep for `col-page` class in raw HTML.

## Known Stubs

None.

## Threat Flags

None — read-only HTTP verification, no writes to production.

## Self-Check: PASSED (for completed code tasks)

- `scripts/verify_live_structure.py`: COLLECTION_HERO_ASSETS dict + extended collection_assertions() — EXISTS
- Commit `a598ef359`: EXISTS
- `.planning/ROADMAP.md`: both plan checkboxes `[x]` — VERIFIED
- DATA-01 in REQUIREMENTS.md: remains `[ ]` — CORRECT (live check failed)
