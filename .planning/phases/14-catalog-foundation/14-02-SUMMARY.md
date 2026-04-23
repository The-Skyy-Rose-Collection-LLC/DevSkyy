---
phase: 14-catalog-foundation
plan: 02
subsystem: infra
tags: [python, catalog, adapter, shim, imagery-pipeline, csv]

requires:
  - phase: 14-01
    provides: garment_type_lock column in canonical CSV + scripts/nano_banana/__init__.py package marker

provides:
  - scripts/nano_banana/catalog.py — shim delegating to skyyrose.core.catalog_loader with full legacy API surface
  - renders/config.py — PRODUCT_CATALOG list + PRODUCTS_DIR + manifest.json-based _find_bundle_dir
  - skyyrose/elite_studio/fashion/context.py — canonical _CATALOG_PATH via import from skyyrose.core.catalog_loader

affects: [phase-15, phase-18, nano-banana-pipeline, elite-studio-compositor, renders-orchestrator]

tech-stack:
  added: []
  patterns:
    - Adapter shim pattern — thin delegation to skyyrose.core.catalog_loader from all three imagery pipelines
    - manifest.json-based bundle resolution — SKU looked up via manifest "sku" field, not directory name

key-files:
  created:
    - scripts/nano_banana/catalog.py
    - renders/config.py
  modified:
    - skyyrose/elite_studio/fashion/context.py

key-decisions:
  - "Shim pattern over full rewrite — preserves caller API, routes all data through single canonical source"
  - "bundle_dir_for_sku scans manifest.json SKU fields rather than matching directory names (INFRA-02)"
  - "fashion/context.py uses 'collection' column, not retired 'collection_slug'"
  - "CATALOG_CSV re-exported from each shim for callers that need the path directly"

patterns-established:
  - "All imagery pipelines import read_catalog_rows from skyyrose.core.catalog_loader — never parse CSV directly"
  - "Bundle resolution always via manifest.json scan, never directory-name matching"

requirements-completed: [INFRA-01, INFRA-02, INFRA-03]

duration: ~8min
completed: 2026-04-23
---

# Phase 14-02: Catalog Adapter Shims Summary

**Three broken catalog readers unified — nano-banana, renders orchestrator, and Elite Studio compositor all now delegate to `skyyrose.core.catalog_loader` via thin shims, eliminating three separate CSV parsers**

## Performance

- **Duration:** ~8 min
- **Completed:** 2026-04-23
- **Tasks:** 2/2
- **Files modified:** 3

## Accomplishments
- `scripts/nano_banana/catalog.py` rebuilt as a shim: exposes full legacy API (`load_catalog`, `load_products`, `load_specs`, `get_material_spec`, `find_source_image`) while delegating all CSV reads to `skyyrose.core.catalog_loader`
- `renders/config.py` created with `PRODUCT_CATALOG` list, `PRODUCTS_DIR`, and `_find_bundle_dir` scanning `manifest.json` SKU fields (INFRA-02 — no more directory-name guessing)
- `skyyrose/elite_studio/fashion/context.py` patched: `_CATALOG_PATH` now sourced via `from skyyrose.core.catalog_loader import CATALOG_CSV`, stale `collection_slug` column reference replaced with `collection`
- All 9 Wave 0 RED tests (5 renders_config + 4 fashion_context) now GREEN

## Task Commits

1. **Task 1: Catalog shim + renders config** — `51dc3ff8b` (feat)
2. **Task 2: Fix stale catalog path in fashion/context.py** — `515fd9a90` (fix)
3. **Style cleanup: remove unused import** — `c7a4c2531` (style)

## Files Created/Modified
- `scripts/nano_banana/catalog.py` — Shim delegating to skyyrose.core.catalog_loader; full legacy API preserved
- `renders/config.py` — PRODUCT_CATALOG list + PRODUCTS_DIR + manifest.json-based _find_bundle_dir
- `skyyrose/elite_studio/fashion/context.py` — _CATALOG_PATH now canonical via import; retired column_slug removed

## Decisions Made
- Shim pattern chosen over full rewrite — zero caller breakage, single canonical source
- `_find_bundle_dir` uses manifest.json SKU field scanning per INFRA-02 spec; directory names are unreliable
- `CATALOG_CSV` re-exported from each module for callers that need the raw path

## Deviations from Plan
None — plan executed exactly as written. One style fix (unused import removal) committed separately.

## Issues Encountered
None — `skyyrose.core.catalog_loader` API was clean and well-typed; shim wiring was straightforward.

## Next Phase Readiness
- All three imagery pipelines now use canonical CSV — Wave 3 (Plan 14-03) preflight audit can rely on this
- `_find_bundle_dir` from renders/config.py is the reference implementation Plan 14-03 should mirror for its inline bundle scan

---
*Phase: 14-catalog-foundation*
*Completed: 2026-04-23*
