# Eval — Marketplace Readiness

> The "fully integrated, working on all cylinders" checklist. Excludes ThemeForest submission per user directive, but every other quality pillar holds.

## Demo install

| ID | Criterion | Method |
|----|-----------|--------|
| DEM1 | Fresh WP 6.8 install + WC + theme + `blueprints/skyyrose-demo-setup.json` import → working storefront in < 5 min | Manual on staging |
| DEM2 | Demo includes published pages for every page-template type (front, about, contact, faq, shipping-returns, info, collection x4, immersive x4, landing x3, preorder, wishlist, experiences, style-quiz, spatial) | Verify after blueprint import |
| DEM3 | Demo includes 3-5 sample products per collection, with images, descriptions, variants | Verify |
| DEM4 | Demo navigation menu populated and matches design | Verify |
| DEM5 | Demo theme.json color presets, font presets, block patterns all loadable | Verify |
| DEM6 | Demo install instructions in `docs/demo-install.html` | File exists |

## Documentation

| ID | Criterion | Method |
|----|-----------|--------|
| DOC1 | Every page template documented with: purpose, where it appears, customization knobs | `docs/templates/*.html` |
| DOC2 | Every integration documented: setup steps, env vars / WP options needed, troubleshooting | `docs/integrations/*.html` |
| DOC3 | Drop-mechanics setup guide: end-to-end T-30 → T+7 process | `docs/drop-setup.html` |
| DOC4 | WebGL configuration guide: scene authoring, beacon hotspot placement | `docs/webgl-config.html` |
| DOC5 | AR config guide: FASHN setup, cost caps, fallback behavior | `docs/ar-config.html` |
| DOC6 | Semantic search guide: Pinecone index setup, embedding model choice, fallback | `docs/semantic-search.html` |
| DOC7 | Style quiz authoring guide: question structure, scoring, product mapping | `docs/style-quiz.html` |
| DOC8 | Multi-builder support: Elementor / Divi / Beaver / Bricks compat notes | `docs/builders.html` |
| DOC9 | Klaviyo flow setup: which flows, how to wire | `docs/klaviyo-setup.html` |
| DOC10 | Stripe + Apple Pay + Google Pay + PayPal setup | `docs/payments-setup.html` |

## Accessibility (WCAG 2.2 AA)

| ID | Criterion | Method |
|----|-----------|--------|
| ACC1 | axe-core scan on every template returns 0 violations | Playwright + axe |
| ACC2 | Keyboard navigation: every interactive element reachable via Tab | Manual + Playwright |
| ACC3 | Focus visible on every interactive element | CSS audit |
| ACC4 | Skip-to-content link present on every page | DOM check |
| ACC5 | Alt text on every content image (decorative images marked `aria-hidden`) | Crawler |
| ACC6 | Form labels properly associated with inputs | DOM check |
| ACC7 | ARIA landmarks: `main`, `nav`, `header`, `footer`, `complementary` | DOM check |
| ACC8 | Reduced-motion preference respected: GSAP / Three.js degrades gracefully | Manual on `prefers-reduced-motion: reduce` |
| ACC9 | Screen reader walkthrough on home page → product → cart → checkout completes without confusion | Manual NVDA / VoiceOver |
| ACC10 | Color contrast ≥ 4.5:1 for body, ≥ 3:1 for large text | axe |
| ACC11 | WebGL canvas has text fallback for screen readers (image-alt-style description) | DOM check |
| ACC12 | Form error messages announced to screen readers (`aria-live`) | Manual |

## Performance budget

| ID | Criterion | Method |
|----|-----------|--------|
| PERF1 | Front page LCP < 2.5s on iPhone 13 emulation, real network | Lighthouse mobile |
| PERF2 | Front page CLS < 0.1 | Lighthouse |
| PERF3 | Front page INP < 200ms | Chrome DevTools |
| PERF4 | Collection page LCP < 2.0s | Lighthouse |
| PERF5 | Product page LCP < 2.0s | Lighthouse |
| PERF6 | Cart/checkout LCP < 1.5s | Lighthouse |
| PERF7 | Initial JS bundle < 200KB compressed for non-immersive templates | Bundle analyzer |
| PERF8 | Initial CSS < 50KB compressed for any template | Network panel |
| PERF9 | Total page weight < 1.5MB compressed for non-immersive templates | Network panel |
| PERF10 | Real-world load test: 5 plugins + 50-product cart + Klaviyo embed → still meets PERF1-9 | Manual |
| PERF11 | Lighthouse mobile score ≥ 85 on every public template | Automated |
| PERF12 | Smart asset loading: collection-pages.css NOT loaded on non-collection pages | Network panel |

## Compatibility

| ID | Criterion | Method |
|----|-----------|--------|
| CMP1 | WP 6.8+ compatible | `Tested up to:` in style.css + actual install |
| CMP2 | WC 8.x, 9.x, 10.x compatible | Test install with each |
| CMP3 | PHP 8.2+ compatible (PHPCS WordPress standard) | `npm run lint:php` |
| CMP4 | WPML / Polylang compatible (text-domain `skyyrose`, all strings translatable) | grep `__()`, `_e()`, `_x()` |
| CMP5 | RTL stylesheet present and functional | Test with `dir="rtl"` |
| CMP6 | Multi-builder: Elementor active → no theme conflicts | Manual |
| CMP7 | Multi-builder: Divi active → no theme conflicts | Manual |
| CMP8 | Multi-builder: Beaver Builder active → no theme conflicts | Manual |
| CMP9 | Multi-builder: Bricks active → no theme conflicts | Manual |
| CMP10 | Block editor (Gutenberg / FSE) compatible — theme.json valid | wp-cli theme.json validate (or block editor preview) |

## Security

| ID | Criterion | Method |
|----|-----------|--------|
| SEC1 | CSP headers active and not bypassable | curl `-D -` |
| SEC2 | All output escaped (PHPCS Generic.PHP.NoSilencedErrors) | PHPCS |
| SEC3 | No `wpdb->query()` without `prepare()` | grep + manual review |
| SEC4 | Nonce + capability checks on every write action | grep `wp_verify_nonce`, `current_user_can` |
| SEC5 | No secrets in source code | gitleaks scan |
| SEC6 | API keys for FASHN, Stripe, Pinecone, Klaviyo all in WP options or env vars | Manual |
| SEC7 | Frame-busting headers prevent clickjacking | curl `-D -` |
| SEC8 | Subresource integrity on any CDN-loaded asset (none expected — self-hosted) | Source check |

## Marketplace metadata

| ID | Criterion | Method |
|----|-----------|--------|
| MKT1 | `style.css` header complete: Theme Name, Version, Description, Author, Author URI, License, Tags | View file |
| MKT2 | Author URI points to a real seller profile (user supplies; not skyyrose.co) | View file |
| MKT3 | License: GPLv2 or later, file `license.txt` present | File exists |
| MKT4 | `readme.txt` present with installation / changelog / FAQ | File exists |
| MKT5 | Theme screenshot at 1200x900 (`screenshot.png`) | File exists |
| MKT6 | Theme tags follow WordPress.org tag taxonomy (e.g., `e-commerce`, `fashion`, `block-styles`) | View style.css |

## CSS / JS asset splitting

| ID | Criterion | Method |
|----|-----------|--------|
| ASS1 | `inc/enqueue.php` template-slug detection routes correctly | Network panel per template |
| ASS2 | No "global" CSS file > 100KB compressed | Network panel |
| ASS3 | No template loads CSS for a different template type | Network panel audit |
| ASS4 | Conditional script loading — Three.js NOT loaded on non-immersive pages | Network panel |
| ASS5 | Critical CSS inlined for above-the-fold content on every template | View source |

---

## Final acceptance: ship gate

`/ship-check wp` returns SHIP only when:
- Every criterion above is PASS or explicitly waived
- All Phase 5 integration criteria PASS (`eval/integrations.md`)
- Every template criterion PASS (`eval/templates.md`)
- Brand voice criteria PASS (`eval/brand.md`)
- "Shocking" criteria self-rated as honestly hit (`eval/shocking.md`)

Output: `eval/results/marketplace-<timestamp>.json` with FULL pass/fail breakdown. Block deploy on any failure not user-waived.
