# SkyyRose Shopify Theme — DEFERRED PLUG-IN

> **Status: scaffold only.** This directory holds the Shopify Online Store 2.0 scaffold that will receive the SkyyRose theme plug-in. Concrete Liquid templates, sections, and the Admin API sync live in a follow-up PR. The elite team dispatcher intentionally raises `NotImplementedError` for `task.platform == "shopify"` until that PR ships.

---

## Why this exists before the plug-in

The `THEME_BUILDER` specialist (Elite Team) is a dual-platform architect: WordPress is primary, Shopify is portable. Shipping the scaffold now does three things:

1. **Locks in the directory structure** so the plug-in PR is pure fill-in, not design.
2. **Gives the theme-builder system prompt a live knowledge reference** (`knowledge/shopify_themes.md`) so Shopify guidance is ready on day one.
3. **Defines the parity matrix** between WordPress (`wordpress-theme/skyyrose-flagship/`) and Shopify so brand tokens, fonts, and components don't drift.

---

## Directory layout (Shopify OS 2.0)

```
themes/shopify/
├── layout/          — theme.liquid (root HTML)
├── sections/        — reusable composable sections (header, footer, hero, product-card)
├── snippets/        — small partials (price, sku-badge, …)
├── templates/       — route manifests (index.json, product.json, collection.json, …)
├── assets/          — theme.css, theme.js, fonts, 3D models (parity with WP)
├── config/          — settings_schema.json (Customizer), settings_data.json (defaults)
└── locales/         — en.default.json, en.default.schema.json
```

Every directory currently holds a `.gitkeep` placeholder. The plug-in PR replaces these with real Liquid / JSON assets.

---

## Parity matrix (WordPress → Shopify)

The full WP ↔ Shopify parity matrix — brand tokens, hooks, templates, catalog
sync, fonts, 3D assets, and deploy flow — is the single source of truth at:

**`agents/elite_web_builder/knowledge/shopify_themes.md §3` (WP ↔ Shopify parity matrix)**

This README intentionally does NOT restate that table. When the plug-in PR
lands, update the knowledge doc once; every consumer (the theme-builder
system prompt, this README, the Shopify sync script) follows.

---

## What the plug-in PR must deliver

1. `layout/theme.liquid` — root layout, head meta, global enqueues
2. `sections/header.liquid`, `footer.liquid`, `hero-skyyrose.liquid`, `collection-showcase.liquid`, `product-holo-card.liquid`
3. `snippets/price.liquid`, `sku-badge.liquid` (reference snippets in `knowledge/shopify_themes.md §5`)
4. `templates/index.json`, `product.json`, `collection.json`, `cart.json`, `page.json`
5. `assets/theme.css` — compiled brand tokens + component styles (port from `wordpress-theme/skyyrose-flagship/assets/css/`)
6. `assets/theme.js` — Shopify Cart AJAX API integration (parity with WP `cart.js`)
7. `config/settings_schema.json` — full brand token + typography editor schema
8. `config/settings_data.json` — default values matching SkyyRose brand palette
9. `locales/en.default.json` + `en.default.schema.json` — i18n
10. `scripts/shopify_sync.py` — CSV → Shopify products via Admin API (metafield mapping per `knowledge/shopify_themes.md §7`)
11. Re-enable `agents/elite_web_builder/triggers.py::_dispatch_theme(platform='shopify')` once the sync script exists

---

## How to test the scaffold

```bash
# Confirm directory tree
ls -la themes/shopify/

# Confirm dispatcher deferral
python -c "
from agents.elite_web_builder.triggers import trigger_pipeline
try:
    trigger_pipeline(kind='theme_build', task={'platform': 'shopify'})
except NotImplementedError as exc:
    print(f'Scaffold OK — dispatcher correctly defers: {exc}')
"
```
