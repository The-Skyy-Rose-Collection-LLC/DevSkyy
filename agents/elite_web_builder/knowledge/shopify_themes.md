# Shopify Themes — Knowledge Base

Extension knowledge for `THEME_BUILDER_SPEC`. The agent's primary platform is WordPress; this doc covers the **Shopify Online Store 2.0** side so the theme-builder can produce dual-platform output when asked. The Shopify scaffold is intentionally **deferred / plug-in later** — directory structure and parity matrix ship now; full implementation is a follow-up PR.

> One theme, two storefronts. WordPress is primary. Shopify is a portable scaffold so SkyyRose can plug into a Shopify merchant on demand without re-theming.

---

## 1. Platform choice — Online Store 2.0 (confirmed)

- **NOT Hydrogen.** Hydrogen (Remix/React headless) requires Oxygen hosting and a separate build pipeline. Too much divergence from the WP Liquid-like templating mindset.
- **Online Store 2.0** — Liquid templates + JSON section groups. Current Shopify standard, easiest merchant install, widest compatibility, closest parity with WordPress theme structure.

Target Shopify CLI: **3.x** (`shopify theme dev`, `shopify theme push`, `shopify theme package`).

---

## 2. Directory scaffold (OS 2.0)

```
themes/shopify/
├── layout/
│   └── theme.liquid              — root layout (head, body wrapper, scripts)
├── sections/
│   ├── header.liquid             — global header + nav
│   ├── footer.liquid             — global footer
│   ├── hero-skyyrose.liquid      — SkyyRose-branded hero section
│   ├── collection-showcase.liquid
│   ├── product-holo-card.liquid  — equivalent of WP product-card-holo.php
│   └── ...
├── snippets/
│   ├── price.liquid              — price formatter with pre-order support
│   ├── sku-badge.liquid
│   └── ...
├── templates/
│   ├── index.json                — homepage, section list
│   ├── product.json              — product page
│   ├── collection.json           — collection page
│   ├── cart.json
│   └── page.json
├── assets/
│   ├── theme.css                 — compiled from WP tokens (rose gold, dark, crimson, silver, gold)
│   ├── theme.js                  — cart + interactions (parity with WP cart.js)
│   ├── fonts/                    — self-hosted woff2 (same files as WP)
│   └── 3d/                       — GLB/USDZ per SKU (same files as WP)
├── config/
│   ├── settings_schema.json      — Customizer-equivalent editor schema
│   └── settings_data.json        — default values
├── locales/
│   ├── en.default.json
│   └── en.default.schema.json
└── README.md                     — deferred-plug-in banner + parity matrix
```

---

## 3. WP ↔ Shopify parity matrix

| WP concept | Shopify OS 2.0 equivalent | Notes |
|---|---|---|
| `theme.json` + CSS custom properties | `config/settings_schema.json` + `assets/theme.css` CSS variables | Brand tokens ride the same names: `--sr-rose-gold`, `--sr-dark`, etc. |
| `functions.php` + action/filter hooks | Liquid templates + storefront events | Shopify doesn't have PHP; logic moves to storefront JS or Shopify Functions |
| Customizer panels | `config/settings_schema.json` | Same JSON schema pattern |
| `template-parts/*.php` | `sections/*.liquid` + `snippets/*.liquid` | Sections = reusable composable blocks; snippets = small partials |
| `page-*.php` templates | `templates/*.json` — section list | JSON list of sections to render for each route |
| WooCommerce product | Shopify product | Native, no plugin needed |
| `skyyrose_get_product($sku)` | `{{ product }}` Liquid global in product.liquid | Shopify injects the product object automatically |
| `skyyrose_get_product_catalog()` | `{{ collections.all.products }}` | All products in Liquid context |
| WooCommerce cart | Shopify cart | Native; theme ships `assets/cart.js` using Shopify Cart AJAX API |
| Blueprints / demo content | Shopify Theme Gift Card or JSON preset | OS 2.0 supports preset templates for demo import |
| `assets/fonts/` self-hosted | Same, but declared in `theme.css` | Shopify CDN auto-serves, no Google Fonts ever |
| `assets/3d/` GLB + USDZ | Same directory, same files | `model-viewer` component works on both platforms |
| Immersive collection experiences (THREE.js) | Same JS, different mount point | `src/collections/*.ts` compiled → `assets/theme.js` or separate `assets/experiences.js` |

---

## 4. Brand-token bridging

`config/settings_schema.json` stub:

```json
[
  {
    "name": "Brand Colors",
    "settings": [
      { "type": "color", "id": "sr_rose_gold", "label": "Rose Gold", "default": "#B76E79" },
      { "type": "color", "id": "sr_dark", "label": "Dark", "default": "#0A0A0A" },
      { "type": "color", "id": "sr_silver", "label": "Silver", "default": "#C0C0C0" },
      { "type": "color", "id": "sr_crimson", "label": "Crimson", "default": "#DC143C" },
      { "type": "color", "id": "sr_gold", "label": "Gold", "default": "#D4AF37" }
    ]
  },
  {
    "name": "Typography",
    "settings": [
      { "type": "font_picker", "id": "sr_heading_font", "label": "Heading Font", "default": "archivo_n4" },
      { "type": "font_picker", "id": "sr_body_font", "label": "Body Font", "default": "inter_n4" }
    ]
  }
]
```

Note: Shopify's `font_picker` uses Shopify's font library. The brand-canon fonts (Archivo display, Hanken Grotesk body, Anton UI caps, Cinzel engraved caps) still ship self-hosted via `assets/fonts/` + `@font-face` in `theme.css` — the picker defaults are library fallbacks only (Hanken Grotesk is not confirmed in Shopify's library, hence `inter_n4` as the body fallback).

---

## 5. Liquid patterns (key snippets)

### Price formatter (handles pre-order)
```liquid
{%- comment -%} snippets/price.liquid {%- endcomment -%}
{%- assign is_preorder = product.metafields.skyyrose.is_preorder -%}
{%- if is_preorder -%}
  <span class="sr-price sr-price--preorder">Pre-Order · {{ product.price | money }}</span>
{%- elsif product.available -%}
  <span class="sr-price">{{ product.price | money }}</span>
{%- else -%}
  <span class="sr-price sr-price--soldout">Sold Out</span>
{%- endif -%}
```

### Product card (holo, parity with WP)
```liquid
{%- comment -%} sections/product-holo-card.liquid {%- endcomment -%}
<article class="sr-holo-card" data-collection="{{ product.metafields.skyyrose.collection }}">
  <a href="{{ product.url }}" class="sr-holo-card__link">
    <img src="{{ product.featured_image | image_url: width: 1200 }}" alt="{{ product.title }}" />
    <div class="sr-holo-card__body">
      <h3>{{ product.title }}</h3>
      {%- render 'price', product: product -%}
    </div>
  </a>
</article>
```

Uses Shopify metafields to carry the SkyyRose branding_spec / collection / is_preorder data that WP pulls from the CSV. Metafield namespace: `skyyrose`.

---

## 6. Deployment pipeline (deferred — scaffold only)

Planned, not implemented:
```bash
cd themes/shopify
shopify theme dev --store=skyyrose-prod.myshopify.com     # local preview
shopify theme push --live --store=skyyrose-prod.myshopify.com
shopify theme package                                      # produces zip for merchant import
```

The WP hot-swap deploy (`scripts/deploy-theme.sh`) has no Shopify equivalent — Shopify theme push is atomic at the platform level.

---

## 7. Catalog sync (deferred)

WP reads `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` at runtime via `skyyrose_get_product_catalog()`. Shopify would:
1. Import the CSV as Shopify Products (via Shopify Admin API or CSV import)
2. Map CSV columns to Shopify fields:

| CSV column | Shopify field |
|---|---|
| `sku` | Variant SKU |
| `name` | Product title |
| `price` | Variant price |
| `collection` | Product tag + Collection (manual) |
| `description` | Product description (HTML) |
| `badge` | Metafield `skyyrose.badge` |
| `is_preorder` | Metafield `skyyrose.is_preorder` (boolean) |
| `branding_spec` | Metafield `skyyrose.branding_spec` (multi-line text) |
| `image` | Product primary image |
| `front_model_image` | Product secondary image |
| `back_image` | Product image |
| `back_model_image` | Product image |
| `sizes` | Variant options (comma-split) |
| `color` | Variant option + tag |
| `edition_size` | Metafield `skyyrose.edition_size` (integer) |
| `published` | `published_at` (null = draft) |

A `scripts/shopify_sync.py` helper would wrap the Admin API — part of the follow-up plug-in PR.

---

## 8. Out of scope for this scaffold phase

- No live Shopify Admin API calls
- No actual theme push to a real Shopify store
- No Liquid template implementations beyond the 3 reference snippets above
- No Shopify Functions / checkout extensions
- No Shop Pay integration tuning

All of the above land in the follow-up "Shopify plug-in" PR. This knowledge file is the contract the plug-in PR must fulfill.

---

## 9. Files this knowledge applies to

**Reads (at build time):**
- `wordpress-theme/skyyrose-flagship/theme.json` — brand tokens, font families (copy into Shopify settings_schema)
- `wordpress-theme/skyyrose-flagship/assets/fonts/*.woff2` — copy into `themes/shopify/assets/fonts/`
- `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` — for sync (deferred)
- `wordpress-theme/skyyrose-flagship/template-parts/product-card-holo.php` — reference for Liquid parity

**Writes (scaffold only in this PR):**
- `themes/shopify/README.md`
- `themes/shopify/config/settings_schema.json` (stub)
- `themes/shopify/{layout,sections,snippets,templates,assets,config,locales}/.gitkeep`
