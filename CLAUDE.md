# CLAUDE.md — DevSkyy Repository Intelligence Protocol

> **Purpose:** Instructions for AI agents working on this codebase.  
> **Scope:** All LLMs (Claude, GPT-4, Gemini, Cursor, Copilot) contributing code.

---

## Quick Reference

```bash
Repository:    devskyy-platform
Language:      Python 3.11 (primary), TypeScript 5 (frontend)
Framework:     FastAPI 0.104.1
Entry Point:   main_enterprise.py
Test Command:  pytest -v --cov=. --cov-report=term-missing
Lint Command:  ruff check . && black --check .
```

---

## 1. Repository Navigation

### Directory Map
```
devskyy-platform/
├── main_enterprise.py      # ← START HERE: FastAPI app entry
├── pyproject.toml          # Dependencies & tool configs (PEP 621)
├── security/               # Auth, encryption, RBAC
│   ├── jwt_oauth2_auth.py  # JWT/OAuth2 (modify for auth changes)
│   └── aes256_gcm_encryption.py
├── api/                    # API layer
│   ├── versioning.py       # /api/v1/, /api/v2/ routing
│   ├── webhooks.py         # Event publishing (HMAC signed)
│   ├── gdpr.py             # GDPR compliance (Articles 15-30)
│   └── agents.py           # 23 AI agents across 7 categories
├── database/               # Database layer
│   └── db.py               # Async SQLAlchemy + connection pooling
├── tests/                  # Test suite
│   ├── conftest.py         # Fixtures
│   ├── test_security.py    # Auth, encryption tests
│   ├── test_gdpr.py        # GDPR compliance tests
│   └── test_agents.py      # Agent API tests
├── devskyy_mcp.py          # MCP server: exposes agents to external AI
└── legacy/                 # Deprecated (reference only)
    ├── complete_working_platform.py
    ├── sqlite_auth_system.py
    ├── autonomous_commerce_engine.py
    └── prompt_system.py
```

### File Modification Guide
| Task | Start File | Related Files |
|------|------------|---------------|
| Add API endpoint | `main_enterprise.py` | `api/versioning.py` |
| Change auth logic | `security/jwt_oauth2_auth.py` | `database/db.py` |
| Add webhook event | `api/webhooks.py` | `main_enterprise.py` |
| Add GDPR feature | `api/gdpr.py` | `database/db.py` |
| Add/modify agent | `api/agents.py` | `devskyy_mcp.py` |
| Expose agent via MCP | `devskyy_mcp.py` | `api/agents.py` |
| Add encryption | `security/aes256_gcm_encryption.py` | — |
| Add database model | `database/db.py` | `api/*.py` |
| Add test | `tests/test_*.py` | `tests/conftest.py` |

---

## 2. Code Generation Rules

### 2.1 Before Creating Any File

```python
# 1. Check if file exists — modify, don't duplicate
# 2. Find related files: find . -name "*{module}*"
# 3. Verify all imports exist on PyPI with exact versions
```

### 2.2 Required File Header

```python
"""
{filename}
Purpose: {one-line description}
Depends: {package}=={version}, ...
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
```

### 2.3 Import Rules

```python
# ✅ VERIFIED (PyPI December 2024)
from fastapi import FastAPI          # fastapi==0.104.1
from pydantic import BaseModel       # pydantic==2.5.2
import httpx                          # httpx==0.25.2

# ❌ HALLUCINATED — DO NOT USE
from fastapi_magic import AutoRouter  # DOES NOT EXIST
from pydantic import AutoValidate     # DOES NOT EXIST
```

### 2.4 No Stubs — Complete Implementations Only

```python
# ❌ FORBIDDEN
def process_order(order_id: str):
    pass  # TODO: implement

def calculate_shipping():
    raise NotImplementedError()

# ✅ REQUIRED
def process_order(order_id: str) -> OrderResult:
    order = db.get_order(order_id)
    if not order:
        raise HTTPException(404, f"Order {order_id} not found")
    order.status = "processing"
    db.save(order)
    return OrderResult(order_id=order_id, status="processing")
```

---

## 3. LLM Automation Patterns

### 3.1 Agent Routing by Complexity

```python
# Route tasks to appropriate LLM
ROUTING = {
    "complex":   ["claude-opus", "gpt-4.1"],       # Architecture, strategy
    "execution": ["claude-sonnet", "gpt-4.1-mini"] # Implementation
}

def route_task(task: Task) -> str:
    return ROUTING["complex"][0] if task.complexity > 0.7 else ROUTING["execution"][0]
```

### 3.2 Large File Handling

```python
# Files >500 lines: chunk by function/class
def process_large_file(path: str, task: str):
    structure = parse_ast(path)  # Extract classes, functions
    relevant = filter_by_keywords(structure, task)
    for section in relevant:
        yield read_section(path, section.start_line, section.end_line)
```

### 3.3 Multi-Agent Task Flow

```
1. PARSE    → Extract intent from user request
2. SEARCH   → Find relevant files in codebase
3. PLAN     → Generate change list
4. VALIDATE → Check syntax, imports, types
5. APPLY    → Write changes
6. TEST     → Run affected tests
7. COMMIT   → Atomic commit with clear message
```

---

## 4. Quality Gates

### 4.1 Pre-Commit (Must Pass)

```bash
ruff check .                    # Lint
black --check .                 # Format
mypy . --ignore-missing-imports # Types
pytest -x --tb=short            # Tests
```

### 4.2 Security Scan

```python
# Block these patterns in all code:
BLOCKED = [
    r'(api_key|password|secret)\s*=\s*["\'][^"\']+["\']',  # Hardcoded secrets
    r'f["\'].*SELECT.*\{',                                  # SQL injection
    r'eval\s*\(|exec\s*\(',                                 # Code injection
    r'subprocess.*shell=True',                              # Shell injection
]
```

### 4.3 Test Coverage Minimums

```
security/*           → 95%
api/*                → 90%
main_enterprise.py   → 85%
everything else      → 80%
```

---

## 5. Commit Protocol

### Format
```
[SCOPE] Imperative description

- Change 1
- Change 2

Refs: RFC-XXXX (if applicable)
```

### Scopes
```
[API]      — Endpoints
[SECURITY] — Auth, encryption
[AGENT]    — AI agents
[MCP]      — Model Context Protocol
[FIX]      — Bug fixes
[DOCS]     — Documentation
[TEST]     — Tests
[REFACTOR] — No behavior change
```

### Atomic Commits
```bash
# ✅ One change per commit
git commit -m "[API] Add orders endpoint"
git commit -m "[TEST] Add orders tests"

# ❌ Mixed changes
git commit -m "Add orders, fix auth, update docs"
```

---

## 6. Verified Dependencies (December 2024)

```
fastapi==0.104.1
pydantic==2.5.2
uvicorn==0.24.0
PyJWT==2.10.1
cryptography==41.0.7
argon2-cffi==23.1.0
httpx==0.25.2
sqlalchemy==2.0.23
asyncpg==0.29.0
```

### Adding New Dependencies
```
1. Verify on PyPI: pip index versions {package}
2. Check vulnerabilities: pip-audit
3. Confirm license: MIT, Apache 2.0, BSD only
4. Add with comment: package==X.Y.Z  # purpose
```

---

## 7. Error Handling

```python
# Use specific exceptions
class DevSkyyError(Exception): pass
class ValidationError(DevSkyyError): pass
class AuthError(DevSkyyError): pass

# ✅ Specific handling
try:
    result = process(data)
except ValidationError as e:
    logger.warning(f"Validation: {e}")
    raise HTTPException(400, str(e))

# ❌ Never do this
try:
    result = process(data)
except:
    pass
```

---

## 8. API Endpoint Template

```python
@router.post(
    "/api/v1/{resource}",
    response_model=ResourceResponse,
    status_code=201,
    tags=["Resource"],
)
async def create_resource(
    request: ResourceCreate,
    user: TokenPayload = Depends(get_current_user),
) -> ResourceResponse:
    """Create resource. Full docstring required."""
    # Complete implementation — no stubs
```

---

## 9. MCP: Exposing to External LLMs

```python
# Make functions callable by Claude/GPT/Gemini
@mcp_tool(name="execute_agent", description="Run AI agent task")
async def mcp_execute_agent(agent_name: str, task: str) -> Dict:
    return await orchestrator.execute(agent_name, task)
```

---

## 10. Quick Commands

```bash
# Run
uvicorn main_enterprise:app --reload --port 8000

# Test
pytest -v
pytest --cov=security --cov-report=html

# Lint & Format
ruff check . --fix
black .

# Security
pip-audit
bandit -r . -ll
```

---

## 11. Pre-Submit Checklist

```
[ ] No duplicate files created
[ ] All imports verified on PyPI
[ ] Versions pinned in requirements.txt
[ ] No hardcoded secrets (grep: api_key, password, secret)
[ ] Specific exception handling (no bare except)
[ ] Logging has context (user_id, request_id)
[ ] Tests added for new code
[ ] Type hints on all functions
[ ] Docstrings on public functions
[ ] Commit message follows format
```

---

## 12. Uncertainty Protocol

When you cannot verify something:

```
I cannot confirm [specific claim].

To verify:
1. Official docs: [url]
2. Test command: [command]
3. Reference: [RFC/NIST/etc]

Safe alternative: [conservative approach]
```

---

## 13. SkyyRose Context

```
Brand:    SkyyRose — "Where Love Meets Luxury"
Domain:   skyyrose.co
Location: Oakland, California
Lines:    BLACK ROSE, LOVE HURTS, SIGNATURE
Stack:    WordPress + Shoptimizer 2.9.0 + Elementor Pro 3.32.2
```

---

**Version:** 4.0  
**Focus:** Large codebase + LLM automation  
**Updated:** December 2024
