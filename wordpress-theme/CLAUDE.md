# wordpress-theme/ — SkyyRose Flagship Theme

Live target: https://skyyrose.co (WordPress.com Business plan, sftp.wp.com).
**Mistakes here are visible to customers within minutes.** Treat every change as production-touching.

## Quick commands

```bash
# From wordpress-theme/ subdir
cd wordpress-theme
npm run deploy:dry              # preview a deploy without uploading
npm run deploy                  # atomic hot-swap deploy (microsecond window)
npm run deploy --with-maintenance  # only for DB migrations / plugin changes
npm run lint:php                # PHP syntax check on staged .php files only
npm run verify                  # full local verification before deploy

# From repo root — catalog & data validators
python3 scripts/validate_catalog_consistency.py    # 13 checks; MUST be green before deploy
python3 scripts/check_catalog_duplicates.py        # name/slug dup detector
python3 scripts/validate_dossier.py                # per-dossier schema
python3 scripts/validate_3d_assets.py              # per-SKU asset presence

# Catalog mutation (precedent helpers)
python3 scripts/append_catalog_rows_2026_05_26.py  # how new SKUs were added
python3 scripts/generate_dossier_stubs_2026_05_26.py  # how stubs were generated

# PHPCS WordPress standard
cd wordpress-theme/skyyrose-flagship && vendor/bin/phpcs --standard=.phpcs.xml -s .
cd wordpress-theme/skyyrose-flagship && vendor/bin/phpcbf --standard=.phpcs.xml .  # auto-fix
```

Composer (required for PHPCS): installed at `~/.local/bin/composer`.

## Source of Truth — Products

**`wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`** is the ONLY product catalog.
46 products across 4 collections (Black Rose, Love Hurts, Signature, Kids Capsule).
The catalog grew 32 → 46 on 2026-05-26 when 14 orphan SKUs were promoted to active
pre-orders (lh-001, sg-004, sg-008, sg-010, sg-016, sg-017, sg-018, br-d01–d04,
sg-d01, sg-d03, sg-d04 — sg-d02 explicitly skipped). Several rows carry a DRAFT
note in `description` pending founder confirmation of name/price.

### Data files (all under `skyyrose-flagship/data/`)

| File | Role | Consumer |
|------|------|----------|
| `skyyrose-catalog.csv` | 24-column SKU table — authoritative product source | PHP helpers, validators, 3D pipeline |
| `logo-registry.json` | Brand-logo metadata + per-SKU logo assignment + jersey patches | Render pipeline, builder palettes |
| `product-similarities.json` | Per-SKU similarity arrays (for cross-sell, recommendations) | WC product recs, search |
| `dossiers/<slug>.md` | Founder-authored "what IS on this product" (one per SKU) | RAS 3D prompt, Gemini photo reference |
| `dossiers/_template.md` | Authoring rubric — vocabularies for `technique` / `region` | Founder reference when authoring |
| `dossiers/CLAUDE.md` | Per-dir agent guidance | Future sessions |
| `brand-logos/<collection>-logo.md` | Canonical brand-logo description (one per collection) | Dossier `logo_reference:` field |
| `product-references/<sku>-*.{jpeg,png}` | Truth-photo references (real-photo + techflat) | 3D pipeline input, founder review |

### PHP helpers (the only correct way to access product data in theme code)

- `skyyrose_get_product_catalog()` — full array keyed by SKU
- `skyyrose_get_product($sku)` — single product by SKU
- `skyyrose_get_collection_products($collection)` — products by collection slug
- `skyyrose_get_preorder_products()` — products where `is_preorder=1`

CSV → PHP array happens via `inc/woocommerce.php` (cached per request). Adding a row
to the CSV is sufficient — no PHP change required to make a new SKU queryable.

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

## Validation Scripts (run BEFORE commit, BEFORE deploy)

All canonical validators live in `/Users/theceo/DevSkyy/scripts/`:

| Script | Purpose | Exit code |
|--------|---------|-----------|
| `validate_catalog_consistency.py` | 13 checks across catalog ↔ logo-registry ↔ similarities ↔ dossiers ↔ retired-SKU guard | non-zero if any FAIL |
| `validate_dossier.py` | Per-dossier schema check (frontmatter required fields, controlled vocab) | non-zero if any FAIL |
| `validate_3d_assets.py` | Per-SKU asset presence check (source-products/, products/<sku>/) | non-zero if any FAIL |
| `validate_production.py` | Pre-deploy gate (env vars, secrets, build artifacts) | non-zero if any FAIL |
| `validate_environment.py` | Local dev env check (Python, PHP, composer paths) | non-zero if any FAIL |
| `check_catalog_duplicates.py` | Detects duplicate names/slugs in CSV | non-zero if any dup |
| `catalog_ml_audit.py` | LoRA-aware audit — flags SKUs the trained LoRA can't render | informational |
| `sync_catalog_downstream.py` | Propagate catalog changes to logo-registry, dossiers, etc. | non-zero on inconsistency |

**One command to run them all** (when this exists):
```bash
make validate-catalog        # runs the four CSV-side validators in sequence
```

If `make validate-catalog` does not exist yet, run individually:
```bash
python3 scripts/validate_catalog_consistency.py && \
  python3 scripts/check_catalog_duplicates.py && \
  python3 scripts/validate_dossier.py && \
  python3 scripts/validate_3d_assets.py
```

CI mirrors this via `.github/workflows/catalog-validate.yml`.

## Catalog Mutation Workflow

Any change to `skyyrose-catalog.csv` follows this protocol:

1. **Never hand-edit the CSV row-by-row in production.** Write a versioned helper
   script (precedent: `scripts/append_catalog_rows_2026_05_26.py` adds 14 rows
   atomically with field-validation + collision check + post-write row-count assert).
2. **Always create dossier stub at the same time.** Precedent:
   `scripts/generate_dossier_stubs_2026_05_26.py` — generates skeletal `.md`
   from `_template.md` for every new SKU. The consistency validator will FAIL
   the `dossier_slugs` check until every SKU's `dossier_slug` resolves to a real file.
3. **Update `logo-registry.json`** if the new SKU has SKU-specific logo placement
   (most do — at minimum, an `sku_logos` entry).
4. **Update `product-similarities.json`** with at least one similarity edge
   (otherwise the new SKU never surfaces in cross-sell recommendations).
5. **Run validators** — all 13 consistency checks + duplicate check must pass.
6. **Commit catalog + dossiers + helper script in one commit** so the audit trail
   shows intent + verification together. Title: `feat(catalog): add <N> pre-order SKUs`.

## Deploy Gate

Before any `npm run deploy`:

1. `npm run lint:php` — must pass with 0 errors
2. `npm run verify` — must pass (PHP syntax + build drift check)
3. `python3 scripts/validate_catalog_consistency.py` — must show 13/13 PASS
4. Manual visual review at skyyrose.co after deploy via `npm run deploy:dry` preview

Deploy uses atomic hot-swap (mv old → .old.ts; mv new → current). No maintenance mode needed
for theme-only changes. Use `--with-maintenance` flag ONLY for DB migrations or plugin changes.

Deploy script: `scripts/deploy-theme.sh` (top-level). Sets `SFTP_KEY=~/.ssh/skyyrose-deploy`,
target `sftp.wp.com`. Pre-deploy steps captured in `npm run verify`; post-deploy verify gate
automatically curls `https://skyyrose.co/?deploy_verify=$ts` and asserts:

- HTTP 200
- Response ≥ 50KB
- No PHP error markers in response body (`Fatal error`, `Parse error`, `Call to undefined`,
  `There has been a critical error`)

Override target URL via `PUBLIC_URL` env var if needed.

**Cache-bust on every post-deploy curl** — WP.com Batcache serves stale HTML for ~minutes
after `wp cache flush`. Always use `curl -s "https://skyyrose.co/?cb=$(date +%s)"` not bare URL.

## Permission Model

- Read operations on live site (`curl -s https://skyyrose.co/...`) are allowed.
- WooCommerce REST API writes (products, orders, media) require explicit confirmation before execution.
- `wp db reset`, `wp db drop`, `wp site empty` are denied.
- Reading `wp-config.php` is denied.

## Don't

- Don't deploy on Friday after 2pm Pacific.
- Don't reference retired SKUs (`br-013`) in any `.php` file. The 2026-05-26 catalog
  extension promoted lh-001, sg-004, sg-008, br-d01–d04, sg-d01, sg-d03, sg-d04 to
  active pre-orders — they are no longer retired. Validator authority:
  `scripts/validate_catalog_consistency.py` `retired_sku_guard` check.
- Don't bypass `npm run lint:php` "for a small fix."
- Don't commit changes that haven't passed `npm run verify`.
- Don't use `products.json` — it doesn't exist. Use the CSV helpers.


<claude-mem-context>

</claude-mem-context>