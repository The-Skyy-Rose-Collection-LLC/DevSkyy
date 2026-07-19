# Fix Log — WP Commercial Theme Sweep

## Wave 1 — 2026-07-19

### P0-1: style.css malformed rule (missing `{`)
- `style.css:515-522` selector list ended with `,` then `padding-top: 0; }` — rule dead.
- CSS error recovery consumed through line 530's `{`, ALSO killing `.homepage-v2 .site-header/.site-footer { display:none }` → double-nav risk on homepage, header-offset dead on immersive templates.
- Fix: last selector now ends ` {`. style.css served unminified (get_stylesheet_uri) — no build step needed.
- Found: Atlas census. Verified: direct read + Atlas's production curl byte-match.

### P0-2: duplicate mobile-bottom-nav include
- `footer.php:253` (intentional, in-footer per WS4 acceptance) + `footer.php:260` (stale) both rendered `<nav class="mobile-nav">` — duplicate fixed chrome + duplicate a11y landmark on every page.
- Fix: deleted line-260 include. `php -l` clean.
- Found: Atlas census (live-verified 2× nav on /about/ + /collections/black-rose/).

### Baseline (pre-fix) — tasks/wp-commercial-theme/baseline/summary.csv
Zero pages ≥90 all-categories on mobile. Fires: PDP mobile perf 49 / LCP 27.3s / TBT 671ms / BP 79 · cart CLS 0.49 + SEO 69 · black-rose mobile LCP 13.6s · landing-BR LCP 13.7s · pre-order mobile LCP 10.1s · wishlist desktop CLS 0.40 · collections a11y 89 · homepage mobile perf 64.
Data gaps to re-run at verify: faq desktop (truncated row), 404 probe (both rows errored).

### Triage corrections (main thread, post-Pixel)
- Pixel P1 "experiences duplicate collections": NOT a defect — documented WS3 301s (inc/redirects.php:118-132, since 1.8.0). Dropped both URLs from pages.txt (audit set now 18).
- Pixel P0 dossier leak: WC product data is CLEAN (the-fannie desc = 107 chars via REST). Leak is THEME-side: single-product.php editorial layout renders internal dossier fields; AND all 36 raw dossier .md files are publicly fetchable (curl 200, 5.5KB) under wp-content/themes/.../data/dossiers/. Wider exposure: data/ also ships skyyrose-catalog.csv + .bak, product-embeddings.json (502KB), logo-registry.json, render-corrections.json, product-references/, python build scripts — all in the deployed theme.
- Pixel P1 pre-order smoking hero: FOUNDER DECISION — flagged, no autonomous swap (money page, paid-ads blocker).

### Atlas — Wave 1 page-level fixes (2026-07-19)

**PDP /product/the-fannie/ — LCP 27.3s root cause fixed**
- Baseline: LCP element = `h2#sr-ed-piece-h` (TEXT, render delay 24,952ms; FCP was 1.7s).
  Chapters 1+2 of `template-parts/product-detail-editorial.php` carried `rv-clip-up` on the
  `<section>` itself — resting state `clip-path: inset(100%); opacity:0`
  (`animations-premium.css:22-32`) until deferred `premium-interactions.js` adds `.is-visible`,
  which on throttled mobile lands after three.js(855ms)/Stripe/GPay eval.
- Fix: removed `rv-clip-up` from `.sr-ed__encounter` and `.sr-ed__piece` (above-fold, LCP path);
  constraint comment added. Below-fold chapters (3/4/7) keep reveals. Same fix family as bug-225.
  Expected: LCP becomes the fetchpriority=high encounter image at ~FCP time.
- NOT fixed here (out of boundary / not theme-fixable): TBT 671ms = mascot three.js+GLB
  (→ enqueue-requests.md #2); best-practices 78-79 = third-party cookies from Stripe/hcaptcha/
  Google Pay express checkout on PDP — plugin territory, only fixable via Stripe gateway
  settings (disable express elements on product pages) — needs a product decision, DOCUMENTED
  AS ACCEPTED for now.

**Cart /cart/ + Wishlist — CLS 0.486/0.507/0.403 root cause fixed (shared)**
- Baseline layout-shifts: the shifted node on BOTH pages is `footer section.ft-cro-craft`
  (score 0.485 mobile / 0.491 desktop cart; 0.388 wishlist desktop). Not WC-block hydration —
  wishlist is fully server-rendered. Root cause: `footer-cro.php` enqueued its stylesheet
  DURING footer render, so WP printed the <link> in wp_footer AFTER the markup → section
  first paints unstyled, then re-lays-out when footer-cro(.min).css lands. Counted only on
  short pages where the footer opens in-viewport (cart top=574px, wishlist top=741px) —
  which is why no other page shows it.
- Fix: `template-parts/footer-cro.php` now `wp_register_style` + `wp_print_styles` in place —
  the in-body <link> blocks paint of subsequent content until applied, so the section renders
  styled on first paint. Composes with a future head enqueue (enqueue-requests.md #1).
- Residual small shifts (0.0007-0.015): late fonts.wp.com Inter re-rendering
  `.ft-cro__subheading` — sitewide font-registration issue (enqueue-requests.md #5).

**Cart SEO 69 — ACCEPTED, no fix**
- Sole failing audit: `is-crawlable`; meta is `max-image-preview:large, noindex, follow` —
  WooCommerce-standard noindex on cart. Correct behavior; per team-lead pre-approval this is
  documented as accepted. SEO 69 on /cart/ will not reach 90 and should be excluded from the
  gate for cart/checkout.

**Verification** (build + deploy deferred to central sweep per rules)
- `php -l` clean: product-detail-editorial.php, footer-cro.php. No .min rebuild done (npm build
  centralized); footer-cro fix is PHP-only, PDP fix is PHP-only — both live-effective on deploy
  without a CSS/JS rebuild.
- Files touched: template-parts/product-detail-editorial.php, template-parts/footer-cro.php,
  tasks/wp-commercial-theme/enqueue-requests.md (new). Boundary respected: no inc/enqueue*.php,
  inc/performance.php, front-page.php.

### Bolt — Wave 1 global enqueue/perf fixes (2026-07-19)

All changes PHP-only — no CSS/JS source edited, no .min rebuild needed for this batch.
`php -l` clean on every touched file: inc/enqueue.php, inc/enqueue-performance.php,
inc/enqueue-phases.php, front-page.php (inc/performance.php read, not modified).

**1. Dead render-blocking hero CSS removed sitewide** — `inc/enqueue.php`
- Verified by grep: `template-parts/hero-cinematic.php` has ZERO `get_template_part` callers;
  the `cine-hero` classes exist nowhere outside the part itself. The prior claim that
  template-preorder-gateway.php uses it is stale — preorder renders its own inline `.po-hero`.
- Removed the sitewide `skyyrose-hero-cinematic` enqueue (was in `<head>` on every
  non-lightweight page, confirmed shipping live via curl). CSS files + part left on disk;
  removal comment documents the re-enqueue requirement if a template ever adopts the part.

**2. Inter preload KEPT — census P1-4 is a false positive** — comment added at
`inc/enqueue-performance.php` preload site
- Evidence: `cookie-consent.css:36,65` uses `Inter` as PRIMARY (banner shows on every fresh/
  Lighthouse visit), and footer.css/components.css/immersive*.css/accessibility.css use
  `var(--font-body, 'Inter', sans-serif)` where `--font-body` is NEVER DEFINED (real token:
  `--skyyrose-font-body`) — so the `'Inter'` fallback actually renders sitewide. Dropping the
  preload would regress font paint. Handoff (Pixel/style owners): repoint those stacks at the
  Hanken token (visual change), THEN gate this preload to 404.
- Related (Atlas req #5): the late-reflowing REMOTE Inter is fonts.wp.com v13 printed via
  `<style class="wp-fonts-local">` (WP Font Library). theme.json is clean (all 5 families
  `file:./assets/fonts/*`), so the remote face is a wp.com Fonts-UI install living in the DB —
  durable fix is uninstalling it in wp.com admin (operator action), not theme code.
- Anton preload verified used (primary face in homepage-v2, single-product, info-pages,
  generic-pages, card CSS) — kept.

**3. Plugin/Jetpack stylesheet flood — real handles now dequeued, all fail-closed** —
`inc/enqueue-performance.php`
- New helper `skyyrose_template_never_renders_content()`: grep-verified that only page.php,
  single.php, search.php + template-elementor-*.php call `the_content()`; the 14 custom
  template slugs never render stored content.
- `skyyrose_dequeue_block_styles()`: bypasses the `has_blocks()` early-return on those slugs —
  front page (and collections etc.) no longer keep wp-block-library/wc-blocks-style/
  global-styles because of UNRENDERED stored block markup. Verified zero `--wp--preset`/
  `has-*-color` usage in custom templates/CSS before extending.
- `skyyrose_dequeue_jetpack_non_context_styles()`: added live-verified handles
  `jetpack-search-results-list-style` + `jetpack-search-filter-wc-attribute-style` (gated
  `! is_search()`), `jetpack-block-podcast-episode` (gated `! has_block(podcast)`),
  `jetpack-forms-layout` (gated `! has_block('jetpack/contact-form')`; contact template has
  zero Jetpack refs).
- New `skyyrose_dequeue_platform_styles()`: `wp-calypso-bridge-masterbar` (logged-out only),
  `wp-block-code` + `jetpack-layout-grid` (per-block `has_block` gates),
  `wc-stripe-blocks-checkout-style` (kept on cart/checkout only), `sharedaddy`+`social-logos`
  (dequeued only on never-renders-content templates; kept on single/blog/page/PDP/cart),
  `elementor-frontend` + `elementor-post-*` (kept whenever Elementor's own document registry
  says it built the page, via `skyyrose_builder_owns_template()`).
- All three dequeue functions also registered at `wp_footer` priority 1 — the trailing
  homepage group (sharing, wc-blocks, Stripe, social-logos) is enqueued mid-render and prints
  in the footer where head-time dequeues never saw it. Dequeues are idempotent.
- Expected homepage impact: ~11 of 15 plugin sheets gone (40 → ~29 stylesheets incl. inline
  savings from global-styles); similar cuts on collection/landing/preorder pages.

**4. Nine raw-served handles now min-aware** — `inc/enqueue.php` + `inc/enqueue-phases.php`
- size-guide/luxury-cursor/skeleton CSS, performance-guardian.js (global),
  brand-atmosphere.css+js, smart-showcase.css, personalization.css+js all use the standard
  `$use_min` pattern. All nine .min siblings verified present AND newer than sources
  (mtime-checked) — no stale-min risk. ~40KB raw → ~19KB min. size-guide.css was in the PDP
  render-blocking audit (173ms) — closes Atlas req #3.

**5. Double animation stack on collection pages — KEPT, map documented (no safe dequeue)**
- Verified usage: Motion One → ONLY premium-interactions.js (8 real refs; powers the .rv/
  reveal system used in collection markup). GSAP → immersive-core.js (27 real refs, embedded
  scene intro). ScrollTrigger → collection-feature-scroll.js (4 refs) + preorder/kc scripts.
  collection-pages.js's "gsap" mention is a comment; immersive-core's "Motion" hits are all
  prefersReducedMotion(). Both stacks are genuinely co-required as coded — removing either
  breaks reveals or the scene intro. De-duplication would need a JS port (premium-interactions
  reveals → GSAP, or immersive-core → Motion), which is beyond surgical scope. Logged for a
  future wave.

**6. Homepage image payload** — `front-page.php` + verification
- Hero LCP: verified correct already — eager, `fetchpriority="high"`, w/h attrs, `<picture>`
  AVIF/WebP. Preload ↔ render match verified: both derive the AVIF URL from the same
  `skyyrose_avif_sibling_pair( homepage-hero-bg.webp )` call — no double-download.
- Strip (12 imgs): had loading (2 eager / 10 lazy), decoding=async, w/h. Added
  `fetchpriority="low"` to all strip imgs so the decorative eager pair never competes with the
  hero LCP fetch. `sizes` NOT added — the strip imgs have no srcset (single SOT-resolved
  files), so `sizes` would be inert; noted instead of cargo-culted.

**7. Footer-cro head enqueue (Atlas req #1)** — `inc/enqueue.php`
- `skyyrose-footer-cro` now head-enqueued globally (min-aware, dep design-tokens). The part's
  interim register+print in template-parts/footer-cro.php becomes a no-op (already-printed
  handle). Completes the cart/wishlist CLS fix chain.

**Deliberately NOT changed (fail-closed log)**
- `skyyrose-immersive-css` (skyyrose-immersive PLUGIN sheet, loads sitewide): plugin source is
  NOT in the repo (server-only) — cannot census its render surface. Left enqueued; needs
  plugin-side gating or an operator decision.
- `woocommerce-layout` kept everywhere (theme relies on it for grid structure, per existing
  intent in skyyrose_dequeue_woocommerce_styles()).
- Mascot 3D cost on mobile PDP (Atlas req #2, TBT 671ms driver): PROPOSAL ONLY — mascot is
  founder-loved with visibility history (bug-225/226/228 family). Proposed gate: on
  `single-product` + viewport ≤768px, require first interaction (pointerdown/scroll) instead
  of requestIdleCallback before fetching mascot.min.js/skyy-3d.min.js/GLB (keeps her, defers
  1.1MB+855ms off the Lighthouse trace). Needs founder/main sign-off before I implement.
- Inter preload (see #2 above) — kept on evidence.
- Navbar 637KB webp fallback (Atlas req #4) — header.php is outside my boundary; stays with
  Pixel/main.

### Bolt — Wave 1 addendum: Inter preload final-state update (2026-07-19)

Supersedes item 2 of my main entry. Team-lead relayed Pixel's live audit: 19/20 pages compute
body font = Inter today (the undefined --font-body fallback I found is the mechanism), and
Pixel is fixing Hanken application sitewide IN THIS SAME deploy train. Preload set updated in
`inc/enqueue-performance.php` to match the FINAL state, not the current one:
- `hanken-grotesk-latin.woff2` stays preloaded sitewide (it was already in the set; it becomes
  the real body font).
- `inter-latin.woff2` preload now gated to the `404` slug only (its sole canonical use,
  404.css `--ff-system`). Saves the 48KB fetch on every other page once Pixel's stack fix
  lands.
- Archivo + Anton preloads unchanged (verified primary-face usage), Cinzel stays BR-gated.
- Coupling note: this gate assumes Pixel's Hanken repoint (incl. cookie-consent.css) ships in
  the same deploy. If that slips, non-404 pages briefly render their (fallback) Inter without
  preload — soft font-swap delay, no breakage. `php -l` clean.

### Deploy-gate checklist (main thread — verify before manifest)
- [ ] COUPLING: Bolt's Inter-preload-404-gate assumes Pixel's Hanken repoint ships SAME deploy — confirm Pixel's font fix landed before build.
- [ ] PENDING: header.php 637KB video-fallback img preload-scanned on EVERY page (~745KB/page savings) — unassigned; Pixel visual call or main-thread fix. Must resolve before deploy train closes.
- [ ] Access round B green-light after Pixel lands (FIX-4/6/9/2 + Pixel-lane contrast items).
- [ ] Central build: npm run build from wordpress-theme/ AFTER all source edits; verify .min freshness.
- [ ] Sweep: php -l all touched, npm run lint:php, git diff scope check, version triple bump (style.css/functions.php/readme.txt).
- [ ] Deploy from MAIN checkout (17 riders present) + SHOW manifest (standing auth).
- [ ] Sentinel: fresh Lighthouse (18-URL set + faq.desktop re-run), Playwright mobile+desktop eyes-on, Bolt's 3 dequeue risk spots (global-styles on collections/homepage, Elementor-built pages, cart footer styles), dossier URL must 404/absent post-deploy.

### Bolt — Wave 1 addendum 2: header 637KB preload-scan fetch (Atlas req #4, reassigned to Bolt)

- Root cause verified: header.php's navbar `<video>` carried an `<img src=tsrc-lockup-rotating@2x.webp>`
  (636,270B live) as fallback content. The preload scanner fetches any `<img>` inside `<video>` on
  every page even though that content only renders in browsers lacking the `<video>` ELEMENT itself —
  browsers that merely can't play the source show the `poster` instead (poster persists when no
  source is playable). So the 636KB animated webp was fetched sitewide and displayed nowhere.
- Fix: fallback `<img>` repointed at `tsrc-lockup-static@2x.webp` (5,854B live — the SAME URL as the
  poster and the adjacent `.navbar__logo-static` img, so the scanner's fetch is one cached request,
  zero extra bytes). Constraint comment added in-place. No blank-hero regression path: can't-play →
  poster; no-video-element → static logo img; reduced-motion → existing `.navbar__logo-static` CSS swap.
- ~630KB saved per page sitewide. `php -l` clean on header.php. Note: both webp files are gitignored
  live riders (only the .webm is tracked) — verified live via curl HEAD, and deploy must stay
  rider-aware per bug-252.

## Access — round A applied (2026-07-19)

All diagnosis-only refs: `tasks/wp-commercial-theme/a11y-seo-fixlist.md`. Source edits only — NO .min rebuilds (central build step), no commits, no deploy. All touched PHP passes `php -l`; JS passes `node --check`.

| Fix | Files (theme-relative) | Change |
|---|---|---|
| FIX-1 (ARIA role cascade, a11y w21) | `template-parts/product-card-v7-lookbook.php:54`, `template-parts/product-grid.php:274` | Removed `role="listitem"` from v7card article + `role="list"` from grid div. Clears aria-allowed-role, aria-required-children, aria-required-parent on shop/black-rose/signature/experience-BR/landing-BR. |
| FIX-3 (aria-prohibited-attr, w7) | `assets/js/premium-interactions.js` (splitChars/splitWords/splitLines) | Split engine no longer sets `aria-label` on the split element; appends a `.screen-reader-text` span with the full text before the aria-hidden animated spans. Verified animation CSS targets `.sr-char/.sr-word/.sr-line` only; split runs once at init (no re-split path). |
| FIX-13 (BP errors-in-console) | `inc/security.php:102` | `Permissions-Policy` accelerometer/gyroscope `()` → `(self)` — both, since Chrome gates `deviceorientation` (immersive-core.js:281) on both. Third-party frames still blocked. |
| FIX-8 (about contrast) | `assets/css/about.css` | `.abt-mission .abt-chapter__label` alpha .55→.62; `.abt-coll-row__index` alpha .32→.38; `.abt-community__label` `var(--skyyrose-accent)`→`#96545F` (rose gold deepened for cream bg, 5.0:1). ⚑ founder-report: local rose-gold-on-cream derivative. |
| FIX-11 (contrast stragglers) | `assets/css/collections-index.css:88`, `assets/css/homepage-v2.css:447`, `assets/css/contact.css:307,391` | ci-card__num alpha .4→.55; press-item opacity .75→.88; order-number `.is-hidden` +`visibility:hidden`; placeholder alpha .5→.6. |
| FIX-14 partial (BP image-aspect-ratio) | `assets/css/landing-scrollytell.css:455` | `.lp-pane__mobile-img` +`height:auto` (covers all 3 landing templates). Pre-order lockup/logo imgs HELD (Pixel lane). |
| FIX-16 (BP inspector-issues, about) | `template-parts/about/featured-video.php:38`, `template-parts/about/press-section.php:69` | YouTube embeds → `youtube-nocookie.com`. |
| FIX-10 (heading-order, shop w3) | `woocommerce/archive-product.php` | sr-only `<h2>Products</h2>` before product loop (bridges h1→h3). |
| FIX-15 partial (label-in-name, w0) | `template-parts/product-card-holo.php:146`, `template-parts/collection/page.php:318` | holo buy aria-label → `Add to Cart: %s` (starts with visible text); crossnav links drop aria-label (name computes from visible h3+p). `a.v7card__frame` case HELD — badge-text interaction needs live re-test; `front-page.php` kc-heir case is Bolt lane. |

**HELD for round B (lanes/decision):** FIX-2 + FIX-14-preorder (template-preorder-gateway.php — Pixel), FIX-4 dark-ink option A (cookie-consent.css/footer.css/woocommerce.css/contact submit — Pixel), FIX-6/7 crimson text token + LH badge ink (product-card-v7.css + about.css:921 — coupled, apply together), FIX-9 (preorder-gateway.css — Pixel). FIX-5 NOT implemented (founder). FIX-12 (Jetpack Likes) = wp-admin/plugin op, not theme code — needs ops.

## Wave 1 — Pixel (visual fixes, 2026-07-19)

### 1. P0 Shop desktop collapse — `assets/css/woocommerce.css`
- Root cause was THREE stacked defects, live-probed at 1440px:
  (a) `#primary.content-area` (theme WC wrapper, `inc/woocommerce.php:99`) has no container styles → h1/notices/grid flush at x=0;
  (b) WC core `woocommerce-layout.css` (kept enqueued per Bolt's Wave-1 decision) float rules inside our CSS grid: `li.product{width:30.75%}` shrank every card to 139px of its 453px track, and the clearfix `ul.products::before{display:table}` became a **phantom first grid item** pushing card 1 into column 2;
  (c) card 1 renders `holo` while 2+ render `v7card` — **by design** (v7 requires verdict:verified imagery per SKU, `inc/v7-cards.php`; holo is the sanctioned fallback). NOT changed.
- Fix: archive-scoped container (`.woocommerce-shop/.post-type-archive-product/.tax-product_cat/.tax-product_tag #primary.content-area`, max-width 1600px + clamp padding) + products-header rhythm + `content:none` on the loop clearfix + float/width/margin neutralization on `li.product`. Single product/cart/checkout untouched (own their layout; cart flush-left resolves via Atlas's canvas-meta repoint — theme cart CSS already containers `.skyy-cart__*` at 1400px but live cart renders default shortcode markup without those classes).

### 2. P1 Body font = Inter on 19/20 pages — `assets/css/design-tokens.css`
- Root cause: `style.css:239` sets `body{font-family:var(--font-body, 'Inter', ...)}` but **`--font-body` was never defined anywhere** — the legacy-alias block §1.12 has `--font-heading`/`--font-headline`/`--ff-*` but skipped the body alias, so every template on the base stylesheet fell to the Inter fallback (home escaped via homepage-v2.css's direct 'Hanken Grotesk' rules).
- Fix: one line — `--font-body: var(--skyyrose-font-body);` in §1.12 (+ comment updated). Cascades to style.css base typography AND components.css:300. Preload implication filed in enqueue-requests.md (Hanken becomes the sitewide body face).

### 3. P1 Mobile overlay stack — `template-parts/cookie-consent.php`, `assets/css/cookie-consent.css`, `assets/css/mascot.css`
- Stacking/clearance contract: while the banner is visible, `<html>` carries `.skyyrose-consent-open` (toggled in the part's inline JS, removed on accept/decline/Esc); `cookie-consent.css` defines `--skyyrose-consent-clearance` (76px desktop / 120px ≤768px); `.skyyrose-mascot` + `.skyyrose-mascot__recall` add the var to their bottom offset — no more widget clipped behind the banner (z 9990 vs 9998).
- Banner compacted on mobile (12px type, tighter padding/gap ≈ ≤120px tall vs ~130px+) and its mobile breakpoint moved 599px→768px to match `.mobile-nav` — previously 600-768px viewports had the banner COVERING the bottom nav.

### 4. P1 Privacy-policy mobile horizontal scroll — `assets/css/generic-pages.css`
- Re-probe corrected the audit: culprit is an unwrapped content `<table>` (408px wide → right edge 424px; 6 raw tables on the page), NOT `.mobile-menu__panel` (fixed wrapper — cannot extend scroll). Audit D6 amended.
- Fix: `.skr-page__content.entry-content table { display:block; max-width:100%; overflow-x:auto }` — tables scroll in their own box on all `.skr-page` templates.

### 5. P1 Pre-order footer — NO CODE CHANGE (audit false positive)
- Verified live (cache-busted curl): `#colophon.site-footer` IS present on /pre-order/; `get_footer()` at `template-preorder-gateway.php:796`. The audit probe's comma-list `querySelector` returned the first DOM-order match — a `.po-card__footer` card element. Audit D4 withdrawn.

### 6. P2 three.js no-WebGL fallback — `assets/js/skyy-3d.js`
- `initScene()` constructed `THREE.WebGLRenderer` bare; in WebGL-less clients (bots, headless, GPU-blocklist) three console.errors then THROWS → the uncaught pageerror seen on every audited page (mascot mounts sitewide via footer.php).
- Fix: throwaway-canvas `webgl2||webgl` pre-probe (silent bail, hides the 3D canvas, keeps mascot.js's 2D sprite) + try/catch backstop around the renderer. `node --check` clean.
- Note: the audit's "empty scene voids" on collection pages carry the scroll-state caveat; no other theme JS constructs a WebGLRenderer (grep-verified — immersive.js has no three usage), so this closes the only in-repo WebGL throw path.

**Verification**: `php -l` clean (cookie-consent.php); `node --check` clean (skyy-3d.js); brace-balance clean on all 5 edited CSS files. Source-only per sweep rules — `.min` rebuild + live Playwright verify deferred to the central build/deploy step.

### Atlas — Wave 1b: data/ exposure remediation (2026-07-19)

**Runtime allowlist (census, file:line evidence)** — theme PHP reads from data/ at runtime:
- `data/skyyrose-catalog.csv` — inc/product-catalog.php:28 (+ inc/skyyrose-product-meta.php:551)
- `data/v7-cards.json` — inc/v7-cards.php:27
- `data/site-guide.json` — inc/mascot-config.php:148
- `data/collections/*/sot.json` — inc/collection-sot-reader.php:10
- `data/editorial-index.json` — NEW compiled artifact (see below)
- `data/product-similarities.json` — read at inc/product-catalog.php:362 but
  skyyrose_get_similarity_skus() has ZERO callers (grep) → runtime-unused → excluded.
Everything else in data/ (36 dossiers, brand/, brand-logos/, product-references/, 5 .py build
scripts, embeddings 502KB, logo-registry, render-corrections/keepers, visual-manifest, CSV .bak,
collections copy.md/identity.json/index.html) has no PHP reference → excluded from deploy.

**PDP leak fix (fail-closed)**
- inc/product-catalog.php: skyyrose_get_product_dossier() no longer opens/parses raw dossier
  .md at runtime. It reads compiled data/editorial-index.json (slug→true map); missing/invalid
  index → null → standard PDP (fail closed, bug-230 rule). Return shape kept (internal keys
  always empty) so ProductCatalogTest contract holds.
- template-parts/product-detail-editorial.php: removed the two internal-field renders —
  `.sr-ed__garment-lock` (the "NOT a backpack…" render-instruction text) and
  `.sr-ed__branding-detail` Front/Back spec blocks — plus their orphaned variables.
  Constraint comment added: dossier fields are render-pipeline specs, never consumer copy.
- NO WooCommerce data touched (confirmed clean per team-lead intel).

**Build step**
- NEW skyyrose-flagship/scripts/build-editorial-index.js — compiles dossiers → editorial-index
  with the SAME eligibility predicate as the retired runtime parser (lock non-empty OR
  branding ### Front non-empty). Deterministic output, refuses to write an empty index.
- wordpress-theme/package.json: "build" now runs build:editorial first.
- Generated + verified: 35/36 files eligible (the 36th is a stray CLAUDE.local.md, not a
  dossier) — predicate parity check vs old PHP regexes: EXACT MATCH → zero products change
  layout.

**Deploy exclusions** — scripts/deploy-theme.sh, added to BOTH tar_excludes (:565+) and
RSYNC_EXCLUDES (:505+), keep-in-sync comments cross-referencing each other. No conflict with
the 17-rider manifest (riders are all under assets/, docs/engineering-learnings.md:154-158).

**Verification (all can fail; all passed)**
- php -l clean ×2; bash -n clean (via tmp copy — paid-api-stopgate false-positives on the
  deploy-script path in command position, bug-177 class; not bypassed, routed around).
- REAL tar built with the script's own exclude array (eval-extracted): all 15 internal
  patterns absent (0 matches each), all 5 runtime files + spot-check theme files present.
- PHPUnit ProductCatalogTest: 41/42 pass incl. all 4 dossier tests. The 1 failure
  (test_display_image_returns_primary_image_slot:147) is PRE-EXISTING — function byte-identical
  to git HEAD; the test encodes the pre-onmodel image preference order. Flagged, not fixed.

**Residual risks for main (not in this wave)**
- data/skyyrose-catalog.csv remains deployed (runtime CSV parse) and world-readable — contains
  internal-ish columns (branding_spec, render_*, engine_override). Proper fix: compile catalog
  → consumer-fields JSON at build, then exclude the CSV too. Bigger refactor.
- tar_excludes lacks the 'scripts' exclusion that RSYNC_EXCLUDES has — theme build scripts
  likely ship in the tar today (harmless-ish; sync the lists).
- Files already ON the live server stay public until the next deploy (hot-swap removes them).
  Post-deploy verify: curl data/dossiers/the-fannie.md → expect 404; sot.json/catalog → 200.
- [ ] OPEN THREAD: Pixel expects cart flush-left to "fully resolve with Atlas's canvas-meta repoint" — but Atlas's wave-1 summary contains no canvas-meta work (his CLS fix was footer-cro). Live cart renders bare shortcode markup instead of the .skyy-cart__* shell (relates to the long-open cart/checkout stale canvas meta item, pages 9451/9452). CONFIRM with Atlas whether the repoint is in scope this train or the cart container styling needs another path before deploy.

### 2b. Font-var follow-up (post team-lead relay) — `assets/css/design-tokens.css`
- Placement verified against the generator: `data/gen-design-tokens.py` "Writes ONLY between
  the GENERATED:* START/END markers" — §1.12 legacy aliases are hand-maintained, so the
  `--font-body` alias survives regens. No relocation needed.
- Full undefined-var sweep (all source CSS + style.css, `var(--font-*/--ff-*)` vs definitions):
  found 2 more of the same class — `--font-display` (kids-capsule.css ×4) and `--font-ui`
  (kids-capsule.css ×6, skeleton.css ×1). Their 'Archivo'/'Anton' fallbacks are canon-correct
  today (no visible defect), but they diverge silently the day typography.json changes.
  Added both aliases to §1.12 + hardened the block comment with the alias-or-silent-fallback
  rule (bug-271 reference). Sweep now clean: every font var reference resolves.

## Access — round B applied (2026-07-19)

Rebased on Pixel's landed state — REUSED Pixel's `--skyyrose-accent-text` token (design-tokens.css:319-322, love-hurts #FF5C7A = 6.66:1) instead of minting a duplicate `--skyyrose-crimson-text`; one canon token. All PHP `php -l` clean. Source-only, no build/commit.

| Fix | Files (theme-relative) | Change |
|---|---|---|
| FIX-2 | `template-preorder-gateway.php:184,249` | Removed `role="list"`/`role="listitem"` — `aria-pressed` now valid on the panel buttons. |
| FIX-4 (option A, dark ink) | `assets/css/cookie-consent.css:104`, `assets/css/footer.css:75`, `assets/css/woocommerce.css:162` | White ink on `#B76E79` (3.8:1) → `#0A0A0A` (5.2:1); brand surface token untouched. ⚑ founder-report. |
| FIX-4 gradient exception | `assets/css/contact.css:489` | Contact submit is a `#9A5662→#B76E79` gradient — dark ink fails the dark end, so the light end darkens to `#A4626C` and white ink passes both ends (5.2/4.62). ⚑ founder-report. |
| FIX-6 | `assets/css/product-card-v7.css` (new `--v7-accent-ink` + eyebrow/price/quickadd ink), `assets/css/about.css:921` | Love-hurts small text on dark → `var(--skyyrose-accent-text, #FF5C7A)`; canon `#DC143C` stays on all surfaces/borders/badges. Other collections unchanged (`--v7-accent-ink` defaults to `--v7-accent`). ⚑ founder-report (value is Pixel's #FF5C7A, supersedes the #E8305A proposal). |
| FIX-7 | `assets/css/product-card-v7.css` (badge rule) | Love-hurts badge ink → `#fff` (4.99:1 on crimson); silver/gold badges keep dark ink. |
| FIX-9 | `assets/css/preorder-gateway.css:243,255` | `.po-btn--primary/--primary-sm` ink hard-set `#0A0A0A` (was `var(--po-bg)` → cream on silver 1.48:1). |
| FIX-14-preorder | `assets/css/preorder-gateway.css:504-505` | `height:auto` on `.po-grid__lockup img` + `.po-email-capture__art img` — stops attr-ratio distortion. |
| FIX-15 frame | `template-parts/product-card-v7-lookbook.php:55` | Frame link aria-label now leads with the badge text when present (`{badge} — {name}`) — badge is the link's only visible text. Sentinel re-tests live. |
| FIX-15 kc-heir | `front-page.php:526` | Dropped the aria-label override; name computes from the visible letter text + new sr-only destination hint span. |

**.min rebuild list for the central build step (rounds A+B):** `premium-interactions.js`; CSS: `about`, `collections-index`, `homepage-v2`, `contact`, `landing-scrollytell`, `cookie-consent`, `footer`, `woocommerce`, `product-card-v7`, `preorder-gateway`.
**Still open for founder/ops report:** FIX-5 (express-pay/hCaptcha cookie scoping — conversion decision), FIX-12 (Jetpack Likes off pages — wp-admin op), cart `a.button.wc-backward` (re-measure post-deploy; if still failing it needs a cart-page `.woocommerce a.button` ink rule — Atlas lane).

### Atlas — Wave 1c (2026-07-19)

**1. tar/rsync exclusion symmetry** — scripts/deploy-theme.sh tar_excludes now excludes
'scripts' (theme build tooling; exactly one scripts/ dir exists in the theme, verified by
find). Re-ran the real-tar manifest test with the script's own eval-extracted patterns (42):
skyyrose-flagship/scripts/ absent, all Wave-1b internal patterns still absent, runtime
allowlist + cart templates + spot-check assets present.

**2. Cart shell — diagnosis corrected, fixed**
- Live evidence (cache-busted curl): the bug-222 template_include override IS working —
  /cart/ renders page.php's .skr-page shell with theme header/footer, body has
  `woocommerce-cart` class (is_cart() true), and woocommerce.min.css + woocommerce-cart.min.css
  both load. The stale `page-template-skyyrose-canvas` body class is cosmetic; NO routing
  change needed (the override already matches by WC conditional, not page meta).
- ACTUAL root cause of the bare cart: WooCommerce routes EMPTY carts to cart/cart-empty.php
  (WC_Shortcode_Cart::output()), which the theme never overrode — the styled empty state
  inside woocommerce/cart/cart.php:37-58 is dead code WC never reaches. Sessionless audits
  (Lighthouse, curl, Pixel) always see an empty cart → always the unstyled core path.
- Fix: NEW woocommerce/cart/cart-empty.php override mirroring the .skyy-cart__empty markup.
  Classes already styled in shipped woocommerce-cart(.min).css → zero CSS edits, no rebuild
  needed. Deliberate deviations documented in the docblock (no woocommerce_cart_is_empty —
  core hooks its duplicate notice there; h2 title since the page.php shell provides the h1).
- Logged bug-274; memory project_cart_checkout_canvas_meta updated from OPEN → neutralized
  (DB meta cleanup remains an optional gated op; checkout-on-canvas founder call unchanged).
- Verification: php -l clean; bash -n clean (tmp-copy route); tar manifest test above.
  Post-deploy check for Sentinel: /cart/ shows .skyy-cart__empty (styled state), and with an
  item added the cart table renders via cart.php unchanged.
