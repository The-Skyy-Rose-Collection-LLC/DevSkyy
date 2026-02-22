# WordPress Knowledge Base — SkyyRose Production

## Live Site Identity

- **Blog ID:** 238510894
- **URL:** https://skyyrose.co
- **Name:** The Skyy Rose Collection
- **Theme:** `skyyrose-flagship` (THE FLAGSHIP)
- **Platform:** WordPress.com Atomic (SSH/SFTP, custom PHP, full plugin access)
- **Homepage:** Static page (ID: 9331)
- **Timezone:** America/Los_Angeles (UTC-8)
- **Admin Email:** corey@skyyrose.co

## WordPress.com MCP Tools (Claude Code Integration)

### Content Authoring (wpcom-mcp-content-authoring)
- **posts:** list, get, create, update, delete
- **pages:** list, get, create, update, delete
- **media:** list, get, update, delete
- **categories:** list, get, create, update, delete
- **tags:** list, get, create, update, delete
- **patterns:** list, get (block patterns from theme)
- **synced-patterns:** list, get (user-created reusable patterns)
- **comments:** list only (create/update/delete disabled)

### Site Editor Context (wpcom-mcp-site-editor-context)
- **theme.active** → get stylesheet slug (`skyyrose-flagship`)
- **theme.presets** → design tokens (colors, fonts, spacing)
- **theme.styles** → block-level style overrides
- **blocks.allowed** → registered block types and style variations

### Content Workflow (MANDATORY sequence)
1. Call `theme.active` → get stylesheet slug
2. Call `theme.presets` → get design tokens
3. Call `patterns.list` → browse available patterns
4. Call `patterns.get` → fetch full markup for chosen pattern
5. Customize with **preset slugs** (NOT hardcoded hex/px values)
6. Create as **draft** → show edit/preview links
7. Check `_content_warnings` in response for stripped markup

### Safety Protocol
Before ANY create/update/delete operation:
1. Describe exactly what you plan to do
2. Ask user for confirmation
3. Include `user_confirmed` in params
4. NEVER auto-execute write operations

## REST API

- Use `index.php?rest_route=` NOT `/wp-json/` (WordPress.com requirement)
- Example: `https://skyyrose.co/index.php?rest_route=/wp/v2/pages`

## Theme Design Tokens (LIVE — use slugs, not hardcoded values)

### Colors (Official — Owner-Confirmed)
| Slug | Name | Hex | Used By |
|------|------|-----|---------|
| `black` | Black | #000000 | BLACK ROSE, LOVE HURTS, site background |
| `white` | White | #FFFFFF | BLACK ROSE, LOVE HURTS, text |
| `metallic-silver` | Metallic Silver | #C0C0C0 | BLACK ROSE accent |
| `crimson` | Crimson | #DC143C | LOVE HURTS accent |
| `red` | Red | #FF0000 | LOVE HURTS secondary |
| `rose-gold` | Rose Gold | #B76E79 | SIGNATURE accent, PRIMARY BRAND COLOR |
| `gold` | Gold | #D4AF37 | SIGNATURE secondary |
| `pink` | Pink | #FFB6C1 | KIDS CAPSULE accent |
| `lavender` | Lavender | #E6E6FA | KIDS CAPSULE secondary |

**Usage:** `has-gold-color`, `has-crimson-background-color` (class names in blocks)

### Gradients
| Slug | Gradient |
|------|----------|
| `black-to-gold` | linear-gradient(135deg, #000000 → #D4AF37) |
| `purple-to-rose` | linear-gradient(135deg, #4B0082 → #FFB6C1) |
| `crimson-to-gold` | linear-gradient(135deg, #8B0000 → #D4AF37) |

### Font Sizes
| Slug | Size |
|------|------|
| `small` | 14px |
| `medium` | 16px |
| `large` | 20px |
| `x-large` | 28px |
| `huge` | 42px |

### Font Families
| Slug | Stack | Usage |
|------|-------|-------|
| `heading` | 'Playfair Display', Georgia, serif | h1-h3, hero text, display headlines |
| `body` | 'Inter', -apple-system, BlinkMacSystemFont, sans-serif | Body text, UI elements, buttons |

**CRITICAL:** These are the ONLY two font families for the theme. Do NOT use Montserrat, Cormorant Garamond, Bebas Neue, or system-font defaults. Import via Google Fonts:
```
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&display=swap');
```

### Spacing Scale
| Slug | Size |
|------|------|
| `xs` | 0.5rem |
| `sm` | 1rem |
| `md` | 1.5rem |
| `lg` | 2rem |
| `xl` | 3rem |
| `2xl` | 4rem |

### Layout
- **Content width:** 1200px
- **Wide width:** 1400px

## Theme Structure

- Active theme: `skyyrose-flagship`
- Theme files: `wordpress-theme/skyyrose-flagship/`
- `theme.json` controls Full Site Editing (colors, fonts, spacing, layout)

### Dark Theme (MANDATORY DEFAULT)

```css
:root {
  --bg-dark: #0A0A0A;       /* Page background — NOT white */
  --bg-card: #111111;       /* Card backgrounds */
  --text-primary: #FFFFFF;
  --text-secondary: rgba(255, 255, 255, 0.7);
  --text-muted: rgba(255, 255, 255, 0.5);
  --border-subtle: rgba(255, 255, 255, 0.1);
}
```
Film grain SVG overlay at 3% opacity required on ALL pages. See `wordpress_deployment.md` for full CSS.

### Key Templates
| Template | Purpose |
|----------|---------|
| `header.php` | Fixed dark navbar with blur, gradient logo text, icon buttons |
| `footer.php` | 5-column grid footer with newsletter bar |
| `front-page.php` | Hero + collections showcase + featured products + brand story |
| `template-collection-black-rose.php` | Black Rose landing page with floating roses |
| `template-collection-love-hurts.php` | Love Hurts landing page with floating hearts |
| `template-collection-signature.php` | Signature landing page with art deco overlay |
| `template-collection-kids-capsule.php` | Kids Capsule landing page (pink/lavender) |
| `template-immersive-black-rose.php` | Image-based gothic garden exploration with product hotspots |
| `template-immersive-love-hurts.php` | Image-based baroque ballroom exploration with product hotspots |
| `template-immersive-signature.php` | Image-based glass runway exploration with product hotspots |
| `template-preorder-gateway.php` | Glassmorphism pre-order with collection tabs + cart sidebar |
| `template-about.php` | Brand story, timeline, values, founder section |
| `template-contact.php` | Contact form + FAQ accordion |
| `woocommerce/single-product.php` | AI model gallery + sticky info panel |
| `woocommerce/cart/cart.php` | Dark luxury cart with sticky order summary |
| `woocommerce/checkout/form-checkout.php` | Multi-step checkout with progress indicator |
| `404.php` | Branded 404 with gold gradient + collection links |

### Key Assets
| File | Purpose |
|------|---------|
| `assets/css/luxury-theme.css` | Full luxury CSS system |
| `assets/css/brand-variables.css` | CSS custom properties (dark theme, collection accents) |
| `assets/css/collection-colors.css` | Per-collection theming variables |
| `assets/css/immersive-scene.css` | Hotspot beacons, product panels, scene transitions |
| `assets/js/navigation.js` | Mobile menu, dropdowns, sticky header |
| `assets/js/main.js` | Scroll-reveal, countdown, parallax, film grain |
| `assets/js/immersive-scene.js` | Scene viewer, hotspot click, room transitions, product panels |

## Active Plugins (30/35)

### Core Commerce
- WooCommerce 10.5.2, WooPayments 10.5.1
- WooCommerce Stripe 10.4.0, PayPal Payments 3.4.0
- Stripe Tax 1.2.4, WooCommerce Tax 3.4.1, Shipping 2.2.0

### Page Builder
- Elementor 3.35.5, Elementor Pro 3.35.1
- Image Optimizer 1.7.2, Layout Grid 1.8.5, Kirki Customizer 5.2.2

### Marketing
- Klaviyo 3.7.2, MailPoet 5.21.2, Jetpack CRM 6.7.2
- Pinterest for WooCommerce 1.4.24, TikTok 1.3.7

### Performance & Security
- Jetpack 15.6-a.3, Jetpack Boost 4.5.7, Page Optimize 0.6.2
- Akismet 5.6, JWT Auth 1.5.0, WP OAuth Server CE 4.5.0
- Ally (Accessibility) 4.0.3

## Deployment

- Package as `.zip` for upload
- Clear Jetpack cache after deploy (10-15 min CDN propagation)
- SFTP available on Atomic platform
- Deploy script: `wordpress-theme/skyyrose-flagship/deploy-to-wpcom.py`

## Hooks & Filters

### Enqueue Scripts
```php
function my_enqueue() {
    wp_enqueue_style('brand-styles', get_template_directory_uri() . '/css/brand.css');
    wp_enqueue_script('main', get_template_directory_uri() . '/js/main.js', [], '1.0', true);
}
add_action('wp_enqueue_scripts', 'my_enqueue');
```

### Conditional Loading
```php
// Only load immersive scene JS on pages that use it (image-based, NOT Three.js)
if (is_page_template('template-immersive-black-rose.php')
    || is_page_template('template-immersive-love-hurts.php')
    || is_page_template('template-immersive-signature.php')) {
    wp_enqueue_script('immersive-scene', get_template_directory_uri() . '/assets/js/immersive-scene.js', [], '1.0', true);
    wp_enqueue_style('immersive-scene', get_template_directory_uri() . '/assets/css/immersive-scene.css');
}
```

### wp_localize_script
```php
wp_localize_script('assistant', 'skyyAIConfig', [
    'apiEndpoint' => 'https://api.skyyrose.co',
    'currentCollection' => get_query_var('collection'),
]);
```

## WooCommerce

### Product Categories
```php
wp_set_object_terms($product_id, 'black-rose', 'product_cat');
```

### Collections (Official Colors — Owner-Confirmed)
| Collection | Room/Theme | Official Colors | Accent Hex | IDs | SKU Prefix |
|------------|-----------|----------------|------------|-----|------------|
| BLACK ROSE | The Garden | Black, White, Metallic Silver | `#C0C0C0` | br-001..008 | SR-BR- |
| LOVE HURTS | The Ballroom | Red, Crimson, Black, White | `#DC143C` | lh-001..005 | SR-LH- |
| SIGNATURE | The Runway | Rose Gold, Gold | `#B76E79` | sg-001..014 | SR-SIG- |
| KIDS CAPSULE | — | Pink, Lavender | `#FFB6C1` | kids-001..002 | SR-KC- |

### Store Pages
- Shop → Collections page
- Cart → Shopping Cart page
- Checkout → Checkout page

### Hooks
```php
add_action('woocommerce_after_single_product_summary', 'my_recommendations', 20);
add_action('woocommerce_before_cart_totals', 'my_custom_notice');
```

## Security

### CSP Headers
```php
function skyyrose_add_csp_headers() {
    header("Content-Security-Policy: default-src 'self'; script-src 'self' cdn.jsdelivr.net;");
}
add_action('send_headers', 'skyyrose_add_csp_headers');
```

### Disable XML-RPC
```php
add_filter('xmlrpc_enabled', '__return_false');
```

### Hide WP Version
```php
remove_action('wp_head', 'wp_generator');
```
