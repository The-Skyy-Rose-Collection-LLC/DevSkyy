# agents/claude_sdk/ — Claude Agent SDK integration (6-layer stack)

Deep integration of Anthropic's Claude Agent SDK into DevSkyy. Six layers, from standalone agents up to a full Dashboard Orchestrator. Any `CoreAgent` or `SubAgent` can inherit `SDKCapabilityMixin` to gain tool-use, multi-agent delegation, and stateful sessions.

## Layer map (cmem #4094, 2026-05-12)

| Layer | Module | Surface | When to use |
|-------|--------|---------|-------------|
| 1 — Base | `base.py` | `ClaudeSDKBaseAgent`, `SDKAgentConfig` | Build a standalone SDK-powered agent from scratch |
| 1 — Standalone agents | `research.py`, `email_automation.py`, `excel_handler.py`, `session.py` | `ResearchAgent`, `EmailAutomationAgent`, `ExcelHandlerAgent`, `SessionManager` | Out-of-the-box SDK agents for common tasks |
| 2 — Capability mixin | `mixin.py` | `SDKCapabilityMixin`, `SDKExecutionResult` | Grant SDK execution to ANY existing agent (mix into your class) |
| 3 — SDK sub-agent | `sdk_sub_agent.py` | `SDKSubAgent` | Build a SubAgent powered by SDK with tool use (combine `SubAgent` + `SDKCapabilityMixin`) |
| 4 — Hook system | `hooks.py` | `DevSkyyHookSystem`, `HookMetrics` | Wire SDK hooks → DevSkyy self-healing → telemetry |
| 5 — Tool profiles | `tool_bridge.py` | `ToolProfile`, `build_researcher_agent`, `build_analyst_agent`, `build_writer_agent`, `build_code_agent`, `build_domain_agents` | Reusable `AgentDefinition` builders with domain-aware tool sets |
| 6 — Dashboard | `dashboard.py` | `DashboardOrchestrator`, `DashboardRequest`, `DashboardResult`, `DashboardHealthResponse` | Top-level multi-agent orchestration with dual modes |

## Package layout

```
claude_sdk/
├── __init__.py            soft-imports every layer (graceful degradation if SDK missing)
├── base.py                ClaudeSDKBaseAgent — wraps ClaudeSDKClient with structured logging + telemetry
├── research.py            ResearchAgent — multi-step research workflow
├── email_automation.py    EmailAutomationAgent — inbox triage
├── excel_handler.py       ExcelHandlerAgent — spreadsheet ingestion + transforms
├── session.py             SessionManager + SessionConfig — stateful multi-turn
├── mixin.py               SDKCapabilityMixin — grants _sdk_execute / _sdk_delegate / _sdk_session
├── sdk_sub_agent.py       SDKSubAgent = SubAgent + SDKCapabilityMixin
├── hooks.py               DevSkyyHookSystem — SDK hooks → self-healing wiring
├── tool_bridge.py         ToolProfile enum + build_* factory functions
├── dashboard.py           DashboardOrchestrator — top-level coordinator
├── domain_agents/         12 domain-specific SDK agents (commerce, marketing, etc.)
├── prompts/               .txt files with reusable system prompts
└── utils/                 recalc.py + tracker.py — telemetry helpers
```

## Surface (from `__init__.py`)

```python
# Layer 1: Standalone agents
ClaudeSDKBaseAgent, SDKAgentConfig
ResearchAgent, ResearchRequest, ResearchResult
EmailAutomationAgent, EmailTriageRequest, EmailTriageResult
ExcelHandlerAgent, ExcelRequest, ExcelResult
SessionManager, SessionConfig

# Layer 4: Hooks
DevSkyyHookSystem, HookMetrics

# Layer 2-3: Mixin + SDK sub-agent
SDKCapabilityMixin, SDKExecutionResult
SDKSubAgent

# Layer 5: Tool profiles
ToolProfile
build_researcher_agent, build_analyst_agent, build_writer_agent, build_code_agent, build_domain_agents

# Layer 6: Dashboard
DashboardOrchestrator, DashboardRequest, DashboardResult, DashboardHealthResponse
```

## SDKCapabilityMixin — granting SDK powers to any agent

```python
from agents.core.sub_agent import SubAgent
from agents.claude_sdk import SDKCapabilityMixin

class MyResearchSubAgent(SubAgent, SDKCapabilityMixin):
    name = "my_research"
    parent_type = CoreAgentType.CONTENT
    sdk_tools = ["Read", "Write", "Bash", "WebSearch"]  # whitelist

    async def execute(self, task, **kwargs):
        # Inherited from mixin:
        result = await self._sdk_execute(task, system_prompt="...")
        return result
```

Three methods granted by the mixin:
- `_sdk_execute()` — full tool-use execution
- `_sdk_delegate()` — multi-agent orchestration (sub-agents within sub-agents)
- `_sdk_session()` — stateful multi-turn conversation

## DashboardOrchestrator — dual modes

Per cmem #4094, the dashboard orchestrator has two operating modes:

1. **Auto mode** — Dashboard routes tasks via its own LLM judgment, picks the right domain agent, executes, returns.
2. **Manual mode** — Caller specifies the target agent + task; Dashboard handles execution + telemetry only.

`DashboardHealthResponse` exposes per-agent health for the 3D portal.

## Base config (`SDKAgentConfig`)

```python
@dataclass(frozen=True)
class SDKAgentConfig:
    model: str = "haiku"                  # default — use "sonnet" for harder tasks
    permission_mode: str = "bypassPermissions"   # SDK auto-confirms tool use
    max_turns: int = 50                   # safety cap on agent loop
    output_dir: Path = Path("data")       # where structured outputs land
```

**`permission_mode: bypassPermissions`** is the default — the agent will execute tool calls without per-call confirmation. **The DevSkyy STOP AND SHOW gates remain** at the SubAgent / domain-agent layer; SDK bypass is for the inner SDK tool loop only.

## Conventions

- **Soft imports throughout.** `__init__.py` wraps every import in try/except so a missing optional dep doesn't break the whole package. Check `is not None` before using.
- **`structlog` for SDK agents.** Per `base.py:25` — `logger = structlog.get_logger(__name__)`. Telemetry events include `correlation_id`, `agent`, `turn`, `tool_calls`.
- **`DevSkyySubagentTracker`** tracks sub-agent invocations within an SDK loop. Pull metrics via `HookMetrics`.
- **Template Method base.** `ClaudeSDKBaseAgent` defines the flow; subclasses override `_build_agents()` + `_build_system_prompt()`. Don't override the lifecycle methods directly.
- **Output directory required.** SDK agents write structured outputs to `config.output_dir` (default `data/`). Don't let agents write to arbitrary paths.

## Don't

- Don't use `permission_mode="bypassPermissions"` for agents that touch production. Combine with STOP AND SHOW at the parent SubAgent layer so the human gate is preserved.
- Don't import this package eagerly from hot-path code. `claude_agent_sdk` has heavy startup cost — lazy-import where possible.
- Don't bypass `DevSkyyHookSystem` to wire raw SDK hooks. The hook system bridges SDK events into self-healing diagnose → heal cycle; raw hooks lose that integration.
- Don't define a new `AgentDefinition` from scratch — use `tool_bridge.build_*` factories so tool profiles stay consistent across agents.
- Don't store SDK secrets in code. `ANTHROPIC_API_KEY` from env only.

## Related

- Underlying SDK: `claude_agent_sdk` package (Anthropic)
- Self-healing layer: `agents/core/base.py` (`SelfHealingMixin`)
- SubAgent base: `agents/core/sub_agent.py` (composes with this mixin)
- Domain SDK agents: `agents/claude_sdk/domain_agents/` (12 files, one per domain)
- Reusable prompts: `agents/claude_sdk/prompts/` (.txt — `research_lead`, `researcher`, `data_analyst`, `email_triage`, `report_writer`)
- Telemetry: `agents/claude_sdk/utils/tracker.py` (`DevSkyySubagentTracker`)

## Recent learnings

- Six-layer architecture confirmed (cmem #4094, 2026-05-12 + #5477, 2026-05-19).
- All `__init__.py` imports use try/except — be defensive when consuming; symbols may be `None` if SDK absent.
- `ClaudeSDKBaseAgent` uses Template Method pattern — override `_build_agents()` / `_build_system_prompt()`, not lifecycle methods.
- Combining `SubAgent` + `SDKCapabilityMixin` = `SDKSubAgent` (already provided in `sdk_sub_agent.py`); don't re-derive — inherit `SDKSubAgent` directly.
