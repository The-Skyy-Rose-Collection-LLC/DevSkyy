---
name: web-vitals-budgets
description: Browser-measured Core Web Vitals (LCP/CLS/INP) budgets and measurement workflow for hero video, animated headers, and immersive media surfaces. Use before/after shipping any above-the-fold media change to skyyrose.co, and during launch audits. Complements wp-performance (which is backend-only by design).
---

# Web Vitals Budgets — Media-Heavy Surfaces

`wp-performance` explicitly opts out of browser measurement. This skill is the browser half: real LCP/CLS numbers via Chrome DevTools MCP or Playwright, with budgets for the media patterns this site actually ships.

## Budgets (skyyrose.co, mobile 4G reference)

| Metric | Budget | Hard fail |
|---|---|---|
| LCP | ≤ 2.5s (excl. known TTFB debt ~2.3-3.4s — track separately, don't hide it) | > 4.0s |
| CLS | ≤ 0.05 | > 0.1 |
| INP | ≤ 200ms | > 500ms |
| Above-fold media weight | ≤ 1.5MB total | > 2.5MB |
| Header animated asset | ≤ 400KB | > 1MB |

## Measurement workflow (must produce numbers, not vibes)

1. **Chrome DevTools MCP**: `performance_start_trace` → navigate cold (cache disabled) → `performance_stop_trace` → `performance_analyze_insight` for LCP breakdown (TTFB / load delay / load time / render delay). Mobile viewport 390×844 AND desktop 1440×900.
2. **Playwright fallback**: `browser_evaluate` → `new PerformanceObserver` for `largest-contentful-paint` + `layout-shift` entries; report element attribution for LCP (WHICH element — if the header video steals LCP candidacy from the hero, that's a regression even at same ms).
3. Three runs, report median. One run = noise.
4. Before/after on the SAME network conditions — deploy comparisons across different cache states are invalid.

## Media patterns that keep vitals green

- **Hero/section video**: `preload="metadata"`, `poster` (the poster IS the LCP candidate — optimize it like a hero image ≤200KB), `autoplay muted loop playsinline`, explicit `width/height` (CLS), lazy-mount below-fold videos via IntersectionObserver.
- **Animated header media (video-in-nav)**: must NOT be the LCP element (small + `fetchpriority="low"`); explicit dimensions so nav never reflows; pause when `document.hidden` and under `prefers-reduced-motion` (battery + vitals + WCAG together).
- **Auto-scrolling image strips**: `content-visibility: auto` off-screen; `loading="lazy"` except first viewport-visible items; `transform`-only animation (compositor thread — zero layout cost); total strip weight budgeted like a carousel, ≤ 100KB/image.
- **Fonts/lockup images in hero**: `fetchpriority="high"` on the ONE intended LCP element; everything else in the hero defers to it.

## CLS traps specific to this theme

- `.min` rebuild changing rendered sizes: any CSS edit that alters above-fold layout re-measures CLS, not just visual QA.
- WP admin-bar (logged-in) shifts everything 32px — measure logged-OUT.
- Batcache/edge cache serves stale HTML referencing new CSS versions (or vice versa) during deploy windows — measure after cache settles or with cache-busted URL, and note which.

## Reporting format

`LCP 2.31s (el: img.hero-lockup, ttfb 1.9s) | CLS 0.02 | INP 140ms | mobile, 3-run median, cold` — element attribution + conditions or the number doesn't count.
