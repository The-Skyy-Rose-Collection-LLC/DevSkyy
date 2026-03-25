# Codebase Structure

**Analysis Date:** 2026-03-07

## Directory Layout

```
/Users/theceo/Devskyy/
├── api/                    # FastAPI routers and handlers
├── agents/                 # AI agent implementations
├── alembic/                # Database migrations
├── analytics/              # Analytics services
├── cli/                    # Command-line tools
├── config/                 # Configuration loading
├── core/                   # Shared infrastructure
├── database/               # Database layer
├── dev/                    # Development utilities
├── errors/                 # Error handling
├── examples/               # Example code
├── frontend/               # Next.js frontend
├── gateway/                # API gateway
├── grpc_server/            # gRPC services
├── imagery/                # Image processing
├── integrations/           # External integrations
├── llm/                    # LLM clients and providers
├── logs/                   # Log files
├── mcp_servers/            # MCP server implementations
├── mcp_tools/              # MCP tools
├── ml/                     # Machine learning utilities
├── models/                 # Trained models
├── monitoring/             # Monitoring services
├── orchestration/          # Workflow orchestration
├── pipelines/              # Data pipelines
├── scripts/                # Utility scripts
├── security/               # Security utilities
├── services/               # Business logic services
├── skyyrose/               # SkyyRose-specific implementations
├── sync/                   # Synchronization utilities
├── tasks/                  # Task definitions
├── tests/                  # Test suites
├── tools/                  # Tool definitions
├── utils/                  # General utilities
├── main_enterprise.py      # Main application entry
├── devskyy_mcp.py          # MCP server entry
├── api/index.py           # Serverless API entry
├── pyproject.toml         # Python project config
├── package.json            # Node.js root config
└── frontend/               # Next.js project
```

## Directory Purposes

**api/:**
- Purpose: FastAPI HTTP handlers and routers
- Contains: REST endpoints, WebSocket handlers, GraphQL
- Key files: `index.py`, `v1/` (versioned endpoints), `graphql/`

**agents/:**
- Purpose: Domain-specific AI agents
- Contains: Agent implementations, toolkits, base classes
- Key files: `base_super_agent.py`, `coding_doctor_agent.py`, `creative_agent.py`, `marketing_agent.py`, `security_ops_agent.py`, `social_media_agent.py`

**core/:**
- Purpose: Shared infrastructure (no external dependencies except third-party libs)
- Contains: Auth, caching, telemetry, DI, events, repositories
- Key files: `registry/service_registry.py`, `auth/`, `events/event_bus.py`, `cqrs/`

**database/:**
- Purpose: Data persistence and migrations
- Contains: SQLAlchemy models, session management, seed data
- Key files: `db.py`, `seed_admin.py`, `query_optimizer.py`

**frontend/:**
- Purpose: Next.js web application
- Contains: React pages, components, API clients
- Key files: `app/` (App Router pages), `lib/` (utilities), `components/`

**llm/:**
- Purpose: LLM abstraction and provider management
- Contains: Unified client, provider adapters, routing, evaluation
- Key files: `unified_llm_client.py`, `providers/`, `router.py`, `round_table.py`

**orchestration/:**
- Purpose: Multi-agent workflows and RAG pipelines
- Contains: Agent orchestration, vector stores, document ingestion
- Key files: `llm_orchestrator.py`, `vector_store.py`, `rag_context_manager.py`

**services/:**
- Purpose: Business logic and external service integration
- Contains: ML enhancement, 3D generation, storage, analytics, notifications
- Key files: `ml/`, `three_d/`, `storage/`, `analytics/`

## Key File Locations

**Entry Points:**
- `main_enterprise.py`: Production FastAPI server (`uvicorn main_enterprise:app`)
- `api/index.py`: Vercel serverless API
- `devskyy_mcp.py`: MCP protocol server

**Configuration:**
- `config/settings.py`: Central configuration with environment loading
- `pyproject.toml`: Python project metadata and dependencies
- `.env`, `.env.hf`: Environment variables (secrets)

**Database:**
- `database/db.py`: SQLAlchemy setup and session management
- `alembic/`: Database migrations
- `database/seed_admin.py`: Initial admin user creation

**Testing:**
- `tests/`: Test suites (pytest)
- `frontend/tests/`: Frontend tests
- `conftest.py`: Pytest configuration

## Naming Conventions

**Files:**
- Python: `snake_case.py` (e.g., `service_registry.py`, `llm_client.py`)
- TypeScript/React: `kebab-case.tsx` or `PascalCase.tsx` for components
- Config: `snake_case.config.*` or `.prefixrc` (e.g., `.eslintrc.cjs`)

**Directories:**
- Python packages: `snake_case` (e.g., `core/auth`, `services/ml`)
- Frontend: `kebab-case` (e.g., `app/admin`, `lib/api`)

**Functions/Methods:**
- Python: `snake_case` (e.g., `get_user`, `process_image`)
- TypeScript: `camelCase` for functions, `PascalCase` for components

**Types/Classes:**
- Python: `PascalCase` (e.g., `ServiceRegistry`, `UserModel`)
- TypeScript: `PascalCase` for types and interfaces

## Where to Add New Code

**New API Endpoint:**
- Implementation: `api/v1/<domain>.py`
- Router registration: `api/v1/__init__.py`
- Request/Response models: Same file or `api/v1/schemas/`

**New Service:**
- Implementation: `services/<domain>/`
- Interface: `core/services/interfaces.py`
- Register in: Service registry or DI container

**New Agent:**
- Implementation: `agents/<agent_name>_agent.py`
- Base class: Extend `BaseSuperAgent` from `agents/base_super_agent.py`
- Tools: Register in agent's toolkit

**New LLM Provider:**
- Implementation: `llm/providers/<provider_name>.py`
- Factory registration: `core/llm/infrastructure/provider_factory.py`

**New Database Model:**
- Model definition: `database/db.py` or `database/models/`
- Migration: `alembic/versions/`

**New Frontend Page:**
- Implementation: `frontend/app/<path>/page.tsx`
- Components: `frontend/components/`
- API client: `frontend/lib/api/`

## Special Directories

**.claude/:**
- Purpose: Claude AI assistant configurations and skills
- Generated: No
- Committed: Yes

**node_modules/:**
- Purpose: npm dependencies
- Generated: Yes (by npm install)
- Committed: No (in .gitignore)

**.venv/, .venv-*/:**
- Purpose: Python virtual environments
- Generated: Yes
- Committed: No

**logs/:**
- Purpose: Application log files
- Generated: Yes (runtime)
- Committed: No

**coverage/:**
- Purpose: Test coverage reports
- Generated: Yes (by pytest)
- Committed: No

**alembic/:**
- Purpose: Database migration scripts
- Generated: Yes (by alembic commands)
- Committed: Yes

---

*Structure analysis: 2026-03-07*
