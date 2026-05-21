---
phase: 11-color-contrast
plan: "01"
subsystem: qa/contrast
tags: [wcag, contrast, regression-gate, pricing, a11y]
dependency_graph:
  requires: [10-a11y-final]
  provides: [wcag-regression-gate, cntr-04-pricing-check]
  affects: [tests/, scripts/verify_live_structure.py]
tech_stack:
  added: []
  patterns: [inline-wcag-helpers, balanced-brace-css-parser, PricingCheck-dataclass]
key_files:
  created:
    - tests/test_color_contrast_wcag.py
  modified:
    - scripts/verify_live_structure.py
decisions:
  - "Multiple :root blocks in design-tokens.css require balanced-brace parser not simple regex"
  - "PricingCheck separate from Assertion — CSS has no :contains(), text content needs iteration"
  - "PRICING_CHECKS outside GLOBAL_ASSERTIONS — pricing check is text-content, not element-count"
metrics:
  duration: "~30 minutes"
  completed: "2026-05-12T22:08:49Z"
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_modified: 1
---

# Phase 11 Plan 01: WCAG AA Regression Gate + CNTR-04 Pricing Assertion Summary

**One-liner:** Pure-Python WCAG contrast regression test parsing design-tokens.css + live-page $0-price assertion via PricingCheck dataclass in verify_live_structure.py.

## Tasks Completed

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 1 | Create tests/test_color_contrast_wcag.py | 63e4f9ce1 | tests/test_color_contrast_wcag.py |
| 2 | Add CNTR-04 pricing check to verify_live_structure.py | 63e4f9ce1 | scripts/verify_live_structure.py |

## Verification

```
pytest tests/test_color_contrast_wcag.py -v
6 passed in 0.36s
```

All 6 tests:
- `test_tokens_css_exists` — PASS
- `test_wcag_helper_known_pair` — PASS (21.0:1 black on white)
- `test_wcag_ratio_order_independent` — PASS
- `test_text_muted_blend` — PASS (blended ~#AFA497, ratio >> 4.5:1)
- `test_root_text_bg_meets_wcag_aa` — PASS (#F5E6D3 on #0A0A0A >= 15.0:1 floor)
- `test_all_collections_inherit_root_text_bg` — PASS (all 4 collections inherit root tokens)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Balanced-brace parser required for multiple :root blocks**
- **Found during:** Task 1 execution (pytest failure on test_root_text_bg_meets_wcag_aa)
- **Issue:** design-tokens.css has 4 separate `:root { }` blocks. The plan's suggested `r":root\s*\{([^}]+)\}"` regex stops at the first `}`, which falls inside a layout/spacing block containing no color tokens.
- **Fix:** `_extract_root_blocks()` uses depth-counting loop; `parse_root_tokens()` merges all root blocks.
- **Files modified:** tests/test_color_contrast_wcag.py
- **Commit:** 63e4f9ce1

**2. [Rule 2 - Architecture note] PricingCheck kept separate from GLOBAL_ASSERTIONS**
- **Found during:** Task 2 design
- **Issue:** Adding `Assertion(selector=".holo .product-price", max_count=0)` would assert zero price elements exist, but price elements exist on every collection page. CSS has no `:contains()`.
- **Fix:** `PricingCheck` dataclass + `check_no_forbidden_text()` iterate element `.text` for forbidden strings. Called in `check_page()` after `evaluate_assertions()`. Not in GLOBAL_ASSERTIONS.
- **Files modified:** scripts/verify_live_structure.py
- **Commit:** 63e4f9ce1

## Known Stubs

None — all helpers produce real outputs from real CSS token values.

## Self-Check: PASSED

- `tests/test_color_contrast_wcag.py` exists: FOUND
- `scripts/verify_live_structure.py` modified with PricingCheck: FOUND
- Commit `63e4f9ce1` exists: FOUND
- 6 pytest tests pass: CONFIRMED
