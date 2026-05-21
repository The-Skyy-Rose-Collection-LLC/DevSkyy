# agents/claude_sdk/domain_agents/ — Domain-specific SDK agents (15 modules)

`SDKSubAgent` subclasses, one per domain. Each defines its own `AgentDefinition`, tool whitelist, and system prompt. Wired into the matching `agents/core/<domain>/agent.py` `_register_sub_agents()` so they appear alongside native sub-agents.

## Inventory

| File | Domain | Notable agents |
|------|--------|----------------|
| `commerce.py` | Commerce | `SDKCatalogManagerAgent`, `SDKPriceOptimizerAgent` |
| `content.py` | Content | content writing + SEO drafting agents |
| `creative.py` | Creative | brand-aligned creative agents |
| `marketing.py` | Marketing | `SDKCampaignAnalystAgent`, `SDKCompetitiveIntelAgent` (Klaviyo tools live here) |
| `operations.py` | Operations | deploy ops, code review, infrastructure |
| `analytics.py` | Analytics | report drafting, forecast review |
| `imagery.py` | Imagery | imagery QA + dossier-aware generation agents |
| `web_builder.py` | Web Builder | theme/template/pattern agents |
| `brand_guardian.py` | Brand | voice consistency enforcement (across all output) |
| `community.py` | Community | reddit / discord / forums |
| `customer_intelligence.py` | Customer | persona modeling, intent classification |
| `immersive.py` | Immersive | 3D portal / AR experience copy + design |
| `influencer.py` | Influencer | outreach + relationship mgmt |
| `seo_discovery.py` | SEO | discovery + keyword research |
| `supply_chain.py` | Supply | inventory + supplier ops |

## SDKSubAgent pattern

Each file defines one or more `SDKSubAgent` subclasses:

```python
from agents.claude_sdk import SDKSubAgent, ToolProfile

class SDKCatalogManagerAgent(SDKSubAgent):
    name = "sdk_catalog_manager"
    parent_type = CoreAgentType.COMMERCE
    description = "Catalog CRUD + dossier-aware product writes"
    sdk_tools = ["Read", "Write", "Bash", "WebSearch"]   # tool whitelist
    tool_profile = ToolProfile.COMMERCE                   # or build a custom profile
    system_prompt = "You manage the SkyyRose catalog..."

    # Inherits _sdk_execute, _sdk_delegate, _sdk_session
```

## Tool profile mapping

`ToolProfile` (from `tool_bridge.py`) groups common tool sets. Use the profile builders rather than enumerating tools per agent:

```python
from agents.claude_sdk import (
    build_researcher_agent, build_analyst_agent,
    build_writer_agent, build_code_agent,
)

# Returns an AgentDefinition with the appropriate tools wired
researcher = build_researcher_agent(name="...", system_prompt="...")
analyst = build_analyst_agent(...)
```

## Klaviyo lives here

`marketing.py` SDK agents have access to Klaviyo MCP tools (`klaviyo_create_campaign`, `klaviyo_get_*`, `klaviyo_subscribe_profile_to_marketing`, etc.). **Only legitimate path for Klaviyo writes** — don't add Klaviyo calls to the native `agents/core/marketing/sub_agents/` files (explicitly out of scope there).

## Registration

Domain SDK agents register into their core's sub-agent map:

```python
# In agents/core/marketing/agent.py
def _register_sub_agents(self):
    self.register_sub_agent("social_media", SocialMediaSubAgent())
    self.register_sub_agent("campaign_ops", CampaignOpsSubAgent())
    # SDK agents
    self.register_sub_agent("sdk_campaign_analyst", SDKCampaignAnalystAgent())
    self.register_sub_agent("sdk_competitive_intel", SDKCompetitiveIntelAgent())
```

Parent CoreAgent routes by keyword; both native + SDK sub-agents are eligible candidates.

## Conventions

- **Class names prefixed `SDK*`** to distinguish from native sub-agents.
- **`sdk_tools` whitelist** — narrowest possible set. Don't grant `Bash` unless the agent legitimately needs it.
- **`ToolProfile` over ad-hoc tools.** Use the profile builders so tool sets stay consistent across domains.
- **System prompts live in `agents/claude_sdk/prompts/` when reusable.** Inline prompts only for one-off agents.
- **`structlog` for telemetry.** Tracker pulls `correlation_id`, `agent`, `domain`, `turn`, `tools_used`.
- **Brand voice enforcement.** Any agent producing user-facing copy passes through `brand_guardian.py` for voice check.

## Don't

- Don't grant `Bash` without justification. `Read` + `Write` + `WebSearch` is enough for 80% of cases.
- Don't bypass the parent CoreAgent. SDK agents are sub-agents — they execute inside a core's heal/escalate context.
- Don't reference live customer PII in agent prompts (`customer_intelligence.py` works on anonymized data).
- Don't add net-new ad-platform writes (Google Ads / Meta Ads) here without a gating strategy — higher risk than Klaviyo email sends.
- Don't reuse a `name` across domains. SDK sub-agent `name` must be unique within `agents/claude_sdk/`.

## Related

- Base mixin / class: `agents/claude_sdk/sdk_sub_agent.py`, `agents/claude_sdk/mixin.py`
- Tool profiles: `agents/claude_sdk/tool_bridge.py` (`ToolProfile`, `build_*`)
- Reusable prompts: `agents/claude_sdk/prompts/`
- Hook → self-healing wiring: `agents/claude_sdk/hooks.py`
- Parent cores: `agents/core/<domain>/agent.py`
- Klaviyo MCP server: registered via the `claude.ai Klaviyo` MCP server
