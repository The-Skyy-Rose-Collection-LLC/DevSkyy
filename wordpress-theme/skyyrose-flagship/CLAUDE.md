# SkyyRose Theme — scoped context

Loads on top of root. Root already covers: `.min` is `SCRIPT_DEBUG`-gated (rebuild after every CSS/JS edit),
`index.php?rest_route=` not `/wp-json/`, escape/sanitize, nonce+capability, no `innerHTML`, PHPCS. The items
below are NOT in root and a fresh session trips on them.

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

## Kill-switch awareness

`SKYYROSE_COMING_SOON_MODE` (`functions.php:~39`) — `true` makes all public traffic see HTTP 503. Default `false`; don't toggle without intent. `CONCATENATE_SCRIPTS = false` (`functions.php:~50`) is an intentional override for WP.com MIME/concat errors — don't "fix" it.
