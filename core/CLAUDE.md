# DevSkyy Core

> Zero dependencies on outer layers | Auth types, models, interfaces

---

## Critical Rule

**ZERO dependencies on outer layers**: core/ must NEVER import from adk/, security/, agents/, api/, or services/.

---

## Learnings (Update When Claude Makes Mistakes)

### Architecture

- ❌ **Mistake**: Importing from security/ or agents/ into core/
  - ✅ **Correct**: core/ has ZERO dependencies. Define types/interfaces here, implement in outer layers.

- ❌ **Mistake**: Putting implementations in core/auth/
  - ✅ **Correct**: core/auth/ = types/models/interfaces only. Implementations go in security/.

- ❌ **Mistake**: Adding new dependencies to core/
  - ✅ **Correct**: core/ depends ONLY on stdlib + pydantic. Use `architect` agent before adding deps.

### Patterns

- ❌ **Mistake**: Creating concrete classes in core/auth/interfaces.py
  - ✅ **Correct**: Use ABC (Abstract Base Class) only. Implementations go in security/.

---

## Structure

```
core/
├── auth/                     # Authentication (types, models, interfaces)
│   ├── types.py             # Enums: UserRole, TokenType, AuthStatus
│   ├── models.py            # Pydantic models: TokenResponse, UserCreate
│   ├── interfaces.py        # ABCs: IAuthProvider, ITokenValidator
│   ├── token_payload.py     # TokenPayload dataclass
│   └── role_hierarchy.py    # ROLE_HIERARCHY + utilities
├── registry/                 # Service registry for dependency injection
├── runtime/                  # Tool registry, input validation
└── errors.py                 # Exception hierarchy
```

---

## Usage Pattern

```python
# ✅ CORRECT: Import types from core, use implementations from security
from core.auth import UserRole, TokenPayload, IAuthProvider
from security.jwt import JWTAuthProvider  # Implementation

provider: IAuthProvider = JWTAuthProvider()
token = await provider.generate_token(user_id="123")
```

---

## Verification

```bash
# Verify zero dependencies
rg "^from (adk|security|agents|api|services)" core/ && echo "❌ Found outer layer imports!" || echo "✅ Zero dependencies verified"

# Run tests
pytest tests/unit/test_core.py -v
```

---

**"The core serves everyone. It depends on no one."**
