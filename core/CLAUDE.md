# DevSkyy Core

> Zero dependencies on outer layers | 16 files

## Architecture
```
core/
├── runtime/
│   ├── input_validator.py    # Pydantic validation
│   └── tools.py              # ToolSpec, ToolRegistry
├── llm/infrastructure/       # Provider abstraction
└── errors.py                 # Exception hierarchy
```

## Pattern
```python
class ToolSpec(BaseModel, Generic[T, R]):
    name: str
    input_schema: type[T]
    output_schema: type[R]

class BaseTool(ABC, Generic[T, R]):
    spec: ToolSpec[T, R]
    async def execute(self, input: T, *, correlation_id: str | None = None) -> R: ...

class ToolRegistry:
    def register(self, tool: BaseTool) -> None: self._tools[tool.spec.name] = tool
    def get(self, name: str) -> BaseTool | None: return self._tools.get(name)
```

## USE THESE TOOLS
| Task | Tool |
|------|------|
| Tool debugging | **MCP**: `tool_catalog`, `health_check` |
| Core changes | **Agent**: `architect` for design review |
| Validation issues | **Skill**: `coding-standards` |

**"The core serves everyone. It depends on no one."**
