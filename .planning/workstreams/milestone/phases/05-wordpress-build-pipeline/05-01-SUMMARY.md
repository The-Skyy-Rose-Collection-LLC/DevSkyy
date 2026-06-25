---
phase: 05-wordpress-build-pipeline
plan: 01
subsystem: infra
tags: [webpack, clean-css, source-maps, minification, wordpress-theme, glob]

# Dependency graph
requires:
  - phase: 02-husky-foundation
    provides: npm install and husky prepare hook in theme directory
provides:
  - Dynamic JS minification via webpack with glob.sync auto-discovery (43 files)
  - Programmatic CSS minification via clean-css with recursive glob (56 files)
  - Source map generation for all minified assets (99 .map files)
  - Build verification script (7 automated checks) reusable by CI
  - Single `npm run build` command producing all .min.js, .min.css, and .map files
affects: [06-ci-build-gate, 07-deploy-pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns: [glob.sync dynamic entry discovery, programmatic clean-css with header preservation, IIFE-wrapped webpack output]

key-files:
  created:
    - wordpress-theme/skyyrose-flagship/scripts/build-css.js
    - wordpress-theme/skyyrose-flagship/scripts/verify-build.sh
  modified:
    - wordpress-theme/skyyrose-flagship/webpack.config.js
    - wordpress-theme/skyyrose-flagship/package.json
    - wordpress-theme/skyyrose-flagship/.gitignore

key-decisions:
  - "glob.sync auto-discovery for webpack entries eliminates manual maintenance of entry list"
  - "Programmatic clean-css API over CLI for recursive file discovery and source map control"
  - "WordPress theme header preserved via extract-and-prepend (style.css uses /* not /*!)"
  - "IIFE output wrapping for browser-safe global scripts (window.SkyyRose patterns)"

patterns-established:
  - "Dynamic entry discovery: glob.sync ignoring *.min.js for zero-maintenance webpack config"
  - "CSS build script: Node.js programmatic approach with clean-css for file discovery and source maps"
  - "Build verification: Shell script with PASS/FAIL checks reusable in CI pipelines"

requirements-completed: [BUILD-01, BUILD-02, BUILD-03, BUILD-04]

# Metrics
duration: 3min
completed: 2026-03-09
---

# Phase 5 Plan 01: WordPress Build Pipeline Summary

**Dynamic webpack + clean-css build pipeline auto-discovering and minifying all 43 JS and 56 CSS files with source maps via single `npm run build` command**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-09T15:19:23Z
- **Completed:** 2026-03-09T15:22:07Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Replaced broken webpack config (6 hardcoded entries, 3 referencing non-existent files) with glob.sync auto-discovery covering all 43 JS source files
- Created programmatic CSS build script processing all 56 CSS files (55 in assets/css/ + root style.css) with source maps, preserving WordPress theme header
- Generated 99 source map files (43 JS + 55 CSS + 1 root) for development debugging
- Created 7-check build verification script validating count matches, source map pairing, header preservation, and size sanity

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite webpack config with dynamic entry discovery and create CSS build script** - `58239fde` (feat)
2. **Task 2: Create build verification script and validate complete output** - `a1b71543` (feat)

**Plan metadata:** (pending) (docs: complete plan)

## Files Created/Modified
- `wordpress-theme/skyyrose-flagship/webpack.config.js` - Rewritten with glob.sync dynamic JS entry discovery, IIFE output, source maps
- `wordpress-theme/skyyrose-flagship/scripts/build-css.js` - New programmatic CSS minification script with recursive discovery and header preservation
- `wordpress-theme/skyyrose-flagship/scripts/verify-build.sh` - New 7-check build verification script (executable)
- `wordpress-theme/skyyrose-flagship/package.json` - Updated build:css script to use programmatic build
- `wordpress-theme/skyyrose-flagship/.gitignore` - Added recursive un-ignore rules for .min files in subdirectories

## Decisions Made
- Used glob.sync auto-discovery for webpack entries to eliminate manual maintenance of entry list (the root cause of the 3 broken entries)
- Chose programmatic clean-css API over CLI for recursive file discovery and source map generation
- Preserved WordPress theme header via extract-and-prepend strategy because style.css uses `/*` not `/*!` (clean-css only auto-preserves `/*!` comments)
- Set webpack output.iife: true because these are vanilla browser scripts setting globals like window.SkyyRose, not ES modules

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tools (webpack 5.105, clean-css 5.3.3, glob) were pre-installed and worked as expected on first run.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Build pipeline fully operational: `npm run build` produces all .min.js, .min.css, and .map files
- `scripts/verify-build.sh` ready for CI integration in Phase 6
- Existing minified files will show diffs from prior generation (different minifier settings) -- expected per STATE.md blocker note

## Self-Check: PASSED

All 5 created/modified files verified on disk. Both task commits (58239fde, a1b71543) verified in git log.

---
*Phase: 05-wordpress-build-pipeline*
*Completed: 2026-03-09*
