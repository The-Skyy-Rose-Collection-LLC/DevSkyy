# Immersive Scene Intro + Premium Motion — Design Spec

**Date:** 2026-05-28
**Status:** Approved (design) — awaiting spec review → implementation plan
**Surfaces:** `template-preorder-gateway.php` + 4× `template-immersive-{signature,black-rose,love-hurts,kids-capsule}.php`
**Trigger:** PixelVault (pixelvault.fit) immersive marketplace as inspiration. Not a clone — the live site was unreachable (TLS-blocked in env). This borrows the *immersive intro feel*, translated to SkyyRose concrete-luxury canon.

---

## 1. Goal

Add a cinematic **scene intro** to the immersive collection rooms, plus two supporting motion upgrades, without rebuilding the rich motion layer the theme already ships. Fold in a canon fix while we're in the relevant templates.

### Success criteria
- Each immersive room opens with a per-collection cinematic intro (concrete-dust → lockup image → wipe → room).
- Preorder page gains inertia smooth-scroll that shares one clock with existing GSAP/parallax.
- Hero + product media gain a *subtle* hover-warp (luxury, not glitch).
- Collection title is no longer type-rendered text — it is the **lockup image** (canon), with a visually-hidden `<h1>` preserved for SEO/a11y.
- Zero regressions: reduced-motion users get instant, static rooms; LCP is not blocked; no CDN added.

### Non-goals (explicitly out)
- Reviving the dormant Three.js/WebGL stack (declined — Move D).
- Any audio / sound-on-interaction (declined — Move E).
- Sitewide rollout. Only the 5 named templates.
- Touching the 2D composited immersive engine's room/hotspot logic.

---

## 2. Scope per surface

| Capability | 4 immersive rooms | Preorder page | Why |
|------------|-------------------|---------------|-----|
| **B · Scene intro** | ✅ full ("bigger") | ✅ light page-in | Fixed-viewport rooms gain feel from the *intro*, not scroll |
| **A · Lenis smooth-scroll** | ✕ no-op | ✅ | Rooms are `100vh; overflow:hidden` (`immersive.css:23-29`) — nothing to smooth |
| **C · Media hover-warp** | ✅ subtle | ✅ subtle | Scene img + product thumb (rooms); showcase cards + holo media (preorder) |

---

## 3. Architecture

### 3.1 New shared module
- `assets/js/system/immersive-core.js` — single entry, exposes `initImmersiveCore()` that feature-detects and wires the three capabilities. Each capability is an independent guarded function so one failing/not-applying never blocks the others.
- `assets/css/system/immersive-core.css` — intro overlay, lockup, dust-canvas layer, warp filter styles. Consumes existing design tokens (`--skyyrose-accent`, `--skyyrose-bg`, `--skyyrose-font-display`, etc. from `design-tokens.css`).
- `assets/js/lib/lenis.min.js` — **self-hosted** (zero-CDN, matches the theme's `lib/` pattern: three, gsap, ScrollTrigger, motion are all self-hosted).

### 3.2 Enqueue gating
Add one block to `inc/enqueue.php` keyed on the existing slug helper `skyyrose_get_current_template_slug()` (maps `template-immersive-*.php → 'immersive'`, `template-preorder-gateway.php → 'preorder-gateway'`):

```
$slug = skyyrose_get_current_template_slug();
if ( in_array( $slug, array( 'immersive', 'preorder-gateway' ), true ) ) {
    // immersive-core.css (depends: design-tokens)
    // immersive-core.js  (depends: gsap, ScrollTrigger; defer)
}
if ( 'preorder-gateway' === $slug ) {
    // lenis (lib) — preorder ONLY; immersive rooms are fixed-viewport → no dead bytes there (cf. CURS-03 lesson)
}
```
GSAP (`inc/enqueue.php:683`) + ScrollTrigger (`:684`) are already enqueued on both these slugs — `immersive-core.js` declares them as deps. No new GSAP load.

### 3.3 Data model — collection signal + lockup mapping
The immersive wrapper currently encodes collection only as a CSS class `.immersive-{slug}` (`scene.php:57`) — no `data-collection`. Add `data-collection="{slug}"` to the scene wrapper and to the preorder `<main>` so `immersive-core.js` reads collection generically (one code path, four collections).

Lockup image per collection (all have `.avif` + `.webp`; `hero-overlays/` also has `.png`):

| Collection | slug | Lockup asset | Path |
|-----------|------|--------------|------|
| Black Rose | `black-rose` | `br-brand-script-logotype` | `assets/images/hero-overlays/` |
| Love Hurts | `love-hurts` | `lh-logo-combined` | `assets/images/hero-overlays/` |
| Signature | `signature` | `sig-brand-skyy-rose-gold` | `assets/images/hero-overlays/` |
| Kids Capsule | `kids-capsule` | `sr-monogram-rose-gold` ⚠ interim | `assets/images/logos/` |

⚠ **Kids Capsule gap:** no dedicated Kids lockup exists. Interim = the rose-gold SR monogram (`logos/sr-monogram-rose-gold`, avif+webp only — no png fallback). A Kids-specific lockup can be generated later and swapped via the mapping table; not a blocker.

Markup: `<picture>` with `avif` + `webp` sources, `webp`/`png` `<img>` fallback, `alt="{Collection name}"`, eager-loaded (intro asset). The lockup also serves as the visible title (see §5).

---

## 4. Capability detail

### A · Lenis smooth-scroll (preorder only)
- Init **only** when the page is long-scroll. Detection: presence of `main.preorder-gateway` (or `data-collection` on a non-`.immersive-page` main). Immersive `.immersive-page` (`100vh; overflow:hidden`) → skip.
- Standard Lenis loop; wire `lenis.on('scroll', ScrollTrigger.update)` and drive Lenis' `raf` from GSAP's ticker so existing parallax (`premium-interactions.js:174-188`) and ScrollTrigger ride one clock (no double-rAF jank).
- Guards: `prefers-reduced-motion: reduce` → do not init (native scroll). Destroy on `pagehide`.

### B · Scene intro ("bigger")
GSAP timeline, ~2.5–3.0s total, mounted as a fixed full-viewport overlay **above** the room (room DOM renders underneath → LCP element is the room, not the overlay):
1. **Concrete (0–0.4s):** palette overlay (collection bg token) + concrete-**dust particle canvas** — capped ~120 particles, single `requestAnimationFrame` loop, canvas destroyed + GC'd when timeline completes.
2. **Lockup resolves (0.4–1.4s):** lockup `<picture>` animates blur+grain→sharp, opacity 0→1, subtle pointer-parallax (translate within ±8px from `pointermove`/`deviceorientation`).
3. **Hairline + tagline (1.4–2.0s):** accent rule scales in; collection tagline line fades up (per-collection copy from existing canon — pulled from template, not hardcoded in JS).
4. **Wipe (2.0–2.6s):** overlay `clip-path` inset wipe upward + slight scale-push (1.0→1.03) on the room beneath.
5. **Room live:** overlay `display:none`; existing engine's first beacon pulse fires (unchanged engine behavior).

Guards:
- `prefers-reduced-motion: reduce` → overlay never shown; room is immediately interactive; lockup still set as visible title (static).
- `sessionStorage['skyyrose_intro_seen_{slug}']` → once per session per collection (configurable constant `INTRO_REPLAY = false`).
- Overlay is `aria-hidden="true"` + `inert`; focus stays in the room. Skip affordance: `Esc` or click → jump to end of timeline.
- No audio.

### C · Media hover-warp (subtle)
- SVG `<filter>` with `feTurbulence` + `feDisplacementMap` (low `scale`, ~4–8px max) + a faint chromatic offset, applied via CSS class on hover, opt-in through `[data-warp]`.
- Targets: immersive `.scene-layer img` (`scene.php:83-88`) + `.product-panel-thumb img` (`scene.php:210-214`); preorder `.showcase__card` (`template-preorder-gateway.php:78-103`) + holo card media (`:154-155`).
- Amplitude capped low (luxury, not glitch). Disabled under reduced-motion and on touch (no hover).

---

## 5. Canon fix (folded in)
- **Problem:** `scene.php:182` renders the collection title as type text (`<h1 id="scene-title" class="rv-split-line">`). Canon: collection names must be **lockup images**, never type-rendered. Lockup assets exist on disk but are unreferenced by these templates.
- **Fix:** the visible title becomes the lockup `<picture>` (same asset the intro animates). The `<h1>` is retained but **visually hidden** (`.screen-reader-text`, the theme's existing WP-standard class) carrying the collection name for SEO + a11y. No layout/SEO regression; closes the canon gap.

---

## 6. Error handling & graceful degradation
- **Lockup missing / 404:** intro falls back to a token-styled wordmark beat (no broken image) and logs `console.warn` once; visible title falls back to the (now-visible) `<h1>`. Never a broken `<img>`.
- **GSAP absent (unexpected):** `immersive-core.js` early-returns its intro/warp init; room renders normally (progressive enhancement).
- **Lenis lib fails to load:** preorder uses native scroll (no error surfaced to user).
- **`prefers-reduced-motion`:** all three capabilities self-disable; static, fully functional pages.
- **Touch / `<768px`:** warp + pointer-parallax disabled; intro plays without parallax.

---

## 7. Performance budget
- No new CDN; one new self-hosted lib (Lenis, ~tens of KB), only parsed on the 5 slugs.
- Dust canvas: ≤120 particles, runs only during the ~2.6s intro, then destroyed. No persistent rAF after intro.
- Intro overlay is additive — does **not** become the LCP element; room media (`.scene-layer img`) remains LCP.
- `immersive-core.js` deferred; intro timeline starts on `DOMContentLoaded` + `requestIdleCallback` for the dust canvas warm-up.

---

## 8. Accessibility
- Full `prefers-reduced-motion` honoring across all three capabilities.
- Intro overlay `aria-hidden` + `inert`; `Esc`/click skip; focus never trapped.
- Visually-hidden `<h1>` preserves heading semantics + SEO.
- Lockup `<img>` carries `alt="{Collection}"`.
- Warp is decorative; no informational content conveyed by motion.

---

## 9. PHP touches (small, enumerated)
| File | Change |
|------|--------|
| `template-parts/immersive/scene.php` (shared → all 4 rooms) | Add `data-collection` to wrapper (`:57`); replace type-text title (`:182`) with lockup `<picture>` + visually-hidden `<h1>`; add `data-warp` to `.scene-layer img` (`:83-88`) + `.product-panel-thumb img` (`:210-214`) |
| `template-preorder-gateway.php` | Add `data-collection` to `<main>` (`:63`); add `data-warp` to `.showcase__card` (`:78-103`) |
| `inc/enqueue.php` | One slug-gated enqueue block (lenis lib + immersive-core css/js) |
| `assets/js/lib/lenis.min.js` | New self-hosted lib |

No changes to `immersive.js` (2D engine), hotspot logic, or room navigation.

---

## 10. Verification (no pytest — theme JS/CSS/PHP)
- `wordpress-theme/skyyrose-flagship` PHP lint on touched templates (`npm run lint:php` / `php -l`).
- PHPCS on touched PHP (`vendor/bin/phpcs --standard=.phpcs.xml`).
- Manual: load each of the 5 templates, confirm intro + lockup title + warp; toggle OS reduced-motion and re-confirm static behavior.
- Bump `SKYYROSE_VERSION` (CDN cache-bust) before deploy verify.
- Deploy via `scripts/deploy-theme.sh` (hot-swap) — its `verify_live()` gate asserts HTTP 200 + size + no PHP error markers.
- Cache-bust post-deploy curls (`?cb=$(date +%s)`) — WP.com Batcache serves stale HTML for minutes.

---

## 11. Phasing
- **Phase 1:** Scene intro (B) + lockup canon fix + `data-collection` wiring + enqueue. The thing asked for.
- **Phase 2:** Lenis smooth-scroll (preorder) + media hover-warp (C).

Each phase is independently shippable and verifiable.

---

## 12. Risks
| Risk | Mitigation |
|------|-----------|
| `scene.php` is shared → a bug hits all 4 rooms at once | Phase 1 manual-checks all 4 before deploy; lockup-missing fallback prevents broken render |
| Kids lockup is interim (monogram, not a Kids mark) | Mapping table is one-line swappable; flagged, not blocking |
| Intro perceived as slow on repeat visits | `sessionStorage` once-per-session gate |
| Dust canvas perf on low-end mobile | Particle cap + destroy-after-intro + reduced-motion/touch skip |
| Lenis + GSAP double-rAF jank | Single clock: drive Lenis raf from GSAP ticker, `ScrollTrigger.update` on Lenis scroll |

---

## 13. File manifest (new / modified)
**New:**
- `assets/js/system/immersive-core.js`
- `assets/css/system/immersive-core.css`
- `assets/js/lib/lenis.min.js`

**Modified:**
- `template-parts/immersive/scene.php`
- `template-preorder-gateway.php`
- `inc/enqueue.php`
- `style.css` / version constant (`SKYYROSE_VERSION` bump)

**Open question (non-blocking):** generate a dedicated Kids Capsule lockup to replace the interim SR monogram.
