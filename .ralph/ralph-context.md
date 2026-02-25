# Ralph Deployment Directive — SkyyRose Flagship WordPress Theme

> **Non-negotiable.** Every instruction in this file is binding.
> **NEVER delete this file.** Update the Progress Log after every iteration.

---

## Mission

Deploy the SkyyRose Flagship WordPress theme (`wordpress-theme/skyyrose-flagship/`) to **enterprise-ready, Fortune 500-tier production**. The theme was built Feb 24-25, 2026. Phases 1-5 are COMPLETE. Now finish Phases 6-8.

## Brand

- **Tagline**: "Luxury Grows from Concrete." — the ONLY tagline
- **RETIRED**: "Where Love Meets Luxury" — NEVER use this anywhere, EVER
- **Primary**: `#B76E79` (rose gold) | **Dark**: `#0a0a0a` | **Gold**: `#D4AF37`
- **Collection accents**: Black Rose `#C0C0C0` (silver) | Love Hurts `#DC143C` (crimson) | Signature `#B76E79` (rose gold)
- **Fonts**: Playfair Display (headings), Inter (body)
- **Homepage hero**: SKYYROSE in upscale script font with animated letter-by-letter reveal

## Sales Funnel (Non-Negotiable Flow)

```
Interactive (Immersive 3D) → Collection Landing → Pre-Order Gateway → Cart
```

---

## CURRENT OBJECTIVE: PHASE 6, 7, 8

Phases 1-5 are COMPLETE. Start Phase 6 NOW.

### Phase 6: WordPress Configuration & Theme Hardening (DO THIS FIRST)

The theme code already has registered nav menus, widget areas, custom logo, and product taxonomy. This phase is about creating the **activation script** and **theme options** that auto-configure WordPress when the theme is activated.

**6A — Theme Activation Hook** (`inc/theme-activation.php`):
Create a one-time activation hook that sets up:
- [ ] Static front page: Set reading settings to use `front-page.php` as the homepage
- [ ] Permalink structure: `/%postname%/` (flush rewrite rules on activation)
- [ ] Create required pages if they don't exist: Shop, Cart, Checkout, My Account, About, Contact, Pre-Order, each collection page, each immersive page
- [ ] Assign WooCommerce pages (shop, cart, checkout, my-account) via `update_option()`
- [ ] Create default navigation menus programmatically:
  - **Primary**: Home, Collections (dropdown: Black Rose, Love Hurts, Signature), Experiences (dropdown: The Garden, The Ballroom, The Runway), Pre-Order, About, Contact
  - **Footer**: About, Contact, FAQ, Shipping & Returns, Privacy Policy, Terms of Service
  - **Mobile**: Same as Primary
- [ ] Set theme mod defaults (custom logo placeholder, color scheme, etc.)

**6B — Product Categories & Tags** (`inc/product-taxonomy.php` — enhance existing):
- [ ] Ensure product categories registered: `black-rose`, `love-hurts`, `signature`, `kids-capsule`
- [ ] Ensure product tags registered: `pre-order`, `limited-edition`, `new-arrival`, `bestseller`, `collaboration`
- [ ] Auto-create WooCommerce product categories on activation if WooCommerce is active

**6C — Commit Uncommitted Work**:
There are uncommitted changes to `template-preorder-gateway.php` and `assets/js/preorder-gateway.js` (WooCommerce AJAX cart integration). Commit these first before starting new work.

**6D — Dead Tagline Cleanup**:
Search the ENTIRE codebase for "Where Love Meets Luxury" and replace every instance with "Luxury Grows from Concrete." — leave no survivors.

### Phase 7: Three Industry-Leading Improvements

After Phase 6, analyze the entire build and apply **3 Fortune 500-level upgrades**. These must be high-impact on sales and brand perception. NOT basic improvements — industry-leading innovations.

Suggestions (pick 3 or propose better ones):
1. **Micro-interaction Sales Engine** — Add haptic-feedback-style micro-animations on every CTA button (pulse on hover, ripple on click, success burst on add-to-cart). Proven to increase conversion 15-25%.
2. **Progressive Loading Cinema** — Implement skeleton screens with rose gold shimmer animation that transition into real content. Each section loads with a cinematic reveal (blur → sharp, dark → lit). Apple-tier loading experience.
3. **Smart Cross-Sell Intelligence** — Add "Customers Also Loved" and "Complete the Look" sections to product panels and modals. Use collection-aware logic (Black Rose items suggest Black Rose, cross-collection for variety). Data-driven upsell.
4. **Immersive Audio Layer** — Ambient audio per collection room (subtle, toggleable): garden sounds for Black Rose, ballroom music for Love Hurts, city ambiance for Signature. With volume control and mute preference saved.
5. **Dynamic Social Proof** — Real-time "X people viewing" indicators on product cards, "Y sold in last 24h" badges, and "Limited Stock" urgency on countdown products.
6. **Accessibility Excellence Package** — WCAG 2.2 AAA compliance across all pages. Screen reader optimization, keyboard navigation perfection, high contrast mode, focus indicators. Industry-leading accessibility.

### Phase 8: Full Verification Loop

Run comprehensive verification across the ENTIRE build:
- [ ] PHP lint: 0 errors across ALL `.php` files
- [ ] Jest tests: ALL passing
- [ ] Every page template renders without PHP warnings/notices
- [ ] Every hotspot in all 3 immersive templates opens product panel correctly
- [ ] Every "Pre-Order Now" button has a working click handler
- [ ] Sales funnel paths verified: Interactive → Collection → Pre-Order → Cart
- [ ] Mobile responsive: all pages tested at 375px, 768px, 1024px, 1440px
- [ ] Accessibility: ARIA labels present, focus traps work, keyboard navigation works
- [ ] SEO: meta descriptions, OG tags, JSON-LD schema on all pages
- [ ] Performance: no render-blocking CSS/JS outside critical path
- [ ] Security: all user inputs escaped, nonces verified, CSP headers configured
- [ ] Tagline: "Luxury Grows from Concrete." everywhere. Zero instances of dead tagline.
- [ ] Brand consistency: colors, fonts, spacing consistent across all pages

---

## Phase Tracking (Phases 1-5 COMPLETE)

### Phase 1: Immersive Templates ✅ COMPLETE
### Phase 2: Collection Landing Pages ✅ COMPLETE
### Phase 3: Pre-Order Gateway ✅ COMPLETE
### Phase 4: Homepage ✅ COMPLETE
### Phase 5: Support Infrastructure ✅ COMPLETE

---

## Theme Architecture Reference

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

### Existing Config (already in code)
- 9 nav menus registered in `inc/theme-setup.php`
- 6 widget areas registered
- Custom logo support enabled
- WooCommerce HPOS declared
- Product taxonomy in `inc/product-taxonomy.php`
- Wishlist CPT registered

---

## Mandatory Protocol

1. **Context7 BEFORE any code** — `resolve-library-id` → `query-docs` for WordPress/WooCommerce
2. **Read before edit** — Always read the file first
3. **PHP lint after every edit** — `php -l <file>`
4. **Update Progress Log** below after every iteration
5. **NEVER delete this file**

---

## Progress Log

### [2026-02-25] — Iterations 1-3: Phases 1-5 Audit + Fixes

**What was done:**
1. Full audit of all 3 immersive templates — enterprise-ready
2. Full audit of all 4 collection landing pages — editorial format confirmed
3. Full audit of pre-order gateway — complete with cart, modals, countdown
4. Full audit of front-page.php — SKYYROSE animated reveal working
5. Fixed dead tagline in `template-homepage-luxury.php` and `CLAUDE.md`
6. Fixed accessibility-seo.php issues
7. Enhanced immersive CSS/JS (parallax, animations, mobile)
8. Added WooCommerce AJAX cart to pre-order gateway (uncommitted)
9. PHP lint: 30+ files, 0 errors
10. Jest tests: 25/25 passing

**Assessment:** Phases 1-5 production-ready. Phase 6-8 are next.

## Context added at 2026-02-25T16:52:33.976Z
STOP READING. START BUILDING. You have been stuck for 4 iterations making no changes. Phase 6 is your target. Create inc/theme-activation.php NOW — a theme activation hook that: (1) creates all required WordPress pages (Home, About, Contact, Pre-Order, Shop, Cart, Checkout, My Account, each collection page, each immersive experience page), (2) sets static front page, (3) sets permalink structure to /%postname%/, (4) creates navigation menus programmatically, (5) assigns WooCommerce pages. Also commit the uncommitted preorder-gateway changes first. Then do Phase 6D: grep -r 'Where Love Meets Luxury' and replace every instance with 'Luxury Grows from Concrete.' across the ENTIRE codebase. After Phase 6, pick 3 industry-leading improvements from ralph-context.md Phase 7 and implement them. Then run full verification (Phase 8). GO.
