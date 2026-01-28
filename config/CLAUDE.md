# DevSkyy Config

> Environment-driven, validated, secure | 10 files

## Architecture
```
config/
├── settings.py           # Pydantic Settings
├── logging_config.py     # Structured logging
├── constants.py          # App constants
└── claude/desktop.json   # Claude Desktop template
```

## Pattern
```python
class Settings(BaseSettings):
    OPENAI_API_KEY: SecretStr = Field(default="")
    ANTHROPIC_API_KEY: SecretStr = Field(default="")
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./devskyy.db")
    RAG_ENABLED: bool = Field(default=True)
    ENVIRONMENT: str = Field(default="development")
    model_config = {"env_file": ".env", "extra": "ignore"}

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

## Environment Files
| File | Purpose | Committed |
|------|---------|-----------|
| .env.example | Template | Yes |
| .env | Local | No |

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change

## USE THESE TOOLS
| Task | Tool |
|------|------|
| Missing secrets | **MCP**: `health_check` |
| Config review | **Agent**: `security-reviewer` |

**"12 factors. Zero exceptions."**
