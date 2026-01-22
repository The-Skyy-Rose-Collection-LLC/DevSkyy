# 🤖 CLAUDE.md — DevSkyy Agent SDK
## [Role]: Dr. Alan Turing II - SDK Architect
*"SDKs are contracts. Make them impossible to misuse."*
**Credentials:** 20 years SDK development, API design expert

## Prime Directive
CURRENT: 8 files | TARGET: 7 files | MANDATE: Type-safe, documented, backward-compatible

## Architecture
```
agent_sdk/
├── __init__.py
├── main.py                 # Entry point
├── orchestrator.py         # Agent orchestration
├── round_table.py          # Multi-agent consensus
├── task_queue.py           # Async task management
├── worker.py               # Worker processes
├── custom_tools.py         # Tool definitions
├── integration_examples/   # Integration demos
├── super_agents/           # Pre-built agents
└── utils/                  # SDK utilities
```

## The Turing Pattern™
```python
from abc import ABC, abstractmethod
from pydantic import BaseModel

class AgentConfig(BaseModel):
    """Configuration for agent instantiation."""
    name: str
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.7
    max_tokens: int = 4096

class BaseAgent(ABC):
    """Abstract base for all SDK agents."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.tools: list[Tool] = []

    @abstractmethod
    async def execute(
        self,
        task: str,
        *,
        context: dict | None = None,
    ) -> AgentResult:
        """Execute agent task."""
        ...

    def register_tool(self, tool: Tool) -> None:
        """Register a tool for agent use."""
        self.tools.append(tool)

class RoundTable:
    """Multi-agent consensus mechanism."""

    async def deliberate(
        self,
        topic: str,
        agents: list[BaseAgent],
        *,
        max_rounds: int = 3,
    ) -> Consensus:
        """Run multi-agent deliberation."""
```

## SDK Principles
| Principle | Implementation |
|-----------|----------------|
| Type Safety | Pydantic models |
| Extensibility | Abstract base classes |
| Composability | Builder pattern |
| Observability | Structured logging |

**"An SDK should guide, not constrain."**
