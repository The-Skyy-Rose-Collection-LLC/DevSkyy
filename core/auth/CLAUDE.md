# core/auth/ — Auth Types & Interfaces

**Zero-dependency auth contracts.** Breaks the historical `api/ ↔ security/` circular import. Types live here; JWT signing / OAuth / password hashing implementations live in `security/`.

## Public Surface (`core/auth/__init__.py`)

| Export | Type | Source |
|--------|------|--------|
| `UserRole`, `TokenType`, `AuthStatus`, `AuthErrorCode`, `Permission`, `SubscriptionTier` | Enums | `types.py` |
| `TokenPayload` | dataclass | `token_payload.py` |
| `AuthCredentials`, `AuthResult`, `TokenRequest`, `TokenResponse`, `TokenPair`, `UserBase`, `UserCreate`, `UserInDB` | Pydantic | `models.py` |
| `IAuthProvider`, `ITokenValidator`, `ITokenBlacklist`, `IRateLimiter`, `IPasswordHasher` | ABC | `interfaces.py` |
| `ROLE_HIERARCHY` + 6 role helpers (`get_role_level`, `is_role_at_least`, `has_required_role`, `get_minimum_required_level`, `get_roles_at_or_above`, `get_highest_role_from_list`) | functions | `role_hierarchy.py` |

## Hard Rules

- This module MUST NOT depend on `api/`, `security/`, `agents/`, `services/` (`core/auth/__init__.py:8`)
- Allowed deps: `pydantic` + stdlib only
- New auth code: define the contract here (ABC/Protocol), implement in `security/`
- `TokenPayload` is the canonical token shape — do not redefine in `security/jwt_manager.py` or middleware
- Role checks go through `role_hierarchy.has_required_role()`, never raw enum compare — hierarchy is non-trivial

## Role Hierarchy

Defined in `role_hierarchy.py`. Use `get_role_level(UserRole.X)` to compare numerically; use `is_role_at_least(actual, required)` for boolean checks.

## Consumers

- `security/jwt_manager.py` — implements `ITokenValidator`
- `api/middleware/auth.py` — consumes `TokenPayload` from `request.state`
- `api/v1/portal/*` — checks `SubscriptionTier` on every paid handler
