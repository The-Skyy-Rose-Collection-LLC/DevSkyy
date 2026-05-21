# core/services/ — Service ports (hexagonal interfaces)

Pure ABC surface. Defines the contracts that `services/` implementations must satisfy and that `orchestration/` + `agents/` depend on. No implementations live here — only the ports that keep the dependency arrow pointing outward.

## Key files

- `interfaces.py` — `IRAGManager` (async `get_context(query, ...)`, `ingest(documents)`), `IMLPipeline` (async `predict(input)`), `ICacheProvider` (async `get`, `set`, `delete`). All three are `abc.ABC` subclasses with `@abstractmethod` on every operation.
- `__init__.py` — Re-exports the three interfaces. The import surface is exactly these three names.

## Conventions

- Business logic depends on the interface, never on a concrete `services/` class. Constructor signatures take `IRAGManager` not `RAGManager`.
- New service capability lands here first as an ABC, then gets an implementation under `services/`. Reverse order breaks the layering.
- Method signatures accept primitives or Pydantic models — never framework-specific types (no `fastapi.UploadFile`, no SQLAlchemy `Session`). Keeping signatures framework-free is what makes the layer hexagonal.
- Async-only. All methods are coroutines so the implementation choice (Redis, in-memory, HTTP) does not leak into the call site.

## Don't

- Don't add implementation logic in `interfaces.py`. The whole file is `@abstractmethod`.
- Don't import from `services/`. That would invert the dependency and re-introduce the cycle `core/` was created to break (see `core/CLAUDE.md` Dependency Rule).
- Don't widen an interface without confirming every implementer in `services/` can satisfy the new method.
- Don't return ORM models or framework objects from interface methods — return plain dataclasses or Pydantic.

## Related

- `core/CLAUDE.md` — parent foundation layer
- `services/` — concrete implementations of these three ports
- `orchestration/` — composes services through these interfaces
- `core/repositories/CLAUDE.md` — sibling ports for data access
