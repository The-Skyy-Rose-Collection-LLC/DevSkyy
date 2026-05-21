---
phase: 15-ghost-mannequin-agent-qa
plan: "02"
subsystem: elite_studio
tags: [security, sku-resolution, path-traversal, accessory-gate, tripo]
dependency_graph:
  requires: []
  provides:
    - skyyrose.elite_studio.sku_resolver.sanitize_sku
    - skyyrose.elite_studio.sku_resolver.resolve_sku
    - skyyrose.elite_studio.sku_resolver.verify_tripo_region
    - skyyrose.elite_studio.sku_resolver.ResolvedSKU
  affects:
    - skyyrose/elite_studio/ghost_mannequin_synthesizer.py
    - skyyrose/elite_studio/ghost_mannequin_agent.py
tech_stack:
  added: []
  patterns:
    - frozen dataclass for immutable resolved product data
    - allowlist regex for input sanitization (security gate)
    - lazy import pattern to avoid hard dependency at module load
    - asyncio.run() wrapper for calling async client from sync context
key_files:
  created:
    - skyyrose/elite_studio/sku_resolver.py
  modified: []
decisions:
  - "parents[2] not parents[3] for repo root — sku_resolver.py lives at skyyrose/elite_studio/sku_resolver.py, so parents[0]=elite_studio, parents[1]=skyyrose, parents[2]=repo root"
  - "asyncio.run(_probe()) wrapper for verify_tripo_region — TripoClient.get_balance() is async def, plan spec was incorrect claiming synchronous"
  - "Both render_is_accessory and garment_type_lock checked in accessory gate — sg-007 and lh-005 have empty garment_type_lock but render_is_accessory=1"
metrics:
  duration_minutes: 15
  tasks_completed: 1
  tasks_total: 1
  files_created: 1
  files_modified: 0
  completed_date: "2026-05-13"
---

# Phase 15 Plan 02: SKU Resolver Security Gate Summary

JWT auth with refresh rotation using jose library — SKU sanitization + catalog resolution security gate using stdlib CSV, regex allowlist, and async Tripo region probe.

## What Was Built

`skyyrose/elite_studio/sku_resolver.py` — the Phase 15 security gate. Every downstream ghost mannequin call routes through this module before any filesystem path is constructed or paid API is dispatched.

Three public functions + one frozen dataclass:

- `sanitize_sku(raw)` — allowlist regex `^[a-zA-Z0-9_-]{1,64}$`, blocks path-traversal (`..`), absolute paths, and all shell metacharacters
- `resolve_sku(raw_sku, catalog_path, bundle_root)` — CSV lookup with accessory silent-skip (D-12/GM-06), returns `ResolvedSKU` or `None`
- `verify_tripo_region(tripo_api_key)` — lazy-imports `TripoClient`, uses `asyncio.run()` wrapper to call async `get_balance()` probe before any paid dispatch (D-08)
- `ResolvedSKU` — frozen dataclass: sku, name, garment_type, bundle_dir, manifest_path, branding_spec, is_jersey

Accessory gate checks both `garment_type_lock == "accessory"` AND `render_is_accessory == "1"` to handle catalog entries where `garment_type_lock` is empty (sg-007 Signature Beanie, lh-005 The Fannie).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed incorrect parents index for repo root path**
- **Found during:** Task 1 pre-implementation analysis
- **Issue:** Plan spec used `parents[3]` which resolves to `/Users/theceo` (the home directory), not the repo root. For `skyyrose/elite_studio/sku_resolver.py`: parents[0]=elite_studio, parents[1]=skyyrose, parents[2]=repo root.
- **Fix:** Used `parents[2]` in implementation. If `parents[3]` had been used, `CATALOG_CSV_PATH` would resolve to `/Users/theceo/wordpress-theme/...` — a nonexistent path causing `FileNotFoundError` on every `resolve_sku` call.
- **Files modified:** `skyyrose/elite_studio/sku_resolver.py`
- **Commits:** d202c99c3

**2. [Rule 1 - Bug] Fixed async/sync mismatch in verify_tripo_region**
- **Found during:** Task 1 — reading `ai_3d/providers/tripo.py`
- **Issue:** Plan spec described `get_balance()` as "a synchronous method" but the actual implementation at `ai_3d/providers/tripo.py:528` is `async def get_balance(self) -> dict[str, Any]`. `TripoClient.__init__` creates `httpx.AsyncClient` — the entire client is async.
- **Fix:** Implemented an inner `async def _probe()` coroutine and called it via `asyncio.run(_probe())` inside the sync `verify_tripo_region()` function. Also handled the `get_balance()` error-swallowing pattern (returns `{}` on internal error) by checking dict truthiness as success signal.
- **Files modified:** `skyyrose/elite_studio/sku_resolver.py`
- **Commits:** d202c99c3

**3. [Rule 1 - Bug] Fixed ruff UP045/UP024 lint violations on initial commit**
- **Found during:** lint-staged pre-commit hook
- **Issue:** `Optional[X]` type annotations (UP045) and `EnvironmentError` alias (UP024) — 6 violations.
- **Fix:** Replaced `Optional[X]` with `X | None` throughout; replaced `EnvironmentError` with `OSError`.
- **Files modified:** `skyyrose/elite_studio/sku_resolver.py`
- **Commits:** 6a7eef17c

## Security Coverage

All three HIGH-severity threats from the plan's threat model are mitigated:

| Threat | Mitigation | Verified |
|--------|-----------|---------|
| T-15-02-01: path-traversal via --sku | `..` rejection + allowlist regex | sanitize_sku('../etc/passwd') raises ValueError |
| T-15-02-02: shell injection via --sku | `[a-zA-Z0-9_-]` allowlist blocks all metacharacters | sanitize_sku('x; evil') raises ValueError |
| T-15-02-03: TRIPO3D_API_KEY exposure | Lazy import, key read from env only, never logged | No key in any log message |

## Task Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 (feat) | d202c99c3 | feat(15-02): create sku_resolver security gate for Phase 15 pipeline |
| Task 1 (fix) | 6a7eef17c | fix(15-02): apply ruff UP045/UP024 fixes to sku_resolver |

## Self-Check: PASSED

- [x] `skyyrose/elite_studio/sku_resolver.py` exists (276 lines)
- [x] Commit d202c99c3 exists: `git log --oneline | grep d202c99`
- [x] Commit 6a7eef17c exists: `git log --oneline | grep 6a7eef1`
- [x] All plan assertions pass: `sku_resolver OK`, `Phase 15-02 sku_resolver verified OK`
- [x] ruff clean on final file state
- [x] No existing tests broken (pre-commit fast unit tests pass)
