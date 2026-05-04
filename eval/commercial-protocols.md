---
name: Commercial Protocols Matrix (WP §4)
specified_by: [wp: §4]
phase: 0
test_command: node scripts/measurement/check-commercial-protocols.js
pass_threshold: All 10 sub-tables (4.1-4.10) reviewed; current status documented; owner phase + pass criterion present per row
last_updated: 2026-05-03
last_updated_by: eval-harness (Phase 0)
---

# Commercial Protocols Matrix

Operationalizes WP §4 with a current-status column. Every row is a deliverable; current status is updated as phases progress. **Phase 6 marketplace polish** is when most rows move from PENDING / PARTIAL to PASS.

The full source spec for each row lives in `docs/SKYYROSE_WORDPRESS_PLAN.md` §4 (sub-sections 4.1 through 4.10). This file adds the current-status column and the file-reference column for Skyyrose-specific implementations.

---

## §4.1 — Payments & financial

| Protocol | Owner phase | Current status | Implementation file(s) |
|----------|-------------|----------------|------------------------|
| PCI DSS SAQ-A compliance | P5.10 | PENDING | TBD `docs/compliance.md` (Phase 5.10) |
| Stripe live + test mode | P5.10 | PENDING | TBD `inc/woocommerce-stripe.php` (Phase 5.10) |
| 3DS / SCA strong customer auth | P5.10 | PENDING | Same |
| Apple Pay / Google Pay | P5.10 | PENDING | WC Stripe plugin config |
| PayPal | P5.10 | PENDING | TBD WC PayPal plugin |
| Refund flow | P5.10 | PENDING | WC admin |
| Stripe Tax | P5.10 | PENDING | Stripe dashboard config + WC integration |
| Stripe Radar (fraud) | P5.10 | PENDING | Stripe dashboard config |
| Multi-currency display | P6 | PENDING | TBD geo-detection in `inc/performance.php` or new helper |
| Failed payment recovery | P6 | PENDING (Klaviyo flow exists but not wired to failed-charge event) | `inc/klaviyo-integration.php` extension |

## §4.2 — Privacy, consent, legal

| Protocol | Owner phase | Current status | Implementation file(s) |
|----------|-------------|----------------|------------------------|
| GDPR cookie consent | P3 | PARTIAL — `template-parts/cookie-consent.php` exists, refactor for compliance | `template-parts/cookie-consent.php` |
| CCPA opt-out | P3 | PENDING | Footer link + `inc/privacy.php` (new) |
| Privacy policy | P3.3 | PARTIAL — relies on WP default page, no theme template | New `template-info-page.php` (Phase 3.3) + content review |
| Terms of service | P3.3 | PARTIAL | Same |
| Returns policy | P3.3 | PARTIAL — `template-shipping-returns.php` covers shipping; returns coverage TBD | `template-shipping-returns.php` review |
| Shipping policy | P3.3 | PRESENT — `template-shipping-returns.php` with rates table | Same |
| Age verification | P3 | N/A — not legally required for any product |  |
| Newsletter consent (CAN-SPAM, GDPR Art. 6) | P3 | PARTIAL via Klaviyo; double opt-in for EU TBD | `inc/klaviyo-integration.php` |
| Cookie audit | P6 | PENDING | `docs/privacy-cookies.md` (new) |
| Data retention policy | P6 | PENDING | `docs/data-retention.md` (new) |

## §4.3 — Accessibility (WCAG 2.2 AA — non-negotiable)

| Protocol | Owner phase | Current status | Implementation file(s) |
|----------|-------------|----------------|------------------------|
| Color contrast 4.5:1 (normal text) | P6 | PENDING audit | All `assets/css/*.css` |
| Keyboard navigation | P6 | PARTIAL — needs sweep | All interactive components |
| Focus visible | P6 | PARTIAL | `assets/css/design-tokens.css` focus-ring tokens |
| Screen reader landmarks | P6 | PARTIAL | `header.php`, `footer.php`, all template-parts |
| Alt text on every image | P6 | PARTIAL | Catalog data + template-parts/figure.php (new Phase 0) |
| Form labels | P6 | PARTIAL | `template-parts/components/form.php` (new Phase 0) |
| Skip-to-content link | P6 | PENDING | `header.php` |
| Motion-reduced fallback | P6 | PENDING | `assets/css/animations-premium.css` audit |
| Heading hierarchy | P6 | PENDING audit | Per-page audit |
| Captioned video | P6 | N/A unless video added |  |

## §4.4 — SEO

| Protocol | Owner phase | Current status | Implementation file(s) |
|----------|-------------|----------------|------------------------|
| JSON-LD: Organization | P6 | PRESENT via `inc/seo.php` | `inc/seo.php` |
| JSON-LD: Product | P6 | PRESENT | Same |
| JSON-LD: BreadcrumbList | P6 | PENDING (Phase 1.5 builds breadcrumbs.php) | `inc/breadcrumbs.php` (new Phase 1.5) |
| JSON-LD: FAQPage | P6 | PENDING | `template-faq.php` extension |
| JSON-LD: Review/AggregateRating | P6 | PENDING | `inc/seo.php` extension |
| Canonical tags | P6 | PARTIAL via WP defaults | `inc/seo.php` audit |
| XML sitemap | P6 | PARTIAL (WP default + Yoast/Rank Math if installed) | Plugin config |
| robots.txt | P6 | PENDING audit | WP virtual robots.txt |
| OpenGraph + Twitter cards | P6 | PRESENT via `inc/seo.php` | `inc/seo.php` |
| Meta descriptions | P6 | PARTIAL | `inc/seo.php` per-page logic |
| Image alt text doubles as SEO | P6 | PARTIAL (catalog has alt text fields) | `data/skyyrose-catalog.csv` |
| URL hierarchy | P6 | PARTIAL — `/collections/<slug>/`, `/products/<slug>/` working | Permalink config |
| Mobile-first indexing | P6 | PARTIAL | Audit per-page |

## §4.5 — Performance (Core Web Vitals)

| Protocol | Target | Current status | Verified by |
|----------|--------|----------------|-------------|
| LCP (mobile) | < 2.5s | PENDING measurement Phase 0.5 | PageSpeed Insights |
| LCP (desktop) | < 1.8s | Same | Same |
| CLS | < 0.1 | Same | Same |
| INP | < 200ms | Same | Same |
| TTFB | < 600ms | Same | Same |
| Initial JS budget | < 200KB compressed | PENDING audit | Webpack analyzer / built-in |
| Initial CSS budget | < 100KB compressed | PENDING audit | Same |
| Image budget | LCP < 200KB; lazy-load below fold | PARTIAL — AVIF support in `inc/performance.php` | `inc/performance.php` |
| Font budget | < 100KB; `font-display: swap` | PRESENT — self-hosted woff2 + theme.json declarations | `assets/fonts/`, `theme.json` |
| Third-party script audit | Every script justified; total < 300KB | PENDING `eval/scripts-audit.md` | `inc/enqueue.php` audit |

## §4.6 — Conversion infrastructure

| Protocol | Owner phase | Current status | Implementation file(s) |
|----------|-------------|----------------|------------------------|
| GA4 measurement | P6.6 | ABSENT in WP theme | New `inc/analytics-ga4.php` (Phase 6.6) |
| Meta Pixel + CAPI | P6.6 | PARTIAL — Pixel present in `inc/facebook-sdk.php`, CAPI TBD | `inc/facebook-sdk.php` extension |
| Google Ads conversion tracking | P6.6 | PENDING (only if ads run) | `inc/analytics-google-ads.php` (new) |
| TikTok Pixel | P6.6 | PENDING (only if ads run) | `inc/analytics-tiktok.php` (new) |
| Klaviyo onsite tracking | P6.6 | PRESENT via `inc/klaviyo-integration.php` | Existing — verify events fire |
| Abandoned cart recovery | P6 | PARTIAL — Klaviyo flow exists in `skyyrose-email-flows` skill | Klaviyo flow build |
| Browse abandonment | P6 | PENDING | Same |
| Welcome flow | P6 | PARTIAL | Same |
| Post-purchase flow | P6 | PARTIAL | Same |
| Replenishment / re-engagement | P6 | PENDING | Same |
| Wishlist persistence | P6 | PRESENT via `page-wishlist.php` for logged-in; cookie for guests TBD | `page-wishlist.php` + new wishlist JS |
| Email capture without lightbox | P6 | PRESENT in footer (assumed); embedded post-purchase TBD | `template-parts/footer/main.php` (Phase 1.5) |
| Exit-intent capture | P6 | PENDING (desktop only, one-time per session, tasteful) | New JS module |

## §4.7 — Trust signals

| Signal | Where | Current status | Implementation |
|--------|-------|----------------|----------------|
| Customer reviews | PDP | PARTIAL via WC reviews | Phase 5.3 redesigns as editorial pulled-quote |
| Press mentions | Homepage + about | PENDING | Phase 4 + Phase 6 about page redesign |
| Founder voice | About | PENDING — Corey on the page as person | Phase 4 about page (`template-about.php`) |
| Made-with detail | PDP | PARTIAL via dossier system | Existing `data/dossiers/<slug>.md` + Phase 5.3 PDP narrative |
| Sustainability claims | If made | PENDING | Phase 6 — only if made specifically |
| Care instructions | PDP | PARTIAL via dossier | Phase 5.3 PDP narrative |
| Size/fit info | PDP | PARTIAL via `template-parts/size-guide-modal.php` | Phase 4 redesign per garment |
| Authenticity statement | Header/footer | PENDING — "Made in The Town" or similar | Footer (Phase 1.5) |
| Customer service touchpoint | Footer + chat | PARTIAL — email/phone TBD; chat policy TBD | Footer (Phase 1.5) + `inc/contact.php` (new) |
| Returns confidence | Cart + PDP | PENDING — plain-English window near CTA | Phase 5.1 cart redesign + Phase 5.3 PDP |

## §4.8 — Inventory & merchandising

| Protocol | Owner phase | Current status | Implementation |
|----------|-------------|----------------|----------------|
| Low-stock indicator | P6 | PENDING | New WC hook in `inc/woocommerce.php` |
| Sold-out state | P6 | PARTIAL via WC defaults | Phase 5 redesign |
| Restock notification | P6 | PENDING | Klaviyo flow + WC trigger |
| Pre-order labeling | P5.4 | PRESENT via `inc/woocommerce-preorder.php` | Existing |
| Drop countdown | P5.4 | PARTIAL via `template-preorder-gateway.php` | Phase 5.4 extends to drop-day |
| Cross-sell on PDP | P6 | PARTIAL via `template-parts/complete-the-look.php` | Phase 5.3 hand-curate (not algorithmic) |
| Cart upsell | P6 | PENDING | Phase 5.1 cart redesign |
| Abandoned cart hold | P6 | PENDING — items reserved 1 hour | Custom WC logic |
| Bundle pricing | P6 | PENDING (only if applicable) | WC product config |
| Gift card | P6 | PENDING | WC gift card plugin + landing page |

## §4.9 — Customer experience

| Protocol | Owner phase | Current status | Implementation |
|----------|-------------|----------------|----------------|
| Order confirmation page | P5 | PENDING — branded, not WC default | WC override |
| Order confirmation email | P5 | PENDING — branded HTML | WC email override + Klaviyo |
| Shipping notification | P5 | PARTIAL via WC defaults | Klaviyo override |
| Delivered notification | P5 | PARTIAL | Same |
| Return request flow | P5 | PENDING — self-serve from /my-account/orders/ | Custom WC integration |
| Account dashboard | P6 | PARTIAL — uses WC defaults | Branded redesign Phase 6 |
| Wishlist | P6 | PRESENT in `page-wishlist.php`; persistent + shareable URL TBD | Phase 6 |
| Saved addresses | P5 | PARTIAL via WC defaults | Verify one-click checkout |
| Guest checkout | P5 | PARTIAL | Verify allowed; no forced account creation |

## §4.10 — Measurement & analytics provisioning

| Data source | Owner | Current status | Verification node |
|-------------|-------|----------------|-------------------|
| Google Analytics 4 | both | PENDING | Phase 0.5 — `scripts/measurement/verify-ga4.js` |
| Google Search Console | both | PENDING | Phase 0.5 — `verify-gsc.js` |
| Google Tag Manager | both | PENDING (no `gtag` / `GTM-` in WP theme) | Phase 0.5 |
| WooCommerce REST API | claude-code | PENDING — autonomous provision | Phase 0.5 — `verify-wc.js` |
| Klaviyo API | claude-code | PRESENT via existing integration + MCP | Phase 0.5 — `verify-klaviyo.js` |
| Stripe API | claude-code | PRESENT via existing MCP | Phase 0.5 — `verify-stripe.js` |
| Meta Business / Pixel + CAPI | both | PARTIAL (Pixel only via `inc/facebook-sdk.php`; CAPI TBD) | Phase 0.5 — `verify-meta.js` |
| TikTok Pixel | both | N/A unless ads run | Phase 0.5 — `verify-tiktok.js` |
| Google Ads | both | N/A unless ads run | Phase 0.5 — `verify-gads.js` |
| Hotjar / Microsoft Clarity (heatmaps) | claude-code | PENDING | Phase 0.5 install + verify |
| Sentry | both | PENDING (added per grill) | Phase 0.5 — `verify-sentry.js` |

---

## Test command

```bash
node scripts/measurement/check-commercial-protocols.js
```

Reads this file and any per-protocol implementation status notes. Exits 0 if all rows are either PASS, PRESENT, N/A, or have a documented Phase ownership; exits 1 if any row is "PENDING" past its owner phase's exit. Phase 7 ship-check requires ZERO PENDING rows for the gates to pass.

---

## Phase entry checklist

- Phase 0 establishes the matrix (this file) with current status per row
- Phase 5 sub-phases drive payments, customer experience, and integration rows
- Phase 6 marketplace polish drives the bulk of remaining PENDING → PASS transitions
- Phase 7 ship-check requires every row PASS / PRESENT / N/A — zero PENDING allowed at ship gate
