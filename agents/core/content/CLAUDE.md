<claude-mem-context>

</claude-mem-context>

# agents/core/content/ — Content domain CoreAgent

`ContentCoreAgent` — all written content: collection pages, product descriptions, blogs, SEO copy. Extends `CoreAgent` (`core_type = CoreAgentType.CONTENT`). Wraps legacy `SkyyRoseContentAgent` plus two native sub-agents and two SDK sub-agents.

## Key files

- `agent.py` — `ContentCoreAgent(CoreAgent)`: registers `CollectionContentSubAgent`, `SeoCopywriterSubAgent` (with ALIASES), `SDKSeoWriterAgent`, `SDKCollectionPublisherAgent`.
- `sub_agents/collection_content.py` — `CollectionContentSubAgent`: writes collection page sections, product taglines, and campaign copy scoped to a specific collection (Signature / Black Rose / Love Hurts / Kids Capsule). Enforces Corey Foster voice register from system prompt.
- `sub_agents/seo_copywriter.py` — `SeoCopywriterSubAgent`: meta titles, meta descriptions, H1/H2 copy, structured data suggestions, keyword integration. Has `ALIASES` tuple for backward-compatible routing.

## Conventions

- Keyword routing in `execute()`: `"seo"/"meta"/"schema"/"keyword"` → `seo_copywriter`, `"collection"/"tagline"/"product description"` → `collection_content`. Unmatched tasks fall back to legacy `SkyyRoseContentAgent`.
- Brand voice rules: no urgency timers, no scarcity language, garment is the protagonist. `CollectionContentSubAgent` enforces this in its system prompt — don't dilute it.
- SDK agents (`SDKSeoWriterAgent`, `SDKCollectionPublisherAgent`) have tool-use (Read/Write/WebSearch) — use them for tasks that require reading dossier files or publishing via WordPress bridge.
- `SeoCopywriterSubAgent.ALIASES` — check current ALIASES in `seo_copywriter.py` before adding routing aliases to avoid conflicts.

## Don't

- Don't route WooCommerce product data writes through `ContentCoreAgent` — content generates copy, commerce publishes it.
- Don't have `CollectionContentSubAgent` generate SKU-level data — it writes prose, not catalog facts. Catalog facts come from `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`.
- Don't skip the voice register check — off-brand copy is a bug, not a style choice.

## Related

- `agents/core/base.py` — `CoreAgent`, `CoreAgentType`
- `agents/skyyrose_content_agent.py` — legacy agent wrapped by `_get_legacy_agent()`
- `agents/claude_sdk/domain_agents/content.py` — `SDKSeoWriterAgent`, `SDKCollectionPublisherAgent`
- `knowledge-base/seed/from-interview.md` — canonical brand voice source used in system prompts
