<claude-mem-context>

</claude-mem-context>

# themes/shopify/ — SkyyRose Shopify OS 2.0 theme

Shopify Online Store 2.0 theme for SkyyRose. Parallel to `wordpress-theme/skyyrose-flagship/` — same brand, different platform. Status: in development, not yet deployed to a live Shopify store.

## Key files

- `layout/theme.liquid` — Root Liquid layout. All pages inherit from here. Scripts and stylesheets enqueued via Shopify's `{% render %}` and `{{ content_for_layout }}`.
- `templates/` — JSON templates (OS 2.0 format) mapping page types to section compositions. Each template is a JSON file referencing section handles.
- `sections/` — Reusable Liquid sections: `header.liquid`, `footer.liquid`, collection/product sections. Sections own their own settings schema at the bottom of each file.
- `snippets/` — Atomic Liquid partials (`product-card.liquid`, `collection-hero.liquid`). No settings schema — snippets receive data via `{% render 'snippet' with obj %}`.
- `assets/` — Theme CSS, JS, and image assets. Shopify serves these via CDN — file names must stay stable (no hashing); bust cache by bumping query params in Liquid.
- `config/settings_schema.json` — Global theme settings definition (colors, typography, layout). Do not edit manually — use Shopify CLI or Admin theme editor to export.
- `config/settings_data.json` — Saved theme settings values. Gitignored by Shopify convention — do not commit.
- `locales/` — Liquid translation strings (en.default.json is canonical).
- `README.md` — Shopify CLI setup and deploy commands.

## Conventions

- Brand tokens (`--skyyrose-accent`, `--skyyrose-bg`, etc.) must mirror `design-tokens.css` from `wordpress-theme/skyyrose-flagship/assets/css/`. Both themes share the same visual identity — keep color values in sync.
- Sections own their own CSS via `{{ 'section-name.css' | asset_url | stylesheet_tag }}`. Global styles go in `assets/base.css`.
- OS 2.0 templates are JSON — never write `{% section %}` tags inside template files. Compose via the JSON `sections` array.
- `AgentRole` for Shopify (`elite_web_builder/agents/`) does not exist yet — see `agents/elite_web_builder/templates/shopify/`. Do not wire Shopify deployment into the Director until the role is implemented.

## Don't

- Don't commit `config/settings_data.json` — it contains environment-specific values that differ between development and production themes.
- Don't hand-edit `config/settings_schema.json` in isolation — schema changes that break existing `settings_data.json` keys will silently revert to defaults in Admin.
- Don't add Shopify-specific logic to `wordpress-theme/` — the two themes are independent deployments.
- Don't deploy to a live Shopify store without STOP AND SHOW confirmation — Shopify theme pushes are live immediately.

## Related

- `wordpress-theme/skyyrose-flagship/` — WooCommerce counterpart sharing the same brand identity
- `agents/elite_web_builder/templates/shopify/` — empty placeholder until Shopify AgentRole is added
- `design-system/skyyrose/MASTER.md` — shared brand design system reference
