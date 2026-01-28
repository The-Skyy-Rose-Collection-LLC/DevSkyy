# DevSkyy Agent SDK

> Type-safe, documented, backward-compatible | 8 files

## Architecture
```
agent_sdk/
├── orchestrator.py         # Agent orchestration
├── round_table.py          # Multi-agent consensus
├── task_queue.py           # Async task management
├── custom_tools.py         # Tool definitions
└── super_agents/           # Pre-built agents
```

## Pattern
```python
class AgentConfig(BaseModel):
    name: str
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-20250514"

class BaseAgent(ABC):
    def __init__(self, config: AgentConfig):
        self.config = config
        self.tools: list[Tool] = []

    @abstractmethod
    async def execute(self, task: str, *, context: dict | None = None) -> AgentResult: ...

class RoundTable:
    async def deliberate(self, topic: str, agents: list[BaseAgent], *, max_rounds: int = 3) -> Consensus: ...
```

## Principles
| Principle | Implementation |
|-----------|----------------|
| Type Safety | Pydantic models |
| Extensibility | Abstract classes |
| Composability | Builder pattern |

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change

## USE THESE TOOLS
| Task | Tool |
|------|------|
| Agent invocation | **MCP**: `multi_agent_workflow` |
| List agents | **MCP**: `list_agents` |
| SDK examples | `examples/` folder |

**"An SDK should guide, not constrain."**
