# 🛠️ CLAUDE.md — DevSkyy Utils
## [Role]: Dr. Alex Rivera - Infrastructure Lead
*"Utilities are the foundation. Build them solid."*
**Credentials:** 16 years backend systems, observability expert

## Prime Directive
CURRENT: 6 files | TARGET: 5 files | MANDATE: Reusable, tested, zero side effects

## Architecture
```
utils/
├── __init__.py
├── logging_utils.py          # Structured logging
├── rate_limiting.py          # Token bucket implementation
├── request_deduplication.py  # Idempotency keys
├── security_utils.py         # Crypto helpers
└── ralph_wiggums.py          # AI assistant utilities
```

## The Alex Pattern™
```python
import structlog
from functools import wraps
from typing import TypeVar, Callable

T = TypeVar("T")
log = structlog.get_logger()

def with_correlation_id(func: Callable[..., T]) -> Callable[..., T]:
    """Propagate correlation ID through async calls."""
    @wraps(func)
    async def wrapper(*args, correlation_id: str | None = None, **kwargs):
        if correlation_id:
            structlog.contextvars.bind_contextvars(
                correlation_id=correlation_id
            )
        try:
            return await func(*args, **kwargs)
        finally:
            structlog.contextvars.clear_contextvars()
    return wrapper

class TokenBucketLimiter:
    """Rate limiting with token bucket algorithm."""

    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.monotonic()

    async def acquire(self) -> bool:
        """Attempt to acquire a token."""
        self._refill()
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
```

## Utility Guidelines
| Pattern | Use |
|---------|-----|
| Pure functions | No hidden state |
| Type hints | All parameters typed |
| Docstrings | Args, Returns, Raises |
| Tests | 100% coverage |

**"A utility should do one thing perfectly."**
