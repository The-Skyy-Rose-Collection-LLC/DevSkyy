# Ralph Deployment Directive — SkyyRose WordPress Theme

> **NEVER DELETE THIS FILE.** Ralph reads it at the start of every iteration.

## Mission

Deploy the SkyyRose Flagship WordPress theme (`wordpress-theme/skyyrose-flagship/`) to
enterprise-ready, Fortune 500-tier production quality. The theme was built Feb 24-25, 2026.
Now we're finishing it — page by page, enterprise-grade.

## Brand Rules (Non-Negotiable)

- **Tagline**: "Luxury Grows from Concrete." — the ONLY tagline
- **RETIRED**: "Where Love Meets Luxury" — NEVER use this, it's dead
- **Primary color**: `#B76E79` (rose gold)
- **Dark**: `#0a0a0a`
- **Gold accent**: `#D4AF37`
- **Homepage hero**: SKYYROSE in upscale script font with animated letter-by-letter reveal

## Sales Funnel (The Money Path)

```
Interactive (Immersive) → Collection Landing → Pre-Order Gateway → Cart
```

Every hotspot closes sales. Every CTA drives toward pre-order.

## Collection Pages = Editorial Landing Pages (NOT Grids)

Collection pages are editorial landing pages with:
- Full-bleed hero with scene background + 3D rotating logo
- Editorial story section (italic, centered, atmospheric)
- Product showcase (cards with hover effects)
- Immersive experience CTA
- Pre-order CTA with conversion intelligence
- Cross-collection navigation

They are NOT WooCommerce product archive grids.

## Collections

| Collection | Immersive Theme | Accent Color |
|-----------|----------------|--------------|
| Black Rose | "The Garden" (gothic cathedral garden) | Silver #C0C0C0 |
| Love Hurts | "The Ballroom" (cathedral + gothic ballroom) | Crimson #DC143C |
| Signature | "The Runway" (waterfront + showroom) | Rose Gold #B76E79 |

## Template Structure

### Immersive Pages (3D Storytelling — NOT shopping)
- `template-immersive-black-rose.php` — 2 rooms, 8 products
- `template-immersive-love-hurts.php` — 2 rooms, 5 products
- `template-immersive-signature.php` — 2 rooms, 10 products

### Collection Landing Pages (Editorial — NOT grids)
- `template-collection-black-rose.php` — 8 products
- `template-collection-love-hurts.php` — 5 products
- `template-collection-signature.php` — 12 products
- `template-collection-kids-capsule.php` — TBD

### Sales Pages
- `template-preorder-gateway.php` — 14 products, cart sidebar, sign-in panel
- `front-page.php` — Homepage with hero, collections, social proof

## Context7 Protocol

ALWAYS `resolve-library-id` → `query-docs` BEFORE writing any library code.

## Quality Standards

- Every product needs front+back AI model shots — 100% accurate replicas
- PHP 8.0+ strict, all output escaped (esc_html, esc_attr, esc_url)
- WCAG 2.1 AA accessibility (ARIA labels, focus traps, keyboard nav)
- `pytest -v` after EVERY file touch
- Enterprise CSS: design tokens, responsive, reduced motion

---

## Progress Log

### Iterations 1-13 (Feb 25, 2026)

**Completed:**
- All 3 immersive templates (Black Rose, Love Hurts, Signature) — multi-room scenes, hotspots, product panels, room navigation, keyboard nav, touch/swipe, parallax, cinematic mode
- All 3 collection landing pages — hero, story, product grid, immersive CTA, pre-order CTA, cross-collection nav
- Pre-order gateway — full product catalog, cart sidebar, sign-in panel, incentive popup, countdown timer
- Homepage — hero with animated SKYYROSE reveal, collections showcase, social proof
- `immersive.js` — comprehensive: room transitions, hotspot interactions, product panel slide-up, WooCommerce AJAX add-to-cart, analytics events
- `conversion-engine.js` — social proof, urgency, scarcity indicators
- `enqueue.php` — conditional loading per template, performance-optimized with defer
- Brand mascot, luxury cursor, cinematic mode toggle
- WooCommerce overrides (cart, checkout, single product, archive)
- Security headers, SEO, accessibility modules
- 31 CSS files, 24 JS files, 26 product images, 13 3D scene renders

### Iteration 14 (Current)

**Focus:** Enterprise quality audit and fixes

**Fixed:**
1. **CSS class mismatch (CRITICAL BUG)**: `collections.css` defined accent colors on `.collection-black-rose` (single dash) but templates use `.collection--black-rose` (double dash BEM). Added dual selectors so both conventions work.
2. **Placeholder products removed**: Signature collection had `sg-013` and `sg-014` with SKU as product name and "details forthcoming" description. Removed — not enterprise-ready.
3. **Missing `<main>` landmark**: All 3 collection landing pages were missing `<main id="primary">` semantic wrapper. Added for WCAG 2.1 AA compliance.
4. **Missing CSS styles**: Added `.collection-hero__cta` button styling and `.collection-explore` section styles to `collection-logos.css`.
5. **`collection-colors.css` not enqueued**: Color scheme CSS for per-collection theming was defined but never loaded on collection pages. Added to `skyyrose_enqueue_collection_logos()`.
6. **Version string hardcoded**: `collection-logos.css` was enqueued with hardcoded `'3.0.0'` instead of `SKYYROSE_VERSION` constant. Fixed.
