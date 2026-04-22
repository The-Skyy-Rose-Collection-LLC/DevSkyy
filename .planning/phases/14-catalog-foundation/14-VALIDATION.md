---
phase: 14
slug: catalog-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-22
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `python3 -m pytest tests/test_catalog_csv_integrity.py -x -q` |
| **Full suite command** | `python3 -m pytest tests/test_catalog_csv_integrity.py tests/scripts/nano_banana/ tests/test_preflight_audit.py -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/test_catalog_csv_integrity.py -x -q`
- **After every plan wave:** Run `python3 -m pytest tests/test_catalog_csv_integrity.py tests/scripts/nano_banana/ tests/test_preflight_audit.py -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 14-01 | 01 | 1 | INFRA-01 | unit | `python3 -m pytest tests/test_catalog_csv_integrity.py -x -q` | ✅ | ⬜ pending |
| 14-02 | 01 | 1 | INFRA-02 | unit | `python3 -m pytest tests/test_catalog_csv_integrity.py -k "bundle" -q` | ❌ W0 | ⬜ pending |
| 14-03a | 01 | 1 | INFRA-03 | unit | `python3 -m pytest tests/scripts/nano_banana/test_catalog.py -x -q` | ✅ (fails now) | ⬜ pending |
| 14-03b | 01 | 1 | INFRA-03 | unit | `python3 -m pytest tests/test_renders_config.py -x -q` | ❌ W0 | ⬜ pending |
| 14-03c | 01 | 1 | INFRA-03 | unit | `python3 -m pytest tests/test_fashion_context.py -x -q` | ❌ W0 | ⬜ pending |
| 14-04 | 01 | 1 | INFRA-04 | unit | `python3 -m pytest tests/test_catalog_csv_integrity.py -k "garment_type_lock" -q` | ❌ W0 | ⬜ pending |
| 14-05 | 01 | 2 | INFRA-05 | unit | `python3 -m pytest tests/test_preflight_audit.py -x -q` | ❌ W0 | ⬜ pending |
| 14-06 | 01 | 2 | INFRA-06 | unit | `python3 -m pytest tests/test_preflight_audit.py -k "pending" -q` | ❌ W0 | ⬜ pending |
| 14-07 | 01 | 2 | INFRA-07 | integration | `python scripts/preflight_audit.py && python3 -m pytest tests/test_preflight_audit.py -k "skipped_json"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/scripts/nano_banana/conftest.py` — update `_CSV_COLUMNS` to canonical schema (add `garment_type_lock`, remove stale columns)
- [ ] `tests/test_renders_config.py` — smoke test that `renders/config.py` imports and `PRODUCT_CATALOG` is a list
- [ ] `tests/test_fashion_context.py` — smoke test that `fashion/context.py` loads catalog without path errors
- [ ] `tests/test_catalog_csv_integrity.py` — add `garment_type_lock` column test and bundle-dir resolver test
- [ ] `tests/test_preflight_audit.py` — test exits 0, SKIPPED.json has sg-007+lh-005 only, PENDING has 5 known SKUs
