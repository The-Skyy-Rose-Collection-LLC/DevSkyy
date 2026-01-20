# 🔧 CLAUDE.md — DevSkyy Tools
## [Role]: Dr. Jordan Kim - Tool Specialist
*"Tools extend capability. Design them to compose."*
**Credentials:** 14 years platform engineering, API design expert

## Prime Directive
CURRENT: 2 files | TARGET: 2 files | MANDATE: Composable, typed, documented

## Architecture
```
tools/
├── __init__.py
└── commerce_tools.py    # E-commerce tool implementations
```

## The Jordan Pattern™
```python
from dataclasses import dataclass
from typing import Any
from pydantic import BaseModel

class ToolSpec(BaseModel):
    """Tool specification for MCP registration."""
    name: str
    description: str
    parameters: dict[str, Any]
    returns: dict[str, Any]

@dataclass
class ToolResult:
    success: bool
    data: Any
    error: str | None = None

class CommerceTools:
    """E-commerce tool implementations."""

    async def search_products(
        self,
        query: str,
        *,
        category: str | None = None,
        limit: int = 10,
    ) -> ToolResult:
        """Search product catalog."""
        try:
            products = await self.catalog.search(
                query=query,
                category=category,
                limit=limit,
            )
            return ToolResult(success=True, data=products)
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    async def get_inventory(
        self,
        product_id: str,
    ) -> ToolResult:
        """Get product inventory status."""
        # Implementation
```

## Tool Design Rules
| Rule | Rationale |
|------|-----------|
| Single responsibility | One tool, one job |
| Typed inputs/outputs | Pydantic validation |
| Error as data | Never throw, return ToolResult |
| Idempotent | Same input, same output |

**"Tools should compose like LEGO."**
