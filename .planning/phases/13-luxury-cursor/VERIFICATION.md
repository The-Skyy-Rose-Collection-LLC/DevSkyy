# Phase 13: Luxury Cursor — Verification Status

**Date:** 2026-05-12
**Status:** PARTIAL — CURS-03 open gap

## Requirements Status

| Requirement | Description | Status | Evidence |
|-------------|-------------|--------|----------|
| CURS-01 | Cursor renders above modals/popups (z-index) | PASS | z-index: 99999 in luxury-cursor.css; pytest PASSED (commit 818868654) |
| CURS-02 | Cursor pauses/adapts when modal is open | PASS | Verified 2026-03-11 |
| CURS-03 | Cursor JS does not load on immersive templates | OPEN GAP | `luxury-cursor.min.js` loaded unconditionally in `skyyrose_enqueue_global_scripts()` (enqueue.php lines 249–259); pytest FAILS (commit 818868654) |

## CURS-03 Gap Detail

**Root cause:** `wp_enqueue_script('skyyrose-luxury-cursor', ...)` lives inside `skyyrose_enqueue_global_scripts()` with no slug conditional. All pages — including immersive templates where the cursor is CSS-hidden — receive the cursor JS.

**Impact:** Wasted bandwidth + potential JS interference with Three.js/WebGL scene on immersive templates.

**Regression gate:** `tests/test_luxury_cursor.py::test_cursor_not_loaded_on_immersive` — intentionally FAILS until fix lands.

**Fix (future phase):**
1. Move `wp_enqueue_script('skyyrose-luxury-cursor', ...)` from `skyyrose_enqueue_global_scripts()` into `skyyrose_enqueue_template_scripts()`
2. Wrap with `if ($slug !== 'immersive') { ... }`
3. Run `npm run deploy` (requires STOP-AND-SHOW confirmation per CLAUDE.md)
4. Verify `test_cursor_not_loaded_on_immersive` PASSES post-deploy

## What Was NOT Done (by design)

- No theme deploy (STOP-AND-SHOW gate)
- No fix to enqueue.php (separate engineering task)
- No WooCommerce or production writes
