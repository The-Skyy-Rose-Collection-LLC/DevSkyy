# database/

Scoped context for the DB layer. Loads on top of root.

## Hard rules

- **Alembic targets `agents/models.py`, NOT `database/db.py`.** `alembic/env.py:41` loads the model file directly via `importlib.util.spec_from_file_location`. `database/db.py` (modern `DeclarativeBase`) is a separate `Base` — changes to it do NOT appear in `alembic autogenerate`. New tables → `agents/models.py` (old-style `declarative_base()`), or they silently never migrate.
- **Async engine only.** All access goes through `async with db_manager.session() as session`. The FastAPI dependency is `get_db()` (`database/db.py:701`), yielding an `AsyncSession`. No synchronous session code — pool is `NullPool` for async (prevents "QueuePool cannot be used with asyncio engine").
- **`DatabaseManager` is a singleton** (`db.py:282`) — `__new__` returns the shared instance. Call `DatabaseManager()`; never monkey-patch `_instance` or call `__init__` directly.
