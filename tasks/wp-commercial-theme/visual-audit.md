# skyyrose.co — Live Visual Audit (2026-07-19)

**Method.** All 20 URLs from `pages.txt` loaded live at mobile 390x844 and desktop 1440x900 (40 page loads, headless Chromium / Playwright 1.58.2). Each load ran a DOM metrics probe (header geometry, hero size, h1 + computed fonts, horizontal overflow, broken images, fixed-header overlap, footer, menu toggle), captured console errors, and saved a viewport screenshot to `tasks/wp-commercial-theme/shots/<slug>.<viewport>.png`. 12 screenshots were then read visually (budget-limited), chosen from probe evidence: product-the-fannie (both), pre-order.desktop, privacy-policy.mobile, collections-black-rose.mobile, home (both), shop.desktop, cart.desktop, collections-love-hurts.desktop, about.mobile, landing-black-rose.mobile.

**Evidence caveats (read before acting on any single item).**
1. Screenshots were taken after a lazy-load scroll cycle; on long pages (`scroll-behavior: smooth`) some captures landed mid-page rather than at the top. DOM probe numbers were taken *before* the scroll cycle and are the authoritative above-fold evidence. Shots verified to be at page top: shop, cart, pre-order, product-desktop, home-desktop.
2. Headless Chromium has no GPU: every page logs `THREE.WebGLRenderer: could not create WebGL context` + an **unhandled pageerror**. Real browsers have WebGL, so the 3D scenes presumably render for real users — but the uncaught exception proves there is **no graceful-degradation guard** for WebGL-less clients (see D10).
3. A Lighthouse batch was hitting the site concurrently — no load-speed judgments were made.

**Corrections (Wave 1 triage — 2026-07-19).** Three findings revised after main-thread verification and deeper probes:
- **D3 withdrawn**: `/experiences/` + `/experience-black-rose/` serving collections content is the documented WS3 301 merge (`inc/redirects.php:118-132`, since 1.8.0) — by design, not a defect.
- **D4 withdrawn (false positive)**: the live pre-order page DOES carry the global footer (`#colophon.site-footer` confirmed via cache-busted curl). The probe's `querySelector('footer, .site-footer, [class*="footer"]')` returns the first match in *document order*, which on this page is a `.po-card__footer` product-card element — a probe artifact, not a missing footer. Pre-order drops from FAIL to WARN (smoking-imagery flag D9 stands, founder decision pending).
- **D6 culprit corrected**: the 34px horizontal scroll on privacy-policy mobile is caused by an unwrapped content `<table>` (408px wide at x=16 → right edge 424px; 6 tables on the page), NOT `.mobile-menu__panel` — the panel lives inside a `position:fixed` wrapper, which cannot extend document scroll. The original culprit list matched off-screen fixed elements indiscriminately.

Revised tally (worst of two viewports): **3 FAIL (product, shop desktop, privacy mobile) · 5 WARN · 12 PASS/PASS\*.**

**Positives worth keeping.** Header is a consistent 82px fixed bar (`rgba(17,17,17,.92)`) on all 20 pages with a working, visible mobile menu toggle everywhere. Zero broken images across 40 loads (every `img.complete && naturalWidth===0` check came back clean after settle). Hero image discipline is correct (above-fold `eager` + `fetchpriority=high`, below-fold `lazy`). None of the banned fonts (Playfair/Cormorant/Bebas/Yellowtail/Pacifico/Kaushan) were detected on any page. The 404 page is branded, on-voice ("Oakland taught us to keep moving"), and returns a true 404 status. Wishlist has a real, written empty state.

---

## Per-page results

Verdicts: **PASS** clean · **PASS\*** minor notes · **WARN** clearly sub-commercial · **FAIL** broken / illegible / wrong content. Defect IDs reference the ranked list below.

| URL | Mobile | Desktop | Defects found |
|---|---|---|---|
| `/` | WARN | PASS\* | D5 overlay stack eats ~30% of mobile viewport; D10 WebGL pageerror; body font = Hanken (only page on canon) |
| `/shop/` | WARN | **FAIL** | D2 h1 + content flush at x=0; first product card malformed (thumb + stray "I", no title/price — `shop.desktop.png`); sparse 2-up grid at 1440px; unstyled native sort `<select>`; D7 Inter body |
| `/collections/` | PASS\* | PASS\* | D7 Inter body; first `<p>` computes ui-monospace; hero 42–44% viewport (by design) |
| `/collections/black-rose/` | WARN | PASS | D11 "MOONLIT COURTYARD — COMING SOON." near-empty carousel section (`collections-black-rose.mobile.png`; WebGL caveat 2); probe hero itself is sound (100% vh, lockup 1600w + emblem load) |
| `/collections/love-hurts/` | PASS\* | WARN | D11 "ENTER THE 3D EXPERIENCE" button overlaps "EXPLORE ↓" label; large empty maroon band where scene renders (`collections-love-hurts.desktop.png`; caveats 1–2) |
| `/collections/signature/` | PASS | PASS | Probe clean: hero 100% vh, lockup + emblem, Archivo h1 |
| `/collections/kids-capsule/` | PASS | PASS | Probe clean; teaser hero 100% vh; "Coming Soon" is by design (launch mode) |
| `/product/the-fannie/` | **FAIL** | **FAIL** | **D1 internal dossier leaked as page content**; D12 no h1, no above-fold title/price/CTA on desktop; D14 hCaptcha 401 ×6 (mobile), Google Pay CSP report-only ×11 (desktop) |
| `/cart/` | WARN | WARN | D8 h1 "Shopping Cart", Woo notice and button flush at x=0 (`cart.desktop.png`); stock Woo empty-state copy (contrast with wishlist's custom copy) |
| `/about/` | PASS | PASS | Cinzel display = canon "engraved caps" use; founder/heir content strong (`about.mobile.png`); D15 split-text a11y ("TheStory") |
| `/contact/` | PASS | PASS | Probe clean; 50% hero, Archivo h1 |
| `/faq/` | PASS | PASS | Probe clean; 10K chars of real FAQ content |
| `/pre-order/` | **FAIL** | **FAIL** | D4 global site footer missing (probe matched only a product-card "footer", height 0); D9 hero background = person smoking (`pre-order.desktop.png`) on the money page; first h1 at y=1046/1160 (below fold) |
| `/experiences/` | **FAIL** | **FAIL** | D3 byte-identical to `/collections/` (same title "Collections — Shop All", same content, same 3971/6790px doc height) |
| `/landing-black-rose/` | PASS\* | PASS\* | No h1 anywhere (lockup `<img alt="Black Rose">` carries the title) — a11y/SEO gap; content sections themselves are strong (`landing-black-rose.mobile.png`) |
| `/experience-black-rose/` | **FAIL** | **FAIL** | D3 byte-identical to `/collections/black-rose/` (same title, same 24529/19367px doc height) |
| `/privacy-policy/` | **FAIL** | PASS\* | D6 34px horizontal overflow on mobile from `.mobile-menu__panel` (right edge 722px on a 390px viewport); D13 divergent minimal footer (202px vs 3973px global); "Privacy Policy" heading rendered twice |
| `/wishlist/` | PASS | PASS | Custom empty state with real copy; Archivo h1 |
| `/shipping-returns/` | PASS | PASS | Probe clean |
| `/this-page…404-probe/` | PASS | PASS | True 404 status; branded copy; 96/192px Archivo "404" |

**Tally (worst of two viewports): 6 FAIL · 4 WARN · 10 PASS/PASS\*.**

---

## Ranked defects

### P0 — broken / wrong content in front of customers

**D1 — Internal AI dossier published on the live product page.** `/product/the-fannie/` renders ~124,600 characters of internal spec text as page content: raw unrendered markdown (`A **black PU/faux-leather fanny pack (waist-belt bag / cross-body sling)**`), prompt-engineering language ("NOT a backpack. NOT a tote bag. NOT a duffel. NOT a wristlet."), and per-panel render specs ("**front-body** … **Technique:** stitched. **Color:** black."), set in monospace. Probe: `mainTextLen=124636`; eyes-on: `product-the-fannie.mobile.png`. This is internal pipeline data exposed publicly on the only live product URL in the list — remove/gate the dossier content and restore a real PDP (title, price, size/CTA).

**D2 — Shop page (desktop) is visually broken.** At 1440px: `Shop` h1 (72px, white) starts at x=0 hard against the viewport edge directly under the header (probe `h1 top=80`); the first product card is malformed — small floating thumb, a stray "I" glyph, no title/price/CTA — while the second card renders fully; the grid shows 2 cards across 1440px with a void between; sort control is an unstyled native `<select>`. Evidence: `shop.desktop.png`. This is the main commerce index.

### P1 — clearly sub-commercial

**D3 — [WITHDRAWN, see Corrections]** Documented WS3 301 merge (`inc/redirects.php:118-132`), not duplicate content.

**D4 — [WITHDRAWN, see Corrections]** False positive from an order-sensitive probe selector; `#colophon.site-footer` is present on the live pre-order page.

**D5 — Mobile overlay stack occludes ~30% of the viewport on every page.** Cookie banner (~130px) + fixed bottom tab bar (~90px) + mascot/video widget stack simultaneously on a 844px viewport; the mascot widget is additionally clipped behind the cookie banner (z-order collision — visible in `product-the-fannie.mobile.png`, `privacy-policy.mobile.png`, `collections-black-rose.mobile.png`). Suppress the widget until consent is resolved, and collapse the banner to a single line.

**D6 — Horizontal scroll on privacy policy (mobile).** `scrollWidth` exceeds the 390px viewport by 34px. [CORRECTED — see Corrections]: the cause is an unwrapped content `<table>` (408px wide, right edge at 424px; the page ships 6 raw tables), not the off-canvas menu panel. Fix shipped in Wave 1: `.skr-page__content.entry-content table` now scrolls inside its own box (`assets/css/generic-pages.css`).

**D7 — Body typography is off-canon on 19 of 20 pages.** Computed body font is `Inter, sans-serif` (the declared *fallback*) everywhere except the homepage (`"Hanken Grotesk", sans-serif`). Some templates re-apply Hanken at the element level (`p` on collection pages), but shop, cart, contact, FAQ-intro, legal, wishlist paragraphs all run on Inter. Hanken Grotesk needs to be applied (and loaded) at `body` level in the base stylesheet, not per-template.

**D8 — WooCommerce container has no horizontal padding.** Cart (and shop, same root cause) render h1, notices, and buttons flush at x=0: `cart.desktop.png` shows "Shopping Cart", the empty-cart notice, and RETURN TO SHOP touching the viewport edge. The Woo wrapper template is missing the site container class/padding.

**D9 — Pre-order hero imagery: person smoking on the money page.** `pre-order.desktop.png`: the hero behind the Skyy Rose lockup is a still of a person smoking. Founder call on canon — but ad networks (Meta/Google) and theme marketplaces restrict smoking imagery, which directly constrains paid traffic to the pre-order funnel. Flagging, not unilaterally judging.

### P2 — polish

**D10 — No graceful degradation when WebGL is unavailable.** Every page throws an *uncaught* `Error: Error creating WebGL context` (three.js 0.170 via jsdelivr) in WebGL-less clients, and scene containers render as large empty voids (maroon band on love-hurts desktop; near-empty dark first section on black-rose mobile). Wrap renderer creation in a capability check with a static-image fallback. (Headless caveat: real browsers usually have WebGL — but old GPUs/enterprise browsers/bots don't, and Googlebot renders without GPU.)

**D11 — 3D-scene sections present empty/overlapping intermediate states.** "MOONLIT COURTYARD — COMING SOON." fills the first mobile viewport section on Black Rose with otherwise empty space (`collections-black-rose.mobile.png`); on Love Hurts desktop, "ENTER THE 3D EXPERIENCE" overlaps the "EXPLORE ↓" label (`collections-love-hurts.desktop.png`). Both captured under caveats 1–2 — verify in a GPU browser before fixing, but a "coming soon" placeholder as a collection page's leading section is a merchandising miss regardless.

**D12 — PDP has no h1 and no above-fold buy-box (desktop).** `/product/the-fannie/` desktop viewport is 100% product image — no title, price, or add-to-cart visible without scrolling (`product-the-fannie.desktop.png`); no h1 exists anywhere on the page. Fix together with D1.

**D13 — Footer inconsistency + mobile mega-footer.** Legal pages use a 146–202px minimal footer; all other pages a global footer that is 1842px on desktop and **3973–3980px on mobile (~4.7 viewports of footer)**. Pick one footer identity; cut the mobile footer height.

**D14 — Product-page third-party errors.** hCaptcha `POST /authenticate` → 401 ×6 (mobile) and Google Pay `frame-ancestors` CSP report-only violations ×11 (desktop) fire on the PDP. Not user-visible today, but the hCaptcha 401 means the widget isn't authenticating (check sitekey/domain), and the CSP will break Google Pay if the policy is ever enforced.

**D15 — Split-letter animations garble text for screen readers.** Probed `textContent` on collection/about heroes runs words together: "Thebeautyofthecolorblack…", "TheycalledmeBeast.Theywereright.", "TheStory", "Namedafteradaughter." — per-letter spans with CSS-only spacing. Add `aria-label` with the real sentence and `aria-hidden` on the span soup.

### P3 — nice-to-have

**D16 — Title-tag inconsistency.** "Shop", "Shopping Cart", "The Fannie", "Kids Capsule Collection" lack the `| The Skyy Rose Collection` suffix that all other pages carry.

**D17 — Cookie ACCEPT button carries a permanent gold focus ring** in every capture (autofocus styling), reading as a pushy default; and shop's native sort `<select>` is unstyled against the luxury dark UI.

---

## Suggested fix order

1. D1 + D12 (PDP): gate the dossier, restore a real product template — this is customer-facing wrong content on the only product URL.
2. D2 + D8 (shop/cart Woo container + card template) — one root cause, two P0/P1 pages.
3. D3 (experiences duplicates) + D4 (pre-order footer) — template wiring.
4. D5 + D6 (mobile occlusion + overflow) — mobile usability sweep.
5. D7 (body = Hanken) — one-line-ish CSS canon fix, sitewide payoff.
6. Founder review: D9 (smoking imagery).
7. P2/P3 batch.

Screenshots: `/Users/theceo/DevSkyy/tasks/wp-commercial-theme/shots/` (40 files, `<slug>.<mobile|desktop>.png`).
Raw probe data: `/Users/theceo/.claude/jobs/c6c2b779/tmp/audit-results.json`.
