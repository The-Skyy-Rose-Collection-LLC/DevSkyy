---
name: Performance Optimization
description: This skill activates when users discuss WordPress performance, WooCommerce optimization, slow queries, caching strategies, or site speed issues. Provides WordPress-specific optimization patterns with focus on database queries, transients, and plugin performance.
---

# WordPress Performance Optimization

Optimize WordPress and WooCommerce for speed, scale, and efficiency.

## When This Activates

- "slow WordPress", "performance", "optimization"
- "database queries", "caching", "transients"
- "WooCommerce slow", "plugin optimization"
- User reports WordPress performance issues
- Discussing WordPress speed improvements

---

## Database Optimization

### Optimize WooCommerce Queries

```php
// ❌ Bad: Loading full product objects
$products = wc_get_products(['limit' => 100]);
foreach ($products as $product) {
    echo $product->get_name();
}

// ✅ Good: Only load IDs, then get what you need
$product_ids = wc_get_products([
    'limit' => 100,
    'return' => 'ids', // Only IDs, much faster
]);

foreach ($product_ids as $id) {
    echo get_the_title($id);
}
```

### Add Database Indexes

```php
// Add indexes for frequently queried meta
function skyyrose_add_custom_indexes() {
    global $wpdb;

    // Index for collection filtering
    $wpdb->query("
        CREATE INDEX IF NOT EXISTS idx_skyyrose_collection
        ON {$wpdb->postmeta} (meta_key(191), meta_value(191))
        WHERE meta_key = '_skyyrose_collection'
    ");

    // Index for featured products
    $wpdb->query("
        CREATE INDEX IF NOT EXISTS idx_featured_products
        ON {$wpdb->postmeta} (meta_key(191), meta_value(191))
        WHERE meta_key = '_featured' AND meta_value = 'yes'
    ");
}
add_action('after_switch_theme', 'skyyrose_add_custom_indexes');
```

### Use Transients for Expensive Queries

```php
function get_skyyrose_featured_products() {
    $cache_key = 'skyyrose_featured_products_v2';
    $products = get_transient($cache_key);

    if (false === $products) {
        // Expensive query
        $products = wc_get_products([
            'meta_key' => '_featured',
            'meta_value' => 'yes',
            'limit' => 8,
            'return' => 'ids',
        ]);

        // Cache for 1 hour
        set_transient($cache_key, $products, HOUR_IN_SECONDS);
    }

    return $products;
}

// Invalidate cache when products change
add_action('woocommerce_update_product', function($product_id) {
    delete_transient('skyyrose_featured_products_v2');
});
```

---

## Object Caching

### Setup Redis/Memcached

```php
// wp-config.php
define('WP_CACHE', true);
define('WP_CACHE_KEY_SALT', 'skyyrose_');

// With Redis
if (class_exists('Redis')) {
    $redis = new Redis();
    $redis->connect('127.0.0.1', 6379);
    wp_cache_add_global_groups(['users', 'userlogins', 'usermeta']);
}
```

### Use Object Cache

```php
function get_skyyrose_product_data($product_id) {
    $cache_key = 'product_data_' . $product_id;
    $cache_group = 'skyyrose_products';

    // Try cache first
    $data = wp_cache_get($cache_key, $cache_group);

    if (false === $data) {
        // Build data
        $product = wc_get_product($product_id);
        $data = [
            'name' => $product->get_name(),
            'price' => $product->get_price(),
            'image' => wp_get_attachment_url($product->get_image_id()),
            'collection' => get_post_meta($product_id, '_skyyrose_collection', true),
        ];

        // Cache for 1 hour
        wp_cache_set($cache_key, $data, $cache_group, HOUR_IN_SECONDS);
    }

    return $data;
}
```

---

## Query Optimization

### Avoid Post Meta Queries

```php
// ❌ Bad: Meta query (slow on large datasets)
$args = [
    'post_type' => 'product',
    'meta_query' => [
        [
            'key' => '_skyyrose_collection',
            'value' => 'black_rose',
        ],
    ],
];
$query = new WP_Query($args);

// ✅ Good: Use taxonomy instead
register_taxonomy('skyyrose_collection', 'product', [
    'hierarchical' => true,
    'label' => 'Collections',
]);

// Query by taxonomy (much faster with proper indexes)
$args = [
    'post_type' => 'product',
    'tax_query' => [
        [
            'taxonomy' => 'skyyrose_collection',
            'field' => 'slug',
            'terms' => 'black-rose',
        ],
    ],
];
$query = new WP_Query($args);
```

### Optimize Main Query

```php
// Limit posts per page
function skyyrose_posts_per_page($query) {
    if (!is_admin() && $query->is_main_query()) {
        if (is_post_type_archive('product')) {
            $query->set('posts_per_page', 12); // Paginate, don't load all
        }
    }
}
add_action('pre_get_posts', 'skyyrose_posts_per_page');
```

---

## Asset Optimization

### Defer Non-Critical Scripts

```php
function skyyrose_defer_scripts($tag, $handle, $src) {
    // Scripts to defer
    $defer = [
        'elementor-frontend',
        'swiper',
        'jquery-slick',
        'aos',
    ];

    if (in_array($handle, $defer)) {
        return str_replace(' src=', ' defer src=', $tag);
    }

    return $tag;
}
add_filter('script_loader_tag', 'skyyrose_defer_scripts', 10, 3);
```

### Remove Unused Assets

```php
function skyyrose_dequeue_unused_assets() {
    // Remove jQuery Migrate (WordPress 5.5+)
    wp_deregister_script('jquery');
    wp_register_script('jquery', includes_url('/js/jquery/jquery.min.js'), [], null, true);

    // Remove block library CSS if not using Gutenberg
    if (!is_singular() || !has_blocks()) {
        wp_dequeue_style('wp-block-library');
        wp_dequeue_style('wp-block-library-theme');
        wp_dequeue_style('wc-blocks-style');
    }

    // Remove emoji scripts
    remove_action('wp_head', 'print_emoji_detection_script', 7);
    remove_action('wp_print_styles', 'print_emoji_styles');
}
add_action('wp_enqueue_scripts', 'skyyrose_dequeue_unused_assets', 100);
```

### Conditionally Load Scripts

```php
function skyyrose_conditional_scripts() {
    // Only load WooCommerce scripts on shop pages
    if (!is_woocommerce() && !is_cart() && !is_checkout()) {
        wp_dequeue_script('wc-cart-fragments');
        wp_dequeue_script('woocommerce');
        wp_dequeue_style('woocommerce-layout');
        wp_dequeue_style('woocommerce-smallscreen');
        wp_dequeue_style('woocommerce-general');
    }

    // Only load 3D viewer on product pages
    if (!is_product()) {
        wp_dequeue_script('three-js');
        wp_dequeue_script('skyy-3d-viewer');
    }
}
add_action('wp_enqueue_scripts', 'skyyrose_conditional_scripts', 99);
```

---

## Image Optimization

### Lazy Loading (Native)

```php
// Enable native lazy loading
add_filter('wp_get_attachment_image_attributes', function($attr) {
    $attr['loading'] = 'lazy';
    return $attr;
});
```

### WebP Conversion

```php
function skyyrose_webp_uploads($image, $attachment_id, $size) {
    // Convert uploaded images to WebP
    $file = get_attached_file($attachment_id);

    if (function_exists('imagewebp')) {
        $info = pathinfo($file);
        $webp_file = $info['dirname'] . '/' . $info['filename'] . '.webp';

        $image_resource = null;
        if ($info['extension'] === 'jpg' || $info['extension'] === 'jpeg') {
            $image_resource = imagecreatefromjpeg($file);
        } elseif ($info['extension'] === 'png') {
            $image_resource = imagecreatefrompng($file);
        }

        if ($image_resource) {
            imagewebp($image_resource, $webp_file, 80);
            imagedestroy($image_resource);
        }
    }

    return $image;
}
add_filter('wp_generate_attachment_metadata', 'skyyrose_webp_uploads', 10, 3);
```

---

## WooCommerce Specific

### Disable Cart Fragments (AJAX)

```php
// Cart fragments cause constant AJAX requests
function skyyrose_disable_cart_fragments() {
    if (is_front_page() || is_page()) {
        wp_dequeue_script('wc-cart-fragments');
    }
}
add_action('wp_enqueue_scripts', 'skyyrose_disable_cart_fragments', 100);

// Alternative: Update cart on page load instead
function skyyrose_update_cart_on_load() {
    if (is_cart() || is_checkout()) {
        WC()->cart->calculate_totals();
    }
}
add_action('wp_loaded', 'skyyrose_update_cart_on_load');
```

### Optimize Product Thumbnails

```php
function skyyrose_optimize_product_thumbnails() {
    // Reduce number of thumbnails generated
    add_filter('woocommerce_product_thumbnails_columns', function() {
        return 3; // Instead of default 4
    });

    // Disable gallery zoom (uses large images)
    add_filter('woocommerce_single_product_zoom_enabled', '__return_false');
}
add_action('after_setup_theme', 'skyyrose_optimize_product_thumbnails');
```

---

## Plugin Optimization

### Limit Plugin Usage

```php
// Disable plugins on specific pages
function skyyrose_disable_plugins_conditionally($plugins) {
    // Disable contact form on shop pages
    if (is_shop() || is_product()) {
        $plugins = array_filter($plugins, function($plugin) {
            return strpos($plugin, 'contact-form') === false;
        });
    }

    return $plugins;
}
add_filter('option_active_plugins', 'skyyrose_disable_plugins_conditionally');
```

---

## Monitoring & Profiling

### Query Monitor Plugin

```php
// Add custom timing markers
if (function_exists('do_action') && defined('QM_ENABLED') && QM_ENABLED) {
    do_action('qm/start', 'skyyrose_expensive_operation');

    // ... expensive code here ...

    do_action('qm/stop', 'skyyrose_expensive_operation');
}
```

### Log Slow Queries

```php
// wp-config.php
define('SAVEQUERIES', true);

// Log queries taking > 0.05 seconds
add_action('shutdown', function() {
    if (!defined('SAVEQUERIES') || !SAVEQUERIES) return;

    global $wpdb;
    $slow_queries = [];

    foreach ($wpdb->queries as $query) {
        if ($query[1] > 0.05) {
            $slow_queries[] = [
                'query' => $query[0],
                'time' => $query[1],
                'stack' => $query[2],
            ];
        }
    }

    if (!empty($slow_queries)) {
        error_log('Slow queries: ' . print_r($slow_queries, true));
    }
});
```

---

## Caching Strategy

### Page Caching

```php
// W3 Total Cache or WP Rocket recommended
// Custom page cache header
function skyyrose_set_cache_headers() {
    if (!is_user_logged_in() && !is_admin()) {
        header('Cache-Control: public, max-age=3600');
        header('Expires: ' . gmdate('D, d M Y H:i:s', time() + 3600) . ' GMT');
    }
}
add_action('send_headers', 'skyyrose_set_cache_headers');
```

### Fragment Caching

```php
function skyyrose_cached_fragment($key, $ttl, $callback) {
    $output = get_transient($key);

    if (false === $output) {
        ob_start();
        call_user_func($callback);
        $output = ob_get_clean();
        set_transient($key, $output, $ttl);
    }

    echo $output;
}

// Usage in template
skyyrose_cached_fragment(
    'homepage_featured_products',
    HOUR_IN_SECONDS,
    function() {
        get_template_part('template-parts/featured-products');
    }
);
```

---

## WordPress.com Specific

### Jetpack Optimizations

```php
function skyyrose_optimize_jetpack() {
    // Disable unused Jetpack modules
    add_filter('jetpack_get_available_modules', function($modules) {
        $disabled = ['carousel', 'tiled-gallery', 'sharedaddy'];
        return array_diff_key($modules, array_flip($disabled));
    });

    // Use Jetpack CDN for images
    add_filter('jetpack_photon_skip_image', '__return_false');
}
add_action('after_setup_theme', 'skyyrose_optimize_jetpack');
```

---

## Quick Wins Checklist

For SkyyRose WordPress site:

- [ ] **Database**: Add indexes, use transients
- [ ] **Caching**: Enable object cache (Redis), page cache
- [ ] **Assets**: Defer non-critical scripts, remove unused CSS/JS
- [ ] **Images**: Lazy load, WebP format, proper sizes
- [ ] **WooCommerce**: Disable cart fragments, optimize thumbnails
- [ ] **Queries**: Limit posts per page, use tax queries not meta
- [ ] **Plugins**: Disable on pages where not needed
- [ ] **CDN**: Use WordPress.com CDN or Cloudflare
- [ ] **Monitoring**: Install Query Monitor, log slow queries

---

## Performance Budget

For SkyyRose:

| Metric | Target | Current | Actions |
|--------|--------|---------|---------|
| **TTFB** | < 600ms | 450ms | ✅ Good |
| **LCP** | < 2.5s | 2.1s | ✅ Good |
| **DB Queries** | < 50 | 67 | ⚠️ Optimize |
| **Page Size** | < 2MB | 1.8MB | ✅ Good |
| **Requests** | < 50 | 42 | ✅ Good |

---

## When User Reports Slow WordPress Site

1. **Profile first**: Install Query Monitor, check slow queries
2. **Identify bottleneck**: Database? Assets? Plugins?
3. **Quick wins**: Enable caching, optimize images, defer scripts
4. **Deep optimization**: Add indexes, fragment caching, CDN
5. **Monitor**: Track metrics, set performance budget

Always measure before and after to prove improvements.
