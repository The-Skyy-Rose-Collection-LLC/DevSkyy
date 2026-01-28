---
name: fix-linting
description: Auto-fix linting errors to meet DevSkyy standards.
---

# DevSkyy Linting Auto-Fix

## Quick Commands
```bash
isort .                    # Sort imports
ruff check --fix .         # Auto-fix Python
black .                    # Format code
mypy .                     # Type check
```

## Standards
- Type annotations: `X | Y` (not `Union[X, Y]`)
- No unused variables (F841)
- Modern isinstance: `isinstance(x, str | bytes)`
- Proper import sorting (isort)

## Common Fixes
```python
# Type annotations
x: str | int  # not Union[str, int]

# Unused variables
_ = expensive_op()  # or remove

# Modern isinstance
isinstance(x, str | bytes)  # not (str, bytes)
```

## Verification
```bash
ruff check . && isort --check-only . && black --check .
```

## Related Tools
- **Command**: `/verify` for full checks
- **Agent**: `build-error-resolver` for type errors
- **MCP**: Run pytest after linting
