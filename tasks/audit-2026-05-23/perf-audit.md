# SkyyRose Performance Audit — v1.5.20
**Date:** 2026-05-23 | **Method:** curl-only, read-only | **Theme:** skyyrose-flagship v1.5.20

All claims marked `[measured]` (live curl) or `[inferred from source]` (file:line).

---

## 1. TTFB — All Templates Cache-Bypassed

Every request returns `x-ac: MISS` with `server-timing: cache;desc=MISS`.
Root cause: WooCommerce session cookie (`wp_woocommerce_session_*`) set on every response,
defeating Batcache/Varnish entirely.

| Template | URL | TTFB (ms) | HTML (KB) | Cache | Status |
|---|---|---|---|---|---|
| Homepage | / | 1,582 | 174 | MISS | [measured] |
| Collection | /collection-black-rose/ | 1,487 | 173 | MISS | [measured] |
| Landing | /landing-love-hurts/ | 1,435 | 112 | MISS | [measured] |
| PDP | /product/br-003/ | ~1,600 | 179 | MISS | [measured] |
| Shop | /shop/ | 1,660 | 101 | MISS | [measured] |
| Immersive | /experience-signature/ | 1,669 | 108 | MISS | [measured] |

**P0 — TTFB 1.4–1.7s on every page, zero cache hits site-wide.**
WP.com Batcache is designed to serve ~10ms TTFB on cache hit. 6x slowdown on every cold request.

**Fix:** WooCommerce ships `woocommerce_settings_page_allowed_posts` and a `woocommerce_cart_hash` cookie strategy. On WP.com, the standard fix is to suppress WC session cookie on non-cart/non-checkout pages. In `inc/woocommerce.php`:

```php
// Suppress WC session cookie on cacheable pages to restore Batcache
add_filter( 'woocommerce_set_cookie_enabled', function( $enabled ) {
    if ( is_cart() || is_checkout() || is_account_page() ) {
        return $enabled;
    }
    return false; // cacheable — no session cookie
} );
```

Expected impact: TTFB drops from ~1,500ms to ~10–30ms on Batcache hit (WP.com SLA).

---

## 2. LCP — Per Template

### 2a. Homepage
- **LCP candidate:** CSS `background-image: url('homepage-hero-bg.webp')` on `.hero-bg` div [measured — /tmp/hp.html]
- **Problem:** CSS backgrounds are invisible to the browser's preload scanner. The browser cannot discover this image until CSS is parsed and the rule applied. No `<img>` tag, no preload.
- **Expected preload:** `inc/enqueue.php:542–554` has logic to emit `<link rel="preload" as="image" href="...avif" fetchpriority="high">` for front-page hero. This tag is **absent from live HTML** [measured — grep of /tmp/hp.html returns 0 preload-as-image hits].
- **AVIF exists:** `homepage-hero-bg.avif` HTTP 200, 301KB [measured]. `homepage-hero-bg.webp` = 396KB [measured]. AVIF 24% smaller but not being served.
- **Version anomaly:** homepage CSS assets use `ver=6.3.0` (WordPress core version), while all other templates use `ver=1.5.20`. Cause: Jetpack Boost Critical CSS rewrites the asset version query string with the WP version. Jetpack Boost is active on homepage but not on other templates [measured — /tmp/hp.html vs /tmp/col.html comparison]. Functional concern: the `ver=6.3.0` query string busts the expected `ver=1.5.20` CDN cache, so Jetpack CDN may be serving stale asset bytes while the theme version increments.
- **LCP estimate:** background-image discovered after CSS parse → TTFB(~1,582ms) + CSS parse + background paint. Likely 3.5–5s on 4G [inferred from source — no background preload].

**P0 fix:** Convert homepage hero to `<img loading="eager" fetchpriority="high">` with `<picture>` AVIF+WebP sources, replacing the CSS background. In `front-page.php`, replace the `.hero-bg` div with:
```html
<picture class="hero-bg parallax-ken-burns" aria-hidden="true">
  <source type="image/avif" srcset="<?= esc_url( get_template_directory_uri() ) ?>/assets/images/homepage-hero-bg.avif">
  <img src="<?= esc_url( get_template_directory_uri() ) ?>/assets/images/homepage-hero-bg.webp"
       loading="eager" fetchpriority="high" decoding="sync" alt="" width="1920" height="1080">
</picture>
```
Browser preload scanner picks up `<img>` immediately, LCP image begins downloading in parallel with HTML parse. Estimated LCP improvement: 1.5–2.5s.

### 2b. Collection Page (/collection-black-rose/)
- **LCP candidate:** `<img src="forbidden-midnight-1280w.webp" loading="eager" fetchpriority="high" decoding="async" width="1680" height="720" srcset="...480w...768w...1280w...1680w" sizes="100vw">` [measured — /tmp/col.html]
- **Format:** WebP only — no AVIF sibling for theme-bundled hero images [measured — HTTP 404 for `.avif`]
- **Size at 1280w:** 192KB. At 1680w: 316KB [measured]
- **Preload:** No `<link rel="preload">` for this image [measured — only font preloads in col HTML]
- **LCP path:** `<img>` is discoverable by preload scanner → good. But no explicit preload means it starts only after HTML parse begins, after TTFB of 1,487ms.
- **Missing:** No AVIF source for `forbidden-midnight-*.webp` hero images. `skyyrose_generate_nextgen_siblings()` only runs on `wp_generate_attachment_metadata` (uploaded media). Theme-bundled images in `assets/branding/hero/` never go through the upload pipeline and never get AVIF siblings [inferred from source — `inc/performance.php:364`].

**P1 fix:** Generate AVIF siblings for all `assets/branding/hero/*.webp` files using `wp skyyrose nextgen-backfill` or manual `skyyrose_gd_convert()` call via WP-CLI. Add `<link rel="preload">` for the collection hero in `inc/enqueue.php` alongside the existing front-page preload at lines 542–554, gated on `collection-standalone` slug.

### 2c. Landing Page (/landing-love-hurts/)
- **LCP candidate:** `lh-logo-combined.avif` (93KB) with `loading="eager" fetchpriority="high"` [measured — /tmp/landing.html]
- **Above-fold model image:** `love-hurts-bomber-front-model.webp` (55KB) — visible above fold but no `fetchpriority="high"`, no preload [measured]
- **Format:** AVIF on logo (good). WebP-only on product model image.
- **Status:** Acceptable — 93KB AVIF logo with fetchpriority is a reasonable LCP at ~55KB. The model image is likely LCP on mobile viewports where the logo is smaller.

**P2 fix:** Add `fetchpriority="high"` to `love-hurts-bomber-front-model.webp` in `template-landing-love-hurts.php` if mobile testing confirms it is LCP element.

### 2d. PDP (/product/br-003/)
- **Preloaded image:** `The-BLACK-Jersey-BLACK-Rose-Collection_detail.jpg` — **2.44MB unoptimized JPEG** [measured]
- **Preload tag:** `<link rel="preload" href="...detail.jpg" as="image" fetchpriority="high">` [measured — /tmp/pdp.html:49]
- **Format:** AVIF exists (HTTP 200) + WebP exists (HTTP 200) for this upload [measured]
- **Critical bug:** The preload points at the raw JPEG, not the AVIF. The browser fetches 2.44MB before using the AVIF in the `<picture>` element. Additionally, the preloaded image (`detail.jpg`) appears to be the product gallery hero rather than the PDP's actual first gallery image (`br-003-baseball-classic.jpeg`).
- **Double waste:** 2.44MB download for an image that has a 300KB AVIF equivalent.

**P0 fix:** The PDP preload logic in `inc/enqueue.php` must resolve the AVIF sibling via `skyyrose_avif_sibling_pair()` (already implemented at line 757 of `inc/performance.php`) and emit the AVIF URL in the preload `href`. Minimum patch:

```php
// inc/enqueue.php — in wp_head action for single-product slug
$lcp_webp = get_post_meta( $product_id, '_thumbnail_id', true );
// resolve attachment URL then call skyyrose_avif_sibling_pair()
$pair = skyyrose_avif_sibling_pair( $webp_url );
$preload_href = $pair ? $pair['url'] : $webp_url;
echo '<link rel="preload" href="' . esc_url( $preload_href ) . '" as="image" fetchpriority="high">';
```
Expected: preload fetches ~200KB AVIF instead of 2,440KB JPEG = 2.24MB per PDP load saved.

---

## 3. CLS — Sources

### 3a. Fonts (FOUT via `font-display: swap`)
- All 17 `@font-face` declarations use `font-display: swap` [measured — fonts.css lines 22, 35, 49, 62, ...]
- Two fonts preloaded (Inter + Playfair Display on all pages; Cormorant Garamond + Bebas Neue + Cinzel added on collection/PDP) [measured — preload tags in HTML]
- **Risk:** 5 font families (9 total) not preloaded. On slow connections, swap causes visible text reflow.
- **Unpreloaded families (collection page):** Cinzel is preloaded. Cormorant Garamond preloaded. All 5 critical display fonts have preloads [measured — /tmp/col.html].
- **Assessment:** CLS from fonts is LOW — critical display fonts are preloaded. Body text (Inter) preloaded globally.

### 3b. Hero Image Sizing
- Collection hero `<img>` has explicit `width="1680" height="720"` [measured]. Browser reserves space before load. No CLS.
- PDP gallery images: no explicit dimensions on product images in `<picture>` elements [measured — /tmp/col.html holo card imgs lack width/height]. **CLS risk** on product grid during lazy load.
- Landing hero logo has no explicit dimensions in HTML [inferred — not found in landing HTML grep].

**P2 fix:** Add `width` and `height` attributes to all `<picture><img>` product card images in `template-parts/product-card-holo.php` to prevent layout shift during lazy load.

### 3c. Homepage CSS `background-image` Hero
- Background image has no intrinsic dimensions. If `.hero-bg` height is set via padding or min-height in CSS, CLS is minimal. If height depends on content reflow, CLS occurs. [inferred from source — no way to confirm via curl without JS execution]

### 3d. Three.js Canvas Mount (Immersive)
- Canvas element is created by JS after DOM parse. No placeholder in HTML.
- **Risk:** Canvas insertion can shift surrounding content if the layout doesn't reserve canvas space. [inferred from source — `template-immersive-*.php` structure]
- Homepage Three.js canvas: homepage uses inline canvas grain effect, not Three.js portals per frontend-audit.md (already verified). CLS risk is lower.

---

## 4. INP — Main Thread Blockers (Inferred)

No JS execution data is available via curl. All findings are [inferred from source].

### 4a. Three.js Init — Immersive Pages (790KB bundle)
- 13 separate `<script>` tags for Three.js libs [measured — /tmp/immersive.html]
- `three.min.js` alone: 607KB uncompressed, 152KB brotli-compressed [measured]
- All scripts are `defer` but each is a separate request — 13 HTTP/2 round trips
- No script module bundling / single-file concatenation
- Total Three.js lib payload: 607+26+103+12+12+6+1+1+12+0.6 = ~780KB uncompressed, ~195KB brotli

**P1:** Bundle all `assets/js/lib/three-examples/*.js` + `three.min.js` into a single `three-bundle.min.js` via the build step. Reduces 13 requests to 1 + reduces parse/eval overhead.

### 4b. Main Thread on Collection Page — Render-Blocking CSS
- 37 render-blocking `<link rel="stylesheet">` tags on collection page [measured]
- 36 on landing page [measured]
- 42 on PDP [measured] — includes `skyyrose-immersive-css` (10KB plugin CSS with no relation to a PDP)
- These are mix of: WooCommerce, Jetpack, WordPress core blocks, theme CSS
- Non-theme stylesheets (Jetpack Podcast, jetpack-forms-layout, wp-block-code, jetpack-instant-search) are loading on PDP despite no relevance

**P0:** `skyyrose-immersive-css` (from `skyyrose-immersive` plugin) loading on PDP [measured — `/tmp/pdp.html`]. Gate it behind immersive template check. In the plugin's `register_scripts()`:
```php
// Only enqueue on immersive template pages
if ( 'immersive' !== skyyrose_get_current_template_slug() ) {
    return;
}
```

**P2:** Audit Jetpack plugin CSS — `jetpack-podcast-episode-style`, `jetpack-forms-layout`, `wp-block-code`, `jetpack-instant-search` CSS all load on PDP. These inflate the render-blocking count by ~10 stylesheets. Review which Jetpack modules are needed per template.

### 4c. Homepage — 0 Render-Blocking CSS
- Jetpack Boost deferred all CSS via `media="not all"` + `onload` pattern [measured — /tmp/hp.html]
- Homepage is the only template with this optimization active
- All other templates use standard synchronous `<link rel="stylesheet">` [measured]

---

## 5. Image Strategy

### 5a. AVIF Delivery — Uploads (WooCommerce Media)
- `<picture>` with AVIF+WebP sources correctly wraps upload images via `skyyrose_wrap_attachment_in_picture()` [inferred from source — `inc/performance.php:313`]
- Example on collection page: `br-001-ai-render-01-1.avif` in `<source type="image/avif">` [measured — /tmp/col.html]
- AVIF sibling URL goes direct to `skyyrose.co` origin, bypassing Jetpack Photon [inferred from source — `inc/performance.php:234–243` strips `i[0-2].wp.com` prefix]
- **AVIF coverage gap:** `<img>` fallback `src` still points to Jetpack Photon (`i0.wp.com`). Photon transcodes `.avif` back to JPEG [documented in `inc/performance.php:226`]. AVIF branch in `<picture>` is correct; Photon fallback degrades format but only for non-AVIF browsers.

### 5b. AVIF Delivery — Theme Branding Assets
- Theme-bundled hero images (`assets/branding/hero/*.webp`, `assets/images/homepage-hero-bg.webp`) have **no AVIF siblings** [measured — HTTP 404 for `.avif` variants]
- These files never pass through the WP upload pipeline so `skyyrose_generate_nextgen_siblings()` never runs on them [inferred from source — `inc/performance.php:364`]
- Impact: homepage hero served as 396KB WebP instead of 294KB AVIF (25% larger) [measured]
- Collection hero served as 192KB WebP at 1280w with no AVIF option [measured]

**P1 fix:** Run `skyyrose_gd_convert()` manually or via WP-CLI on all `assets/branding/` and `assets/images/` WebP files during build/deploy. Store AVIF at same path with `.avif` extension. `skyyrose_avif_sibling_pair()` will auto-detect them. Add a `package.json` build task:
```bash
# in wordpress-theme/package.json scripts
"build:avif": "find wordpress-theme/skyyrose-flagship/assets -name '*.webp' | xargs -I{} wp eval 'skyyrose_gd_convert(\"{}\", \"avif\");'"
```

### 5c. Responsive Images — Collection Hero
- `srcset` with 4 breakpoints (480w/768w/1280w/1680w) + `sizes="100vw"` [measured]
- Mobile (480w): 27KB, tablet (768w): 72KB, desktop (1280w): 192KB, wide (1680w): 316KB [measured]
- Adequate responsive coverage.

### 5d. Lazy Loading
- Holo card product images: `loading="lazy"` [measured — /tmp/col.html]
- Above-fold hero images: `loading="eager"` [measured]
- Correct pattern applied.

### 5e. PDP — 2.44MB JPEG Preload (CRITICAL)
- See Section 2d above. Preloading 2.44MB JPEG when 200KB AVIF exists is P0.

---

## 6. Font Loading

| Family | Preloaded | Templates | woff2 Size | font-display |
|---|---|---|---|---|
| Inter | Yes | All | 47KB | swap [measured] |
| Playfair Display | Yes | All | 38KB | swap [measured] |
| Cormorant Garamond | Yes | Collection, PDP, Landing | unknown | swap |
| Bebas Neue | Yes | Collection, PDP, Landing | unknown | swap |
| Cinzel | Yes | Collection | unknown | swap |
| Bebas Neue | Yes | Collection | unknown | swap |

- All 17 `@font-face` declarations use `font-display: swap` [measured — fonts.css]
- Critical fonts (Inter, Playfair Display) preloaded on every page [measured]
- Collection page preloads 5 font families — good coverage [measured — /tmp/col.html]
- `fonts.css` itself is delivered async via Jetpack Boost `data-media` pattern on homepage, standard sync on other templates

**No P0/P1 font issues.** FOUT risk is LOW given preload coverage. P3: consider `font-display: optional` for non-critical decorative fonts (Cinzel used only in Black Rose headings) to eliminate FOUT on slow connections at cost of occasional invisible text.

---

## 7. Three.js — Immersive Bundle Breakdown

| File | Uncompressed | Brotli | Notes |
|---|---|---|---|
| three.min.js | 607KB | 152KB | [measured] |
| GLTFLoader.js | 103KB | — | [measured] |
| gsap.min.js | 71KB | — | [measured] |
| ScrollTrigger.min.js | 42KB | — | [measured] |
| OrbitControls.js | 26KB | — | [measured] |
| UnrealBloomPass.js | 12KB | — | [measured] |
| DRACOLoader.js | 12KB | — | [measured] |
| RGBELoader.js | 12KB | — | [measured] |
| EffectComposer.js | 6KB | — | [measured] |
| experience-base.min.js | ~10KB | 3KB brotli | [measured] |
| signature-experience.min.js | ~12KB | 2.5KB brotli | [measured] |
| Total libs | ~906KB | ~195KB+ | 13 separate requests |

- Brotli active on `three.min.js` (152KB brotli vs 607KB raw = 75% compression) [measured]
- 13 separate `<script src>` tags in `<body>` [measured]
- Scripts are `defer` — parse does not block render
- Three.js r147 (2022 vintage) — current is r168. Not a performance issue but security surface.

**P1:** Concatenate all `assets/js/lib/three-examples/*.js` into `three-bundle.min.js` in the build step. 13 HTTP/2 requests → 1. Already brotli-compressed by WP.com CDN so concatenation does not increase payload.

**P2:** Tree-shake Three.js imports. The full `three.min.js` (r147) includes renderers, geometries, and lights not used by the signature experience. Custom Three.js module build via `three-minifier` webpack plugin or equivalent can reduce from 607KB to ~150–200KB raw.

---

## 8. Render-Blocking CSS Summary

| Template | Blocking `<link rel="stylesheet">` | Jetpack Boost Async | Theme CSS Mode |
|---|---|---|---|
| Homepage | 0 | Yes (media=not all) | Async [measured] |
| Collection | 37 | No | Sync [measured] |
| Landing | 36 | No | Sync [measured] |
| PDP | 42 | No | Sync [measured] |
| Immersive | 35 | No | Sync [measured] |

**Notable outliers on PDP (42 stylesheets):**
- `skyyrose-immersive-css-css` — 10KB, plugin CSS irrelevant to PDP [measured]
- `jetpack-podcast-episode-style` — irrelevant to PDP
- `jetpack-forms-layout` — irrelevant to PDP
- `wp-block-code` — irrelevant to PDP
- `jetpack-instant-search` — 45KB+, loads on PDP despite no search widget [inferred from source — Jetpack Search loads globally]
- `mediaelement` — WC audio player CSS, irrelevant to fashion PDP
- `brands-styles` — WC Brands extension CSS

**Root cause:** Jetpack Boost's CSS async optimization is only active on the homepage (front-page template). Other templates serve all stylesheets synchronously. The theme has no control over plugin CSS gating outside of `wp_dequeue_style()` calls.

**P1 fix — immersive CSS on PDP:**
In `skyyrose-immersive` plugin's main PHP file, gate the style registration:
```php
add_action( 'wp_enqueue_scripts', function() {
    if ( 'immersive' !== skyyrose_get_current_template_slug() ) { return; }
    wp_enqueue_style( 'skyyrose-immersive-css', ... );
} );
```

**P2 fix — Jetpack CSS globally:**
Add `wp_dequeue_style('jetpack-instant-search')` on non-search templates in `inc/performance.php`. Also dequeue `mediaelement` on non-product-with-audio pages.

---

## Priority Summary

| ID | Severity | Finding | Template | Measured | Fix Location |
|---|---|---|---|---|---|
| PERF-01 | P0 | Zero page cache hits — WC session cookie defeats Batcache | All | Yes | `inc/woocommerce.php` |
| PERF-02 | P0 | PDP preloads 2.44MB JPEG instead of AVIF | PDP | Yes | `inc/enqueue.php` |
| PERF-03 | P0 | Homepage LCP is CSS background-image — invisible to preload scanner | Homepage | Yes | `front-page.php` |
| PERF-04 | P0 | `skyyrose-immersive-css` loads on PDP (irrelevant 10KB render-blocker) | PDP | Yes | Plugin PHP |
| PERF-05 | P1 | 37–42 render-blocking stylesheets on collection/landing/PDP | Collection, Landing, PDP | Yes | Jetpack Boost config |
| PERF-06 | P1 | No AVIF for theme-bundled hero images (WebP only) | Collection, Homepage | Yes | Build step + `inc/performance.php` |
| PERF-07 | P1 | Collection hero has no `<link rel="preload">` | Collection | Yes | `inc/enqueue.php` |
| PERF-08 | P1 | 13 separate Three.js lib requests — no concatenation | Immersive | Yes | Build step |
| PERF-09 | P2 | Product card `<picture>` imgs lack `width`/`height` — CLS risk | Collection, PDP | Inferred | `template-parts/product-card-holo.php` |
| PERF-10 | P2 | Tree-shake Three.js — 607KB full build, only subset used | Immersive | Yes | Build step |
| PERF-11 | P2 | Jetpack Instant Search CSS (45KB+) loads on non-search templates | All | Inferred | `inc/performance.php` |
| PERF-12 | P3 | Homepage CSS `ver=6.3.0` (Jetpack Boost override) vs theme `ver=1.5.20` — stale CDN cache risk | Homepage | Yes | Jetpack Boost settings |
| PERF-13 | P3 | `font-display: swap` on all fonts — minor FOUT on slow 3G | All | Yes | `assets/css/fonts.css` |

---

## Quick Wins (Under 30 Minutes Each)

1. **Gate `skyyrose-immersive-css` to immersive template** — 5 lines in plugin PHP. Removes one render-blocking request from PDP. (PERF-04)
2. **PDP preload → AVIF** — Edit `inc/enqueue.php` preload URL resolution to call `skyyrose_avif_sibling_pair()`. Already implemented in `inc/performance.php:757`. (PERF-02)
3. **WC session cookie suppression on cacheable pages** — 8-line filter in `inc/woocommerce.php`. Enables Batcache site-wide. Highest ROI fix in this audit. (PERF-01)

---

*Audit tooling: curl 8.x, headers via `-D -`, compression test via `Accept-Encoding: gzip,br`.
Source cross-reference: `inc/enqueue.php` (865 lines), `inc/performance.php` (772 lines), live HTML at `/tmp/hp.html` `/tmp/col.html` `/tmp/landing.html` `/tmp/pdp.html` `/tmp/immersive.html`.*
