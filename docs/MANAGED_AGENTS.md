# Managed Agents — Claude Agent SDK Integration

DevSkyy's managed-agent layer wraps the `claude-agent-sdk` Python package (currently `0.1.41`) into two complementary stacks. This document is the onboarding entry point for adding a new agent, calling an existing one, or extending the platform.

---

## Prerequisites

| Tool | Version verified | Install |
|------|------------------|---------|
| Python | 3.11+ (running on 3.14) | `make install` |
| `claude-agent-sdk` | `>=0.1.18` (installed `0.1.41`) | pulled by core deps in `pyproject.toml` |
| `claude` CLI (Node backend) | `2.1.140` | `npm install -g @anthropic-ai/claude-code` |
| Node.js | `v25.6.1` | system install |
| `ANTHROPIC_API_KEY` | required | export or `.env` (do not commit) |

The Python SDK shells out to the Node `claude` CLI. Both must be present on `PATH`.

### Environment

```bash
# In repo root
set -a; source .env; set +a
python3 -c "import claude_agent_sdk; print(claude_agent_sdk.__version__)"
# expected: 0.1.41 (or newer)
```

---

## Two Stacks, One SDK

DevSkyy has two parallel managed-agent surfaces. Pick the one whose ergonomics match your task — they coexist and share the same `claude-agent-sdk` primitives.

### Stack A — `agents/claude_sdk/` (class-based)

Use when:
- You want to subclass a base agent and override system prompt / tools / subagents.
- You need to wire SDK execution into an existing `SuperAgent` or `SubAgent` via mixin.
- You want pre-built domain specialists (16 ready-to-use agents).

Layout:

```
agents/claude_sdk/
├── base.py              # ClaudeSDKBaseAgent — subclass this for new agents
├── session.py           # SessionManager — multi-turn conversations
├── mixin.py             # SDKCapabilityMixin — grant SDK powers to any agent
├── sdk_sub_agent.py     # SDKSubAgent — sub-agent backed by SDK
├── hooks.py             # DevSkyyHookSystem — telemetry + self-healing
├── tool_bridge.py       # ToolProfile + build_{researcher,analyst,writer,code}_agent
├── domain_agents/       # 16 prebuilt: analytics, brand_guardian, commerce, content,
│                        #   creative, customer_intelligence, imagery, immersive,
│                        #   influencer, marketing, operations, seo_discovery,
│                        #   supply_chain, web_builder, community
├── prompts/             # Reusable .txt system prompts (researcher, data_analyst, …)
├── utils/tracker.py     # DevSkyySubagentTracker — Pre/PostToolUse hooks
├── research.py          # Standalone ResearchAgent
├── email_automation.py  # Standalone EmailAutomationAgent
├── excel_handler.py     # Standalone ExcelHandlerAgent
└── dashboard.py         # DashboardOrchestrator
```

### Stack B — `skyyrose/multi_agent/` (function-based orchestrator)

Use when:
- You need a CLI-driven multi-agent workflow with brand-specific MCP tools.
- You want budget-capped one-shot or interactive sessions.
- You want the orchestrator to delegate to brand subagents (`brand-writer`, `theme-auditor`, `product-analyst`, `deploy-manager`, `qa-inspector`).

Layout:

```
skyyrose/multi_agent/
├── __main__.py     # python -m skyyrose.multi_agent "..."
├── orchestrator.py # run_orchestrator() + run_single_agent()
├── agents.py       # AGENT_DEFINITIONS dict
├── tools.py        # 11 MCP tools → skyyrose_mcp_server
├── hooks.py        # audit_tool_use, guard_bash, log_file_edit, report_progress
└── config.py       # ORCHESTRATOR_MODEL, SUBAGENT_MODEL, MAX_BUDGET_USD, REPO_DIR
```

CLI:

```bash
# Orchestrator with budget cap
python -m skyyrose.multi_agent --budget 2.0 "Audit theme for a11y"

# Single subagent
python -m skyyrose.multi_agent --agent brand-writer "Write captions for br-001"

# Interactive
python -m skyyrose.multi_agent --interactive "Let's review the platform"

# List agents
python -m skyyrose.multi_agent --list-agents
```

---

## Core SDK Primitives (what each layer uses)

All DevSkyy agents compose these `claude_agent_sdk` primitives:

| Primitive | Role |
|-----------|------|
| `ClaudeAgentOptions` | Single config object — system prompt, model, tools, hooks, MCP servers, budget, permission mode, agents map |
| `ClaudeSDKClient` | Async context manager for stateful multi-turn conversations |
| `query()` | Async generator for one-shot prompts (no client lifecycle) |
| `AgentDefinition` | Subagent definition (prompt + tools + description) — passed via `agents={}` |
| `HookMatcher` | Bind a hook fn to a tool-name regex (PreToolUse / PostToolUse / UserPromptSubmit) |
| `create_sdk_mcp_server` + `@tool` | Define in-process MCP tools — exposed as `mcp__<server>__<tool>` |
| `AssistantMessage`, `TextBlock`, `ToolUseBlock`, `ResultMessage` | Stream parsing |

Permission modes: `default` | `acceptEdits` | `plan` | `bypassPermissions` | `dontAsk` | `auto`.

---

## Recipe 1 — Add a new domain agent (Stack A)

Goal: ship a new SKU-pricing-strategist agent.

1. **Create file** `agents/claude_sdk/domain_agents/pricing.py`.

```python
"""SKU pricing strategist powered by Claude Agent SDK."""
from __future__ import annotations

from claude_agent_sdk import AgentDefinition

from agents.claude_sdk.base import ClaudeSDKBaseAgent


class SDKPricingStrategistAgent(ClaudeSDKBaseAgent):
    """Analyze SKU pricing across collections and suggest adjustments."""

    def _build_system_prompt(self) -> str:
        return (
            "You are the SkyyRose pricing strategist. Use the product catalog "
            "tools to read current prices, compare against brand positioning "
            "rules (luxury streetwear, $80-$450 band), and propose specific "
            "adjustments with reasoning."
        )

    def _build_allowed_tools(self) -> list[str]:
        return [
            "Read",
            "Glob",
            "Grep",
            "mcp__skyyrose-tools__get_product_catalog",
        ]

    def _build_agents(self) -> dict[str, AgentDefinition]:
        return {}  # No sub-agents needed
```

2. **Register the export** in `agents/claude_sdk/domain_agents/__init__.py` (follow the existing pattern — every domain agent is re-exported).

3. **Update anatomy**: `.wolf/anatomy.md` line 239+ (the `domain_agents/` block) — append the new entry.

4. **Smoke test**:

```python
import anyio
from agents.claude_sdk.domain_agents.pricing import SDKPricingStrategistAgent

async def main():
    agent = SDKPricingStrategistAgent()
    result = await agent.run("Audit br-001 pricing vs Black Rose collection floor")
    print(result)

anyio.run(main)
```

---

## Recipe 2 — Add a new subagent to the brand orchestrator (Stack B)

Goal: add an `image-qc` subagent the orchestrator can delegate to.

1. **Edit** `skyyrose/multi_agent/agents.py`. Append to `AGENT_DEFINITIONS`:

```python
"image-qc": AgentDefinition(
    description="Audits product imagery for resolution, color profile, and brand consistency.",
    prompt=(
        "You are the SkyyRose image-quality inspector. Use list_product_images "
        "to enumerate assets, then verify each image meets brand specs: "
        "2048px min side, sRGB color space, no watermarks. Report any failures."
    ),
    tools=["Read", "Glob", "Bash", "mcp__skyyrose-tools__list_product_images"],
),
```

2. **(Optional) Add an MCP tool** if you need new capabilities — append to `skyyrose/multi_agent/tools.py`:

```python
@tool(
    "verify_image_resolution",
    "Check that an image file meets the 2048px minimum",
    {"path": str},
)
async def verify_image_resolution(args: dict) -> dict:
    from PIL import Image
    img = Image.open(args["path"])
    ok = min(img.size) >= 2048
    return {"content": [{"type": "text", "text": f"{args['path']}: {img.size} ok={ok}"}]}
```

Then register it on `skyyrose_mcp_server` (follow the existing `create_sdk_mcp_server` call in `tools.py`) and add `"mcp__skyyrose-tools__verify_image_resolution"` to both `allowed_tools` lists in `orchestrator.py` (line 107 for orchestrator, line 234 for single-agent).

3. **Smoke test**:

```bash
python -m skyyrose.multi_agent --agent image-qc --budget 1.0 \
    "Audit images for br-001 and lh-002"
```

---

## Recipe 3 — Wire SDK execution into an existing SuperAgent (mixin pattern)

Use when you already have a `SuperAgent` subclass and want to grant it SDK powers without rewriting it.

```python
from agents.core.base import SuperAgent
from agents.claude_sdk.mixin import SDKCapabilityMixin


class CommerceAgentWithSDK(SDKCapabilityMixin, SuperAgent):
    async def reprice_collection(self, collection: str) -> str:
        return await self._sdk_execute(
            prompt=f"Reprice {collection} collection based on competitor scan",
            system_prompt="You are a luxury streetwear pricing analyst.",
            allowed_tools=["Read", "WebFetch"],
        )
```

The mixin grants three async methods:
- `_sdk_execute(prompt, ...)` — full tool-use loop.
- `_sdk_delegate(subagents={...}, prompt=...)` — multi-agent orchestration.
- `_sdk_session(...)` — stateful conversation.

---

## Hooks — telemetry and security

DevSkyy ships two hook systems. Pick based on stack:

| Hook system | File | Purpose |
|-------------|------|---------|
| `DevSkyySubagentTracker` | `agents/claude_sdk/utils/tracker.py` | Per-session JSONL log of Pre/PostToolUse — used by `ClaudeSDKBaseAgent.run()` |
| `HOOKS` dict | `skyyrose/multi_agent/hooks.py` | `audit_tool_use`, `guard_bash`, `log_file_edit`, `report_progress` — used by orchestrator |

`guard_bash` blocks destructive Bash commands (e.g., `rm -rf`, `sudo`, `force push`) before the SDK executes them. Any new agent that runs Bash must include hooks or the orchestrator's `HOOKS` map.

To add a custom PreToolUse guard:

```python
from claude_agent_sdk import HookMatcher

async def block_production_writes(tool_name, tool_input, _):
    if tool_name == "Write" and "wordpress-theme/" in tool_input.get("file_path", ""):
        return {"decision": "block", "reason": "Theme writes go through deploy-theme.sh"}
    return None

options = ClaudeAgentOptions(
    hooks={"PreToolUse": [HookMatcher(matcher="Write", hooks=[block_production_writes])]},
    # ...
)
```

---

## Models, budgets, and cost

`skyyrose/multi_agent/config.py` defines defaults:

| Constant | Value | Notes |
|----------|-------|-------|
| `ORCHESTRATOR_MODEL` | `"opus"` (or alias) | Coordinator — uses Opus for routing decisions |
| `SUBAGENT_MODEL` | `"sonnet"` (or alias) | Workers — most domain tasks |
| `MAX_BUDGET_USD` | `5.0` | Hard cap per session |
| `MAX_TURNS_ORCHESTRATOR` | controlled by config | Cuts runaway loops |
| `MAX_TURNS_SUBAGENT` | controlled by config | Same, scoped per agent |

For high-volume / classification work, override with `model="haiku"` in `ClaudeAgentOptions`. SDK aliases (`opus`, `sonnet`, `haiku`) resolve to the latest model in each tier — keep that abstraction unless you need a pinned version.

Always set `max_budget_usd` — the SDK aborts the session if exceeded. Without it, an off-the-rails agent can burn dollars per turn.

---

## Smoke test commands

**Important:** if you are running these from inside a Claude Code session (any shell launched by the `claude` CLI), use the wrapper script. It strips `CLAUDECODE` + `CLAUDE_CODE_ENTRYPOINT` so the SDK's nested-session guard doesn't fail the subprocess. Outside Claude Code, both forms work identically.

```bash
# Read-only — no API call, runs anywhere (no wrapper needed)
python -m skyyrose.multi_agent --list-agents

# API-touching smoke tests — use the wrapper inside Claude Code sessions
./scripts/run_managed_agent.sh --budget 0.50 \
    --agent product-analyst "List products missing primary images"

./scripts/run_managed_agent.sh --interactive "Let's review the platform"

# Stack A — base agent (must strip ALL Claude Code env markers, not just CLAUDECODE)
env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT -u CLAUDE_CODE_SESSION_ID \
    -u CLAUDE_CODE_EXECPATH -u CLAUDE_CODE_LOG_LEVEL -u CLAUDE_CODE_SUBAGENT_MODEL \
    -u CLAUDE_CODE_TMPDIR -u CLAUDE_AUTOCOMPACT_PCT_OVERRIDE -u CLAUDE_TMPDIR \
    -u CLAUDE_EFFORT -u AI_AGENT \
    python3 -c "
import anyio
from agents.claude_sdk.base import ClaudeSDKBaseAgent
async def main():
    print(await ClaudeSDKBaseAgent().run('Reply with READY in one word'))
anyio.run(main)
"
```

**Why the wrapper exists:** the Python SDK shells out to the Node `claude` CLI. That CLI refuses to start when ANY of 12+ Claude Code parent-session env vars are set (`CLAUDECODE`, `CLAUDE_CODE_SESSION_ID`, `CLAUDE_CODE_EXECPATH`, `CLAUDE_CODE_LOG_LEVEL`, `CLAUDE_CODE_SUBAGENT_MODEL`, `CLAUDE_CODE_TMPDIR`, `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`, `CLAUDE_TMPDIR`, `CLAUDE_EFFORT`, `CLAUDE_CODE_ENTRYPOINT`, `AI_AGENT`). The wrapper enumerates env and strips them all. **Symptom of zero strip**: `ProcessError: Command failed with exit code 1` with stderr `Claude Code cannot be launched inside another Claude Code session.`

**Independent SDK bug:** `claude-agent-sdk 0.1.41`'s `query()` function closes stdin after string prompts (`end_input()` in `_internal/client.py:134`), which breaks the bidirectional control protocol required by SDK MCP servers (`create_sdk_mcp_server`). Symptom: `CLIConnectionError: ProcessTransport is not ready for writing` at `_handle_control_request`. **Fix**: use `ClaudeSDKClient` async context manager for any agent code that wires SDK MCP servers. The DevSkyy orchestrator was migrated from `query()` to `ClaudeSDKClient` for both one-shot and interactive paths (see `skyyrose/multi_agent/orchestrator.py`). Never invoke `claude_agent_sdk.query()` with `mcp_servers={...}` configured.

If you hit `ANTHROPIC_API_KEY not set`, the wrapper already handles that — it sources `.env` automatically. For raw `python -m` invocations, source it manually: `set -a; source .env; set +a` (subprocess env scope — see `CLAUDE.md` learnings).

---

## Pitfalls

1. **Two version pins** — `pyproject.toml` previously declared `claude-agent-sdk` in both `dependencies` (`>=0.1.0`) and the `[project.optional-dependencies.sdk]` extra (`>=0.1.18`). Now consolidated: core dep is the canonical pin (`>=0.1.18`), extras block is reserved for future SDK-adjacent optionals.
2. **MCP tool name format** — In-process MCP tools register as `mcp__<server_name>__<tool_name>`. Forgetting the prefix in `allowed_tools` causes silent permission prompts.
3. **`agents` map vs `mcp_servers` map** — Subagents go in `agents={"name": AgentDefinition(...)}`; MCP tool servers go in `mcp_servers={"name": server}`. Confusing them yields `KeyError` at session start.
4. **Don't use `.venv-agents/`** — that venv is reserved for **Google ADK** (numpy conflicts). Claude Agent SDK installs into the main project Python (`make install`).
5. **`claude` CLI must be on PATH** — the Python SDK shells out to the Node binary. `which claude` should return a path; if not, `npm install -g @anthropic-ai/claude-code`.
6. **`permission_mode="bypassPermissions"`** — Used by `ClaudeSDKBaseAgent` for headless runs. Never expose this mode through a user-facing endpoint without an audit hook (`guard_bash` or equivalent).
7. **Budget cap is mandatory** — Always pass `max_budget_usd`. The SDK enforces it; without it, infinite-loop scenarios are billable.

---

## Where to look next

| Question | File |
|----------|------|
| How does the orchestrator route to subagents? | `skyyrose/multi_agent/orchestrator.py` |
| How is a domain agent structured? | `agents/claude_sdk/domain_agents/immersive.py` (richest example) |
| How do MCP tools get registered? | `skyyrose/multi_agent/tools.py` |
| How does telemetry capture tool use? | `agents/claude_sdk/utils/tracker.py` |
| How does the SDK base class wrap a session? | `agents/claude_sdk/base.py:99` (`run()` method) |
| How does mixin pattern work? | `agents/claude_sdk/mixin.py` |
| SDK reference docs | `https://docs.anthropic.com/claude/docs/claude-agent-sdk` |
