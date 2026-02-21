# WordPress Knowledge Base

## Theme Architecture (Block/FSE Themes)

### Required Files
- `theme.json` — Global settings and styles (version 2)
- `style.css` — Theme metadata header (name, version, text domain)
- `templates/` — Block templates (index.html, single.html, page.html, archive.html)
- `parts/` — Template parts (header.html, footer.html, sidebar.html)
- `patterns/` — Block patterns (reusable layouts)
- `functions.php` — PHP hooks, filters, enqueue, REST API

### theme.json Structure (Version 2)
```json
{
  "$schema": "https://schemas.wp.org/trunk/theme.json",
  "version": 2,
  "settings": {
    "color": { "palette": [...] },
    "typography": { "fontFamilies": [...] },
    "spacing": { "spacingScale": {...} },
    "layout": { "contentSize": "800px", "wideSize": "1200px" }
  },
  "styles": { ... },
  "templateParts": [...],
  "customTemplates": [...],
  "patterns": [...]
}
```

## WordPress.com Specifics

### REST API
- **CRITICAL**: Use `index.php?rest_route=` NOT `/wp-json/`
- Example: `https://skyyrose.co/index.php?rest_route=/wp/v2/posts`
- Authentication: Bearer token or application passwords

### Jetpack CDN
- Images served via `i0.wp.com`, `i1.wp.com`, `i2.wp.com`
- Cache invalidation: 10-15 minutes propagation
- Photon transforms: `?w=800&h=600&crop=1`

### Atomic Platform
- SSH/SFTP access available
- PHP 8.x runtime
- WP-CLI available via SSH

## Hooks and Filters

### Action Hooks (Common)
- `wp_enqueue_scripts` — Enqueue CSS/JS (priority 10 default)
- `after_setup_theme` — Theme support, menus, image sizes
- `init` — Register post types, taxonomies, shortcodes
- `wp_head` — Output in `<head>` (CSP headers, meta tags)
- `wp_footer` — Output before `</body>`
- `widgets_init` — Register widget areas

### Filter Hooks (Common)
- `the_content` — Modify post content
- `body_class` — Add CSS classes to body
- `script_loader_tag` — Modify script tags (add async/defer)
- `wp_resource_hints` — Preconnect, prefetch, preload

## WooCommerce Integration

### Required Pages
- Shop page (product archive)
- Cart page
- Checkout page
- My Account page

### Key Hooks
- `woocommerce_before_cart` — Before cart table
- `woocommerce_checkout_process` — Validate checkout
- `woocommerce_payment_complete` — After successful payment
- `woocommerce_thankyou` — Thank you page

### REST API
- Products: `/wc/v3/products` (consumer key/secret auth)
- Orders: `/wc/v3/orders`
- Customers: `/wc/v3/customers`

## Common Mistakes
- Using `/wp-json/` on WordPress.com (use `index.php?rest_route=`)
- Not registering theme support (`add_theme_support()`)
- Hardcoding URLs (use `get_template_directory_uri()`)
- Missing `text_domain` in `__()` and `_e()` calls
- Not escaping output (`esc_html()`, `esc_attr()`, `esc_url()`)
- Enqueuing scripts without dependencies
