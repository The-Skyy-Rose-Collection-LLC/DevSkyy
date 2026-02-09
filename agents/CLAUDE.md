# DevSkyy Agents

> AI Agents & Orchestration | 54 agents | Use ADK base classes

---

## Learnings (Update When Claude Makes Mistakes)

### Agent Base Classes

- ❌ **Mistake**: Using `base_legacy.py` or `operations_legacy.py`
  - ✅ **Correct**: Use `adk/base_super_agent.py` (17 reasoning techniques, ADK-based)

- ❌ **Mistake**: Creating agent without proper __init__ signature
  - ✅ **Correct**: Always accept `correlation_id` as keyword-only arg

- ❌ **Mistake**: Not propagating correlation_id through agent calls
  - ✅ **Correct**: Pass `correlation_id=correlation_id` to all sub-calls

### Agent Orchestration

- ❌ **Mistake**: Creating tight coupling between agents
  - ✅ **Correct**: Agents communicate via messages, not direct method calls

- ❌ **Mistake**: Not handling agent failures gracefully
  - ✅ **Correct**: Use `try/except` with fallback strategies

- ❌ **Mistake**: Forgetting to register agent in registry
  - ✅ **Correct**: Add to `core/registry/` after creation

### Round Table

- ❌ **Mistake**: Using round table for simple tasks
  - ✅ **Correct**: Round table is for complex multi-perspective analysis only (3+ agents)

- ❌ **Mistake**: Not setting proper voting thresholds
  - ✅ **Correct**: Use 66% consensus threshold (configurable)

---

## Structure

```
agents/
├── base_super_agent.py       # ✅ USE THIS (17 techniques, ADK-based)
├── base_legacy.py            # ❌ DEPRECATED
├── operations_legacy.py      # ❌ DEPRECATED
├── orchestrator.py           # Multi-agent orchestration
└── round_table.py            # Consensus mechanism
```

---

## Usage Pattern

```python
# ✅ CORRECT: Use ADK base
from adk.base import SuperAgent

class MyAgent(SuperAgent):
    async def execute(
        self,
        task: str,
        *,
        correlation_id: str | None = None
    ) -> Result:
        try:
            result = await self.process(task)
            return Result(success=True, data=result)
        except Exception as e:
            raise AgentError(
                f"Agent failed: {task}",
                correlation_id=correlation_id
            ) from e
```

---

## Verification

```bash
# Check no legacy imports
rg "from.*base_legacy|operations_legacy" agents/ && echo "❌ Found legacy imports!" || echo "✅ No legacy imports"

# Run agent tests
pytest tests/unit/test_agents.py -v
```

---

**"17 reasoning techniques. Zero legacy dependencies."**
