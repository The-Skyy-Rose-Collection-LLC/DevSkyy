# Seed Index: GSD Artifacts (`.planning/`)

**Phase 0 seeding date:** 2026-05-03
**Total files:** 105+ across directory
**How to use:** When a task matches a category, load the relevant artifact via `Read .planning/<path>`. These are pointer entries — the value is in the GSD files themselves. The Phase 14 PATTERNS.md is the single highest-value artifact for code patterns.

---

## Project Charter

### `.planning/PROJECT.md`
- **Covers:** SkyyRose imagery pipeline charter (v1.2 milestone). Core value statement: "skyyrose.co works flawlessly on every device, passes WCAG AA accessibility, and shows the right products in the right collections." Current milestone: CSV-driven ghost mannequin generation. Also covers v1.1 shipped features and validated requirements.
- **Relevant for:** Any session kickoff, understanding what the system was built to do, aligning new V2 work with the established architecture.
- `[planning: PROJECT.md]`

### `.planning/MILESTONES.md`
- **Covers:** Milestone definitions — v1.0 through v1.2, each milestone's goals, phases, and shipped deliverables.
- **Relevant for:** Phase planning, understanding what was delivered when.
- `[planning: MILESTONES.md]`

### `.planning/REQUIREMENTS.md`
- **Covers:** Formal requirements list with validation status. Cross-references CI, WooCommerce, accessibility, deployment, and imagery requirements.
- **Relevant for:** Any feature that must satisfy a requirement; checking "does X already satisfy REQ-NNN?"
- `[planning: REQUIREMENTS.md]`

### `.planning/ROADMAP.md`
- **Covers:** Project roadmap — phases 14–18 and beyond, with requirements and status per phase.
- **Relevant for:** Phase planning, understanding what phases 17–18 (Review & Approval CLI, Full Batch + WooCommerce upload) still need.
- `[planning: ROADMAP.md]`

---

## Codebase Map

### `.planning/codebase/ARCHITECTURE.md`
- **Covers:** High-level architecture: WP theme + Elite Studio + Vercel dashboard + Python API + Agent SDK layers.
- **Relevant for:** Understanding system boundaries, where code lives, cross-system data flows.
- `[planning: codebase/ARCHITECTURE.md]`

### `.planning/codebase/CONVENTIONS.md`
- **Covers:** Naming conventions (PascalCase components, camelCase hooks, kebab-case config), function naming (verb prefix for actions, noun prefix for queries), Prettier config (semi, singleQuote, printWidth: 120, trailingComma: es5).
- **Relevant for:** Any TypeScript/JavaScript code writing, component creation.
- `[planning: codebase/CONVENTIONS.md]`

### `.planning/codebase/CONCERNS.md`
- **Covers:** Tech debt and architectural concerns logged during milestones. Cross-references specific file-level issues.
- **Relevant for:** Before touching a file that might have known tech debt — check here first.
- `[planning: codebase/CONCERNS.md]`

### `.planning/codebase/INTEGRATIONS.md`
- **Covers:** Integration map — how the WordPress theme, Vercel, Python API, WooCommerce, and external services connect.
- **Relevant for:** Integration work, understanding HMAC bridge, Klaviyo/Stripe/Pinecone wiring.
- `[planning: codebase/INTEGRATIONS.md]`

### `.planning/codebase/STACK.md`
- **Covers:** Full technology stack enumeration — Python 3.11+, FastAPI, Next.js 16, React 19, WordPress, WooCommerce, Three.js, GSAP, LangGraph, CrewAI, etc.
- **Relevant for:** Dependency decisions, version constraints, "can we use X" questions.
- `[planning: codebase/STACK.md]`

### `.planning/codebase/STRUCTURE.md`
- **Covers:** Directory structure map — where each type of file lives in the repo.
- **Relevant for:** Finding files, understanding where new files should go.
- `[planning: codebase/STRUCTURE.md]`

### `.planning/codebase/TESTING.md`
- **Covers:** Testing strategy — pytest for Python, Jest for Next.js, Playwright for E2E, PHP syntax checks.
- **Relevant for:** Any test writing, CI pipeline understanding, 85%+ coverage target.
- `[planning: codebase/TESTING.md]`

---

## Research Findings

### `.planning/research/ARCHITECTURE.md`
- **Covers:** Architecture research — patterns investigated for multi-agent orchestration, LangGraph design choices.
- **Relevant for:** Agent orchestration design, LangGraph node patterns.
- `[planning: research/ARCHITECTURE.md]`

### `.planning/research/PITFALLS.md` ⭐ HIGH VALUE
- **Covers:** Domain pitfalls for the ghost mannequin AI imagery pipeline. Two critical pitfalls documented in depth:
  1. **Scorched-Earth Precedent** — wrong source data drove everything downstream; 16,950 lines deleted; root cause was prompts reading `data/product-specs.json` instead of CSV `branding_spec` column.
  2. **Bundle Directory Name Mismatches** — 17 of 30 products have directory names that don't match CSV names (em dashes vs hyphens, ALL CAPS vs title case, curly quotes vs plain, garment name differences). Plus 12 bundle dirs have no `techflat-front.jpeg`.
- **Relevant for:** ANY imagery pipeline work, batch generation runs, bundle directory resolution, prompt construction.
- `[planning: research/PITFALLS.md]`

### `.planning/research/STACK.md`
- **Covers:** Technology stack research — libraries investigated and chosen for the imagery pipeline.
- **Relevant for:** Library selection, understanding why specific versions were chosen.
- `[planning: research/STACK.md]`

### `.planning/research/LANGCHAIN-MODELS.md`
- **Covers:** LangChain/LangGraph model integration research — which models work with which nodes.
- **Relevant for:** LangGraph pipeline design, model selection for nodes.
- `[planning: research/LANGCHAIN-MODELS.md]`

### `.planning/research/FEATURES.md`
- **Covers:** Feature research notes — features investigated for the imagery pipeline.
- **Relevant for:** Feature planning, understanding what was considered and why some things were scoped out.
- `[planning: research/FEATURES.md]`

### `.planning/research/SUMMARY.md`
- **Covers:** Research summary — conclusions from the entire research phase.
- **Relevant for:** Understanding the research-to-decision pipeline; what the research phase concluded.
- `[planning: research/SUMMARY.md]`

---

## Patterns (Highest-Value Artifact)

### `.planning/phases/14-catalog-foundation/14-PATTERNS.md` ⭐ HIGHEST VALUE
- **Covers:** 579-line pattern map for Phase 14 (Catalog Foundation). Maps every new/modified file to its role, data flow, closest analog in the codebase, and match quality. Key patterns:
  - `__init__.py` package marker convention (one-line docstring minimum)
  - `nano_banana/catalog.py` shim pattern wrapping `skyyrose/core/catalog_loader.py`
  - Env-var override pattern for catalog path (`SKYYROSE_CATALOG_PATH`)
  - `bool_col()` / `int_col()` utilities for CSV boolean/int parsing
  - Test contract dictating exact output dict shape for `load_catalog()`
  - Preflight audit script pattern (file-I/O utility, dry-run first)
- **Relevant for:** Any new Python module that reads the catalog; any test that touches catalog data; any new package directory creation.
- `[planning: phases/14-catalog-foundation/14-PATTERNS.md]`

---

## Phase Records

### `.planning/STATE.md`
- **Covers:** Current GSD state: milestone v1.2, Phase 16 COMPLETED (3D Replica Architect & Purge). Phases 17 (Review & Approval CLI) and 18 (Full Batch + WooCommerce) are not started. Last activity: 2026-04-24.
- **Relevant for:** Understanding where the GSD pipeline left off; what Phase 17–18 will need when the V2 build activates those workstreams.
- `[planning: STATE.md]`

### `.planning/RETROSPECTIVE.md`
- **Covers:** Cross-milestone lessons. v1.1 key lessons: (1) read before writing — 2 of 5 plans needed 0 code changes; (2) defense-in-depth for PHP/WC dual paths; (3) continuation agents need explicit task tables to prevent hallucination; (4) gitignored assets need separate deploy tracking. Cross-milestone top lessons: extend don't replace, automated verification catches more than code review.
- **Relevant for:** Any multi-phase planning; understanding what process improvements worked.
- `[planning: RETROSPECTIVE.md]`

---

## Render Pipeline

### `.planning/render-pipeline-architecture.md`
- **Covers:** Architecture of the render pipeline — how ghost mannequin generation flows from CSV through pipeline to output.
- **Relevant for:** Pipeline design, understanding the Nano Banana + Elite Studio + FLUX orchestration.
- `[planning: render-pipeline-architecture.md]`

### `.planning/CLAUDE-SDK-INTEGRATION-PLAN.md`
- **Covers:** Claude SDK integration plan — how the Claude SDK agents connect to the Elite Studio pipeline.
- **Relevant for:** Claude SDK agent work, `SDKGarment3DAgent` integration, LangGraph wiring.
- `[planning: CLAUDE-SDK-INTEGRATION-PLAN.md]`

---

## Handoffs

### `.planning/handoffs/trellis2-deployment.md`
- **Covers:** TRELLIS.2 deployment handoff. Phase 1: fork Microsoft's HF Space to private `skyyrose` space (~3 hours, ~$0.40/hr). Phase 2: port to Modal serverless GPU, wire into `agents/trellis_agent.py` mirroring `agents/meshy_agent.py`. Active integration points: `creative/nodes.py:130` (`three_d_model_node`), `orchestration/threed_round_table.py:552` (tournament orchestrator). **CRITICAL NOTE:** `pipelines/skyyrose_master_orchestrator.py` was deleted in commit `f25fd25d3` — does not exist. All references to it in docs are stale.
- **Relevant for:** 3D generation pipeline work, TRELLIS.2 integration, any new 3D provider wiring.
- `[planning: handoffs/trellis2-deployment.md]`

---

## Highest-Leverage GSD Artifacts (read these before the relevant task type)

| Task type | Read first |
|-----------|-----------|
| Any imagery/generation/batch work | `.planning/research/PITFALLS.md` |
| Any new Python package/module | `.planning/phases/14-catalog-foundation/14-PATTERNS.md` |
| Any catalog reader / product data work | `.planning/phases/14-catalog-foundation/14-PATTERNS.md` |
| Multi-phase planning | `.planning/RETROSPECTIVE.md` |
| 3D generation / TRELLIS / Meshy / Tripo | `.planning/handoffs/trellis2-deployment.md` |
| Architecture decisions | `.planning/codebase/ARCHITECTURE.md` |
| TypeScript conventions | `.planning/codebase/CONVENTIONS.md` |
