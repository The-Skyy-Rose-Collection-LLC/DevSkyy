# Cerebrum

> OpenWolf's learning memory. Updated automatically as the AI learns from interactions.
> Do not edit manually unless correcting an error.
> Last updated: 2026-04-07

## User Preferences

<!-- How the user likes things done. Code style, tools, patterns, communication. -->

## Source of Truth

- **`assets/product-masters/catalog.yaml` is the SINGLE source of truth** for all 30 live SKUs (schema v2). Contains: sku, name, collection, price_usd, status, aliases, filename_patterns, color_spec, text_spec, master (path/hash/source), source_files, ai_renders, review_flags, notes. Plus collection defaults, unclaimed_legacy_files section, orphan_brand_files section.
- **`manifest.json` is DERIVED** — never edit directly. Regenerate via `scripts/generate_catalog.py` (reads manifest + filesystem + hardcoded operational memory → emits catalog.yaml).
- **`MEMORY.md` product lists are HISTORICAL** — operational truth now lives in catalog.yaml. Do not add new SKU data to MEMORY.md.
- **Legacy SKU → current SKU mappings live in `aliases: []`** per product. The vision test, bootstrap, and fidelity gate should resolve legacy filenames through aliases before falling back to color matching.

## Key Learnings

- **Python packaging convention (MANDATORY)**: Every top-level package directory in DevSkyy MUST contain `__init__.py`. No implicit namespace packages. `mypy.ini` has `namespace_packages = False` enforcing this repo-wide. Missing `__init__.py` in a package dir causes mypy to resolve the same `.py` file under two module names (e.g., `preflight` and `renders.preflight`) and emit "Source file found twice under different module names" — blocking commits with a non-obvious root cause. Add `__init__.py` in the same commit as any new top-level package dir, even if empty.
- **Project:** devskyy
- **Description:** AI-driven multi-agent orchestration platform for enterprise e-commerce automation
- **SDK canonical path:** `sdk/python/agent_sdk/` is the authoritative SDK. Root `agent_sdk/` was a stale copy with wrong brand data and has been deleted.
- **SDK internal imports:** All intra-package imports inside `sdk/python/agent_sdk/` use relative imports (`.module`), NOT absolute `from agent_sdk.module`.
- **base_super_agent:** The `agents/base_super_agent/` package is authoritative. `agents/base_super_agent.py` monolith has been deleted — do not recreate it.
- **Integration tests canonical location:** `tests/integration/` — not `tests/test_*.py` at root for integration-level tests.

## Do-Not-Repeat

<!-- Mistakes made and corrected. Each entry prevents the same mistake recurring. -->
<!-- Format: [YYYY-MM-DD] Description of what went wrong and what to do instead. -->
- [2026-04-15] Never import from root `agent_sdk/` — it no longer exists. Use `from sdk.python.agent_sdk.X import Y`.
- [2026-04-15] Never create `agents/base_super_agent.py` as a flat file — the package at `agents/base_super_agent/` is authoritative and Python will silently ignore the .py if you recreate it anyway.

## Decision Log

<!-- Significant technical decisions with rationale. Why X was chosen over Y. -->
- [2026-04-15] Chose `sdk/python/agent_sdk/` as SDK source of truth over root `agent_sdk/` — root copy had stale brand data ("Where Love Meets Luxury" tagline, missing EliteStudio integration). All internal imports converted to relative to make the package location-independent.
- [2026-04-16] Compositor pipeline (`skyyrose/elite_studio/agents/compositor_agent.py`) commercial retrofit — chose **instrument-first** (read-only per-stage telemetry via `elite_studio/telemetry.py` → `logs/compositor-telemetry-YYYY-MM-DD.jsonl`) over proposed schema/breaker/cache refactor. **Why:** 40% token-reduction and 3-retry breaker claims are estimates until we have baseline unit economics. Two weeks of telemetry converts the retrofit from "optimization theatre" into a defensible CFO-grade business case. **Trade-off:** zero behavior change ships slower than a full refactor, but eliminates the risk of breaking the revenue-critical drop pipeline on speculative gains. Retrofit waves 2–4 (schema pinning, `forward_qa_verdict`, idempotent content-hash cache, per-stage circuit breaker) gated on telemetry data. [cmem #533]
