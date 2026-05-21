<claude-mem-context>

</claude-mem-context>

# agents/core/web_builder/sub_agents/ — Web Builder sub-agents

One consolidated sub-agent registered by `WebBuilderCoreAgent`. Covers all five web development roles through ALIASES.

## Key files

- `web_dev.py` — `WebDevSubAgent`: full-stack web development consolidated into one agent. Consolidates `frontend_dev`, `backend_dev`, `accessibility`, `performance`, `platform_adapter`. `ALIASES = ("frontend_dev", "backend_dev", "accessibility", "performance", "platform_adapter")`. 21 capabilities across 5 domains: frontend (`html_template`, `css_styling`, `js_interactive`, `react_component`, `block_pattern`, `animation`), backend (`php_template`, `rest_api`, `database_query`, `server_config`), accessibility (`wcag_audit`, `aria_check`, `contrast_check`, `keyboard_nav`), performance (`lighthouse_audit`, `lazy_loading`, `caching_strategy`, `bundle_optimize`), platform adapters (`wordpress_adapter`, `vercel_adapter`, `shopify_adapter`). `parent_type = CoreAgentType.WEB_BUILDER`.

## Conventions

- `WebDevSubAgent` is LLM-only — it generates PHP/CSS/JS code and plans but cannot write files or run commands. Writing files and executing builds requires `SDKThemeDevAgent` or `SDKTemplateBuilderAgent` (SDK variants registered by parent).
- `ALIASES` cover all five role names — any caller using `"frontend_dev"`, `"backend_dev"`, etc. resolves to the same `WebDevSubAgent` instance. Do not add new roles without adding a corresponding ALIAS.
- For WordPress theme edits, `web_dev` output must follow the theme conventions in `wordpress-theme/skyyrose-flagship/CLAUDE.md` — escaping (`esc_html`, `esc_attr`), nonce checks, no `innerHTML` in JS.
- `accessibility` capability enforces WCAG 2.2 AA — `contrast_check` is 4.5:1 minimum for normal text. Do not loosen this threshold.
- Platform adapter capabilities (`wordpress_adapter`, `vercel_adapter`, `shopify_adapter`) produce platform-specific configuration and integration code — not generic web code.

## Don't

- Don't route PRD-driven full theme generation through `WebDevSubAgent` — that requires `Director.from_config()` via `SDKTemplateBuilderAgent`. `WebDevSubAgent` handles targeted edits, not full-build orchestration.
- Don't add imagery generation capabilities here — image generation is `ImageryCoreAgent` territory.
- Don't change `ALIASES` without updating `WebBuilderCoreAgent._register_sub_agents()` callers.

## Related

- `agents/core/web_builder/agent.py` — parent that registers `WebDevSubAgent` under all ALIASES
- `agents/elite_web_builder/director.py` — full PRD build system invoked by `SDKTemplateBuilderAgent`
- `wordpress-theme/skyyrose-flagship/CLAUDE.md` — theme conventions that PHP/CSS output must follow
- `agents/core/base.py` — `SubAgent` base class with `_apply_fix()` self-healing hook
