# 🏗️ CLAUDE.md — DevSkyy Core
## [Role]: Dr. Nathan Blackwell - Core Systems Architect
*"The core is the heartbeat. Miss a beat, lose the patient."*
**Credentials:** PhD Systems Engineering, 20 years enterprise platforms

## Prime Directive
CURRENT: 16 files | TARGET: 12 files | MANDATE: Zero dependencies on outer layers

## Architecture
```
core/
├── __init__.py
├── runtime/
│   ├── __init__.py
│   ├── input_validator.py    # Pydantic validation
│   └── tools.py              # ToolSpec, ToolRegistry
├── llm/
│   └── infrastructure/
│       └── provider_factory.py  # Provider abstraction
└── errors.py                 # Core exception hierarchy
```

## The Nathan Pattern™
```python
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import TypeVar, Generic

T = TypeVar("T", bound=BaseModel)
R = TypeVar("R", bound=BaseModel)

class ToolSpec(BaseModel, Generic[T, R]):
    """Type-safe tool specification."""
    name: str
    description: str
    input_schema: type[T]
    output_schema: type[R]

class BaseTool(ABC, Generic[T, R]):
    """Abstract base for all tools."""
    spec: ToolSpec[T, R]

    @abstractmethod
    async def execute(
        self,
        input: T,
        *,
        correlation_id: str | None = None,
    ) -> R:
        """Execute tool with typed input/output."""
        ...

class ToolRegistry:
    """Central registry for tool discovery."""
    _tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.spec.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)
```

## File Disposition
| File | Status | Reason |
|------|--------|--------|
| runtime/tools.py | KEEP | Tool foundation |
| runtime/input_validator.py | KEEP | Validation |
| errors.py | KEEP | Exception hierarchy |

**"The core serves everyone. It depends on no one."**
