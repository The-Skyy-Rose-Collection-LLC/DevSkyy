---
name: woocommerce
description: WordPress and WooCommerce development guidelines with PHP best practices, security standards, and extensibility patterns
---

# WooCommerce Development

You are an expert in WordPress and WooCommerce development, PHP best practices, and e-commerce solutions.

## Core Principles

- Follow WordPress coding standards
- Use WooCommerce hooks and filters properly
- Prioritize security in all code
- Maintain backwards compatibility
- Write performant, scalable code

## PHP Best Practices

### Coding Standards

- Follow WordPress PHP Coding Standards
- Use meaningful function and variable names
- Prefix all functions and classes to avoid conflicts
- Document code with PHPDoc comments

### Namespacing

```php
namespace MyPlugin\WooCommerce;

class ProductHandler {
    public function __construct() {
        add_action('woocommerce_before_add_to_cart_form', [$this, 'custom_content']);
    }

    public function custom_content() {
        // Custom functionality
    }
}
```

## WooCommerce Hooks

### Action Hooks

```php
// Add content after product summary
add_action('woocommerce_after_single_product_summary', 'custom_product_content', 15);
function custom_product_content() {
    echo '<div class="custom-content">Additional information</div>';
}

// Modify order processing
add_action('woocommerce_order_status_completed', 'process_completed_order', 10, 1);
function process_completed_order($order_id) {
    $order = wc_get_order($order_id);
    // Process order
}
```

### Filter Hooks

```php
// Modify product price display
add_filter('woocommerce_get_price_html', 'custom_price_html', 10, 2);
function custom_price_html($price, $product) {
    if ($product->is_on_sale()) {
        $price .= '<span class="sale-badge">Sale!</span>';
    }
    return $price;
}

// Add custom checkout fields
add_filter('woocommerce_checkout_fields', 'custom_checkout_fields');
function custom_checkout_fields($fields) {
    $fields['billing']['billing_custom_field'] = [
        'type' => 'text',
        'label' => __('Custom Field', 'textdomain'),
        'required' => false,
        'priority' => 25,
    ];
    return $fields;
}
```

## Security

### Data Validation

```php
// Sanitize input
$product_id = absint($_POST['product_id']);
$quantity = wc_stock_amount($_POST['quantity']);
$email = sanitize_email($_POST['email']);

// Escape output
echo esc_html($product->get_name());
echo esc_url($product->get_permalink());
echo wp_kses_post($product->get_description());
```

### Nonce Verification

```php
// Create nonce
wp_nonce_field('custom_action', 'custom_nonce');

// Verify nonce
if (!wp_verify_nonce($_POST['custom_nonce'], 'custom_action')) {
    wp_die(__('Security check failed', 'textdomain'));
}
```

### Capability Checks

```php
if (!current_user_can('manage_woocommerce')) {
    wp_die(__('Unauthorized access', 'textdomain'));
}
```

## Custom Product Types

```php
class WC_Product_Custom extends WC_Product {
    public function get_type() {
        return 'custom';
    }

    // Custom methods
}

add_filter('product_type_selector', function($types) {
    $types['custom'] = __('Custom Product', 'textdomain');
    return $types;
});
```

## REST API Extensions

```php
add_action('rest_api_init', function() {
    register_rest_route('custom/v1', '/products/featured', [
        'methods' => 'GET',
        'callback' => 'get_featured_products',
        'permission_callback' => '__return_true',
    ]);
});

function get_featured_products($request) {
    $args = [
        'status' => 'publish',
        'featured' => true,
        'limit' => 10,
    ];
    $products = wc_get_products($args);
    return rest_ensure_response($products);
}
```

## HPOS (High-Performance Order Storage)

WooCommerce 8.2+ can store orders in dedicated tables (`wp_wc_orders`, `wp_wc_order_addresses`, etc.)
instead of `wp_posts`/`wp_postmeta`. The data-store API abstracts both backends — your code must
never query order tables directly.

### Declare HPOS compatibility

Place this in your main plugin file (fires before WooCommerce initializes):

```php
add_action( 'before_woocommerce_init', function() {
    if ( class_exists( \Automattic\WooCommerce\Utilities\FeaturesUtil::class ) ) {
        \Automattic\WooCommerce\Utilities\FeaturesUtil::declare_compatibility(
            'custom_order_tables',
            __FILE__,
            true   // true = compatible, false = incompatible
        );
    }
} );
```

Without this declaration WooCommerce shows a warning in wp-admin and may disable HPOS for
stores running your plugin.

### Order CRUD via the data-store API

Always use the WC data-store layer — never `$wpdb` against `wp_posts` or `wp_postmeta` for orders:

```php
// Fetch a single order
$order = wc_get_order( $order_id );      // returns WC_Order or false
if ( $order ) {
    $status  = $order->get_status();
    $total   = $order->get_total();
    $email   = $order->get_billing_email();

    // Write via setters, persist with save()
    $order->update_status( 'completed', 'Fulfilled via API.' );
    $order->update_meta_data( '_custom_key', 'value' );
    $order->save();
}

// Query multiple orders
$orders = wc_get_orders( [
    'status' => [ 'processing', 'on-hold' ],
    'limit'  => 20,
    'return' => 'objects',   // or 'ids'
] );

// Advanced query with WC_Order_Query
$query  = new WC_Order_Query( [
    'customer_id' => get_current_user_id(),
    'date_after'  => '2024-01-01',
    'orderby'     => 'date',
    'order'       => 'DESC',
] );
$orders = $query->get_orders();
```

Why: with HPOS enabled orders live in `wp_wc_orders`; with legacy storage they live in `wp_posts`.
`wc_get_order()`, `wc_get_orders()`, and `WC_Order_Query` handle both transparently. A raw
`$wpdb` query against `wp_posts` will silently return stale or missing data on HPOS stores.

### SkyyRose context

skyyrose.co runs WordPress.com Atomic + WooCommerce. REST API writes use the `?rest_route=/wc/v3`
form (not `/wp-json/wc/v3` — WP.com Atomic returns 401 on the `/wp-json/` path). The WC
data-store API works identically on Atomic; HPOS compatibility declaration is still required for
any plugin deployed to the store.

## Database Operations

```php
// Products: WC data stores work the same way
$product = new WC_Product_Simple();
$product->set_name( 'New Product' );
$product->set_regular_price( '29.99' );
$product->save();   // returns product ID

// Direct $wpdb is acceptable for custom plugin tables (not WC core tables)
global $wpdb;
$results = $wpdb->get_results( $wpdb->prepare(
    "SELECT * FROM {$wpdb->prefix}my_plugin_table WHERE status = %s",
    'active'
) );
```

## Performance

- Use transients for caching
- Optimize database queries
- Lazy load when possible
- Minimize HTTP requests
- Use object caching

### Caching

```php
$cached_data = get_transient('custom_product_data');
if (false === $cached_data) {
    $cached_data = expensive_query();
    set_transient('custom_product_data', $cached_data, HOUR_IN_SECONDS);
}
```

## Testing

- Write unit tests with PHPUnit
- Use WP_UnitTestCase for WordPress tests
- Test with WooCommerce test helpers
- Validate with PHPCS WordPress standards
