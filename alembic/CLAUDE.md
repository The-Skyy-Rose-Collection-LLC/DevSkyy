# DevSkyy Alembic

> Zero-downtime migrations, rollback always possible | 2 files

## Architecture
```
alembic/
├── env.py              # Migration config
├── script.py.mako      # Template
└── versions/           # Migration files
```

## Commands
```bash
alembic revision --autogenerate -m "Add table"  # Create
alembic upgrade head                             # Apply
alembic downgrade -1                             # Rollback
alembic history --verbose                        # History
```

## Pattern
```python
def run_migrations_online():
    connectable = async_engine_from_config(config.get_section(...))
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=metadata)
        with context.begin_transaction():
            context.run_migrations()
```

## Safety Rules
1. Always autogenerate, review before apply
2. Test rollback for every migration
3. No data loss during schema changes

## USE THESE TOOLS
| Task | Tool |
|------|------|
| DB changes | **Skill**: `backend-patterns` |
| Migration review | **Agent**: `code-reviewer` |
| Schema issues | **Agent**: `build-error-resolver` |

**"Every migration has a reverse. Plan it first."**
