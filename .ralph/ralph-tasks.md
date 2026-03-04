# Ralph Tasks — Elite Web Builder v2 Full Website Makeover

## INSTRUCTIONS
- Update this file AFTER EVERY ITERATION with progress
- Mark tasks [x] when complete, [/] when in progress, [ ] when pending
- Add Context7 query logs under each task
- Add notes about what was done and any decisions made
- NEVER DELETE THIS FILE

---

## SECTION 1: Foundation & Configuration (Iterations 1-4)

- [ ] Read entire design package (all 12 HTML files + WP overlay files)
- [ ] Merge new functions.php with existing (keep all existing hooks, add new)
- [ ] Update style.css theme header to v4.0.0
- [ ] Deploy assets/css/main.css (new global stylesheet)
- [ ] Set up navigation menus (primary, footer, collection, mobile hamburger)
- [ ] SEO base setup (OG tags, JSON-LD, canonical URLs, meta descriptions)
- [ ] Configuration (conditional wp_enqueue, Google Fonts preconnect, critical CSS, reduced-motion)
- [ ] **BONUS ROUND**: Add 2 industry-proven features (your choice — explain why)

**Context7 Queries:**
- [ ] WordPress register_nav_menus
- [ ] WordPress wp_enqueue_style / wp_enqueue_script
- [ ] WordPress add_theme_support
- [ ] WooCommerce theme support hooks

---

## SECTION 2: Homepage Makeover (Iterations 5-8)

- [ ] Convert homepage/index.html → front-page.php
- [ ] Extract CSS → assets/css/homepage.css
- [ ] Extract JS → assets/js/homepage.js
- [ ] Replace hardcoded products with WooCommerce queries
- [ ] Replace base64 images with asset references
- [ ] Add AJAX add-to-cart functionality
- [ ] Create template parts for reusable sections
- [ ] Conditional enqueue for homepage assets
- [ ] **BONUS ROUND**: Add 2 industry-proven features (your choice — explain why)

**Context7 Queries:**
- [ ] WooCommerce wc_get_products()
- [ ] WordPress template parts (get_template_part)
- [ ] WooCommerce AJAX add-to-cart

---

## SECTION 3: Landing Pages — Conversion Engines (Iterations 9-14)

- [x] Create template-landing-black-rose.php from lp-black-rose.html
  - **Iteration 9**: Full 8-section conversion framework implemented
  - Uses `skyyrose_get_collection_products('black-rose')` for dynamic product data
  - CSS custom properties for collection theming (`--lp-accent: #C0C0C0`)
  - All text properly escaped (`esc_html()`, `esc_attr()`, `esc_url()`)
  - ARIA labels on all sections, FAQ buttons use `<button>` with `aria-expanded`
  - Product grid shows cost-per-wear calculator and scarcity indicators
- [x] Create template-landing-love-hurts.php from lp-love-hurts.html
  - **Iteration 10**: Full 8-section conversion framework implemented
  - Accent color: `#DC143C` (crimson), `--lp-accent-rgb: 220, 20, 60`
  - Hero: "Named After a Bloodline — Designed for Survivors"
  - Unique content: founder's family name "Hurts", emotional/vulnerability theme
  - Reviews from Aaliyah M. (Chicago), Tyler J. (Oakland), Kevin L. (Houston)
  - FAQ covers origin of name, DTG printing, sizing, returns, seasonal rotation
  - Lookbook: 5 images from `scenes/love-hurts/` (shrine, staircase, dome, ballroom, chamber)
  - Email capture: "Join 8,200+ people who wear their story"
- [x] Create template-landing-signature.php from lp-signature.html
  - **Iteration 10**: Full 8-section conversion framework implemented
  - Accent color: `#D4AF37` (gold), `--lp-accent-rgb: 212, 175, 55`
  - Hero: "Foundation Wardrobe — Built to Last"
  - Unique content: everyday wardrobe, not limited-edition, restocking model
  - Cost-per-wear uses 3 wears/week (156/year) vs Black Rose's 2 wears/week
  - Added "Always Available" green dot variant (`.lp-scarcity__dot--green`) to landing.css
  - "Bestseller" badge for top products instead of scarcity countdown
  - Reviews from Chris W. (SF), Priya N. (Brooklyn), Andre C. (Oakland)
  - FAQ differentiates Signature from Black Rose (restocking vs limited)
  - Lookbook: scenes from `scenes/signature/` + about images
  - Email capture: "Join 15,800+ members in the SkyyRose community"
- [x] Extract CSS → assets/css/landing.css (SHARED — single file, collection-specific via CSS vars)
  - **Architecture decision**: One `landing.css` instead of 3 per-collection files
  - CSS custom properties `--lp-accent` and `--lp-accent-rgb` set per template
  - Responsive breakpoints at 768px (tablet) and 480px (mobile)
  - `prefers-reduced-motion` support for all animations
- [x] Extract JS → assets/js/landing-engine.js (shared: countdown, scarcity, parallax, FAQ accordion)
  - **Iteration 9**: All 6 features implemented:
    1. IntersectionObserver scroll-reveal
    2. Nav scroll state (compact on scroll)
    3. FAQ accordion (single-open, keyboard accessible)
    4. Countdown timer (reads `data-countdown-end` or sessionStorage fallback)
    5. Parallax break images
    6. Newsletter AJAX form (hooks into `skyyrose_ajax_newsletter_subscribe`)
- [x] Implement 8-section conversion framework on all 3 pages (Black Rose iter 9, Love Hurts + Signature iter 10)
- [x] Hook countdown to get_option('skyyrose_preorder_deadline')
- [x] Hook email capture to admin-ajax.php with nonce
  - Uses existing `skyyrose_ajax_newsletter_subscribe` handler
  - Nonce from `wp_nonce_field('skyyrose_newsletter')` in form + `skyyRoseData.nonce` in JS
- [x] Conditional enqueue for landing page assets
  - Added to `skyyrose_get_current_template_slug()` template map (lines 268-270)
  - Added `'landing' => 'landing.css'` to template styles (line 310)
  - Added `'landing' => 'landing-engine.js'` to template scripts (line 397)
  - Added `'skyyrose-template-landing-engine'` to defer handles (line 881)
- [ ] **BONUS ROUND**: Add 2 industry-proven features (your choice — explain why)

**Context7 Queries:**
- [x] WordPress Hooks (library: `/websites/developer_wordpress_reference_hooks`) — wp_ajax handlers, nonce, admin-post patterns
- [x] WooCommerce (library: `/woocommerce/woocommerce`) — wc_get_products by category, stock_status, pagination
- [x] WordPress nonce verification (wp_nonce_field, check_ajax_referer) — covered via WordPress Hooks query above
- [x] WordPress Classes (library: `/websites/developer_wordpress_reference_classes`) — esc_html, esc_attr, esc_url escaping, wp_nonce_field
- [x] WooCommerce (library: `/woocommerce/woocommerce`) — wc_get_products by category slug, stock_quantity, stock_status

---

## SECTION 4: Collection Pages — Full Product Showcases (Iterations 15-18)

- [ ] Replace template-collection-black-rose.php with new design
- [ ] Replace template-collection-love-hurts.php with new design
- [ ] Replace template-collection-signature.php with new design
- [ ] Verify template-collection-kids-capsule.php nav links work
- [ ] Product grid with hover effects and quick-view capability
- [ ] Sort/filter controls
- [ ] Cross-collection navigation
- [ ] Pre-order CTA section
- [ ] Link to immersive experience (DO NOT MODIFY immersive pages)
- [ ] **BONUS ROUND**: Add 2 industry-proven features (your choice — explain why)

**Context7 Queries:**
- [ ] WooCommerce product queries by category
- [ ] WordPress taxonomy queries (get_terms, WP_Term_Query)

---

## SECTION 5: Single Product Pages (Iterations 19-22)

- [ ] Deploy woocommerce/single-product.php (collection-aware)
- [ ] Deploy inc/wc-product-functions.php (helpers)
- [ ] Deploy assets/css/single-product.css
- [ ] Deploy assets/js/single-product.js
- [ ] Verify collection detection (Black Rose=silver, Love Hurts=crimson, Signature=gold)
- [ ] Image gallery, size selector, AJAX cart, tabs
- [ ] Related products from same collection
- [ ] Conditional enqueue for single product assets
- [ ] **BONUS ROUND**: Add 2 industry-proven features (your choice — explain why)

**Context7 Queries:**
- [ ] WooCommerce single product hooks
- [ ] WooCommerce woocommerce_before_single_product
- [ ] WooCommerce product gallery / variations API

---

## SECTION 6: About Page + Global Polish (Iterations 23-26)

- [ ] Convert homepage/about.html → template-about.php (replace existing)
- [ ] Cinematic hero with parallax
- [ ] Founder story timeline
- [ ] YouTube embed (The Blox interview)
- [ ] Press room with logos
- [ ] Verify ALL menu links work (primary, footer, collection, mobile)
- [ ] Verify breadcrumb navigation across all pages
- [ ] Test WooCommerce cart flow end-to-end
- [ ] Responsive design audit (mobile, tablet, desktop)
- [ ] Performance pass (lazy-load, defer, minify)
- [ ] Accessibility pass (ARIA, focus, keyboard nav)
- [ ] 404 page consistency with new design language
- [ ] **BONUS ROUND**: Add 2 industry-proven features (your choice — explain why)

**Context7 Queries:**
- [ ] WordPress breadcrumbs
- [ ] WooCommerce cart fragments
- [ ] WordPress responsive/mobile best practices

---

## SECTION 7: SEO, Config Lockdown & Final QA (Iterations 27-30)

- [ ] SEO final pass: every page has title, meta desc, OG image/title/desc
- [ ] JSON-LD: Organization (homepage), Product (each product), BreadcrumbList (all pages)
- [ ] Robots.txt configuration
- [ ] Canonical URLs audit
- [ ] Internal linking audit (every page links to 2+ other pages)
- [ ] Image alt text audit (every img has descriptive alt)
- [ ] Page speed: critical CSS, font-display swap, image optimization
- [ ] Verify all wp_enqueue calls are conditional per template
- [ ] Verify security headers intact (inc/security.php)
- [ ] Verify AJAX nonce verification on all handlers
- [ ] Verify no inline onerror handlers (CSP compliance)
- [ ] Verify index.php?rest_route= used everywhere (not /wp-json/)
- [ ] Final QA checklist (see ralph-context.md Section 7)
- [ ] **BONUS ROUND**: Add 2 FINAL industry-proven features (your choice — explain why)

**Context7 Queries:**
- [ ] Schema.org structured data (JSON-LD)
- [ ] WordPress robots.txt / canonical
- [ ] Core Web Vitals best practices

---

## Serena Memory Updates
- [ ] After Section 1: Save foundation decisions
- [ ] After Section 3: Save conversion framework decisions
- [ ] After Section 5: Save product page architecture
- [ ] After Section 7: Save final site map and config

## Code Reviews
- [ ] After Section 1: Run code-reviewer agent
- [ ] After Section 3: Run code-reviewer agent
- [ ] After Section 5: Run code-reviewer agent
- [ ] After Section 7: Run code-reviewer + security-reviewer agents
