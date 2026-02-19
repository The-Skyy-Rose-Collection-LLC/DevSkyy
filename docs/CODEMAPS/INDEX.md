# DevSkyy Codemaps Index

**Last Updated:** 2026-02-19
**Source of Truth:** Repository structure, `package.json`, `.env.example`

## What Are Codemaps?

Codemaps provide navigable, high-level overviews of each major area of the DevSkyy codebase. They are generated from the actual code structure and kept under 500 lines each.

## Available Codemaps

| Codemap | Covers | Location |
|---------|--------|----------|
| [Frontend](frontend.md) | TypeScript SDK, React components, 3D collections, Next.js dashboard | `docs/CODEMAPS/frontend.md` |
| [Backend](backend.md) | Python FastAPI, agents, security, LLM providers, MCP server | `docs/CODEMAPS/backend.md` |

## Repository Overview

```
DevSkyy/                         # v3.0.0 - AI orchestration platform
|-- main_enterprise.py           # FastAPI entry point (47+ endpoints)
|-- devskyy_mcp.py               # MCP server (13 tools, 54 agents)
|-- package.json                 # Node.js config (28 scripts)
|-- .env.example                 # Environment variable template
|
|-- core/                        # Foundation layer (zero outer deps)
|-- security/                    # AES-256-GCM, JWT, audit, zero-trust
|-- agents/                      # 54 AI agents (SuperAgent base)
|-- llm/                         # 6 LLM providers + tournament router
|-- api/                         # REST endpoints, webhooks, dashboard
|-- services/                    # ML, 3D, analytics, notifications
|
|-- src/                         # TypeScript SDK
|   |-- collections/             # 5 Three.js 3D experiences
|   |-- components/              # React Three Fiber components
|   |-- lib/                     # Cart, checkout, Stripe, materials
|   |-- hooks/                   # React hooks (cart, scroll, filters)
|   |-- services/                # Agent, OpenAI, ThreeJS services
|   `-- types/                   # TypeScript type definitions
|
|-- frontend/                    # Next.js dashboard application
|-- wordpress-theme/             # SkyyRose WordPress theme
|   `-- skyyrose-flagship/       # Production theme
|
|-- tests/                       # unit/, integration/, e2e/
|-- docs/                        # 90+ documentation files
|-- config/                      # TypeScript, Jest, Vite configs
`-- scripts/                     # Utility and deployment scripts
```

## Dependency Flow

```
Core (auth, registry, runtime) -- zero dependencies on outer layers
  |
  v
Security, Database, LLM Providers
  |
  v
Orchestration, Services (ML, 3D, analytics)
  |
  v
Agents (54 specialized, SuperAgent base)
  |
  v
API (FastAPI REST, WebSocket, MCP)
```

## Key Entry Points

| Entry Point | Technology | Purpose |
|-------------|-----------|---------|
| `main_enterprise.py` | FastAPI (Python) | Backend API server |
| `devskyy_mcp.py` | FastMCP (Python) | MCP tool server |
| `src/index.ts` | TypeScript | SDK exports |
| `frontend/` | Next.js | Dashboard UI |
| `wordpress-theme/skyyrose-flagship/` | PHP | Production WordPress theme |

## Related Documentation

- [CONTRIB.md](../CONTRIB.md) -- Development workflow and setup
- [RUNBOOK.md](../RUNBOOK.md) -- Deployment and operations
- [SCRIPTS_REFERENCE.md](../SCRIPTS_REFERENCE.md) -- NPM scripts reference
- [ENV_VARS_REFERENCE.md](../ENV_VARS_REFERENCE.md) -- Environment variables
- [ARCHITECTURE.md](../ARCHITECTURE.md) -- System architecture
