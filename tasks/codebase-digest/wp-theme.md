# WordPress Theme Digest — `wordpress-theme/skyyrose-flagship/`

**Theme:** SkyyRose | **Version:** 1.1.0 (`SKYYROSE_VERSION` in code; CLAUDE.md says 1.0.0 — code is authoritative)  
**PHP:** 8.2+ | **WP:** 6.8+ | **WC:** 9.9+ | **Text Domain:** `skyyrose`  
**Production URL:** https://skyyrose.co (WordPress.com Business plan, SFTP deploy only)

---

## 1. Theme Architecture

### Entry Points & Dependency Flow

```
functions.php
  ├── Defines: SKYYROSE_VERSION='1.1.0', SKYYROSE_THEME_DIR, SKYYROSE_ASSETS_URI
  ├── $skyyrose_core_includes[] array → ordered include_once for all inc/*.php modules
  ├── Builder bootstrap order (MANDATORY): detection.php → shared.php → elementor.php / divi.php / beaver-builder.php / bricks.php
  └── All hooks registered inside included files (functions.php has no hook logic directly)
```

**Module dependency chain:**
```
inc/security.php         (priority 1 — CSP, DISALLOW_FILE_EDIT)
inc/performance.php      (blocks Google Fonts at load time)
inc/enqueue.php          (orchestrates all CSS/JS loading — the hub)
inc/theme-setup.php      (nav menus, image sizes, WC HPOS compat)
inc/brand-colors.php     (12-key color map, skyyrose_brand_colors())
inc/brand.generated.php  (AUTO-GENERATED from brand.yaml — do not edit)
inc/collections-config.php (4-collection metadata)
inc/product-catalog.php  (CSV loader, 2-tier cache)
inc/product-catalog-display.php (resolver, static card shape, featured products)
inc/wc-product-functions.php (skyyrose_current_wc_product, per-product helpers)
inc/template-functions.php (SVG kses, body classes, nav fallback, social links)
inc/seo.php              (Schema.org, OG, Twitter Cards, Yoast deference)
inc/woocommerce.php      (WC hooks, cart fragments, $150 free-shipping threshold)
inc/ajax-handlers.php    (6 AJAX endpoints)
inc/experience-engine.php (6 SEE modules, wp_skyyrose_analytics table)
inc/personalization.php   (visitor hash cookie, SkyyCurated localization)
inc/builders/detection.php → shared.php → elementor.php / divi.php / beaver-builder.php / bricks.php
```

### PHP/CSS/JS Composition

**PHP:** Classic WP theme (not FSE/block). Templates call `get_header()` / `get_footer()` and delegate sections to `template-parts/`. Exception: `front-page.php` uses an inline footer (`.ft` class) + `wp_footer()` instead of `get_footer()`.

**CSS Architecture:**
- `design-tokens.css` — globally enqueued at priority 10. Single source of truth for all CSS custom properties. Per-collection palette via `[data-collection="<slug>"]` attribute blocks.
- `system/animations-premium.css` — globally enqueued. Defines all `.rv-*`, `.btn-*`, `.magnetic`, `.stagger-grid`, `.parallax-*` classes. JS sets CSS custom properties; CSS drives transitions.
- Feature CSS files are conditionally loaded per template slug via `skyyrose_get_current_template_slug()`.

**JS Architecture:**
- `navigation.js` — globally enqueued. Header scroll state, mobile menu, search overlay, dropdowns, smooth scroll.
- `premium-interactions.js` — globally enqueued. Unified IntersectionObserver for ALL reveal classes across the entire theme. Single source of truth for `revealSelectors`. Motion One + IntersectionObserver fallback.
- `toast.js` — globally enqueued. `window.skyyToast(msg, type, duration)`.
- `luxury-cursor.js` — globally enqueued (desktop only). Dot + ring follower, LERP 0.15.
- Page-specific JS is enqueued conditionally: `homepage-v2.js`, `collection-pages.js`, `landing-pages.js`, `immersive.js`, `immersive-wc-bridge.js`, `preorder-gateway.js`, `single-product.js`, `woocommerce.js`.

**Key constants:**
- `SKYYROSE_FREE_SHIPPING_THRESHOLD = 150` (USD)
- `SKYYROSE_SETUP_VERSION = '4.0.0'` (theme activation flag)
- `SKYYROSE_SEE_VERSION = '1.0.0'` (Experience Engine)

---

## 2. Page Template Inventory

| File | Slug | Purpose |
|------|------|---------|
| `front-page.php` | `front-page` | V6 Editorial Homepage. Grain canvas, collection split, specimen ticker, press section (5 real outlets), featured product grid. Has own inline footer. |
| `template-collection-black-rose.php` | `collection-black-rose` | 3-line wrapper → `template-parts/collection/page.php` with `slug=black-rose` |
| `template-collection-love-hurts.php` | `collection-love-hurts` | Same pattern, `slug=love-hurts` |
| `template-collection-signature.php` | `collection-signature` | Same pattern, `slug=signature` |
| `template-collection-kids-capsule.php` | `collection-kids-capsule` | Same pattern, `slug=kids-capsule`. Kids-specific: no hero bg, h1 title instead of logo, pre-order URLs, dynamic product count, `show_on_front: false`. |
| `template-landing-black-rose.php` | `landing` | `<div class="lp" data-collection="black-rose">`. Delegates to template-parts/landing/ partials. |
| `template-landing-love-hurts.php` | `landing` | Same, `data-collection="love-hurts"` |
| `template-landing-signature.php` | `landing` | Same, `data-collection="signature"` |
| `template-immersive-black-rose.php` | `immersive` | 2D hotspot scene engine (NOT Three.js). Two rooms (Moonlit Courtyard + second). Uses `skyyrose_immersive_product()`. |
| `template-immersive-love-hurts.php` | `immersive` | Same pattern |
| `template-immersive-signature.php` | `immersive` | Same pattern |
| `template-immersive-kids-capsule.php` | `immersive` | Same pattern |
| `template-preorder-gateway.php` | `preorder-gateway` | 4-collection selector grid. GSAP animations. Products via `skyyrose_get_collection_products()`. |
| `template-about.php` | `about` | `abt-*` BEM classes. Founder story, timeline, collections grid. |
| `template-elementor-canvas.php` | `elementor-canvas` | Builder canvas (no header/footer) |
| `template-elementor-fullwidth.php` | `elementor-fullwidth` | Builder fullwidth (with header/footer) |
| Standard WP templates | — | `page.php`, `single.php`, `archive.php`, `404.php`, `search.php`, `index.php` |

**Routing:** WP template hierarchy. Slug-based detection in `enqueue.php` for conditional asset loading.

---

## 3. Includes (`inc/`) — Module Reference

### Core Modules

| File | Since | Key Responsibility |
|------|-------|--------------------|
| `enqueue.php` (1166L) | 1.0.0 | All CSS/JS loading. 4-phase priority system (5/10/15/20/30/40/42/65). `skyyrose_get_current_template_slug()` static-cached dispatcher. Template slug map. `skyyrose3D` JS config. |
| `theme-setup.php` | 1.0.0 | 5 nav menu locations, custom image sizes, WC HPOS compat, Jetpack optimization disabling |
| `security.php` | 1.0.0 | CSP headers, rate limiting by email-hash MD5 (not IP — WP.com proxy), `DISALLOW_FILE_EDIT`, `CONCATENATE_SCRIPTS=false` |
| `performance.php` | 1.0.0 | AVIF MIME, Google Fonts dequeue priority 999, nosniff header, WC style dequeue |
| `enqueue-performance.php` | 1.0.0 | WC style dequeue, font preloads, script defer by prefix, SRI hashes (GSAP CDN only), jQuery Migrate removal |
| `brand-colors.php` | 1.0.0 | 12 color keys: rose_gold, gold, crimson, silver, dark, deep_black, deep_red, purple, navy, deep_blue, soft_pink, lavender. `skyyrose_brand_colors()`, `skyyrose_hex_to_rgba()` |
| `brand.generated.php` | — | AUTO-GENERATED from `assets/brand/brand.yaml` via `scripts/sync_brand_to_php.py`. `SKYYROSE_LEGAL_NAME`, `SKYYROSE_BRAND_TAGLINE`, `skyyrose_brand_collections()`, `skyyrose_social_handles()`, `skyyrose_json_ld_organization()`. Do not edit directly. |
| `collections-config.php` | 1.0.0 | 4 collection configs. Kids-capsule: `show_on_front: false`. |
| `template-functions.php` | 1.0.0 | `skyyrose_svg_kses()`, collection colors, breadcrumbs, body classes, social links, `skyyrose_nav_fallback()` |
| `seo.php` | 1.0.0 | Product/Organization/WebSite/BreadcrumbList/CollectionPage Schema.org, OG, Twitter Cards. Defers to Yoast if active. |
| `customizer.php` | 1.0.0 | 3 customizer sections: Brand Identity (primary color, gold accent, dark bg, brand logo), Social Media (7 networks + twitter handle + contact info), Kids Capsule Launch (`skyyrose_kc_mode` radio). CSS output via `wp_add_inline_style('skyyrose-design-tokens', ...)`. |
| `patterns.php` | 1.0.0 | 3 block pattern categories. `skyyrose_get_pattern($slug)` loads PHP files via ob_start with sanitize_file_name guard. |
| `redirects.php` | 6.7.0 | Canonical collection URL redirects (`/collections/{slug}/` → `/collection-{slug}/` 301). `/preorder/` → `/pre-order/` (canonical, template_redirect priority 1). |
| `accessibility-fix.php` | — | `SkyyRose_Accessibility_Fix` class: ob_start on template_redirect, 9 DOM transforms (regex on output buffer). Legacy `/preorder/` redirect also here — superseded by redirects.php. |
| `accessibility-seo.php` | — | accessibility.css/js enqueue. ARIA nav labels, role="menuitem", ARIA live regions. WC add-to-cart aria-labels. Admin WCAG checklist page. |
| `menu-setup.php` | 3.2.0 | Creates 6 nav menus (primary, footer, footer-legal, mobile, collection, experiences). Experience menu names: The Garden (BR), The Ballroom (LH), The Runway (SIG). Versioned flag `skyyrose_menus_setup_v620`. |
| `theme-activation-setup.php` | 4.0.0 | 13 required pages, reading/WC settings, tagline, permalink structure, timezone. `SKYYROSE_SETUP_VERSION='4.0.0'`. |

### Product & Catalog

| File | Since | Key Responsibility |
|------|-------|--------------------|
| `product-catalog.php` | 1.0.0 | CSV loader (`data/skyyrose-catalog.csv`). 2-tier cache: WP object cache + static `$catalog`. Helpers: `skyyrose_get_product_catalog()`, `skyyrose_get_product($sku)`, `skyyrose_get_collection_products($slug)`, `skyyrose_normalize_sku()`, `skyyrose_format_price()`, `skyyrose_product_image_uri()`, `skyyrose_product_url()`. |
| `product-catalog-display.php` | 6.5.1 | `skyyrose_catalog_to_static_card(array $cat)` — canonical static card shape. `skyyrose_resolve_display_products()` — WC-first/catalog-fallback resolver. `skyyrose_get_featured_display_products($limit=8)` — 2-tier cache (static + 5-min transient). Default curated SKUs: sg-015, br-004, br-008, lh-004, sg-006, br-010, sg-013, kids-001. `skyyrose_featured_product_skus` filter for override. Cache invalidated on product save/update/trash/delete. |
| `wc-product-functions.php` | 6.7.0 | `skyyrose_current_wc_product($post_id=null)` — canonical safe WC_Product resolver (extracted v6.7.0 to fix fatal on single-product pages). `skyyrose_get_product_collection()`, `skyyrose_collection_config()`, `skyyrose_localize_product_data()`. |
| `product-taxonomy.php` | 3.1.0 | Fallback `skyyrose_product_tag` taxonomy when WC not active. Creates parent "Shop" + 4 child collection categories, 17 product tags. |
| `collection-content.php` | 6.5.0 | `skyyrose_get_collection_content($slug)` — single source of truth for all per-collection copy (hero_badge, story, features, cta, newsletter) for all 4 collections. |
| `immersive-product-adapter.php` | 3.2.2 / 6.5.1 | `skyyrose_immersive_product($sku, $scene)` — strips variant suffixes. Returns RAW strings — templates must escape at output. |
| `immersive-ajax.php` | — | 3 AJAX handlers: get_product_by_sku, get_collection_products (4-slug allowlist), immersive_add_to_cart (rate limit 30/min, SKU variant stripping, WC_Data_Store variation matching). |

### WooCommerce

| File | Since | Key Responsibility |
|------|-------|--------------------|
| `woocommerce.php` | 1.0.0 | `SKYYROSE_FREE_SHIPPING_THRESHOLD=150`. Cart fragments for AJAX count update. `_product_3d_model` meta field. WC gallery/breadcrumb hooks. |
| `woocommerce-preorder.php` | — | Pre-order meta box (5 fields: is_preorder, date, edition_size, msrp, referral_credit). Button text filter. Price override. Referral credit on `order_status_completed`. |
| `woocommerce-kids-capsule.php` | 6.5.0 | `_kc_age_range` (6 options: 2t-3t, 4t-5t, 4-6, 7-10, 11-14, 14-16), `_kc_matching_adult_id`, `_kc_drop_number`. |
| `wishlist-functions.php` | 1.0.0 | Dual storage: logged-in=wp_options, guest=WC session transient 30d. 50-item cap. 5 AJAX handlers using `skyyrose-wishlist-nonce`. nopriv move_to_cart returns `require_login: true`. `move_all_to_cart` rate-limited 3/min. 4 REST endpoints (auth-required). Wishlist button hook removed v6.2.0. |

### APIs & Integrations

| File | Since | Key Responsibility |
|------|-------|--------------------|
| `ajax-handlers.php` | 1.0.0 | 6 AJAX: contact form, newsletter subscribe (Klaviyo), early-access incentive, sign-in, referral claim, mascot chat. |
| `klaviyo-integration.php` | — | API v3, revision 2024-02-15. Bulk-subscription-job pattern. Rate limit: 5 requests/15min per email MD5. REST: GET `/skyyrose/v1/stock/{sku}`. Klaviyo JS injected in `<head>` priority 5. |
| `fastapi-client.php` | 6.5.0 | URL resolution priority: WP option > SEE_FASTAPI_URL env > DEVSKYY_API_URL env > localhost:8000. SSRF protection (blocks 169.254.169.254, private IPs; allows 127.x only in local). 5-min availability transient cache. `non_blocking` mode: 1s timeout. |
| `facebook-sdk.php` | 3.10.0 / 6.6.0 | Pixel consent-gated behind `localStorage('skyyrose_cookie_consent')==='accepted'` or `skyyrose:consent:accepted` custom event. ViewContent on PDP, InitiateCheckout on checkout, AddToCart via delegated listener. |
| `rest-api-experience.php` | — | 6 REST routes. POST /analytics/events (max 50, rate-limited 10/min). GET /personalization/{hash}. Admin: GET/PUT /settings (7 whitelisted keys), GET /analytics/summary, POST /settings/narrative. |
| `rest-kids-capsule.php` | 6.5.0 | GET `/skyyrose/v1/kids-capsule/matching-set/{id}`. Returns `{kids, adult}` pair. |

### Experience Engine (SEE)

`inc/experience-engine.php` — `SKYYROSE_SEE_VERSION='1.0.0'`. 6 modules: analytics-beacon, personalization, real-time-signals, session-intelligence, recommendation-engine, conversion-optimizer. Creates `wp_skyyrose_analytics` DB table via dbDelta. `inc/experience-analyzer.php` — upsert pattern, 5-query summary, 90-day cleanup cron. `inc/admin-experience-dashboard.php` — admin UI with module toggles, analytics stats, narrative form (all via REST `/?rest_route=/skyyrose/v1`).

### Personalization

`inc/personalization.php` — `skyyrose_see_get_visitor_hash()` creates `skyy_visitor` cookie (16-64 hex, httponly=false, 90-day, samesite=Lax). `SkyyCurated` JS localization at priority 45.

### Builders

| File | Key Responsibility |
|------|--------------------|
| `inc/builders/detection.php` | `skyyrose_active_builder()` — static-cached, returns slug. `skyyrose_builder_owns_template()`. Detection order: elementor → divi → beaver-builder → bricks → gutenberg. |
| `inc/builders/shared.php` | `skyyrose_register_builder_compat(string $slug, array $config)`. Config keys: theme_support, palette_hook+palette_callback, palette_priority (default 10), post_setup. |
| `inc/builders/elementor.php` | 8 widgets: three-viewer, product-card, collection-hero, featured-product, lookbook, newsletter, testimonials, preorder-cta. Categories: skyyrose, skyyrose-3d. Breakpoints: mobile=768, tablet=1024. |
| `inc/builders/elementor-compat.php` | Since 6.5.0. 'skyyrose-editorial' category. 16 scroll-reveal/animation CSS classes. Collection palette meta box (signature/black-rose/love-hurts only — kids-capsule excluded). |
| `inc/builders/divi.php` | ET_BUILDER_VERSION guard. Allows `model-viewer` in `et_pb_allowed_tags`. |
| `inc/builders/beaver-builder.php` | FLBuilderLoader guard. Registers header/footer/parts locations via FLThemeBuilderLayoutData. |
| `inc/builders/bricks.php` | BRICKS_VERSION guard. `bricks/setup/default_globals` hook. No theme_support (Bricks reads theme.json natively). |

---

## 4. WooCommerce Integration

**Template overrides (5 files):**
- `woocommerce/archive-product.php` — Standard WC archive. Calls `wc_get_template_part('content', 'product')` which routes to:
- `woocommerce/content-product.php` — Thin bridge: checks `$product->is_visible()`, then calls `get_template_part('template-parts/product-card-holo', null, array('product' => $product))` inside a `<li>`. This is the WC product loop card.
- `woocommerce/single-product.php` — Full custom PDP. Two-column layout: gallery (techflat-first via `$catalog_entry['image']` → WC attachment fallback) + info (collection label, title, price, specs, WC ATC via `woocommerce_template_single_add_to_cart()`).
- `woocommerce/cart/` — Cart overrides (mini-cart)
- `woocommerce/checkout/` — Checkout overrides

**WC hook patterns:**
- `woocommerce_before_shop_loop` / `woocommerce_after_shop_loop` — standard WC hooks used
- `woocommerce_product_get_image` — not overridden; gallery managed via template override
- Cart fragments updated via AJAX for mini-cart count
- Pre-order: custom meta box + button text filter + price override in `woocommerce-preorder.php`
- Kids Capsule: 3 custom meta fields in `woocommerce-kids-capsule.php`

**`skyyrose_current_wc_product()` (canonical safe resolver):**
```
$post_id → global $product if matches → wc_get_product($post_id) → get_queried_object_id() fallback
```
Extracted to `wc-product-functions.php` v6.7.0 to fix fatal on single-product pages.

**REST API pattern:** `/?rest_route=/skyyrose/v1/...` (not `/wp-json/`) for WordPress.com compat.

---

## 5. Asset Pipeline

### `enqueue.php` — 4-Phase Load System

**Phase 1 (priority 5):** Klaviyo JS, SRI hashes on GSAP CDN scripts.

**Phase 2 (priority 10 — global foundation):**
- `skyyrose-design-tokens` (design-tokens.css) — globally always
- `skyyrose-global` (global.css)
- `skyyrose-premium-animations` (system/animations-premium.css)
- `skyyrose-navigation` (navigation.js)
- `skyyrose-premium-interactions` (premium-interactions.js)
- `skyyrose-toast` (toast.js)
- `skyyrose-luxury-cursor` (luxury-cursor.js)

**Phase 3 (priority 15 — page-specific, via slug dispatcher):**
- `skyyrose_get_current_template_slug()` — static-cached, reads template file basename. Maps slugs:
  - `front-page` → homepage-v2.css + homepage-v2.js + product-card-holo.css/js
  - `collection-*` → collection-pages.css + collection-pages.js + product-card-holo.css/js
  - `landing` → landing-pages.css + landing-pages.js + product-card-holo.css/js
  - `immersive` → immersive.css + immersive.js + immersive-wc-bridge.js
  - `preorder-gateway` → preorder-gateway.css + GSAP CDN + preorder-gateway.js
  - `about` → about.css + about.js
  - `single` / `product` → single-product.css + single-product.js + woocommerce.js
  - `search` → search.css (before blog catch-all — order matters)

**Phase 4 (priority 20–65):** WC scripts, personalization, performance-guardian.

**Version bumping:** All enqueued assets use `?v=SKYYROSE_VERSION`. Image URLs use `?v=SKYYROSE_VERSION` cache-busting in templates.

**SRI hashes:** Only on GSAP CDN scripts. Three.js CDN has no SRI.

**Google Fonts blocked at 3 levels:** Elementor filter, priority-999 dequeue loop, DNS prefetch removal.

**JS localization objects:**
- `skyyrose_homepage` — ajax_url, newsletter_nonce, cart_url
- `skyyrose3D` — config object for Three.js experiences
- `skyyRoseWishlist` — ajaxUrl, nonce, i18n
- `skyyRoseNewsletter` — ajaxUrl, nonce
- `skyyRoseImmersive` — ajaxUrl, nonce
- `SkyyCurated` — personalization data (priority 45)
- `SkyyPerformanceBudget` — perf config from performance-guardian.php

---

## 6. Three.js / Experiences Layer

### Critical Discovery: Three.js 3D is NOT active on immersive templates

**What immersive templates actually are:** 2D scene engine with hotspot images. `template-immersive-*.php` files use `.immersive-scene` / `.scene-layer` / `.hotspot` / `.product-panel` markup. JS handler: `immersive.js` — handles hotspot clicks, product panel slide-up, multi-room transitions (layers array), keyboard nav, touch/swipe.

**`immersive.js`:** DOM-based scene. Reads `.scene-layer` (multiple "rooms"), `.hotspot` elements (product data via attributes), `.product-panel` (slide-up drawer). Product data passed to immersive panel via `immersive.js:openPanel()` which sets `panel.dataset.currentProductId` and `panel.dataset.currentProductSku`. WC bridge (`immersive-wc-bridge.js`) reads these for AJAX add-to-cart.

**`assets/js/experiences/` — Three.js files exist but may not be activated:**
- `experience-base.js` — `SkyyRoseExperience` class. Three.js r160+. PBR materials, WebGL renderer, ACES filmic tonemapping, post-processing, particles, raycaster for interactive objects, reduced-motion support. Constructor requires `document.getElementById(containerId)` — if the container `#*-experience` doesn't exist, it throws.
- `blackrose-experience.js`, `lovehurts-experience.js`, `signature-experience.js` — per-world subclasses (757L, 696L, 521L respectively).
- `init-3d.js` — Bootstrap. Per prior session observation (claude-mem #2131): no PHP template emits `id="*-experience"` — Three.js 3D system has no activating container anywhere in the codebase. These files are effectively dead code on current branch.

**`assets/js/skyy-3d.js`:** Loads `assets/models/skyy.glb`. Expects Mixamo-named `idle` + `walk` clips. 6 static model variants (skyy.glb 32MB etc.), all with 0 bones/animations.

---

## 7. Holo Card System

### Template: `template-parts/product-card-holo.php` (93L)

**Dual input contract:**
- `$args['product']` = WC_Product → WC-first data resolution
- `$args['title'/'price'/'sku'/'image_url'/'image_back'/'collection']` = static card (catalog fallback)

**Card structure (BEM `.holo`):**
```
.holo
  .holo__body
    .holo__gallery               (aspect-ratio: 3/4)
      .holo__img--front          (product photo, opacity 1)
      .holo__img--back           (techflat, grayscale/blueprint look, opacity 0 → 1 on hover)
      .holo__badge               (soldout / preorder / new-arrival)
    .holo__info
      .holo__collection          (Space Mono, 10px, tracking 4px)
      .holo__name → <a>          (Cinzel, tracking 2px)
      .holo__price-row
    .holo__drawer                (translateY(100%) → 0 on hover, blur backdrop)
      .holo__sizes
        .holo__size-pill         (plain <span>, no a11y roles on current branch)
      .holo__buy                 (data-product-id contract: <= 0 → disabled)
```

**`.holo__buy` button:** `data-product-id` is the WC activation contract. `product_id <= 0` disables the button (catalog-only fallback, no WC product found). `woocommerce.js` reads this attribute for AJAX add-to-cart.

**JS (`product-card-holo.js` IIFE):**
- `initEntrance()` — IntersectionObserver: threshold 0.05, rootMargin 50px bottom, stagger 80ms delay per card
- `initTilt()` — magnetic tilt up to MAX_TILT=8°, skipped on touch/reduced-motion, cached bounding rect on mouseenter

**CSS (`product-card-holo.css`):**
- Front image: product photo (opacity 1). Back: techflat (grayscale+contrast, opacity 0 → hover swap)
- Drawer: `position: absolute; bottom: 0; translateY(100%) → translateY(0)` on hover
- `.holo:hover`: `translateY(-4px)`, rose-gold border

**Grid containers:** Only `.product-grid`, `.product-grid__items`, `.br-product-grid__items` should be `display: grid`. Holo card itself is a flex column.

---

## 8. Builder Integrations

**Detection pattern (`skyyrose_active_builder()`):**
- Static-cached, called once per request
- Order: `did_action('elementor/loaded')` → `defined('ET_BUILDER_VERSION')` → `class_exists('FLBuilderLoader')` → `defined('BRICKS_VERSION')` → fallback 'gutenberg'
- `skyyrose_builder_owns_template()` → checks if active builder manages the current template

**Shared scaffold (`skyyrose_register_builder_compat()`):**
- `theme_support` — array of WP `add_theme_support()` calls
- `palette_hook` + `palette_callback` — builder-specific palette registration hook
- `palette_priority` — default 10
- `post_setup` — additional callback after registration

**Elementor (richest integration):**
- 8 custom widgets in `elementor/widgets/*.php`
- Custom categories: `skyyrose`, `skyyrose-3d`
- Breakpoints: mobile=768, tablet=1024
- Google Fonts disabled via Elementor's own filter
- `design-tokens.css` enqueued via Elementor frontend conditional (allowed exception to global-only rule)
- Builder-compat also registers 'skyyrose-editorial' category + 16 reveal CSS classes
- Collection palette meta box (signature/black-rose/love-hurts; kids-capsule excluded)

**Divi:** Minimal — adds `model-viewer` to allowed tags.

**Beaver Builder:** Registers header/footer/parts theme builder locations.

**Bricks:** No `theme_support` (Bricks reads `theme.json` natively).

**`design-tokens.css` enqueue rule:** Globally by `inc/enqueue.php:71-76` only. Per-builder duplicates are forbidden. Only exception: Elementor-conditional enqueue of `skyyrose-product-card-holo` in `inc/builders/elementor.php`.

---

## 9. Conventions

### PHP Naming
- All functions prefixed `skyyrose_` (not `skyyrose_flagship_` — that's a legacy alias for nav fallback only)
- No leading underscore on public functions (WPCS requirement)
- Classes: `SkyyRose_*` (e.g., `SkyyRose_Accessibility_Fix`, `SkyyRose_Wishlist_Widget`)
- Constants: `SKYYROSE_*` uppercase

### Escape / Sanitize
- Output: `esc_html()`, `esc_attr()`, `esc_url()`, `wp_kses_post()`, `wp_kses($val, $svg_kses)` for SVG
- Input: `sanitize_text_field()`, `absint()`, `sanitize_key()`, `sanitize_title()` (for ID slugs)
- SQL: Always `$wpdb->prepare()` — no concatenation
- Nonce + capability check on all write AJAX/REST actions
- SSRF: `skyyrose_see_is_safe_url()` blocks 169.254.x.x and private IP ranges; allows 127.x in local only

### CSS Conventions
- BEM: `block__element--modifier` (`.holo__buy--disabled`)
- Collection pages: `col-*` prefix, `data-collection` attribute on wrapper
- Landing pages: `lp-*` prefix
- About page: `abt-*` prefix
- Footer CRO: `ft-cro-*` prefix
- Single product: `sr-*` prefix
- Reveal classes: `rv-clip-up`, `rv-clip-left`, `rv-clip-right`, `rv-clip-diagonal`, `rv-blur`, `rv-blur-down`, `rv-split-char`, `rv-split-word`, `rv-split-line`, `col-reveal`, `lp-rv`, `.abt-page .rv`
- State class: `.is-visible` (toggled by `premium-interactions.js` — single source of truth)
- `homepage-v2.js` uses `.vis` (different class, different semantics — intentional exception)

### JS Conventions
- All IIFEs: `(function () { 'use strict'; })();`
- No `innerHTML` on live DOM — `createElement` + `textContent` everywhere
- `requestAnimationFrame` + `ticking` flag for scroll handlers
- `passive: true` on all scroll/touch event listeners
- `prefers-reduced-motion` checked at module init, early return or force-visible
- `hover: none` detection for touch-specific paths

### Template Part Conventions
- `template-parts/product-card-holo.php` — central card, called via `get_template_part()` with `$args`
- `template-parts/product-grid.php` — unified grid wrapper; 4-source cascade (products > featured > collection > skus)
- `template-parts/collection/page.php` — unified collection layout; all 4 collection templates delegate here
- `template-parts/landing/hero.php` + `landing/product-grid.php` + `landing/faq.php` — landing page partials
- `template-parts/footer-cro.php` — reviews, value props, FAQ (globally included above newsletter bar)

### Block Patterns
- 4 collection hero patterns: `collection-hero-{black-rose,love-hurts,signature,kids-capsule}.php`
- 3 Elementor widget pattern registrations: featured-product, lookbook, newsletter, preorder-cta, testimonials
- `inc/patterns.php` — ob_start loader with sanitize_file_name guard

---

## 10. Recent Activity (by version marker)

| Version | Changes |
|---------|---------|
| 1.0.0 | Commercial release baseline. All theme fundamentals. |
| 3.x | Redirects, immersive adapter, menu setup, product taxonomy |
| 4.0.0 | Theme activation setup. 13 required pages. `SKYYROSE_SETUP_VERSION`. Homepage V2. |
| 5.0.0 | WC content-product.php override → holo card. Toast, wishlist, luxury cursor. |
| 6.1.0 | collection-pages.js unified (replaced 4 separate files). |
| 6.2.0 | Premium animations + interactions engine. Wishlist button hook removed. |
| 6.3.0 | `premium-interactions.js` Motion One integration. |
| 6.4.0 | Admin experience dashboard. SEE analytics. |
| 6.5.0 | `collection/page.php` unified collection layout. Product catalog display layer. Landing page partials. Kids Capsule. FastAPI client. REST kids-capsule. Collection content module. |
| 6.5.1 | `product-catalog-display.php` extracted. `immersive-product-adapter.php` extracted. |
| 6.6.0 | Facebook Pixel consent gate. |
| 6.7.0 | `redirects.php` canonical. `wc-product-functions.php` extracted (fatal fix). |
| 7.0.0 | `footer-cro.php` (reviews, value props, FAQ). |
| **1.1.0** | Current (`SKYYROSE_VERSION`). Accessibility fixes wired (PR #486 merged). Various performance + a11y improvements. |

**Current branch:** `feat/v2-phase-0-5`  
**PR #486 merged:** holo card add-to-cart activation + a11y fixes  
**PR #488 accessibility review:** 7 WCAG regression findings identified (some may already be on current branch)

---

## 11. Notable Gotchas

### 1. Version Mismatch: Code vs. CLAUDE.md
`SKYYROSE_VERSION='1.1.0'` in both `functions.php` and `style.css`. CLAUDE.md says `1.0.0`. Code is authoritative. CDN caches CSS aggressively — always bump `SKYYROSE_VERSION` to verify changes.

### 2. front-page.php Has Its Own Footer
`front-page.php` uses an inline footer (`.ft` class) + `wp_footer()` instead of `get_footer()`. Any template part added to `footer.php` (size-guide-modal, cookie-consent, mobile-nav, toast-container, skyy-mascot) **must also be added to `front-page.php` before `wp_footer()`**. Omitting this means features silently break on the homepage.

### 3. Three.js 3D System Is Dead Code
`assets/js/experiences/` files (experience-base.js, blackrose-experience.js, lovehurts-experience.js, signature-experience.js, init-3d.js) exist and are well-structured but **no PHP template emits the required container IDs** (`#*-experience`). The immersive templates use a 2D hotspot scene engine instead. `init-3d.js` has a `clock.stop()/clock.start()` bug (resets elapsedTime) but it doesn't matter since it's never activated.

### 4. Duplicate `/preorder/` Redirect
`/preorder/` → `/pre-order/` exists in BOTH `inc/accessibility-fix.php` (legacy, in `init` action) AND `inc/redirects.php` (canonical v6.7.0, `template_redirect` priority 1). Both are active. Not a runtime bug (the canonical one fires first), but a maintenance hazard.

### 5. `skyyrose_immersive_product()` Returns Unescaped Values
`inc/immersive-product-adapter.php` explicitly returns raw strings. Templates calling this function must escape output themselves. No automatic escaping.

### 6. Rate Limiting by Email MD5, Not IP
`inc/security.php` rate-limits by MD5 of email address rather than IP address. This is intentional — WordPress.com proxies make IP-based rate limiting unreliable. Side effect: attackers can bypass by using different emails.

### 7. `inc/brand.generated.php` Is Auto-Generated
Do not edit directly. Source of truth is `assets/brand/brand.yaml`, synced via `scripts/sync_brand_to_php.py`. Manual edits will be overwritten on next sync.

### 8. Kids Capsule Collection Behavioral Differences
- No hero background image, uses `<h1>` title instead of logo image
- Products link to `/pre-order/` (via permalink override) not to PDPs
- `show_on_front: false` in collections config
- 3 custom WC meta fields (`_kc_age_range`, `_kc_matching_adult_id`, `_kc_drop_number`)
- Excluded from Elementor collection palette meta box
- Experience menu name is absent (Garden/Ballroom/Runway are for BR/LH/SIG)

### 9. `skyyrose_get_current_template_slug()` is Statically Cached
Called repeatedly within a request safely (0 overhead after first call), but if called before `get_queried_object()` is available it may cache a stale/empty value. All calls happen inside `wp_enqueue_scripts` which fires after the query is resolved — this is not a current issue but would break if called earlier.

### 10. `holo__size-pill` Elements Have No ARIA Roles
Current branch: size pills are plain `<span>` elements inside `.holo__sizes`. No `role="radio"`, no keyboard interaction, no ARIA group labeling. This is a known a11y gap (PR #488 finding). When implementing size selection, use `role="radio"` group with `aria-checked`.

### 11. `.vis` vs `.is-visible` — Two Reveal State Classes
`homepage-v2.js` uses `.vis` for front-page reveal (`.rv`, `.rv-left`, `.rv-right`, `.rv-scale` selectors). All other pages use `.is-visible` toggled by `premium-interactions.js`. These are intentionally separate systems with different semantics — do not unify them.

### 12. Google Fonts Blocked at 3 Levels (Intentional)
All 9 font families are self-hosted woff2 (zero external CDN). Blocking is enforced via: Elementor filter, priority-999 dequeue loop in `inc/performance.php`, DNS prefetch removal. Any future font must be added to `assets/fonts/` and declared in `theme.json`.

### 13. WP.com REST API Pattern
All internal REST API calls use `/?rest_route=/skyyrose/v1/...` pattern, NOT `/wp-json/`. This is required for WordPress.com hosting compatibility. The `inc/admin-experience-dashboard.php` JS also uses this pattern.

### 14. `product-grid.php` null Sentinel for `products` Arg
The `$products` key in `template-parts/product-grid.php` uses `null` as a sentinel (not empty array). Passing `array()` explicitly renders an empty grid (no cascade). Passing `null` or omitting the key cascades to `featured` → `collection` → `skus`. This is intentional — prevents collection pages with 0 visible WC products from silently showing unrelated products.

### 15. Scene WebP Images Missing
Prior session observation (claude-mem #1208, Apr 18): scene WebP background images referenced in immersive templates were missing from the deployed theme assets directory. Verify `assets/images/` includes all scene-bg/*.webp before deploying immersive templates.
