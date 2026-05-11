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
- **[2026-05-03] BRAND CANON (PRIMARY SOURCE) lives at `knowledge-base/seed/from-interview.md`.** Corey provided four blocks of canon directly: (1) Visual references — KITH, Coach, Palm Angels, Drake Related, Aimé Leon Dore, Fear of God Eternal, The Row, Jacquemus, Document/i-D. (2) Anti-references — NO BLUE in any shade, no luxury clichés (gold filigree / marble / champagne), no dry CSS-only product reveals, no lackluster/safe defaults, no dated 2015-2022 e-commerce templates, no gendered copy framing ("for him"/"for her"/"men's"/"women's" all banned). (3) Oakland canon — Deep East, Oakland Hills, Stone City, The 100s, Brookfield, Sobrante Park, The Coliseum, Real Oakland, The Shows, Sequoyah Highlands — these names appear in copy but are NEVER explained. Bay Area ≠ Oakland; the brand is Oakland-specific. (4) Engineering rules — identify verified canonical source first, no glob fishing; silent correction not apologies. (5) Reality check — IMAGERY GENERATION IS THE #1 LAUNCH BLOCKER (Phase 5 sub-phase order is reprioritized in `knowledge-base/decisions/0003-imagery-as-launch-blocker.md`); aesthetic translation is the unexpected win — protect it. When canon conflicts with derived docs (banned-elements.md, brand-story.md), the interview file wins.
- **[2026-05-03] AP-16 added — Glob Fishing Instead of Consulting Canonical Source.** Before any task, name the canonical source(s) you'll consult in one sentence. Catalog → CSV. Brand → from-interview.md + brand-story.md. Architecture → ADRs + decisions/. Locked decisions → SKYYROSE_V2_MASTER_PLAN.md §1.1. Per-page intent → SKYYROSE_WORDPRESS_PLAN.md §6. Catalog reader code → `inc/product-catalog.php` (PHP) / `skyyrose/core/catalog_loader.py` (Python). If you can't name the source, stop and ask — don't grep. See `knowledge-base/lessons/anti-patterns.md` AP-16.
- **[2026-05-03] Silent-disable audit found 8 instances of "configured but invisibly failing" anti-pattern.** See `eval/silent-disable-audit.md` for the full list. Critical instances: `~/DevSkyy/.mcp.json` runs claude-context (Milvus down) + postgresql (env var unset) + aidesigner (HTTP 401) every session, all silently failing. `~/.claude.json` stores WP app password in plaintext. Measurement packet's test_command points at `scripts/measurement/verify-all-grants.js` which doesn't exist yet. Fixes await user direction. Common fingerprint: "exit 0" used as success signal when work didn't happen.
- **[2026-05-03] MCP servers must live under the literal `mcpServers` key in `~/.claude/settings.json`.** Renaming the key (e.g., `_disabled_mcpServers__rename_to_mcpServers_to_reenable`) silently disables every server beneath it — no error, no log line, no tool surfaces. Sequential Thinking was parked under that renamed key for an unknown duration and looked "missing" until the fix on this date. Re-enabled by creating a proper `mcpServers` block. `claude-context` left disabled because it needs Milvus on `127.0.0.1:19530` (Ollama on `11434` is up). See `~/.claude/projects/-Users-theceo-DevSkyy/memory/project_mcp_settings.md`. **Tool surfaces only on next session restart.**
- **[2026-04-18] When the diff is large, audit the abstraction before polishing the code inside it.** Before running local code-quality reviews (lint, style, redundancy) on a non-trivial refactor, first check whether an existing adapter/helper/pattern in the codebase already solves the problem a different way. A correct-abstraction fix dissolves the local findings automatically — wrong-abstraction polish just makes the wrong thing tidier.

  **Why:** During the LH cathedral immersive retrofit, three parallel review agents ran (reuse / quality / efficiency). The quality and efficiency agents found real local issues (redundant `(string)` casts, uncached `wc_get_products` query, stringly-typed props, copy-paste fallback branches). The reuse agent found that `skyyrose_immersive_product()` in `inc/immersive-product-adapter.php` already encapsulated the entire build — used by BR and SIG templates. Switching to the adapter deleted ~70 lines and invalidated every other finding (no more WC query to cache, no more fallback to DRY, no more casts to remove, no more duplicated catalog data). If only the quality agent had run, I'd have spent 20 minutes polishing the doomed abstraction.

  **How to apply:** For any diff >50 lines, spawn a reuse-scan agent FIRST (or alongside quality/efficiency) with the question *"does an existing helper/adapter/convention already solve this in this codebase?"* — and read its findings before acting on the others. If reuse finds a better abstraction, scrap the diff and restart from the adapter; do not layer polish on top of what you're about to delete.

- **[2026-04-19] Preflight scope MUST match deploy scope.** If a path is excluded from what ships, it must also be excluded from what gets validated. Coherence between the two is a correctness property, not a performance optimization.

  **Why:** `scripts/deploy-theme.sh` had `vendor/`, `node_modules/`, `tests/` in its rsync/tar exclude lists (they never ship), AND in `.phpcs.xml` (they don't get style-checked), AND in `.gitignore` (they're not tracked) — but the preflight PHP syntax check walked the theme with a plain `find -name '*.php'` and no prunes. Result: 3,881 files linted per deploy when only 124 are actually shipped. Cost: ~5–6 min per deploy for vendor/ alone, multiplied by every deploy for the life of the project. This isn't slow — it's incoherent. The lint was validating code that would never run in production.

  **How to apply:** For any validation step (lint, test, type-check, security scan) in a deploy/build script, reference the same exclude list the transport layer uses. If the tarball excludes `vendor/`, the lint must prune `vendor/`. If the zip skips `node_modules/`, the type-check must skip `node_modules/`. Ideal implementation: one source-of-truth array that both the transport and every validator consume. When scope diverges, silently-wrong work accumulates (and deploys get slow as a symptom). Treat divergence as a bug, not a performance issue. [bug-058]

- **[2026-04-24] Elite Studio `THREE_D_MODEL` LangGraph node bypasses the Claude SDK immersive agents.** `three_d_model_node` (`skyyrose/elite_studio/creative/nodes.py`) calls `ai_3d.generation_pipeline.ThreeDGenerationPipeline` directly. `SDKGarment3DAgent`, `SDKSceneBuilderAgent`, and `SDKAvatarStylistAgent` in `agents/claude_sdk/domain_agents/immersive.py` are a parallel orphaned implementation — never invoked by any LangGraph node. The `rationale_for` edge graphify drew between `creative/__init__.py` and `claude_sdk/domain_agents/` is docstring-level only ("3D models" appears in both module docstrings), not a code import. Closing this gap requires wiring `three_d_model_node` to `SDKGarment3DAgent`.

- **[2026-04-24] Local `adk/` module is the Elite Studio agents' actual ADK layer.** All 11 agents in `skyyrose/elite_studio/agents/` do `from adk.super_agents import BaseSuperAgent` — this resolves to DevSkyy's own `adk/` package at the project root, which lazily wraps `google.adk.agents.Agent` via `adk/google_adk.py`. The full chain: Elite Studio agent → local `BaseSuperAgent` → `adk.google_adk.GoogleADKAgent` → `google.adk.agents.Agent`. Use `.venv-agents/` (Python 3.14.3, `google-adk 1.30.0`, `google-genai 1.73.1`) to run any code in this chain — the main `.venv/` has numpy conflicts that block ADK installs.

## Do-Not-Repeat

<!-- Mistakes made and corrected. Each entry prevents the same mistake recurring. -->
<!-- Format: [YYYY-MM-DD] Description of what went wrong and what to do instead. -->
- [2026-04-15] Never import from root `agent_sdk/` — it no longer exists. Use `from sdk.python.agent_sdk.X import Y`.
- [2026-04-15] Never create `agents/base_super_agent.py` as a flat file — the package at `agents/base_super_agent/` is authoritative and Python will silently ignore the .py if you recreate it anyway.
- [2026-04-24] **Local imports inside a function body are NOT patchable via `unittest.mock.patch`.** If a name (`GeneratorAgent`, `MeshyClient`, etc.) is imported inside `async def generate_replica()`, it has no module-level attribute — `patch("module.Name")` raises `AttributeError: module does not have attribute 'Name'`. Fix: move the import to module top-level. The patch target must be `"the_module_where_it_is_used.ClassName"`, not `"the_module_where_it_is_defined.ClassName"`.
- [2026-04-24] **`Path(__file__).parents[N]` depth in `skyyrose/elite_studio/tests/conftest.py`**: `conftest.py` is at `.../DevSkyy/skyyrose/elite_studio/tests/conftest.py`. `parents[0]`=`tests/`, `parents[1]`=`elite_studio/`, `parents[2]`=`skyyrose/`, `parents[3]`=`DevSkyy/`. Use `parents[3]` to reach the project root and then `"wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv"`. Using `parents[4]` resolves to `/Users/theceo/` and the path silently doesn't exist.
- [2026-04-24] **ADK "promotion" anti-pattern gutted working synchronous agents.** Phase 16 replaced `PromptEnrichmentAgent`, `SafetyAgent`, and `UpscalingAgent` real implementations with `async def` stubs that only called `await self.execute(adk_prompt)`. Tests were written for the sync API; calling `async def` without `await` returns a coroutine object — every `result.success` access raises `AttributeError: 'coroutine' object has no attribute 'success'`. Fix: restore sync `def` implementations with the private methods (`_enrich`, `_check`, `_upscale`) that tests monkeypatch. Never "promote" a working agent to ADK inheritance without simultaneously updating its test contract.
- [2026-04-24] **`scripts/meshy_verified_generation.py` was a hazardous duplicate.** It wrapped a sync `requests`-based call instead of using the production `MeshyClient` in `ai_3d/providers/meshy.py`. Every rate-limit guard, backoff, and error handler was bypassed. The file was deleted (Phase 16 fix). If a session regenerates it or imports from `scripts.meshy_verified_generation`, that is a regression — use `MeshyClient` directly.
- [2026-04-24] **`graphify-out/graph.json` uses `links` not `edges`.** networkx's JSON export uses the key `links` for edge data (not `edges`). Any BFS/traversal script reading that file must use `g['links']`, not `g['edges']` — the latter raises `KeyError` silently if you don't check.
- [2026-04-24] **Local `adk/` module ≠ PyPI `google-adk`.** `from adk.super_agents import BaseSuperAgent` in Elite Studio agents resolves to DevSkyy's own `adk/` package (project root), NOT Google's PyPI package. That local module lazily wraps `google.adk.agents.Agent` inside a try/except. Don't confuse the two layers — installing `google-adk` affects `adk/google_adk.py`'s internals, but the Elite Studio import chain itself goes through `adk/`.
- [2026-04-24] **`google-genai 1.73.0` has a circular import on Python 3.14.** Symptom: `ImportError: cannot import name 'is_mapping_t' from partially initialized module 'google.genai._interactions._utils'`. Fix: upgrade to `google-genai>=1.73.1`. Downgrading to 1.16.x is blocked because `google-adk>=1.4.0` requires `google-genai>=1.72.0`. The fix command: `pip install "google-adk>=1.4.0"` pulls 1.73.1 automatically.

- **2026-04-27** — Drafted a TRELLIS.2 deployment handoff that cited `pipelines/skyyrose_master_orchestrator.py` as the integration point. The file was deleted in commit `f25fd25d3` ("Phase B1 scorched earth"). I had sourced the reference from MEMORY.md notes that hadn't been pruned. **Rule:** before citing a file path or class name in any doc/handoff/plan that another agent will execute against, verify with `ls`/`find`/`grep`. MEMORY.md is for concepts and constraints; treat its file paths as hints, not facts. Same principle the project's own catalog warning encodes ("Memory rots; the CSV doesn't").

- **2026-04-27** — `memory-audit.py` had a path-shadowing bug: `build_path_index()` walked into `.claude/worktrees/` (stale Claude Code worktree snapshots), letting deleted files like `pipelines/skyyrose_master_orchestrator.py` resolve via worktree copies and pass the audit. **Rule:** any whole-tree indexer for staleness detection MUST exclude isolation/snapshot directories — `.claude/worktrees/`, `.git/worktrees/`, `.archive/`, anything that holds historical complete trees. Pruning at walk time (in `INDEX_SKIP_DIRS`) is preferable to filtering at resolve time. Fixed by adding `worktrees` to `INDEX_SKIP_DIRS`. Separate latent bug noted in same module: `LINECOUNT_RE.search(line)` returns first match only, applies one count to all paths on multi-claim lines (e.g., MEMORY.md line 108) — needs `findall` per-path-claim binding.

- **2026-04-28** — Three CRITICAL broken asset references survived in production for an unknown duration: `footer.php` pointed to `assets/images/sr-monogram.png`; `seo.php` pointed to `sr-monogram-hero.png` and `sr-monogram-favicon.png` — all non-existent. Root cause: `assets/branding/` directory was organized at some point but PHP reference strings were never updated to match. The broken refs silently 404'd on every page (footer image + every social OG card + site favicon). **Rule:** after any asset reorganization that moves files to a new directory, immediately grep the entire theme for the old path segment and update all references in one atomic commit. The pattern `grep -r "assets/images/sr-monogram" --include="*.php"` would have caught all three in 1 second. Moving files without moving their references is the most silent class of breakage in WP themes because WordPress silently returns the broken template — no 500, no PHP error, just invisible missing elements.

- **2026-05-11** — Tripo `generate_multiview_image` template hallucinated branding on 30 SKUs (120 renders) because the dispatch boundary had no guard. The template runs FLUX.1 Kontext with NO prompt, NO logo overlay, NO dossier branding spec — naked image-to-multiview. Symptoms (verified by reading 3 outputs): br-001 black-rose crewneck rendered with FLUX-prior "rose-on-cloud" embroidery instead of the canonical black-rose three-rose-cluster; br-011 hockey jersey rendered as a cyan/teal hoodie with invented crests (different garment type entirely); sg-007 signature beanie got an off-canon patch sewn to the wrong location. Same "rose-on-cloud" motif appeared on three unrelated SKUs — FLUX defaulted to a training-set prior because no canon anchored it. **Rule:** Tripo's `generate_multiview_image` is for UNBRANDED CLEAN TECH-FLATS only. NEVER dispatch a SKU through it when (a) the dossier's `logo_reference` frontmatter is populated, or (b) the catalog `image` column is empty (forces fallback to `front_model_image`, a model-on shot the template can't preserve). Branded SKUs route through `agents/render_pipeline/` (ADK 9-step with logo overlay + 3-judge QA + refine loop). `scripts/tripo_dispatch.py` now enforces both guards at the dispatch boundary with a `--force-branded` escape hatch that prints a WARNING. See `renders/output/tripo/QUARANTINE.md` for the full RCA and which outputs to discard.

## Decision Log

<!-- Significant technical decisions with rationale. Why X was chosen over Y. -->
- [2026-04-15] Chose `sdk/python/agent_sdk/` as SDK source of truth over root `agent_sdk/` — root copy had stale brand data ("Where Love Meets Luxury" tagline, missing EliteStudio integration). All internal imports converted to relative to make the package location-independent.
- [2026-04-16] Compositor pipeline (`skyyrose/elite_studio/agents/compositor_agent.py`) commercial retrofit — chose **instrument-first** (read-only per-stage telemetry via `elite_studio/telemetry.py` → `logs/compositor-telemetry-YYYY-MM-DD.jsonl`) over proposed schema/breaker/cache refactor. **Why:** 40% token-reduction and 3-retry breaker claims are estimates until we have baseline unit economics. Two weeks of telemetry converts the retrofit from "optimization theatre" into a defensible CFO-grade business case. **Trade-off:** zero behavior change ships slower than a full refactor, but eliminates the risk of breaking the revenue-critical drop pipeline on speculative gains. Retrofit waves 2–4 (schema pinning, `forward_qa_verdict`, idempotent content-hash cache, per-stage circuit breaker) gated on telemetry data. [cmem #533]

## Project Conventions (updated 2026-04-27)

### AGENTS.md — Component-Scoped Agent Guides

- **Pattern**: Each major component directory now has an `AGENTS.md` (NOT `CLAUDE.md`) that agents read first before working in that directory.
- **Why**: Keeps the global CLAUDE.md uncluttered; gives each specialized agent a focused workspace brief with explicit permissions and safeguards.
- **AGENTS.md locations**:
  - `wordpress-theme/skyyrose-flagship/inc/AGENTS.md` — PHP modules, enqueue, SEO, WC hooks
  - `wordpress-theme/skyyrose-flagship/template-parts/AGENTS.md` — PHP partials
  - `wordpress-theme/skyyrose-flagship/assets/css/AGENTS.md` — CSS token system, collection styles
  - `wordpress-theme/skyyrose-flagship/assets/js/AGENTS.md` — Vanilla JS (nav, holo, toast, etc.)
  - `wordpress-theme/skyyrose-flagship/assets/js/experiences/AGENTS.md` — Three.js immersive worlds
  - `frontend/app/AGENTS.md` — Next.js App Router pages
  - `frontend/components/AGENTS.md` — React components (shadcn/ui, Tailwind)
  - `frontend/lib/AGENTS.md` — TypeScript types, API clients, config
- **Structure every AGENTS.md must have**: Isolated Workspace → Infrastructure → File/Module Map → Permissions → Safeguards → Mandatory Quality Workflow (lint → /simplify → /verification-loop) → Do NOT list

### Infrastructure (2026-04-27 confirmed)

- `skyyrose.co` = WordPress.com Business plan — no wp-cli, SFTP deploy only (script or SSH), no direct DB
- `devskyy.app` = Vercel, Next.js 16, React 19, npm (NOT pnpm)
- These are two fully independent systems — no shared auth, sessions, or database

### Deploy Options (WordPress theme)

- Script: `bash scripts/deploy-theme.sh` (atomic hot-swap, microsecond swap window)
- SSH: `sftp sftp.wp.com` (manual file upload)
- Both require explicit user confirmation before execution

### Context7-First Coding Protocol (added 2026-04-29)
Before writing or modifying ANY code that touches an external library, SDK, or API:
1. `mcp__claude_ai_Context7__resolve-library-id` → get the library ID
2. `mcp__claude_ai_Context7__query-docs` → pull the relevant section
3. Verify the method signatures, model IDs, and parameters against live docs
4. THEN write the code

This applies to: google-genai / Gemini SDK, FLUX API clients, httpx, Pydantic, LangGraph, any library not in stdlib.
Goal: eliminate fix cycles caused by outdated or assumed API knowledge — spend tokens on features, not corrections.
- **2026-04-29** — Wrote code changes to `audit_filter.py` and `vision_audit_agent.py` WITHOUT first running Context7 to verify the Gemini REST API pattern. The fixes themselves were correct (pure string logic), but the workflow was wrong. **Rule: Context7 `resolve` + `query-docs` is MANDATORY before every task that touches any external library — not just pipeline/workflow tasks. Every task. No exceptions.**
