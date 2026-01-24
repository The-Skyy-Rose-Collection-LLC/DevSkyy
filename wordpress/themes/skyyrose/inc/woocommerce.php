<?php
/**
 * WooCommerce Integration
 *
 * @package SkyyRose
 */

defined('ABSPATH') || exit;

/**
 * Remove WooCommerce breadcrumbs (we use custom)
 */
remove_action('woocommerce_before_main_content', 'woocommerce_breadcrumb', 20);

/**
 * Remove default product tabs
 */
add_filter('woocommerce_product_tabs', function($tabs) {
    // Remove default tabs - we'll use custom layout
    unset($tabs['description']);
    unset($tabs['additional_information']);
    unset($tabs['reviews']);
    return $tabs;
});

/**
 * Change add to cart button text
 */
add_filter('woocommerce_product_single_add_to_cart_text', function($text) {
    global $product;

    $preorder_enabled = get_post_meta($product->get_id(), '_preorder_enabled', true);

    if ($preorder_enabled === 'yes') {
        $status = get_post_meta($product->get_id(), '_preorder_status', true);
        return $status === 'blooming_soon' ? 'Join Waitlist' : 'Pre-Order Now';
    }

    return 'Add to Bag';
});

/**
 * Custom product gallery wrapper
 */
remove_action('woocommerce_before_single_product_summary', 'woocommerce_show_product_images', 20);
add_action('woocommerce_before_single_product_summary', 'skyyrose_product_gallery', 20);

function skyyrose_product_gallery(): void {
    global $product;

    $gallery_ids = $product->get_gallery_image_ids();
    $main_image = $product->get_image_id();
    $has_3d = get_post_meta($product->get_id(), '_skyyrose_3d_model', true);
    ?>
    <div class="skyyrose-product-gallery" data-product-id="<?php echo esc_attr($product->get_id()); ?>">
        <?php if ($has_3d) : ?>
            <div class="gallery-3d-viewer">
                <model-viewer
                    src="<?php echo esc_url($has_3d); ?>"
                    alt="<?php echo esc_attr($product->get_name()); ?> 3D Model"
                    ar
                    ar-modes="webxr scene-viewer quick-look"
                    camera-controls
                    touch-action="pan-y"
                    auto-rotate
                    shadow-intensity="1"
                    exposure="0.8"
                    class="skyyrose-model-viewer"
                >
                    <button slot="ar-button" class="ar-button glass-button">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                            <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="1.5"/>
                            <path d="M12 18V6M6 12H18" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                        </svg>
                        View in AR
                    </button>
                </model-viewer>
            </div>
        <?php endif; ?>

        <div class="gallery-main">
            <?php if ($main_image) : ?>
                <div class="gallery-main-image">
                    <?php echo wp_get_attachment_image($main_image, 'skyyrose-product', false, [
                        'class' => 'main-product-image',
                        'data-zoom' => wp_get_attachment_image_url($main_image, 'full'),
                    ]); ?>
                </div>
            <?php endif; ?>
        </div>

        <?php if (!empty($gallery_ids)) : ?>
            <div class="gallery-thumbnails">
                <?php if ($main_image) : ?>
                    <button class="gallery-thumb active" data-image-id="<?php echo esc_attr($main_image); ?>">
                        <?php echo wp_get_attachment_image($main_image, 'skyyrose-product-thumb'); ?>
                    </button>
                <?php endif; ?>

                <?php foreach ($gallery_ids as $gallery_id) : ?>
                    <button class="gallery-thumb" data-image-id="<?php echo esc_attr($gallery_id); ?>">
                        <?php echo wp_get_attachment_image($gallery_id, 'skyyrose-product-thumb'); ?>
                    </button>
                <?php endforeach; ?>

                <?php if ($has_3d) : ?>
                    <button class="gallery-thumb gallery-thumb-3d" data-view="3d">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        <span>3D</span>
                    </button>
                <?php endif; ?>
            </div>
        <?php endif; ?>
    </div>
    <?php
}

/**
 * Add custom product meta (collection badge)
 */
add_action('woocommerce_before_shop_loop_item_title', function() {
    global $product;

    $collection = get_post_meta($product->get_id(), '_skyyrose_collection', true);

    if ($collection) {
        $collection_data = skyyrose_get_collection($collection);
        echo '<span class="collection-badge" style="--badge-color: ' . esc_attr($collection_data['colors']['primary']) . '">';
        echo esc_html($collection_data['name']);
        echo '</span>';
    }
}, 5);

/**
 * Customize loop product title
 */
remove_action('woocommerce_shop_loop_item_title', 'woocommerce_template_loop_product_title', 10);
add_action('woocommerce_shop_loop_item_title', function() {
    echo '<h3 class="woocommerce-loop-product__title">' . get_the_title() . '</h3>';
}, 10);

/**
 * Add quick view button to product cards
 */
add_action('woocommerce_after_shop_loop_item', function() {
    global $product;
    ?>
    <button class="quick-view-btn magnetic-btn" data-product-id="<?php echo esc_attr($product->get_id()); ?>">
        <span>Quick View</span>
    </button>
    <?php
}, 15);

/**
 * AJAX Quick View Handler
 */
add_action('wp_ajax_skyyrose_quick_view', 'skyyrose_quick_view');
add_action('wp_ajax_nopriv_skyyrose_quick_view', 'skyyrose_quick_view');

function skyyrose_quick_view(): void {
    check_ajax_referer('skyyrose_nonce', 'nonce');

    $product_id = isset($_POST['product_id']) ? absint($_POST['product_id']) : 0;

    if (!$product_id) {
        wp_send_json_error(['message' => 'Invalid product ID']);
    }

    $product = wc_get_product($product_id);

    if (!$product) {
        wp_send_json_error(['message' => 'Product not found']);
    }

    $gallery_ids = $product->get_gallery_image_ids();
    $images = [];

    if ($product->get_image_id()) {
        $images[] = wp_get_attachment_image_url($product->get_image_id(), 'skyyrose-product');
    }

    foreach ($gallery_ids as $id) {
        $images[] = wp_get_attachment_image_url($id, 'skyyrose-product');
    }

    wp_send_json_success([
        'id'          => $product_id,
        'name'        => $product->get_name(),
        'price'       => $product->get_price_html(),
        'description' => wp_trim_words($product->get_short_description(), 30),
        'images'      => $images,
        'link'        => $product->get_permalink(),
        'add_to_cart' => $product->is_purchasable() && $product->is_in_stock(),
        '3d_model'    => get_post_meta($product_id, '_skyyrose_3d_model', true),
        'collection'  => get_post_meta($product_id, '_skyyrose_collection', true),
    ]);
}

/**
 * Add collection filter to admin product list
 */
add_action('restrict_manage_posts', function($post_type) {
    if ($post_type !== 'product') return;

    $current = $_GET['skyyrose_collection'] ?? '';
    $collections = ['signature', 'black-rose', 'love-hurts'];
    ?>
    <select name="skyyrose_collection">
        <option value=""><?php esc_html_e('All Collections', 'skyyrose'); ?></option>
        <?php foreach ($collections as $collection) : ?>
            <option value="<?php echo esc_attr($collection); ?>" <?php selected($current, $collection); ?>>
                <?php echo esc_html(ucwords(str_replace('-', ' ', $collection))); ?>
            </option>
        <?php endforeach; ?>
    </select>
    <?php
});

add_filter('parse_query', function($query) {
    global $pagenow, $typenow;

    if ($pagenow === 'edit.php' && $typenow === 'product' && !empty($_GET['skyyrose_collection'])) {
        $query->query_vars['meta_query'][] = [
            'key'   => '_skyyrose_collection',
            'value' => sanitize_text_field($_GET['skyyrose_collection']),
        ];
    }
});

/**
 * Add SkyyRose meta box to product editor
 */
add_action('add_meta_boxes', function() {
    add_meta_box(
        'skyyrose_product_meta',
        __('SkyyRose Settings', 'skyyrose'),
        'skyyrose_product_meta_box',
        'product',
        'side',
        'high'
    );
});

function skyyrose_product_meta_box($post): void {
    wp_nonce_field('skyyrose_product_meta', 'skyyrose_product_meta_nonce');

    $collection = get_post_meta($post->ID, '_skyyrose_collection', true);
    $model_3d = get_post_meta($post->ID, '_skyyrose_3d_model', true);
    $preorder_enabled = get_post_meta($post->ID, '_preorder_enabled', true);
    $preorder_status = get_post_meta($post->ID, '_preorder_status', true);
    $launch_date = get_post_meta($post->ID, '_preorder_launch_date', true);
    ?>
    <p>
        <label for="skyyrose_collection"><strong><?php esc_html_e('Collection', 'skyyrose'); ?></strong></label>
        <select name="skyyrose_collection" id="skyyrose_collection" class="widefat">
            <option value=""><?php esc_html_e('Select Collection', 'skyyrose'); ?></option>
            <option value="signature" <?php selected($collection, 'signature'); ?>>Signature</option>
            <option value="black-rose" <?php selected($collection, 'black-rose'); ?>>Black Rose</option>
            <option value="love-hurts" <?php selected($collection, 'love-hurts'); ?>>Love Hurts</option>
        </select>
    </p>

    <p>
        <label for="skyyrose_3d_model"><strong><?php esc_html_e('3D Model URL (GLB)', 'skyyrose'); ?></strong></label>
        <input type="url" name="skyyrose_3d_model" id="skyyrose_3d_model" value="<?php echo esc_url($model_3d); ?>" class="widefat">
    </p>

    <hr>

    <p>
        <label>
            <input type="checkbox" name="skyyrose_preorder_enabled" value="yes" <?php checked($preorder_enabled, 'yes'); ?>>
            <strong><?php esc_html_e('Enable Pre-Order', 'skyyrose'); ?></strong>
        </label>
    </p>

    <p>
        <label for="skyyrose_preorder_status"><strong><?php esc_html_e('Pre-Order Status', 'skyyrose'); ?></strong></label>
        <select name="skyyrose_preorder_status" id="skyyrose_preorder_status" class="widefat">
            <option value="blooming_soon" <?php selected($preorder_status, 'blooming_soon'); ?>>Blooming Soon</option>
            <option value="now_blooming" <?php selected($preorder_status, 'now_blooming'); ?>>Now Blooming</option>
            <option value="available" <?php selected($preorder_status, 'available'); ?>>Available</option>
        </select>
    </p>

    <p>
        <label for="skyyrose_launch_date"><strong><?php esc_html_e('Launch Date', 'skyyrose'); ?></strong></label>
        <input type="datetime-local" name="skyyrose_launch_date" id="skyyrose_launch_date" value="<?php echo esc_attr($launch_date ? date('Y-m-d\TH:i', strtotime($launch_date)) : ''); ?>" class="widefat">
    </p>
    <?php
}

add_action('save_post_product', function($post_id) {
    if (!isset($_POST['skyyrose_product_meta_nonce']) || !wp_verify_nonce($_POST['skyyrose_product_meta_nonce'], 'skyyrose_product_meta')) {
        return;
    }

    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) {
        return;
    }

    if (!current_user_can('edit_post', $post_id)) {
        return;
    }

    $fields = [
        'skyyrose_collection'      => '_skyyrose_collection',
        'skyyrose_3d_model'        => '_skyyrose_3d_model',
        'skyyrose_preorder_status' => '_preorder_status',
        'skyyrose_launch_date'     => '_preorder_launch_date',
    ];

    foreach ($fields as $input => $meta_key) {
        if (isset($_POST[$input])) {
            $value = sanitize_text_field($_POST[$input]);
            update_post_meta($post_id, $meta_key, $value);
        }
    }

    // Handle checkbox
    $preorder_enabled = isset($_POST['skyyrose_preorder_enabled']) ? 'yes' : 'no';
    update_post_meta($post_id, '_preorder_enabled', $preorder_enabled);
});

/**
 * Customize checkout fields
 */
add_filter('woocommerce_checkout_fields', function($fields) {
    // Add custom classes for styling
    foreach ($fields as $fieldset_key => $fieldset) {
        foreach ($fieldset as $field_key => $field) {
            $fields[$fieldset_key][$field_key]['class'][] = 'skyyrose-field';
            $fields[$fieldset_key][$field_key]['input_class'][] = 'glass-input';
        }
    }

    return $fields;
});

/**
 * Add free shipping notice
 */
add_action('woocommerce_before_cart', function() {
    $threshold = 150; // Free shipping threshold
    $cart_total = WC()->cart->get_cart_contents_total();
    $remaining = $threshold - $cart_total;

    if ($remaining > 0) {
        echo '<div class="free-shipping-notice glass-card">';
        echo '<p>Add <strong>' . wc_price($remaining) . '</strong> more to qualify for <strong>FREE SHIPPING</strong></p>';
        echo '</div>';
    } else {
        echo '<div class="free-shipping-notice free-shipping-qualified glass-card">';
        echo '<p>You\'ve qualified for <strong>FREE SHIPPING</strong>!</p>';
        echo '</div>';
    }
});
