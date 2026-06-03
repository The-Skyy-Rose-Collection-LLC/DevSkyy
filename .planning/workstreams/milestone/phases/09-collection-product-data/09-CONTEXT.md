# Phase 9: Collection & Product Data - Context

**Gathered:** 2026-05-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Collection pages must each render their own hero banner (correct asset, correct alt text) and show only the products that belong to them. Phase covers three requirements from v1.1: DATA-01 (Black Rose hero banner correct), DATA-02 (pre-order SKUs excluded from live grids), DATA-03 (no cross-collection product leakage). REQUIREMENTS.md marks DATA-02 and DATA-03 `[x]` complete; DATA-01 remains `[ ]` pending — primary engineering target of this phase.

</domain>

<decisions>
## Implementation Decisions

### Black Rose Hero Diagnosis
- Hero configured in `inc/collection-content.php:31` via `hero_bg => /branding/sr-collection-black-rose.webp`
- Asset verified present: `assets/branding/sr-collection-black-rose.webp` (1.5MB WebP)
- Template consumption verified in `template-parts/collection/page.php:62-65` with `?v=' . SKYYROSE_VERSION` cache-bust
- Diagnosis path: confirm whether live site actually shows the wrong banner (caching artifact vs code bug). If asset + config both correct and live site still wrong, inspect CDN, version constant, or downstream template overrides.
- Verification via post-deploy curl + visual diff (`openwolf designqc`).

### Pre-Order SKU Filtering (DATA-02 — already complete)
- Source: `pre_order` column in `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` (single source of truth)
- Filter point: PHP catalog loader (single enforcement)
- Affected SKUs: br-004, br-005, br-006, br-d01..d04, lh-001, sg-001, sg-d01
- Live-site state already marked complete in REQUIREMENTS.md; phase task is to verify state, not re-implement.

### Cross-Collection Assignment (DATA-03 — already complete)
- Source: `collection` column in catalog CSV
- Enforcement: catalog loader filters by collection key
- Leak prevention: post-deploy structural assertion per collection page (grid SKUs must match `collection` field)
- Already marked complete; phase task is verification + audit script.

### Claude's Discretion
- Exact verification script structure (PHP audit vs Python audit)
- Whether to add a post-deploy regression test or rely on `verify_live()` gate alone
- Hero banner re-render trigger if cache is the issue (version bump vs manual purge)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `inc/collection-content.php` — per-collection content config (hero_bg, hero_logo, taglines per slug)
- `inc/collections-config.php` — collection metadata (slug, page_url, homepage tile images)
- `inc/product-catalog-display.php` — product grid rendering, likely the filter point for pre-orders
- `template-parts/collection/page.php` — unified collection layout consuming the content config
- `data/skyyrose-catalog.csv` — single source of truth for SKU metadata including `collection` and `pre_order` columns
- `scripts/deploy-theme.sh` — has `verify_live()` post-deploy gate; can be extended for collection assertions

### Established Patterns
- Asset URLs version-busted via `?v=' . SKYYROSE_VERSION` constant — bumping `SKYYROSE_VERSION` invalidates CDN cache
- Hero/template parts consume associative config arrays keyed by slug
- Translation-ready via `__('...', 'skyyrose')` for all visible strings
- Single-source-of-truth: catalog CSV is the only authoritative product list; PHP catalog loader reads it

### Integration Points
- Collection templates (`template-collection-*.php`) delegate to unified `template-parts/collection/page.php`
- Hero asset path resolution: `SKYYROSE_ASSETS_URI . $c['hero_bg']` (relative path from `assets/`)
- Cache control: SKYYROSE_VERSION in `functions.php`; `?nocache=` query param for ad-hoc bypass
- Deploy verification: `verify_live()` curls `https://skyyrose.co/?deploy_verify=<ts>` and asserts HTTP 200 + size + no PHP errors

</code_context>

<specifics>
## Specific Ideas

- Bumping `SKYYROSE_VERSION` and redeploying is the canonical fix for stale-CDN-asset bugs (per `CLAUDE.md` learnings).
- If Black Rose hero genuinely shows Love Hurts banner on live site, suspect: (a) wrong asset committed under right filename, (b) collection-content.php `hero_bg` value mutated, (c) collections-config.php `homepage-col-*.webp` mapping mismatched. Order of investigation: live curl → template render → asset bytes.
- Pre-order exclusion: only validate on live grid pages (catalog, shop), not on direct product URLs or admin (pre-orders should still be visible for purchase via direct link).

</specifics>

<deferred>
## Deferred Ideas

- Frontend admin UI for collection assignment editing — out of scope, CSV editing covers it.
- Multi-collection products (a SKU appearing in two collections) — current schema is single-collection-per-SKU; defer until product line warrants it.

</deferred>
