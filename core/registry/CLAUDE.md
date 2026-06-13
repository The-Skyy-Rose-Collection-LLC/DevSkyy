# core/registry/ — Service Registry (DI Container)

**Thread-safe singleton service locator.** Replaces global module-level mutation for cross-cutting dependencies (ML pipeline, RAG manager, DB pool, cache provider).

## Public Surface (`core/registry/__init__.py`)

- `ServiceRegistry` — singleton class, `__new__` double-checked-locking (`service_registry.py:101-112`)
- `ServiceNotFoundError` — raised by `.get()` when service missing
- `register_service(name, instance=..., factory=..., lazy=False)` — convenience wrapper around global registry
- `get_service(name)` — convenience wrapper

## Patterns (`service_registry.py:114`)

| Mode | Use | Example |
|------|-----|---------|
| Singleton | Pre-built instance reused | `register("db", instance=engine)` |
| Factory (eager) | New instance each `.get()` | `register("temp_dir", factory=lambda: tempfile.mkdtemp())` |
| Factory (lazy) | One instance, built on first access | `register("ml_pipeline", factory=load_model, lazy=True)` |

## Hard Rules

- **Singleton survives the process** — tests MUST call `registry.clear()` between cases or state leaks
- Service names: lowercase snake_case strings (`"ml_pipeline"`, `"rag_manager"`, `"cache_provider"`)
- Lazy factories use double-checked locking (`service_registry.py:82-88`) — safe under contention
- `get()` raises `ServiceNotFoundError`; `get_or_none()` returns `None` for optional services
- Use `is_registered(name)` for guards; do not catch `ServiceNotFoundError` for control flow

## Consumers

- `main_enterprise.py` startup — registers core services (DB, cache, ML pipeline)
- `agents/base_super_agent/agent.py` — resolves `rag_manager` / `ml_pipeline` via `get_service()`
- Tests in `tests/integration/` — `pytest fixture` calls `registry.clear()` in teardown

## Registered Service Specs

See `registrations.py` for the canonical list of standard service names and shapes consumed across the app


