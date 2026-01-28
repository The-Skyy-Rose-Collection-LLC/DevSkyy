# DevSkyy Database

> Alembic migrations, async sessions | 8 files

## Architecture
```
database/
├── engine.py           # Async SQLAlchemy engine
├── session.py          # Session management
├── models.py           # ORM models
└── repositories/       # Data access layer
```

## Pattern
```python
class DatabaseManager:
    def __init__(self, url: str):
        self.engine = create_async_engine(url, pool_size=10, max_overflow=20)
        self.session_factory = async_sessionmaker(self.engine, class_=AsyncSession)

    @asynccontextmanager
    async def session(self):
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
```

## Migrations
```bash
alembic revision --autogenerate -m "Add table"  # Create
alembic upgrade head                             # Apply
alembic downgrade -1                             # Rollback
```

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change

## USE THESE TOOLS
- **MCP**: `analytics_query` | **Skill**: `backend-patterns`

**"Every migration is reviewed. Every rollback is planned."**
