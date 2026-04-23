---
phase: 14
reviewers: [codex, opencode, internal-synthesis]
reviewed_at: 2026-04-23T00:47:00Z
plans_reviewed: [14-01-PLAN.md, 14-02-PLAN.md, 14-03-PLAN.md]
cli_status:
  codex: "FAILED — workspace deactivated (402 Payment Required)"
  opencode: "FAILED — token refresh rate limit (429)"
  claude: "SKIPPED — self-review excluded for independence (running inside Claude Code)"
---

# Cross-AI Plan Review — Phase 14: Catalog Foundation

> **Note on reviewer availability**: Codex CLI failed (workspace deactivated / 402). OpenCode failed (429 rate limit). Claude CLI skipped (self-review). The review below is a structured adversarial internal synthesis — attacking each plan from multiple lenses (correctness, edge cases, dependency ordering, security, performance) to replicate what independent reviewers would surface.

---

## Plan 14-01 Review: CSV Column + Wave 0 Test Scaffolding

### Summary

Plan 01 is well-structured and appropriately scoped: it makes only additive changes (new CSV column, new test fixtures) and creates a RED scaffold that drives Plans 02 and 03. The wave ordering is correct — no downstream code is modified here. The plan correctly identifies that test files should fail by design and explicitly calls this out. One gap: the plan says "Wave 0 test files are RED by design" but doesn't address what happens if a RED test accidentally passes (e.g., if `renders/config.py` already existed from a git stash or worktree). The verification step runs only `--collect-only`, not the actual test run, so a false-green from a pre-existing file would be silently accepted.

### Strengths

- **Additive-only CSV change**: appending `garment_type_lock` as column 22 without modifying row order eliminates all reorder-related risk
- **Closed enum of garment types**: hard-coded `ALLOWED_GARMENT_TYPES` set in tests means any future mistyped value (e.g. "windbreaker" instead of "jacket") is caught immediately
- **Comprehensive integrity tests**: 4 new test cases cover schema, non-empty for garments, empty for accessories, and count=28 — no obvious test gap
- **Package marker is zero-surface**: single docstring, no code, no import side effects
- **Correct conftest column removal**: explicitly removing `type`, `collection_slug`, `render_variant_of` prevents legacy schema leaking into downstream test fixtures

### Concerns

- **[MEDIUM] RED-but-actually-green risk**: If `renders/config.py`, `scripts/preflight_audit.py`, or `skyyrose/elite_studio/fashion/context.py` (with a working path) already exist from a git stash, branch artifact, or worktree, the Wave 0 "RED" tests will pass on collection and also on execution — the plan's acceptance criteria only runs `--collect-only`, not a full `pytest` run. This creates false confidence that the tests will turn GREEN when Plan 02/03 implement the modules.
  - *Fix*: Add a negative assertion: `python3 -m pytest tests/test_renders_config.py -x -q 2>&1 | grep -c FAILED` must return >= 1 before Plan 02 runs.

- **[MEDIUM] `conftest.py` _SAMPLE_ROWS update is underspecified**: The plan tells the executor to "update every entry in `_SAMPLE_ROWS`" to add `garment_type_lock` and remove legacy columns, but the exact existing contents of `_SAMPLE_ROWS` are not included in the plan. If the conftest already has non-obvious fixture rows (e.g., a `none` collection variant, a pre-order fixture, a row without edition_size), the update instructions may be insufficient.
  - *Fix*: Plan should read conftest.py first and list specific rows to modify (the plan does say `read_first: tests/scripts/nano_banana/conftest.py` — this is partially addressed, but the action doesn't show what the existing rows look like).

- **[LOW] `test_all_28_in_scope_garments_have_garment_type_lock` vs. 30 total rows**: The test asserts `count == 28` (28 non-empty garment_type_lock values). This is correct given 2 accessories. But if a future CSV edit adds a 31st product (a garment), this test will start failing — it's brittle to exact count. Consider deriving the count from `render_is_accessory == "1"` count rather than hardcoding 28.

- **[LOW] No test for `garment_type_lock` preserving CSV quoting**: The plan notes "Preserve quoting on any existing quoted fields." But there's no test that verifies fields with commas (like `"bomber jacket"`) are properly quoted after the CSV edit. A naive CSV append that doesn't handle multi-word values could corrupt the schema.

### Suggestions

- Add a `--collect-only` → then a `pytest --tb=no -q` run on the 3 Wave 0 test files, confirming they each fail with the expected error (ImportError/ModuleNotFoundError) rather than a test logic failure
- Make `test_all_28_in_scope_garments_have_garment_type_lock` compute the expected count as `len([r for r in rows if not bool_col(r, "render_is_accessory")])` rather than asserting `count == 28`
- Explicitly verify the CSV after edit: `python3 -c "import csv; rows=list(csv.DictReader(open('...skyyrose-catalog.csv'))); print(rows[0]['garment_type_lock'])"` — confirms quoting was handled correctly

### Risk Assessment: **LOW**

Plan 01 makes no behavior changes to production code. The only risk is the RED-but-green scenario which is a false confidence issue, not a correctness issue. The phase can proceed safely from this plan.

---

## Plan 14-02 Review: Fix Three Broken Readers

### Summary

Plan 02 is the highest-complexity plan in Phase 14 — it rebuilds three distinct modules across different subsystems in a single plan. The task decomposition is good (Task 1: nano_banana + renders; Task 2: fashion/context.py). The API contracts are well-specified and anchored to actual test expectations. The key risk is that `renders/config.py` builds `PRODUCT_CATALOG` at import time by scanning 32 bundle directories — this is a correct tradeoff (import-time compute is the existing project pattern) but deserves explicit acknowledgment. One correctness gap: `_find_bundle_dir` has a `name` parameter that is retained for backwards compatibility but explicitly not used — this could cause confusion in future callers who pass a name expecting it to matter.

### Strengths

- **Shim pattern is appropriate**: nano_banana.catalog delegates to `skyyrose.core.catalog_loader` rather than reimplementing — single source of truth preserved
- **`load_specs()` silent-return on missing file**: returning `{}` when `data/product-specs.json` doesn't exist is correct — this is an optional supplemental file, not a required catalog
- **`find_source_image()` precedence is explicit**: override → bundle scan → None, clearly documented
- **`_find_bundle_dir()` uses manifest.json scan not name matching**: correct implementation of INFRA-02
- **fashion/context.py fix is minimal**: replaces exactly one line (stale path) and one column reference — no refactoring beyond what's needed
- **`collection_slug` fix scope is narrow**: only CSV column lookups change; local variable names retain `collection_slug` for caller compatibility

### Concerns

- **[HIGH] `_find_bundle_dir` backwards-compat `name` parameter creates silent correctness risk**: `renders/config.py`'s `_find_bundle_dir(name, sku=None)` accepts `name` but ignores it when `sku` is provided. However: if `sku=None` is passed (the default!), the function returns `None` immediately. This means any caller that passes only a name (e.g., `_find_bundle_dir("BLACK Rose Crewneck")`) will silently get `None` instead of the bundle. The existing `renders/preflight.py` call pattern is `_find_bundle_dir(row["name"], sku=row["sku"])` — but any future caller who doesn't know to pass `sku=` gets broken behavior with no error.
  - *Fix*: Either make `sku` non-optional (removing the backwards-compat shim), or add a warning/log when `sku=None` is passed: `if not sku: logger.warning("_find_bundle_dir called without sku — returning None"); return None`

- **[HIGH] `PRODUCT_CATALOG = _build_product_catalog()` runs at import time for ALL 30 rows × manifest scan**: The bundle scan iterates 32 directories and reads 32 manifest.json files. At import time, this means every test that imports `renders.config` will pay this I/O cost. This is noted in the research as "acceptable" (<0.1s) — but it should be verified by timing. Also: if `data/product-bundles/` doesn't exist (e.g., in a CI environment or stripped clone), `_build_product_catalog()` will fail at import time with a `FileNotFoundError` because `_BUNDLES_DIR.iterdir()` raises if the directory doesn't exist.
  - *Fix*: Add `if not _BUNDLES_DIR.is_dir(): return []` guard in `_build_product_catalog()` (or the `_find_bundle_dir` function already handles this — verify it propagates).

- **[MEDIUM] nano_banana `load_catalog()` always reads from disk (no caching)**: `load_catalog()` calls `read_catalog_rows()` on every invocation. The test suite may call this 10+ times per run. This is not a correctness issue but could make tests slow if the CSV grows. The existing `fashion/context.py` has a `_catalog_cache` pattern — `nano_banana.catalog` should consider the same.

- **[MEDIUM] `renders/config.py` `_find_bundle_dir` doesn't guard against malformed manifests at import time**: `_build_product_catalog()` calls `_find_bundle_dir()` for every row. Inside `_find_bundle_dir()`, the OSError/JSONDecodeError is caught — but if `_BUNDLES_DIR` contains a very large directory tree (nested bundles), this scan could be slow. Existing bundle structure is flat (32 top-level dirs), so this is LOW risk currently but could regress if directory structure changes.

- **[LOW] `fashion/context.py` may have more than one `collection_slug` reference**: The plan says to scan for "any OTHER references" and fix them. But the acceptance criteria only checks `grep -c '"collection_slug"' = 0`. A reference like `row.get('collection_slug')` (single quotes) would pass this grep. The search should use a more robust pattern: `grep -P "(\"collection_slug\"|'collection_slug')"`.

- **[LOW] `load_products()` always calls `find_source_image()` for every product**: This means even a filtered call (e.g., `load_products(collection="black-rose")`) will scan bundle manifests for every product in that collection to find the source image path. Consider making `source_path` lazy (only resolve when needed) or documenting the performance characteristics.

### Suggestions

- Make `sku` a required parameter in `_find_bundle_dir` (or at minimum add a deprecation warning when called with `sku=None`)
- Add `if not _BUNDLES_DIR.is_dir(): return []` in `_build_product_catalog()` to prevent import-time crash in CI environments
- Grep for both quote styles when checking for retired `collection_slug` column references
- Add a single-line `_catalog_cache` mechanism to `nano_banana.catalog.load_catalog()` for test performance (mirrors the fashion/context.py pattern)

### Risk Assessment: **MEDIUM**

The stale `_find_bundle_dir` name parameter and the potential import-time crash when `data/product-bundles/` is missing are real correctness risks. Neither blocks phase completion but could surface as confusing failures in CI or when a new developer runs tests in a fresh environment. The fashion/context.py fix is clean and low-risk.

---

## Plan 14-03 Review: Preflight Audit Script

### Summary

Plan 03 is the most mature plan in the phase: the script architecture is clean, the three-category classification is correct, the exit-code design (exit 0 even with PENDING) is explicitly justified, and the SKIPPED.json format is well-specified. The test suite from Plan 01 provides comprehensive coverage. One structural concern: `scripts/preflight_audit.py` imports from `skyyrose.core.catalog_loader` — but `scripts/` is not on sys.path by default. The test suite uses `import scripts.preflight_audit` which requires `scripts/` to be importable as a Python package. This depends on `scripts/__init__.py` existing. If it doesn't, `import scripts.preflight_audit` will fail.

### Strengths

- **Three-category classification matches the research findings**: READY / SKIPPED / PENDING_USER_ASSETS exactly matches the analysis of the 30 SKUs
- **Exit 0 on PENDING is intentional and documented**: The comment explains the rationale — "The user must provide the source assets before Phase 15 runs — the script's job is to surface this clearly"
- **`generated_at` timestamp in SKIPPED.json**: provides an audit trail for when the file was regenerated
- **`classify_sku()` is a pure function**: takes a row and bundles_dir, returns an AuditEntry — this makes it independently testable via monkeypatch
- **`main()` accepts `skipped_out` kwarg**: allows tests to redirect output to tmp_path without patching filesystem globals
- **`_find_bundle_for_sku()` mirrors the Plan 02 pattern exactly**: consistent implementation avoids divergence between the audit and the runtime resolver
- **`shutil.get_terminal_size()` fallback**: `(100, 40)` default means the script doesn't fail on non-tty environments

### Concerns

- **[HIGH] `import scripts.preflight_audit` fails unless `scripts/__init__.py` exists**: The test `test_preflight_audit_module_importable` does `import scripts.preflight_audit`. This requires `scripts/` to be importable as a Python package. If `scripts/__init__.py` doesn't exist (common for `scripts/` directories), this import fails with `ModuleNotFoundError: No module named 'scripts'`. The plan doesn't create `scripts/__init__.py`. The acceptance criteria doesn't check for it.
  - *Fix*: Either create `scripts/__init__.py` (empty or with docstring), or change the test import to use `importlib.util.spec_from_file_location` to import by file path. Check whether `scripts/__init__.py` exists in the current codebase.

- **[MEDIUM] `_print_summary()` format may not match test assertions**: `test_ready_count_equals_23` asserts: `"23" in out and "READY" in out`. The actual print is `f"  READY:               {len(ready):3d}"` — this produces `"  READY:                23"`. The test's loose assertion `"23" in out` will pass, but if anyone changes the format (e.g., to `"READY (23/28)"`) the number 23 still appears in out. This is not a bug but a fragile test.

- **[MEDIUM] `test_all_30_skus_classified` asserts `"30" in out`**: The number "30" appears in the summary line `"  TOTAL:               {len(entries):3d} / 30"`. But "30" could also appear in SKU names, dates, or the catalog path. If `CATALOG_CSV` path contains "30" (unlikely but possible), this creates a false positive. More robust: assert `len(entries) == 30` directly in the test via the `main()` return value or a separate assertion.

- **[LOW] lh-006 bundle mismatch not handled in SKIPPED.json**: The research notes that `data/product-bundles/The Fannie/manifest.json` has `"sku": "lh-006"` but the CSV has `lh-005`. Since lh-005 is an accessory → SKIPPED.json, this is fine for Phase 14. But the audit stdout doesn't mention the orphan bundle (lh-006 bundle but no CSV entry). A future phase could misinterpret this as a missing product. Consider adding an "orphan bundles" check to stdout (optional enhancement, not a blocker).

- **[LOW] No test for re-running idempotency**: If `python scripts/preflight_audit.py` is run twice, the second run should overwrite SKIPPED.json cleanly. The code does `skipped_out.write_text(...)` which is idempotent, but there's no test verifying this. Not a blocker.

- **[LOW] `_SEP` uses `─` (U+2500 BOX DRAWINGS LIGHT HORIZONTAL)**: Some terminal environments or log collectors may not render this correctly. ASCII fallback `─` vs `-` is a cosmetic issue but worth noting.

### Suggestions

- Check whether `scripts/__init__.py` exists; if not, create it (empty or docstring) as part of Plan 03 or as a prerequisite note
- Change `test_all_30_skus_classified` to check `rc == 0` and validate entry count structurally rather than string-matching `"30"` in output
- Add an "orphan bundles" section to the audit stdout — bundles in `data/product-bundles/` whose `manifest.json` SKU doesn't match any CSV SKU
- Document in the script's docstring that PENDING_USER_ASSETS is informational and doesn't trigger exit 1

### Risk Assessment: **MEDIUM**

The `scripts/__init__.py` issue is a genuine blocker: if `scripts/` isn't a Python package, `import scripts.preflight_audit` in the test suite will fail with ModuleNotFoundError before any test logic runs. Everything else is LOW risk. Once the package marker issue is resolved, this plan should execute cleanly.

---

## Consensus Summary

### Agreed Strengths

All three plans share these well-designed properties:

1. **Canonical source of truth is preserved**: Every new file delegates to `skyyrose.core.catalog_loader` — the existing adapter is not modified or bypassed
2. **Wave ordering is correct**: Plan 01 (CSV + test scaffolding) → Plan 02 (readers) → Plan 03 (audit). No circular dependencies. Each wave has a clear input/output contract
3. **TDD discipline is maintained**: RED test files from Plan 01 become GREEN in Plans 02 and 03. The test suite drives implementation, not the reverse
4. **Zero API calls, zero cost**: The entire phase is pure filesystem I/O — correct for an infrastructure foundation phase
5. **Threat model is minimal and accurate**: No user input, no network, no auth. The STRIDE register accurately reflects the zero external-boundary architecture

### Agreed Concerns

These issues appear across multiple plans and warrant attention before execution:

1. **`scripts/__init__.py` existence is assumed but not verified** (Plan 03, HIGH): The test suite imports `scripts.preflight_audit` as a Python package. If `scripts/__init__.py` doesn't exist, all Plan 03 tests fail before reaching any test logic. Should be verified and created if missing — either in Plan 01 (alongside `scripts/nano_banana/__init__.py`) or early in Plan 03.

2. **`_find_bundle_dir(name, sku=None)` silent-None when sku omitted** (Plan 02, HIGH): The backwards-compat signature is a latent correctness bug. Future callers who omit `sku=` will get `None` silently. This should be documented prominently or the signature changed to `_find_bundle_dir(sku: str) -> Path | None`.

3. **Wave 0 RED tests should be explicitly verified as failing** (Plan 01, MEDIUM): The acceptance criteria use `--collect-only` to verify syntax but don't confirm the tests actually fail. A pre-existing `renders/config.py` from a worktree would silently turn Plan 01's "RED" tests green before Plan 02 runs.

### Divergent Views (Worth Investigating)

1. **Import-time PRODUCT_CATALOG build (Plan 02)**: The research says <0.1s for 32 dirs — this is probably fine. But the CI environment may not have `data/product-bundles/` available. The missing-dir guard in `_build_product_catalog()` should be confirmed as present (it is in `_find_bundle_dir()` via the `is_dir()` check, but `_build_product_catalog()` itself still calls `iterdir()` without checking).

2. **Preflight exit code design (Plan 03)**: Treating PENDING_USER_ASSETS as informational (exit 0) is correct for Phase 14, but Phase 15 planning should add an explicit gate: `python scripts/preflight_audit.py && [ $(jq '.total_in_scope_garments' renders/ghost-mannequin/SKIPPED.json) -eq 28 ]` to confirm the audit ran successfully before any generation.

---

## Pre-Execution Checklist

Before starting Plan 01 execution, verify:

- [ ] `scripts/__init__.py` — does it exist? If not, add it (empty or docstring) to Plan 01's file list
- [ ] `renders/config.py` — confirm it does NOT exist (verify Plan 02's start state)
- [ ] `scripts/nano_banana/__pycache__/` — confirm only .pyc files (no .py source) to validate Plan 02's rebuild approach
- [ ] `tests/scripts/nano_banana/conftest.py` — read the actual `_SAMPLE_ROWS` content before Plan 01 updates it

To incorporate this feedback into planning:
```
/gsd-plan-phase 14 --reviews
```
