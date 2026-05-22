# wordpress-theme/ — SkyyRose Flagship Theme

Live target: https://skyyrose.co (WordPress.com Business plan, sftp.wp.com).
**Mistakes here are visible to customers within minutes.** Treat every change as production-touching.

## Quick commands

```bash
cd wordpress-theme
npm run deploy:dry        # preview a deploy without uploading
npm run deploy            # atomic hot-swap deploy (microsecond window, no maintenance mode)
npm run lint:php          # PHP syntax check on staged .php files only
npm run verify            # full local verification before deploy
```

## Source of Truth — Products

**`wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`** is the ONLY product catalog.
34 products across 4 collections (Black Rose, Love Hurts, Signature, Kids Capsule).

PHP helpers (the only correct way to access product data in theme code):
- `skyyrose_get_product_catalog()` — full array keyed by SKU
- `skyyrose_get_product($sku)` — single product by SKU
- `skyyrose_get_collection_products($collection)` — products by collection slug

**RETIRED (do not reference in any code):**
- `assets/product-masters/catalog.yaml` — deleted 2026-04-19
- `assets/product-masters/manifest.json` — deleted 2026-04-19
- `scripts/generate_catalog.py` — obsolete
- Any `products.json` reference — that file does not exist in this project

## Architecture

```
wordpress-theme/skyyrose-flagship/
├── assets/css/         43 CSS files — all tokens live in design-tokens.css
├── assets/js/          23 JS files + experiences/ (Three.js worlds)
├── assets/fonts/       19 woff2 files (self-hosted, zero Google CDN)
├── inc/                21 PHP modules (enqueue, security, WC, ajax, SEO)
├── inc/builders/       Builder detection (Elementor, Divi, Beaver, Bricks)
├── template-parts/     37 partials — product-card-holo.php = holo card system
├── patterns/           Block patterns (4 collection heroes)
├── woocommerce/        5 WC template overrides
├── data/               skyyrose-catalog.csv + brand-logos/ + dossiers/ + product-references/
└── *.php               24 page templates + 3 builder templates
```

## PHP Rules (Non-Negotiable)

- Escape all output: `esc_html()`, `esc_attr()`, `esc_url()`, `wp_kses_post()`
- Sanitize all input: `sanitize_text_field()`, `absint()`
- Always `$wpdb->prepare()` — never concatenate untrusted SQL
- Nonce + capability checks on every write action
- No `innerHTML` in JS — use `createElement()` + `textContent`
- PHPCS WordPress standard enforced via `.phpcs.xml`. Run `vendor/bin/phpcs` before commits.

## Template Conventions

- **`front-page.php`** uses inline footer (`.ft` class) + `wp_footer()` instead of `get_footer()`.
  Any new template part added to `footer.php` MUST also be added to `front-page.php` before `wp_footer()`.
- Collection pages: `col-*` CSS classes, `data-collection` attribute, IntersectionObserver scroll-reveal (`.col-reveal`)
- Landing pages: `lp-*` CSS classes, IntersectionObserver scroll-reveal (`.lp-rv`)
- GSAP is only for: preorder, about, immersive templates — NOT collection or landing pages

## Deploy Gate

Before any `npm run deploy`:

1. `npm run lint:php` — must pass with 0 errors
2. `npm run verify` — must pass (PHP syntax + build drift check)
3. Manual visual review at skyyrose.co after deploy via `npm run deploy:dry` preview

Deploy uses atomic hot-swap (mv old → .old.ts; mv new → current). No maintenance mode needed
for theme-only changes. Use `--with-maintenance` flag ONLY for DB migrations or plugin changes.

Post-deploy verify gate automatically curls `https://skyyrose.co/?deploy_verify=$ts` and asserts:
- HTTP 200
- Response ≥ 50KB
- No PHP error markers in response body

## Permission Model

- Read operations on live site (`curl -s https://skyyrose.co/...`) are allowed.
- WooCommerce REST API writes (products, orders, media) require explicit confirmation before execution.
- `wp db reset`, `wp db drop`, `wp site empty` are denied.
- Reading `wp-config.php` is denied.

## Don't

- Don't deploy on Friday after 2pm Pacific.
- Don't reference retired SKUs (`lh-001`, `sg-004`, `sg-008`, `br-d01–d04`, `sg-d01–d04`) in any `.php` file.
- Don't bypass `npm run lint:php` "for a small fix."
- Don't commit changes that haven't passed `npm run verify`.
- Don't use `products.json` — it doesn't exist. Use the CSV helpers.


<claude-mem-context>

</claude-mem-context>