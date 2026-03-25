# Architecture

**Analysis Date:** 2026-03-07

## Pattern Overview

**Overall:** Multi-layered Python FastAPI backend with Next.js frontend, organized around domain-driven services with agent orchestration.

**Key Characteristics:**
- FastAPI-based REST API with versioned endpoints (`/v1/`)
- Multi-agent orchestration system for AI-driven workflows
- Repository pattern for data access with SQLAlchemy 2.0 async
- Event-driven architecture with event bus for inter-service communication
- Service registry for dependency injection
- CQRS pattern for command/query separation

## Layers

**API Layer:**
- Purpose: HTTP request handling, validation, authentication
- Location: `api/`
- Contains: FastAPI routers, request/response models, WebSocket handlers
- Depends on: Services layer, core auth
- Used by: Frontend, external clients

**Services Layer:**
- Purpose: Business logic orchestration, external API integration
- Location: `services/`
- Contains: ML services (enhancement, 3D generation), storage, analytics, notifications
- Depends on: Database, core, orchestration
- Used by: API layer, agents

**Orchestration Layer:**
- Purpose: Multi-agent coordination, LLM routing, RAG pipelines
- Location: `orchestration/`
- Contains: Agent orchestration, LLM clients, vector stores, document ingestion
- Depends on: LLM providers, core services
- Used by: Services, agents

**Agents Layer:**
- Purpose: Specialized AI agents for domains (commerce, creative, marketing, security, etc.)
- Location: `agents/`
- Contains: Agent implementations, toolkits, base classes
- Depends on: Core, orchestration, services
- Used by: API endpoints, orchestration workflows

**Core Layer:**
- Purpose: Shared infrastructure (auth, caching, telemetry, DI, events)
- Location: `core/`
- Contains: Auth models, service registry, event bus, caching, telemetry
- Depends on: Third-party libraries only
- Used by: All layers

**Database Layer:**
- Purpose: Data persistence, query optimization
- Location: `database/`
- Contains: SQLAlchemy models, session management, migrations (alembic)
- Depends on: SQLAlchemy, asyncpg/aiosqlite
- Used by: Services, API

**LLM Layer:**
- Purpose: Unified LLM client abstraction, provider management
- Location: `llm/`
- Contains: LLM clients, providers (OpenAI, Anthropic, Google, etc.), routing, evaluation
- Depends on: External LLM APIs
- Used by: Orchestration, agents

**Frontend Layer:**
- Purpose: Next.js React application for admin dashboard and storefront
- Location: `frontend/`
- Contains: Pages, components, API clients, state management
- Depends on: Backend API
- Used by: End users, admins

## Data Flow

**API Request Flow:**

1. Client sends request to `api/v1/<resource>`
2. Router validates request using Pydantic models
3. Authentication middleware validates JWT token (from `core/auth/`)
4. Service layer executes business logic
5. Database layer persists/retrieves data via Repository pattern
6. Response returned through same chain

**Agent Execution Flow:**

1. API triggers orchestration workflow (`api/v1/orchestration`)
2. LLM orchestrator routes task to appropriate agent(s)
3. Agent executes with tools from toolkit registry
4. Results fed back through event bus
5. WebSocket pushes updates to frontend

**Asset Processing Flow:**

1. Upload to `/api/v1/assets` triggers processing job
2. Queue receives job (`services/ml/processing_queue.py`)
3. Enhancement pipeline runs (background removal, upscaling, etc.)
4. Results stored in R2 storage (`services/storage/r2_client.py`)
5. Webhook notifies completion

## Key Abstractions

**Service Registry:**
- Purpose: Dependency injection container
- Examples: `core/registry/service_registry.py`
- Pattern: Singleton and factory registration with lazy initialization

**Event Bus:**
- Purpose: Decoupled inter-service communication
- Examples: `core/events/event_bus.py`, `core/events/event_handlers.py`
- Pattern: Publish-subscribe with typed events

**CQRS:**
- Purpose: Command/query separation
- Examples: `core/cqrs/command_bus.py`, `core/cqrs/query_bus.py`
- Pattern: Separate handlers for mutations vs reads

**Repository Pattern:**
- Purpose: Data access abstraction
- Examples: `core/repositories/interfaces.py`, `database/db.py`
- Pattern: Async SQLAlchemy sessions with Repository classes

**LLM Provider Factory:**
- Purpose: Unified LLM interface across providers
- Examples: `core/llm/infrastructure/provider_factory.py`, `llm/providers/`
- Pattern: Factory with adapter pattern for OpenAI, Anthropic, Google, etc.

**Agent Base Classes:**
- Purpose: Common agent functionality
- Examples: `agents/base_super_agent.py`, `agents/base_legacy.py`
- Pattern: Inheritance hierarchy with tool registration

## Entry Points

**Main Application:**
- Location: `main_enterprise.py`
- Triggers: `uvicorn main_enterprise:app`
- Responsibilities: FastAPI app initialization, lifespan management, middleware setup, router registration

**Serverless API:**
- Location: `api/index.py`
- Triggers: Vercel serverless function
- Responsibilities: Lightweight FastAPI app for serverless deployment

**MCP Server:**
- Location: `devskyy_mcp.py`
- Triggers: MCP protocol connection
- Responsibilities: Model Context Protocol tool exposure

**Frontend:**
- Location: `frontend/app/`
- Triggers: Next.js dev server or production build
- Responsibilities: React pages, API proxy, authentication

## Error Handling

**Strategy:** Centralized error handling with custom exception types

**Patterns:**
- Custom exceptions in `agents/errors.py` and `core/`
- HTTPException for API-level errors
- Global exception handler in FastAPI app
- Structured logging with correlation IDs

## Cross-Cutting Concerns

**Logging:** Structured logging via `core/structured_logging.py` with context injection

**Validation:** Pydantic models throughout (request/response), `core/runtime/input_validator.py`

**Authentication:** JWT-based with role hierarchy, `core/auth/` module with token management

**Caching:** Multi-tier caching in `core/caching/`, Redis integration

**Telemetry:** OpenTelemetry tracing in `core/telemetry/`, optional Sentry integration

---

*Architecture analysis: 2026-03-07*
