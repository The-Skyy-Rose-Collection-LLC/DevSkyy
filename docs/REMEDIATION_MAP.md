# SkyyRose Structural Remediation — Phase 0 Map

Spec: `.planning/SKYYROSE_STRUCTURAL_REMEDIATION_SPEC.html` (artifact 055049ff).
Snapshots: `artifacts/live-snapshot/2026-07-05/` (7 pages, cache-busted curl, 2026-07-05).
Branch: `fix/structural-remediation` off `origin/main` (e3517cc73).

## Finding reproduction (live, 2026-07-05)

### REPRODUCES — in scope

| # | Finding | Evidence (snapshot grep) | WS |
|---|---------|--------------------------|----|
| F1 | Legacy footer social handles on shared footer | `instagram.com/theskyyrosecollection` ×2 on pre-order, about, collection-black-rose, experience-black-rose, pdp-br-001. Home uses `skyyroseco` (correct) | WS1 |
| F2 | Two footer implementations | home `<footer class="ft">` (front-page inline) vs all others `<footer class="site-footer">` (theme footer.php). Home lacks Social/Legal footer navs (3 navs vs 5–6) | WS1 |
| F3 | 4 skip links on home/pre-order/about (3 on collections) | "Skip to content", "Skip to content navigation", "Skip to main content", "Skip to the story" | WS1 |
| F4 | Mobile nav = second full menu copy | `<nav aria-label="Mobile navigation">` duplicate DOM alongside "Primary Navigation" on every shelled page | WS1 |
| F5 | `/collections/` index is an **empty page** | page 9327, template `skyyrose-canvas.php`: 0 `<header`, 0 `<footer`, 0 `<main`, 0 kids refs, 0 canvas/three.js. Visible copy = title + skip links + Jetpack share buttons only. Needs full flagship-shell index build, not just a shell wrap | WS1/WS2 |
| F6 | Dual nav trees: Collections + Experiences 1:1 | header links both `/collection-{slug}/` ×4 and `/experience-{slug}/` ×4 + `/experiences/` | WS3 |
| F7 | Canonical direction inverted | `/collections/black-rose/` **301 → `/collection-black-rose/`** (spec wants the reverse) | WS2 |
| F8 | `/experiences/` and `/experience-{slug}/` live 200 | probe | WS2/WS3 |
| F9 | Shopify-era `/products/*` dies 404 on apex | `www./products/black-rose-crop-set` 301→apex, apex 404 | WS2 |
| F10 | Footer Contact `mailto:` vs nav `/contact/` | `mailto:info@skyyrose.co` in home footer + 3× `/contact/` links | WS1 |
| F11 | Hardcoded piece counts on home | "14 Pieces", "5 Pieces", "12 Pieces" (home.html); collections index has no counts at all + omits Kids Capsule | WS4 |
| F12 | 64KB of content after `</footer>` on home | incl "Why SkyyRose" ×2, FAQ ×1, size guide ×5, cookie ×27, dialog ×4 | WS4 |
| F13 | `og:image`/`twitter:image` = .mp4 | `videos.files.wordpress.com/1zWCcc7C/logo_400x100.mp4` | WS4 |
| F14 | "ship Spring 2026" stale copy | home.html + pre-order.html | WS4 |
| F15 | GET add-to-cart anchors | `add-to-cart=` home ×6, collection-black-rose ×4 | WS5 |
| F16 | `/size-guide/` 404 | probe (spec wants canonical page) | WS4 |

### N/A — RESOLVED UPSTREAM (skip, list in PR)

| Finding (spec evidence) | Live status 2026-07-05 |
|---|---|
| "Enter the Universe" legacy nav | 0 occurrences on all 7 pages |
| Legacy nav links `/preorder/` | 0 occurrences; `/preorder/` 301s → `/pre-order/` single hop |
| www → apex missing | `www.skyyrose.co/*` 301s to apex single-hop (edge rule exists) — **HG-2 likely N/A**, re-verify at audit time |
| Countdown 00:00:00 on /pre-order/ | 0 countdown/timer markup |
| Quick View grids | 0 occurrences on collections/pre-order/collection-black-rose |
| placeholder.jpg product images | 0 image-file matches (16 hits are CSS class names) |
| `theskyyrosecollection`/`skyyrosellc` on home | home footer already uses `skyyroseco` handles |
| Elementor page documents for /collections/ & /pre-order/ | REST: both are theme-template pages (`skyyrose-canvas.php`, `template-preorder-gateway.php`). No `_elementor_data` surface to strip → `strip_legacy_shell.py` N/A; shell fix is theme-side |
| Fit Guide card 02 dead node | Now `<button data-open-size-guide>` wired to `#size-guide-modal` (exists on home). Remaining: `/size-guide/` canonical page 404s (F16) and modal is a div, not `<dialog>` |
| /faq/ missing | `/faq/` 200 with FAQPage JSON-LD ×1 (`template-faq.php`). Remaining: homepage still renders full FAQ after footer (F12) — cut to 3-question teaser |

## Site facts (REST, no auth)

- 30 published pages; all collection/experience/landing pages are theme-template pages, `parent=0` (flat slugs).
- `/collections/` = page 9327 (`skyyrose-canvas.php`), `/pre-order/` = page 9335 (`template-preorder-gateway.php`).
- Collections are **static pages, not product_cat archives** → per spec WS2: implement routes as pages now, log taxonomy migration as follow-up.
- Route flip needs: re-slug/re-parent 4 collection pages under `/collections/{slug}/` (site-state script, gated) **or** rewrite rules; plus removing the existing inverse 301.
- **Redirect mechanism: none exists.** Live 301s (`/preorder/`, `/collections/black-rose/`) carry `x-redirect-by: WordPress` + `x-litespeed-tag: …HTTP.404` → they are WP core `redirect_guess_404_permalink` guesses, not configured rules. The spec's "find and extend the live mechanism" resolves to: build the explicit layer in theme (`template_redirect` hook + map), which also kills the backward guess once pages re-slug.
- Host: WP.com (Atomic) + nginx; `.htaccess` not applicable. Edge www→apex already handled upstream.

## Base branch decision

`fix/structural-remediation` is based on **`feat/site-audit-batch` (PR #704, OPEN)** — not main.
Live skyyrose.co runs theme 1.7.0 = that branch (verified via asset `?ver=` on live HTML);
main is behind at 1.6.7. Basing on main would revert live improvements on deploy.
**Merge order: PR #704 first, then this PR** (its diff collapses to remediation-only once #704 lands).

## Repo locations

- Theme root: `wordpress-theme/skyyrose-flagship/` (version bumped 1.7.0 → **1.8.0**)
- Shell: monolithic `header.php` / `footer.php` (no header/footer template-part split); front-page previously bypassed `get_footer()` entirely
- Nav: theme-managed via `inc/menu-setup.php` (`skyyrose_get_menu_definitions()` + `SKYYROSE_MENU_BUILD_VERSION` bump ⇒ rebuild fires once on next request after deploy — **no site-state script needed**)
- Redirects: theme `inc/redirects.php` (`template_redirect` prio 1). The live backward 301 was `skyyrose_collection_redirects()` — flipped in place. `/home/`→`/` and www→apex live at the WP.com edge, not in theme.
- Catalog consumer: `inc/product-catalog.php` (`skyyrose_get_product_catalog()` reads the theme-relative CSV); preflight `READY/PENDING_USER_ASSETS` is a render-pipeline bundle status computed from `data/product-bundles/`, NOT a CSV column
- WP REST env names: `WORDPRESS_URL` / `WORDPRESS_USERNAME` / `WORDPRESS_APP_PASSWORD` (fallback `WP_*` in `wordpress/client.py`); file of record `.env.wordpress`
- Deploy: `wordpress-theme/package.json` → `npm run deploy` (`scripts/deploy-theme.sh`, tar+scp full-theme hot swap — stale live-only files like `skyyrose-canvas.php` disappear on next deploy). CI theme job = lint/build only, never deploys.

## Implementation summary (this branch)

| WS | Shipped |
|----|---------|
| WS1 | Canonical socials via `skyyrose_get_social_links()` (theme-mod overridable, defaults: instagram/tiktok/x `skyyroseco`, facebook `TheSkyyRoseCollection`); front-page now uses `get_footer()` (inline `.ft` footer deleted — killed F1/F2/F10/F12 in one move); single-menu shell (drawer relocates the one `wp_nav_menu` node via `matchMedia`, second copy removed); menu definitions → canonical tree (Collections▾4 canonical routes, Experiences tree removed, About→Our Story, FAQ→/faq/), `SKYYROSE_MENU_BUILD_VERSION` v702; footer Size Guide→/size-guide/, Care→/faq/; coming-soon handle fix |
| WS2 | `inc/redirects.php` overhaul: canonical `/collections/{slug}/` rewrites onto existing pages (`pagename=collection-{slug}`), `redirect_canonical` guard, `page_link` filter (every `get_permalink()` emits canonical), FLIPPED legacy 301 map (+experiences, custom-collection, Shopify `/products/*` best-match, is_404-gated case-normalization); all hardcoded flat-slug emitters swept to `/collections/{slug}/` (front-page, footer, 404, search, configs, landing fallbacks, nav fallback, about grid); `redirects.csv` manifest |
| WS3 | `inc/experience-rooms.php` = single room-data source; scene part gains `embedded` mode (no loader/tab-bar/toggle/CTA, lazy images, h2 demotion); collection pages render the experience as `#experience` opening layer after hero (static-LCP preserved); immersive templates deduped onto the helper (kept as rollback path, routes 301); enqueue: collection pages ship immersive bundle (gsap→immersive-core→immersive.js→wc-bridge via shared `skyyrose_enqueue_immersive_runtime()`) |
| WS4 | footer-cro: testimonials+Why-SkyyRose merged into one section, FAQ 6→3-question teaser + /faq/ link (stale "ship Spring 2026" answer REMOVED — HG-3 only affects /faq/ copy now); `skyyrose_og_logo_url()` MIME guard (mp4 logo can never be og:image again) applied at all 3 emitters; `/size-guide/` virtual route (rewrite+query var+template_include, 200, canonical+title) + `template-size-guide.php` sharing `skyyrose_get_size_guide_tables()` with the modal; `page-collections.php` collections index (flagship shell, 4 collections, editorial, no grids) + `collections-index.css`; data-count contract `[data-collection][data-piece-count]` on homepage cards + index cards; mobile-bottom-nav moved inside `<footer>` (DOM acceptance) |
| WS5 | Pre-order Reserve → Woo AJAX (`ajax_add_to_cart` + `data-product_id`, PDP-href fallback, rel=nofollow); v7 card → "View Piece" primary + "Quick Add" AJAX secondary (GET cart URL eliminated); production-image gate on gateway (file-existence, data-driven — see N/A note on the stale 6-SKU list); kids-capsule.css blues → brand tokens (#A8D8EA→#D8A1AA, #1A1A2E→#171310); theme.json `defaultDuotone:false` |
| WS6 | `scripts/structural_audit.py` — 7 check groups, AUDIT_BASE_URL, exits non-zero; before-run vs live captured 30 failures (evidence). WP-core-emitted style blocks exempted from brand scan (theme disables every disableable default) |
| Extra | v7 card backdrops: 4 founder-supplied artworks (black-rose star plaque, love-hurts neon star, SR script, rose emblem) → 800px AVIF+WebP derivatives (18–67KB; white knocked to alpha on the marks), wired via `skyyrose_v7_lockup_sources()` + `image-set()`, registered in visual-manifest; commercial-polish: global @25 confirmed covering new templates, `.btn.btn-ghost` primitives adopted on new CTAs |

### Spec findings that did NOT survive verification (added during implementation)

- **PENDING_USER_ASSETS 6-SKU exclusion list (WS5)** — all six (br-007, sg-009, sg-012, br-012, lh-006, sg-015) are `published=1` in the catalog CSV with real, on-disk theme imagery (front_model + image verified `file_exists`). The list described render-pipeline bundle state, not web assets. Shipped the durable rule instead: display-image-on-disk or the SKU doesn't render.
- **Fit Guide card 02 dead node (WS4)** — already a wired `data-open-size-guide` button targeting the existing `#size-guide-modal`.
- **"menu rendered twice consecutively" on homepage (WS1)** — audit-batch already removed front-page's own `#mainNav`; the remaining duplication was header.php's desktop+drawer double `wp_nav_menu`, fixed here.

## Human gates (final)

| Gate | Status |
|------|--------|
| HG-1 social handle set | Non-blocking. Shipped defaults: instagram/tiktok/x.com/`skyyroseco`, facebook.com/`TheSkyyRoseCollection`, contact stays `info@skyyrose.co` pending Corey's call on `corey@skyyrose.co`. Overridable in Customizer without code. |
| HG-2 www→apex | **N/A — already live at the edge** (single-hop 301 verified 2026-07-05, incl. deep paths). |
| HG-3 pre-order ship window | Non-blocking. Stale copy removed site-wide; `/faq/` pre-order timing copy is the only remaining surface — confirm real window. |
| HG-4 deploy + flush (BLOCKING) | `npm run deploy` from `wordpress-theme/`, then **flush permalinks** (Settings→Permalinks→Save) — required for `/collections/{slug}/` + `/size-guide/` rewrites. Menu rebuild fires automatically (v702 flag). Then `python3 scripts/structural_audit.py` must exit 0. |
| HG-5 (new) Ally skip-links | The extra "Skip to main content"/"Skip to content" links are injected by the live Ally a11y plugin (`skyyrose-ally-fixes-css`), not the theme. Theme emits exactly one. Disable the plugin's skip-nav feature to pass the one-skip-link acceptance. |
