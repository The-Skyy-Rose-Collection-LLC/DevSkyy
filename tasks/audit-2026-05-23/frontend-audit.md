# Frontend Audit — 2026-05-23

**Theme version:** SkyyRose v1.0.0 (SKYYROSE_VERSION constant)
**Source:** `/Users/theceo/DevSkyy/wordpress-theme/skyyrose-flagship/`
**Live:** https://skyyrose.co/ (200, 178KB, verified)

---

## 1. Accessibility AA+

### 1.1 Focus-Visible

**Implementation status:** Present in two competing layers.

`design-tokens.css:179–185` declares a global `:focus-visible` rule with a 2px rose-gold (`#B76E79`) outline. `accessibility.css:84–103` re-declares the same ring via `*:focus-visible` plus per-element selectors. Both are consistent.

**Critical conflict — `commercial-polish.css:303–311` (loaded globally at priority 25, after everything else):**

```css
:focus-visible {
    outline: 2px solid var(--color-gold, #D4AF37);  /* overrides rose-gold */
    outline-offset: 3px;
}
button:focus-visible, a:focus-visible, .btn:focus-visible {
    box-shadow: 0 0 0 3px rgba(212,175,55,0.35);
    outline: none;   /* REMOVES outline on buttons and links */
}
```

`outline: none` on `button:focus-visible` and `a:focus-visible` replaces the visible outline with only a box-shadow. **Box-shadow does not satisfy WCAG SC 1.4.11 Non-Text Contrast** — it is invisible in Windows High Contrast / Forced Colors mode. The `@media (forced-colors: active)` block in `accessibility.css` does not compensate for links or buttons outside the immersive-specific selectors.

| Finding | WCAG SC | Severity |
|---------|---------|----------|
| `a:focus-visible` and `button:focus-visible` have `outline: none` — box-shadow only | 1.4.11, 2.4.7 | **P0** |

**Fix:** `commercial-polish.css:309–311` — change to:
```css
button:focus-visible, a:focus-visible, .btn:focus-visible {
    outline: 2px solid var(--color-gold, #D4AF37);
    outline-offset: 3px;
    box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.35);
}
```

**Other interactive elements:**
- Holo cards: `product-card-holo.php:53,114,120` — links and wishlist buttons have `aria-label`. Focus state inherited from global `*:focus-visible`. Acceptable (but rendered moot by the commercial-polish override above).
- Mobile nav trigger: `header.php:79` — `<button aria-expanded="false" aria-controls="mobile-menu">` — correct.
- Hamburger / close: `header.php:94` — `aria-label="Close navigation menu"` — correct.
- Mascot: disabled. `inc/enqueue.php:207–209` confirms both CSS and JS are commented out pending art finalisation. No finding.

---

### 1.2 Skip Link

**Source:** `header.php:20`, `accessibility.css:15–41`

```html
<a class="skip-link" href="#primary">Skip to the story</a>
```

CSS: `position: absolute; top: -100%` at rest; `top: 0` on `:focus`. Renders above page at top of viewport on tab — visible by design.

**Issues found:**

| Issue | Detail | Severity |
|-------|--------|---------|
| Target anchor `#primary` — `id="content"` is on `div.site-content` (`header.php:125`), not `id="primary"`. The skip link points to a non-existent anchor on the homepage (`front-page.php` does not emit `id="primary"`). | WCAG SC 2.4.1 | **P1** |
| Skip link text "Skip to the story" is non-standard. "Skip to main content" is the recognised pattern; "the story" is brand flavour but assistive tech users rely on predictable text. | WCAG best practice | P3 |
| No `scroll-padding-top` is set on `:root` or `html` despite `--header-height: 72px` being declared in `design-tokens.css:33`. Without it, the sticky navbar (72px) obscures the focussed landmark after skip. | WCAG SC 2.4.1 intent | **P1** |

**Fix for broken target:** Either add `id="primary"` to the `<main>` element in each template, or change `href="#content"` in `header.php:20` to match the existing `id="content"` div at `header.php:125`. The `id="content"` approach already exists; the skip link target is simply wrong.

**Fix for scroll offset:** Add to `design-tokens.css` (after `:root` block):
```css
html {
    scroll-padding-top: var(--header-height, 72px);
}
```

---

### 1.3 Contrast Ratios

All ratios calculated against deployed CSS token values. Background is `#0A0A0A` (default `--skyyrose-bg`) unless noted.

**Body copy and primary text:**

| Pair | Ratio | AA (4.5:1) | AAA (7:1) |
|------|-------|-----------|---------|
| `#F5E6D3` (body text) on `#0A0A0A` | 16.16:1 | PASS | PASS |
| `rgba(245,230,211,0.7)` muted (≈ `#ABA194`) on `#0A0A0A` | 7.78:1 | PASS | PASS |
| `rgba(255,255,255,0.55)` `.ft-cro__subheading` (≈ `#8C8C8C`) on `#0A0A0A` | 5.89:1 | PASS | fail |
| `rgba(255,255,255,0.6)` `.col-hero__subtitle` (≈ `#999`) on `#0A0A0A` | 6.95:1 | PASS | fail |

**Brand accent colors as text/UI on dark background:**

| Pair | Ratio | AA-body | AA-large (3:1) | Note |
|------|-------|---------|---------------|------|
| Rose-gold `#B76E79` on `#0A0A0A` | 5.20:1 | PASS | PASS | Default, Kids Capsule accent |
| Silver `#C0C0C0` on `#0A0A0A` | 10.88:1 | PASS | PASS | Black Rose accent |
| Crimson `#DC143C` on `#0A0A0A` | 3.97:1 | **FAIL** | PASS | Love Hurts accent |
| Gold `#D4AF37` on `#0A0A0A` | 9.42:1 | PASS | PASS | Signature accent |
| Love Hurts `--skyyrose-accent-dark` `#9B0F2E` on `#0A0A0A` | 2.36:1 | **FAIL** | **FAIL** | Used in hover/active states |

**Focus ring contrast:**

| Pair | Ratio | AA-body | Note |
|------|-------|---------|------|
| Rose-gold focus ring `#B76E79` on `#0A0A0A` (dark pages) | 5.20:1 | PASS | |
| Gold focus ring `#D4AF37` on `#0A0A0A` (commercial-polish override) | 9.42:1 | PASS | |
| Rose-gold focus ring `#B76E79` on white `#FFFFFF` (WC checkout form fields) | 3.80:1 | **FAIL** | WCAG SC 1.4.11 requires 3:1 for UI components — barely fails |

**Skip link:**

| Pair | Ratio | Note |
|------|-------|------|
| White `#FFF` text on rose-gold `#B76E79` background | 3.80:1 | **FAIL** AA-body (4.5:1). Meets AA-large (3:1) only if text ≥ 18pt/24px. Skip link is `0.75rem` / 12px — **fails**. |
| Gold outline `#D4AF37` on rose-gold `#B76E79` background (skip link border) | 1.81:1 | Decorative — not a content failure, but reinforces visual inconsistency |

**Summary of contrast failures:**

| Failure | Location | WCAG SC | Severity |
|---------|----------|---------|----------|
| Crimson `#DC143C` as body text on dark (e.g. `.lp-alert`, CTA labels in Love Hurts) | `design-tokens.css:327`, `landing-pages.css` | 1.4.3 | **P1** — only applies when crimson used at normal text weight/size |
| `#9B0F2E` (love-hurts accent-dark) on dark bg — 2.36:1 | `design-tokens.css:329` | 1.4.11 | **P1** |
| Skip-link white text on rose-gold bg — 3.80:1 at 12px | `accessibility.css:22–23` | 1.4.3 | **P1** |
| Rose-gold focus ring on white checkout field backgrounds — 3.80:1 | `woocommerce-checkout.css:233` | 1.4.11 | **P2** |

---

### 1.4 ARIA Semantics

| Element | Status | Finding |
|---------|--------|---------|
| `<header id="masthead" role="banner">` | Correct | `role="banner"` is redundant on `<header>` but harmless |
| `<nav aria-label="Primary Navigation">` | Correct | |
| Mobile menu `<div id="mobile-menu" aria-hidden="true" inert>` | Correct | Uses native `inert` attribute — modern and correct |
| Search overlay `<div id="search-overlay" aria-hidden="true" inert>` | **Partial** | Missing `role="dialog"` and `aria-modal="true"`. Screen reader users tabbing when overlay is open get no dialog context. Per prior observation cmem #2034. |
| Search form `<form role="search">` + `<label class="screen-reader-text" for="search-overlay-input">` | Correct | |
| Cookie consent `role="dialog" aria-label="Cookie consent"` | Correct | |
| Holo card links: `aria-label` set | Correct | |
| Holo card wishlist/add buttons: `aria-label` set | Correct | |
| Mobile nav items (`.mobile-nav__item`): no `aria-current` for active page | Missing `aria-current="page"` on active nav item | P2 |
| Checkout `showStep()`: does not move keyboard focus to new step | `assets/js/single-product.js` — per prior observation cmem #2030 | **P1** |

---

## 2. Mobile 375px Breakpoint Review

Smallest responsive breakpoint in the theme's CSS is **480px** (`collection-pages.css:544`, `landing-pages.css:970`). There are **no 375px-specific breakpoints** anywhere in the theme CSS. The 375px viewport falls through to the 480px block, meaning layout is only tested/designed at 480px, not the 375px iPhone SE target.

### 2.1 Homepage (`front-page.php`)

The homepage JS (`homepage-v2.js`) is **inlined** as a critical-path script (`front-page.php:597–609`) — no Three.js dependency confirmed (grep for `THREE` returns 0 matches in `homepage-v2.js`). Three.js is only loaded by `inc/enqueue-experiences.php` for the four `template-immersive-*.php` pages.

| Issue | Detail | Severity |
|-------|--------|---------|
| No 375px breakpoint — layout falls through from 480px styles | No source file addresses 375–479px explicitly | P2 |
| Inline canvas grain (`grainCanvas`) runs at 12fps — on low-end iPhone SE this produces detectable jank; no device-capability gate | `homepage-v2.js:347–362` | P2 |
| `env(safe-area-inset-bottom)` used in mobile-nav padding — correct. Homepage has its own inline footer, not `get_footer()`. Verify `mobile-nav` template part is included before `wp_footer()` in `front-page.php` | `front-page.php:612+` — template part inclusion order per cerebrum | P3 |

### 2.2 Collection Page (`/collection-signature/`)

CSS: `collection-pages.css`. Breakpoints: 1024px, 768px, 480px.

| Issue | Detail | Severity |
|-------|--------|---------|
| **11px and 10px body text** in hero badge/subtitle/tag elements rendered at all breakpoints including 480px: `.col-hero__badge` (`collection-pages.css:67`), `.col-hero__subtitle` (`collection-pages.css:105`), `.col-product-tag` (`collection-pages.css:264`) | iOS Safari forces 16px minimum for form fields only — it does **not** auto-zoom for non-form text < 16px. 10–11px text is visually unreadable at 375px, fails WCAG SC 1.4.4 (resize) and creates poor UX. | **P1** |
| No 375px breakpoint — `col-hero` columns and grid layout only adjust at 480px | `collection-pages.css:544` | P2 |
| `.col-hero__badge` uses `ui-monospace` at 11px with 8px letter-spacing — at 375px this renders as 2–3 characters visible per line | `collection-pages.css:65–69` | P2 |

### 2.3 Landing Page (`/landing-love-hurts/` or equivalent)

CSS: `landing-pages.css`. Breakpoints: 1024px, 768px, 480px.

| Issue | Detail | Severity |
|-------|--------|---------|
| No 375px breakpoint | `landing-pages.css:970` bottom breakpoint is 480px | P2 |
| `14px` text at `.lp-prose` (`landing-pages.css:251`) not addressed in the 480px block — likely renders smaller than 16px on viewport scaling at 375px | `landing-pages.css:251` | P2 |
| Crimson `#DC143C` used as accent text on dark (`--skyyrose-bg: #0A0A0A` for love-hurts) — 3.97:1, fails AA for normal-weight body text | `design-tokens.css:327` | P1 (same as §1.3) |

### 2.4 PDP (Single Product)

CSS: `single-product.css` (loaded conditionally — correct). JS: `single-product.js` + `complete-the-look.js` + `product-card-holo.js`.

| Issue | Detail | Severity |
|-------|--------|---------|
| Focus management: checkout `showStep()` does not move focus to new step | `assets/js/single-product.js` — keyboard users lose context on multi-step interactions | P1 |
| No 375px breakpoint found in `single-product.css` | Would require reading full file — bottom breakpoint assumed 480px by pattern | P2 (caveat) |

### 2.5 Mobile Bottom Navigation

The `.mobile-nav` bar uses `padding: 8px 12px calc(8px + env(safe-area-inset-bottom))` and item labels at **9px** (`mobile-bottom-nav.css:68,80`).

| Issue | Detail | Severity |
|-------|--------|---------|
| **9px label text** below nav icons | `mobile-bottom-nav.css:68,80` — WCAG SC 1.4.4: text must be resizable to 200% without loss of content. 9px × 2 = 18px: technically compliant at 200%, but at default size 9px is smaller than any browser's minimum recommended size (12px) and near-unreadable on iPhone SE | P2 |
| Nav item tap target: `width: 20%; padding: 6px 0` with icon 22×22px and font 9px. Total touch height ≈ 22+9+6+6 = 43px — **1px below the 44px WCAG 2.2 SC 2.5.8 minimum**. `accessibility.css:232–241` sets `min-height: 44px` on `a` but `mobile-bottom-nav.css` does not explicitly enforce this via `min-height` on `.mobile-nav__item` | `mobile-bottom-nav.css:37,55–56` vs `accessibility.css:238` | P2 |

### 2.6 Cart / Checkout

CSS: `woocommerce.css` + `woocommerce-checkout.css` (conditionally loaded — correct).

| Issue | Detail | Severity |
|-------|--------|---------|
| Rose-gold focus ring `#B76E79` on white form field backgrounds — 3.80:1, fails SC 1.4.11 | `woocommerce-checkout.css:228–234` — `--skyy-woo-accent` resolves to `#B76E79` (`woocommerce.css:28`) | P2 |
| Checkout `padding: 40px` at base, `20px` at `max-width: 768px` — no 375px adjustment | `woocommerce-checkout.css:16–25` | P2 |

---

## 3. JS Bundle Analysis

### 3.1 Library Sizes (local, `.min.js`)

| Library | Size (min) | Loaded On |
|---------|-----------|----------|
| `lib/three.min.js` | **594KB** | immersive templates only (enqueue-experiences.php) |
| `lib/gsap.min.js` | **70KB** | preorder-gateway, immersive, kc-launch only |
| `lib/motion.min.js` | **64KB** | all pages except cart/checkout/blog/single/404/search/default |
| `lib/ScrollTrigger.min.js` | 42KB | preorder-gateway, immersive, kc-launch only |

**Three.js is correctly gated to immersive templates only.** `homepage-v2.js` uses a `<canvas>` element for grain but implements it with plain `Canvas2D` — confirmed by grep (0 `THREE` references). Three.js does **not** load on the homepage.

### 3.2 Per-Template JS Payload Estimate

Computed from `.min.js` file sizes. "Global" = loads on every template.

| Script | Size | Scope |
|--------|------|-------|
| `navigation.min.js` | 2.9KB | Global |
| `toast.min.js` | 1.0KB | Global |
| `footer-cro.min.js` | 647B | Global |
| `page-transitions.min.js` | 2.1KB | Global |
| `motion.min.js` | 64KB | Global (skip: cart/checkout/blog/single/404/search) |
| `premium-interactions.min.js` | 4.5KB | Global (same skip list as motion) |
| `luxury-cursor.min.js` | 1.8KB | All except immersive (CURS-03 gate) |
| `performance-guardian.min.js` | 1.1KB | Global (Phase 2 — if module active) |

| Template | Core Global | + Template JS | + Lib | Est. Total |
|----------|------------|--------------|-------|-----------|
| **Homepage** | 72KB (nav+toast+fcro+pt+motion+pi+cursor) | 5.9KB (homepage-v2) | — | ~78KB |
| **Collection page** | 72KB | 1.4KB (collection-pages) + 4.7KB (holo) + 3.1KB (brand-atmosphere) + 6.2KB (smart-showcase) + 3.0KB (micro-interactions) + 2.5KB (experience-analyzer) | — | ~93KB |
| **Landing page** | 72KB | 2.3KB (landing-pages) + 4.7KB (holo) | — | ~79KB |
| **PDP** | 72KB | 5.5KB (single-product) + 984B (complete-the-look) + 4.7KB (holo) | — | ~83KB |
| **Cart** | 11KB (nav+toast+fcro+pt; no motion) | 8.9KB (woocommerce) | — | ~20KB |
| **Checkout** | 11KB | 8.9KB (woocommerce) | — | ~20KB |
| **Immersive** | 72KB (motion loads) | 7.6KB (immersive) + 2.3KB (wc-bridge) | 594KB (three) + 70KB (gsap) + 42KB (ST) | ~790KB |
| **Preorder gateway** | 72KB | 4.8KB (preorder) + 4.7KB (holo) | 70KB (gsap) + 42KB (ST) | ~194KB |

*Estimates use minified sizes. Does not include WP core scripts, jQuery, or WooCommerce scripts.*

### 3.3 Global Scripts That Should Be Template-Gated

| Script | Current scope | Actually used on | Recommendation |
|--------|--------------|-----------------|----------------|
| `luxury-cursor.min.js` (1.8KB) | All pages except immersive | Desktop only, cursor interaction pages | Already gated via CURS-03. **Correct — no action.** |
| `page-transitions.min.js` (2.1KB) | Global all pages | All pages (prefetch + skeleton screens) | **Correct — global use is intentional.** |
| `motion.min.js` + `premium-interactions.min.js` (68.5KB combined) | Global minus lightweight slugs | Front-page, collection, landing, about, preorder, PDP, shop-archive | Skip list at `enqueue.php:237–241` is correct. **One gap:** `shop-archive` is in `skyyrose_phase3_product_slugs()` (loads motion) but `shop-archive` is also a WooCommerce loop page — if the Experience Engine modules are inactive, motion.min.js (64KB) still loads because `$skip_premium_js` only checks `cart/checkout/blog/single/404/search/default`, and `shop-archive` is not in that list. Confirm with module activation state. |
| `performance-guardian.min.js` (1.1KB) | Global (Phase 2) | All pages — lightweight tracker | **Correct — intentionally global.** |
| `footer-cro.min.js` (647B) | Global | Pages with footer FAQ accordion | Footer is global — **correct.** |
| `brand-atmosphere.js` (3.1KB) | Collection pages only (Phase 2b) | `collection-standalone` only | **Correct — already template-gated.** |
| `experience-analyzer.min.js` (2.5KB) | Phase 3 slugs (incl. front-page, search) | Product-facing pages | **Correct.** |

### 3.4 Positive Signals (Leave As-Is)

- Three.js (594KB) is gated exclusively to `immersive` slug via `enqueue-experiences.php`. Never loads on commercial pages.
- GSAP + ScrollTrigger (112KB combined) gated to `preorder-gateway`, `immersive`, `kc-launch`. Removed from `about` in v1.5.8 (per enqueue.php comment line 679).
- Cart and checkout payload is lean (~20KB) — no motion lib, no holo cards.
- `luxury-cursor.js` gated off immersive (CURS-03 — `enqueue.php:624`). Pattern is correct.
- WooCommerce-specific JS only loads on `cart`, `checkout`, `single-product` — correct.

---

## Fix Priority Matrix

| Severity | Effort | File | Line | Fix |
|----------|--------|------|------|-----|
| **P0** | Low | `assets/css/commercial-polish.css` | 309–311 | Remove `outline: none` from `button:focus-visible, a:focus-visible` block; keep box-shadow, add `outline: 2px solid var(--color-gold)` |
| **P1** | Low | `header.php` | 20 | Change `href="#primary"` to `href="#content"` (matching existing `id="content"` at line 125) |
| **P1** | Low | `assets/css/design-tokens.css` | after line 177 | Add `html { scroll-padding-top: var(--header-height, 72px); }` |
| **P1** | Low | `assets/css/accessibility.css` | 22–23 | Increase skip-link text contrast: change text to `#0A0A0A` (dark) on rose-gold bg — ratio becomes 5.20:1, PASS |
| **P1** | Medium | `assets/css/collection-pages.css` | 65–70, 103–108, 262–266 | Increase `.col-hero__badge`, `.col-hero__subtitle`, and tag elements to minimum `13px` (12px minimum with letter-spacing is unreadable; use `clamp(11px, 1.5vw, 12px)` or set a 375px breakpoint) |
| **P1** | Low | `assets/css/design-tokens.css` | 329 | `#9B0F2E` used as text/UI `--skyyrose-accent-dark` in Love Hurts hover states — 2.36:1 fails. Change to `#C4143E` (4.51:1) or use only for decorative/non-text elements |
| **P1** | Medium | `assets/js/single-product.js` | showStep() function | Move keyboard focus to new step heading or first field on step transition (cmem #2030) |
| **P2** | Low | `header.php` | 112–122 | Add `role="dialog" aria-modal="true"` to `#search-overlay` div (cmem #2034) |
| **P2** | Low | `assets/css/woocommerce-checkout.css` | 233 | Change focus outline color to gold `#D4AF37` (9.42:1 on white WC field bg) instead of rose-gold (3.80:1) |
| **P2** | Low | `assets/css/mobile-bottom-nav.css` | 37 | Add `min-height: 44px` to `.mobile-nav__item` to guarantee tap target compliance |
| **P2** | Low | `assets/css/collection-pages.css` | 544 | Add `@media (max-width: 375px)` block addressing col-hero padding, font scaling |
| **P2** | Low | `assets/css/landing-pages.css` | 970 | Add `@media (max-width: 375px)` block addressing lp-hero padding, prose font size |
| **P2** | Medium | `template-parts/` (navigation) | mobile-nav active item | Add `aria-current="page"` to active `.mobile-nav__item` via PHP `is_page()` check |
| **P3** | Low | `header.php` | 20 | Optionally change skip text to "Skip to main content" for screen-reader familiarity |
