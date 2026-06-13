# agents/core/content/sub_agents/ — Content sub-agents

Two sub-agents registered by `ContentCoreAgent`. Both extend `SubAgent` with `parent_type = CoreAgentType.CONTENT`.

## Key files

- `collection_content.py` — `CollectionContentSubAgent`: collection page sections, product descriptions, hero banners. `name = "collection_content"` — no ALIASES, callers use this name directly. 4 capabilities: `generate_section`, `product_description`, `hero_content`, `collection_overview`. Enforces SkyyRose brand voice in system prompt: Black Rose / Love Hurts / Signature / Kids Capsule aesthetics, "bold, poetic, street luxury" register.
- `seo_copywriter.py` — `SeoCopywriterSubAgent`: SEO optimization and brand copywriting. Consolidates `seo_content` and `copywriter`. `ALIASES = ("seo_content", "copywriter")`. 10 capabilities: `meta_tags`, `schema_org`, `sitemap`, `og_tags`, `heading_hierarchy`, `product_description`, `page_copy`, `cta_copy`, `blog_post`, `brand_voice`.

## Conventions

- Both classes set `parent_type = CoreAgentType.CONTENT` — escalations route back to `ContentCoreAgent`.
- `SeoCopywriterSubAgent.ALIASES` must stay `("seo_content", "copywriter")` — existing callers use these names. Check before renaming.
- `CollectionContentSubAgent` is scoped to prose generation only — it writes copy about products, not SKU-level catalog data. Catalog facts (price, colorway, sizes) come from `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`.
- Brand voice rule baked into `CollectionContentSubAgent.system_prompt`: tagline is "Luxury Grows from Concrete." (period included), garment is the protagonist, no urgency timers, no scarcity language.
- `SeoCopywriterSubAgent` returns structured output with explicit `meta_title`, `meta_description`, and `body` keys — callers must consume this structure; do not flatten to plain text.

## Don't

- Don't have `CollectionContentSubAgent` generate prices, SKU codes, or inventory data — it generates prose only.
- Don't change the brand voice rules in `CollectionContentSubAgent.system_prompt` without approval — off-brand copy is a bug, not a style choice.
- Don't route WooCommerce product data writes through either sub-agent — content generates copy, `CommerceCoreAgent` publishes it.

## Related

- `agents/core/content/agent.py` — parent that registers both sub-agents and routes keywords
- `agents/skyyrose_content_agent.py` — legacy agent wrapped by `_get_legacy_agent()` in `ContentCoreAgent`
- `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` — canonical product facts (not derived from these agents)
- `knowledge-base/seed/from-interview.md` — canonical brand voice source referenced in system prompts
