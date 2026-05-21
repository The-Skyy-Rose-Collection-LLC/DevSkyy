<claude-mem-context>

</claude-mem-context>

# agents/core/creative/ — Creative domain CoreAgent

`CreativeCoreAgent` — visual identity, design system, brand enforcement. Extends `CoreAgent` (`core_type = CoreAgentType.CREATIVE`). One native sub-agent (`BrandCreativeSubAgent`) plus keyword routing to four logical roles.

## Key files

- `agent.py` — `CreativeCoreAgent(CoreAgent)`: registers `BrandCreativeSubAgent` with all ALIASES. Keyword routing in `execute()`: `"design system"/"css"/"token"/"variable"` → `design_system`, `"brand"/"off-brand"/"color"/"font"` → `brand_guardian`, `"generate"/"asset"/"create"` → `asset_generator`. Falls back to legacy `CreativeAgent` for unmatched tasks.
- `sub_agents/brand_creative.py` — `BrandCreativeSubAgent`: consolidated design_system, brand_guardian, asset_generator, quality_checker. Has `ALIASES` tuple covering all four roles — check `brand_creative.py` for current alias values before adding callers.

## Conventions

- `BrandCreativeSubAgent` handles all four creative roles through ALIASES — this is intentional consolidation. Do not add separate sub-agent files for `design_system_agent.py` etc.
- Brand violations are bugs: if `brand_guardian` finds an off-brand color or font, the fix is mandatory, not optional.
- Design token changes must be coordinated with `assets/css/design-tokens.css` — `BrandCreativeSubAgent` knows the token names from its system prompt.
- Quality checker validates cross-browser regression (screenshot diff) — requires a running dev server; check `WebBuilderCoreAgent` preconditions before invoking.

## Don't

- Don't route image generation through `CreativeCoreAgent` — image generation (FASHN, Gemini, FLUX) is `ImageryAgent` territory.
- Don't add new roles to `execute()` keyword routing without adding the corresponding ALIAS to `BrandCreativeSubAgent.ALIASES`.
- Don't bypass the legacy `CreativeAgent` fallback — it handles categories not yet migrated to `BrandCreativeSubAgent`.

## Related

- `agents/core/base.py` — `CoreAgent`, `CoreAgentType`, circuit breaker
- `agents/creative_agent.py` — legacy agent wrapped by `_get_legacy_agent()`
- `assets/css/design-tokens.css` — token source of truth referenced in `BrandCreativeSubAgent` system prompt
- `agents/core/imagery/` — image generation (separate domain, not here)
