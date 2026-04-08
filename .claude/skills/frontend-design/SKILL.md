---
name: frontend-design
description: >
  Create distinctive, production-grade frontend interfaces with deep expertise in UI/UX design,
  full-stack WordPress/WooCommerce theme development, and component architecture. Use when building
  web pages, templates, components, landing pages, or any visual interface. Covers end-to-end:
  design system creation, CSS architecture, animation orchestration, PHP template hierarchy,
  WooCommerce integration, Elementor compatibility, accessibility (WCAG 2.1 AA), performance
  optimization (Core Web Vitals), and responsive design. Triggers on any frontend, design, theme,
  template, component, landing page, or UI/UX work.
---

# Frontend Design — Full-Stack Theme & UI/UX Architecture

End-to-end guide for building distinctive, production-grade frontend interfaces. Covers design thinking, component architecture, WordPress theme development, WooCommerce integration, animation systems, accessibility, and performance.

---

## 1. Design Thinking

Before writing any code, commit to a clear design direction:

### Design Process
1. **Purpose** — What problem does this interface solve? Who uses it?
2. **Tone** — Pick an intentional aesthetic: luxury/refined, editorial/magazine, brutalist/raw, maximalist, minimalist, organic, retro-futuristic, etc.
3. **Differentiation** — What's the one thing someone will remember?
4. **Constraints** — Framework, performance budget, accessibility requirements

### Anti-Slop Rules
NEVER produce generic AI aesthetics:
- No default font stacks (Inter, Roboto, Arial, system-ui)
- No purple-on-white gradient cliches
- No predictable card-grid-with-rounded-corners layouts
- No cookie-cutter component patterns
- Every design must have a clear point-of-view

Match complexity to vision: maximalist designs need elaborate animation and layered effects. Minimalist designs need precision in spacing, typography weight, and subtle details.

---

## 2. UI/UX Design System

### Typography Scale (Fluid)
Use `clamp()` for responsive type. Define a complete scale:
```css
--text-xs: 0.8125rem;           /* 13px — captions, fine print */
--text-sm: 0.9375rem;           /* 15px — secondary text */
--text-base: 1.0625rem;         /* 17px — body text */
--text-lg: 1.1875rem;           /* 19px — emphasized body */
--text-xl: 1.375rem;            /* 22px — large body */
--text-2xl: 1.625rem;           /* 26px — small headings */
--text-3xl: clamp(1.875rem, 2.8vw, 2.25rem);   /* Section titles */
--text-4xl: clamp(2.25rem, 3.8vw, 2.875rem);   /* Page titles */
--text-5xl: clamp(2.75rem, 5.5vw, 4rem);       /* Hero headings */
--text-decorative: clamp(5rem, 14vw, 12.5rem); /* Display text */
```

### Spacing System (4px/8px grid)
```css
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
--space-24: 6rem;     /* 96px */
```

### Color Architecture
Define semantic tokens, not raw hex in components:
```css
/* Brand layer */
--color-brand-primary: #B76E79;
--color-brand-accent: #D4AF37;

/* Surface layer */
--color-page-bg: #0A0A0A;
--color-card-bg: #111111;
--color-border: #2A2A2A;

/* Text layer */
--color-text-primary: #FFFFFF;
--color-text-secondary: #E0E0E0;
--color-text-muted: #B3B3B3;

/* Semantic layer */
--color-success: #10B981;
--color-error: #DC143C;
--color-warning: #F59E0B;
```

Use `[data-collection]` or `[data-theme]` attributes for palette switching:
```css
[data-collection="black-rose"] {
  --col-accent: #C0C0C0;
  --col-font-display: 'Cinzel', serif;
}
[data-collection="love-hurts"] {
  --col-accent: #DC143C;
  --col-font-display: 'Playfair Display', serif;
}
```

### Shadow & Depth System
```css
--depth-1: 0 2px 8px rgba(0, 0, 0, 0.4);      /* Cards */
--depth-2: 0 8px 24px rgba(0, 0, 0, 0.5);      /* Elevated cards */
--depth-3: 0 16px 48px rgba(0, 0, 0, 0.6);     /* Modals */
--depth-4: 0 24px 64px rgba(0, 0, 0, 0.7);     /* Hero overlays */
```

### Glass Effects
```css
--glass-bg: rgba(17, 17, 17, 0.92);
--glass-border: 1px solid rgba(255, 255, 255, 0.06);
--glass-blur: blur(24px) saturate(1.4);
```

### Z-Index Scale
```css
--z-base: 0;
--z-sticky: 200;
--z-overlay: 400;
--z-tooltip: 600;
--z-modal: 800;
--z-cursor: 9999;
```

---

## 3. Animation Architecture

### Easing Library
```css
--ease-cinematic: cubic-bezier(0.22, 1, 0.36, 1);      /* Hero entrances */
--ease-magnetic: cubic-bezier(0.03, 0.98, 0.52, 0.99); /* Cursor-reactive */
--ease-whip: cubic-bezier(0.75, 0, 0.25, 1);           /* Snappy micro-interactions */
--ease-smooth-out: cubic-bezier(0.16, 1, 0.3, 1);      /* Exit animations */
--ease-dramatic: cubic-bezier(0.65, 0, 0.35, 1);       /* Clip-path reveals */
```

### Scroll Reveal System
Base class `.rv` with directional variants:
```css
.rv { opacity: 0; transform: translateY(40px); transition: opacity 0.9s var(--ease-cinematic), transform 0.9s var(--ease-cinematic); }
.rv.visible { opacity: 1; transform: none; }
.rv-left { transform: translateX(-40px); }
.rv-right { transform: translateX(40px); }
.rv-scale { transform: scale(0.95); }
```

Stagger delays via CSS custom properties:
```css
.rv-d1 { transition-delay: 0.1s; }
.rv-d2 { transition-delay: 0.2s; }
/* Or dynamic: */
.stagger-grid > * { transition-delay: calc(var(--stagger-index) * 60ms); }
```

### Premium Animation Classes
| Class | Effect | Trigger |
|---|---|---|
| `.rv-clip-up` | Clip-path wipe from bottom | `.is-visible` |
| `.rv-clip-left/right` | Horizontal clip reveal | `.is-visible` |
| `.rv-blur` | Blur(12px) + scale(0.97) → sharp | `.is-visible` |
| `.rv-split-char` | Per-character stagger via `--char-index` | `.is-visible` |
| `.rv-split-word` | Per-word stagger with blur fade | `.is-visible` |
| `.stagger-grid` | Grid children cascade entrance | `.is-visible` |
| `.magnetic` | Cursor-reactive translate (--mag-x, --mag-y) | mousemove |
| `.btn-sweep` | Diagonal background slide-in | hover |
| `.btn-border-draw` | Borders animate from corners | hover |
| `.parallax-slow/medium/fast` | Y-offset at 15%/30%/50% scroll speed | scroll |

### Reduced Motion (MANDATORY)
```css
@media (prefers-reduced-motion: reduce) {
  .rv, .rv-clip-up, .rv-blur, .stagger-grid > * {
    opacity: 1; transform: none; transition: none;
    clip-path: none; filter: none;
  }
}
```

### JavaScript Animation Patterns
```javascript
// IntersectionObserver for scroll reveals (NO jQuery, NO GSAP for basic reveals)
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.1 });
document.querySelectorAll('.rv').forEach(el => observer.observe(el));

// Magnetic cursor tracking
el.addEventListener('mousemove', (e) => {
  const rect = el.getBoundingClientRect();
  const magX = (e.clientX - rect.left - rect.width / 2) / (rect.width / 2);
  const magY = (e.clientY - rect.top - rect.height / 2) / (rect.height / 2);
  el.style.setProperty('--mag-x', magX);
  el.style.setProperty('--mag-y', magY);
});

// Parallax (use transform, never top/left)
window.addEventListener('scroll', () => {
  const progress = window.scrollY / window.innerHeight;
  document.querySelectorAll('[data-parallax]').forEach(el => {
    el.style.setProperty('--parallax-offset', progress * 100);
  });
});
```

---

## 4. WordPress Theme Architecture

### Template Hierarchy
```
page-{slug}.php → page-{id}.php → page.php → singular.php → index.php
```

Custom page templates use the `Template Name` header:
```php
<?php
/**
 * Template Name: Landing — Black Rose
 * Template Post Type: page
 */
get_header();
```

### Theme File Structure
```
theme-root/
├── functions.php              # Entry point — constants, includes array
├── header.php / footer.php    # Global wrappers
├── style.css                  # WP header + version
├── inc/                       # PHP modules (enqueue, security, WC, catalog, config)
│   ├── enqueue.php            # CSS/JS loading system
│   ├── brand-colors.php       # Color constants (PHP mirrors CSS tokens)
│   ├── collections-config.php # Collection metadata SOT
│   ├── product-catalog.php    # Static product database
│   ├── template-functions.php # Utility helpers
│   └── security.php           # CSP, rate limiting, ABSPATH guards
├── assets/
│   ├── css/
│   │   ├── design-tokens.css  # Root CSS custom properties
│   │   ├── system/animations.css + animations-premium.css
│   │   └── [template-specific].css
│   ├── js/                    # Vanilla JS modules (no jQuery dependency)
│   └── fonts/                 # Self-hosted woff2 (GDPR compliant)
├── template-parts/            # Reusable PHP components
│   └── product-card-holo.php  # Props via $args, data attributes
├── woocommerce/               # WC template overrides
└── template-*.php             # Custom page templates
```

### Component Pattern (Template Parts)
Components receive data via `$args` array with `wp_parse_args()`:
```php
<?php
// Calling the component
get_template_part('template-parts/landing/hero', null, [
    'collection'  => 'black-rose',
    'title'       => 'Black Rose',
    'hero_image'  => 'br-brand-script.png',
    'tagline'     => 'Dark luxury streetwear from Oakland.',
    'badge'       => 'Limited Edition — 200 Pieces Per Style',
]);

// Inside template-parts/landing/hero.php
$defaults = [
    'collection' => '',
    'title'      => '',
    'hero_image' => '',
    'tagline'    => '',
    'badge'      => '',
];
$args = wp_parse_args($args, $defaults);
?>
<section class="lp-hero" data-collection="<?php echo esc_attr($args['collection']); ?>">
    <div class="lp-hero__badge rv rv-d1"><?php echo esc_html($args['badge']); ?></div>
    <img class="lp-hero__logo rv rv-d2" src="<?php echo esc_url(SKYYROSE_ASSETS_URI . '/techflats/hero-overlays/' . $args['hero_image']); ?>" alt="<?php echo esc_attr($args['title']); ?>" loading="eager">
    <p class="lp-hero__tagline rv rv-d3"><?php echo esc_html($args['tagline']); ?></p>
</section>
```

### CSS Class Conventions
- **BEM-inspired**: `.block__element--modifier` for components
- **Short prefixes for page-scoped**: `.lp-hero`, `.lp-products`, `.col-story`
- **State classes**: `.is-visible`, `.is-active`, `.is-open`, `.is-loading`
- **Data attributes for theming**: `[data-collection="slug"]`, `[data-scroll-fade]`
- **Stagger indexing**: `style="--stagger-index: 3"` (CSS does the math)

### Conditional Asset Loading
```php
// Template slug detection → surgical CSS/JS delivery
function skyyrose_get_current_template_slug() {
    if (is_front_page()) return 'front-page';
    if (is_404()) return '404';
    if (is_product()) return 'single-product';
    // ... page template file map
    $template = get_page_template_slug();
    if (strpos($template, 'template-landing') !== false) return 'landing';
    if (strpos($template, 'template-collection') !== false) return 'collection-standalone';
}

// Enqueue by slug (priority 20, after globals at 10)
$slug = skyyrose_get_current_template_slug();
if ($slug === 'landing') {
    wp_enqueue_style('skyyrose-landing', $uri . '/assets/css/landing-pages.css', ['skyyrose-design-tokens'], SKYYROSE_VERSION);
    wp_enqueue_script('skyyrose-landing', $uri . '/assets/js/landing-pages.js', [], SKYYROSE_VERSION, true);
}
```

### Hook Priority Sequencing
```
Priority 5:  Fonts (preload, prevent FOUT)
Priority 10: Global styles + scripts (design-tokens, components, animations, nav)
Priority 15: Script localization (wp_localize_script)
Priority 20: Template-specific CSS/JS (conditional on slug)
```

---

## 5. WooCommerce Integration

### Product Data Access
```php
// From WC product object
$product = wc_get_product($product_id);
$price = $product->get_price_html();
$stock = $product->get_stock_quantity();
$image = wp_get_attachment_image_url($product->get_image_id(), 'large');

// From static catalog (non-WC fallback)
$catalog = skyyrose_get_product_catalog();
$item = $catalog[$sku];
```

### Add-to-Cart (AJAX, No Page Reload)
```javascript
// WooCommerce native AJAX add-to-cart
document.querySelectorAll('.add-to-cart').forEach(btn => {
  btn.addEventListener('click', async (e) => {
    e.preventDefault();
    btn.classList.add('is-loading');
    const form = new URLSearchParams({
      product_id: btn.dataset.productId,
      quantity: 1,
    });
    const res = await fetch('/?wc-ajax=add_to_cart', {
      method: 'POST',
      body: form,
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    const data = await res.json();
    btn.classList.remove('is-loading');
    if (data.error) { window.skyyToast(data.error, 'error'); return; }
    window.skyyToast('Added to bag', 'success');
    // Update cart count in nav
    document.querySelectorAll('.cart-count').forEach(el => {
      el.textContent = data.cart_hash ? parseInt(el.textContent || 0) + 1 : el.textContent;
    });
  });
});
```

### Scarcity Display Pattern
```php
<div class="scarcity-indicator">
    <span class="scarcity-dot"></span>
    <span class="scarcity-text">
        <?php echo esc_html($stock); ?> of <?php echo esc_html($edition_size); ?> remaining
    </span>
</div>
```
```css
.scarcity-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--color-error); animation: pulse 1.5s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
```

### WooCommerce Template Overrides
Place in `theme/woocommerce/` to override WC defaults:
```
woocommerce/
├── single-product.php          # Product page layout
├── content-product.php         # Shop grid card
├── cart/cart.php                # Cart page
├── checkout/form-checkout.php  # Checkout
└── single-product/
    ├── title.php               # Product title
    └── price.php               # Price display
```

---

## 6. Elementor Compatibility

### Elementor JSON Structure
Pages store layout in `_elementor_data` postmeta:
```json
[{
  "elType": "section",
  "settings": { "layout": "full_width", "background_color": "#0A0A0A" },
  "elements": [{
    "elType": "column",
    "elements": [{
      "elType": "widget",
      "widgetType": "heading",
      "settings": { "title": "BLACK ROSE", "typography_font_family": "Cinzel" }
    }]
  }]
}]
```

### Theme + Elementor Hybrid
Use PHP templates for performance-critical pages (landing pages, collections). Use Elementor for admin-editable content:
```php
// Render Elementor template inside theme template
if (class_exists('\Elementor\Plugin')) {
    echo \Elementor\Plugin::instance()->frontend->get_builder_content_for_display($template_id);
}
```

### Custom Elementor Widgets
```php
add_action('elementor/widgets/register', function($widgets_manager) {
    require_once get_template_directory() . '/elementor/widgets/product-card.php';
    $widgets_manager->register(new \SkyyRose\Product_Card_Widget());
});
```

---

## 7. Accessibility (WCAG 2.1 AA)

### Critical Requirements
- **Contrast**: 4.5:1 for normal text, 3:1 for large text (18px+ bold or 24px+)
- **Focus states**: Visible 2-4px rings on all interactive elements
- **Touch targets**: Minimum 44x44px (use `hitSlop` / padding if icon is smaller)
- **Alt text**: Descriptive on meaningful images, `alt=""` + `aria-hidden="true"` on decorative
- **Keyboard nav**: Tab order matches visual order, skip-to-content link
- **ARIA labels**: On icon-only buttons, landmark regions
- **Heading hierarchy**: Sequential h1→h6, no level skips
- **Color not only**: Never convey information by color alone (add icon/text)
- **Reduced motion**: Respect `prefers-reduced-motion` — disable animations, parallax

### WordPress-Specific A11y
```php
// Skip nav (in header or via output buffer)
<a class="skip-nav" href="#main-content">Skip to main content</a>

// Screen reader text
<span class="screen-reader-text">Close menu</span>

// Escape all output
echo esc_html($title);          // Text content
echo esc_attr($class);          // HTML attributes
echo esc_url($link);            // URLs
echo wp_kses_post($description); // Rich text (limited HTML)
```

---

## 8. Performance (Core Web Vitals)

### LCP (Largest Contentful Paint) < 2.5s
- Preload hero image: `<link rel="preload" as="image" href="...">`
- Self-host fonts (woff2) with `font-display: swap`
- Inline critical CSS for above-fold content
- `loading="eager"` on hero image, `loading="lazy"` on everything below fold

### CLS (Cumulative Layout Shift) < 0.1
- Set `width` + `height` or `aspect-ratio` on all images
- Reserve space for async content (skeleton screens)
- No font-swap reflow (preload critical fonts)

### INP (Interaction to Next Paint) < 200ms
- Defer non-critical JS: `wp_enqueue_script(..., true)` for footer
- No layout-triggering animations (use `transform` + `opacity` only)
- Debounce scroll/resize handlers

### WordPress Performance
```php
// Version-bust CSS on deploy
define('SKYYROSE_VERSION', '6.4.0');
wp_enqueue_style('handle', $uri, [], SKYYROSE_VERSION);

// Conditional premium animations (skip on lightweight pages)
$skip = ['cart', 'checkout', 'blog', 'single', '404', 'search'];
if (!in_array($slug, $skip)) {
    wp_enqueue_style('animations-premium');
}

// GSAP only where needed (3 pages, not global)
if (in_array($slug, ['preorder-gateway', 'about', 'immersive'])) {
    wp_enqueue_script('gsap');
}
```

### Image Optimization
- WebP format, quality 85-92 for product shots
- Responsive images: `srcset` + `sizes` attributes
- Aspect ratio 3:4 for product cards, 16:9 for banners
- Maximum 200KB per hero image, 80KB per product image

---

## 9. Responsive Design

### Breakpoints
```css
/* Mobile first */
@media (min-width: 375px)  { /* Small phone adjustments */ }
@media (min-width: 768px)  { /* Tablet: 2-column layouts */ }
@media (min-width: 1024px) { /* Desktop: full layouts */ }
@media (min-width: 1440px) { /* Large desktop: max-width containers */ }
```

### Container System
```css
.container        { max-width: 1200px; margin: 0 auto; padding: 0 24px; }
.container--wide  { max-width: 1400px; }
.container--narrow { max-width: 800px; }
```

### Mobile Considerations
- Minimum 16px body text (prevents iOS auto-zoom)
- Stack grids to single column below 768px
- Hide hover-dependent interactions on touch devices
- Bottom nav for mobile (hidden on desktop >=769px)
- Safe area padding for notch/gesture bar devices
- `min-height: 100dvh` over `100vh` for mobile viewports

---

## 10. Security

### WordPress Output Security
```php
echo esc_html($text);              // ALWAYS escape text output
echo esc_attr($attribute);         // ALWAYS escape attributes
echo esc_url($url);                // ALWAYS escape URLs
echo wp_kses_post($rich_content);  // Allow limited HTML
```

### JavaScript Security
- NEVER use `innerHTML` — use `createElement` + `textContent`
- Validate `nonce` on all AJAX requests
- Sanitize URL parameters before use
- CSP headers in `inc/security.php`

### Asset Security
- SRI hashes on CDN scripts (GSAP, etc.)
- `?v=SKYYROSE_VERSION` on all asset URLs for cache busting
- No inline `onclick` handlers — use `addEventListener`

---

## Quick Reference: WordPress Template Checklist

Before shipping any WordPress template:
- [ ] `esc_html()` / `esc_attr()` / `esc_url()` on ALL dynamic output
- [ ] `loading="lazy"` on below-fold images, `loading="eager"` on hero
- [ ] `alt` text on meaningful images, `alt=""` on decorative
- [ ] CSS enqueued via `wp_enqueue_style()`, not inline `<style>`
- [ ] JS enqueued via `wp_enqueue_script()` with `true` (footer)
- [ ] `SKYYROSE_VERSION` on all asset URLs
- [ ] `data-collection` attribute for palette switching
- [ ] `prefers-reduced-motion` media query disabling animations
- [ ] Mobile layout tested at 375px
- [ ] No hardcoded URLs (use `get_template_directory_uri()`)
- [ ] Focus states visible on interactive elements
- [ ] `php -l` passes on all PHP files
