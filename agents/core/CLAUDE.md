# agents/core/ — Domain-partitioned agent hierarchy (8 cores + Orchestrator)

The **self-healing** agent layer. 8 domain CoreAgents + 1 Orchestrator, each with `SelfHealingMixin` (diagnose → heal → escalate → circuit-breaker). New agent code goes here, not in `agents/base_super_agent/`.

## Hierarchy

```
Orchestrator                            (single root, all cores connect to it)
    ├── CommerceCore       (4 sub-agents)   products / orders / pricing / WP-bridge
    ├── ContentCore        (3 sub-agents)   copy / SEO / blog
    ├── CreativeCore       (4 sub-agents)   brand voice / visual identity / design
    ├── MarketingCore      (3 sub-agents)   social / campaigns / A/B
    ├── OperationsCore     (4 sub-agents)   deploy / security / health / build
    ├── AnalyticsCore      (3 sub-agents)   metrics / forecast / reports
    ├── ImageryCore        (5 sub-agents)   gemini_image / fashn_vton / tripo_3d / meshy_3d / hf_spaces
    └── WebBuilderCore     (5 sub-agents)   theme / template / pattern / Elementor / blocks
```

## Self-Healing Flow

```
1. Agent executes task
2. Failure detected → diagnose(failure) → Diagnosis(failure_category, suggested_actions)
3. heal(diagnosis) → retry with different params (3 attempts max)
4. Still failing → escalate_to_parent()  (sub-agent → core)
                  → escalate_to_orchestrator()  (core → orchestrator)
                  → escalate_to_dashboard()  (orchestrator → human via 3D portal)

Circuit Breaker (per-agent):
    CLOSED      → normal operation
    OPEN        → 5 consecutive failures → stop attempting, alert
    HALF_OPEN   → cooldown expired → try one request → close or re-open
```

## Surface (from `__init__.py`)

| Symbol | File | Role |
|--------|------|------|
| `SelfHealingMixin` | `base.py` | diagnose / heal / health_check / circuit_breaker — every agent inherits |
| `CoreAgent` | `base.py` | Base for the 8 domain cores (`SelfHealingMixin` + sub-agent registry) |
| `CoreAgentType` | `base.py` | StrEnum: COMMERCE, CONTENT, CREATIVE, MARKETING, OPERATIONS, ANALYTICS, IMAGERY, WEB_BUILDER, ORCHESTRATOR |
| `SubAgent` | `sub_agent.py` | Base for sub-agents (handles narrow tasks within a domain) |
| `Orchestrator` | `orchestrator.py` | Top-level router + escalation endpoint |
| `FailureCategory` | `base.py` | code_bug, config, wrong_approach, external, data_quality, provider_down |
| `CircuitBreakerState` | `base.py` | closed, open, half_open |
| `Diagnosis`, `HealAttempt`, `HealResult`, `HealCycleResult`, `HealthStatus` | `base.py` | Frozen dataclasses for heal cycle bookkeeping |
| `WordPressAIBridge` | `shared/wp_ai_bridge.py` | Shared WP/WC bridge used by Commerce + WebBuilder + Content cores |
| `create_orchestrator` | `factory.py` | Factory — builds an Orchestrator with all 8 cores pre-registered |

## Files

```
core/
├── base.py                    SelfHealingMixin + CoreAgent + circuit breaker + dataclasses
├── sub_agent.py               SubAgent base (lazy UnifiedLLMClient via _llm_execute)
├── orchestrator.py            Orchestrator + _ROUTING_RULES (keyword → CoreAgentType)
├── factory.py                 create_orchestrator() — wires all 8 cores
├── validation_scoring.py      Output validation scoring (used by heal cycle for quality gate)
├── shared/                    Cross-domain helpers (wp_ai_bridge.py)
├── commerce/                  CommerceCoreAgent + 3 sub-agents
├── content/                   ContentCoreAgent + 3 sub-agents
├── creative/                  CreativeCoreAgent + 4 sub-agents
├── marketing/                 MarketingCoreAgent + 2 sub-agents
├── operations/                OperationsCoreAgent + 4 sub-agents
├── analytics/                 AnalyticsCoreAgent + 3 sub-agents
├── imagery/                   ImageryCoreAgent + 5 sub-agents (gemini, fashn, tripo, meshy, hf_spaces)
└── web_builder/               WebBuilderCoreAgent + 5 sub-agents
```

Each domain dir has its own `CLAUDE.md` with sub-agent specifics + routing rules.

## Orchestrator routing (`_ROUTING_RULES`)

Keyword → CoreAgentType matching. First-match-wins on lowercased task string:

| Keywords | Routed to |
|----------|-----------|
| `product`, `order`, `inventory`, `price`, `payment`, `cart`, `woocommerce` | `COMMERCE` |
| `content`, `copy`, `blog`, `seo`, `page`, `description`, `text` | `CONTENT` |
| `design`, `brand`, `visual`, `logo`, `creative`, `style`, `color` | `CREATIVE` |
| `campaign`, `social`, `marketing`, `email`, `audience`, `ad` | `MARKETING` |
| `deploy`, `security`, `health`, `monitor`, `build`, `ci`, `code quality` | `OPERATIONS` |
| `analytics`, `data`, `report`, `forecast`, `trend`, `conversion`, `metric` | `ANALYTICS` |
| `image`, `photo`, `3d`, `model`, `render`, `vton`, `try-on`, `asset` | `IMAGERY` |
| `theme`, `template`, `wordpress`, `web build`, `site`, `page template` | `WEB_BUILDER` |

Unmatched → defaults to Orchestrator's own LLM judgment.

## Conventions

- **Inherit `SelfHealingMixin`.** Even root-level helpers should — heal cycle is the universal contract.
- **`core_type: CoreAgentType`** class-level attribute on every CoreAgent subclass.
- **`name`, `description`** as class attributes — used by Orchestrator dashboard + 3D portal.
- **Sub-agents register at init.** CoreAgent subclasses call `self._register_sub_agents()` from `__init__`. Use `importlib.import_module` for graceful fallback on missing sub-agents.
- **ALIASES tuple** on sub-agents for backward-compatible routing. E.g. `ProductOpsSubAgent.ALIASES = ("product_manager", "pricing_engine", "inventory_tracker", "order_processor")` — old callers still route correctly.
- **LLM calls via `_llm_execute()`** in `SubAgent`. Routes through `UnifiedLLMClient` (lazy singleton). Don't call provider SDKs directly.
- **Errors → `agents/errors.py` `AgentError`** with `ErrorCategory` enum. Don't raise raw `RuntimeError` / `Exception`.
- **Promoted from `elite_web_builder/core/self_healer.py`.** This is now the universal self-healing implementation — `elite_web_builder` still uses its own; eventual consolidation target is this `base.py`.

## Don't

- Don't add a CoreAgent without registering it in `factory.create_orchestrator()` + `Orchestrator._ROUTING_RULES`.
- Don't reach across cores. Cross-domain coordination goes through Orchestrator (or via shared helpers in `shared/`).
- Don't bypass `SelfHealingMixin`. If a task can fail, it goes through heal → escalate.
- Don't write business logic in `Orchestrator` — it's a router, not a worker. Worker logic lives in domain CoreAgents.
- Don't reintroduce per-domain healers. The implementation in `base.py` is the universal one; `elite_web_builder/core/self_healer.py` is legacy slated for removal.

## Related

- Pre-self-healing layer: `agents/base_super_agent/` (legacy SuperAgents) — has Round Table + 17 prompt techniques but no self-heal
- SDK-powered sub-agents: `agents/claude_sdk/sdk_sub_agent.py` `SDKSubAgent` (combine with `SubAgent` for tool-use sub-agents)
- LLM routing: `llm/unified_llm_client.py` (consumed by `SubAgent._llm_execute`)
- Errors: `agents/errors.py`
- 3D portal escalation endpoint: `api/dashboard.py`

## Recent learnings

- **Four parallel hierarchies exist** (cmem #5160 verified 2026-05-15): `base_legacy.py`, `base_super_agent/`, `agents/core/`, `agents/claude_sdk/`. Zero agents currently have both heal AND learn — architectural debt, not a goal.
- Hexagonal architecture violation verified (cmem #2351, 2026-05-06): orchestration imports leak into the domain core layer. Acceptable for now; track for future refactor.
- `orchestrator.py`, `sub_agent.py`, `validation_scoring.py` were previously undocumented top-level files (cmem #5475, 2026-05-19). Now covered here.
- `agents/core/base.py` `SelfHealingMixin` was promoted from `elite_web_builder/core/self_healer.py`. The `elite_web_builder` version is the older copy — converge on this one.
