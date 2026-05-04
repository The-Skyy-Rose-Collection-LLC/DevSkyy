---
name: Marketplace Readiness Checklist
specified_by: [v2: §5 Phase 0, §5 Phase 6]
phase: 0
test_command: node scripts/measurement/run-marketplace-eval.js  # PHASE 0.5 DELIVERABLE — script does not exist yet; running it will exit 1 with a 'Phase 0.5 not started' message until the runner is built. See scripts/measurement/README.md.
pass_threshold: 100% green across all checklist rows
last_updated: 2026-05-03
last_updated_by: eval-harness (Phase 0)
---

# Marketplace Readiness Checklist

Comprehensive readiness rubric for the V2 build, applied during Phase 6 (polish) and re-run at Phase 7 ship-check. **TF submission is out of scope** per V2 §12 — this checklist exists for production readiness on `skyyrose.co`, not for ThemeForest review.

## Categories

### One-click demo install

| Row | Pass criterion |
|-----|----------------|
| `blueprints/skyyrose-demo-setup.json` covers every page template | Manifest includes every `template-*.php` with seed content |
| Demo install completes without errors on a fresh WP.com Business site | Verified via test site (Phase 6.1 deliverable) |
| All collection products import correctly | 33+ SKUs from `data/skyyrose-catalog.csv` populate as WC products |
| All immersive worlds load on demo install | 3D worlds initialize on `/experience-*` pages |

### Accessibility (WCAG 2.2 AA — non-negotiable)

| Row | Pass criterion |
|-----|----------------|
| Color contrast 4.5:1 (normal text) | Audit every collection palette; failures fixed |
| Keyboard navigation | Every interactive element reachable + activatable via keyboard |
| Focus visible | Every focused element has a visible indicator that respects the design |
| Screen reader landmarks | Header, nav, main, footer correctly tagged; ARIA where semantic HTML insufficient |
| Alt text on every image | Decorative = `alt=""`; content = descriptive |
| Form labels | Every input has an associated label, not just placeholder |
| Skip-to-content link | Visible on focus; jumps to `<main>` |
| Motion-reduced fallback | `prefers-reduced-motion` honored on every animation, including Three.js scenes |
| Heading hierarchy | One H1 per page; no skipped levels |
| Captioned video | Any video on the site has captions |
| WebGL keyboard nav | Immersive scenes are keyboard-navigable (orbit / zoom via arrow keys + +/-) |

### Performance budget

| Row | Pass criterion |
|-----|----------------|
| Mobile LCP | < 2.5s |
| Desktop LCP | < 1.8s |
| CLS | < 0.1 |
| INP | < 200ms |
| TTFB | < 600ms |
| Initial JS | < 200KB compressed |
| Initial CSS | < 100KB compressed |
| LCP image | < 200KB; lazy-load below fold |
| Font budget | < 100KB; `font-display: swap` |
| Third-party script audit | Every script has a justification; total < 300KB |
| Test under load | 5 plugins + 50-product cart + Klaviyo embed + reviews — all targets still met |

### Demo coverage

| Row | Pass criterion |
|-----|----------------|
| Every page template has demo content authored | Verified via Phase 6.1 audit |
| Every collection has product photography | Verified via catalog audit (Phase 0 dossier alignment) |
| Every immersive world has a working scene | Phase 5.2/5.8 deliverables |
| Every drop template has at least one example drop authored | Phase 5.4 deliverable |
| Every email flow has draft template authored | Phase 5.4 + 6 via `skyyrose-email-flows` |

### Documentation

| Row | Pass criterion |
|-----|----------------|
| 11 existing HTML docs in `docs/` audited and current | Phase 6.2 deliverable |
| Drop setup doc | Authored Phase 6.2 |
| WebGL config doc | Authored Phase 6.2 |
| AR config doc | Authored Phase 6.2 |
| Semantic search config doc | Authored Phase 6.2 |
| Style-quiz authoring doc | Authored Phase 6.2 |
| Compliance doc | `docs/compliance.md` covers PCI SAQ-A (Phase 5.10) |
| Data retention doc | `docs/data-retention.md` covers WP §4.2 |

### Conversion infrastructure

| Row | Pass criterion |
|-----|----------------|
| GA4 measurement | Installed via GTM; e-commerce events fire |
| Meta Pixel + CAPI | Server-side dedup with browser pixel |
| Google Ads conversion tracking (if running) | Purchase event fires on order confirmation |
| TikTok Pixel (if running) | Installed |
| LinkedIn Insight Tag (if running) | Installed |
| Klaviyo onsite tracking | view-product, add-to-cart, started-checkout fire |
| Abandoned cart recovery | 3-email Klaviyo flow live |
| Welcome flow | 5-email series live |
| Post-purchase flow | 4-email series live |
| Replenishment / re-engagement | 30/60/90d flows live |

### SEO

| Row | Pass criterion |
|-----|----------------|
| JSON-LD: Organization on every page | Validates against schema.org |
| JSON-LD: Product on every PDP | Price, availability, SKU, images, brand |
| JSON-LD: BreadcrumbList | On every nested page |
| JSON-LD: FAQPage | On `template-faq.php` |
| JSON-LD: Review/AggregateRating | On PDPs with reviews |
| Canonical tags | Every page; collection variants point to base URL |
| XML sitemap | Auto-generated, submitted to Google Search Console |
| robots.txt | Excludes /cart, /checkout, /my-account, /wp-admin |
| OpenGraph + Twitter cards | Every page has og:title, og:description, og:image (1200x630) |
| Meta descriptions | Every page < 160 chars; written, not auto-generated |

### Privacy / consent / legal

| Row | Pass criterion |
|-----|----------------|
| GDPR cookie consent | Banner with Accept/Reject/Customize; no non-essential cookies until consent |
| CCPA opt-out | "Do Not Sell My Personal Information" link in footer; honors request |
| Privacy policy | Reviewed; lawyer-readable |
| Terms of service | Returns/refunds/IP/dispute clauses present |
| Returns policy | Plain-English; window in days; condition reqs; who pays return shipping |
| Shipping policy | Times by region; carrier; tracking; signature requirement on high-value |
| Newsletter consent | Double opt-in for EU; clear unsubscribe |
| Cookie audit | Every cookie listed in privacy policy with purpose and expiry |
| Data retention policy | Documented; aligned with platform defaults |

### Payments

Per WP §4.1 — see `eval/integrations.md` for Stripe-specific scoring.

| Row | Pass criterion |
|-----|----------------|
| PCI DSS SAQ-A compliance | Stripe-hosted fields; no card data on WP server; documented |
| Stripe live + test mode | Test charge $0.50 succeeds in test |
| 3DS / SCA strong customer auth | EU-card test triggers 3DS challenge; flow completes |
| Apple Pay / Google Pay | Buttons appear on iOS/Android in WC checkout; tap-to-pay completes |
| PayPal | PayPal Smart Button on cart + checkout; sandbox txn completes |
| Refund flow | Admin can refund; customer email auto-fires |
| Stripe Tax | US sales tax auto-calc on checkout based on shipping state |
| Stripe Radar (fraud) | Default rules enabled; high-risk orders flagged |

## Test command

```bash
node scripts/measurement/run-marketplace-eval.js
```

Exits 0 on 100% PASS, 1 on any FAIL with diagnostic output listing failed rows.

## Phase entry checklist

Phase 6 (marketplace polish) drives every row from "PENDING" to "PASS." Phase 7 ship-check re-runs and gates deploy on 100% green.
