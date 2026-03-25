---
name: WooCommerce Integration
description: Expert knowledge in WooCommerce development, hooks, filters, custom functionality, product types, and REST API integration. ALWAYS verify with Context7 for up-to-date WooCommerce 8.5+ documentation. Triggers on keywords like "woocommerce", "product", "cart", "checkout", "wc_", "shop", "orders".
version: 1.0.0
---

# WooCommerce Integration

Build custom WooCommerce functionality with hooks, filters, REST API, and SkyyRose luxury e-commerce features.

**CRITICAL**: Always use Context7 to verify current WooCommerce 8.5+ documentation before implementing.

## When to Use This Skill

Activate when working on:
- WooCommerce product customization
- Custom checkout flows
- Cart modifications
- Order management
- Product types (simple, variable, grouped)
- WooCommerce hooks and filters
- REST API integration
- Payment gateway customization

## WooCommerce Structure

### Core Files

```
wp-content/plugins/woocommerce/
├── includes/
│   ├── wc-template-functions.php  # Template functions
│   ├── wc-product-functions.php   # Product utilities
│   └── class-wc-product.php       # Product class
│
└── templates/                      # Template files
    ├── single-product.php
    ├── archive-product.php
    ├── cart/
    └── checkout/
```

### Theme Overrides

```
skyyrose-2025/
└── woocommerce/                    # WooCommerce template overrides
    ├── single-product.php          # Product page
    ├── archive-product.php         # Shop page
    ├── cart/
    │   ├── cart.php
    │   └── mini-cart.php
    ├── checkout/
    │   ├── form-checkout.php
    │   └── thankyou.php
    └── content-product.php         # Product loop item
```

## Context7 Verification Required

**Before implementing ANY WooCommerce code:**

```bash
# 1. Resolve WooCommerce library ID
resolve-library-id --query="WooCommerce hooks and filters" --library-name="woocommerce"

# 2. Query current documentation
query-docs --library-id="/woocommerce/woocommerce" --query="custom product fields"

# 3. Implement following verified patterns
```

**Never use deprecated hooks** - Context7 ensures you use current APIs.

## Product Customization

### Add Custom Product Fields

```php
<?php
/**
 * Add custom product fields (Meta Box)
 * VERIFIED: WooCommerce 8.5+ compatible
 */
add_action('woocommerce_product_options_general_product_data', 'skyyrose_add_custom_product_fields');

function skyyrose_add_custom_product_fields() {
    global $product_object;

    echo '<div class="options_group">';

    // Collection field
    woocommerce_wp_select([
        'id'      => '_skyyrose_collection',
        'label'   => __('Collection', 'skyyrose'),
        'options' => [
            ''            => __('Select collection...', 'skyyrose'),
            'signature'   => __('Signature Collection', 'skyyrose'),
            'black_rose'  => __('Black Rose Collection', 'skyyrose'),
            'love_hurts'  => __('Love Hurts Collection', 'skyyrose'),
        ],
        'value'   => $product_object ? $product_object->get_meta('_skyyrose_collection') : '',
    ]);

    // 3D Model URL
    woocommerce_wp_text_input([
        'id'          => '_3d_model_url',
        'label'       => __('3D Model URL', 'skyyrose'),
        'placeholder' => 'https://assets.skyyrose.co/models/product.glb',
        'desc_tip'    => true,
        'description' => __('URL to the 3D model (.glb or .gltf)', 'skyyrose'),
        'value'       => $product_object ? $product_object->get_meta('_3d_model_url') : '',
    ]);

    // Materials
    woocommerce_wp_textarea_input([
        'id'          => '_materials_description',
        'label'       => __('Materials Description', 'skyyrose'),
        'placeholder' => '.925 Sterling Silver, Conflict-Free Diamonds',
        'value'       => $product_object ? $product_object->get_meta('_materials_description') : '',
    ]);

    // Craftsmanship hours
    woocommerce_wp_text_input([
        'id'          => '_craftsmanship_hours',
        'label'       => __('Craftsmanship Hours', 'skyyrose'),
        'type'        => 'number',
        'custom_attributes' => [
            'step' => '0.5',
            'min'  => '0',
        ],
        'value'       => $product_object ? $product_object->get_meta('_craftsmanship_hours') : '',
    ]);

    echo '</div>';
}

// Save custom fields
add_action('woocommerce_admin_process_product_object', 'skyyrose_save_custom_product_fields');

function skyyrose_save_custom_product_fields($product) {
    // Collection
    if (isset($_POST['_skyyrose_collection'])) {
        $product->update_meta_data('_skyyrose_collection', sanitize_text_field($_POST['_skyyrose_collection']));
    }

    // 3D Model URL
    if (isset($_POST['_3d_model_url'])) {
        $product->update_meta_data('_3d_model_url', esc_url_raw($_POST['_3d_model_url']));
    }

    // Materials
    if (isset($_POST['_materials_description'])) {
        $product->update_meta_data('_materials_description', sanitize_textarea_field($_POST['_materials_description']));
    }

    // Craftsmanship hours
    if (isset($_POST['_craftsmanship_hours'])) {
        $product->update_meta_data('_craftsmanship_hours', floatval($_POST['_craftsmanship_hours']));
    }
}
```

### Display Custom Fields on Product Page

```php
<?php
/**
 * Display custom fields on product page
 */
add_action('woocommerce_single_product_summary', 'skyyrose_display_product_meta', 25);

function skyyrose_display_product_meta() {
    global $product;

    $collection = $product->get_meta('_skyyrose_collection');
    $materials = $product->get_meta('_materials_description');
    $hours = $product->get_meta('_craftsmanship_hours');

    if (!$collection && !$materials && !$hours) {
        return;
    }

    echo '<div class="skyyrose-product-meta">';

    if ($collection) {
        $collection_names = [
            'signature'  => __('Signature Collection', 'skyyrose'),
            'black_rose' => __('Black Rose Collection', 'skyyrose'),
            'love_hurts' => __('Love Hurts Collection', 'skyyrose'),
        ];
        ?>
        <div class="meta-item collection">
            <strong><?php _e('Collection:', 'skyyrose'); ?></strong>
            <a href="<?php echo esc_url(home_url('/collection/' . $collection)); ?>">
                <?php echo esc_html($collection_names[$collection] ?? $collection); ?>
            </a>
        </div>
        <?php
    }

    if ($materials) {
        ?>
        <div class="meta-item materials">
            <strong><?php _e('Materials:', 'skyyrose'); ?></strong>
            <p><?php echo esc_html($materials); ?></p>
        </div>
        <?php
    }

    if ($hours) {
        ?>
        <div class="meta-item craftsmanship">
            <strong><?php _e('Craftsmanship:', 'skyyrose'); ?></strong>
            <p><?php printf(__('%s hours of artisan work', 'skyyrose'), $hours); ?></p>
        </div>
        <?php
    }

    echo '</div>';
}
```

## Custom Product Types

### Pre-Order Product Type

```php
<?php
/**
 * Register custom pre-order product type
 */
add_filter('product_type_selector', 'skyyrose_add_preorder_product_type');

function skyyrose_add_preorder_product_type($types) {
    $types['preorder'] = __('Pre-Order', 'skyyrose');
    return $types;
}

class WC_Product_PreOrder extends WC_Product {

    public function __construct($product = 0) {
        $this->product_type = 'preorder';
        parent::__construct($product);
    }

    public function get_type() {
        return 'preorder';
    }

    public function is_purchasable() {
        return true;
    }

    public function is_sold_individually() {
        return true;
    }

    public function get_expected_ship_date() {
        return $this->get_meta('_expected_ship_date');
    }

    public function set_expected_ship_date($date) {
        $this->update_meta_data('_expected_ship_date', $date);
    }
}
```

## Checkout Customization

### Add Custom Checkout Field

```php
<?php
/**
 * Add gift message field to checkout
 */
add_action('woocommerce_after_order_notes', 'skyyrose_add_gift_message_field');

function skyyrose_add_gift_message_field($checkout) {
    echo '<div class="skyyrose-gift-options">';

    woocommerce_form_field('gift_message', [
        'type'        => 'textarea',
        'class'       => ['gift-message-field'],
        'label'       => __('Gift Message (Optional)', 'skyyrose'),
        'placeholder' => __('Your heartfelt message...', 'skyyrose'),
        'maxlength'   => 250,
        'rows'        => 4,
    ], $checkout->get_value('gift_message'));

    woocommerce_form_field('gift_wrap', [
        'type'    => 'checkbox',
        'class'   => ['gift-wrap-checkbox'],
        'label'   => __('Premium Gift Wrapping (+$25)', 'skyyrose'),
    ], $checkout->get_value('gift_wrap'));

    echo '</div>';
}

// Save custom fields
add_action('woocommerce_checkout_update_order_meta', 'skyyrose_save_gift_message');

function skyyrose_save_gift_message($order_id) {
    if (!empty($_POST['gift_message'])) {
        update_post_meta($order_id, '_gift_message', sanitize_textarea_field($_POST['gift_message']));
    }

    if (!empty($_POST['gift_wrap'])) {
        update_post_meta($order_id, '_gift_wrap', 'yes');

        // Add gift wrap fee
        $order = wc_get_order($order_id);
        $item = new WC_Order_Item_Fee();
        $item->set_name(__('Premium Gift Wrapping', 'skyyrose'));
        $item->set_amount(25);
        $item->set_total(25);
        $order->add_item($item);
        $order->calculate_totals();
    }
}

// Display in admin
add_action('woocommerce_admin_order_data_after_billing_address', 'skyyrose_display_gift_message_admin');

function skyyrose_display_gift_message_admin($order) {
    $gift_message = $order->get_meta('_gift_message');
    $gift_wrap = $order->get_meta('_gift_wrap');

    if ($gift_message || $gift_wrap) {
        echo '<div class="order-gift-options">';
        echo '<h3>' . __('Gift Options', 'skyyrose') . '</h3>';

        if ($gift_wrap) {
            echo '<p><strong>' . __('Gift Wrapping:', 'skyyrose') . '</strong> Yes</p>';
        }

        if ($gift_message) {
            echo '<p><strong>' . __('Gift Message:', 'skyyrose') . '</strong></p>';
            echo '<blockquote>' . wp_kses_post($gift_message) . '</blockquote>';
        }

        echo '</div>';
    }
}
```

## Cart Modifications

### Add Collection Badge to Cart Items

```php
<?php
/**
 * Add collection badge to cart items
 */
add_filter('woocommerce_cart_item_name', 'skyyrose_add_collection_badge_to_cart', 10, 3);

function skyyrose_add_collection_badge_to_cart($product_name, $cart_item, $cart_item_key) {
    $product = $cart_item['data'];
    $collection = $product->get_meta('_skyyrose_collection');

    if ($collection) {
        $collection_names = [
            'signature'  => 'Signature',
            'black_rose' => 'Black Rose',
            'love_hurts' => 'Love Hurts',
        ];

        $badge = sprintf(
            '<span class="collection-badge collection-%s">%s</span>',
            esc_attr($collection),
            esc_html($collection_names[$collection] ?? $collection)
        );

        $product_name = $badge . ' ' . $product_name;
    }

    return $product_name;
}
```

## WooCommerce Hooks Reference

### Product Hooks

```php
// Before product content
do_action('woocommerce_before_single_product');

// Product images
do_action('woocommerce_product_thumbnails');

// Product summary
do_action('woocommerce_single_product_summary');
// Priority order:
// 5: Title
// 10: Rating
// 20: Price
// 30: Excerpt
// 40: Add to cart
// 50: Meta

// After product content
do_action('woocommerce_after_single_product');
```

### Shop/Archive Hooks

```php
// Before shop loop
do_action('woocommerce_before_shop_loop');

// Product loop item
do_action('woocommerce_before_shop_loop_item');
do_action('woocommerce_before_shop_loop_item_title');  // Image
do_action('woocommerce_shop_loop_item_title');         // Title
do_action('woocommerce_after_shop_loop_item_title');   // Price, rating
do_action('woocommerce_after_shop_loop_item');

// After shop loop
do_action('woocommerce_after_shop_loop');
```

### Cart Hooks

```php
// Cart table
do_action('woocommerce_before_cart');
do_action('woocommerce_before_cart_table');
do_action('woocommerce_before_cart_contents');
do_action('woocommerce_cart_contents');
do_action('woocommerce_after_cart_contents');
do_action('woocommerce_after_cart_table');
do_action('woocommerce_cart_collaterals');
do_action('woocommerce_after_cart');
```

### Checkout Hooks

```php
// Checkout form
do_action('woocommerce_before_checkout_form', $checkout);
do_action('woocommerce_checkout_before_customer_details');
do_action('woocommerce_checkout_billing');
do_action('woocommerce_checkout_shipping');
do_action('woocommerce_checkout_after_customer_details');
do_action('woocommerce_checkout_before_order_review');
do_action('woocommerce_checkout_order_review');
do_action('woocommerce_checkout_after_order_review');
do_action('woocommerce_after_checkout_form', $checkout);
```

## WooCommerce REST API

### Create Product via API

```php
<?php
/**
 * Create product via WooCommerce REST API
 */
function skyyrose_create_product_via_api($product_data) {
    $consumer_key = get_option('woocommerce_consumer_key');
    $consumer_secret = get_option('woocommerce_consumer_secret');

    $auth = base64_encode("{$consumer_key}:{$consumer_secret}");

    $response = wp_remote_post(rest_url('/wc/v3/products'), [
        'headers' => [
            'Authorization' => "Basic {$auth}",
            'Content-Type'  => 'application/json',
        ],
        'body' => wp_json_encode([
            'name'              => $product_data['name'],
            'type'              => 'simple',
            'regular_price'     => $product_data['price'],
            'description'       => $product_data['description'],
            'short_description' => $product_data['short_description'],
            'categories'        => $product_data['category_ids'],
            'images'            => $product_data['images'],
            'meta_data'         => [
                [
                    'key'   => '_skyyrose_collection',
                    'value' => $product_data['collection'],
                ],
                [
                    'key'   => '_3d_model_url',
                    'value' => $product_data['model_url'],
                ],
            ],
        ]),
    ]);

    if (is_wp_error($response)) {
        return $response;
    }

    return json_decode(wp_remote_retrieve_body($response), true);
}
```

## SkyyRose-Specific Patterns

### Luxury Price Display

```php
<?php
/**
 * Custom price display with luxury formatting
 */
add_filter('woocommerce_get_price_html', 'skyyrose_custom_price_display', 10, 2);

function skyyrose_custom_price_display($price, $product) {
    if ($product->is_on_sale()) {
        return sprintf(
            '<div class="luxury-price sale">
                <span class="original-price">%s</span>
                <span class="sale-price">%s</span>
            </div>',
            wc_format_sale_price($product->get_regular_price(), $product->get_sale_price()),
            ''
        );
    }

    return sprintf(
        '<div class="luxury-price">
            <span class="price-amount">%s</span>
        </div>',
        $price
    );
}
```

## References

See `references/` for:
- `woocommerce-hooks-complete.md` - All WooCommerce hooks
- `rest-api-reference.md` - REST API endpoints
- `custom-product-types.md` - Creating custom product types
- `checkout-optimization.md` - Luxury checkout patterns

## Examples

See `examples/` for:
- `custom-product-fields.php` - Complete custom fields implementation
- `pre-order-product-type.php` - Pre-order product type
- `luxury-checkout.php` - Custom checkout with gift options
- `collection-filtering.php` - Collection-based product filtering
