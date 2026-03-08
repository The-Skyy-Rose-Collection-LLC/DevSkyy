# DevSkyy Architecture Codemap

> Freshness: 2026-03-03 | Monorepo: Python + Next.js + WordPress

## System Overview

```
DevSkyy Monorepo
├── Python Backend (FastAPI + gRPC + Event Sourcing)
├── Next.js 16 Frontend (React 19, Turbopack, App Router)
├── WordPress Theme (skyyrose-flagship v3.2.0)
├── 189 Scripts (AI/ML, deployment, training, utilities)
└── 54 AI Agents (commerce, content, imagery, operations)
```

## Dependency Flow (One-Way, Zero Circular)

```
CORE (zero deps)
  ↓
ADK / SECURITY / ORCHESTRATION
  ↓
API / AGENTS / LLM
  ↓
SERVICES (specialized implementations)
```

## Package Map

| Package | Files | Purpose |
|---------|-------|---------|
| `core/` | 40+ | Types, interfaces, caching, CQRS, events, feature flags |
| `database/` | 2 | SQLAlchemy 2.0 async ORM (User, Product, Order, EventRecord) |
| `security/` | 32 | AES-256-GCM, JWT/OAuth2, RBAC, audit, SSRF, PII, MFA |
| `orchestration/` | 27 | LLM routing, RAG pipeline, vector stores, prompt engineering |
| `llm/` | 25 | Multi-provider client (7 providers), round table, A/B testing |
| `adk/` | 9 | Agent Dev Kit (Google ADK, PydanticAI, CrewAI, AutoGen, Agno) |
| `agents/` | 40+ | 54 AI agents (commerce, content, imagery, security, support) |
| `api/` | 50+ | FastAPI REST v1, GraphQL (Strawberry), WebSockets, webhooks |
| `gateway/` | 1 | Circuit breaker, rate limiter, SSRF-safe routing |
| `analytics/` | 1 | Kafka stream processor, event aggregation |
| `grpc_server/` | 2 | ProductService (Get, List, Create, UpdatePrice) |
| `services/` | 10 | Approval queue, 3D providers, image enhancement |
| `frontend/` | 200+ | Next.js 16, 23 routes, 60+ components, 50+ API routes |
| `wordpress-theme/` | 150+ | 29 templates, 43 CSS, 29 JS, 22 inc/ modules |
| `scripts/` | 189 | AI/ML (42), deploy (30), train (18), upload (12), util (25) |

## Key Design Patterns

| Pattern | Location | Purpose |
|---------|----------|---------|
| Event Sourcing | `core/events/` | Immutable event log, replay for state |
| CQRS | `core/cqrs/` | Separate read/write paths |
| Multi-Tier Cache | `core/caching/` | L1 (TTLCache) + L2 (Redis), auto-promotion |
| Circuit Breaker | `gateway/` | 3-state FSM per route |
| Repository | `database/db.py` | Type-safe data access |
| Feature Flags | `core/feature_flags/` | Consistent hash rollout, kill switches |
| DataLoader | `api/graphql/dataloaders/` | N+1 prevention, request-scoped batching |

## Entry Points

| Entry | Command | Port |
|-------|---------|------|
| FastAPI | `uvicorn main_enterprise:app` | 8000 |
| gRPC | `python -m grpc_server.product_service` | 50051 |
| Frontend | `npm run dev` (in frontend/) | 3000 |
| AI CLI | `python scripts/ai.py` | — |
| MCP Server | `python mcp_tools/server.py` | — |

## Health Endpoints

- `GET /health` — Liveness
- `GET /health/ready` — Readiness
- `GET /health/live` — Live probe
- `GET /metrics` — Prometheus metrics
- `GET /api/monitoring/health` — Frontend health
- `GET /api/monitoring/metrics` — Frontend metrics

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, gRPC |
| Frontend | Next.js 16, React 19, Tailwind, Radix UI, Three.js |
| WordPress | PHP 8.x, WooCommerce, Elementor |
| AI/ML | Gemini, Claude, GPT-4, LoRA, CLIP, Replicate |
| Infra | Vercel, HuggingFace Spaces, Git LFS |
| Data | SQLite/PostgreSQL, Redis, ChromaDB, Pinecone |
| Auth | NextAuth.js, JWT/OAuth2, RBAC |
| Commerce | Stripe, WooCommerce |
