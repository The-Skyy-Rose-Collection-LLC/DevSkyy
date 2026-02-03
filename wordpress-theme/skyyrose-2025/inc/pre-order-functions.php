<?php
/**
 * Pre-Order Functions for Vault
 *
 * Handles multi-collection product queries, stock aggregation,
 * live viewer tracking, and email automation for the Vault pre-order page.
 *
 * @package SkyyRose_2025
 * @version 1.0.0
 */

if (!defined('ABSPATH')) {
    exit;
}

/**
 * Get products from multiple collections for Vault
 *
 * @param array $collections Collection slugs to query
 * @param int $limit Number of products to return (-1 for all)
 * @return WP_Query
 */
function skyyrose_get_vault_products($collections = ['black-rose', 'love-hurts', 'signature'], $limit = -1) {
    $args = [
        'post_type' => 'product',
        'posts_per_page' => $limit,
        'meta_query' => [
            'relation' => 'AND',
            [
                'key' => '_vault_preorder',
                'value' => '1',
                'compare' => '='
            ],
            [
                'key' => '_skyyrose_collection',
                'value' => $collections,
                'compare' => 'IN'
            ]
        ],
        'orderby' => 'menu_order',
        'order' => 'ASC',
        'post_status' => 'publish'
    ];

    return new WP_Query($args);
}

/**
 * Get aggregated stock across all Vault collections
 *
 * @return array {
 *     @type int $total Total stock available
 *     @type int $sold Total items sold
 *     @type int $remaining Remaining stock
 *     @type float $percent_sold Percentage sold
 *     @type array $by_collection Stock breakdown by collection
 * }
 */
function skyyrose_get_total_vault_stock() {
    // Check cache first
    $cache_key = 'skyyrose_vault_stock';
    $cached = get_transient($cache_key);
    if (false !== $cached) {
        return $cached;
    }

    $collections = ['black-rose', 'love-hurts', 'signature'];
    $stock_data = [
        'total' => 0,
        'sold' => 0,
        'remaining' => 0,
        'percent_sold' => 0,
        'by_collection' => []
    ];

    foreach ($collections as $collection) {
        $products = skyyrose_get_vault_products([$collection]);

        $collection_total = 0;
        $collection_sold = 0;

        if ($products->have_posts()) {
            while ($products->have_posts()) {
                $products->the_post();
                $product = wc_get_product(get_the_ID());

                if ($product) {
                    $stock = $product->get_stock_quantity();
                    $total_sales = (int) get_post_meta(get_the_ID(), 'total_sales', true);

                    $collection_total += ($stock ?: 0) + $total_sales;
                    $collection_sold += $total_sales;
                }
            }
            wp_reset_postdata();
        }

        $stock_data['by_collection'][$collection] = [
            'total' => $collection_total,
            'sold' => $collection_sold,
            'remaining' => $collection_total - $collection_sold
        ];

        $stock_data['total'] += $collection_total;
        $stock_data['sold'] += $collection_sold;
    }

    $stock_data['remaining'] = $stock_data['total'] - $stock_data['sold'];
    $stock_data['percent_sold'] = $stock_data['total'] > 0
        ? round(($stock_data['sold'] / $stock_data['total']) * 100, 2)
        : 0;

    // Cache for 5 minutes
    set_transient($cache_key, $stock_data, 5 * MINUTE_IN_SECONDS);

    return $stock_data;
}

/**
 * Update live viewer count for Vault page
 *
 * @param string $session_id Unique session identifier
 * @return int Current viewer count
 */
function skyyrose_update_viewer_count($session_id) {
    $viewers_key = 'skyyrose_vault_viewers';
    $viewers = get_transient($viewers_key) ?: [];

    // Add current viewer with timestamp
    $viewers[$session_id] = time();

    // Remove stale viewers (>5 minutes)
    $cutoff = time() - (5 * MINUTE_IN_SECONDS);
    $viewers = array_filter($viewers, function($timestamp) use ($cutoff) {
        return $timestamp > $cutoff;
    });

    // Save updated viewer list
    set_transient($viewers_key, $viewers, 10 * MINUTE_IN_SECONDS);

    return count($viewers);
}

/**
 * Get current viewer count
 *
 * @return int Number of active viewers
 */
function skyyrose_get_viewer_count() {
    $viewers_key = 'skyyrose_vault_viewers';
    $viewers = get_transient($viewers_key) ?: [];

    // Clean stale entries
    $cutoff = time() - (5 * MINUTE_IN_SECONDS);
    $viewers = array_filter($viewers, function($timestamp) use ($cutoff) {
        return $timestamp > $cutoff;
    });

    return count($viewers);
}

/**
 * Send pre-order confirmation email
 *
 * @param int $order_id WooCommerce order ID
 * @return bool Success status
 */
function skyyrose_send_preorder_confirmation($order_id) {
    $order = wc_get_order($order_id);
    if (!$order) {
        return false;
    }

    $email = $order->get_billing_email();
    $name = $order->get_billing_first_name();

    // Get Vault items from order
    $vault_items = [];
    foreach ($order->get_items() as $item) {
        $product_id = $item->get_product_id();
        if (get_post_meta($product_id, '_vault_preorder', true) === '1') {
            $collection = get_post_meta($product_id, '_skyyrose_collection', true);
            $vault_items[] = [
                'name' => $item->get_name(),
                'collection' => $collection,
                'quantity' => $item->get_quantity()
            ];
        }
    }

    if (empty($vault_items)) {
        return false;
    }

    $subject = 'Your SkyyRose Vault Pre-Order Confirmation';

    ob_start();
    ?>
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body { font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #B76E79 0%, #8B5A62 100%); color: white; padding: 40px 20px; text-align: center; }
            .content { background: #f9f9f9; padding: 30px 20px; }
            .item { background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #B76E79; }
            .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
            .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; margin-top: 5px; }
            .black-rose { background: #8B0000; color: white; }
            .love-hurts { background: #E91E63; color: white; }
            .signature { background: #D4AF37; color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>THE VAULT</h1>
                <p>Pre-Order Confirmation</p>
            </div>
            <div class="content">
                <p>Dear <?php echo esc_html($name); ?>,</p>
                <p>Thank you for your exclusive pre-order from The Vault! You now have early access to all SkyyRose collections.</p>

                <h3>Your Pre-Order Items:</h3>
                <?php foreach ($vault_items as $item): ?>
                    <div class="item">
                        <strong><?php echo esc_html($item['name']); ?></strong>
                        <span class="badge <?php echo esc_attr($item['collection']); ?>">
                            <?php echo esc_html(strtoupper(str_replace('-', ' ', $item['collection']))); ?>
                        </span>
                        <p>Quantity: <?php echo esc_html($item['quantity']); ?></p>
                    </div>
                <?php endforeach; ?>

                <p><strong>Order #<?php echo esc_html($order->get_order_number()); ?></strong></p>
                <p>Total: <?php echo wp_kses_post($order->get_formatted_order_total()); ?></p>

                <p style="margin-top: 30px;">Your exclusive early access code will be sent when collections launch. Stay tuned!</p>

                <p style="color: #B76E79; font-style: italic;">Where Love Meets Luxury</p>
            </div>
            <div class="footer">
                <p>&copy; <?php echo date('Y'); ?> SkyyRose LLC. All rights reserved.</p>
                <p>Oakland, CA</p>
            </div>
        </div>
    </body>
    </html>
    <?php
    $message = ob_get_clean();

    $headers = ['Content-Type: text/html; charset=UTF-8'];

    return wp_mail($email, $subject, $message, $headers);
}

/**
 * Send launch notification to Vault members
 *
 * @param array $subscriber_ids Array of user IDs
 * @return array {
 *     @type int $sent Number of emails sent
 *     @type int $failed Number of emails failed
 * }
 */
function skyyrose_send_launch_notification($subscriber_ids) {
    $results = ['sent' => 0, 'failed' => 0];

    foreach ($subscriber_ids as $user_id) {
        $user = get_userdata($user_id);
        if (!$user) {
            $results['failed']++;
            continue;
        }

        $email = $user->user_email;
        $name = $user->first_name ?: $user->display_name;
        $access_code = get_user_meta($user_id, '_skyyrose_early_access_code', true);

        $subject = 'The Vault is Now Open - Your Early Access Code';

        ob_start();
        ?>
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #B76E79 0%, #8B5A62 100%); color: white; padding: 40px 20px; text-align: center; }
                .content { background: #f9f9f9; padding: 30px 20px; }
                .code-box { background: white; border: 2px solid #B76E79; padding: 20px; text-align: center; margin: 20px 0; }
                .code { font-size: 24px; font-weight: bold; color: #B76E79; letter-spacing: 2px; }
                .cta { display: inline-block; background: #B76E79; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
                .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>THE VAULT IS OPEN</h1>
                    <p>Your Exclusive Access Awaits</p>
                </div>
                <div class="content">
                    <p>Dear <?php echo esc_html($name); ?>,</p>
                    <p>The wait is over! All SkyyRose collections are now live and ready for you.</p>

                    <?php if ($access_code): ?>
                        <div class="code-box">
                            <p>Your Early Access Code:</p>
                            <div class="code"><?php echo esc_html($access_code); ?></div>
                            <p style="font-size: 12px; color: #666;">Use at checkout for 10% off</p>
                        </div>
                    <?php endif; ?>

                    <p>As a Vault member, you have exclusive early access to:</p>
                    <ul>
                        <li><strong>BLACK ROSE</strong> - Gothic elegance collection</li>
                        <li><strong>LOVE HURTS</strong> - Romantic castle collection</li>
                        <li><strong>SIGNATURE</strong> - Oakland pride collection</li>
                    </ul>

                    <div style="text-align: center;">
                        <a href="<?php echo esc_url(home_url('/vault')); ?>" class="cta">
                            Shop The Vault Now
                        </a>
                    </div>

                    <p style="color: #B76E79; font-style: italic; text-align: center; margin-top: 30px;">Where Love Meets Luxury</p>
                </div>
                <div class="footer">
                    <p>&copy; <?php echo date('Y'); ?> SkyyRose LLC. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        <?php
        $message = ob_get_clean();

        $headers = ['Content-Type: text/html; charset=UTF-8'];

        if (wp_mail($email, $subject, $message, $headers)) {
            $results['sent']++;
        } else {
            $results['failed']++;
        }
    }

    return $results;
}

/**
 * Generate early access code for Vault member
 *
 * @param int $user_id User ID
 * @return string Generated access code
 */
function skyyrose_generate_early_access_code($user_id) {
    // Check if code already exists
    $existing_code = get_user_meta($user_id, '_skyyrose_early_access_code', true);
    if ($existing_code) {
        return $existing_code;
    }

    // Generate unique code
    $code = 'VAULT-' . strtoupper(wp_generate_password(8, false));
    update_user_meta($user_id, '_skyyrose_early_access_code', $code);

    // Create WooCommerce coupon
    $coupon = new WC_Coupon();
    $coupon->set_code($code);
    $coupon->set_discount_type('percent');
    $coupon->set_amount(10); // 10% discount
    $coupon->set_individual_use(true);
    $coupon->set_usage_limit(1);
    $coupon->set_usage_limit_per_user(1);

    // Set email restriction
    $user = get_userdata($user_id);
    if ($user) {
        $coupon->set_email_restrictions([$user->user_email]);
    }

    $coupon->set_description('Vault Early Access - 10% off');
    $coupon->save();

    return $code;
}

/**
 * AJAX: Get live viewer count
 */
function skyyrose_ajax_get_viewer_count() {
    $count = skyyrose_get_viewer_count();
    wp_send_json_success(['count' => $count]);
}
add_action('wp_ajax_skyyrose_get_viewer_count', 'skyyrose_ajax_get_viewer_count');
add_action('wp_ajax_nopriv_skyyrose_get_viewer_count', 'skyyrose_ajax_get_viewer_count');

/**
 * AJAX: Register viewer
 */
function skyyrose_ajax_register_viewer() {
    $session_id = sanitize_text_field($_POST['session_id'] ?? '');

    if (empty($session_id)) {
        wp_send_json_error(['message' => 'Invalid session ID']);
        return;
    }

    $count = skyyrose_update_viewer_count($session_id);
    wp_send_json_success(['count' => $count]);
}
add_action('wp_ajax_skyyrose_register_viewer', 'skyyrose_ajax_register_viewer');
add_action('wp_ajax_nopriv_skyyrose_register_viewer', 'skyyrose_ajax_register_viewer');

/**
 * AJAX: Submit pre-order
 */
function skyyrose_ajax_submit_preorder() {
    // Verify nonce
    check_ajax_referer('skyyrose_vault', 'nonce');

    // Sanitize inputs
    $product_id = absint($_POST['product_id'] ?? 0);
    $variation_id = absint($_POST['variation_id'] ?? 0);
    $quantity = absint($_POST['quantity'] ?? 1);

    // Validate product
    if (!$product_id) {
        wp_send_json_error(['message' => 'Product ID is required']);
        return;
    }

    // Verify it's a vault item
    if (get_post_meta($product_id, '_vault_preorder', true) !== '1') {
        wp_send_json_error(['message' => 'This product is not available for pre-order']);
        return;
    }

    // Add to cart
    $cart_item_key = WC()->cart->add_to_cart(
        $product_id,
        $quantity,
        $variation_id
    );

    if ($cart_item_key) {
        wp_send_json_success([
            'message' => 'Product added to cart',
            'cart_count' => WC()->cart->get_cart_contents_count(),
            'cart_url' => wc_get_cart_url()
        ]);
    } else {
        wp_send_json_error(['message' => 'Failed to add product to cart']);
    }
}
add_action('wp_ajax_skyyrose_submit_preorder', 'skyyrose_ajax_submit_preorder');
add_action('wp_ajax_nopriv_skyyrose_submit_preorder', 'skyyrose_ajax_submit_preorder');

/**
 * Hook: Send pre-order confirmation on new order
 */
add_action('woocommerce_new_order', function($order_id) {
    $order = wc_get_order($order_id);
    if (!$order) {
        return;
    }

    $has_vault_item = false;

    foreach ($order->get_items() as $item) {
        if (get_post_meta($item->get_product_id(), '_vault_preorder', true) === '1') {
            $has_vault_item = true;
            break;
        }
    }

    if ($has_vault_item) {
        skyyrose_send_preorder_confirmation($order_id);

        // Generate early access code for customer
        $user_id = $order->get_customer_id();
        if ($user_id) {
            skyyrose_generate_early_access_code($user_id);
        }
    }
});

/**
 * Hook: Send launch notification (trigger manually or via cron)
 */
add_action('skyyrose_collection_launch', 'skyyrose_send_launch_notification');

/**
 * Cleanup transients on product stock change
 */
add_action('woocommerce_product_set_stock', function($product) {
    delete_transient('skyyrose_vault_stock');
});

add_action('woocommerce_variation_set_stock', function($variation) {
    delete_transient('skyyrose_vault_stock');
});
