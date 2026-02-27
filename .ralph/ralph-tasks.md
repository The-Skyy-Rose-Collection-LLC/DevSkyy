# Ralph Tasks — Elite Web Builder Full Site Build

## INSTRUCTIONS
- Update this file AFTER EVERY ITERATION with progress
- Mark tasks [x] when complete, [/] when in progress, [ ] when pending
- Add notes under each task about what was done

## Phase 1: Audit & Inventory
- [x] Read every template file in wordpress-theme/skyyrose-flagship/
  - Done: iterations 1-13, all templates read and built
- [x] Inventory all product images in assets/images/products/ — identify missing shots
  - Done: 26 single-angle shots cataloged, 6 placeholder-only products identified
- [x] Audit menus registered in functions.php
  - Done: primary, footer, mobile, collection menus all registered in inc/menu-setup.php
- [x] Audit SEO tags across all templates (title, meta, OG, JSON-LD)
  - Done: inc/seo.php + inc/accessibility-seo.php handle all SEO

## Phase 2: AI Model Imagery (50 images)
- [/] Black Rose collection — 8 products x front+back = 16 images
  - 4 front-model VTON done (br-001, br-003, br-006, br-008), 0 back views (HF auth blocked)
  - 4 products placeholder-only (br-002, br-004, br-005, br-007)
- [/] Love Hurts collection — 5 products x front+back = 10 images
  - 2 front-model VTON done (lh-002, lh-005), 0 back views (HF auth blocked)
  - 2 products placeholder-only (lh-003, lh-004)
- [/] Signature collection — 12 products x front+back = 24 images
  - 7 front-model VTON done (sg-001, sg-004, sg-005, sg-006, sg-008, sg-009, sg-010, sg-012)
  - sg-011 VTON low quality (10 KB, needs regen with HF auth)
- [ ] Verify all images generated and placed in correct directories
  - BLOCKED: All VTON/3D providers need `huggingface-cli login` for ZeroGPU quota

## Phase 3: Content Build — Page by Page
- [x] front-page.php — hero, collections preview, social proof, pre-order CTA
- [x] template-collection-black-rose.php — full editorial content
- [x] template-collection-love-hurts.php — full editorial content
- [x] template-collection-signature.php — full editorial content
- [x] template-collection-kids-capsule.php — full editorial content (iteration 48: added url+image to static)
- [x] template-immersive-black-rose.php — 3D storytelling content
- [x] template-immersive-love-hurts.php — 3D storytelling content
- [x] template-immersive-signature.php — 3D storytelling content (iteration 48: fixed split-SKU prices)
- [x] template-preorder-gateway.php — all products, pricing, cart
- [x] header.php — polished nav, mobile menu (iteration 48: WC cart null safety)
- [x] footer.php — social links, newsletter, brand footer
- [x] 404.php, search.php, single.php, page.php — polish (iteration 48: i18n wrapped)

## Phase 4: Menus & Navigation
- [x] Register all menus in functions.php (primary, footer, mobile, collection)
- [x] Nav walkers working correctly
- [x] Mobile hamburger menu functional
- [x] Breadcrumbs on interior pages
- [x] Verify all internal links resolve

## Phase 5: SEO Optimization
- [x] Unique title tags + meta descriptions per template
- [x] Open Graph tags (og:title, og:description, og:image) on every page
- [x] JSON-LD structured data (Organization, Product, BreadcrumbList)
- [x] Single H1 per page, proper heading hierarchy
- [x] Alt text on ALL images
- [x] Canonical URLs

## Phase 6: Marketplace Polish
- [x] Design tokens consistent (#B76E79, #0a0a0a, #D4AF37)
- [x] Luxury micro-interactions (hover, scroll, parallax)
- [x] Responsive across mobile/tablet/desktop/ultrawide
- [x] WCAG 2.1 AA accessibility (ARIA, focus, keyboard nav) — 48 iterations of fixes
- [x] Performance: lazy loading, critical CSS, optimized fonts
- [x] Security: output escaping, CSP headers, rate limiting

## Phase 7: Verification
- [x] Run all 8 gate checkers on modified files — 3 parallel code review agents every iteration
- [ ] pytest -v passes — no WordPress-specific pytest suite configured
- [ ] Final cost report from cost_tracker

## Iteration 48 Summary (2026-02-27)
- 10 CRITICAL + 5 HIGH fixes across 12 files
- PHP: wishlist nopriv, REST nonce, rate limiting, WC null safety, slug-based page detection
- JS: eventQueue cap, interval cleanup, focus restoration, Escape key priority, search overlay inert trap, innerHTML→DOM API
- Templates: i18n wrapping (404 + about), Kids Capsule static data, split-SKU price mismatch
- All 8 PHP files pass lint, all 12 files SFTP deployed to skyyrose.co
