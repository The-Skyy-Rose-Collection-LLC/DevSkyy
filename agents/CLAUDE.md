# DevSkyy Agents

> Hierarchical AI Agent System | 8 Core Agents + 1 Orchestrator | Universal Self-Healing

---

## Architecture (NEW — March 2026)

```
Orchestrator (routes, escalates, Round Table consensus)
├── CommerceCoreAgent    — products, orders, pricing, inventory
├── ContentCoreAgent     — pages, blogs, SEO, copy
├── CreativeCoreAgent    — design system, brand, assets
├── MarketingCoreAgent   — campaigns, social, audience
├── OperationsCoreAgent  — deploy, security, health, code quality
├── AnalyticsCoreAgent   — data, trends, conversion
├── ImageryCoreAgent     — photos, VTON, 3D models
└── WebBuilderCoreAgent  — theme generation, deployment
```

Every component inherits **SelfHealingMixin**: `diagnose()` → `heal()` → `health_check()` → `circuit_breaker()`

Escalation chain: **sub-agent → core agent → orchestrator → human**

---

## Directory Structure

```
agents/
├── core/                          # NEW hierarchical system
│   ├── __init__.py                # Exports: CoreAgent, SubAgent, Orchestrator, etc.
│   ├── base.py                    # SelfHealingMixin + CoreAgent base + enums
│   ├── sub_agent.py               # SubAgent base class
│   ├── orchestrator.py            # Top-level Orchestrator (routing, budget, health)
│   ├── commerce/                  # CommerceCoreAgent
│   │   ├── agent.py
│   │   └── sub_agents/            # wordpress_assets, (product_manager, pricing_engine...)
│   ├── content/                   # ContentCoreAgent
│   │   ├── agent.py
│   │   └── sub_agents/            # collection_content, (seo_content, copywriter...)
│   ├── creative/                  # CreativeCoreAgent
│   │   ├── agent.py
│   │   └── sub_agents/
│   ├── marketing/                 # MarketingCoreAgent
│   │   ├── agent.py
│   │   └── sub_agents/            # social_media, (campaign_manager, ab_testing...)
│   ├── operations/                # OperationsCoreAgent
│   │   ├── agent.py
│   │   └── sub_agents/            # security_monitor, coding_doctor
│   ├── analytics/                 # AnalyticsCoreAgent
│   │   ├── agent.py
│   │   └── sub_agents/
│   ├── imagery/                   # ImageryCoreAgent
│   │   ├── agent.py
│   │   └── sub_agents/            # gemini_image, fashn_vton, tripo_3d, meshy_3d, hf_spaces
│   └── web_builder/               # WebBuilderCoreAgent
│       ├── agent.py
│       └── sub_agents/
├── base_super_agent.py            # Legacy base (EnhancedSuperAgent, 17 techniques)
├── base_legacy.py                 # ⚠️ DEPRECATED — 5 files still import (migration pending)
├── elite_web_builder/             # Legacy WordPress agent (wrapped by WebBuilderCoreAgent)
├── commerce_agent.py              # Legacy (wrapped by CommerceCoreAgent)
├── creative_agent.py              # Legacy (wrapped by CreativeCoreAgent)
├── marketing_agent.py             # Legacy (wrapped by MarketingCoreAgent)
├── ...                            # Other legacy agents (all still importable)
└── __init__.py                    # Package exports (core + legacy)
```

---

## Base Classes (Use These)

### For new agents — use the core hierarchy:

```python
from agents.core.base import CoreAgent, CoreAgentType, SelfHealingMixin
from agents.core.sub_agent import SubAgent

class MySubAgent(SubAgent):
    name = "my_sub_agent"
    parent_type = CoreAgentType.COMMERCE
    description = "Does a specific thing"
    capabilities = ["capability_a", "capability_b"]

    async def execute(self, task: str, **kwargs) -> dict:
        # Your logic here — self-healing is automatic via execute_safe()
        return {"success": True, "result": "done"}
```

### For legacy compatibility — existing agents still work:

```python
from adk.base import BaseDevSkyyAgent
from agents.base_super_agent import EnhancedSuperAgent
```

---

## Key Types

| Type | Location | Purpose |
|------|----------|---------|
| `SelfHealingMixin` | `core/base.py` | Universal self-healing (diagnose/heal/circuit breaker) |
| `CoreAgent` | `core/base.py` | Base for 8 domain agents |
| `SubAgent` | `core/sub_agent.py` | Base for specialized sub-agents |
| `Orchestrator` | `core/orchestrator.py` | Top-level router + budget gate |
| `CoreAgentType` | `core/base.py` | Enum: COMMERCE, CONTENT, CREATIVE, etc. |
| `FailureCategory` | `core/base.py` | Enum: CODE_BUG, CONFIG, EXTERNAL, etc. |
| `CircuitBreakerState` | `core/base.py` | Enum: CLOSED, OPEN, HALF_OPEN |

---

## Self-Healing Pattern

Every agent (core + sub) inherits SelfHealingMixin:

1. **Circuit Breaker** — CLOSED → OPEN (5 failures) → HALF_OPEN (cooldown) → CLOSED
2. **Diagnose** — Categorizes failure (CODE_BUG, CONFIG, EXTERNAL, etc.)
3. **Heal** — Up to 3 attempts with strategy based on category
4. **Escalate** — Sub-agent → parent CoreAgent → Orchestrator → human
5. **Learn** — Records fix in bounded learning journal (LRU, max 100 entries)

---

## Learnings (Update When Claude Makes Mistakes)

### Agent Base Classes

- ❌ **Mistake**: Using `base_legacy.py` or `operations_legacy.py`
  - ✅ **Correct**: New agents use `core/base.py` (SelfHealingMixin + CoreAgent). Legacy agents use `adk/base_super_agent.py`

- ❌ **Mistake**: Creating agent without proper __init__ signature
  - ✅ **Correct**: Always accept `correlation_id` as keyword-only arg

- ❌ **Mistake**: Not propagating correlation_id through agent calls
  - ✅ **Correct**: Pass `correlation_id=correlation_id` to all sub-calls

- ❌ **Mistake**: Ad-hoc try/except for agent failures
  - ✅ **Correct**: Use `execute_safe()` which wraps with circuit breaker + self-healing automatically

### Agent Orchestration

- ❌ **Mistake**: Creating tight coupling between agents
  - ✅ **Correct**: Agents communicate via the Orchestrator, not direct method calls

- ❌ **Mistake**: Not handling agent failures gracefully
  - ✅ **Correct**: SelfHealingMixin handles this — diagnose → heal → escalate

- ❌ **Mistake**: Using unbounded dict/set for per-agent tracking
  - ✅ **Correct**: Use OrderedDict with `popitem(last=False)` for FIFO eviction (max_size guard)

### Round Table

- ❌ **Mistake**: Using round table for simple tasks
  - ✅ **Correct**: Round table is for complex multi-perspective analysis only (3+ agents)

- ❌ **Mistake**: Not setting proper voting thresholds
  - ✅ **Correct**: Use 66% consensus threshold (configurable)

---

## Verification

```bash
# Check core hierarchy imports
python -c "from agents.core import CoreAgent, SubAgent, Orchestrator, SelfHealingMixin; print('Core hierarchy OK')"

# Check no deleted legacy imports
rg "operations_legacy" agents/ && echo "FAIL: operations_legacy references found" || echo "OK"

# Run agent tests
pytest tests/unit/test_agents.py -v
```

---

**"Self-healing at every level. Escalation, not failure."**
