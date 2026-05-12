---
phase: 13
plan: "01"
subsystem: wordpress-theme
tags: [cursor, testing, regression-gate, curs-01, curs-03]
dependency_graph:
  requires: [inc/enqueue.php, assets/css/luxury-cursor.css]
  provides: [tests/test_luxury_cursor.py]
  affects: [REQUIREMENTS.md, ROADMAP.md]
tech_stack:
  added: [pytest (static file analysis)]
  patterns: [brace-depth PHP function body extraction, intentional failing test as gap report]
key_files:
  created: [tests/test_luxury_cursor.py]
  modified: []
decisions:
  - "Use pytest.fail() not xfail for CURS-03 — fail must be visible in CI, not masked"
  - "brace-depth counter chosen over regex for PHP function body extraction (handles nested braces correctly)"
  - "Place test at tests/ root not tests/unit/ so pre-commit (tests/unit/ only) is not blocked by intentional CURS-03 failure"
metrics:
  duration: "~10 min"
  completed: "2026-05-12"
  tasks_completed: 1
  files_created: 1
---

# Phase 13 Plan 01: Luxury Cursor Regression Gate Summary

**One-liner:** pytest static-analysis gate confirming CURS-01 z-index=99999 (PASS) and surfacing CURS-03 immersive exclusion gap (intentional FAIL).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write tests/test_luxury_cursor.py | 818868654 | tests/test_luxury_cursor.py |

## Test Results

```
tests/test_luxury_cursor.py ..F                    [100%]

PASSED  test_cursor_zindex_above_modals        — CURS-01 confirmed: z-index 99999 > 9999
PASSED  test_cursor_css_enqueued_globally      — sanity: CSS in global_styles()
FAILED  test_cursor_not_loaded_on_immersive    — CURS-03 GAP: unconditional enqueue in global_scripts()
```

## CURS-03 Gap Confirmed

`luxury-cursor.min.js` is enqueued in `skyyrose_enqueue_global_scripts()` (inc/enqueue.php lines 249–259) with no slug check. On immersive templates (`template-immersive-*.php`, slug=`'immersive'`), the cursor JS loads and conflicts with the Three.js/WebGL scene.

**Fix path (future phase, requires STOP-AND-SHOW + deploy):** Move `wp_enqueue_script('skyyrose-luxury-cursor', ...)` into `skyyrose_enqueue_template_scripts()` behind `if ($slug !== 'immersive') { ... }`.

## Deviations from Plan

None — plan executed exactly as written. Test structure, helper function design, and expected pass/fail results all match spec.

## Self-Check: PASSED

- [x] `tests/test_luxury_cursor.py` exists at commit 818868654
- [x] pytest confirms 2 PASSED / 1 FAILED
- [x] CURS-03 failure message includes exact fix path
