# agents/core/creative/sub_agents/ — Creative sub-agents

One consolidated sub-agent registered by `CreativeCoreAgent`. Handles all four creative roles through ALIASES.

## Key files

- `brand_creative.py` — `BrandCreativeSubAgent`: design system, brand enforcement, asset generation, and visual QA — all four roles in one agent. `ALIASES = ("design_system", "brand_guardian", "asset_generator", "quality_checker")`. 15 capabilities across 4 domains: design tokens (`design_tokens`, `color_palette`, `typography`, `spacing_grid`), brand enforcement (`brand_check`, `logo_usage`, `voice_tone`, `style_audit`), asset generation (`generate_asset`, `resize_asset`, `format_convert`), quality checking (`visual_qa`, `consistency_check`, `contrast_check`). `parent_type = CoreAgentType.CREATIVE`.

## Conventions

- `BrandCreativeSubAgent` consolidates all four creative roles intentionally — do not add separate files for `design_system_agent.py`, `brand_guardian_agent.py`, etc. The consolidation was a deliberate architectural choice; new creative capabilities belong here.
- `ALIASES` must cover all four role names: `("design_system", "brand_guardian", "asset_generator", "quality_checker")` — existing callers use these names. Adding a new role requires adding a new ALIAS and corresponding capability entries.
- Design token changes made via the `design_tokens` capability must coordinate with `assets/css/design-tokens.css` — the token names in the system prompt must stay in sync with the CSS file.
- Brand violations found by `brand_check` are bugs, not suggestions — the fix is mandatory. `style_audit` results should trigger blocking issues, not warnings.
- `contrast_check` capability enforces WCAG 2.2 AA minimum (4.5:1 text, 3:1 large text) — do not loosen this threshold.

## Don't

- Don't route image generation (FASHN, Gemini, FLUX) through `BrandCreativeSubAgent` — image generation is `ImageryCoreAgent` territory.
- Don't add a new keyword route in `CreativeCoreAgent.execute()` without adding the corresponding ALIAS to `BrandCreativeSubAgent.ALIASES`.
- Don't bypass the legacy `CreativeAgent` fallback in `_get_legacy_agent()` — it handles categories not yet migrated to this sub-agent.

## Related

- `agents/core/creative/agent.py` — parent that registers `BrandCreativeSubAgent` under all ALIASES
- `agents/creative_agent.py` — legacy agent wrapped by `_get_legacy_agent()` in `CreativeCoreAgent`
- `assets/css/design-tokens.css` — token source of truth; `BrandCreativeSubAgent.system_prompt` references token names from this file
- `agents/core/imagery/` — image generation (separate domain, not creative)
