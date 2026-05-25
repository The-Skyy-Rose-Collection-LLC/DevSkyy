# SkyyRose v1.1.2 — Unified Fix Matrix
**Date:** 2026-05-23
**Audit fleet:** 6 parallel agents (Frontend, Senior Dev, Security, SEO, UX, Performance)
**Total findings catalogued:** 1744 lines across 6 reports
**P0 count:** 9 confirmed → 5 shipped to branch · 1 deferred (PERF-01) · 1 already live (PERF-03)
**SEO P0s INVALIDATED 2026-05-23 post-synthesis:** Live curl + grep on 4 pages (homepage, /collection-signature/, /product/br-001/, /product/sg-001/) confirms 2 JSON-LD blocks per page (Organization+Brand+Person+ImageObject+PostalAddress on home; BreadcrumbList+ItemList+ListItem+Offer on collection; Product+BreadcrumbList+ListItem+Offer on PDPs) AND OG tags present on home + PDP. Yoast NOT installed (0 markers in HTML). SEO audit agent likely used WebFetch which strips `<script>` blocks. Audit's CFG-03 + Yoast theory dead.
**PERF-03 ALSO RESOLVED 2026-05-23 — was stale CDN cache, not a real bug.** Cache-busted curl (`https://skyyrose.co/?cb=<ts>`) shows `<picture>` + `<img fetchpriority="high">` live. Today's deploy shipped the v1.5.17 LCP refactor; perf audit + initial verify both hit Batcache stale copy.

**Phase B branch state:** `fix/audit-2026-05-23-p0-sprint` in worktree `.claude/worktrees/audit-p0-sprint`, 8 atomic commits, 0🔴 cavecrew-reviewer findings outstanding, all PHP lint clean. 5 P0s closed in branch: A11Y-01, PDP-01 (badge + full unhook), PDP-02, TY-01, PERF-02. Awaiting founder review of diff before merge/deploy.

---

## 0. Read-Order for Decision-Makers

If you only read one section: **Section 2 (Sprint 1 Plan)** = the 12-hour cut that ships the maximum revenue + brand impact.

---

## 1. P0 Master List (sorted by ship-effort, ascending)

| # | ID | Title | Source | Effort | Mechanism | Risk |
|---|----|----|-------|--------|-----------|------|
| 1 | CFG-01 | WP Site Title typo "The Skyy Rose Collection" → "SkyyRose" | seo-audit.md | 30s | wp-admin → Settings → General | Zero |
| 2 | CFG-02 | Cart page using Elementor HTML widget instead of WC shortcode | checkout-ux-audit.md C-P0-01/02/03 | 2 min | wp-admin → Pages → Cart → swap template OR replace HTML widget with `[woocommerce_cart]` | Low (revertible) |
| ~~3~~ | ~~CFG-03~~ | ~~Yoast schema config~~ **INVALIDATED — verified live, schema fires correctly on all 4 page types tested. Yoast not installed.** | seo-audit.md P0 | — | — | — |
| 4 | A11Y-01 | `outline: none` on `:focus-visible` leaves only box-shadow | frontend-audit.md | 5 min | `commercial-polish.css:309-311` add `outline: 2px solid var(--skyyrose-accent); outline-offset: 2px;` | Zero |
| 5 | PDP-01 | Cross-sell "Save 10%" badge violates brand canon | senior-craft-audit.md | 10 min | Remove "Complete the Look" block from PDP template OR disable in WC settings | Zero |
| 6 | PDP-02 | Size chips decorative — no form binding | senior-craft-audit.md | 30 min | Wire `<span class="sr-ed__size">` to WC variation form OR replace with native `<select name="attribute_pa_size">` | Low |
| 7 | TY-01 | No `woocommerce/checkout/thankyou.php` brand-voice override | checkout-ux-audit.md | 30 min | Create `woocommerce/checkout/thankyou.php` with founder-voice copy | Zero |
| 8 | PERF-01 | WC session cookie defeats Batcache → 1.5s TTFB sitewide | perf-audit.md | 30 min | 8-line filter in `inc/woocommerce.php` suppressing WC session cookie on non-cart/checkout pages | Medium (cart/checkout regression test required) |
| 9 | PERF-02 | PDP preloads 2.44MB JPEG instead of AVIF/WebP sibling | perf-audit.md | 30 min | Wire existing `skyyrose_avif_sibling_pair()` (`inc/performance.php:757`) into PDP preload emission in `inc/enqueue.php` | Low |
| 10 | PERF-03 | Homepage LCP element is CSS background-image | perf-audit.md | 45 min | Convert hero div to `<img loading="eager" fetchpriority="high">` in `front-page.php` | Low |

**SEO P0s (DEAD):** P0-A JSON-LD absent + P0-B OG/Twitter absent — both invalidated post-synthesis by direct curl. Real residual finding: homepage emits duplicate `og:type` (`article` + `website`) — moved to P3 below.

---

## 2. Sprint 1 Plan — "12-Hour Ship Cut"

Goal: every P0 closed, deployed, verified live in one work-day.

### Phase A: Zero-deploy admin changes (5 minutes total)
| Step | Action | Owner |
|------|--------|-------|
| 1 | wp-admin → Settings → General → Site Title → "SkyyRose" (corroborated by `og:site_name` curl) | Founder or admin |
| 2 | wp-admin → Pages → Cart → swap from Elementor Canvas to default OR replace HTML widget with `[woocommerce_cart]` shortcode | Founder or admin |
| 3 | Validate Site Title via `curl -s https://skyyrose.co/ \| grep og:site_name` (expect "SkyyRose"); validate cart via `curl -s https://skyyrose.co/cart/ \| grep -c "woocommerce-cart-form"` (expect ≥ 1) | Self |

**No deploy required.** Both are wp-admin operations + curl verifies. Yoast/schema step removed — verified working live.

### Phase B: Single bundled deploy (one PR, one deploy window)
Branch: `fix/audit-2026-05-23-p0-sprint`

| Commit | Files | Test |
|--------|-------|------|
| `fix(a11y): restore focus-visible outline` | `wordpress-theme/skyyrose-flagship/assets/css/commercial-polish.css` | Tab through homepage nav |
| `fix(pdp): remove cross-sell save-10 badge — brand canon` | `template-parts/product/related.php` or wherever block emits | curl PDP HTML, grep absent |
| `fix(pdp): wire size chips to variation form` | `template-parts/product/size-chips.php` + `assets/js/single-product.js` | Manual add-to-cart test |
| `feat(wc): brand-voice thankyou template` | new `woocommerce/checkout/thankyou.php` | Place test order |
| `perf(cache): suppress WC session cookie on non-cart pages` | `inc/woocommerce.php` (8-line filter) | curl -I, check `x-cache: HIT` on second request |
| `perf(pdp): preload AVIF/WebP sibling instead of raw JPEG` | `inc/enqueue.php` (wire `skyyrose_avif_sibling_pair`) | curl PDP HTML, verify preload href ends `.avif` or `.webp` |
| `perf(home): img-tag LCP hero w/ fetchpriority` | `front-page.php` | Lighthouse LCP element check |

**Single deploy via `wordpress-theme && npm run deploy`** with post-verify (already in `deploy-theme.sh`).

### Phase C: Post-deploy verification (15 minutes)
- Homepage HTTP 200 + size ≥ 50KB (auto via `verify_live` in deploy-theme.sh)
- Cart page renders `<form class="woocommerce-cart-form">` (curl + grep)
- PDP preload tag href ends `.avif` or `.webp` (curl + grep)
- Second-hit homepage: `x-cache: HIT` (curl -I twice)
- Place test order, screenshot thank-you page

---

## 3. Sprint 2 Plan — "High-Impact Hardening" (estimated 2 days)

| ID | Title | Sprint cost | Source |
|----|-------|-------------|--------|
| SEC-06 | `smart-showcase.js:34` innerHTML → createElement | 2h | security-audit.md |
| SEC-07 | `immersive-wc-bridge.js:56` innerHTML → DOMParser | 1h | security-audit.md |
| SEC-09 | `sr_ref` cookie SameSite=Lax | 10m | security-audit.md |
| UX-P1 | inputmode + enterkeyhint on checkout form fields | 1h | checkout-ux-audit.md |
| SEO-P1-a | Add `og:image:width/height` for fallback image | 30m | seo-audit.md |
| SEO-P1-b | Variable product price guard for OG `product:price:amount` | 15m | seo-audit.md |
| SEO-P1-c | robots.txt Disallow cart/checkout/my-account/wishlist | 10m | seo-audit.md |
| SEO-P1-d | Remove cart/checkout/my-account/wishlist from sitemap | 15m | seo-audit.md |
| A11Y-P1 | Skip link href fix (`#primary` → `#content`) + scroll-padding | 20m | frontend-audit.md |
| A11Y-P1-b | Crimson `#DC143C` body text fails AA (3.97:1) | 30m (palette decision) | frontend-audit.md |
| A11Y-P1-c | Love Hurts accent-dark `#9B0F2E` fails all (2.36:1) | 30m | frontend-audit.md |
| MOBILE-P1 | Add 375px breakpoint (smallest = 480px currently) | 4h | frontend-audit.md |
| MOBILE-P1-b | Collection font sizes 9–11px → 12px+ | 1h | frontend-audit.md |
| TYPE-P1 | Homepage `--font-heading` undefined → falls to wrong font | 15m | senior-craft-audit.md |
| MOTION-P1 | Landing hero keyframes bypass reduced-motion | 30m | senior-craft-audit.md |
| PERF-P1 | Extend Jetpack Boost async CSS to all templates | 1h | perf-audit.md |
| BUNDLE-P1 | Add `shop-archive` to premium JS skip list when Experience Engine inactive | 15m | frontend-audit.md |

**Total Sprint 2:** ~13–15 hours single dev.

---

## 4. Backlog (Sprint 3+)

- SEC-02 CSP nonce migration (remove `'unsafe-inline'`) — multi-day
- SEC-11 SRI hashes for external CDN scripts
- SEC-05 WP.com support ticket for HSTS pass-through
- SEC-10 SSRF DNS TOCTOU IP-pinning
- SEO-P2-multi (collection H1 hidden keyword headings, brand fallback, PDP meta desc, product title modifier, custom collection breadcrumb)
- SEO-P3 (color/material/category in schema, landing page schema, breadcrumb collection page integration)
- MOTION-P2 motion choreography refinement
- TYPE-P2 type scale unification across templates
- All low-severity items per individual audits

---

## 5. STOP-AND-SHOW Manifest (Phase B deploy)

**Action:** `cd /Users/theceo/DevSkyy/wordpress-theme && npm run deploy`
**Touches:** Production site skyyrose.co
**Cost:** $0 (no paid APIs)
**Reversibility:** Hot-swap deploy (cerebrum: atomic mv, microseconds swap window). Rollback = re-deploy previous theme tarball.
**Files changing in Phase B:**
- `assets/css/commercial-polish.css` (focus-visible outline)
- `template-parts/product/*.php` (PDP cross-sell removal + size chips wiring)
- `assets/js/single-product.js` (size chip form binding)
- `woocommerce/checkout/thankyou.php` (NEW file — brand voice)
- `inc/woocommerce.php` (Batcache session cookie filter)
- `inc/enqueue.php` (PDP AVIF preload wiring)
- `front-page.php` (LCP hero img conversion)

**Verification gate already in deploy-theme.sh** — `verify_live()` curls homepage post-cache-flush, asserts HTTP 200, size ≥ 50KB, no PHP fatal markers. Deploy exits non-zero on failure.

**Requires user explicit "y" or "yes" before dispatch.**

---

## 6. Cerebrum Updates Required Post-Implementation

After Phase B ships, update `/Users/theceo/DevSkyy/CLAUDE.md` Learnings section AND `.wolf/cerebrum.md`:

- "All innerHTML Uses Cleared" claim (cerebrum obs #6378) is stale as of v1.1.2 → update with smart-showcase.js + immersive-wc-bridge.js still active uses
- WP Site Title canonical value = "SkyyRose" (not "The Skyy Rose Collection") — record so future agents don't reintroduce the mismatch
- Cart page must use `[woocommerce_cart]` shortcode template, NOT Elementor HTML widget — Do-Not-Repeat
- Batcache session-cookie filter pattern: document in WordPress Deploy section
- AVIF preload sibling resolver lives in `skyyrose_avif_sibling_pair()` at `inc/performance.php:757` — must be wired into every preload emission, not just selected templates
- PDP size chips MUST bind to WC variation form (Do-Not-Repeat for any future redesign of PDP UI)
- founder-voice thank-you template canonical location: `woocommerce/checkout/thankyou.php` (was missing)

---

## 7. Audit Source Index

| File | Lines | Coverage |
|------|-------|----------|
| frontend-audit.md | 291 | A11y AA+, mobile 375px, JS bundles |
| senior-craft-audit.md | 340 | Typography, motion, PDP+landing CTAs |
| security-audit.md | 339 | CSP, headers, WP hardening, XSS, SSRF |
| seo-audit.md | 241 | Schema, OG, meta, sitemap, robots |
| checkout-ux-audit.md | 220 | Cart, checkout, order-received friction |
| perf-audit.md | 311 | LCP/INP/CLS, cache, fonts, images |
| **Total** | **1742** | 6 dimensions, parallel scope, no overlap |
