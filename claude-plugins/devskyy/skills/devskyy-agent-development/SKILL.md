---
name: DevSkyy Agent Development
description: This skill should be used when the user asks to "create an agent", "add a SuperAgent", "implement a new agent", "extend agent capabilities", "modify agent behavior", or mentions DevSkyy agent architecture, SuperAgent patterns, or agent-based workflows.
version: 1.0.0
---

# DevSkyy Agent Development Skill

Use this skill when developing, modifying, or extending SuperAgents in the DevSkyy AI platform.

## When to Use This Skill

Invoke this skill when the user:

- Asks to create a new SuperAgent (Commerce, Creative, Marketing, Support, Operations, Analytics)
- Wants to modify existing agent capabilities or behaviors
- Needs to implement agent coordination or multi-agent workflows
- Requests agent tool integration or ToolRegistry modifications
- Asks about agent architecture, LLM Round Table, or self-learning features

## Core Agent Architecture

### SuperAgent Base Class Pattern

All DevSkyy agents inherit from `EnhancedSuperAgent` located in `agents/base_super_agent.py`:

```python
from agents.base_super_agent import EnhancedSuperAgent
from orchestration.tool_registry import ToolRegistry
from typing import Optional, Dict, Any

class NewAgent(EnhancedSuperAgent):
    """NewAgent SuperAgent for specific domain."""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        llm_router: Optional[Any] = None,
        brand_context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            name="NewAgent",
            domain="Domain Description",
            capabilities=[
                "Capability 1",
                "Capability 2",
                "Capability 3"
            ],
            tool_registry=tool_registry,
            llm_router=llm_router,
            brand_context=brand_context
        )
```

### Key Agent Features

1. **17 Prompt Techniques** (auto-selected by task type):
   - Chain of Thought (CoT)
   - Tree of Thought (ToT)
   - ReAct (Reasoning + Acting)
   - Self-Consistency
   - Few-Shot Learning
   - Zero-Shot CoT
   - And 11 more advanced techniques

2. **ML Module** (`agents/base_super_agent.py:MLModule`):
   - Sentiment analysis
   - Text classification
   - Named entity recognition
   - Clustering and pattern detection

3. **Self-Learning System**:
   - Success/failure tracking
   - Feedback loop integration
   - Performance metrics

4. **LLM Round Table**:
   - All 6 LLM providers compete on same prompt
   - Top 2 enter A/B test phase
   - Statistical significance testing (chi-square)
   - Winner becomes default for task type

## Agent Workflow Pattern

```python
async def execute_task(self, task_description: str) -> Dict[str, Any]:
    """Standard agent execution pattern."""

    # 1. Plan
    plan = await self.plan(task_description)

    # 2. Retrieve context (RAG)
    context = await self.retrieve_context(task_description)

    # 3. Execute with tools
    results = []
    for step in plan.steps:
        if step.requires_tool:
            result = await self.use_tool(
                step.tool_name,
                step.tool_inputs
            )
            results.append(result)

    # 4. Validate results
    validation = await self.validate(results, plan.success_criteria)

    # 5. Return structured output
    return {
        "status": "completed" if validation.passed else "failed",
        "results": results,
        "artifacts": validation.artifacts,
        "metrics": self.get_metrics()
    }
```

## Tool Integration

### Using ToolRegistry

```python
# Register new tool
tool_spec = ToolSpec(
    name="custom_tool",
    description="Tool description",
    schema={
        "type": "object",
        "properties": {
            "input": {"type": "string"}
        },
        "required": ["input"]
    },
    category=ToolCategory.CUSTOM,
    severity=SeverityLevel.LOW,
    permissions=["read"],
    timeout_ms=5000
)

self.tool_registry.register(tool_spec)

# Execute tool with context
context = ToolCallContext(
    correlation_id=str(uuid.uuid4()),
    agent_id=self.name,
    timestamp=datetime.utcnow()
)

result = await self.tool_registry.execute(
    "custom_tool",
    {"input": "value"},
    context
)
```

## Brand Context Integration

Agents automatically receive SkyyRose brand DNA:

```python
SKYYROSE_BRAND_DNA = {
    "name": "SkyyRose",
    "tagline": "Where Love Meets Luxury",
    "colors": {
        "primary": "#B76E79",
        "secondary": "#1A1A1A"
    },
    "style": ["premium", "sophisticated", "bold", "elegant"],
    "collections": {
        "BLACK_ROSE": "dark romantic aesthetic",
        "LOVE_HURTS": "edgy romantic style",
        "SIGNATURE": "clean minimal aesthetic"
    }
}
```

Access via `self.brand_context` in any agent method.

## Agent File Locations

- **Base Class**: `agents/base_super_agent.py`
- **Existing Agents**: `agents/{commerce,creative,marketing,support,operations,analytics}_agent.py`
- **Tool Registry**: `orchestration/tool_registry.py`
- **LLM Router**: `llm/router.py`
- **Round Table**: `llm/round_table.py`

## Testing Pattern

```python
import pytest
from agents.new_agent import NewAgent

@pytest.mark.asyncio
async def test_new_agent_execution(tool_registry):
    agent = NewAgent(tool_registry=tool_registry)

    result = await agent.execute_task("Test task description")

    assert result["status"] == "completed"
    assert "results" in result
    assert len(result["artifacts"]) > 0
```

## Common Patterns

### Pattern 1: Commerce Operations

```python
# Product management
products = await self.use_tool("manage_products", {
    "operation": "create",
    "product_data": {...}
})

# Dynamic pricing
pricing = await self.use_tool("dynamic_pricing", {
    "strategy": "ml_based",
    "product_ids": [...]
})
```

### Pattern 2: Creative Generation

```python
# 3D asset generation
asset = await self.use_tool("generate_3d_from_description", {
    "prompt": "luxury hoodie design",
    "style": "photorealistic"
})

# Visual generation with Imagen/FLUX
images = await self.generate_visuals({
    "collection": "SIGNATURE",
    "prompt": "product photography setup"
})
```

### Pattern 3: Multi-Agent Coordination

```python
# Orchestrate multiple agents
workflow_result = await self.use_tool("multi_agent_workflow", {
    "agents": ["commerce", "creative", "marketing"],
    "task": "Launch new product collection",
    "coordination_strategy": "sequential"
})
```

## Next Steps

1. **Review** existing agents in `agents/` directory
2. **Understand** `EnhancedSuperAgent` base class capabilities
3. **Plan** new agent's domain, capabilities, and tool requirements
4. **Implement** following the SuperAgent pattern
5. **Test** with pytest suite
6. **Integrate** with LLM Router and Tool Registry
7. **Document** in `docs/` with examples

## References

See `references/` directory for:

- Advanced prompt techniques guide
- ML module capabilities
- Self-learning system architecture
- LLM Round Table detailed specs
- Tool category definitions
- Agent coordination patterns
