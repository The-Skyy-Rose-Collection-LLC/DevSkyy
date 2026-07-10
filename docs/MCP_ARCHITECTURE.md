# DevSkyy MCP Architecture

## System Overview

<!-- AUTO-GENERATED: current MCP wiring — from mcp_service.py, http_mount.py, .mcp.json (2026-07-10) -->
> **Current wiring (2026-07-10) — read this before the diagram and server sections below.**
> DevSkyy ships **one** first-party MCP server: the **devskyy MCP** (82 tools live / 96 defined),
> served both as **stdio** (`devskyy_mcp.py`) and **streamable HTTP** at `/mcp`
> (`mcp_tools/http_mount.py` → `mcp_service:app`, bearer-auth via `MCP_SERVICE_TOKEN`, Python 3.12).
> It is **not** split into `devskyy-openai` + `devskyy-main`; OpenAI is a set of **tools inside**
> that one server (e.g. `devskyy_oai_render_*`) plus the 6-provider LLM router — not a standalone
> server. Third-party MCP servers (filesystem, sequential-thinking, etc.) are **developer-configured
> per scope**, not shipped by DevSkyy — the project `.mcp.json` currently wires only `aidesigner` +
> `gemini-api-docs-mcp`. **The `devskyy-openai` / `devskyy-main` split, the "Standard MCP Servers"
> roster, and the diagram below are historical/aspirational**, kept for design reference.
<!-- /AUTO-GENERATED -->

```
┌─────────────────────────────────────────────────────────────────┐
│                      AI Assistants Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Claude     │  │   ChatGPT    │  │  Other MCP   │          │
│  │   Desktop    │  │   Desktop    │  │   Clients    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
                    Model Context Protocol
                             │
┌─────────────────────────────┴─────────────────────────────────┐
│                      MCP Servers Layer                         │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │           DevSkyy Custom MCP Servers                   │   │
│  │  ┌──────────────────┐    ┌──────────────────┐         │   │
│  │  │ devskyy-openai   │    │  devskyy-main    │         │   │
│  │  │                  │    │                  │         │   │
│  │  │ • GPT-4o         │    │ • 54 AI Agents   │         │   │
│  │  │ • Vision         │    │ • WordPress      │         │   │
│  │  │ • Code Gen       │    │ • WooCommerce    │         │   │
│  │  │ • Functions      │    │ • SEO/Content    │         │   │
│  │  └──────────────────┘    └──────────────────┘         │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │           Standard MCP Servers                         │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │filesystem│ │   git    │ │  github  │ │ postgres │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │sequential│ │  brave   │ │  fetch   │ │  memory  │  │   │
│  │  │ thinking │ │  search  │ │          │ │          │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  └────────────────────────────────────────────────────────┘   │
└────────────────────────────┬───────────────────────────────────┘
                             │
┌────────────────────────────┴───────────────────────────────────┐
│                    DevSkyy Platform Layer                      │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              Core Platform Services                    │   │
│  │  ┌──────────────────┐    ┌──────────────────┐         │   │
│  │  │  FastAPI Server  │    │  Agent Registry  │         │   │
│  │  │  (Port 8000)     │    │  (54 Agents)     │         │   │
│  │  └──────────────────┘    └──────────────────┘         │   │
│  │  ┌──────────────────┐    ┌──────────────────┐         │   │
│  │  │  LLM Orchestrator│    │  WordPress Client│         │   │
│  │  └──────────────────┘    └──────────────────┘         │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              Data & Storage Layer                      │   │
│  │  ┌──────────────────┐    ┌──────────────────┐         │   │
│  │  │   PostgreSQL     │    │      Redis       │         │   │
│  │  │   Database       │    │      Cache       │         │   │
│  │  └──────────────────┘    └──────────────────┘         │   │
│  └────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Example: WordPress Product Creation

```
1. User Request (Claude Desktop)
   ↓
2. MCP Protocol
   ↓
3. devskyy-main Server
   ↓
4. wordpress_agent Tool
   ↓
5. DevSkyy FastAPI Server
   ↓
6. WordPress REST API
   ↓
7. WooCommerce Product Created
   ↓
8. Response → MCP → Claude → User
```

### Example: Code Generation with Vision

```
1. User: "Analyze this design and generate code"
   ↓
2. MCP Protocol
   ↓
3. devskyy-openai Server
   ↓
4. GPT-4o Vision Analysis
   ↓
5. Code Generation Tool
   ↓
6. filesystem Server (write code)
   ↓
7. git Server (commit changes)
   ↓
8. Response → MCP → Claude → User
```

## MCP Server Details

### DevSkyy Custom Servers

#### devskyy-openai

- **Technology**: FastMCP + OpenAI SDK
- **Models**: GPT-4o, GPT-4o-mini, o1-preview
- **Transport**: stdio (MCP standard) **+ streamable HTTP** — the same FastMCP tool registry is now also mounted at `/mcp` over HTTP (Bearer-token gated; see [Security Architecture](#security-architecture))
- **Tools**: 7 specialized tools
- **Use Cases**: Complex reasoning, vision, code generation

#### devskyy-main

- **Technology**: FastMCP + DevSkyy API
- **Agents**: the DevSkyy agent fleet — 8 core domains via `agents/core/factory.py` (`_CORE_AGENT_REGISTRY`) plus legacy `EnhancedSuperAgent` domain agents; **count is dynamic and grows — never hardcoded** (query `devskyy_list_agents` or `GET /api/v1/agents`)
- **Transport**: stdio (local, `devskyy_mcp.py` via `.mcp.json`) **+ streamable HTTP** (`mcp_tools/http_mount.py` mounts the same FastMCP instance at `/mcp`, served by `mcp_service:app`; Bearer-token gated, see [Security Architecture](#security-architecture))
- **Tools**: 96 `@mcp.tool` handlers defined across 24 modules in `mcp_tools/` (runtime-registered count is env-dependent — some modules are gated on optional dependencies; exposed live via the `/health` endpoint's `tool_count` field). Largest modules: external_mcp (18), wc_client (11), resources (8), rag (6), claude_sdk (6), wp_deploy (5), lora_generation (5), elite_studio (5), lora_training (4), virtual_tryon (4), orchestration (4).
- **Use Cases**: E-commerce automation, content creation

### Standard MCP Servers

#### filesystem

- **Provider**: @modelcontextprotocol/server-filesystem
- **Scope**: /Users/coreyfoster/DevSkyy
- **Operations**: read, write, search, list
- **Security**: Sandboxed to project directory

#### git

- **Provider**: @modelcontextprotocol/server-git
- **Repository**: /Users/coreyfoster/DevSkyy
- **Operations**: status, diff, log, commit, branch
- **Security**: Read-only by default

#### github

- **Provider**: @modelcontextprotocol/server-github
- **Authentication**: GitHub Personal Access Token
- **Operations**: issues, PRs, workflows, search
- **Rate Limits**: GitHub API limits apply

#### postgres

- **Provider**: @modelcontextprotocol/server-postgres
- **Connection**: postgresql://localhost/devskyy
- **Operations**: queries, schema inspection
- **Security**: Configurable read-only mode

#### sequential-thinking

- **Provider**: @modelcontextprotocol/server-sequential-thinking
- **Purpose**: Extended chain-of-thought reasoning
- **Use Cases**: Complex problem solving, planning

#### brave-search

- **Provider**: @modelcontextprotocol/server-brave-search
- **Authentication**: Brave API Key
- **Operations**: web search, news search
- **Rate Limits**: Brave API limits apply

#### fetch

- **Provider**: @modelcontextprotocol/server-fetch
- **Operations**: HTTP requests, web scraping
- **Security**: Configurable allowed domains

#### memory

- **Provider**: @modelcontextprotocol/server-memory
- **Storage**: Persistent across conversations
- **Use Cases**: Context retention, preferences

## Security Architecture

### Authentication Flow

```
┌──────────────┐
│ AI Assistant │
└──────┬───────┘
       │ 1. Request with env vars
       ↓
┌──────────────┐
│  MCP Server  │
└──────┬───────┘
       │ 2. Validate API keys
       ↓
┌──────────────┐
│ DevSkyy API  │
└──────┬───────┘
       │ 3. JWT authentication
       ↓
┌──────────────┐
│   Resource   │
└──────────────┘
```

<!-- AUTO-GENERATED: HTTP transport auth — from mcp_tools/http_mount.py -->
### HTTP Transport Authentication (`/mcp`)

The streamable-HTTP mount (`mcp_tools/http_mount.py`, served by `mcp_service:app`) sits behind its own gate, separate from the JWT flow above:

- **Token**: a single shared Bearer token in env var `MCP_SERVICE_TOKEN`.
- **Enforced**: in every non-dev environment `MCP_SERVICE_TOKEN` is REQUIRED. `BearerAuthMiddleware` rejects any request missing `Authorization: Bearer <token>` with HTTP 401 and JSON body `{"error":"unauthorized",...}`.
- **Local dev**: if the token is unset, enforcement is skipped and a warning is logged — a deployed, reachable `/mcp` is never silently open (`http_mount.py` lines 7-10, 20, 46, 50-53).
- **Comparison**: timing-safe (`hmac.compare_digest`), so a plain `!=` timing leak is avoided.
- Mutation gating for individual write-tools stays a separate, tool-level concern — this Bearer check is the coarse network gate in front of the whole registered tool set.
<!-- /AUTO-GENERATED -->

### Security Layers

1. **Environment Variables**: API keys stored securely
2. **MCP Protocol**: Encrypted communication
3. **JWT Tokens**: API authentication
4. **MCP Bearer Token**: shared-secret (`MCP_SERVICE_TOKEN`) gate on the HTTP `/mcp` mount (see above)
5. **RBAC**: Role-based access control
6. **Rate Limiting**: Prevent abuse
7. **Sandboxing**: Filesystem access restricted

## Performance Optimization

### Caching Strategy

```
┌─────────────┐
│ AI Request  │
└──────┬──────┘
       │
       ↓
┌─────────────┐     Cache Hit
│   Memory    │────────────────→ Fast Response
│   Server    │
└──────┬──────┘
       │ Cache Miss
       ↓
┌─────────────┐
│ MCP Server  │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  DevSkyy    │
│  Platform   │
└─────────────┘
```

### Load Balancing

- **Concurrent Requests**: Up to 5 per server
- **Timeout**: 60 seconds default
- **Retry Logic**: 3 attempts with exponential backoff
- **Circuit Breaker**: Automatic failover

## Monitoring & Observability

### Metrics Collected

- Request count per server
- Response time (p50, p95, p99)
- Error rate
- Memory usage
- Active connections

### Logging

```
~/Library/Logs/Claude/
├── mcp-devskyy-openai.log
├── mcp-devskyy-main.log
├── mcp-filesystem.log
├── mcp-git.log
└── mcp-*.log
```

### Health Checks

- **Endpoint**: /health (where applicable)
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3

## Deployment Scenarios

### Development

- Local MCP servers
- Claude Desktop integration
- Hot reload enabled
- Debug logging

### Production

<!-- AUTO-GENERATED: Fly topology — from fly.toml, fly.backend.toml, Dockerfile.mcp -->
Two independent Fly.io apps. The naming is counterintuitive — **`devskyy-backend` is the REST API, `devskyy-api` is the MCP server** — do not swap them:

- **`devskyy-backend`** (`fly.backend.toml` → `Dockerfile.api`) — the FastAPI REST + GraphQL backend, serves `main_enterprise` (public at `api.devskyy.app`).
- **`devskyy-api`** (`fly.toml` → `Dockerfile.mcp`) — the slim, single-machine MCP-only service, serves `mcp_service:app` (Python 3.12, `python:3.12-slim`, no ML/torch stack). Exposes only `/mcp`, `/health`, `/ready`; container `CMD python -m uvicorn mcp_service:app --host 0.0.0.0 --port 8000`, `EXPOSE 8000`, healthcheck `curl -f http://localhost:8000/health`. 82 MCP tools verified live in the 2026-07-09 deployment (of 96 defined — see [MCP Server Details](#mcp-server-details)).
<!-- /AUTO-GENERATED -->

- Containerized MCP servers
- Load balancer
- Production logging
- Monitoring enabled

### CI/CD

- Automated testing
- MCP server validation
- Integration tests
- Performance benchmarks

---

**Version**: 1.0.0
**Last Updated**: 2026-07-10 (dual-transport HTTP mount, bearer auth, Fly topology, tool count)
**Maintained by**: The Skyy Rose Collection LLC
