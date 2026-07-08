# Architecture Codemap

<!-- Generated: 2026-07-06 | Files scanned: ~90 top-level dirs + 6 entry points | Token estimate: ~700 -->

## Three independent systems (never cross-wire)

```
+----------------------+   +-----------------------+   +--------------------------+
| Python API (root)    |   | Next.js dashboard      |   | WordPress theme          |
| main_enterprise.py    |   | frontend/               |   | wordpress-theme/          |
| devskyy_mcp.py         |   | devskyy.app (Vercel)   |   | skyyrose-flagship/        |
| Docker / Fly deploy   |   | NextAuth admin gate     |   | skyyrose.co (SFTP)        |
+----------------------+   +-----------------------+   +--------------------------+
           \                          |                            /
            `--- shared read-only: skyyrose-catalog.csv + dossiers + sot-images.json
                                 (registered in SOT.md) ---'
```

## Backend dependency flow (Python API)

```
core/  (auth, caching, cqrs, errors, events, feature_flags, llm, middleware,
        registry, repositories, runtime, services, telemetry -- zero outer deps)
  |
  v
security/ (30 modules: AES-256-GCM, JWT/OAuth2, SSRF, zero-trust, secrets)
database/ (SQLAlchemy + Alembic, 3 migrations)   llm/ (11 provider adapters + router/tournament)
  |                                                     |
  v                                                     v
orchestration/ (33 modules: RAG, brand_learning, catalog_retriever, 3D round table)
services/ (analytics, competitive, forecasting, lifecycle, ml, notifications,
           personalization, risk, storage, three_d)
  |
  v
agents/ (218 .py files: base_super_agent.EnhancedSuperAgent, core/ 8-domain hierarchy,
          claude_sdk/domain_agents/, elite_web_builder/, render_pipeline/ ADK agent)
  |
  v
api/ (25 top-level + api/v1/ 30 modules + api/v2/ 5 + api/graphql/ Strawberry schema)
main_enterprise.py -- mounts api.v1 aggregator + individual routers + /graphql
```

## Adjacent subsystems

| Subsystem | Role |
|---|---|
| `aos/` | Experimental agent micro-kernel (kernel, governance/approval, healing, memory, IPC) — not wired into `main_enterprise.py`'s request path yet |
| `skyyrose/elite_studio/` | Canonical imagery pipeline hub — Meshy/TRELLIS/Tripo/FASHN wrapped as swappable engines |
| `scripts/oai_render/` | OAI gpt-image-2 render pipeline — current canonical new-render engine, replaces prior nano-banana path |
| `eval/` | Content/brand evaluation rulebook (banned-elements, commercial-protocols, luxury-references) feeding the QC judge |
| `devskyy_mcp.py` | MCP server exposing agents/WooCommerce/imagery/RAG tools to external MCP clients |

## Deploy targets

| Target | Command | Config |
|---|---|---|
| WordPress | `bash scripts/deploy-theme.sh` | `.env.wordpress` |
| Dashboard | `cd frontend && npm run deploy` | `vercel.json` |
| API | `docker compose up -d` | `docker-compose.yml` |
| API (serverless alt) | `api/index.py` on Vercel | Mirrors `main_enterprise.py` but mounts only 7 routers — the two entry points can drift |

## Related codemaps

[backend.md](backend.md) · [frontend.md](frontend.md) · [wordpress.md](wordpress.md) · [data.md](data.md) · [dependencies.md](dependencies.md)
