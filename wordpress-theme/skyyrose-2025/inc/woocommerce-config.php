<?php
/**
 * WooCommerce Configuration
 * Custom WooCommerce layouts and functionality
 *
 * @package SkyyRose_2025
 * @version 2.0.0
 */

if (!defined('ABSPATH')) exit;

// Declare WooCommerce support
function skyyrose_add_woocommerce_support() {
    add_theme_support('woocommerce');
    add_theme_support('wc-product-gallery-zoom');
    add_theme_support('wc-product-gallery-lightbox');
    add_theme_support('wc-product-gallery-slider');
}
add_action('after_setup_theme', 'skyyrose_add_woocommerce_support');

/**
 * Custom product loop columns
 */
function skyyrose_loop_columns() {
    return 3; // 3 products per row
}
add_filter('loop_shop_columns', 'skyyrose_loop_columns');

/**
 * Products per page
 */
function skyyrose_products_per_page() {
    return 12;
}
add_filter('loop_shop_per_page', 'skyyrose_products_per_page');

/**
 * Customize Add to Cart button text
 */
function skyyrose_custom_cart_button_text() {
    return __('Add to Collection', 'skyyrose');
}
add_filter('woocommerce_product_single_add_to_cart_text', 'skyyrose_custom_cart_button_text');
add_filter('woocommerce_product_add_to_cart_text', 'skyyrose_custom_cart_button_text');

/**
 * Remove default WooCommerce breadcrumbs
 */
remove_action('woocommerce_before_main_content', 'woocommerce_breadcrumb', 20);

/**
 * Custom product meta display
 */
function skyyrose_custom_product_meta() {
    global $product;

    $collection = get_post_meta($product->get_id(), '_skyyrose_collection', true);

    if ($collection) {
        $collection_names = [
            'black_rose' => 'Black Rose Collection',
            'love_hurts' => 'Love Hurts Collection',
            'signature' => 'Signature Collection',
        ];

        $collection_name = $collection_names[$collection] ?? $collection;

        echo '<div class="skyyrose-collection-badge">';
        echo '<span class="collection-label">' . esc_html($collection_name) . '</span>';
        echo '</div>';
    }
}
add_action('woocommerce_single_product_summary', 'skyyrose_custom_product_meta', 6);

/**
 * Add size guide link to single product page
 */
function skyyrose_add_size_guide() {
    global $product;

    if ($product->is_type('variable')) {
        echo '<div class="skyyrose-size-guide">';
        echo '<a href="#size-guide-modal" class="size-guide-link">';
        echo '<svg class="icon" width="16" height="16"><use href="#icon-ruler"></use></svg>';
        echo esc_html__('Size Guide', 'skyyrose');
        echo '</a>';
        echo '</div>';
    }
}
add_action('woocommerce_single_product_summary', 'skyyrose_add_size_guide', 25);

/**
 * Custom related products
 */
function skyyrose_related_products_args($args) {
    $args['posts_per_page'] = 4;
    $args['columns'] = 4;
    return $args;
}
add_filter('woocommerce_output_related_products_args', 'skyyrose_related_products_args');

/**
 * Customize WooCommerce pagination
 */
function skyyrose_pagination_args($args) {
    $args['prev_text'] = '← Previous';
    $args['next_text'] = 'Next →';
    return $args;
}
add_filter('woocommerce_pagination_args', 'skyyrose_pagination_args');

/**
 * Enqueue collection split-view script
 */
function skyyrose_enqueue_split_view_script() {
    // Only load on collection pages (pages using template-collection.php)
    if (is_page_template('template-collection.php')) {
        wp_enqueue_script(
            'skyyrose-split-view',
            get_template_directory_uri() . '/assets/js/collection-split-view.js',
            [],
            SKYYROSE_VERSION,
            true
        );
    }
}
add_action('wp_enqueue_scripts', 'skyyrose_enqueue_split_view_script');

/**
 * Enqueue vault interactive selector script
 */
function skyyrose_enqueue_vault_selector() {
    // Only load on vault pages (pages using template-vault.php)
    if (is_page_template('template-vault.php')) {
        wp_enqueue_script(
            'skyyrose-vault-selector',
            get_template_directory_uri() . '/assets/js/vault-interactive-selector.js',
            [],
            SKYYROSE_VERSION,
            true
        );
    }
}
add_action('wp_enqueue_scripts', 'skyyrose_enqueue_vault_selector');

/**
 * Handle vault pre-order AJAX submission
 */
function skyyrose_handle_vault_preorder() {
    // Verify nonce if implementing nonce validation
    // check_ajax_referer('skyyrose_vault_nonce', 'nonce');

    $email = sanitize_email($_POST['email'] ?? '');
    $collections = json_decode(stripslashes($_POST['collections'] ?? '[]'), true);
    $products = json_decode(stripslashes($_POST['products'] ?? '[]'), true);

    if (empty($email) || !is_email($email)) {
        wp_send_json_error(['message' => 'Invalid email address']);
        return;
    }

    // Save to database or send to email service (Mailchimp/Klaviyo)
    // For now, just return success
    $data = [
        'email' => $email,
        'collections' => $collections,
        'products' => $products,
        'timestamp' => current_time('mysql')
    ];

    // TODO: Integrate with Mailchimp/Klaviyo API
    // TODO: Store in WordPress database as custom post type

    wp_send_json_success(['message' => 'Pre-order saved successfully', 'data' => $data]);
}
add_action('wp_ajax_skyyrose_vault_preorder', 'skyyrose_handle_vault_preorder');
add_action('wp_ajax_nopriv_skyyrose_vault_preorder', 'skyyrose_handle_vault_preorder');
