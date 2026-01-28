---
name: devskyy-analytics-patterns
description: DevSkyy-specific patterns from analytics module implementation.
---

# DevSkyy Analytics Patterns

## Key Patterns

**1. DevSkyError** - Use `code=` not `error_code=`:
```python
raise DevSkyError(message="Failed", code=DevSkyErrorCode.INTERNAL_ERROR)
```

**2. Falsy numeric check** - Handle zero correctly:
```python
if numeric_value is not None:  # Not `if numeric_value`
```

**3. PostgreSQL arrays** - Format for raw SQL:
```python
channels_array = "{" + ",".join(channels) + "}" if channels else "{}"
```

**4. Mock side effects** - For stats tracking:
```python
async def mock_fn(arg):
    service._stats["count"] += 1
    return True
mock.side_effect = mock_fn
```

**5. Role-based access**:
```python
user: TokenPayload = Depends(require_roles(["admin", "analyst"]))
```

## Related Tools

- **Skill**: `backend-patterns` for general API patterns
- **Skill**: `coding-standards` for style guide
- **Agent**: `code-reviewer` for pattern compliance
- **MCP**: `analytics_query` for analytics operations
