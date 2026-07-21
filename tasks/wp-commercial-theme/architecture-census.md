# Architecture Census — skyyrose-flagship

Atlas (Theme Architect) · 2026-07-19 · read-only census, no code edits.
Theme version: `SKYYROSE_VERSION = '1.11.1'` (`functions.php:21`). All file refs relative to
`/Users/theceo/DevSkyy/wordpress-theme/skyyrose-flagship/` unless noted. Live claims verified by
cache-busted curls this session.

---

## 1. Template ↔ URL map (20 audit URLs)

Every template calls `get_header()` → **`header.php`** (no `header-shop.php` exists, so
`get_header('shop')` in the WC templates also falls back to `header.php`). Footer chrome for all:
`footer.php` (which pulls `template-parts/footer-cro.php`, `mobile-bottom-nav.php`,
`size-guide-modal.php`, `cookie-consent.php`, `skyy-mascot.php`).

| # | URL | Template | Hero renderer |
|---|-----|----------|---------------|
| 1 | `/` | `front-page.php` (slug `front-page`) | Inline `<section class="hero">` `front-page.php:160-231` — AVIF/WebP `<picture>` LCP, on-model scroll strip (12 imgs), type-rendered `h1.hero-title` |
| 2 | `/shop/` | `woocommerce/archive-product.php` (`get_header('shop')` at `:21`) | No hero section — WC breadcrumb + loop via `woocommerce_before_main_content` hooks |
| 3 | `/collections/` | `page-collections.php` (hierarchy: page slug `collections`; slug `collections-index`, `inc/enqueue.php:516-518`) | Inline `.ci-hero` `page-collections.php:49-52` — **type-rendered h1**, per-collection lockup images used on cards (`:27-35`) |
| 4 | `/collections/black-rose/` | `template-collection-black-rose.php:14-16` → `template-parts/collection/page.php` (slug `collection-standalone`) | `.col-hero` `collection/page.php:79-143` — emblem 220×300 + lockup img (SOT-resolved) + responsive bg srcset 480/768/1280/1680w, `fetchpriority=high`, w/h attrs present |
| 5 | `/collections/love-hurts/` | `template-collection-love-hurts.php` → same part | same |
| 6 | `/collections/signature/` | `template-collection-signature.php` → same part | same |
| 7 | `/collections/kids-capsule/` | `template-collection-kids-capsule.php` → same part; slug becomes `kc-launch` in launch mode (`inc/enqueue.php:532`) | `.col-hero` with **no bg image, h1 title** by design (`collection/page.php:9`, launch mode = 0 cards is intentional) |
| 8 | `/product/the-fannie/` | `woocommerce/single-product.php:18` (`get_header('shop')`) → `template-parts/product-detail-editorial.php` (`:49-50`) | PDP gallery is the LCP; preload via `inc/enqueue-performance.php:175-237` (skipped when Photon active, `:192`) |
| 9 | `/cart/` | **`page.php` forced** by `skyyrose_wc_page_shell_template()` `inc/redirects.php:282-290` (`template_include` prio 20, bug-222 fix — beats stale live-only `skyyrose-canvas.php` meta on pages 9451/9452) | No hero — `.skr-page__header` h1 (`page.php:23-25`) |
| 10 | `/about/` | `template-about.php` (slug `about`) | `template-parts/about/chapter-origin.php` opening chapter |
| 11 | `/contact/` | `template-contact.php` (slug `contact`) | Inline within template (19.3K file) |
| 12 | `/faq/` | `template-faq.php` (slug `faq` → `info-pages.css`) | Inline |
| 13 | `/pre-order/` | `template-preorder-gateway.php` (slug `preorder-gateway`) | `.po-hero` `:86-116` — video + poster `<picture>` 1680×945 `fetchpriority=high` + lockup 600×200 |
| 14 | `/experiences/` | `template-experiences.php` (slug `experiences`) | Full-bleed per-collection SOT heroes (`skyyrose_experiences_hero()` `:54-56`, priority hero→hero_backdrop→scene_portrait) |
| 15 | `/landing-black-rose/` | `template-landing-black-rose.php` (slug `landing`) | `.lp-hero` `:64-120` — lockup AVIF/WebP/PNG 640×160 `fetchpriority=high`; only the KC landing uses `template-parts/landing/hero.php` |
| 16 | `/experience-black-rose/` | `template-immersive-black-rose.php` (slug `immersive`) — **route 301s to `/collections/black-rose/`** per WS3 (docblock `:7-11`); template kept as rollback | `template-parts/immersive/scene.php` (100vh scene, `immersive.css:26`) |
| 17 | `/privacy-policy/` | `page.php` (default, slug `page`) | None — h1 header |
| 18 | `/wishlist/` | `page-wishlist.php` (hierarchy) | None |
| 19 | `/shipping-returns/` | `template-shipping-returns.php` (slug `shipping-returns` → `info-pages.css`) | Inline |
| 20 | 404 probe | `404.php` (slug `404`) | Mascot-image hero, `404.php:190-197` (skyy-canonical.jpeg since bug-094) |

---

## 2. Enqueue map

### Hook pipeline (`wp_enqueue_scripts` priorities)

| Prio | Function | File |
|------|----------|------|
| 5 | `skyyrose_enqueue_local_fonts` (fonts.css) | `inc/enqueue.php:1137` |
| 10 | `skyyrose_enqueue_global_styles` / `_global_scripts` | `inc/enqueue.php:1138-1139` |
| 15 | `skyyrose_localize_scripts` (skyyRoseData) | `inc/enqueue.php:1140` |
| 20 | `skyyrose_enqueue_template_styles` / `_template_scripts` | `inc/enqueue.php:1141-1142` |
| 25 | `skyyrose_enqueue_commercial_polish` (last-CSS specificity layer) | `inc/enqueue-phases.php:331` |
| 30 | Phase 2: performance-guardian (global) + brand-atmosphere (collections) | `inc/enqueue-phases.php:332` |
| 40 | Phase 3: experience-analyzer, smart-showcase, micro-interactions (product-y slugs, `skyyrose_phase3_product_slugs()` `:113-122`) | `inc/enqueue-phases.php:333` |
| 42 | Phase 4: personalization (product slugs + PDP) | `inc/enqueue-phases.php:334` |
| 100/101 | Block-library + Jetpack dequeues | `inc/enqueue-performance.php:362,365` |

Template slug detection: `skyyrose_get_current_template_slug()` `inc/enqueue.php:502-569`.
Adding a template requires TWO edits (`$template_map` `:528-550` + `$template_styles` `:587-610`)
or CSS silently misroutes (theme CLAUDE.md rule).

### Global styles, every page (prio 5-10)

`skyyrose-fonts`, `skyyrose-style` (**style.css, always unminified**, `:51-56`), `skyyrose-main`,
`skyyrose-design-tokens`, `skyyrose-components`, `skyyrose-animations`, `skyyrose-header`,
`skyyrose-footer`, `skyyrose-mobile-nav`, `skyyrose-cookie-consent`, `skyyrose-agency-visuals`.
Conditionally skipped on lightweight slugs (cart/checkout/blog/single/404/search/default/±page/contact):
`animations-premium` (`:105-119`), `size-guide`/`luxury-cursor`/`skeleton` (`:172-206`),
`hero-cinematic` (`:249-263`), mascot pair gated by kill switch + not-checkout (`:211-233`).

### Global scripts, every page

`navigation`, `toast`, `footer-cro`, `page-transitions` (all defer, in_footer);
`motion-one` (65.5KB) + `premium-interactions` skipped on lightweight slugs (`:283-287,340-367`);
mascot loader + localized config gated (`:395-462`). All `skyyrose-*` handles get `defer` via
`skyyrose_defer_scripts` (`inc/enqueue-performance.php:109-134`); jQuery Migrate removed (`:250-260`).

### Template-specific (prio 20)

CSS map `inc/enqueue.php:587-610`; JS map `:966-977`. Notables:
- `collection-standalone` stacks: collection-pages + view-transitions (`inc/enqueue-phases.php:349-364`) + pin-narrative + collection-feature-scroll + **immersive.css + immersive-scenes** (embedded experience, `:664-689`) + product-grid + immersive-core CSS/JS + **GSAP + ScrollTrigger** (`:880-894`) + collection-pages.js + feature-scroll.js + immersive.js + WC bridge (`:1036-1049`) + holo cards.
- GSAP slugs: `preorder-gateway, immersive, kc-launch, collection-standalone` (`:880-883`); ScrollTrigger drops `immersive` (`:891-894`). Lenis only preorder (`:919-927`).
- Holo card CSS+JS on 8 slugs (`:1069-1091`); v7 cards enqueued from `inc/v7-cards.php:159-165`.
- `wc-add-to-cart` force-enqueued on front-page/collection/preorder (`:1062-1065`).
- Luxury-cursor JS on every non-immersive slug incl. mobile where it self-disables (`:800-811`).

### Handles that bypass `$use_min` (unminified in production; .min siblings EXIST on disk)

- `size-guide.css` (3.9K), `luxury-cursor.css` (1.3K), `skeleton.css` (3.3K) — `inc/enqueue.php:179-206`
- `performance-guardian.js` (3.5K, **global every page**) — `inc/enqueue-phases.php:34-47`
- `brand-atmosphere.css/js` (1.3K/7.2K) — `:66-87`; `smart-showcase.css` (8.0K) — `:181-188`;
  `personalization.css/js` (4.3K/7.4K) — `:280-301`

### Live homepage totals (curl, cache-busted, this session)

**40 stylesheets** (25 theme + 15 plugin/mu-plugin), 31 external scripts, HTML 164KB.
Plugin CSS present that theme dequeues fail to catch (handle mismatches vs
`inc/enqueue-performance.php:307-333`): jetpack-podcast episode-block, jetpack-forms-layout,
jetpack-search results-list + filter-wc-attribute, sharing.css, social-logos, masterbar,
wpcom-blocks-code-style, layout-grid, wc-blocks.css, Elementor `frontend.min.css` + `post-13.css`,
Stripe upe-blocks, and the separate **skyyrose-immersive plugin's immersive.css**.
`skyyrose_dequeue_block_styles` (`:272-286`) is skipped whenever the page object's content
`has_blocks()` — true for the front page even though `front-page.php` never calls `the_content()`.

---

## 3. Asset weight inventory

No `.min` >100KB. All 52 CSS + 34 JS sources have `.min` siblings; only mtime drift found was
`design-tokens.min.css` (source 07-16 vs min 07-13) — **content-verified in sync** (declaration-level
diff: identical token names/values, whitespace-only differences). Largest payloads:

| Asset | Bytes | Loads on |
|-------|-------|----------|
| `js/lib/gsap.min.js` | 71,520 | preorder, immersive, kc-launch, collection |
| `js/lib/motion.min.js` | 65,529 | all non-lightweight pages |
| `js/lib/ScrollTrigger.min.js` | 42,667 | preorder, kc-launch, collection |
| `css/homepage-v2.min.css` | 36,263 | homepage |
| `style.css` (unminified, sitewide) | 26,312 | every page |
| `css/immersive.min.css` | 19,258 | immersive + collection |
| `css/contact.min.css` / `about` / `404` / `preorder` | 17-19K | respective pages |
| `js/lib/lenis.min.js` | 17,722 | preorder only |
| Fonts preloaded sitewide | archivo 90,096 + inter 48,432 + hanken 34,664 + anton 12,004 = **185KB** | every page (`inc/enqueue-performance.php:50-72`) |
| `images/homepage-hero-bg.avif/.webp` | 294K / 396K | homepage LCP (preloaded, `inc/enqueue.php:706-728`) |

Collection pages carry BOTH animation stacks: Motion One (global) + GSAP + ScrollTrigger ≈ 180KB of
animation libs before any template JS.

---

## 4. Perf/structural hazard list (ranked)

### P0
1. **Malformed CSS rule shipping live — `style.css:515-522`.** The "Full-bleed hero pages handle
   their own offset" rule has **no opening `{`** (selector list ends in a trailing comma at `:520`,
   then `padding-top: 0;` then `}`). Live-verified byte-identical. The reset is dead, so
   full-bleed pages keep `padding-top: var(--header-height, 72px)` from `:509-512`; depending on
   parser error-recovery the following rule `.homepage-v2 .site-header … { display:none }`
   (`:530-535`) may ALSO be swallowed. Note the contradiction either way: body gets `homepage-v2`
   class on the front page (`inc/template-functions.php:384-387`) while `front-page.php:157` says
   the WP header now handles homepage navigation — if `:530-535` ever applies, the homepage has NO
   header. Needs Pixel/Sentinel computed-style verification, then a source fix. `style.css` is
   served raw (no .min), so the syntax error is not build-masked.
2. **Duplicate mobile bottom nav on every page — `footer.php:253` AND `footer.php:260`.**
   Both `get_template_part('template-parts/mobile-bottom-nav')` calls survive; live pages render
   **two `<nav class="mobile-nav">`** (verified 2× on `/about/` and `/collections/black-rose/`).
   Two stacked `position:fixed` bars, duplicate landmark (Lighthouse a11y: landmark-unique /
   identical nav labels), and the second renders after `</footer>` outside `#page` — regressing the
   exact WS4 acceptance bug-185 fixed (its fix added the inside-footer copy at `:253` but never
   removed `:260`).

### P1
3. **Dead render-blocking hero CSS sitewide — `hero-cinematic(.min).css`.** Enqueued in `<head>` on
   all non-lightweight templates (`inc/enqueue.php:249-263`) but `template-parts/hero-cinematic.php`
   has **zero callers** (grep: only enqueue.php + the part itself reference it; no
   `get_template_part` anywhere). Every page pays for CSS whose markup never renders.
4. **Wasted sitewide font preload — Inter.** `inter-latin.woff2` (48.4KB) preloaded on every page
   (`inc/enqueue-performance.php:53`) but Inter is a primary face only in `404.css`
   (`var(--ff-system)`); everywhere else it is a fallback behind Hanken Grotesk
   (`design-tokens.css` `--skyyrose-font-body`). Forced 48KB fetch + "preloaded but not used"
   console warning on ~every page. Anton preload (`:56`) similarly needs per-page verification.
5. **40-stylesheet homepage; theme Jetpack/plugin dequeues miss their targets.** The handles
   dequeued at `inc/enqueue-performance.php:307-333` (`jetpack-podcast-player`, `grunion-front-end`,
   `jetpack-forms`, `jetpack-search-widget`…) do not match what actually loads (see §2 live list).
   Elementor frontend CSS + `post-13.css` load on the PHP-rendered front page; `wc-blocks.css` and
   `global-styles` survive because `has_blocks()` is true on unrendered page content (`:272-286`).
6. **Homepage image payload.** 294KB AVIF hero (preloaded, square 1920×1920 attrs with CSS crop —
   intentional per `front-page.php:178-181`) plus a 12-image on-model hero strip at 1024×1536
   (2 eager, 10 lazy, `front-page.php:196-215`). LCP + bandwidth budget dominated by decoration.

### P2
7. **Nine handles serve unminified sources in production** despite existing `.min` siblings
   (~40KB raw total; list + refs in §2). `performance-guardian.js` is global.
8. **Double animation library on collection pages** (Motion One + GSAP + ScrollTrigger ≈ 180KB,
   §3) — collection-standalone is also the heaviest CSS stack (12+ theme sheets incl. two
   immersive sheets for the embedded experience layer).
9. **`style.css` 26.3KB always unminified** (`get_stylesheet_uri`, `inc/enqueue.php:51-56`) —
   candidate for trimming/splitting; it still contains the pre-2026-07-01 homepage-header-hide
   block (`:524-535`) whose intent is now contradicted (see P0-1).
10. **Touch devices download desktop-only luxury-cursor JS+CSS** (`inc/enqueue.php:189-196,
    800-811`) — small (3.9K) but pure waste on mobile Lighthouse runs.

### P3
11. `--header-height` fallback mismatch: `style.css:511,1064` fall back to 72px; token is 80px
    (`design-tokens.css:64`, matching `.navbar` height `header.css:36`). Only bites if tokens fail.
12. `style.css:518-520` full-bleed selector list omits `template-immersive-kids-capsule` (3 of 4
    immersive templates listed) — moot while the rule is malformed, must be fixed together.
13. Pacifico + Kaushan still declared in `fonts.css:116-131` and **used by `experiences.css`**
    despite the 2026-07-11 bespoke-script replacement (typography canon). Brand-canon drift for
    Pixel; fonts only download where rendered, so perf impact limited to `/experiences/`.
14. Inline output: homepage inlines its template JS raw into `<script>` (`front-page.php:672-681`,
    ~4.5KB min) + JSON-LD block (`:635`); `header.php`/`scene.php` carry small inline
    `<style>`/`<noscript>` blocks. Acceptable sizes, but CSP + audit surface.
15. PDP module-script history: bug-176 (three.js bare-specifier ×4 on live PDP) logged OPEN;
    bug-189 later resolved the same error class via jsdelivr `/+esm`. No `importmap`/`type=module`
    emitters remain in inc/ or woocommerce/ templates (grep clean) — Sentinel should confirm PDP
    console is clean and bug-176 can be closed.

---

## 5. Header / hero structural notes

**Header (`header.php`):**
- `.navbar` inside `#masthead.site-header`; **`position:fixed; top:0; z-index:1000`**
  (`header.css:6-8`), container height **80px → 56px when `.scrolled`** (`header.css:36-41`).
- **No admin-bar offset rule anywhere** (`grep admin-bar` in theme CSS: 0 layout hits) — logged-in
  founder view has the WP admin bar overlapping the fixed navbar. Not a Lighthouse item (logged-out)
  but worth one rule.
- Offset compensation: `.site-content { padding-top: var(--header-height, 72px) }`
  (`style.css:509-512`); full-bleed pages rely on the **broken** reset (P0-1). Homepage `.hero`
  additionally self-pads 80px (`homepage-v2.css:121`) — if the reset were working this is correct;
  with it broken, expect double offset.
- Optional announcement bar renders above navbar when the theme_mod is set (`header.php:29-46`) —
  fixed-header math does not account for its height.
- Center brand = rotating webm `<video>` 60×44 with static poster + webp fallback, w/h attrs set,
  `fetchpriority=low` (`header.php:79-108`) — CLS-safe.
- Single-menu shell: one server-rendered menu; `navigation.js` relocates it into the mobile drawer
  ≤1024px; `<noscript>` fallback keeps it visible (`header.php:136-142`). Search overlay + mobile
  menu use `inert` + `aria-hidden` correctly (`:155,174-179`).

**Heroes by family:**
- **Homepage**: inline; `<picture>` AVIF/WebP, `fetchpriority=high`, w/h attrs (CLS-guarded);
  `min-height:100vh/100dvh` (`homepage-v2.css:122-124`); type-rendered `h1` "SkyyRose" (homepage is
  brand-name, not a collection lockup — canon-consistent).
- **Collection** (`collection/page.php:79-143`): lockup IMAGE as title with `h1.screen-reader-text`
  companion (`:119-122`) — canon-correct; emblem + lockup + bg all carry explicit w/h; bg has
  responsive srcset `sizes=100vw`; BR gets scroll-timeline bloom (`:112-118`). KC: no bg, real h1.
- **Landing** (`template-landing-*.php`): lockup `<picture>` AVIF/WebP/PNG 640×160
  `fetchpriority=high`; KC landing alone uses `template-parts/landing/hero.php`.
- **Preorder** (`:86-116`): video hero + poster 1680×945 + lockup 600×200, eager+high.
- **Immersive** (`immersive/scene.php`): 100vh scene (`immersive.css:26,901-902`), loader part,
  lockup reveal has `<noscript>` guard (`scene.php:273`). Reveal-animation classes on hero children
  have a history of stuck-invisible states — bug-225/226/228 all in this territory.
- **Shop/PDP**: no hero; PDP LCP = gallery image, preload logic Photon-aware
  (`inc/enqueue-performance.php:178-209`); editorial layout part `product-detail-editorial.php`.
- **404**: mascot image hero (`404.php:190-197`).
- **Cart/checkout/legal**: `page.php` h1 header only; cart/checkout shell restored via
  `template_include` (bug-222) — canvas-meta cleanup on pages 9451/9452 still pending upstream
  (memory: `project_cart_checkout_canvas_meta` OPEN).

**Lockup vs type-rendered summary:** collection + landing + preorder + immersive = lockup images
(canon-correct). Homepage h1 + `/collections/` index h1 + KC = type-rendered (first two arguably
fine — brand name / hub title; Pixel to rule).

---

## 6. Known constraints

- **Production serves `.min`** (`$use_min = ! SCRIPT_DEBUG`, e.g. `inc/enqueue.php:48`). Every
  CSS/JS edit requires `npm run build` from `wordpress-theme/` (package.json lives in the PARENT,
  not the theme dir); verify BOTH source and `.min`. Exceptions that dodge the rule today: the nine
  raw-served handles (§2) and `style.css` itself.
- **Version**: `SKYYROSE_VERSION = '1.11.1'` (`functions.php:21`) — also the cache-buster on every
  handle, the mascot GLB, and hub image URLs. Bump with targeted edits only (bug-248: blanket sed
  corrupted readme.txt changelog).
- **17 gitignored live riders** (BR/LH emblems, mascot png, avatar refs, scene backdrops,
  `inc/brand.generated.php` behavior-adjacent): theme deploy is an atomic hot-swap — deploying from
  a clean tree DELETES them (bug-252; manifest in `docs/engineering-learnings.md`). Deploy only from
  the main checkout.
- **WP.com quirks**: `CONCATENATE_SCRIPTS=false` is intentional (`functions.php:50-53`, MIME
  errors — don't "fix"); REST via `index.php?rest_route=`; Batcache serves stale — always
  cache-bust verification curls; WebFetch strips `<script>` (never use it for JSON-LD/OG checks).
- **Kill switches**: `SKYYROSE_COMING_SOON_MODE` (`functions.php:39-41`, false);
  mascot Customizer kill switch — a stored DB `false` overrides code default
  (`skyyrose_mascot_is_enabled`, `inc/mascot-config.php`).
- **Live-only state**: `skyyrose-canvas.php` exists only on the server (stale `_wp_page_template`
  meta on cart/checkout, neutralized by the `template_include` filter); Experience Engine phase
  modules are admin-toggleable (`skyyrose_see_is_module_active`), so live enqueue sets can differ
  from static analysis — Lighthouse runs are the ground truth for what actually loads.
- **Shared worktree**: new commits only, no `--amend`/`reset` (team charter).
