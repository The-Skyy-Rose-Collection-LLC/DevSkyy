# Legacy Code

These files are preserved for reference but have been superseded by the enterprise modules.

## Files

| Legacy File | Replaced By | Notes |
|-------------|-------------|-------|
| `complete_working_platform.py` | `main_enterprise.py` | Old 47-endpoint monolith |
| `sqlite_auth_system.py` | `security/jwt_oauth2_auth.py` | Old SQLite-only auth |
| `autonomous_commerce_engine.py` | `api/agents.py` | E-commerce automation |
| `prompt_system.py` | `api/agents.py` + MCP | Agent prompt templates |

## Migration Status

All functionality has been migrated to:
- `main_enterprise.py` — Main application entry
- `security/` — JWT/OAuth2, AES-256-GCM encryption
- `api/` — Versioning, webhooks, GDPR, agents
- `database/` — Async SQLAlchemy with pooling

## Do Not Import

These files are **not used** by the production system. They exist only for:
- Historical reference
- Migrating any missed functionality
- Understanding original design decisions

## Removal

These files can be safely deleted after confirming all functionality is covered.
