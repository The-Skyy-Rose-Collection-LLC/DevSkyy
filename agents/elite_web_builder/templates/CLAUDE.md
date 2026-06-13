# agents/elite_web_builder/templates/ — Output scaffold templates

Starter files the Director uses as the structural skeleton for generated themes. The Director copies and populates these during story execution — they define required shape, not final content.

## Key files

### `wordpress/`
- `functions-starter.php` — WordPress theme bootstrap scaffold: required `add_action`/`add_filter` hooks, `wp_enqueue_scripts` stub, ABSPATH guard, text domain setup, `$wpdb->prepare()` placeholder query example. New theme generations start from this file.
- `theme-json-starter.json` — Minimal valid `theme.json` with the `version`, `settings`, and `styles` keys the block editor requires. Includes the custom property scaffold for design tokens. Director populates color palette, typography, and spacing from `DesignSystemAgent` output.
- `settings_schema_starter.json` — WordPress Customizer schema stub listing the expected setting groups (colors, typography, layout). Used by `ThemeBuilderAgent` to generate the Customizer PHP.

### `shopify/`
- Empty — Shopify template support is not yet implemented. Do not add files here until a Shopify specialist agent exists.

## Conventions

- Templates are copied verbatim as the starting point — never modify them mid-generation. Specialist agents receive the starter content and return modified content; they do not mutate templates in place.
- PHP in `functions-starter.php` must pass PHPCS WordPress standard — run `vendor/bin/phpcs` before modifying the template.
- `theme-json-starter.json` must remain valid JSON. Validate with `python -m json.tool` before committing changes.
- Do not add Shopify files until a matching Shopify `AgentRole` and `AgentSpec` exist in `agents/`.

## Don't

- Don't put final/production content in templates — they are structural scaffolds, not deployable output.
- Don't add logic or conditionals to PHP templates — keep them declarative; branching belongs in the agent that consumes them.
- Don't add `shopify/` content without a corresponding specialist agent — orphan templates have no consumer.

## Related

- `agents/elite_web_builder/agents/theme_builder.py` — `THEME_BUILDER_SPEC` reads `theme-json-starter.json`
- `agents/elite_web_builder/agents/backend_dev.py` — `BACKEND_DEV_SPEC` starts from `functions-starter.php`
- `agents/elite_web_builder/core/output_writer.py` — copies templates to `output/` at story start
- `agents/elite_web_builder/config/` — routing and quality gate config consumed by the Director
