# Seed Index: OpenWolf System (`.wolf/`)

**Phase 0 seeding date:** 2026-05-03
**Primary files:** `.wolf/cerebrum.md` (110 lines), `.wolf/buglog.json` (95 bugs, 1,552 lines)
**How to use:** When diagnosing a recurring failure, query buglog by tag first. When generating code, load cerebrum.md Do-Not-Repeat + Key Learnings before writing. These are pointer entries — the value is in the source files.

---

## cerebrum.md — Section Map

Full path: `/Users/theceo/DevSkyy/.wolf/cerebrum.md`

### Source of Truth (lines ~1–15)

- Canonical product data: `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`
- Retired files (do not resurrect): `catalog.yaml`, `manifest.json`, `generate_catalog.py`, `sync_manifest_from_catalog.py` (all 2026-04-19), plus `skyyrose/assets/data/prompts/overrides/` (2026-04-25, hallucination source)
- `[wolf: cerebrum.md:1]`

### Key Learnings (lines ~16–60)

| Date | Entry | Cross-ref |
|------|-------|-----------|
| 2026-04-15 | Python packaging: every top-level package dir needs `__init__.py` — mypy has `namespace_packages=False` and will silently resolve the same file under two module names without it | `[wolf: cerebrum.md:17]` |
| 2026-04-16 | SDK canonical import path: `from sdk.python.agent_sdk...` (not `from agent_sdk...`) — agent_sdk is a submodule of the monorepo | `[wolf: cerebrum.md:28]` |
| 2026-04-17 | `agents/base_super_agent/` is a **package directory** (not a flat .py file) — Python silently ignores `base_super_agent.py` if the package exists; never create a flat-file shim | `[wolf: cerebrum.md:35]` |
| 2026-04-18 | Integration tests live in `tests/integration/` (not `tests/api/`) — `tests/api/` is for API unit tests only | `[wolf: cerebrum.md:40]` |
| 2026-04-18 | Audit-abstraction-first principle: add instrumentation + metrics before enforcing gates — measure, then enforce | `[wolf: cerebrum.md:44]` |
| 2026-04-19 | Preflight scope must match deploy scope — if deploy excludes `vendor/`, preflight must too, or lint takes 5+ min on vendor PHP files | `[wolf: cerebrum.md:48]` |
| 2026-04-24 | Elite Studio `THREE_D_MODEL` node can be bypassed when the Creative node returns a score above threshold — not a bug, by design | `[wolf: cerebrum.md:52]` |
| 2026-04-24 | `local adk/ module ≠ PyPI google-adk` — the local `adk/` directory shadows the PyPI package; ADK work needs `.venv-agents/` to avoid import conflicts | `[wolf: cerebrum.md:56]` |
| 2026-04-27 | `front-page.php` uses `wc_get_products()` for per-collection counts — must be replaced with `skyyrose_get_collection_products()` from `inc/product-catalog.php` | `[wolf: cerebrum.md:60]` |

### Do-Not-Repeat (lines ~62–95)

These are confirmed past mistakes — check this list before generating code in the affected domains.

| Date | Rule | Cross-ref |
|------|------|-----------|
| 2026-04-15 | Never create `agents/base_super_agent.py` as a flat file — it silently shadows the package directory | `[wolf: cerebrum.md:63]` |
| 2026-04-16 | Never import from `agent_sdk` directly — use `sdk.python.agent_sdk` (wrong-reference bug cluster: bug-033, 035, 036, 037, 038) | `[wolf: cerebrum.md:67]` |
| 2026-04-17 | Never read `branding_spec` from `data/product-specs.json` — that file was the root cause of the scorched-earth rebuild (16,950 lines deleted). Read from `dossier_loader` only | `[wolf: cerebrum.md:72]` `[cmem #581]` |
| 2026-04-18 | Never place integration tests in `tests/api/` — they go in `tests/integration/` | `[wolf: cerebrum.md:76]` |
| 2026-04-19 | Never re-reference retired files: `catalog.yaml`, `manifest.json`, overrides JSONs, `pipelines/skyyrose_master_orchestrator.py` — all deleted | `[wolf: cerebrum.md:80]` |
| 2026-04-24 | Never install `google-adk` into the main `.venv/` — use `.venv-agents/` to avoid numpy conflicts | `[wolf: cerebrum.md:84]` |
| 2026-04-27 | Never call `wc_get_products()` in templates to fetch catalog data — use `skyyrose_get_collection_products()` from `inc/product-catalog.php` | `[wolf: cerebrum.md:88]` |
| 2026-04-28 | Never create `.venv-imagery/` — it was an early design that was never built. Nano Banana shares the main `.venv/` | `[wolf: cerebrum.md:92]` |

### Decision Log (lines ~96–110)

| Date | Decision | Cross-ref |
|------|----------|-----------|
| 2026-04-17 | Instrument-first over circuit-breaker: add telemetry before fidelity enforcement in Elite Studio compositor | `[wolf: cerebrum.md:97]` `[cmem #572]` |
| 2026-04-27 | AGENTS.md convention adopted: component-level agent guides live in `AGENTS.md` (not `CLAUDE.md`) within each component directory | `[wolf: cerebrum.md:104]` |

---

## buglog.json — Tag Index

Full path: `/Users/theceo/DevSkyy/.wolf/buglog.json`
**Total bugs logged:** 95 (IDs bug-001 to bug-095, with some ID collisions from manual entries)
**Date range:** 2026-04-07 to 2026-05-03

### Tag Distribution (top tags — "look here for X")

| Tag | Count | What it covers |
|-----|-------|----------------|
| `auto-detected` | 82 | All automatically-detected bugs (super-set; combine with domain tag to narrow) |
| `py` | 41 | Python bugs — async/await, wrong refs, refactors in elite_studio, queue, sdk |
| `refactor` | 31 | Files edited 2+ times in a session (auto-flagged by OpenWolf) |
| `wrong-value` | 19 | Hardcoded wrong values — PHP template SKUs, JS logic, deploy script vars |
| `php` | 10 | WordPress theme PHP bugs — enqueue, functions.php, template wrong values |
| `wrong-reference` | 10 | Wrong import paths, wrong symbol names (biggest cluster: `agent_sdk` → `sdk.python.agent_sdk`) |
| `js` | 9 | JavaScript bugs — mascot, 3D experience, smart-showcase error handling |
| `deploy` | 7 | `scripts/deploy-theme.sh` bugs — preflight scope, concurrency, rollback, credential exposure |
| `sh` | 7 | Shell script bugs — deploy script series |
| `md` | 7 | Markdown plan files auto-flagged (mostly noise) |
| `async-fix` | 7 | Missing `async`/`await` in Python and YAML configs |
| `error-handling` | 6 | Missing try/catch or error handling in `after_compositor`, closeDialog, etc. |

### Domain Lookup ("Where do I look for X?")

| Scenario | Tags to search | Key bugs |
|----------|---------------|----------|
| Deploy script fails / slow | `deploy`, `sh` | bug-058 through bug-065 (deploy cluster) |
| PHP template has wrong product data | `php`, `wrong-value`, `catalog` | bug-091, bug-092 |
| Python async errors | `async-fix`, `py` | bug-004, bug-005, bug-057, bug-066, bug-068 |
| Import errors in Python | `wrong-reference`, `py` | bug-033, bug-035–038 |
| Elite Studio / compositor Python | `py`, `refactor` (elite_studio path) | bug-047, bug-051, bug-052 |
| Security / credential leaks | `security`, `credential-exposure` | bug-064 |
| JavaScript event listener errors | `typeerror`, `javascript`, `event-listener` | bug-093 |
| Missing asset / 404 | `missing-file`, `404` | bug-094 |
| Voyage rate limiting | `voyage`, `rate-limit` | bug-095 |

### Deploy Script Bug Cluster (highest density, 2026-04-19)

Seven bugs were filed against `scripts/deploy-theme.sh` in a single day:
- **bug-058**: PHP lint walks `vendor/` — 5–6 min preflight (`deploy`, `preflight`, `lint-scope`, `find-prune`)
- **bug-059**: No concurrency guard — parallel deploys race on `.old.$swap_id` (`concurrency`, `race-condition`, `flock`)
- **bug-060**: No auto-rollback when `verify_live()` fails (`rollback`, `verify`, `safety`)
- **bug-061**: `.old.$swap_id` deleted immediately — no rollback anchor (`rollback`, `retention`, `bounded-disk`)
- **bug-062**: `verify_live()` only checked homepage — CSS/JS breakage silent (`verify`, `asset-integrity`, `observability`)
- **bug-063**: `tar -czf` compresses already-compressed media (WebP/GLB/JPG) — CPU waste (`compression`, `zstd`)
- **bug-064**: `SSHPASS` exported for full deploy duration — credential exposure (`security`, `credential-exposure`, `sshpass`)

---

## Other .wolf/ Files

| File | What it contains | Token estimate |
|------|-----------------|----------------|
| `.wolf/anatomy.md` | 2-3 line description + token estimate for every file in the repo | ~2,500 |
| `.wolf/memory.md` | Session-by-session action log (timestamp, description, files, outcome) | ~1,500 |
| `.wolf/claude-mem-digest.md` | Last 25 claude-mem observations synced at SessionStart | ~800 |
| `.wolf/OPENWOLF.md` | Operating protocol (rules that govern OpenWolf behavior) | ~600 |
| `.wolf/hooks/claude-mem-sync.sh` | Shell script that syncs claude-mem → digest at session start | ~50 |

**When to load each:**
- `anatomy.md` — always check before opening any file; saves redundant reads
- `memory.md` — when you need "what happened in the last session" context
- `claude-mem-digest.md` — when you need cross-session memory beyond what's in cerebrum

---

## Highest-Leverage OpenWolf Reads

| Task type | Read first |
|-----------|------------|
| Any Python code generation | `.wolf/cerebrum.md` Do-Not-Repeat (lines 62–95) |
| Any deploy script work | `.wolf/buglog.json` tag: `deploy` + `sh` |
| Any catalog/SKU work | `.wolf/cerebrum.md` Source of Truth (lines 1–15) |
| Debugging async/import errors | `.wolf/buglog.json` tags: `async-fix`, `wrong-reference` |
| Any WordPress template work | `.wolf/buglog.json` tags: `php`, `wc_get_products` |
| Any Elite Studio pipeline work | `.wolf/cerebrum.md` Key Learnings + Decision Log |
