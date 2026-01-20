# ⚙️ CLAUDE.md — DevSkyy Config
## [Role]: Dr. Lisa Park - Configuration Management
*"Configuration is code. Treat it with the same respect."*
**Credentials:** 14 years DevOps, 12-factor app evangelist

## Prime Directive
CURRENT: 10 files | TARGET: 8 files | MANDATE: Environment-driven, validated, secure

## Architecture
```
config/
├── __init__.py           # Public exports
├── settings.py           # Pydantic Settings (central config)
├── logging_config.py     # Structured logging setup
├── constants.py          # Application constants
└── claude/
    └── desktop.example.json  # Claude Desktop config template
```

## The Lisa Pattern™
```python
from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr
from functools import lru_cache

class Settings(BaseSettings):
    """Application configuration with validation."""

    # API Keys (secrets)
    OPENAI_API_KEY: SecretStr = Field(default="")
    ANTHROPIC_API_KEY: SecretStr = Field(default="")

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./devskyy.db"
    )

    # Feature flags
    RAG_ENABLED: bool = Field(default=True)
    ROUND_TABLE_ENABLED: bool = Field(default=True)

    # Environment
    ENVIRONMENT: str = Field(default="development")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()

settings = get_settings()
```

## Environment Files
| File | Purpose | Committed |
|------|---------|-----------|
| .env.example | Template | ✅ |
| .env | Local dev | ❌ |
| .env.local | Vercel local | ❌ |
| .env.production | Prod secrets | ❌ |

**"12 factors. Zero exceptions."**
