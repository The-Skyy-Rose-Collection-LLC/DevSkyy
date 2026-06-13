# core/ — Foundation Layer

**Zero-dependency foundation.** Provides shared types, interfaces, and DI primitives that every outer layer (`api/`, `agents/`, `services/`, `pipelines/`) consumes.

## Dependency Rule (HARD)

`core` MUST NOT import from `api/`, `security/`, `agents/`, or `services/`. Only depends on stdlib + `pydantic`. Violating this re-introduces the circular imports `core/` was created to break (`core/__init__.py:16`).

Outer layers depend on `core` abstractions. Implementations live elsewhere.

## Public Surface (lazy-loaded)

`core/__init__.py:29` lazy-loads `agents`, `auth`, `registry`, `repositories`, `services` via `__getattr__`. Other subpackages (caching, cqrs, events, errors, feature_flags, llm, middleware, runtime, telemetry, middleware) must be imported explicitly.

| Subpackage | Purpose | Tier |
|------------|---------|------|
| `auth/` | TokenPayload, UserRole, JWT contracts (zero security/ dep) | 1 |
| `caching/` | L1 (TTLCache) → L2 (Redis) multi-tier cache + `@cached` decorator | 1 |
| `events/` | Event sourcing — append-only store + in-process bus | 1 |
| `registry/` | Thread-safe DI singleton — `register_service()` / `get_service()` | 1 |
| `cqrs/` | Command and query buses (separate write/read paths) | 1 |
| `errors/` | `DevSkyError` hierarchy + correlation IDs for distributed tracing | 1 |
| `feature_flags/` | Runtime flag manager + global `flag_manager` | 1 |
| `middleware/` | FastAPI ASGI middleware (tenant resolution) | 1 |
| `llm/` | Hexagonal shim — domain ports + provider factory wrapping `llm/` | 1 |
| `agents/` | `IAgent`, `ISuperAgent`, `IAgentOrchestrator` Protocols | 1 |
| `repositories/` | `IRepository`, `IUserRepository`, `IProductRepository` | 1 |
| `services/` | `IRAGManager`, `IMLPipeline`, `ICacheProvider` | 1 |
| `runtime/` | `ToolRegistry`, `BUILTIN_TOOLS` (consolidated tool execution) | 2 |
| `telemetry/` | OTel tracer (`init_telemetry`, `get_tracer`) | 2 |

## Top-Level Modules (not yet promoted to subpackages)

- `performance.py` (~4.6k tok) — perf instrumentation utilities
- `product_spec.py` — **single source of truth** for product specs across all pipelines
- `redis_cache.py` — LLM response Redis cache (pre-multi-tier; new code uses `core/caching/`)
- `structured_logging.py` — `structlog` context-var helpers (`bind_contextvars`, etc.)
- `task_status_store.py` — async job status (GET endpoint)
- `token_tracker.py` — LLM token + cost tracker

## Rules

- New code MUST consume `core.caching.MultiTierCache`, NOT `core.redis_cache` (legacy)
- Cost tracking: any new LLM call must record via `core.token_tracker`
- Errors raised by `core/` modules MUST inherit `DevSkyError` (`core.errors.DevSkyError`)
- Singletons (registry, event_bus, flag_manager) survive the process — tests MUST `.clear()` between cases


