<?php
/**
 * SkyyRose Theme Functions
 *
 * @package SkyyRose
 * @version 2.0.0
 */

defined('ABSPATH') || exit;

// Theme constants
define('SKYYROSE_VERSION', '2.0.0');
define('SKYYROSE_DIR', get_template_directory());
define('SKYYROSE_URI', get_template_directory_uri());

/**
 * Theme Setup
 */
function skyyrose_setup(): void {
    // Add theme support
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('html5', [
        'search-form',
        'comment-form',
        'comment-list',
        'gallery',
        'caption',
        'style',
        'script',
    ]);
    add_theme_support('custom-logo', [
        'height'      => 100,
        'width'       => 300,
        'flex-height' => true,
        'flex-width'  => true,
    ]);
    add_theme_support('automatic-feed-links');
    add_theme_support('responsive-embeds');
    add_theme_support('align-wide');

    // WooCommerce support
    add_theme_support('woocommerce');
    add_theme_support('wc-product-gallery-zoom');
    add_theme_support('wc-product-gallery-lightbox');
    add_theme_support('wc-product-gallery-slider');

    // Register navigation menus
    register_nav_menus([
        'primary'        => __('Primary Menu', 'skyyrose'),
        'footer'         => __('Footer Menu', 'skyyrose'),
        'footer-shop'    => __('Footer Shop', 'skyyrose'),
        'footer-company' => __('Footer Company', 'skyyrose'),
        'footer-support' => __('Footer Support', 'skyyrose'),
        'footer-legal'   => __('Footer Legal', 'skyyrose'),
        'mobile'         => __('Mobile Menu', 'skyyrose'),
    ]);

    // Image sizes
    add_image_size('skyyrose-hero', 1920, 1080, true);
    add_image_size('skyyrose-collection', 800, 1000, true);
    add_image_size('skyyrose-product', 600, 750, true);
    add_image_size('skyyrose-product-thumb', 300, 375, true);
    add_image_size('skyyrose-blog', 800, 500, true);
}
add_action('after_setup_theme', 'skyyrose_setup');

/**
 * Enqueue Scripts and Styles
 */
function skyyrose_enqueue_assets(): void {
    // Google Fonts
    wp_enqueue_style(
        'skyyrose-fonts',
        'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;500;600;700&display=swap',
        [],
        null
    );

    // Theme styles
    wp_enqueue_style(
        'skyyrose-main',
        SKYYROSE_URI . '/assets/css/main.css',
        [],
        SKYYROSE_VERSION
    );

    wp_enqueue_style(
        'skyyrose-glassmorphism',
        SKYYROSE_URI . '/assets/css/glassmorphism.css',
        ['skyyrose-main'],
        SKYYROSE_VERSION
    );

    wp_enqueue_style(
        'skyyrose-animations',
        SKYYROSE_URI . '/assets/css/animations.css',
        ['skyyrose-main'],
        SKYYROSE_VERSION
    );

    wp_enqueue_style(
        'skyyrose-footer',
        SKYYROSE_URI . '/assets/css/footer.css',
        ['skyyrose-main', 'skyyrose-glassmorphism'],
        SKYYROSE_VERSION
    );

    // WooCommerce styles (only on WC pages)
    if (class_exists('WooCommerce')) {
        wp_enqueue_style(
            'skyyrose-woocommerce',
            SKYYROSE_URI . '/assets/css/woocommerce.css',
            ['skyyrose-main'],
            SKYYROSE_VERSION
        );
    }

    // GSAP (from CDN for performance)
    wp_enqueue_script(
        'gsap',
        'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js',
        [],
        '3.12.5',
        true
    );

    wp_enqueue_script(
        'gsap-scrolltrigger',
        'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js',
        ['gsap'],
        '3.12.5',
        true
    );

    wp_enqueue_script(
        'gsap-scrollto',
        'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollToPlugin.min.js',
        ['gsap'],
        '3.12.5',
        true
    );

    // Theme scripts
    wp_enqueue_script(
        'skyyrose-gsap-init',
        SKYYROSE_URI . '/assets/js/gsap-init.js',
        ['gsap', 'gsap-scrolltrigger'],
        SKYYROSE_VERSION,
        true
    );

    wp_enqueue_script(
        'skyyrose-mega-menu',
        SKYYROSE_URI . '/assets/js/mega-menu.js',
        [],
        SKYYROSE_VERSION,
        true
    );

    wp_enqueue_script(
        'skyyrose-custom-cursor',
        SKYYROSE_URI . '/assets/js/custom-cursor.js',
        ['gsap'],
        SKYYROSE_VERSION,
        true
    );

    wp_enqueue_script(
        'skyyrose-main',
        SKYYROSE_URI . '/assets/js/main.js',
        ['gsap', 'skyyrose-gsap-init'],
        SKYYROSE_VERSION,
        true
    );

    // Pre-order script (only on pre-order page)
    if (is_page_template('page-preorder.php') || is_page('pre-order')) {
        wp_enqueue_script(
            'skyyrose-preorder',
            SKYYROSE_URI . '/assets/js/preorder.js',
            ['skyyrose-main'],
            SKYYROSE_VERSION,
            true
        );

        // Pass server time to JS for countdown sync
        wp_localize_script('skyyrose-preorder', 'skyyrose_preorder', [
            'ajax_url'    => admin_url('admin-ajax.php'),
            'nonce'       => wp_create_nonce('skyyrose_preorder_nonce'),
            'server_time' => time() * 1000,
        ]);
    }

    // 3D Viewer script (product pages)
    if (is_singular('product')) {
        wp_enqueue_script(
            'model-viewer',
            'https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js',
            [],
            '3.4.0',
            true
        );

        wp_enqueue_script(
            'skyyrose-3d-viewer',
            SKYYROSE_URI . '/assets/js/3d-viewer.js',
            ['model-viewer'],
            SKYYROSE_VERSION,
            true
        );
    }

    // Experience page assets
    if (is_page_template(['page-experience-black-rose.php', 'page-experience-love-hurts.php', 'page-experience-signature.php'])) {
        // Experience CSS
        wp_enqueue_style(
            'skyyrose-experience',
            SKYYROSE_URI . '/assets/css/experience.css',
            ['skyyrose-main'],
            SKYYROSE_VERSION
        );

        // Model Viewer for AR/3D
        wp_enqueue_script(
            'model-viewer',
            'https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js',
            [],
            '3.4.0',
            true
        );

        // Experience Controller
        wp_enqueue_script(
            'skyyrose-experience',
            SKYYROSE_URI . '/assets/js/experience-controller.js',
            ['gsap', 'gsap-scrolltrigger', 'gsap-scrollto', 'model-viewer'],
            SKYYROSE_VERSION,
            true
        );

        // Enhanced Hotspots System
        wp_enqueue_script(
            'skyyrose-enhanced-hotspots',
            SKYYROSE_URI . '/assets/js/enhanced-hotspots.js',
            ['gsap', 'model-viewer'],
            SKYYROSE_VERSION,
            true
        );

        // Enhanced Hotspots CSS
        wp_enqueue_style(
            'skyyrose-hotspots',
            SKYYROSE_URI . '/assets/css/enhanced-hotspots.css',
            ['skyyrose-experience'],
            SKYYROSE_VERSION
        );

        // Three.js Post-Processing Effects (optional, enabled via theme setting)
        if (get_theme_mod('skyyrose_enable_threejs_effects', true)) {
            wp_enqueue_script(
                'skyyrose-threejs-effects',
                SKYYROSE_URI . '/assets/js/threejs-effects.js',
                ['gsap'],
                SKYYROSE_VERSION,
                true
            );
        }

        // MediaPipe Virtual Try-On (optional, enabled via theme setting)
        if (get_theme_mod('skyyrose_enable_virtual_tryon', false)) {
            wp_enqueue_script(
                'skyyrose-virtual-tryon',
                SKYYROSE_URI . '/assets/js/virtual-tryon.js',
                [],
                SKYYROSE_VERSION,
                true
            );
        }

        // Localize experience data
        $collection = '';
        if (is_page_template('page-experience-black-rose.php')) {
            $collection = 'black-rose';
        } elseif (is_page_template('page-experience-love-hurts.php')) {
            $collection = 'love-hurts';
        } elseif (is_page_template('page-experience-signature.php')) {
            $collection = 'signature';
        }

        wp_localize_script('skyyrose-experience', 'skyyrose_experience', [
            'ajax_url'   => admin_url('admin-ajax.php'),
            'nonce'      => wp_create_nonce('skyyrose_experience_nonce'),
            'collection' => $collection,
            'theme_uri'  => SKYYROSE_URI,
        ]);
    }

    // Localize main script
    wp_localize_script('skyyrose-main', 'skyyrose', [
        'ajax_url'  => admin_url('admin-ajax.php'),
        'theme_uri' => SKYYROSE_URI,
        'nonce'     => wp_create_nonce('skyyrose_nonce'),
        'is_mobile' => wp_is_mobile(),
    ]);
}
add_action('wp_enqueue_scripts', 'skyyrose_enqueue_assets');

/**
 * WooCommerce Setup
 */
function skyyrose_woocommerce_setup(): void {
    // Remove default WooCommerce styles
    add_filter('woocommerce_enqueue_styles', '__return_empty_array');

    // Change products per row
    add_filter('loop_shop_columns', fn() => 3);

    // Change related products count
    add_filter('woocommerce_output_related_products_args', function($args) {
        $args['posts_per_page'] = 4;
        $args['columns'] = 4;
        return $args;
    });
}
add_action('init', 'skyyrose_woocommerce_setup');

/**
 * Register Widget Areas
 */
function skyyrose_widgets_init(): void {
    register_sidebar([
        'name'          => __('Footer Newsletter', 'skyyrose'),
        'id'            => 'footer-newsletter',
        'description'   => __('Newsletter signup widget area', 'skyyrose'),
        'before_widget' => '<div class="footer-newsletter-widget">',
        'after_widget'  => '</div>',
        'before_title'  => '<h4 class="widget-title">',
        'after_title'   => '</h4>',
    ]);

    register_sidebar([
        'name'          => __('Shop Sidebar', 'skyyrose'),
        'id'            => 'shop-sidebar',
        'description'   => __('Sidebar for shop pages', 'skyyrose'),
        'before_widget' => '<div class="shop-widget glass-card">',
        'after_widget'  => '</div>',
        'before_title'  => '<h4 class="widget-title">',
        'after_title'   => '</h4>',
    ]);
}
add_action('widgets_init', 'skyyrose_widgets_init');

/**
 * Custom Mega Menu Walker
 */
class SkyyRose_Mega_Menu_Walker extends Walker_Nav_Menu {
    public function start_lvl(&$output, $depth = 0, $args = null): void {
        $indent = str_repeat("\t", $depth);
        $classes = $depth === 0 ? 'mega-menu-panel glass-panel' : 'mega-menu-submenu';
        $output .= "\n$indent<div class=\"$classes\">\n";
    }

    public function end_lvl(&$output, $depth = 0, $args = null): void {
        $indent = str_repeat("\t", $depth);
        $output .= "$indent</div>\n";
    }

    public function start_el(&$output, $item, $depth = 0, $args = null, $id = 0): void {
        $indent = ($depth) ? str_repeat("\t", $depth) : '';
        $classes = empty($item->classes) ? [] : (array) $item->classes;
        $classes[] = 'menu-item-' . $item->ID;

        if ($depth === 0 && in_array('menu-item-has-children', $classes)) {
            $classes[] = 'has-mega-menu';
        }

        $class_names = implode(' ', array_filter($classes));
        $class_names = $class_names ? ' class="' . esc_attr($class_names) . '"' : '';

        $output .= $indent . '<div' . $class_names . '>';

        $atts = [];
        $atts['title']  = !empty($item->attr_title) ? $item->attr_title : '';
        $atts['target'] = !empty($item->target) ? $item->target : '';
        $atts['rel']    = !empty($item->xfn) ? $item->xfn : '';
        $atts['href']   = !empty($item->url) ? $item->url : '';
        $atts['class']  = 'menu-link';

        $attributes = '';
        foreach ($atts as $attr => $value) {
            if (!empty($value)) {
                $value = ('href' === $attr) ? esc_url($value) : esc_attr($value);
                $attributes .= ' ' . $attr . '="' . $value . '"';
            }
        }

        $title = apply_filters('the_title', $item->title, $item->ID);

        $item_output = $args->before ?? '';
        $item_output .= '<a' . $attributes . '>';
        $item_output .= ($args->link_before ?? '') . $title . ($args->link_after ?? '');
        $item_output .= '</a>';
        $item_output .= $args->after ?? '';

        $output .= apply_filters('walker_nav_menu_start_el', $item_output, $item, $depth, $args);
    }

    public function end_el(&$output, $item, $depth = 0, $args = null): void {
        $output .= "</div>\n";
    }
}

/**
 * Get Collection Data
 */
function skyyrose_get_collection(string $slug): array {
    $collections = [
        'black-rose' => [
            'name'        => 'Black Rose',
            'tagline'     => 'Dark Romance in Every Thread',
            'description' => 'A collection that embraces the beauty of darkness and the elegance of mystery.',
            'colors'      => [
                'primary'   => '#C0C0C0',
                'secondary' => '#0A0A0A',
                'accent'    => '#c8c8dc',
            ],
        ],
        'signature' => [
            'name'        => 'Signature',
            'tagline'     => 'Timeless Elegance Meets Modern Sophistication',
            'description' => 'Our flagship collection representing the pinnacle of luxury fashion.',
            'colors'      => [
                'primary'   => '#C9A962',
                'secondary' => '#B76E79',
                'accent'    => '#D4AF37',
            ],
        ],
        'love-hurts' => [
            'name'        => 'Love Hurts',
            'tagline'     => 'Bold Statements for the Fearless Soul',
            'description' => 'A daring collection that celebrates passion, intensity, and unapologetic self-expression.',
            'colors'      => [
                'primary'   => '#B76E79',
                'secondary' => '#DC143C',
                'accent'    => '#1a1a2e',
            ],
        ],
    ];

    return $collections[$slug] ?? $collections['signature'];
}

/**
 * Pre-order AJAX Handler
 */
function skyyrose_get_preorder_countdown(): void {
    check_ajax_referer('skyyrose_preorder_nonce', 'nonce');

    $product_id = isset($_POST['product_id']) ? absint($_POST['product_id']) : 0;

    if (!$product_id) {
        wp_send_json_error(['message' => 'Invalid product ID']);
    }

    $launch_date = get_post_meta($product_id, '_preorder_launch_date', true);
    $status = get_post_meta($product_id, '_preorder_status', true) ?: 'available';

    if (!$launch_date) {
        wp_send_json_error(['message' => 'No launch date set']);
    }

    $launch_timestamp = strtotime($launch_date);
    $server_time = time();
    $remaining = max(0, $launch_timestamp - $server_time);

    wp_send_json_success([
        'product_id'      => $product_id,
        'launch_date_iso' => date('c', $launch_timestamp),
        'launch_date_unix'=> $launch_timestamp * 1000,
        'server_time_unix'=> $server_time * 1000,
        'status'          => $status,
        'remaining_ms'    => $remaining * 1000,
    ]);
}
add_action('wp_ajax_skyyrose_get_preorder_countdown', 'skyyrose_get_preorder_countdown');
add_action('wp_ajax_nopriv_skyyrose_get_preorder_countdown', 'skyyrose_get_preorder_countdown');

/**
 * Get Pre-order Products
 */
function skyyrose_get_preorder_products(): array {
    $args = [
        'post_type'      => 'product',
        'posts_per_page' => -1,
        'meta_query'     => [
            [
                'key'     => '_preorder_enabled',
                'value'   => 'yes',
                'compare' => '=',
            ],
        ],
        'orderby'        => 'meta_value',
        'meta_key'       => '_preorder_launch_date',
        'order'          => 'ASC',
    ];

    $query = new WP_Query($args);
    $products = [];

    if ($query->have_posts()) {
        while ($query->have_posts()) {
            $query->the_post();
            $product_id = get_the_ID();
            $product = wc_get_product($product_id);

            if (!$product) continue;

            $products[] = [
                'id'          => $product_id,
                'name'        => $product->get_name(),
                'price'       => $product->get_price_html(),
                'image'       => wp_get_attachment_image_url($product->get_image_id(), 'skyyrose-product'),
                'link'        => $product->get_permalink(),
                'status'      => get_post_meta($product_id, '_preorder_status', true) ?: 'blooming_soon',
                'launch_date' => get_post_meta($product_id, '_preorder_launch_date', true),
                'collection'  => get_post_meta($product_id, '_preorder_collection', true),
                'ar_enabled'  => get_post_meta($product_id, '_preorder_ar_enabled', true) === 'yes',
            ];
        }
        wp_reset_postdata();
    }

    return $products;
}

/**
 * Add body classes
 */
function skyyrose_body_class(array $classes): array {
    $classes[] = 'skyyrose-theme';

    if (is_front_page()) {
        $classes[] = 'skyyrose-home';
    }

    if (is_page_template('page-preorder.php') || is_page('pre-order')) {
        $classes[] = 'skyyrose-preorder';
    }

    if (is_page_template('page-templates/collection-experience.php')) {
        $classes[] = 'skyyrose-experience';
    }

    // Experience page specific classes
    if (is_page_template('page-experience-black-rose.php')) {
        $classes[] = 'skyyrose-experience';
        $classes[] = 'experience-black-rose';
    }

    if (is_page_template('page-experience-love-hurts.php')) {
        $classes[] = 'skyyrose-experience';
        $classes[] = 'experience-love-hurts';
    }

    if (is_page_template('page-experience-signature.php')) {
        $classes[] = 'skyyrose-experience';
        $classes[] = 'experience-signature';
    }

    // Detect touch devices
    if (wp_is_mobile()) {
        $classes[] = 'is-touch-device';
    }

    return $classes;
}
add_filter('body_class', 'skyyrose_body_class');

/**
 * Include additional files
 */
require_once SKYYROSE_DIR . '/inc/customizer.php';

// Include WooCommerce functions if active
if (class_exists('WooCommerce')) {
    require_once SKYYROSE_DIR . '/inc/woocommerce.php';
}

/**
 * ============================================================================
 * Email Capture & Newsletter System
 * ============================================================================
 */

/**
 * Handle email capture AJAX request
 */
function skyyrose_handle_email_capture(): void {
    // Verify nonce
    if (!wp_verify_nonce($_POST['email_nonce'] ?? '', 'skyyrose_email_capture')) {
        wp_send_json_error('Security check failed');
        return;
    }

    $email = sanitize_email($_POST['email'] ?? '');
    $source = sanitize_text_field($_POST['source'] ?? 'unknown');

    if (!is_email($email)) {
        wp_send_json_error('Please enter a valid email address');
        return;
    }

    // Check if email already exists
    $existing = get_users([
        'search'         => $email,
        'search_columns' => ['user_email'],
        'number'         => 1,
    ]);

    $subscriber_exists = !empty($existing);

    // Also check newsletter subscribers table/option
    $subscribers = get_option('skyyrose_newsletter_subscribers', []);
    if (isset($subscribers[$email])) {
        $subscriber_exists = true;
    }

    // Generate discount code
    $discount_code = skyyrose_generate_discount_code($email);

    if (!$subscriber_exists) {
        // Store subscriber
        $subscribers[$email] = [
            'email'      => $email,
            'source'     => $source,
            'subscribed' => current_time('mysql'),
            'ip'         => sanitize_text_field($_SERVER['REMOTE_ADDR'] ?? ''),
            'discount'   => $discount_code,
        ];
        update_option('skyyrose_newsletter_subscribers', $subscribers);

        // Create WooCommerce customer if WooCommerce is active
        if (class_exists('WooCommerce')) {
            $customer = new WC_Customer();
            $customer->set_email($email);
            $customer->set_billing_email($email);
            $customer->save();
        }

        // Send welcome email
        skyyrose_send_welcome_email($email, $discount_code);

        // Hook for external integrations (Mailchimp, Klaviyo, etc.)
        do_action('skyyrose_new_subscriber', $email, $source, $discount_code);
    }

    wp_send_json_success([
        'message' => 'Welcome to the SkyyRose family!',
        'code'    => $discount_code,
    ]);
}
add_action('wp_ajax_skyyrose_capture_email', 'skyyrose_handle_email_capture');
add_action('wp_ajax_nopriv_skyyrose_capture_email', 'skyyrose_handle_email_capture');

/**
 * Generate a unique discount code for new subscriber
 */
function skyyrose_generate_discount_code(string $email): string {
    $discount_percent = get_theme_mod('skyyrose_popup_discount', '15');

    // Create unique code based on email hash
    $code = 'ROSE' . strtoupper(substr(md5($email . wp_salt()), 0, 6));

    // Create WooCommerce coupon if it doesn't exist
    if (class_exists('WooCommerce')) {
        $existing_coupon = wc_get_coupon_id_by_code($code);

        if (!$existing_coupon) {
            $coupon = new WC_Coupon();
            $coupon->set_code($code);
            $coupon->set_discount_type('percent');
            $coupon->set_amount($discount_percent);
            $coupon->set_individual_use(true);
            $coupon->set_usage_limit(1);
            $coupon->set_usage_limit_per_user(1);
            $coupon->set_email_restrictions([$email]);
            $coupon->set_date_expires(strtotime('+30 days'));
            $coupon->set_description('Welcome discount for ' . $email);
            $coupon->save();
        }
    }

    return $code;
}

/**
 * Send welcome email with discount code
 */
function skyyrose_send_welcome_email(string $email, string $discount_code): void {
    $discount_percent = get_theme_mod('skyyrose_popup_discount', '15');
    $shop_url = wc_get_page_permalink('shop');

    $subject = 'Welcome to the Rose Garden - Your ' . $discount_percent . '% Discount Inside';

    $message = '
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #0A0A0A; color: #ffffff;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0A0A0A;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px;">
                    <!-- Logo -->
                    <tr>
                        <td align="center" style="padding-bottom: 30px;">
                            <h1 style="font-family: Georgia, serif; font-size: 32px; color: #B76E79; margin: 0;">SkyyRose</h1>
                            <p style="color: #888; font-size: 12px; margin: 5px 0 0; letter-spacing: 2px;">WHERE LOVE MEETS LUXURY</p>
                        </td>
                    </tr>

                    <!-- Hero -->
                    <tr>
                        <td style="background: linear-gradient(145deg, #1A1A1A 0%, #0D0D0D 100%); border-radius: 16px; padding: 40px; text-align: center;">
                            <h2 style="font-family: Georgia, serif; font-size: 28px; color: #ffffff; margin: 0 0 20px;">Welcome to the Garden</h2>
                            <p style="color: #aaa; font-size: 16px; line-height: 1.6; margin: 0 0 30px;">
                                Thank you for joining the SkyyRose family. As a welcome gift, here\'s your exclusive discount:
                            </p>

                            <!-- Discount Code Box -->
                            <div style="background: rgba(183, 110, 121, 0.1); border: 2px dashed #B76E79; border-radius: 8px; padding: 20px; margin: 0 0 30px;">
                                <p style="color: #888; font-size: 12px; margin: 0 0 10px; text-transform: uppercase; letter-spacing: 2px;">Your Discount Code</p>
                                <p style="font-family: monospace; font-size: 28px; font-weight: bold; color: #B76E79; margin: 0; letter-spacing: 3px;">' . esc_html($discount_code) . '</p>
                                <p style="color: #aaa; font-size: 14px; margin: 10px 0 0;">' . esc_html($discount_percent) . '% off your first order</p>
                            </div>

                            <!-- CTA Button -->
                            <a href="' . esc_url($shop_url) . '" style="display: inline-block; background: #B76E79; color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 8px; font-weight: 600; font-size: 16px;">Shop Now</a>

                            <p style="color: #666; font-size: 12px; margin: 30px 0 0;">
                                Code expires in 30 days. One-time use only.
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px; text-align: center;">
                            <p style="color: #666; font-size: 12px; margin: 0;">
                                SkyyRose LLC | Oakland, CA<br>
                                <a href="' . esc_url(home_url('/privacy-policy/')) . '" style="color: #B76E79;">Privacy Policy</a> |
                                <a href="' . esc_url(home_url('/unsubscribe/?email=' . urlencode($email))) . '" style="color: #B76E79;">Unsubscribe</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>';

    $headers = [
        'Content-Type: text/html; charset=UTF-8',
        'From: SkyyRose <hello@skyyrose.co>',
    ];

    wp_mail($email, $subject, $message, $headers);
}

/**
 * Include email popup in footer
 */
function skyyrose_include_email_popup(): void {
    // Only show on frontend, not in admin
    if (is_admin()) {
        return;
    }

    // Check if popup is enabled
    if (!get_theme_mod('skyyrose_enable_popup', true)) {
        return;
    }

    get_template_part('template-parts/email-capture-popup');
}
add_action('wp_footer', 'skyyrose_include_email_popup');

/**
 * Admin page for viewing subscribers
 */
function skyyrose_add_subscribers_menu(): void {
    add_submenu_page(
        'woocommerce',
        'Newsletter Subscribers',
        'Newsletter',
        'manage_woocommerce',
        'skyyrose-subscribers',
        'skyyrose_subscribers_page'
    );
}
add_action('admin_menu', 'skyyrose_add_subscribers_menu');

/**
 * Render subscribers admin page
 */
function skyyrose_subscribers_page(): void {
    $subscribers = get_option('skyyrose_newsletter_subscribers', []);
    $count = count($subscribers);

    echo '<div class="wrap">';
    echo '<h1>Newsletter Subscribers (' . esc_html($count) . ')</h1>';

    // Export button
    echo '<p><a href="' . esc_url(admin_url('admin.php?page=skyyrose-subscribers&export=csv')) . '" class="button">Export CSV</a></p>';

    // Handle CSV export
    if (isset($_GET['export']) && $_GET['export'] === 'csv') {
        header('Content-Type: text/csv');
        header('Content-Disposition: attachment; filename="skyyrose-subscribers-' . date('Y-m-d') . '.csv"');

        $output = fopen('php://output', 'w');
        fputcsv($output, ['Email', 'Source', 'Subscribed', 'Discount Code']);

        foreach ($subscribers as $sub) {
            fputcsv($output, [
                $sub['email'],
                $sub['source'],
                $sub['subscribed'],
                $sub['discount'] ?? '',
            ]);
        }

        fclose($output);
        exit;
    }

    // Display table
    if (empty($subscribers)) {
        echo '<p>No subscribers yet.</p>';
    } else {
        echo '<table class="wp-list-table widefat fixed striped">';
        echo '<thead><tr><th>Email</th><th>Source</th><th>Subscribed</th><th>Discount</th></tr></thead>';
        echo '<tbody>';

        foreach (array_reverse($subscribers) as $sub) {
            echo '<tr>';
            echo '<td>' . esc_html($sub['email']) . '</td>';
            echo '<td>' . esc_html($sub['source']) . '</td>';
            echo '<td>' . esc_html($sub['subscribed']) . '</td>';
            echo '<td><code>' . esc_html($sub['discount'] ?? 'N/A') . '</code></td>';
            echo '</tr>';
        }

        echo '</tbody></table>';
    }

    echo '</div>';
}

/**
 * Add customizer settings for email popup
 */
function skyyrose_email_customizer(WP_Customize_Manager $wp_customize): void {
    // Add section
    $wp_customize->add_section('skyyrose_email_popup', [
        'title'    => __('Email Popup', 'skyyrose'),
        'priority' => 35,
    ]);

    // Enable popup
    $wp_customize->add_setting('skyyrose_enable_popup', [
        'default'           => true,
        'sanitize_callback' => 'wp_validate_boolean',
    ]);

    $wp_customize->add_control('skyyrose_enable_popup', [
        'label'   => __('Enable Email Popup', 'skyyrose'),
        'section' => 'skyyrose_email_popup',
        'type'    => 'checkbox',
    ]);

    // Discount percentage
    $wp_customize->add_setting('skyyrose_popup_discount', [
        'default'           => '15',
        'sanitize_callback' => 'absint',
    ]);

    $wp_customize->add_control('skyyrose_popup_discount', [
        'label'   => __('Discount Percentage', 'skyyrose'),
        'section' => 'skyyrose_email_popup',
        'type'    => 'number',
    ]);

    // Popup delay
    $wp_customize->add_setting('skyyrose_popup_delay', [
        'default'           => 5000,
        'sanitize_callback' => 'absint',
    ]);

    $wp_customize->add_control('skyyrose_popup_delay', [
        'label'       => __('Popup Delay (ms)', 'skyyrose'),
        'description' => __('Time before popup appears (in milliseconds)', 'skyyrose'),
        'section'     => 'skyyrose_email_popup',
        'type'        => 'number',
    ]);

    // Collection theme
    $wp_customize->add_setting('skyyrose_popup_collection', [
        'default'           => 'signature',
        'sanitize_callback' => 'sanitize_text_field',
    ]);

    $wp_customize->add_control('skyyrose_popup_collection', [
        'label'   => __('Popup Theme', 'skyyrose'),
        'section' => 'skyyrose_email_popup',
        'type'    => 'select',
        'choices' => [
            'signature'  => __('Signature (Gold)', 'skyyrose'),
            'black-rose' => __('Black Rose (Red)', 'skyyrose'),
            'love-hurts' => __('Love Hurts (Pink)', 'skyyrose'),
        ],
    ]);
}
add_action('customize_register', 'skyyrose_email_customizer');
