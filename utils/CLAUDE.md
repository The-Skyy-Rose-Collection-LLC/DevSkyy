# DevSkyy Utils

> Reusable, tested, zero side effects | 6 files

## Architecture
```
utils/
├── logging_utils.py          # Structured logging
├── rate_limiting.py          # Token bucket
├── request_deduplication.py  # Idempotency
└── security_utils.py         # Crypto helpers
```

## Pattern
```python
def with_correlation_id(func):
    @wraps(func)
    async def wrapper(*args, correlation_id: str | None = None, **kwargs):
        if correlation_id:
            structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        return await func(*args, **kwargs)
    return wrapper

class TokenBucketLimiter:
    async def acquire(self) -> bool:
        self._refill()
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
```

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change

## USE THESE TOOLS
| Task | Tool |
|------|------|
| Monitoring | **MCP**: `system_monitoring` |
| Utils review | **Agent**: `code-reviewer` |

**"A utility should do one thing perfectly."**
