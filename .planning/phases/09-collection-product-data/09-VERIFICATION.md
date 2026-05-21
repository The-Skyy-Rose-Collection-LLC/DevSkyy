---
phase: "09"
status: partial
data_02: passed
data_03: passed
data_01: failed_pre_existing_regression
verified_at: "2026-05-12T14:23:00Z"
---

# Phase 9 Verification Report

## Goal-Backward Summary

**Phase goal:** Every collection page shows its own correct hero banner and only the products that belong to it.

| Requirement | Status | Evidence |
|-------------|--------|----------|
| DATA-02: Pre-order SKUs flagged in CSV | PASSED | pytest 3/3 green — `br-003`, `br-006`, `sg-001` confirmed `is_preorder=1` |
| DATA-03: No cross-collection SKU leakage | PASSED | pytest 3/3 green — all SKU prefix→collection mappings valid in CSV |
| DATA-01: Black Rose hero banner correct on live | BLOCKED | Live site regression — collection template not serving expected markup |

## DATA-02 Verification (PASSED)

```
test(09-01): test_preorder_skus_flagged          PASSED
test(09-01): test_no_cross_collection_sku_leakage PASSED
test(09-01): test_collections_are_valid           PASSED
```

Regression gate committed at `tests/test_collection_data_integrity.py` (commit `1c1f22898`).

## DATA-03 Verification (PASSED)

Same test run as DATA-02 — `test_no_cross_collection_sku_leakage` validates prefix-to-collection mapping for all rows in the catalog CSV.

## DATA-01 Verification (BLOCKED — Pre-existing Site Regression)

Live run at 2026-05-12 14:23:00 UTC:

```
$ python scripts/verify_live_structure.py --page black-rose
[FAIL] col-page[data-collection='black-rose']  found=0, min=1
[FAIL] section.col-hero                        found=0, min=1
[FAIL] div.holo--black-rose                    found=0, min=12
[FAIL] img[src*='sr-collection-black-rose.webp'] found=0, min=1
Exit code 2
```

**Root cause not determined** — collection template markup (`col-page`, `col-hero`, collection-specific `holo--*` classes) absent from live HTML despite HTTP 200 and correct theme CSS. Signature collection shows same pattern. Not caused by Phase 9 code changes (no PHP/theme changes made).

**Required next step:** Inspect raw HTML of `https://skyyrose.co/collection-black-rose/` to determine which template WordPress is serving. Compare against `template-collection-black-rose.php` expected output.

```bash
# Diagnostic command — read-only, no production writes
curl -s "https://skyyrose.co/collection-black-rose/?nocache=$(date +%s)" | grep -o 'col-page\|col-hero\|holo--black\|template' | head -20
```

## Commits

| Plan | Commit | Description |
|------|--------|-------------|
| 09-01 | `1c1f22898` | test(09-01): add collection data integrity tests for DATA-02 and DATA-03 |
| 09-02 | `a598ef359` | feat(09-02): extend verify_live_structure with collection hero asset assertions |

## What Remains

- [ ] DATA-01: Diagnose and fix live collection page template regression
- [ ] DATA-01: Re-run `python scripts/verify_live_structure.py --page black-rose` — must exit 0
- [ ] DATA-01: Close `[ ] **DATA-01**` checkbox in `.planning/REQUIREMENTS.md` after live pass
