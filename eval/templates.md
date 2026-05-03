# Eval — Templates

> Pass/fail rubric for every template type. Phase 4 + 5 builds and Phase 3 consolidations are graded against this. Each criterion is observable — every "PASS" must be defensible with evidence (screenshot, lighthouse run, e2e test, curl response).

## Universal criteria — apply to every template

| ID | Criterion | Method |
|----|-----------|--------|
| U1 | Loads with HTTP 200, response ≥ 50KB | `curl -s -o /dev/null -w "%{http_code} %{size_download}\n" <url>` |
| U2 | Zero PHP errors in response body | grep response body for "Fatal error", "Parse error", "Call to undefined", "There has been a critical error" |
| U3 | Zero JS console errors on page load | Playwright `page.on('console')` listener, fail on `error` level |
| U4 | All images load without 404 | Playwright network listener, fail on any image request returning 4xx/5xx |
| U5 | All internal links resolve | Crawler check on every `<a href>` pointing to `skyyrose.co/*` |
| U6 | Self-hosted fonts only (no Google CDN) | grep response for `fonts.googleapis.com` or `fonts.gstatic.com` — must be 0 |
| U7 | Mobile LCP < 2.5s on iPhone 13 emulation | Lighthouse mobile run |
| U8 | Mobile CLS < 0.1 | Lighthouse |
| U9 | Mobile INP < 200ms | Lighthouse / Chrome DevTools |
| U10 | WCAG 2.2 AA color contrast on every text element | axe-core scan, zero violations of `color-contrast` |
| U11 | Keyboard-navigable (every interactive element reachable via Tab) | Playwright keyboard scan |
| U12 | Screen reader landmarks present (`<main>`, `<nav>`, `<header>`, `<footer>`) | DOM check |
| U13 | Brand voice compliance (no banned phrases per `eval/brand.md`) | grep |
| U14 | No emoji unless explicitly part of brand spec | grep against unicode emoji ranges |
| U15 | Holo cards (where rendered) animate smoothly at 60fps | Chrome perf timeline |

---

## Per-template-type criteria

### Front page (`front-page.php`)
- F1: Three.js portals render in < 2s after DOMContentLoaded
- F2: Three particle systems active (one per collection ring)
- F3: All 4 collections discoverable from above-the-fold
- F4: SkyyRose avatar easter egg present (per CLAUDE.md spec — find all 3 = intro unlocks)
- F5: Scroll-reveal triggers fire as expected (no IntersectionObserver leaks)

### About page (`template-about.php`)
- A1: Brand timeline renders with no broken images
- A2: GSAP scroll triggers fire and clean up on unmount
- A3: Press links open in new tab with `rel="noopener noreferrer"`

### Contact page (`template-contact.php`)
- C1: Form validates client-side (required fields)
- C2: Form submission creates Klaviyo event (verify via Klaviyo MCP `klaviyo_get_events`)
- C3: Honeypot or reCAPTCHA active (no spam submissions)
- C4: Success state UI renders, error state UI renders

### FAQ + Shipping-Returns + Info pages (`template-info-page.php`, `template-faq.php`, `template-shipping-returns.php`)
- I1: Reading time visible on hero
- I2: Smooth-scroll TOC functional
- I3: Anchor links share-able (`#section` deep links work)
- I4: Quiet premium aesthetic — minimal motion, generous spacing
- I5: Print stylesheet renders cleanly (legal pages)

### Collection pages (4 — `template-collection-*.php`)
- COL1: Per-collection palette swap via `data-collection` attribute resolves
- COL2: IntersectionObserver `.col-reveal` triggers (no GSAP — theme rule)
- COL3: Holo cards link to product detail pages
- COL4: Pre-order banner shows when collection has any pre-order SKU
- COL5: Sort/filter works (no full page reload — AJAX or JS)

### Immersive pages (4 — `template-immersive-*.php`)
- IMM1: Three.js scene loads in < 3s
- IMM2: Beacon hotspots match catalog SKUs (no orphan beacons)
- IMM3: Click on beacon opens product modal/drawer
- IMM4: Skyy avatar renders if scene includes it (post `skyy.glb` rig fix)
- IMM5: Performance: 60fps on M1 MacBook Air, 30fps minimum on iPhone 13
- IMM6: Reduced-motion preference respected (static fallback)
- IMM7: WebXR session button visible on supported devices (post Phase 5.8)

### Landing pages (3 — `template-landing-*.php`)
- LP1: All 10 sections render (press, story, parallax, editorial, reviews, craft, cta, hero, product-grid, faq)
- LP2: `.lp-rv` scroll-reveal triggers (no GSAP)
- LP3: CTA pill button has working magnetic hover (desktop only)
- LP4: Per-collection palette swap functional
- LP5: Time-to-add-to-cart < 60s on usability test

### Pre-order / Drop templates (`template-preorder-gateway.php`, `template-drop-day.php`, `template-drop-live.php`)
- DRP1: Countdown renders correctly across timezones
- DRP2: Klaviyo waitlist subscribe fires on form submit
- DRP3: Drop-live: queue position UI updates via WebSocket every 5s
- DRP4: Sold-out state UI renders cleanly
- DRP5: Email "drop is live" arrives < 30s after server-side unlock
- DRP6: Stress test: 1000 concurrent waitlist users → unlock-to-cart < 500ms p95

### Wishlist (`page-wishlist.php`)
- W1: Add/remove from wishlist persists across sessions (cookie or user account)
- W2: Wishlist accessible from header on all pages
- W3: Item count badge updates instantly
- W4: Empty state UI renders with CTA to shop

### Product pages (standard + narrative)
- P1: Product image carousel works (touch swipe on mobile, click on desktop)
- P2: Variant selector updates price + availability
- P3: Add-to-cart fires WC AJAX, no full page reload
- P4: Sticky add-to-cart on mobile after first scroll
- P5: Schema.org Product JSON-LD valid (Google Rich Results test)
- P6: Narrative variant only — chapter scroll sequence intact, CTA at chapter 4

### WebGL product canvas (Phase 5.2)
- WGL1: Canvas initializes in < 1s
- WGL2: 60fps on M1 MacBook Air
- WGL3: 30fps minimum on iPhone 13
- WGL4: Scroll-pinned camera moves match design spec
- WGL5: Mobile fallback: 3-photo swipe gallery loads if WebGL unsupported
- WGL6: Memory: < 200MB heap after 5 minutes of interaction (no leaks)

### Cart + Checkout (block-based)
- CK1: Block cart loads without flash of unstyled content
- CK2: Block checkout loads without FOUC
- CK3: Stripe element renders within block context
- CK4: Apple Pay / Google Pay express buttons render on supported browsers
- CK5: Field validation: zip code, email, card number, CVV
- CK6: Successful test charge in test mode → order created in WP admin
- CK7: 3DS challenge handled gracefully
- CK8: Refund flow works from order admin

### Style quiz (`template-style-quiz.php`)
- SQ1: 5-7 question flow with progress indicator
- SQ2: Each answer animates between questions
- SQ3: Result screen shows curated 3-5 product set
- SQ4: One-click "Add all to cart" works
- SQ5: Retake button restores quiz to question 1
- SQ6: Klaviyo profile updated with quiz answers (segment for re-targeting)

### Experiences hub (`template-experiences.php`)
- EXP1: All 4 immersive worlds visible (cards or beacons)
- EXP2: Hover/tap reveals collection palette + entry button
- EXP3: Direct link to each immersive page
- EXP4: SkyyRose avatar easter-egg counter visible (3/3 = unlocked)

### Spatial / WebXR landing (`template-spatial-home.php`)
- SP1: Device detection: shows VR button on Vision Pro / Quest 3, AR button on iOS / Android (via WebXR or AR Quick Look)
- SP2: Falls back to standard 3D viewer on unsupported devices
- SP3: WebXR session start works on supported browser/device combos
- SP4: Hand-tracking controls functional (no gamepad requirement)

### Skyyrose canvas (`skyyrose-canvas.php`) — builder shell
- BC1: Loads brand tokens + fonts but no theme content chrome
- BC2: Elementor / Divi / Beaver / Bricks can render full content
- BC3: No layout shifts caused by theme stylesheets

### 404 (`404.php`)
- E1: Editorial deep-dark hero renders
- E2: Search input functional from 404
- E3: "Back to home" CTA works
- E4: Suggested products load (3 random featured)

### Search (`search.php`)
- S1: Standard `s=` query returns relevant results
- S2: Pinecone semantic results render when API available (Phase 5.7)
- S3: Falls back to WP search if Pinecone unavailable
- S4: Empty results state renders with suggestions

---

## Eval execution protocol

For every PR / phase exit:
1. Run universal criteria against every template
2. Run per-template criteria against modified templates
3. Generate `eval-results-<phase>-<timestamp>.json` with PASS/FAIL per criterion
4. Block phase exit on any FAIL — fix or explicitly waive with user approval

Storage: `eval/results/` directory. Each run timestamped.
