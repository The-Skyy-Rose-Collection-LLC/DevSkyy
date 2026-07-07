# DevSkyy Codemaps Index

<!-- Generated: 2026-07-06 | Files scanned: 6 codemaps + repo root scan | Token estimate: ~450 -->

**Status: STAGED FOR APPROVAL.** This is a full rewrite of the codemap set (previous headers dated 2026-02-19, ~140 days stale, predating major repo growth). Files live in `docs/CODEMAPS/.pending/` — not yet promoted to `docs/CODEMAPS/`. See `.reports/codemap-diff.txt` for the full diff.

## Available Codemaps

| Codemap | Covers |
|---|---|
| [architecture.md](architecture.md) | System diagram, 3 independent deployables, backend dependency flow |
| [backend.md](backend.md) | FastAPI (`main_enterprise.py` + `api/v1/*`), GraphQL, `core`/`security`/`llm`/`orchestration`/`services`/`agents` |
| [frontend.md](frontend.md) | Next.js 16 dashboard (`frontend/`), `proxy.ts` auth gate, legacy `src/` SDK |
| [wordpress.md](wordpress.md) | `skyyrose-flagship` theme templates, `inc/` modules, `.min` build discipline |
| [data.md](data.md) | Catalog CSV + dossiers, SOT imagery resolution, Alembic models, asset hub |
| [dependencies.md](dependencies.md) | External services: WooCommerce, WP.com, Vercel, OAI gpt-image-2, Pinecone, Meshy/Tripo, LLM providers |

## Three independent systems — never cross-wire

1. **Python API** (repo root) — `main_enterprise.py` (Docker/Fly) or `api/index.py` (Vercel serverless mirror)
2. **Next.js dashboard** (`frontend/`) — devskyy.app on Vercel
3. **WordPress theme** (`wordpress-theme/skyyrose-flagship/`) — skyyrose.co, deployed via SFTP

All three read the same canonical product data (`skyyrose-catalog.csv` + dossiers + `sot-images.json`, registered in `SOT.md`) but never call into each other's admin APIs directly.

## Repository scale (verified this pass)

- `agents/`: 218 Python files (root CLAUDE.md's "54 agents" figure predates the `core/` 8-domain hierarchy, `claude_sdk/domain_agents/`, `elite_web_builder/`, and `render_pipeline/` additions)
- `api/`: 25 top-level modules + `api/v1/` (30 modules, 3 subpackages) + `api/v2/` (5, new) + `api/graphql/`
- `llm/providers/`: 11 adapter files — root CLAUDE.md's "6 providers" claim is stale (adds deepseek, replicate, stability, vertex_imagen, litellm_provider) — see [dependencies.md](dependencies.md)

## Staleness warning

Previous codemaps (`docs/CODEMAPS/{INDEX,backend,frontend}.md`) carry a `2026-02-19` "Last Updated" header (git shows the files were last touched 2026-06-12 without the header being bumped) — 137+ days stale by header date. They predate `database/`, `orchestration/`, `eval/`, `skyyrose/`, `aos/`, and most of `api/v1/`.
