# DevSkyy Tools

> Composable, typed, documented | 2 files

## Architecture
```
tools/
├── __init__.py
└── commerce_tools.py    # E-commerce implementations
```

## Pattern
```python
class ToolSpec(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]

@dataclass
class ToolResult:
    success: bool
    data: Any
    error: str | None = None

class CommerceTools:
    async def search_products(self, query: str, *, limit: int = 10) -> ToolResult:
        try:
            products = await self.catalog.search(query=query, limit=limit)
            return ToolResult(success=True, data=products)
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))
```

## Rules
| Rule | Rationale |
|------|-----------|
| Single responsibility | One tool, one job |
| Typed inputs/outputs | Pydantic validation |
| Error as data | Return ToolResult, never throw |

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change

## USE THESE TOOLS
- **MCP**: `product_search`, `tool_catalog`

**"Tools should compose like LEGO."**
