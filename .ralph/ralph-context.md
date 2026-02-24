# Ralph Loop Context — CRITICAL CLARIFICATION

## Context added at 2026-02-24T18:05:00.000Z

## STOP — READ THIS BEFORE DOING ANYTHING ELSE

You may be confused about the architecture. Let me be crystal clear:

### THE WEBSITE = WORDPRESS. PERIOD.

ALL static pages AND interactive pages live in the **WordPress theme** (`wordpress-theme/skyyrose-flagship/`). This is a custom WordPress theme that runs on skyyrose.co. Everything the customer sees is WordPress:

- Homepage → `front-page.php` (WordPress)
- Collection landing pages → `template-collection-*.php` (WordPress)
- Immersive 3D scenes → `template-immersive-*.php` (WordPress)
- Product pages → `woocommerce/single-product.php` (WordPress)
- Shop page → `woocommerce/archive-product.php` (WordPress)
- Cart → `woocommerce/cart/cart.php` (WordPress)
- Checkout → `woocommerce/checkout/form-checkout.php` (WordPress)
- Pre-order → `template-preorder-gateway.php` (WordPress)
- About, Contact, Wishlist, 404 → all WordPress templates

This theme MUST be:
- **WordPress.org marketplace-worthy** — follows all WordPress coding standards, theme review requirements, proper use of `wp_enqueue_script/style`, proper template hierarchy, translation-ready, accessibility compliant
- **Fully compatible with WooCommerce** — product catalog, cart, checkout, payment gateways, shipping, tax, coupons, order management
- **Fully compatible with Jetpack** — site stats, CDN, security, social sharing, related posts, subscriptions
- **Compatible with standard WordPress plugins** — Elementor, Yoast SEO, WPForms, Akismet, UpdraftPlus, etc.
- **Child-theme friendly** — all customizations hookable via actions/filters
- **WordPress Customizer integrated** — brand colors, logos, social links all configurable from Appearance > Customize

DO NOT build React pages, Next.js routes, or standalone HTML files for the customer-facing site. Everything goes through WordPress PHP templates with proper WordPress hooks, filters, and enqueue functions.

### THE VERCEL DASHBOARD = INTERNAL ADMIN TOOL (NOT THE WEBSITE)

The Next.js app in `frontend/` deploys to Vercel project **"devskyy"**. This is NOT the customer-facing website. This is the internal DevSkyy admin dashboard that:

- Configures and monitors the **automated AI agents** (54 agents)
- Deploys content **TO WordPress** (pushes products, pages, media via WP REST API)
- Deploys content **TO HuggingFace** (3D models, AI assets)
- Deploys content **TO social media platforms** (Instagram, TikTok, etc.)
- Monitors health, performance, analytics
- Manages the 3D asset pipeline
- Runs quality assurance checks
- Orchestrates multi-agent workflows (Round Table)

The dashboard is for the TEAM, not the customer. Build/enhance it separately from the WordPress theme.

### SUMMARY

| What | Where | Tech | Who sees it |
|------|-------|------|-------------|
| The Website | skyyrose.co | WordPress theme + WooCommerce | Customers |
| Admin Dashboard | devskyy Vercel | Next.js + Tailwind | Team only |
| Showroom prototype | localhost:3000 | Vanilla JS (skyyrose/) | Dev reference |

---

## NOW DO THIS (in order):

### 1. FIX THE WORDPRESS ERROR
There's an error on the live site. Diagnose and fix it first. Check `functions.php`, `inc/*.php`, and all template files for PHP errors.

### 2. UPGRADE THE WORDPRESS THEME
Examine every PHP template. Apply modern UI/UX while following WordPress standards:

- All CSS via `wp_enqueue_style()` in `inc/enqueue.php`
- All JS via `wp_enqueue_script()` with proper dependencies
- All data via `wp_localize_script()` — no inline PHP-to-JS hacks
- Proper use of `get_template_part()` for reusable components
- `esc_html()`, `esc_attr()`, `esc_url()`, `wp_kses()` on ALL output
- Translation-ready: `__()`, `_e()`, `esc_html__()` on all strings
- Proper WooCommerce hooks: `woocommerce_before_shop_loop`, `woocommerce_single_product_summary`, etc.
- Theme Customizer for all brand settings (not hardcoded)

### 3. COLLECTION LOGOS — ROTATING 3D
Each collection page shows its own rotating logo (same 3D spin as the SR animated monogram):
- `assets/branding/black-rose-logo.png` → 8s silver moonlight rotation
- `assets/branding/love-hurts-logo.jpg` → 6s crimson fire rotation
- `assets/branding/signature-logo.jpg` → 7s gold sheen rotation
- `assets/branding/skyyrose-logo-animated.gif` → optimize to <2MB, homepage + pre-order only

### 4. SEAMLESS FLOW IN WORDPRESS
Homepage → Collection Landing → Product Gallery → Immersive 3D → Pre-Order

All within WordPress. Use AJAX page transitions or smooth scroll between template sections. No leaving WordPress.

### 5. AI FASHION MODELS
Generate via Gemini (`build/generate-fashion-models.js`) or HuggingFace. 100% replica products on diverse models. Upload generated images to WordPress Media Library for use in templates.

### 6. PRE-ORDER PAGE — THE MONEY PAGE
`template-preorder-gateway.php` — highlight reel with all 3 collections, animated SR logo in header, interactive product selection, exclusive incentive popup, checkout flow. All WordPress.

### 7. DEPLOY
- WordPress theme → push to skyyrose.co
- Next.js dashboard → `vercel --prod` to existing **"devskyy"** project (admin tool only)

---

## Signature Scene Images
`assets/scenes/signature/signature-waterfront-runway.png` and `signature-golden-gate-showroom.png` — use in `template-immersive-signature.php`

## After Each Iteration
1. Test: `npm test` and `pytest -v`
2. Commit: `feat:`, `fix:`, `style:`, `perf:`
3. Append to `.ralph/progress.txt`
