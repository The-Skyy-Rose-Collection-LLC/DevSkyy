<claude-mem-context>

</claude-mem-context>

# agents/core/web_builder/ — Web Builder domain CoreAgent

`WebBuilderCoreAgent` — WordPress/Shopify theme generation, template building, and theme development automation. Extends `CoreAgent` (`core_type = CoreAgentType.WEB_BUILDER`). One native sub-agent (`WebDevSubAgent`) plus two SDK sub-agents, delegating heavy build work to `elite_web_builder/director.py`.

## Key files

- `agent.py` — `WebBuilderCoreAgent(CoreAgent)`: registers `WebDevSubAgent` (with ALIASES), `SDKThemeDevAgent`, `SDKTemplateBuilderAgent`. Lazy-loads `Director` from `agents/elite_web_builder/director.py` — import is deferred to avoid circular deps and heavy boot cost.
- `sub_agents/web_dev.py` — `WebDevSubAgent`: theme CSS/JS edits, PHP template modifications, design token updates. Has `ALIASES` tuple — check before adding routing names.

## Conventions

- Keyword routing in `execute()`: match against `"theme"/"css"/"template"/"php"` → `WebDevSubAgent`, `"generate"/"prd"/"build full"` → `SDKTemplateBuilderAgent` (invokes Director). Unmatched tasks fall back to legacy `operations_agent.py`.
- `Director` is lazy-loaded via `importlib` — do not import at module top level. The elite_web_builder tree has heavy transitive imports (provider adapters, cost tracker, etc.) that should not load on every agent init.
- `SDKThemeDevAgent` and `SDKTemplateBuilderAgent` use `SDKSubAgent` with `sdk_tools = ["Read", "Write", "Bash", "WebSearch"]` — they need filesystem access to write generated PHP/CSS files.
- After `Director.execute_prd()` completes, push to WooCommerce only through `CommerceCoreAgent` → `WordPressBridgeSubAgent` — not directly from this agent.

## Don't

- Don't call `Director()` directly — always use `Director.from_config(config_path)`.
- Don't add WordPress REST writes to `web_dev.py` — file edits only; WC product sync goes through `WordPressBridgeSubAgent`.
- Don't import `elite_web_builder` at module top level — use the lazy-import pattern already established in `agent.py`.
- Don't route imagery generation through `WebBuilderCoreAgent` — image generation is `ImageryCoreAgent` territory.

## Related

- `agents/elite_web_builder/director.py` — `Director.from_config()` entry point for full PRD-driven theme builds
- `agents/elite_web_builder/core/` — cost tracker, model router, verification loop used by Director
- `agents/core/commerce/sub_agents/wordpress_bridge.py` — WooCommerce push after theme is generated
- `wordpress-theme/skyyrose-flagship/` — the production theme that `WebDevSubAgent` edits
