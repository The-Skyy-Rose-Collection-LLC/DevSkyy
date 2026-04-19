# Cerebrum

> OpenWolf's learning memory. Updated automatically as the AI learns from interactions.
> Do not edit manually unless correcting an error.
> Last updated: 2026-04-07

## User Preferences

<!-- How the user likes things done. Code style, tools, patterns, communication. -->

## Source of Truth

- **`wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` is the SINGLE source of truth** for all live SKUs (30 products as of 2026-04-19). Every consumer — the WP theme's `inc/product-catalog.php` loader, any Python pipeline, any script — must read through this file. **Do not introduce a second catalog.**
- **WP theme loader**: `wordpress-theme/skyyrose-flagship/inc/product-catalog.php` parses the CSV and exposes `skyyrose_get_product_catalog()`, `skyyrose_get_product($sku)`, `skyyrose_get_collection_products($collection)`, `skyyrose_product_url($sku)`, etc. PHP code inside the theme MUST go through these helpers — never read the CSV directly.
- **Retired 2026-04-19** (deleted): `assets/product-masters/catalog.yaml`, `assets/product-masters/manifest.json`. Generators `scripts/generate_catalog.py` and `scripts/sync_manifest_from_catalog.py` are now obsolete — remove in a follow-up commit.
- **Broken Python readers pending rewrite to the CSV**: `skyyrose/elite_studio/catalog.py`, `wordpress/collection_page_manager.py`, `skyyrose/elite_studio/master_registry.py`, and their tests (`skyyrose/elite_studio/tests/test_catalog*.py`, `tests/wordpress/test_collection_page_manager.py`). These will throw on import until they read `data/skyyrose-catalog.csv` — flag when running the compositor/fidelity/collection-page pipelines.
- **CSV schema**: sku, name, price, collection, description, badge, image, front_model_image, back_image, back_model_image, sizes, color, edition_size, published, is_preorder. Booleans are `1`/`0`. Badge is a free string (`Pre-Order`, `Draft`, or empty = Active). Image paths are theme-relative (`assets/images/products/...`).
- **MEMORY.md product lists are HISTORICAL** snapshots — operational truth lives in the CSV. Do not add new SKU data to MEMORY.md.

## Key Learnings

- **Python packaging convention (MANDATORY)**: Every top-level package directory in DevSkyy MUST contain `__init__.py`. No implicit namespace packages. `mypy.ini` has `namespace_packages = False` enforcing this repo-wide. Missing `__init__.py` in a package dir causes mypy to resolve the same `.py` file under two module names (e.g., `preflight` and `renders.preflight`) and emit "Source file found twice under different module names" — blocking commits with a non-obvious root cause. Add `__init__.py` in the same commit as any new top-level package dir, even if empty.
- **Project:** devskyy
- **Description:** AI-driven multi-agent orchestration platform for enterprise e-commerce automation
- **SDK canonical path:** `sdk/python/agent_sdk/` is the authoritative SDK. Root `agent_sdk/` was a stale copy with wrong brand data and has been deleted.
- **SDK internal imports:** All intra-package imports inside `sdk/python/agent_sdk/` use relative imports (`.module`), NOT absolute `from agent_sdk.module`.
- **base_super_agent:** The `agents/base_super_agent/` package is authoritative. `agents/base_super_agent.py` monolith has been deleted — do not recreate it.
- **Integration tests canonical location:** `tests/integration/` — not `tests/test_*.py` at root for integration-level tests.
- **[2026-04-18] When the diff is large, audit the abstraction before polishing the code inside it.** Before running local code-quality reviews (lint, style, redundancy) on a non-trivial refactor, first check whether an existing adapter/helper/pattern in the codebase already solves the problem a different way. A correct-abstraction fix dissolves the local findings automatically — wrong-abstraction polish just makes the wrong thing tidier.

  **Why:** During the LH cathedral immersive retrofit, three parallel review agents ran (reuse / quality / efficiency). The quality and efficiency agents found real local issues (redundant `(string)` casts, uncached `wc_get_products` query, stringly-typed props, copy-paste fallback branches). The reuse agent found that `skyyrose_immersive_product()` in `inc/immersive-product-adapter.php` already encapsulated the entire build — used by BR and SIG templates. Switching to the adapter deleted ~70 lines and invalidated every other finding (no more WC query to cache, no more fallback to DRY, no more casts to remove, no more duplicated catalog data). If only the quality agent had run, I'd have spent 20 minutes polishing the doomed abstraction.

  **How to apply:** For any diff >50 lines, spawn a reuse-scan agent FIRST (or alongside quality/efficiency) with the question *"does an existing helper/adapter/convention already solve this in this codebase?"* — and read its findings before acting on the others. If reuse finds a better abstraction, scrap the diff and restart from the adapter; do not layer polish on top of what you're about to delete.

- **[2026-04-19] Preflight scope MUST match deploy scope.** If a path is excluded from what ships, it must also be excluded from what gets validated. Coherence between the two is a correctness property, not a performance optimization.

  **Why:** `scripts/deploy-theme.sh` had `vendor/`, `node_modules/`, `tests/` in its rsync/tar exclude lists (they never ship), AND in `.phpcs.xml` (they don't get style-checked), AND in `.gitignore` (they're not tracked) — but the preflight PHP syntax check walked the theme with a plain `find -name '*.php'` and no prunes. Result: 3,881 files linted per deploy when only 124 are actually shipped. Cost: ~5–6 min per deploy for vendor/ alone, multiplied by every deploy for the life of the project. This isn't slow — it's incoherent. The lint was validating code that would never run in production.

  **How to apply:** For any validation step (lint, test, type-check, security scan) in a deploy/build script, reference the same exclude list the transport layer uses. If the tarball excludes `vendor/`, the lint must prune `vendor/`. If the zip skips `node_modules/`, the type-check must skip `node_modules/`. Ideal implementation: one source-of-truth array that both the transport and every validator consume. When scope diverges, silently-wrong work accumulates (and deploys get slow as a symptom). Treat divergence as a bug, not a performance issue. [bug-058]

## Do-Not-Repeat

<!-- Mistakes made and corrected. Each entry prevents the same mistake recurring. -->
<!-- Format: [YYYY-MM-DD] Description of what went wrong and what to do instead. -->
- [2026-04-15] Never import from root `agent_sdk/` — it no longer exists. Use `from sdk.python.agent_sdk.X import Y`.
- [2026-04-15] Never create `agents/base_super_agent.py` as a flat file — the package at `agents/base_super_agent/` is authoritative and Python will silently ignore the .py if you recreate it anyway.

## Decision Log

<!-- Significant technical decisions with rationale. Why X was chosen over Y. -->
- [2026-04-15] Chose `sdk/python/agent_sdk/` as SDK source of truth over root `agent_sdk/` — root copy had stale brand data ("Where Love Meets Luxury" tagline, missing EliteStudio integration). All internal imports converted to relative to make the package location-independent.
- [2026-04-16] Compositor pipeline (`skyyrose/elite_studio/agents/compositor_agent.py`) commercial retrofit — chose **instrument-first** (read-only per-stage telemetry via `elite_studio/telemetry.py` → `logs/compositor-telemetry-YYYY-MM-DD.jsonl`) over proposed schema/breaker/cache refactor. **Why:** 40% token-reduction and 3-retry breaker claims are estimates until we have baseline unit economics. Two weeks of telemetry converts the retrofit from "optimization theatre" into a defensible CFO-grade business case. **Trade-off:** zero behavior change ships slower than a full refactor, but eliminates the risk of breaking the revenue-critical drop pipeline on speculative gains. Retrofit waves 2–4 (schema pinning, `forward_qa_verdict`, idempotent content-hash cache, per-stage circuit breaker) gated on telemetry data. [cmem #533]
