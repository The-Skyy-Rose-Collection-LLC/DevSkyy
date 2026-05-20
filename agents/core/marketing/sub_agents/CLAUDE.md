# agents/core/marketing/sub_agents/ — Marketing sub-agents (2 modules)

Native sub-agents for the Marketing domain. Two files cover **social media** and **campaign operations**. Klaviyo (email/SMS) lives in `agents/claude_sdk/domain_agents/marketing.py` — not here.

## Inventory

| File | Class | Capabilities | ALIASES |
|------|-------|--------------|---------|
| `social_media.py` | `SocialMediaSubAgent` | post scheduling, engagement tracking, IG/TikTok/X content gen | none — callers use `"social_media"` |
| `campaign_ops.py` | `CampaignOpsSubAgent` | campaign lifecycle, budget allocation, auto-pause on exhaust, A/B experiments | `("campaign_manager", "ab_testing")` |

## ALIASES contract

`CampaignOpsSubAgent.ALIASES = ("campaign_manager", "ab_testing")` — established in a prior session. Old callers routing to `"campaign_manager"` or `"ab_testing"` resolve to this same sub-agent. **Do not rename** without auditing callers.

```python
# Both of these resolve to CampaignOpsSubAgent:
await marketing_core.execute("manage campaign for Black Rose launch")  # → campaign_manager alias
await marketing_core.execute("run ab test on hero copy")               # → ab_testing alias
```

`SocialMediaSubAgent` has no ALIASES — single keyword `"social_media"` only.

## Keyword routing (handled by `MarketingCoreAgent.execute()`)

| Keywords in task | Routed to |
|------------------|-----------|
| `social`, `post`, `instagram`, `tiktok`, `x.com`, `twitter` | `SocialMediaSubAgent` |
| `campaign`, `budget`, `ab test`, `experiment`, `variant` | `CampaignOpsSubAgent` (via alias) |
| Unmatched | falls back to legacy `MarketingAgent` (via `_get_legacy_agent()`) |

## Hard scope boundaries

These sub-agents are NOT allowed to:

- **Klaviyo email/SMS sends** — that's `agents/claude_sdk/domain_agents/marketing.py` SDK agents with direct Klaviyo MCP tool access. Not here.
- **Paid media buys** (Google Ads, Meta Ads API writes) — too high risk for this layer. Separate gated agents required.
- **Auto-post to live social platforms** — `SocialMediaSubAgent` generates copy; the actual schedule/post step requires STOP AND SHOW.

## SocialMediaSubAgent specifics

- **Brand-voice gate.** All generated copy passes through `skyyrose_content_agent.py` style enforcement before output. SkyyRose voice: "Luxury Grows from Concrete." No urgency timers, no related-products, garment is the protagonist.
- **Platform-specific shape.** IG = single-image + carousel-friendly captions, TikTok = hook-first script, X = ≤280 char with hashtag discipline.
- **Founder voice register** for tone. See `knowledge-base/seed/from-interview.md` and the project memory `project_founder_voice.md`.

## CampaignOpsSubAgent specifics

- **Auto-pause logic.** When `spent_to_date >= budget`, the sub-agent pauses the campaign and notifies the operator. No exceptions; budget caps are hard.
- **A/B experiment runner.** Wraps the experiment tracker — defines variants, picks statistical significance threshold (default 95% confidence), declares winners.
- **No actual ad-platform writes.** This sub-agent does plan + measure; pausing a live ad requires a separate gated call to whichever ad platform is hosting it.

## Conventions

- **Async `execute(task, **kwargs)`.** Per `SubAgent` contract.
- **`name` matches alias casing.** `SocialMediaSubAgent.name = "social_media"`. `CampaignOpsSubAgent.name = "campaign_ops"` with ALIASES routing the other names.
- **Errors → `AgentError`** with `ErrorCategory`. Never raw exceptions.
- **STOP AND SHOW for posting/sending.** Copy generation is free; the act of publishing isn't.
- **Brand-voice consistency.** Use `skyyrose_content_agent.py` for voice enforcement before any user-facing output.

## Don't

- Don't add a Klaviyo client here. Klaviyo lives in the SDK layer.
- Don't auto-publish or schedule posts without explicit human approval. Generate, present, gate.
- Don't bypass `CampaignOpsSubAgent` auto-pause when budget is exceeded — that's the safety net.
- Don't break the ALIASES tuple. Renaming breaks callers silently.
- Don't reference products by SKU in social copy. Name-first (per project memory `feedback_product_naming.md`).

## Related

- Parent core: `agents/core/marketing/agent.py` (`MarketingCoreAgent`)
- SubAgent base: `agents/core/sub_agent.py`
- Legacy fallback: `agents/marketing_agent.py`
- SDK email/SMS layer: `agents/claude_sdk/domain_agents/marketing.py` (`SDKCampaignAnalystAgent`, `SDKCompetitiveIntelAgent`)
- Brand voice: `agents/skyyrose_content_agent.py`
- Founder voice register: `knowledge-base/seed/from-interview.md`
- Brand canon: project memory `project_brand.md`
- Klaviyo MCP tools available via Claude MCP server

## Recent learnings

- `CampaignOpsSubAgent.ALIASES = ("campaign_manager", "ab_testing")` established and documented — back-compat-critical.
- Klaviyo MCP tools (klaviyo_create_campaign, klaviyo_get_*, klaviyo_subscribe_*) are exposed via the `claude.ai Klaviyo` MCP server. SDK domain agents own those calls.
