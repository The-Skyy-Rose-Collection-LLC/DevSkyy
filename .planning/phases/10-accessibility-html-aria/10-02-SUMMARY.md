---
phase: 10-accessibility-html-aria
plan: "02"
subsystem: testing
tags: [scrapling, post-deploy, a11y, accessibility, verify_live_structure, requirements, roadmap]

requires:
  - phase: 10-accessibility-html-aria
    provides: v1.1 accessibility fixes (inc/accessibility-fix.php) and plan 10-01 regression suite

provides:
  - A11Y_ASSERTIONS tuple (3 selectors) added to GLOBAL_ASSERTIONS in scripts/verify_live_structure.py
  - All 9 A11Y requirements formally closed in REQUIREMENTS.md with commit references
  - ROADMAP.md Phase 10 plan-list updated from Fix to Verify language, both plans marked [x]

affects: [deploy-gate, post-deploy-verification, roadmap-phase-status]

tech-stack:
  added: []
  patterns:
    - Separate _STRUCTURAL_ASSERTIONS + A11Y_ASSERTIONS tuples concatenated into GLOBAL_ASSERTIONS (extensible constant pattern)
    - A11Y selectors use CSS attribute selectors compatible with Scrapling (no BeautifulSoup)

key-files:
  created: []
  modified:
    - scripts/verify_live_structure.py (A11Y_ASSERTIONS constant + GLOBAL_ASSERTIONS extension)
    - .planning/REQUIREMENTS.md (commit references appended to A11Y-01..09)
    - .planning/ROADMAP.md (Phase 10 plan-list: [ ] -> [x], Fix -> Verify language)

key-decisions:
  - "A11Y_ASSERTIONS uses three selectors: [tabindex='-1'] (A11Y-05), a.skip-link (A11Y-07), img[loading='lazy'] (A11Y-09) — structural ones (A11Y-01/02/08) deferred to unit tests per plan spec"
  - "Split _STRUCTURAL_ASSERTIONS from A11Y_ASSERTIONS for clarity and independent extensibility; both concat into GLOBAL_ASSERTIONS"
  - "Structural assertions (A11Y-01/02/08) remain in unit test suite not post-deploy gate — selector-level detection of button types and ID uniqueness is too fragile over live fetches"
  - "REQUIREMENTS.md lines annotated with search input gap note (A11Y-06) and transitive-coverage note (A11Y-08) to preserve intent"

requirements-completed: [A11Y-01, A11Y-02, A11Y-03, A11Y-04, A11Y-05, A11Y-06, A11Y-07, A11Y-08, A11Y-09]

duration: 15min
completed: 2026-05-12
---

# Phase 10 Plan 02: A11Y Post-Deploy Gate + Requirements Closure Summary

**Three A11Y CSS selector assertions added to verify_live_structure.py GLOBAL_ASSERTIONS; all 9 A11Y requirements formally closed with v1.1 commit references**

## Performance

- **Duration:** ~15 min
- **Completed:** 2026-05-12
- **Tasks:** 2 (verify_live_structure.py extension + REQUIREMENTS.md / ROADMAP.md updates)
- **Files modified:** 3

## Accomplishments

- Extended `GLOBAL_ASSERTIONS` with `A11Y_ASSERTIONS` (A11Y-05 tabindex, A11Y-07 skip-link, A11Y-09 lazy img)
- Post-deploy gate now validates A11Y assertions on every page in `--all` mode
- All 9 A11Y requirements in REQUIREMENTS.md annotated with commit references (923455187 + dfc4e1e94 + 8ad0df313)
- ROADMAP.md Phase 10 plan-list updated from Fix language to Verify language; both plans marked [x]

## Task Commits

1. **Task 1: A11Y assertions in verify_live_structure.py** - `de463e3c7` (feat: add A11Y post-deploy assertions to verify_live_structure.py)
2. **Task 2: Close requirements + fix roadmap** - `a285ceeaf` (docs: close A11Y-01..09 requirements; fix roadmap plan-list)

## Files Modified

- `/Users/theceo/DevSkyy/scripts/verify_live_structure.py` — `A11Y_ASSERTIONS` constant + `GLOBAL_ASSERTIONS` extended; `_STRUCTURAL_ASSERTIONS` renamed from previous inline tuple
- `/Users/theceo/DevSkyy/.planning/REQUIREMENTS.md` — commit refs appended to A11Y-01..09; gap notes for A11Y-06 and A11Y-08
- `/Users/theceo/DevSkyy/.planning/ROADMAP.md` — Phase 10 plans: `[ ]`→`[x]`, Fix→Verify language

## Decisions Made

- A11Y-05, A11Y-07, A11Y-09 chosen for post-deploy gate (observable via Scrapling CSS selectors on a live fetch)
- A11Y-01/02/08 stay in unit test suite — detecting button types and ID uniqueness over a live network fetch with cache-busting is less reliable than static fixture assertions
- Scrapling CSS selectors chosen (not bs4): `[tabindex='-1']`, `a.skip-link`, `img[loading='lazy']` — all standard CSS attribute selectors Scrapling supports

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Issues Encountered

None.

## Next Phase Readiness

- Post-deploy gate now covers A11Y-05, A11Y-07, A11Y-09 in addition to the structural regression beacon
- Phase 11 (Color Contrast) can proceed with this gate active
- If Phase 9 template regression is fixed, test_a11y_02_08_shop xfail in 10-01 suite should be re-evaluated

---
*Phase: 10-accessibility-html-aria*
*Completed: 2026-05-12*
