# agents/core/marketing/ — Marketing domain CoreAgent

`MarketingCoreAgent` — campaigns, social media, audience growth. Extends `CoreAgent` (`core_type = CoreAgentType.MARKETING`). Two native sub-agents (`SocialMediaSubAgent`, `CampaignOpsSubAgent`) plus two SDK sub-agents.

## Key files

- `agent.py` — `MarketingCoreAgent(CoreAgent)`: registers `SocialMediaSubAgent`, `CampaignOpsSubAgent` (with ALIASES), `SDKCampaignAnalystAgent`, `SDKCompetitiveIntelAgent`. Falls back to legacy `MarketingAgent` for unmatched tasks.
- `sub_agents/social_media.py` — `SocialMediaSubAgent`: post scheduling, engagement tracking, platform-specific content generation (IG, TikTok, X). No ALIASES — callers use `"social_media"` directly.
- `sub_agents/campaign_ops.py` — `CampaignOpsSubAgent`: campaign lifecycle management, budget allocation, auto-pause on budget exhaustion, A/B experiment runner. `ALIASES = ("campaign_manager", "ab_testing")` — established in prior session.

## Conventions

- Keyword routing in `execute()`: `"social"/"post"/"instagram"/"tiktok"` → `social_media`, `"campaign"/"budget"/"ab test"/"experiment"` → `campaign_ops` alias.
- Klaviyo email/SMS sends are NOT routed through `MarketingCoreAgent` — Klaviyo calls go through `agents/claude_sdk/domain_agents/marketing.py` SDK agents that have direct Klaviyo MCP tool access.
- `CampaignOpsSubAgent.ALIASES` must remain `("campaign_manager", "ab_testing")` — these names are used by existing callers. Check before renaming.
- SDK agents (`SDKCampaignAnalystAgent`, `SDKCompetitiveIntelAgent`) need WebSearch tool access — they use `SDKSubAgent` base which grants `sdk_tools = ["Read", "Write", "Bash", "WebSearch"]`.

## Don't

- Don't route paid media buys (Google Ads, Meta Ads API writes) through `SocialMediaSubAgent` — those are higher-risk WC/ad-platform writes that need separate gating.
- Don't auto-post to social platforms without human review — `SocialMediaSubAgent` generates copy; scheduling/posting requires STOP AND SHOW.
- Don't add Klaviyo REST calls to `campaign_ops.py` — Klaviyo lives in the SDK domain agents layer.

## Related

- `agents/core/base.py` — `CoreAgent`, `CoreAgentType`, circuit breaker
- `agents/marketing_agent.py` — legacy agent wrapped by `_get_legacy_agent()`
- `agents/claude_sdk/domain_agents/marketing.py` — `SDKCampaignAnalystAgent`, `SDKCompetitiveIntelAgent`
- `agents/core/marketing/sub_agents/campaign_ops.py` — `CampaignOpsSubAgent` with ALIASES tuple
