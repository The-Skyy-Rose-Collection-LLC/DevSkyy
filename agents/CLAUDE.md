<claude-mem-context>

</claude-mem-context>

# agents/ — SuperAgent layer (162 Python files)

The brain of DevSkyy. Six SuperAgents handle the major domains, each consolidating what used to be many narrow agents.

## SuperAgents (one file each)

- `commerce_agent.py` — products, orders, inventory, pricing, payments, fulfillment
- `creative_agent.py` — copy, brand voice, content generation
- `marketing_agent.py` — campaigns, social posting, paid media
- `operations_agent.py` — workflow ops, internal tooling
- `analytics_agent.py` — reporting, metrics, demand forecasting (Prophet)
- `security_ops_agent.py` — auth, secrets, audit log

## SkyyRose-specific agents

- `skyyrose_content_agent.py`, `skyyrose_imagery_agent.py`, `skyyrose_spaces_orchestrator.py`
- `fashn_agent.py` — FASHN virtual try-on (gated by `/preflight`)
- `tripo_agent.py`, `meshy_agent.py` — 3D model generation
- `asset_tagging_agent.py`, `collection_content_agent.py` — collection/SKU work

## Base architecture

```python
# Correct import (current):
from agents.core.base import SuperAgent, AgentConfig, AgentCapability

# Wrong import (DEPRECATED):
from agents.base_legacy import ...   # do not use; will be removed
```

`base_super_agent/` carries the modular runtime: `agent.py`, `learning_module.py`, `ml_module.py`, `prompt_module.py`, `round_table_module.py`, `types.py`. Custom agents extend `SuperAgent` from `agents.core.base`.

## Conventions

- Every agent file starts with a module docstring naming its consolidated responsibilities and ML capabilities. Match the pattern when adding new agents.
- Use `StrEnum` for capability enums and `from __future__ import annotations` at top.
- Errors raised by agents go through `agents/errors.py` — use the existing exception classes; do not raise raw `RuntimeError`.
- Any new agent MUST be reachable from `api/agents.py` or one of the dashboard endpoints — orphan agents do not ship.

## Don't

- Don't import from `base_legacy.py`. It's marked deprecated.
- Don't bypass `agents.core.base.SuperAgent` to write a "lighter" base. Add functionality to the base if needed.
- Don't call FASHN, Tripo, or Meshy APIs directly from anywhere outside the corresponding agent. The agents handle preflight, retry, and cost gating.

## Related

- Endpoints that expose these agents: `api/agents.py`, `api/dashboard.py`
- Pipelines that compose them: `orchestration/asset_pipeline.py`, `orchestration/agent_counter.py`
- MCP exposure: `mcp_servers/agent_bridge_server.py`
