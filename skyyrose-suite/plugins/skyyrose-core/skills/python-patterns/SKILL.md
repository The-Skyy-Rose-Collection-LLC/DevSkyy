---
name: python-patterns
description: Python best practices, security patterns, type hints, async patterns, and Pythonic idioms for FastAPI/Django projects.
---

# Python Patterns

## Type Hints

```python
# ✅ GOOD: Fully typed with modern syntax (3.10+)
from collections.abc import Sequence

def process_items(items: Sequence[str], *, limit: int = 10) -> list[str]:
    """Process items with optional limit."""
    return [item.strip() for item in items[:limit] if item]

# ✅ GOOD: Optional and Union
from typing import TypeAlias

UserID: TypeAlias = int | str

def get_user(user_id: UserID) -> dict[str, str] | None:
    ...

# ❌ BAD: Missing types, using Any
def process(data, limit=10):
    return [x for x in data]
```

## Error Handling

```python
# ✅ GOOD: Typed exceptions with context
class ServiceError(Exception):
    def __init__(self, service: str, reason: str, *, correlation_id: str | None = None):
        self.service = service
        self.correlation_id = correlation_id
        super().__init__(f"{service}: {reason}")

async def fetch_data(url: str) -> dict:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as exc:
        raise ServiceError("fetch", f"Timeout: {url}") from exc
    except httpx.HTTPStatusError as exc:
        raise ServiceError("fetch", f"HTTP {exc.response.status_code}") from exc

# ❌ BAD: Bare except, swallowed errors
try:
    result = do_thing()
except:
    pass
```

## Immutable Patterns

```python
from dataclasses import dataclass, replace
from typing import Self

# ✅ GOOD: Frozen dataclass — immutable by default
@dataclass(frozen=True, slots=True)
class Product:
    sku: str
    name: str
    price_cents: int
    active: bool = True

    def with_price(self, price_cents: int) -> Self:
        return replace(self, price_cents=price_cents)

# ✅ GOOD: NamedTuple for simple data
from typing import NamedTuple

class Coordinate(NamedTuple):
    lat: float
    lon: float

# ❌ BAD: Mutable default arguments
def add_item(item: str, items: list[str] = []):  # DANGEROUS
    items.append(item)
    return items

# ✅ FIX: Use None sentinel
def add_item(item: str, items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    return [*items, item]
```

## Async Patterns (FastAPI)

```python
import asyncio
from contextlib import asynccontextmanager

# ✅ GOOD: Proper async with concurrency control
semaphore = asyncio.Semaphore(10)

async def fetch_with_limit(url: str) -> dict:
    async with semaphore:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.json()

# ✅ GOOD: Gather with error handling
async def fetch_all(urls: list[str]) -> list[dict]:
    tasks = [fetch_with_limit(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]

# ❌ BAD: Blocking in async context
async def bad_endpoint():
    import time
    time.sleep(5)  # Blocks event loop!

# ✅ FIX: Use async sleep or run_in_executor
async def good_endpoint():
    await asyncio.sleep(5)  # Non-blocking
```

## Security Patterns

```python
import secrets
import hashlib
from pathlib import Path

# ✅ GOOD: Parameterized queries
async def get_user(db, user_id: int) -> dict | None:
    return await db.fetch_one("SELECT * FROM users WHERE id = $1", user_id)

# ❌ BAD: SQL injection
async def get_user_bad(db, user_id):
    return await db.fetch_one(f"SELECT * FROM users WHERE id = {user_id}")

# ✅ GOOD: Safe path handling
def safe_file_path(base_dir: str, filename: str) -> Path:
    base = Path(base_dir).resolve()
    target = (base / filename).resolve()
    if not target.is_relative_to(base):
        raise ValueError("Path traversal detected")
    return target

# ✅ GOOD: Constant-time comparison for secrets
def verify_token(provided: str, expected: str) -> bool:
    return secrets.compare_digest(provided, expected)

# ✅ GOOD: Safe subprocess
import subprocess
def run_command(args: list[str]) -> str:
    result = subprocess.run(args, capture_output=True, text=True, check=True)
    return result.stdout

# ❌ BAD: Shell injection
subprocess.run(f"echo {user_input}", shell=True)
```

## Pydantic Validation

```python
from pydantic import BaseModel, Field, field_validator

class CreateProductRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    price_cents: int = Field(..., gt=0, le=999_999_99)
    sku: str = Field(..., pattern=r"^[A-Z]{2,4}-\d{4,8}$")
    tags: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be blank")
        return v.strip()
```

## Testing Patterns

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_fetch_data_success():
    """fetch_data returns parsed JSON on success."""
    mock_response = AsyncMock()
    mock_response.json.return_value = {"key": "value"}
    mock_response.raise_for_status = AsyncMock()

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        result = await fetch_data("https://api.example.com/data")

    assert result == {"key": "value"}

@pytest.mark.asyncio
async def test_fetch_data_timeout():
    """fetch_data raises ServiceError on timeout."""
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("timeout")):
        with pytest.raises(ServiceError, match="Timeout"):
            await fetch_data("https://api.example.com/data")
```

## Pythonic Idioms

```python
# Comprehensions over loops
squares = [x ** 2 for x in range(10) if x % 2 == 0]

# Context managers for resources
with open("data.json") as f:
    data = json.load(f)

# Walrus operator for check-and-use
if (match := pattern.search(text)) is not None:
    process(match.group())

# Structural pattern matching (3.10+)
match command:
    case {"action": "create", "data": data}:
        create(data)
    case {"action": "delete", "id": id_}:
        delete(id_)
    case _:
        raise ValueError(f"Unknown command: {command}")
```

## Related

- **Agent**: `python-reviewer` | **Command**: `/code-review` | **Skill**: `coding-standards`, `security-review`
