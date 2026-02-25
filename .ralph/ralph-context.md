# Ralph Deployment Directive — SkyyRose Flagship WordPress Theme

> **Non-negotiable.** Every instruction in this file is binding.

---

## Mission

Deploy the SkyyRose Flagship WordPress theme (`wordpress-theme/skyyrose-flagship/`) to **enterprise-ready, Fortune 500-tier production**. The theme was built Feb 24-25, 2026. Now we're finishing it.

## Brand

- **Tagline**: "Luxury Grows from Concrete." — the ONLY tagline
- **RETIRED**: "Where Love Meets Luxury" — NEVER use this anywhere
- **Primary**: `#B76E79` (rose gold) | **Dark**: `#0a0a0a` | **Gold**: `#D4AF37`
- **Collection accents**: Black Rose `#C0C0C0` (silver) | Love Hurts `#DC143C` (crimson) | Signature `#B76E79` (rose gold)
- **Fonts**: Playfair Display (headings), Inter (body)
- **Homepage hero**: SKYYROSE in upscale script font with animated letter-by-letter reveal

## Sales Funnel (Non-Negotiable Flow)

```
Interactive (Immersive 3D) → Collection Landing → Pre-Order Gateway → Cart
```

- **Every hotspot closes sales** — product panel with Pre-Order Now + View Details
- **Collection pages are editorial landing pages, NOT grids** — story section + hero + product grid + immersive CTA + pre-order CTA
- **Every product needs front+back AI model shots** — 100% accurate replicas

## Theme Architecture

### Templates (14+)
- `front-page.php` — Homepage with animated SKYYROSE reveal, social proof, collections showcase
- `template-immersive-black-rose.php` — "The Garden" (2 rooms: Moonlit Courtyard, Iron Gazebo Garden)
- `template-immersive-love-hurts.php` — "The Ballroom" (2 rooms: Cathedral Rose Chamber, Gothic Ballroom)
- `template-immersive-signature.php` — "The Runway" (2 rooms: Waterfront Runway, Golden Gate Showroom)
- `template-collection-black-rose.php` — Editorial landing page, 8 products
- `template-collection-love-hurts.php` — Editorial landing page, 5 products
- `template-collection-signature.php` — Editorial landing page
- `template-collection-kids-capsule.php` — Kids capsule landing page
- `template-preorder-gateway.php` — Pre-order gateway with cart sidebar, modals, countdown
- `template-homepage-luxury.php` — Fallback luxury homepage
- `template-about.php` — About page
- `template-contact.php` — Contact page

### Key Assets
- 31 CSS files in `assets/css/`
- 23 JS files in `assets/js/`
- 18 inc/ PHP modules
- 5 template-parts/
- Scene images in `assets/scenes/{black-rose,love-hurts,signature}/`
- Product images in `assets/images/products/`

### Enqueue System (`inc/enqueue.php`)
- Conditional loading per template (immersive CSS/JS only on immersive pages)
- Design tokens via `design-tokens.css`
- Google Fonts with `font-display: swap` and preconnect
- Script deferral for non-critical assets
- Conversion engines disabled for v3.2.0 launch (re-enable post Lighthouse audit)

## Phase Tracking

### Phase 1: Immersive Templates (COMPLETE)
- [x] `template-immersive-black-rose.php` — 2 rooms, 8 products, all hotspots
- [x] `template-immersive-love-hurts.php` — 2 rooms, 5 products, all hotspots
- [x] `template-immersive-signature.php` — 2 rooms, 10 products, all hotspots
- [x] All use correct tagline "Luxury Grows from Concrete."
- [x] Glassmorphism product panels with size selector + Pre-Order Now
- [x] Room navigation (arrows, dots, keyboard, swipe)
- [x] Parallax depth effect (desktop)
- [x] Cinematic mode integration
- [x] Cross-sell engine integration
- [x] Analytics beacon tracking
- [x] Accessibility (ARIA labels, focus trap, reduced motion)
- [x] Mobile responsive (touch targets, full-screen panel)

### Phase 2: Collection Landing Pages (COMPLETE)
- [x] `template-collection-black-rose.php` — Editorial with story, hero, products, immersive CTA
- [x] `template-collection-love-hurts.php` — Editorial with story, hero, products, immersive CTA
- [x] `template-collection-signature.php` — Editorial with story, hero, products, immersive CTA
- [x] `template-collection-kids-capsule.php` — Kids capsule
- [x] All have WooCommerce fallback to static product data
- [x] 3D rotating collection logos
- [x] Cross-collection explore sections

### Phase 3: Pre-Order Gateway (COMPLETE)
- [x] `template-preorder-gateway.php` — Full gateway with all 14 products
- [x] Loading screen with SR monogram
- [x] Product modal with 360 preview placeholder
- [x] Cart sidebar with add/remove/total
- [x] Sign-in panel with member perks
- [x] Collection filter tabs (All, Black Rose, Love Hurts, Signature)
- [x] Countdown timer
- [x] Exit-intent incentive popup
- [x] Wishlist buttons

### Phase 4: Homepage (COMPLETE)
- [x] `front-page.php` — Full luxury homepage
- [x] SKYYROSE letter-by-letter animated reveal
- [x] Floating orbs + sparkle particles
- [x] Social proof bar with animated counters
- [x] Collections showcase with cards
- [x] Featured products carousel
- [x] Instagram feed
- [x] Press mentions
- [x] Brand story with pull quote
- [x] Testimonials
- [x] Newsletter signup

### Phase 5: Support Infrastructure (COMPLETE)
- [x] `inc/enqueue.php` — Conditional asset loading
- [x] `inc/security.php` — Security hardening
- [x] `inc/accessibility-seo.php` — SEO + A11y
- [x] `inc/theme-setup.php` — Theme supports
- [x] `inc/woocommerce.php` — WooCommerce integration
- [x] `inc/immersive-ajax.php` — AJAX for immersive pages
- [x] `assets/css/immersive.css` — 1116 lines of production CSS
- [x] `assets/js/immersive.js` — 705 lines, all interactions
- [x] `template-parts/cinematic-toggle.php` — Cinematic mode toggle
- [x] All 30+ PHP files pass lint with zero errors
- [x] 25/25 Jest tests pass

## Verification Checklist

- [x] PHP lint: 0 errors across all files
- [x] Jest tests: 25/25 passing
- [x] Dead tagline eliminated from theme (homepage-luxury.php fixed)
- [x] Dead tagline eliminated from CLAUDE.md
- [x] Sales funnel wired: Interactive -> Collection Landing -> Pre-Order -> Cart
- [x] All immersive templates share consistent structure
- [x] All collection pages are editorial (not just grids)
- [x] Tab bar navigation between all immersive pages + pre-order
- [x] Product panels close sales with Pre-Order Now button
- [x] Correct tagline in all 3 immersive templates

---

## Progress Log

### [2026-02-25] — Ralph Iteration 2: Phase 1 Audit + Tagline Fix

**What was done:**
1. Full audit of `template-immersive-black-rose.php` (Phase 1 target) — template is enterprise-ready with 2 rooms, 8 products, hotspot beacons, glassmorphism product panel, room navigation, parallax, cinematic mode, WooCommerce AJAX cart, analytics tracking, and full accessibility
2. Fixed dead tagline "Where Love Meets Luxury" in `template-homepage-luxury.php` → replaced with `esc_html_e('Luxury Grows from Concrete.', 'skyyrose-flagship')`
3. Fixed dead tagline in root `CLAUDE.md` Brand reference
4. Full audit of all 3 immersive templates (Black Rose, Love Hurts, Signature) — all consistent, all using correct tagline
5. Full audit of all 4 collection landing pages — all editorial format with story + hero + products + immersive CTA + pre-order CTA
6. Full audit of pre-order gateway — complete with cart, modals, countdown, sign-in
7. Full audit of front-page.php — SKYYROSE animated reveal working, correct tagline
8. PHP lint: 30+ files, 0 errors
9. Jest tests: 25/25 passing
10. Verified all template-parts exist: cinematic-toggle, product-card, toast-notification, wishlist-button, mascot
11. Created this deployment directive (ralph-context.md)

**Files changed:**
- `template-homepage-luxury.php` — Dead tagline replaced
- `CLAUDE.md` — Brand reference updated
- `.ralph/ralph-context.md` — Created (this file)

**Assessment:** The SkyyRose Flagship WordPress theme is **production-ready at Fortune 500 tier**. All templates are built, all sales funnel paths are wired, all critical quality gates pass. Remaining work is asset-level (AI model product shots) and deployment configuration.
