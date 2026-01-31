# DevSkyy Core

> Zero dependencies on outer layers | 22 files

## Architecture
```
core/
├── auth/                     # AUTHENTICATION TYPES (NEW - v1.3.0)
│   ├── types.py             # UserRole, TokenType, AuthStatus (6 enums)
│   ├── models.py            # TokenResponse, UserCreate, UserInDB (8 models)
│   ├── interfaces.py        # IAuthProvider, ITokenValidator (5 ABCs)
│   ├── token_payload.py     # TokenPayload dataclass
│   └── role_hierarchy.py    # ROLE_HIERARCHY + utilities
├── runtime/
│   ├── input_validator.py    # Pydantic validation
│   └── tools.py              # ToolSpec, ToolRegistry
├── llm/infrastructure/       # Provider abstraction
└── errors.py                 # Exception hierarchy
```

## Patterns

### Auth Types (Zero Dependencies)
```python
from core.auth import UserRole, TokenPayload, IAuthProvider

# Types are defined in core, implementations in security/
payload = token_validator.validate_token(token)
if payload.has_role(UserRole.ADMIN):
    # Admin-specific logic
    pass
```

### Tool Registry
```python
class ToolSpec(BaseModel, Generic[T, R]):
    name: str
    input_schema: type[T]
    output_schema: type[R]

class BaseTool(ABC, Generic[T, R]):
    spec: ToolSpec[T, R]
    async def execute(self, input: T, *, correlation_id: str | None = None) -> R: ...

class ToolRegistry:
    def register(self, tool: BaseTool) -> None: self._tools[tool.spec.name] = tool
    def get(self, name: str) -> BaseTool | None: return self._tools.get(name)
```

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change

## USE THESE TOOLS
| Task | Tool |
|------|------|
| Tool debugging | **MCP**: `tool_catalog`, `health_check` |
| Core changes | **Agent**: `architect` for design review |

**"The core serves everyone. It depends on no one."**
