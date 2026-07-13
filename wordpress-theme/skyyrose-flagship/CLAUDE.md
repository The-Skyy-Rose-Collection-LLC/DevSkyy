# SkyyRose Theme — scoped context

**Commercial marketplace theme. Production at skyyrose.co**
**Theme Name:** SkyyRose | **Text Domain:** `skyyrose` | **@package:** SkyyRose

```
wordpress-theme/skyyrose-flagship/   — per-file map + token sizes in .wolf/anatomy.md
  assets/{css,js,fonts}    self-hosted fonts, zero Google Fonts CDN
  inc/ + inc/builders/     enqueue, security, WC, ajax, SEO; builder detection
  template-parts/          product-card-holo.php = holo card system
  patterns/ · woocommerce/ · blueprints/ · docs/ (ThemeForest)
  *.php                    collection + landing + immersive + builder templates
```

**Key systems:**
- `product-card-holo.css/js` — Holographic glass cards with magnetic tilt
- `inc/enqueue.php` — All CSS/JS loading, template slug detection
- `inc/security.php` — CSP headers, rate limiting, ABSPATH guards
- `inc/builders/detection.php` — `skyyrose_active_builder()` + `skyyrose_builder_owns_template()`
- `inc/patterns.php` — Block pattern registration for all collections
- `inc/performance.php` — Google Fonts removal, AVIF support, custom image sizes
- `functions.php` — Theme constants (`SKYYROSE_VERSION`), includes array

**PHPCS compliance:**
- `.phpcs.xml` in theme root — WordPress standard, `skyyrose` prefix
- Run: `cd wordpress-theme/skyyrose-flagship && vendor/bin/phpcs --standard=.phpcs.xml -s .`
- Auto-fix: `vendor/bin/phpcbf --standard=.phpcs.xml .`
- Composer must be installed first: `~/.local/bin/composer install`

## WordPress Rules

- **Theme serves `.min` in production** (`$use_min = ! SCRIPT_DEBUG`). After ANY CSS/JS edit, rebuild with `node scripts/build-css.js && node scripts/build-js.js` or the change is inert live. Re-verify the `.min` output, not just the source.
- Extend via hooks (actions/filters), never modify core
- API: `index.php?rest_route=` NOT `/wp-json/`
- Escape output: `esc_html()`, `esc_attr()`, `esc_url()`, `wp_kses_post()`
- Sanitize input: `sanitize_text_field()`, `absint()`
- Always `$wpdb->prepare()` — never concatenate untrusted input
- Nonce + capability checks on all write actions
- No `innerHTML` in JS — use `createElement` + `textContent`

The gotchas below trip fresh sessions.

## Build commands run from `wordpress-theme/` (the PARENT), not here

There is NO `package.json` in `skyyrose-flagship/` — it lives at `wordpress-theme/package.json`. From `wordpress-theme/`:
`npm run build` (CSS+JS) · `npm run build:css` · `npm run build:js` · `npm run rebuild` (clean+build) · `npm run watch:build`.
From inside `skyyrose-flagship/` you can still run the raw scripts: `node scripts/build-css.js` / `node scripts/build-js.js`.

## Adding a template = TWO edits in `inc/enqueue.php` (or CSS loads wrong, silently)

1. `$template_map` in `skyyrose_get_current_template_slug()` (~`enqueue.php:426`) — maps `template-*.php` filename → slug string.
2. `$template_styles` in `skyyrose_enqueue_template_styles()` (~`enqueue.php:485`) — maps slug → CSS file (a JS section mirrors this).
Then create the source CSS/JS and run `npm run build` to emit `.min`. Miss either array → new template gets wrong CSS or none.

## Brand constants — use them, never hardcode

Color constants (`SKYYROSE_COLOR_ROSE_GOLD` / `_GOLD` / `_CRIMSON` / `_SILVER`) are defined in committed `inc/brand-colors.php`. `functions.php` ALSO includes `inc/brand.generated.php` (loaded first) — that file is **generated from `assets/brand/brand.yaml` at build and is NOT committed** (you won't see it in a fresh checkout); it supplies `SKYYROSE_BRAND_TAGLINE` + helpers like `skyyrose_brand_collections()`. NEVER hardcode a hex value or the tagline in PHP — reference the constants.

## Skyy mascot (3D site host) — v1.9.0

- `assets/models/skyy.glb` is **draco-compressed** — `skyy-3d.js` MUST keep its DRACOLoader wiring (`setDRACOLoader` + decoder path derived from `MODEL_URL`) or the load fails silently and she never appears. Decoders live in `assets/js/lib/draco/`; CSP needs `'wasm-unsafe-eval'` (inc/security.php).
- Clip contract: lowercase `idle`/`walk` required, `wave`/`point`/`talk`/`joy` optional. mascot.js emits `skyy:*` CustomEvents; skyy-3d.js maps them to clips by name.
- Gate: `skyyrose_mascot_is_enabled()` (inc/mascot-config.php) — Customizer theme_mod `skyyrose_mascot_enabled`, **live by default**, but an explicit stored `false` in the DB overrides code defaults (bit us on first deploy).
- Mounts ONLY via footer.php (front-page.php uses `get_footer()`); checkout excluded.
- `window.SKYY_3D_CONFIG` is optional — nothing emits it; loader uses hardcoded theme-path fallbacks.

## Kill-switch awareness

`SKYYROSE_COMING_SOON_MODE` (`functions.php:~39`) — `true` makes all public traffic see HTTP 503. Default `false`; don't toggle without intent. `CONCATENATE_SCRIPTS = false` (`functions.php:~50`) is an intentional override for WP.com MIME/concat errors — don't "fix" it.
