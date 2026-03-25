---
phase: 03-pre-commit-hook-checks
plan: 01
subsystem: infra
tags: [lint-staged, pre-commit, eslint, ruff, black, isort, mypy, tsc, php-lint, pytest]

# Dependency graph
requires:
  - phase: 02-husky-foundation
    provides: Husky v9 initialized with proof-of-life pre-commit hook
provides:
  - lint-staged.config.mjs routing 4 file types to lint/type/syntax tools
  - scripts/php-lint.sh wrapper for php -l per-file execution
  - Pre-commit hook calling lint-staged + conditional mypy + conditional pytest
affects: [03-02-verification, 04-pr-branch-protection]

# Tech tracking
tech-stack:
  added: [lint-staged v16.2.7 (already in devDeps, now configured)]
  patterns: [lint-staged function syntax for whole-project tools (tsc), conditional hook execution via git diff --cached grep]

key-files:
  created:
    - lint-staged.config.mjs
    - scripts/php-lint.sh
  modified:
    - .husky/pre-commit

key-decisions:
  - "ESLint scoped to frontend/** only (root .eslintrc.cjs + ESLint v9 = ajv crash)"
  - "tsc uses function syntax () => to prevent lint-staged file arg appending"
  - "ESLint runs without --max-warnings 0 (242 existing warnings would block every commit)"
  - "mypy and pytest run from pre-commit hook directly, not lint-staged (JS duplicate key limitation)"
  - "pytest scoped to tests/unit/ only (~2s) -- full suite (2379 tests) too slow for pre-commit"

patterns-established:
  - "lint-staged function syntax for whole-project tools: () => 'command' prevents file path appending"
  - "Conditional hook execution: git diff --cached --name-only --diff-filter=ACMR | grep pattern"
  - "PHP lint wrapper loops over file args (php -l only accepts one file at a time)"

requirements-completed: [HOOK-01, HOOK-02, HOOK-03, HOOK-04, HOOK-05, HOOK-06]

# Metrics
duration: 2min
completed: 2026-03-09
---

# Phase 3 Plan 1: Pre-commit Hook Checks Summary

**lint-staged config routing Python/JS/TS/PHP to ruff+black+isort/eslint/tsc/php-l, with conditional mypy and pytest for Python commits**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-09T03:34:36Z
- **Completed:** 2026-03-09T03:36:10Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created lint-staged.config.mjs with 4 glob patterns routing staged files to their respective lint/type/syntax tools
- Created scripts/php-lint.sh wrapper that loops over file arguments calling php -l per file
- Replaced proof-of-life echo in .husky/pre-commit with real lint-staged orchestration plus conditional mypy and pytest

## Task Commits

Each task was committed atomically:

1. **Task 1: Create lint-staged config and PHP lint wrapper** - `23c19d09` (feat)
2. **Task 2: Replace proof-of-life pre-commit hook with real checks** - `242c14a7` (feat)

## Files Created/Modified
- `lint-staged.config.mjs` - lint-staged configuration with 4 glob patterns (Python, frontend JS/TS, frontend TS type-check, PHP)
- `scripts/php-lint.sh` - PHP syntax check wrapper looping over files with php -l
- `.husky/pre-commit` - Real pre-commit hook: lint-staged + conditional mypy + conditional pytest

## Decisions Made
- ESLint scoped to `frontend/**` only because root `.eslintrc.cjs` + ESLint v9 causes ajv crash (matches CI behavior, per research Option 2)
- tsc uses function syntax `() =>` to prevent lint-staged from appending file paths (which would cause tsc to ignore tsconfig.json)
- ESLint runs without `--max-warnings 0` because there are 242 existing warnings -- plain `eslint` exits non-zero on errors only
- mypy and pytest run from the pre-commit hook directly instead of lint-staged (JS object keys must be unique, can't have multiple `'*.py'` entries)
- pytest scoped to `tests/unit/` only (~2s, 9 tests) -- full suite (2379 tests) too slow for pre-commit

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 6 tool types are wired into the pre-commit hook (ESLint, ruff/black/isort, tsc, mypy, php -l, pytest)
- Plan 03-02 can now create end-to-end verification scripts to validate all HOOK requirements
- HOOK-08 (30-second timing requirement) will be validated in Plan 03-02

## Self-Check: PASSED

All created files verified present on disk. Both task commits (23c19d09, 242c14a7) verified in git log.

---
*Phase: 03-pre-commit-hook-checks*
*Completed: 2026-03-09*
