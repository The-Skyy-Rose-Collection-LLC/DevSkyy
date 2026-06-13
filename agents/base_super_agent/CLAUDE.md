# agents/base_super_agent/ — EnhancedSuperAgent foundation package

Modular runtime for the **6 legacy SuperAgents** (commerce, creative, marketing, operations, analytics, security_ops). Provides 17 prompt techniques + ML + self-learning + Round Table integration. **NOT the new self-healing hierarchy** — that's `agents/core/`.

## Critical context: four parallel hierarchies

DevSkyy has **four parallel agent base layers** (cmem #5160 verified 2026-05-15). Pick the right one:

| Layer | Base class | Adds | Used by |
|-------|-----------|------|---------|
| Legacy | `agents/base_legacy.py` | original SuperAgent shape | DEPRECATED — still has importers, do not delete yet (cmem #4323) |
| **This** | `EnhancedSuperAgent` (here) | 17 prompt techniques, ML, learning, Round Table | 6 legacy SuperAgents in `agents/*_agent.py` |
| Self-healing | `agents/core/CoreAgent` + `SubAgent` | diagnose / heal / circuit breaker / escalation | 8 CoreAgents in `agents/core/<domain>/` |
| SDK | `agents/claude_sdk/ClaudeSDKBaseAgent` | tool-use via Claude Agent SDK | standalone research/email/excel agents + SDKSubAgent for SDK-powered sub-agents |

**Zero agents combine self-heal + self-learn currently.** This is architectural debt, not a goal — when consolidating, the merge target is `agents/core/` (self-healing wins).

## Package layout

```
base_super_agent/
├── __init__.py            re-exports everything for back-compat
├── agent.py               EnhancedSuperAgent class (extends BaseDevSkyyAgent from adk.base)
├── learning_module.py     SelfLearningModule — records outcomes, adapts weights
├── ml_module.py           MLCapabilitiesModule + Sklearn/Prophet/TrendExtrapolation wrappers
├── prompt_module.py       PromptEngineeringModule + TaskCategoryAnalyzer (auto-selects 1 of 17 techniques)
├── round_table_module.py  LLMRoundTableInterface — wraps llm/round_table.py for high-stakes tasks
└── types.py               SuperAgentType, TaskCategory, LLMProvider, AGENT_PROVIDER_PREFERENCES, ROUND_TABLE_QUALITY_THRESHOLD
```

## Surface (from `__init__.py`)

| Symbol | File | Role |
|--------|------|------|
| `EnhancedSuperAgent` | `agent.py` | Base for the 6 legacy SuperAgents |
| `PromptEngineeringModule`, `TaskCategoryAnalyzer`, `get_task_analyzer` | `prompt_module.py` | Auto-selects 1 of 17 prompt techniques per task |
| `MLCapabilitiesModule`, `SklearnModelWrapper`, `ProphetModelWrapper`, `TrendExtrapolationWrapper` | `ml_module.py` | ML model registry + Prophet forecasting |
| `SelfLearningModule` | `learning_module.py` | Tracks `LearningRecord`s — outcome-based weight updates |
| `LLMRoundTableInterface` | `round_table_module.py` | Round-Table gateway — invoked when task is `HIGH_STAKES` |
| `SuperAgentType`, `TaskCategory`, `LLMProvider` | `types.py` | Enums (StrEnum) |
| `AGENT_PROVIDER_PREFERENCES`, `TASK_PROVIDER_PREFERENCES` | `types.py` | Routing tables: agent_type/task_type → preferred LLM provider |
| `HIGH_STAKES_TASK_TYPES`, `HIGH_STAKES_AGENT_TYPES`, `ROUND_TABLE_QUALITY_THRESHOLD`, `ROUND_TABLE_SCORING_WEIGHTS` | `types.py` | Round Table activation thresholds |
| `LLM_ROUTER_AVAILABLE`, `PRODUCTION_ROUND_TABLE_AVAILABLE` | flag exports | Soft-import availability indicators |

## Module composition (from `agent.py`)

```python
class EnhancedSuperAgent(BaseDevSkyyAgent):  # from adk.base
    agent_type: SuperAgentType = None
    sub_capabilities: list[str] = []

    def __init__(self, config: AgentConfig, *, rag_manager=None, ml_pipeline=None,
                 llm_client=None, cache=None):
        super().__init__(config)
        # Composes:
        # - PromptEngineeringModule
        # - MLCapabilitiesModule
        # - SelfLearningModule
        # - LLMRoundTableInterface
        # - LLMRouter (if available)
        # - ToolRegistry
```

**Key fact:** imports `AgentConfig`, `AgentResult`, `AgentStatus` exclusively from `adk.base` — NOT from `agents/models.py` (cmem #4995). When adding fields to these types, update `adk/base.py`.

## Round Table activation

Round Table fires automatically when **either** condition true:
- `task_type in HIGH_STAKES_TASK_TYPES` (e.g. brand-critical copy, security audit)
- `agent_type in HIGH_STAKES_AGENT_TYPES`

When fired:
1. Fan-out to providers in `AGENT_PROVIDER_PREFERENCES[agent_type]` (or `TASK_PROVIDER_PREFERENCES[task_type]`).
2. Score with `ROUND_TABLE_SCORING_WEIGHTS`.
3. Filter by `ROUND_TABLE_QUALITY_THRESHOLD` — if no response clears, escalate.
4. Persist to Neon via `RoundTableDatabase` (in `llm/round_table.py`).

Cost-prohibitive for hot paths — keep thresholds tight.

## Conventions

- **Subclasses must set `agent_type: SuperAgentType`** at class scope. Module-level enum constant.
- **`sub_capabilities: list[str]`** — declares what the agent handles. Used by routing tables + dashboard.
- **Async public API.** All agent methods are `async def` — composed modules expose async interfaces.
- **Optional dependency injection** — `rag_manager`, `ml_pipeline`, `llm_client`, `cache` are kwargs. Don't instantiate them inside the agent; pass via constructor or default to lazy-loaded singletons.
- **`structlog` for structured logging** (matching the orchestration convention). `bind_contextvars` / `unbind_contextvars` from `core.structured_logging` wrap each task.
- **17 prompt techniques** include: Chain-of-Thought, Tree-of-Thoughts, ReAct, Self-Consistency, Few-Shot, Role-Based, RAG, Constitutional, Step-Back, Multi-Agent Debate, etc. `TaskCategoryAnalyzer` auto-selects; override via `PromptTechniqueResult.technique` if needed.

## Don't

- Don't add new SuperAgents here unless the architecture team decides to extend the legacy hierarchy. **New domain agents go into `agents/core/<domain>/`** (self-healing path).
- Don't bypass `_llm_execute` to call provider SDKs directly. Routing + cost tracking + Round Table activation all live in the composed modules.
- Don't import `Message`/`ModelProvider` from `llm.base` at module top-level unless `LLM_ROUTER_AVAILABLE` is checked — the soft-import pattern at `agent.py:29-39` is intentional.
- Don't re-export the monolithic `agents/base_super_agent.py` file — it's a parallel duplicate (cmem #297) and the package wins. The flat file exists for legacy importers only.

## Related

- Round Table engine: `llm/round_table.py` (text completion only — separate from `orchestration/threed_round_table.py`)
- Prompt techniques: `orchestration/prompt_engineering.py` `PromptTechnique` enum
- LLM router: `llm/router.py`
- Legacy concrete agents extending this: `agents/commerce_agent.py`, `agents/creative_agent.py`, `agents/marketing_agent.py`, `agents/operations_agent.py`, `agents/analytics_agent.py`, `agents/security_ops_agent.py`
- ADK foundation (`BaseDevSkyyAgent`, `AgentConfig`, `AgentResult`, `AgentStatus`): `adk/base.py`

## Recent learnings

- `EnhancedSuperAgent` has NO self-healing surface (cmem #5016 verified 2026-05-14). For diagnose/heal/escalate, the agent must inherit `SelfHealingMixin` from `agents/core/base.py` — currently no agent does both.
- Monolithic `agents/base_super_agent.py` exists alongside this package (cmem #297). The package wins via `__init__.py` re-export; the flat file is kept for back-compat importers.
- `agents/base_legacy.py` still has active importers as of 2026-05-13 (cmem #4323) — **don't delete yet**, even though new code must use this package.
- Per `model_ids.py` migration (2026-05-05, cmem #2103): all 8 production agent files aligned to elite-team model policy tiers. New agents must use `model_ids.py` aliases, not hardcoded model strings.


