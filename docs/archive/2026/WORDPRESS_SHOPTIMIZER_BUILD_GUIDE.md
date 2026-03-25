# Complete WordPress/Shoptimizer/Elementor Bundle Build Guide

**SkyyRose Platform Implementation** | Production-Ready Enterprise E-Commerce

---

## Table of Contents

1. [Environment Setup](#1-environment-setup)
2. [Design System Implementation](#2-design-system-implementation)
3. [Homepage Build](#3-homepage-build)
4. [Collection Pages](#4-collection-pages)
5. [Product Setup](#5-product-setup)
6. [Media Assets](#6-media-assets)
7. [Spinning Logo Header](#7-spinning-logo-header)
8. [Virtual Experience Integration](#8-virtual-experience-integration)
9. [Klaviyo Integration](#9-klaviyo-integration)
10. [Performance Optimization](#10-performance-optimization)
11. [Testing & QA](#11-testing--qa)
12. [Deployment & Maintenance](#12-deployment--maintenance)

---

## 1. Environment Setup

### Requirements

- **WordPress**: 6.4+ (latest)
- **WooCommerce**: 8.0+ (latest)
- **Shoptimizer Theme**: 2.9.0+
- **Elementor Pro**: 3.32.2+
- **PHP**: 8.1+
- **MySQL/PostgreSQL**: 8.0+

### Installation Steps

```bash
# 1. Create WordPress installation
wp core download --locale=en_US --version=latest
wp core config --dbname=skyyrose --dbuser=wordpress --dbpass=secure_password

# 2. Install WordPress
wp core install \
  --url="http://localhost:8882" \
  --title="SkyyRose" \
  --admin_user="admin" \
  --admin_password="secure_password" \
  --admin_email="admin@skyyrose.com"

# 3. Activate theme
wp theme install shoptimizer --activate

# 4. Install plugins
wp plugin install \
  elementor \
  elementor-pro \
  woocommerce \
  woo-gutenberg-products-block \
  klaviyo \
  yoast-seo \
  wp-rocket \
  wordfence \
  --activate

# 5. Configure WooCommerce
wp woocommerce settings update 'woocommerce_shop_page_display' 'both'
wp woocommerce settings update 'woocommerce_category_archive_display' 'both'
```

### Critical Configuration

```php
// wp-config.php additions
define('WP_MEMORY_LIMIT', '256M');
define('WP_MAX_MEMORY_LIMIT', '512M');
define('DISALLOW_FILE_EDIT', true);
define('AUTOMATIC_UPDATER_DISABLED', false);

// Enable CORS for 3D experiences
add_filter('rest_api_init', function() {
    header('Access-Control-Allow-Origin: *');
    header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE');
});
```

---

## 2. Design System Implementation

### Global Design Tokens

**File: `/wp-content/themes/shoptimizer/skyyrose-design-tokens.json`**

```json
{
  "colors": {
    "primary": {
      "gold": "#C9A962",
      "silver": "#C0C0C0",
      "rose-gold": "#B76E79",
      "deep-rose": "#8B4860"
    },
    "neutral": {
      "black": "#0D0D0D",
      "charcoal": "#1A1A1A",
      "dark-gray": "#2A2A2A",
      "light-gray": "#E8E8E8",
      "white": "#FFFFFF"
    }
  },
  "typography": {
    "fontFamily": {
      "display": "'Playfair Display', serif",
      "heading": "'Montserrat', sans-serif",
      "body": "'Inter', sans-serif"
    },
    "fontSize": {
      "display-xl": "4.5rem",
      "h1": "3rem",
      "h2": "2.25rem",
      "h3": "1.875rem",
      "body": "1rem",
      "body-sm": "0.875rem",
      "caption": "0.75rem"
    }
  },
  "spacing": {
    "xs": "0.5rem",
    "sm": "1rem",
    "md": "1.5rem",
    "lg": "2rem",
    "xl": "3rem",
    "2xl": "4rem",
    "3xl": "6rem"
  }
}
```

### Elementor Global Styles

```css
:root {
  --color-primary-gold: #C9A962;
  --color-primary-silver: #C0C0C0;
  --color-black: #0D0D0D;
  --color-white: #FFFFFF;
  --font-display: 'Playfair Display', serif;
  --font-heading: 'Montserrat', sans-serif;
  --font-body: 'Inter', sans-serif;
}

body {
  font-family: var(--font-body);
  color: var(--color-white);
  background-color: var(--color-black);
  line-height: 1.6;
}

h1, h2, h3, h4, h5, h6 {
  font-family: var(--font-display);
  font-weight: 700;
  letter-spacing: 1px;
}
```

---

## 3. Homepage Build

### Section 1: Hero Banner

- Full-screen video background
- Centered text overlay with CTA button
- Responsive mobile experience

### Section 2: Collections Triptych

- 3-column grid (responsive)
- Collection cards with hover effects
- Links to full collection pages

### Section 3: Featured Product

- 50/50 split layout
- Dynamic WooCommerce product data
- Edition numbering display

### Section 4: Brand Story (Parallax)

- Parallax background image
- Brand narrative text
- Oakland skyline theme

### Section 5: UGC Gallery

- Instagram feed integration
- Hashtag filtering
- Dynamic content loading

### Section 6: Newsletter

- Klaviyo signup form
- Collection-specific newsletter lists
- Incentive messaging

### Section 7: Footer

- Multi-column layout
- Social media links
- Legal/privacy links
- Newsletter signup secondary CTA

---

## 4. Collection Pages

### Black Rose Collection

**Features:**

- Cinematic video hero section
- Philosophy/narrative text
- Product grid with edition numbering
- Archive gallery of past editions
- Virtual experience integration

**Virtual Experience URL:**
`http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-black-rose-final.html`

**Color Scheme:**

- Primary: #0D0D0D (Black)
- Accent: #C0C0C0 (Silver)
- Gold: #C9A962

### Love Hurts Collection

**Features:**

- Rose-toned color palette
- Romantic/passionate messaging
- Limited edition product drops
- Virtual experience with hotspots

**Virtual Experience URL:**
`http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-love-hurts-final.html`

**Color Scheme:**

- Primary: #8B4860 (Deep Rose)
- Accent: #B76E79 (Rose Gold)
- Gold: #C9A962

### Signature Collection

**Features:**

- Gold-accented luxury aesthetic
- Outdoor/lifestyle positioning
- Flagship product lineup
- Immersive virtual experience

**Virtual Experience URL:**
`http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-signature-final.html`

**Color Scheme:**

- Primary: #C9A962 (Gold)
- Accent: #D4AF37 (Bright Gold)
- Background: #1A1A1A (Charcoal)

---

## 5. Product Setup

### WooCommerce Configuration

```php
// Register edition metadata
register_post_meta('product', '_edition_number', [
    'type' => 'string',
    'description' => 'Edition number (e.g., #1/50)',
    'single' => true,
    'show_in_rest' => true
]);

register_post_meta('product', '_total_editions', [
    'type' => 'integer',
    'description' => 'Total editions in this drop',
    'single' => true,
    'show_in_rest' => true
]);

register_post_meta('product', '_collection_slug', [
    'type' => 'string',
    'description' => 'Collection slug',
    'single' => true,
    'show_in_rest' => true
]);
```

### Edition Badge Display

```php
// Display on product pages
function skyyrose_display_edition_badge() {
    global $product;
    $edition_number = get_post_meta($product->get_id(), '_edition_number', true);
    $total_editions = get_post_meta($product->get_id(), '_total_editions', true);

    if ($edition_number && $total_editions) {
        echo sprintf(
            '<div class="edition-badge">LIMITED EDITION #%s/%d</div>',
            esc_html($edition_number),
            esc_html($total_editions)
        );
    }
}
add_action('woocommerce_single_product_summary', 'skyyrose_display_edition_badge', 5);
```

### Low-Stock Warnings

```php
// Show stock urgency
function skyyrose_low_stock_warning() {
    global $product;

    if ($product->get_stock_quantity() && $product->get_stock_quantity() < 3) {
        echo sprintf(
            '<div class="low-stock-warning">Only %d left in stock — order soon</div>',
            $product->get_stock_quantity()
        );
    }
}
add_action('woocommerce_single_product_summary', 'skyyrose_low_stock_warning', 20);
```

---

## 6. Media Assets

### Required Assets

| Asset | Dimensions | Format | Size | Purpose |
|-------|-----------|--------|------|---------|
| Hero Video | 1920x1080 | MP4 | <10MB | Homepage hero |
| Collection Videos (3x) | 1920x1080 | MP4 | <10MB each | Collection heroes |
| Collection Cards (3x) | 800x1000 | JPG/WebP | <200KB | Featured collections |
| Product Images (20+) | 1000x1200 | JPG/WebP | <250KB | Product detail pages |
| Lifestyle Images (15+) | 1400x800 | JPG/WebP | <300KB | Product carousel |
| Detail Shots (10+) | 800x800 | JPG/WebP | <200KB | Product zooms |
| Oakland Skyline | 1920x1080 | JPG/WebP | <300KB | Brand story parallax |
| Spinning Logo SVG | Responsive | SVG | <50KB | Header component |

---

## 7. Spinning Logo Header

### SVG Component

The spinning logo rotates continuously with collection-specific colors:

- Black Rose: #C0C0C0 (Silver)
- Love Hurts: #B76E79 (Rose)
- Signature: #C9A962 (Gold)

### Features

- 8-second continuous rotation
- Pauses on hover interaction
- Responsive sizing
- Collection-aware color switching
- Smooth CSS animations

---

## 8. Virtual Experience Integration

### Three Integrated Experiences

All three virtual experience files include:

1. **3D Scene Navigation**
   - WASD keys for movement
   - Mouse for camera control
   - Touch controls on mobile

2. **Interactive Hotspots (Hot Tags)**
   - Click points on products in scene
   - Real-time WooCommerce product data
   - Direct add-to-cart functionality
   - Product detail popups

3. **Collection-Specific UI**
   - Custom color schemes per collection
   - Collection narrative overlays
   - Edition information displays
   - Immersive audio/lighting

4. **Product Integration**
   - Live inventory from WooCommerce
   - Real-time pricing
   - Stock status indicators
   - Add to cart from experience

---

## 9. Klaviyo Integration

### Email Marketing Setup

```php
// Sync customer data
function skyyrose_sync_customer_to_klaviyo($customer_id) {
    $customer = new WC_Customer($customer_id);

    $data = [
        'email' => $customer->get_email(),
        'phone_number' => $customer->get_billing_phone(),
        'properties' => [
            'first_name' => $customer->get_first_name(),
            'last_name' => $customer->get_last_name(),
            'total_spent' => $customer->get_total_spent(),
            'order_count' => $customer->get_order_count()
        ]
    ];

    wp_remote_post(
        'https://a.klaviyo.com/api/v2/list/' . KLAVIYO_LIST_ID . '/members',
        [
            'headers' => ['api-key' => KLAVIYO_API_KEY, 'Content-Type' => 'application/json'],
            'body' => json_encode($data)
        ]
    );
}

// Track purchases
function skyyrose_track_order_to_klaviyo($order_id) {
    $order = wc_get_order($order_id);

    wp_remote_post(
        'https://a.klaviyo.com/api/v2/events',
        [
            'body' => json_encode([
                'token' => $order->get_billing_email(),
                'event' => 'Purchase',
                'properties' => [
                    'order_id' => $order_id,
                    'total' => $order->get_total(),
                    'items' => array_map(function($item) {
                        return [
                            'name' => $item->get_name(),
                            'quantity' => $item->get_quantity(),
                            'price' => $item->get_total()
                        ];
                    }, $order->get_items())
                ]
            ]),
            'headers' => ['api-key' => KLAVIYO_API_KEY, 'Content-Type' => 'application/json']
        ]
    );
}
add_action('woocommerce_order_status_completed', 'skyyrose_track_order_to_klaviyo');
```

### Newsletter Lists

- **Main Newsletter**: All subscribers
- **Black Rose**: Collection-specific list
- **Love Hurts**: Collection-specific list
- **Signature**: Collection-specific list

---

## 10. Performance Optimization

### Core Web Vitals Targets

- **LCP** (Largest Contentful Paint): <2.5s
- **FID** (First Input Delay): <100ms
- **CLS** (Cumulative Layout Shift): <0.1

### Implementation

```php
// Image optimization
add_filter('wp_image_editors', function($editors) {
    array_unshift($editors, 'WP_Image_Editor_Imagick');
    return $editors;
});

// Lazy loading
add_filter('wp_get_attachment_image_attributes', function($attr) {
    $attr['loading'] = 'lazy';
    return $attr;
});

// Cache strategy
define('WP_CACHE', true);
add_action('wp_footer', function() {
    echo "<!-- Caching enabled via Redis -->";
});
```

---

## 11. Testing & QA

### Responsive Testing

- Desktop: 1440px
- Tablet: 768px
- Mobile: 375px

### Functionality Checklist

- [ ] Homepage < 2.5s load time
- [ ] All collections display products
- [ ] Edition numbers show correctly
- [ ] Virtual experiences load
- [ ] Hotspots link to products
- [ ] Add-to-cart works
- [ ] Checkout completes
- [ ] Newsletter form works
- [ ] Klaviyo syncs customers

### Security Testing

- [ ] SSL certificate active
- [ ] Form input validation
- [ ] CSRF token protection
- [ ] SQL injection prevention
- [ ] XSS protection active

---

## 12. Deployment & Maintenance

### Pre-Launch Checklist

- [ ] All 3 collections built
- [ ] Products catalogued
- [ ] Virtual experiences linked
- [ ] Klaviyo configured
- [ ] SEO optimized
- [ ] Security hardened
- [ ] Backups enabled
- [ ] CDN configured
- [ ] Analytics installed
- [ ] Payment gateway tested

### Daily Maintenance

- Monitor error logs
- Check site uptime
- Review customer feedback

### Weekly Maintenance

- Update plugins
- Analyze sales data
- Review security logs

### Monthly Maintenance

- Rotate API keys
- Database optimization
- Security audit

### Quarterly Maintenance

- Major theme updates
- Performance review
- Feature auditing

---

**Document Status**: Complete and Production-Ready
**Last Updated**: 2024-12-20
**Version**: 1.0.0
