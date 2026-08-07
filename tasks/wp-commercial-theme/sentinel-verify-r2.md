# Sentinel2 — v1.12.5 Live Verification (Round 2)

Date: 2026-07-20 · Target: skyyrose.co theme v1.12.5 (live) · Method: cache-busted curl + Playwright (mobile 390x844 + desktop 1440x900). All evidence re-derived fresh this session; no change descriptions trusted.

## Verdicts

### 1. Collection scroll motion — VERIFIED
- HTML ships ONLY `collection-motion-loader.min.js?ver=1.12.5` (deferred, 482B) on /collections/black-rose/ and /collections/love-hurts/ — no eager gsap/ScrollTrigger/immersive-core/feature-scroll/immersive/wc-bridge script tags (curl, cache-busted).
- (a) Hero paints fully styled with no blank/unstyled flash — eyes-on desktop BR (lockup image, emblem, backdrop, copy), mobile BR, mobile LH (screenshots s2-br-desktop-hero / s2-br-mobile-hero / s2-lh-mobile-hero.jpeg).
- (b) After scroll, feature-scroll + product grid are opacity 1 / visible with real content: BR 14 cards (eyes-on: jersey cards, prices, PRE-ORDER buttons), LH 5 cards (eyes-on: Fannie crossbody, tracksuit, VIEW PIECE / QUICK ADD). Nothing stays invisible.
- (c) Zero console errors AND zero warnings on every page tested (BR/LH desktop+mobile, home, shop, cart, wishlist).
- (d) Injected chain loads in order, all HTTP 200: gsap → ScrollTrigger → collection-feature-scroll → immersive-core → immersive → wc-bridge (late request indices = injected, not eager).
  - Interaction path: fresh LH load, wheel immediately → gsap requested at 2549ms vs loadEnd 2504ms (45ms after wheel).
  - Timer path: fresh LH load, NO interaction → gsap absent at 5.5s, requested at 10529ms ≈ load(~2.5s)+8000ms. Mobile BR same: 10122ms. Matches loader source exactly (pointerdown/keydown/touchstart/wheel once-listeners + 8s post-load setTimeout).

### 2. Footer CLS guard — VERIFIED
- /cart/ + /wishlist/: `skyyrose-footer-css`, `skyyrose-footer-cro-css`, `skyyrose-mascot-css` are render-blocking `media='all'` links (curl) → footer styled at first paint, no async flash possible. Eyes-on: styled footer bottom bar on cart (s2-cart-footer.jpeg).
- Tall pages (home, collections): same three sheets load async `media='print' onload="this.media='all'"` with `<noscript>` fallbacks; after load the link is media=all and the footer is identically styled — cart/wishlist/tall all measure bg rgb(0,0,0), height 1842px, 36 links.

### 3. Shop LCP — VERIFIED
- First content image (br-003 holo front) is `loading="eager" fetchpriority="high"`; first-row v7 card fronts eager; below-fold cards (br-009 onward) and all alt/back shots `loading="lazy"` (curl, DOM order).
- Page renders correctly: "Showing 1–12 of 33 results", first row painted, sorting control present, 0 console errors (s2-shop-desktop.jpeg).

### 4. Mascot — VERIFIED
- Fresh session, NO interaction: appears at ~14.5s = 8s loader + 4.5s designed FIRST_ENTRY_DELAY_MS entrance — eyes-on with greeting bubble "Hey! I'm Skyy 👋 Welcome…" (s2-home-mascot.jpeg). Note: total is ~12.5–14.5s, not literally ≤8s — that is the designed v1.12.5 stack (loader 8s + entrance 4.5s), not a defect.
- With interaction she comes sooner (loader fires instantly on wheel) — eyes-on walking on BR desktop mid-scroll and LH desktop mid-scroll screenshots.
- Mid-session subtlety (designed, source-verified in mascot.js): after her first appearance, re-entries on subsequent pages wait a randomized 10–30s idle window — observed hidden at 27s on home mid-session before the fresh-session probe confirmed first-entry behavior.
- 0 console errors from her loader anywhere. Checkout exclusion: `inc/enqueue.php:240` and `:412` (`! is_checkout()`); live /checkout/ 302→/cart/ with empty cart, so the live checkout page itself was not exercisable without seeding a cart — exclusion is source-verified.

### 5. Regression sweep — VERIFIED
- HTTP 200 + zero PHP error markers + healthy sizes (cache-busted): / 175KB, /shop/ 186KB, /collections/black-rose/ 217KB, /collections/love-hurts/ 176KB, /product/the-fannie/ 236KB, /cart/ 253KB, /wishlist/ 127KB, /faq/ 148KB.

## Non-blocking observations
1. **Injected chain pinned at ?ver=1.12.4** while the loader is 1.12.5 (gsap lib at ver=3.12.2 is intentional). If a future release edits any chained file, stale-cache risk unless the injected-chain version string is bumped with SKYYROSE_VERSION. Cosmetic today — all files serve current content.
2. **Pre-existing, not v1.12.5:** BR "Moonlit Courtyard" scene layer references `homepage-col-black-rose.webp` (404 live, absent in local tree); renders the designed "COMING SOON." fallback card. Reference dates to SOT-era commits (a717f522a et al.). Iron Gazebo scene loads fine (200).
