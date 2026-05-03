# GEMINI.md - Project Context & Instructions

This document provides foundational context and operational mandates for the DevSkyy project.

## Project Overview
**DevSkyy** is an AI-driven luxury fashion e-commerce platform for the **SkyyRose** brand. It integrates high-end 3D experiences, multi-agent AI orchestration, and a seamless WordPress/WooCommerce backend.

### Core Stack
- **Backend:** Python 3.11+ (FastAPI, SQLAlchemy, Pydantic v2, LangGraph, Claude Agent SDK).
- **Frontend:** Next.js 16 (React 19, TypeScript), Three.js for immersive 3D collections.
- **CMS:** WordPress + WooCommerce (SkyyRose Flagship theme, REST API sync).
- **AI:** 6 SuperAgents (Commerce, Creative, Marketing, Support, Operations, Analytics) across 6 LLM providers (OpenAI, Anthropic, Google, Mistral, Cohere, Groq).
- **Infrastructure:** Docker, MCP (Model Context Protocol) server, gRPC, Kafka.

---

## Architecture (8-Layer platform)
1. **Presentation:** `api/`, `frontend/` (FastAPI + Next.js)
2. **AI Agents:** `agents/`, `agent_sdk/`, `prompts/`
3. **Orchestration/Services:** `orchestration/`, `services/`, `pipelines/`, `imagery/`, `ai_3d/`
4. **LLM/Integrations:** `llm/`, `integrations/`, `mcp_servers/`
5. **Database/Security:** `database/`, `security/`, `alembic/`
6. **Core:** `core/` (Auth, cache, events, errors, runtime)

**Dependency Rule:** `core → security → database/llm → orchestration/services → agents → api`

---

## Development Protocols

### 1. Anti-Hallucination & Research
- **Mandate:** "If you haven't read it, you don't know it." Always trace claims to tool calls.
- **Library Verification:** Before using ANY external library (e.g., `google-genai`, `httpx`, `pydantic`), you **MUST** read the source or verify signatures via documentation lookups.

### 2. Engineering Standards
- **File/Function Size:** Files < 800 lines, functions < 50 lines.
- **Immutability:** Prefer `{...obj, key: val}` over `obj.key = val`.
- **Validation:** Use **Pydantic** (backend) and **Zod** (frontend) at all system boundaries.
- **Error Handling:** Generic errors to clients, detailed structured logs server-side.
- **Python Style:** Line length 100. Use `isort`, `ruff`, and `black` for formatting.

### 3. WordPress Guidelines
- **Security:** Always use `esc_html()`, `esc_attr()`, `wp_kses_post()` for output and `$wpdb->prepare()` for SQL.
- **Hooks:** Extend via actions/filters; never modify core files.
- **No innerHTML:** Use `createElement` + `textContent` in JS.

---

## Commands & Workspaces

### Python API (Root)
```bash
make install          # Install all dependencies
make dev              # Install + dev tools
make test             # Run pytest
make format           # isort + ruff --fix + black
make lint             # ruff + black --check
make ci               # Full pipeline (lint + type + test)
mypy .                # Type check
```

### Dashboard (frontend/)
```bash
cd frontend
npm install           # Install deps
npm run dev           # Start dev server
npm run build         # Production build
```

### WordPress (wordpress-theme/skyyrose-flagship/)
```bash
bash scripts/deploy-theme.sh  # Deploy to production
```

---

## Behavioral Mandates
- **Direct Communication:** No conversational filler (e.g., "I'll now...", "Great!"). Start with the answer.
- **Tone:** Staff engineer to founder. Direct, specific, no hedging.
- **Act vs Ask:** 
    - **Ask if:** Action costs money, touches production (deploy, WC write), or is irreversible.
    - **Act if:** Reading files, writing code, running tests, or research.
- **Stop and Show:** For any action requiring confirmation, print the exact file path, cost, and action, then wait for "y".

---

## Key Entry Points
- `main_enterprise.py`: FastAPI application entry (REST + GraphQL).
- `devskyy_mcp.py`: MCP Server entry.
- `agents/base_super_agent/agent.py`: Base class for all AI agents.
- `frontend/src/index.ts`: Dashboard entry.

---

## Brand Identity
- **Tagline:** "Luxury Grows from Concrete."
- **Colors:** Rose Gold (`#B76E79`), Dark (`#0A0A0A`), Gold (`#D4AF37`), Silver (`#C0C0C0`), Crimson (`#DC143C`).
- **Typography:** Cinzel, Playfair Display, Cormorant Garamond, Bebas Neue, Inter.
