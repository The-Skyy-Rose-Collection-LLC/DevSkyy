# A11y / SEO / Best-Practices Fixlist — skyyrose.co baseline

**Auditor**: Access (Accessibility + SEO) · **Date**: 2026-07-19 · **Standard**: WCAG 2.2 AA + Lighthouse
**Input**: `tasks/wp-commercial-theme/baseline/*.json` (20 URLs × mobile+desktop, live capture) — no re-crawl performed.
**Theme source**: `/Users/theceo/DevSkyy/wordpress-theme/skyyrose-flagship/` (all file:line refs below are relative to this root).

**DIAGNOSIS ONLY — no code was edited.** 16 distinct root-cause fixes cover every failing audit.

> ⚠️ **Live-vs-source drift detected**: the baseline was captured from production, and for at least 3 flagged elements the *current source tree already contains a fix* that hasn't deployed (marked `[DRIFT — verify post-deploy]` below). Production serves `.min` builds — every CSS fix here requires `npm run build` + deploy before it counts (see `theme-min-build` rule).

---

## Failing-audit inventory (grouped, deduped)

Lighthouse a11y audit weights: aria-allowed-attr **10**, aria-required-children **10**, aria-required-parent **10**, aria-prohibited-attr **7**, color-contrast **7**, heading-order **3**, aria-allowed-role **1**, label-content-name-mismatch **0**.

| # | Audit | Cat | Weight | Page-runs affected |
|---|-------|-----|--------|--------------------|
| A1 | aria-allowed-role | a11y | 1 | 14 (black-rose, love-hurts, signature, experience-BR, landing-BR, pre-order, shop × m+d) |
| A2 | aria-required-children | a11y | 10 | 8 (black-rose, signature, experience-BR, landing-BR × m+d) |
| A3 | aria-required-parent | a11y | 10 | 2 (shop m+d) |
| A4 | aria-allowed-attr | a11y | 10 | 2 (pre-order m+d) |
| A5 | aria-prohibited-attr | a11y | 7 | 12 (about, black-rose, kids-capsule, love-hurts, signature, experience-BR × m+d) |
| A6 | color-contrast | a11y | 7 | **38 — every page** |
| A7 | heading-order | a11y | 3 | 2 (shop m+d) |
| A8 | label-content-name-mismatch | a11y | 0 | 14 (home, shop, 4 collection/landing pages × m+d) |
| B1 | third-party-cookies | bp | 5 | 4 (cart, product/the-fannie × m+d) |
| B2 | inspector-issues (Cookie) | bp | 1 | 8 (cart, about, privacy-policy, PDP × m+d) |
| B3 | errors-in-console | bp | 1 | 4 (black-rose, love-hurts, signature, experience-BR — mobile only) |
| B4 | image-aspect-ratio | bp | 1 | 3 (pre-order m+d, landing-BR desktop) |
| S1 | is-crawlable (noindex) | seo | ~4/13 | 2 (cart m+d) — **ACCEPTED-BY-DESIGN** |
| S2 | crawlable-anchors | seo | 1 | 2 (privacy-policy m+d) |

Measurement gap: `faq.desktop.json` has `runtimeError: NO_NAVSTART` → its BP/perf categories are null. Not a site defect; re-run Lighthouse on that URL when re-baselining.

---

## P0 — blocks ≥90 on a category

### FIX-1 — Remove bogus `role="list"` / `role="listitem"` from product grids and cards
**Audits cleared**: A1 (w1) + A2 (w10) + A3 (w10) — the entire cascade shares one root cause.
**Pages unblocked**: shop 90→~97, collections/black-rose 89→~96, signature 89→~96, experience-black-rose 89→~96, landing-black-rose 92→~96 (m+d each).
**Evidence**:
- `<article class="v7card" role="listitem" …>` — axe rejects `listitem` on `article` (A1). Because the role is invalid, axe resolves the card to non-listitem, so the parent `div.product-grid__items[role="list"]` "has children which are not allowed: a[aria-label], h3[tabindex], [role=radiogroup], button[aria-label]" (A2).
- On `/shop/` the same card sits inside native `ul.products > li.product`, so `article[role="listitem"]`'s parent is a `li` (implicit listitem), not a list → "Required ARIA parent role not present: list" (A3).
**Source**:
- `template-parts/product-card-v7-lookbook.php:54` — delete ` role="listitem"` from the `<article>`.
- `template-parts/product-grid.php:274` — delete ` role="list"` from `.product-grid__items` (a styled div grid needs no list semantics; if list semantics are wanted later, render `ul`/`li` natively instead).
**Risk**: none — removes incorrect ARIA; native semantics (`ul/li` on shop, plain grid elsewhere) remain intact. Do NOT touch `template-parts/about/collections-grid.php:78-91` or `template-parts/contact/faq-list.php:32-35` (their role pairs are valid and unflagged).

### FIX-2 — Pre-order gateway: drop `role="list"/"listitem"` so `aria-pressed` becomes valid
**Audits cleared**: A4 (w10) + A1 on pre-order. **Pages unblocked**: pre-order 92→~97 (m+d).
**Evidence**: `<button … role="listitem" aria-pressed="true">` — `aria-pressed` is not allowed on role `listitem` ("ARIA attribute is not allowed: aria-pressed"), and `listitem` is not allowed on `button`.
**Source**: `template-preorder-gateway.php:184` (`role="list"` on `.po-gateway__panels`) and `template-preorder-gateway.php:249` (`role="listitem"` on the `.po-panel` buttons).
**Fix**: delete both role attributes. The buttons keep their native role and `aria-pressed` (toggle semantics) becomes legal.
**Risk**: none. (`front-page.php:453` uses `aria-pressed` on a plain button — correctly — and is not flagged.)

### FIX-3 — Split-text engine writes `aria-label` onto `<p>` elements (prohibited ARIA)
**Audits cleared**: A5 (w7). **Pages unblocked**: about 94→~97+, kids-capsule 93→~96, love-hurts 93→~96, and contributes to black-rose/signature/experience-BR reaching 95+ alongside FIX-1.
**Evidence**: runtime DOM shows `<p class="abt-community__manifesto rv rv-split-line …" aria-label="Deep East·The Hills·…">`, `<p class="col-hero__tagline rv-split-word …" aria-label="The beauty of the color black…">`, `<p class="kc-teaser__quote-text rv-split-word" aria-label="Named after a daughter…">` — "aria-label attribute cannot be used on a p with no valid role attribute."
**Source**: `assets/js/premium-interactions.js:53`, `:72`, `:88` — `splitChars`/`splitWords`/`splitLines` each do `el.setAttribute('aria-label', text)` before wrapping the text in `aria-hidden` spans. (Templates `template-parts/about/community.php:43`, `template-parts/collection/page.php` hero tagline, `template-parts/kids-capsule/teaser.php` only carry the `rv-split-*` classes; the ARIA is injected by JS.)
**Fix (one place, all three functions)**: instead of `aria-label` on the parent, prepend a visually-hidden span holding the full text (`<span class="sr-only">{text}</span>`) and keep the animated spans `aria-hidden="true"`. Screen readers read the sr-only copy; no prohibited ARIA. Rebuild `premium-interactions.min.js`.
**Risk**: low — verify an `.sr-only`/`.screen-reader-text` utility class exists in the base CSS (WordPress ships `.screen-reader-text`); no visual change.

### FIX-4 — Rose-gold button surfaces: white ink on `#B76E79` = 3.8:1 (needs 4.5:1)
**Audits cleared**: the dominant share of A6 (w7) — this exact pair is flagged on **all 19 pages** via the cookie-consent banner, plus footer newsletter, contact submit, and product quick-add buttons.
**Evidence**: "insufficient color contrast of 3.8 (foreground #ffffff, background #b76e79)" — `button#skyyrose-cookie-accept` (every page), `.footer-newsletter__submit`, `.contact-form__submit-text`, `.v7card__quickadd` (live), `p.return-to-shop > a.button.wc-backward` (cart).
**Source (confirmed in-source offenders)**:
- `assets/css/cookie-consent.css:82-86` — `.cookie-consent__btn--accept { background: var(--color-rose-gold,#B76E79); color: var(--color-text-primary,#fff); }`
- `assets/css/footer.css:67-75` — `.footer-newsletter__submit { background: var(--skyyrose-accent,#B76E79); color:#fff; }`
- `assets/css/woocommerce.css:155-161` — `.skyy-product-card__actions .add_to_cart_button { background: var(--skyy-woo-accent); color:#fff; }` (`--skyy-woo-accent` = `#B76E79`, `woocommerce.css:28`)
- Contact submit: `assets/css/contact.css` submit button block (white on accent).
- `[DRIFT — verify post-deploy]`: `.col-newsletter__submit` (`collection-pages.css:500` — source is now `#fff` bg / `#000` ink) and `.kc-waitlist-form__btn` (`kids-capsule.css:324` — source is now `#E8A0BF`/`#171310`) both already pass in source; live still serves the old white-on-rose-gold build. `.v7card__quickadd` (`product-card-v7.css:151-169`) is also transparent-bg in source vs filled rose gold live.
**Fix — pick ONE, apply everywhere (⚑ FOUNDER VISIBILITY — brand-token adjacent)**:
- **Option A (recommended)**: keep the `#B76E79` surface, switch button ink to `#0A0A0A` → **5.20:1** ✓. Matches the existing hover pattern (gold bg + dark ink on cookie-accept hover) and leaves the brand token untouched.
- **Option B**: keep white ink, darken button surface to `#A4626C` → **4.62:1** ✓ (smallest luminance shift of rose gold that passes; still reads rose gold). Define as `--skyyrose-accent-btn` in `assets/css/design-tokens.css` (accent tokens at `:253`) so the identity token `#B76E79` is untouched for borders/accents/large display text.
**Risk**: visual-brand sensitive; founder should pick A or B. Either way rebuild all touched `.min` files.

### FIX-5 — Cart + PDP third-party cookies (Stripe / hCaptcha / Google Pay) — DECISION REQUIRED
**Audits cleared**: B1 (w5) + most of B2 (w1). **Pages unblocked**: cart BP 78/79→96+, product/the-fannie BP 78/79→96+. **This is the only path to BP ≥90 on these pages.**
**Evidence** (exact, from `details.items` — note: these BP scores are **not** console errors):
- cart: cookie set by `https://m.stripe.com/6` (name `m`).
- PDP: cookies from `https://hcaptcha.com/1/api.js` (`__cf_bm`), `https://m.stripe.com/6` (`m`), `https://api2.hcaptcha.com/checksiteconfig…` (`__cflb`), `https://api.hcaptcha.com/getcaptcha/…` (`__cflb`); plus `pay.google.com/gp/p/js/pay.js` frames (inspector-issues).
**Source**: not theme code — WooCommerce Stripe gateway express-checkout (loads `m.stripe.com` + Google Pay on PDP/cart) and the hCaptcha plugin (PDP review form). 
**Fix**: scope the gateway's express-pay buttons and hCaptcha to checkout only (gateway settings, or `wp_dequeue_script` on non-checkout pages via a small mu-plugin/`inc/` hook). **Trade-off**: removes one-tap Apple/Google Pay from PDP/cart — conversion-relevant, founder must approve. If declined, mark B1 ACCEPTED and note cart/PDP BP ceiling ≈78.
**Risk**: medium (checkout UX) — do not change without approval.

---

## P1 — blocks ≥95 (a11y) / 100 (seo)

### FIX-6 — Love Hurts crimson `#DC143C` as small-text ink on dark = 3.78:1
**Audits cleared**: remainder of A6 on love-hurts (93→96+ with FIX-3/4) and about.
**Evidence**: `.v7card__eyebrow` (10px), `.v7card__price` (20px), `.v7card__quickadd` ink — `#DC143C` on `#111111` = 3.78 (needs 4.5); `.abt-coll-row__tag` `#DC143C` on `#0A0A0A` = 3.96.
**Source**: `assets/css/product-card-v7.css:11` (`--v7-accent:#DC143C` for `[data-collection="love-hurts"]`, consumed as text color at `:118` eyebrow, `:123` price, `:160` quickadd) and `assets/css/about.css:921` (`.abt-coll-row[data-collection="love-hurts"] .abt-coll-row__tag { color:#DC143C }`).
**Fix (⚑ FOUNDER VISIBILITY — brand token)**: introduce a text-only variant `--v7-accent-text:#E8305A` for love-hurts (4.50:1 on `#111`, 4.72:1 on `#0A0A0A` — minimal luminance lift, unmistakably still the Love Hurts crimson) and use it for eyebrow/price/quickadd ink + the about tag. Keep `#DC143C` for surfaces, borders, badges, large display text.
**Risk**: brand-sensitive; smallest shift that passes. Surfaces keep the exact canon crimson.

### FIX-7 — `v7card__badge` dark ink on crimson badge = 3.96:1 (love-hurts only)
**Evidence**: `.v7card__badge` fg `#0A0A0A` on bg `#DC143C`, 10px → 3.96 (needs 4.5).
**Source**: `assets/css/product-card-v7.css:102-112` (badge bg = `var(--v7-accent)`).
**Fix**: per-collection badge ink — for `[data-collection="love-hurts"]` set badge `color:#fff` → **4.99:1** ✓. Silver (`#C0C0C0`) and gold (`#D4AF37`) badges must KEEP dark ink (white would fail on those).
**Risk**: none.

### FIX-8 — About page grays and labels (about 94 → 97+ with FIX-3)
**Evidence / Source / Fix** (all in `assets/css/about.css`):
- `:835` `.abt-coll-row__index` — `rgba(245,241,235,0.32)` on `#0A0A0A` = 2.61 at 36px (large text needs 3:1) → raise alpha to **0.38** (≈3.06 ✓).
- `:381` `.abt-mission .abt-chapter__label` — computes `#74726f` on cream `#F5F1EB` = 4.26 → darken to ≥ `#6E6C69` (4.65 ✓).
- `:542` `.abt-community__label` — `var(--skyyrose-accent)` `#B76E79` on cream = 3.38 → local override `#96545F` (5.00 ✓) for light-background context. ⚑ rose-gold-on-cream fails everywhere; consider a `--skyyrose-accent-on-light` token.
- Love-hurts tag at `:921` — covered by FIX-6.
**Risk**: low; page-local.

### FIX-9 — Pre-order hero CTA: cream on silver = 1.48:1 (worst contrast on the site)
**Evidence**: `.po-btn.po-btn--primary` fg `#F5E6D3` on bg `#C0C0C0` at 11.5px — 1.48:1, effectively invisible text.
**Source**: `assets/css/preorder-gateway.css:241-246` — `.po-btn--primary { background: var(--po-accent); color: var(--po-bg); }`. In the hero's themed context `--po-accent` resolves to silver `#C0C0C0` and `--po-bg` to cream (vars at `preorder-gateway.css:16-20` + per-collection overrides `:37-38`).
**Fix**: hard-set `color:#0A0A0A` on `.po-btn--primary`/`--primary-sm` (dark ink on silver = **10.88:1** ✓, on gold/rose also passes). Don't rely on `--po-bg` for ink.
**Risk**: none — restores legibility.

### FIX-10 — Shop heading skip: first product card `<h3>` follows page `<h1>`
**Evidence**: `h3.holo__name` (first holo card in the shop loop) — "Heading order invalid" (h1→h3, no h2). Shop only, w3.
**Source**: `template-parts/product-card-holo.php:111` (`<h3 class="holo__name">`); loop entry `woocommerce/archive-product.php` (~line 50-61, `woocommerce_before_shop_loop`).
**Fix**: output a visually-hidden `<h2 class="screen-reader-text">Products</h2>` before the product loop in `woocommerce/archive-product.php` (or on the `woocommerce_before_shop_loop` hook). Do not demote card headings — they're h3 consistently, which is correct once an h2 exists.
**Risk**: none.

### FIX-11 — Collections/experiences index numerals + home press strip + contact form dimming
Smaller color-contrast stragglers (each page-local, all part of A6):
- `assets/css/collections-index.css:84-89` — `.ci-card__num` `rgba(237,230,223,0.4)` on `#0F0F0F` = 3.31 at 12px → alpha **0.55** (≈4.9 ✓). Fixes collections + experiences pages (a11y 97 each).
- `assets/css/homepage-v2.css:441-448` — `.press-item` `var(--haze)` (`rgba(255,255,255,.55)`, `:22`) × `opacity:.75` = effective `#6C6C6C` on `#050505` = 3.88. The comment "AA contrast at rest" is **wrong** (it cleared 3:1, not 4.5:1). Raise to `opacity:.88` (effective ≈4.9 ✓) or drop opacity and set `--haze` to `.62`.
- `assets/css/contact.css:307-309` — `.contact-form__group--order-number.is-hidden { opacity:.4 }` leaves a *visible, focusable, low-contrast* labeled input (label 2.41:1, placeholder 3.7:1). Fix: add `visibility:hidden` to `.is-hidden` (transition-safe) so the dimmed state is truly hidden from view and AT; also raise `::placeholder` (`contact.css:389-391`) from `rgba(255,255,255,.5)` to `.6`.
**Risk**: none — decorative/utility text only.

### FIX-12 — privacy-policy SEO 92: href-less anchor from Jetpack Likes
**Evidence**: `<a class="sd-link-color">` inside `div#like-post-wrapper-…` — "Links are not crawlable" (S2, w1). Plugin-injected (Jetpack Likes/Sharedaddy), not theme markup.
**Fix**: disable Jetpack Likes on pages (Jetpack → Settings → Sharing, or `add_filter('wpl_is_likes_visible','__return_false')` scoped to pages) — takes privacy-policy SEO 92→100. Also removes the wp.com widgets cookie flagged in B2 for this page.
**Risk**: low — removes the "Like" button UI from pages; confirm founder doesn't want it.

### S1 — cart SEO 69: `noindex` — **ACCEPTED-BY-DESIGN, do not "fix"**
**Evidence**: `<meta name="robots" content="max-image-preview:large, noindex, follow" />` on `/cart/` → is-crawlable fails (weight ~4/13 → 69).
**Source**: WooCommerce core noindexes cart/checkout/account (theme's own `inc/seo.php:965-970` only noindexes search/404/attachment — confirmed not the source). Correct SEO practice for a cart page. **Mark accepted; cart SEO will never be 100 and that's right.** Team scoring should exclude cart SEO from the ≥90 gate or accept 69.

---

## P2 — polish toward 100

### FIX-13 — Permissions-Policy blocks the theme's own gyro parallax (console error)
**Audits cleared**: B3 — the single failing BP audit on the four 96-score mobile collection runs.
**Evidence**: "Permissions policy violation: accelerometer is not allowed in this document." from `assets/js/system/immersive-core.min.js?ver=1.11.1` (col 6035).
**Source**: `inc/security.php:102` sends `Permissions-Policy: … accelerometer=(), gyroscope=() …` while `assets/js/system/immersive-core.js:281` adds a `deviceorientation` listener on touch devices (`hover:none` path, `:250`).
**Fix**: change the header to `accelerometer=(self), gyroscope=(self)` (first-party only — third parties stay blocked), OR gate the listener with `document.featurePolicy?.allowsFeature('accelerometer')`. Header change is 1 line and restores the intended mobile parallax.
**Risk**: none — `(self)` still blocks third-party frames.

### FIX-14 — Distorted image dimensions (BP 96 on pre-order m+d, landing-BR desktop)
**Evidence + Source**:
- `template-preorder-gateway.php:362` — collection lockup `<img … width="200" height="60">`; the lockup PNGs aren't 10:3, so rendered ratio ≠ natural.
- `template-preorder-gateway.php:751+` — email-capture logo `width="200" height="200"` (logo not square).
- `template-landing-black-rose.php:223-227` — `.lp-pane__mobile-img` `width="480" height="600"` on square product renders (also present in `template-landing-love-hurts.php:230`, `template-landing-signature.php:224` — fix all three; only BR desktop was flagged because the others' mobile imgs weren't visible at capture).
**Fix**: CSS one-liners — `.po-grid__lockup img, .po-email-capture__art img { height:auto; }` and `.lp-pane__mobile-img { object-fit:contain; }` (or correct the width/height attrs to the assets' real ratios). Keep width/height attributes present (CLS).
**Risk**: none.

### FIX-15 — `aria-label` overrides that drop the visible text (A8, weight 0 — no score impact, real AT impact)
**Evidence**: "Text inside the element is not included in the accessible name" — e.g. `a.v7card__frame[aria-label="BLACK is Beautiful Jersey Series: …"]`, `button.holo__buy[aria-label="Add … to cart"]`, `a.kc-heir__stage[aria-label="You were born into the rose — …"]` (home), `.col-crossnav__link[aria-label="Explore the … collection"]`.
**Source**: `template-parts/product-card-v7-lookbook.php` (frame link), `template-parts/product-card-holo.php` (buy button), `front-page.php` (kc-heir stage link), `template-parts/collection/page.php:318` (crossnav links).
**Fix**: ensure each `aria-label` *starts with* the element's visible text, or drop the `aria-label` and use visible text + sr-only suffix. Voice-control users ("click BLACK Rose Hoodie") currently can't target these (WCAG 2.5.3 Label in Name).
**Risk**: none.

### FIX-16 — about page YouTube embed cookie (B2 on about, BP 96)
**Evidence**: inspector-issues Cookie from `https://www.youtube.com/embed/Ja11W-g34Zo?…`.
**Source**: `template-parts/about/featured-video.php:38` (and the same pattern at `template-parts/about/press-section.php:72`).
**Fix**: swap embed host to `https://www.youtube-nocookie.com/embed/…` (also trim `allow="accelerometer; …"` to what's needed). One-line, removes the cookie issue.
**Risk**: none.

---

## What's working well (preserve)
- Landmark/heading structure is clean everywhere except the shop h2 gap; skip links and `focus-visible` outlines are consistently present (`cookie-consent.css:77`, `product-card-v7.css:37`, `footer.css:295`).
- `press-item` and `col-newsletter` show prior deliberate contrast work — right instinct, ratios just short of 4.5:1.
- SEO is 100 on 17/19 pages; structured data and crawlability are solid. Home/contact/faq/wishlist/shipping a11y ≥97 need only FIX-4's cookie banner to move.
- Native `ul.products > li` on shop is correct — FIX-1 removes the ARIA fighting it, not the semantics.

## Score projections after all P0+P1 fixes
- a11y: every page ≥96 (remaining decimals are label-mismatch w0 + rounding); the five 89-93 pages all clear 95.
- BP: 100 on all theme-controlled pages; cart/PDP reach ≥96 **only if** FIX-5 is approved, else stay ~78.
- SEO: 100 everywhere except cart 69 (accepted-by-design).

## Verification protocol (post-fix)
1. Rebuild every touched `.min` (`npm run build` in `wordpress-theme/`) — production serves `.min` only.
2. Re-run Lighthouse on the 9 sub-95-a11y pages + cart + PDP + pre-order, mobile+desktop; re-run faq desktop (NO_NAVSTART gap).
3. Manual: keyboard-walk the pre-order gateway (aria-pressed toggles announce), VoiceOver pass on a collection grid (cards announce as links/articles, no ghost list), cookie banner button legibility eyes-on.
