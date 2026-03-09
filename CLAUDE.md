# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands

```bash
# Python backend
uvicorn main_enterprise:app --host 0.0.0.0 --port 8000 --reload
python devskyy_mcp.py                    # MCP server

# Frontend (Next.js 16)
npm run dev                              # Dev server
npm run build && npm start               # Production

# Install
make install                             # Python production deps
make dev                                 # Python + TypeScript dev deps
pip install -e ".[all]"                  # All optional deps
```

## Test Commands

```bash
make test                                # Python: pytest tests/ -v --tb=short
make test-fast                           # Python: pytest -x -q (stop on first failure)
make test-cov                            # Python: pytest with coverage report
pytest tests/unit/test_foo.py -v         # Single test file
pytest tests/ -k "test_name" -v          # Single test by name
pytest tests/ -m integration             # By marker: unit, integration, security, smoke, slow
make ts-test                             # TypeScript: jest
make test-all                            # Both Python + TypeScript
```

## Lint & Format

```bash
make format                              # Python: isort . && ruff check --fix && black .
make lint                                # Python: ruff check . && mypy
make format-all                          # Python + TypeScript
make lint-all                            # Python + TypeScript
make ci                                  # Full local CI (lint-all + test-all)
npm run type-check                       # TypeScript type checking
npm run lint                             # ESLint
```

## Verify After Changes

```bash
pytest tests/ -v && mypy . --ignore-missing-imports && ruff check .
npm run type-check && npm run lint
```

## Architecture

**8-layer platform** for AI-driven luxury fashion e-commerce (SkyyRose brand).

```
API (FastAPI REST + GraphQL)  →  Security (JWT, OAuth2, AES-256-GCM)
         ↓
Agents (54 specialized)  →  Orchestration (RAG, LangGraph, CrewAI)
         ↓
Services (ML, 3D, Analytics)  →  LLM Providers (6: OpenAI, Anthropic, Google, Mistral, Cohere, Groq)
         ↓
Core (auth, cache, events, registry — zero external deps)
```

**Dependency flow is one-way:** `core → security → database/llm → orchestration/services → agents → api`

### Key Entry Points
- `main_enterprise.py` — FastAPI app (47+ REST endpoints, GraphQL, webhooks)
- `devskyy_mcp.py` — MCP server (20+ tools)
- `frontend/` — Next.js 16 + React 19 + Three.js (5 immersive 3D collection experiences)
- `skyyrose/elite_studio/` — Multi-agent coordinator: VisionAgent (Gemini+OpenAI) → GeneratorAgent (Gemini) → QualityAgent (Claude)
- `pipelines/` — FLUX orchestrator, master pipeline, luxury pipeline
- `agents/base_super_agent.py` — EnhancedSuperAgent base class (17 prompt techniques)

### Key Directories
- `core/` — Foundation layer (registry, caching, events, feature flags, CQRS) — no external deps
- `agents/` — 54 agents (wordpress_bridge, elite_web_builder, visual_generation)
- `api/v1/` — REST routes; `api/graphql/` — schema + dataloaders
- `orchestration/` — RAG pipeline, LangGraph workflows, asset pipeline
- `services/ml/` — Stable Diffusion, ControlNet, DreamBooth; `services/three_d/` — Tripo3D, Meshy
- `integrations/` — WordPress client, Cloudflare R2, product sync
- `mcp_tools/` — MCP tool implementations
- `scripts/` — 171 utility scripts

### Virtual Environments
- `.venv` — main (diffusers, torch)
- `.venv-imagery` — image processing (rembg, BRIA)
- `.venv-lora` — LoRA training
- `.venv-agents` — ADK (conflicts with numpy, must be separate)

## Development Protocol

1. **Context7** → `resolve-library-id` → `query-docs` BEFORE writing any library code (WordPress, Three.js, WooCommerce)
2. Read existing code first, then `Edit` (targeted) or `Write` (new files only)
3. TDD: RED → GREEN → IMPROVE
4. `pytest -v` after EVERY change — target 85%+ coverage
5. Format: `isort . && ruff check --fix && black .`
6. After corrections → add Learnings entry below, commit fix + learning together

## Critical Rules

- Files <800 lines, functions <50 lines
- Immutability: `{...obj, key}` not `obj.key = val`
- No hardcoded secrets — use env vars
- Generic errors to clients, detailed logs server-side only
- Validate inputs with Zod (frontend) / Pydantic (backend) at system boundaries
- Git messages: `<type>: <description>` (feat, fix, refactor, docs, test, chore)
- Python line length: 100 (black + ruff + isort all configured to match)
- Use npm not pnpm for Vercel deploys (ERR_INVALID_THIS on Node 22+)

## WordPress Rules

- Extend via hooks (actions/filters), never modify core
- API: `index.php?rest_route=` NOT `/wp-json/`
- Escape on output (`esc_html()`, `esc_attr()`), sanitize on input (`sanitize_text_field()`)
- Always `$wpdb->prepare()` — never concatenate untrusted input
- Nonce + capability checks on all write actions
- Only theme: `skyyrose-flagship` in `wordpress-theme/`
- Read templates before assuming purpose: Immersive = 3D storytelling, Catalog = product grids
- Catalog templates: `template-collection-{black-rose,love-hurts,signature,kids-capsule}.php`

## Learnings

### Architecture
- Use `agents/base_super_agent.py` (not legacy files)
- DataLoaders → `api/graphql/dataloaders/` (not `core/`)
- `strawberry.argument()`: only `description`, `name`, `deprecation_reason`
- Use `schema.execute()` for GraphQL unit tests
- Integration tests → `tests/integration/` (not `tests/api/`)

### Google ADK
- Agent names: underscores only (valid Python identifiers)
- Loop per-product with `time.sleep(8)` to avoid 429s
- Prepend `"READ-ONLY AUDIT"` to audit prompts
- Load authoritative keys LAST with `override=True`
- `session_svc.create_session_sync()` before `runner.run()`
- Use `.venv-agents/` (ADK conflicts with numpy)

### Security
- Validate backend URLs against allowlist; block `169.254.x.x`, `file://`, `gopher://`
- Cap in-memory tracking with LRU eviction (`OrderedDict.popitem(last=False)`)
- Whitelist config keys before `**unpacking`

### Mocking
- Import deps at module level so `patch("module.Class")` works
- Fixed in: `core/cqrs/command_bus.py`, `grpc_server/product_service.py`

### Vercel
- `rootDirectory` set → reads that dir's `vercel.json`, not root

### Hooks
- macOS: canonicalize paths (`/tmp` → `/private/tmp`)
- Use `${VAR:-default}` for testable paths
- Reject flag-like targets: `case "$target" in -*) exit 0 ;; esac`

### Cache
- `cache_invalidate` and main key must use same hash length (fixed `multi_tier_cache.py:295`)

## Brand

- Colors: `#B76E79` rose gold, `#0A0A0A` dark, `#C0C0C0` silver, `#DC143C` crimson, `#D4AF37` gold
- Tagline: "Luxury Grows from Concrete."
- Collections: Black Rose, Love Hurts, Signature (Immersive 3D), Kids Capsule (Catalog)
- Health endpoints: `/health` `/health/ready` `/health/live` `/metrics`

## Self-Correction

1. Fix the issue → 2. Add Learnings entry above → 3. Commit both together
