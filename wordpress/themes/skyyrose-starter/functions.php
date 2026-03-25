<?php
/**
 * SkyyRose Starter Theme Functions
 *
 * @package SkyyRose
 * @version 1.0.0
 */

defined('ABSPATH') || exit;

/**
 * Theme Constants
 */
define('SKYYROSE_VERSION', '1.0.0');
define('SKYYROSE_DIR', get_template_directory());
define('SKYYROSE_URI', get_template_directory_uri());
define('SKYYROSE_DEBUG', defined('WP_DEBUG') && WP_DEBUG);

/**
 * Get asset suffix for minified files
 */
function skyyrose_asset_suffix(): string {
    return SKYYROSE_DEBUG ? '' : '.min';
}

/**
 * Get asset path with optional minification
 */
function skyyrose_asset_url(string $type, string $file): string {
    $suffix = skyyrose_asset_suffix();
    $base = SKYYROSE_URI . "/assets/{$type}";

    if ($suffix && file_exists(SKYYROSE_DIR . "/assets/{$type}/min/{$file}{$suffix}.{$type}")) {
        return "{$base}/min/{$file}{$suffix}.{$type}";
    }

    return "{$base}/{$file}.{$type}";
}

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

    // WooCommerce support
    add_theme_support('woocommerce');
    add_theme_support('wc-product-gallery-zoom');
    add_theme_support('wc-product-gallery-lightbox');
    add_theme_support('wc-product-gallery-slider');

    // Custom logo
    add_theme_support('custom-logo', [
        'height'      => 60,
        'width'       => 200,
        'flex-height' => true,
        'flex-width'  => true,
    ]);

    // Register nav menus
    register_nav_menus([
        'primary'    => __('Primary Menu', 'skyyrose'),
        'footer'     => __('Footer Menu', 'skyyrose'),
        'shop'       => __('Shop Menu', 'skyyrose'),
        'support'    => __('Support Menu', 'skyyrose'),
        'social'     => __('Social Menu', 'skyyrose'),
    ]);

    // Custom image sizes
    add_image_size('skyyrose-hero', 1920, 1080, true);
    add_image_size('skyyrose-product', 600, 800, true);
    add_image_size('skyyrose-product-large', 900, 1200, true);
    add_image_size('skyyrose-product-thumb', 150, 200, true);
    add_image_size('skyyrose-collection', 800, 600, true);
    add_image_size('skyyrose-blog', 800, 500, true);
}
add_action('after_setup_theme', 'skyyrose_setup');

/**
 * Enqueue Scripts and Styles
 */
function skyyrose_scripts(): void {
    // Google Fonts - with display=swap for performance
    wp_enqueue_style(
        'skyyrose-fonts',
        'https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap',
        [],
        null
    );
    // Add preconnect for Google Fonts (handled in header)

    // Main stylesheet
    wp_enqueue_style(
        'skyyrose-style',
        get_stylesheet_uri(),
        ['skyyrose-fonts'],
        SKYYROSE_VERSION
    );

    // Component styles (minified in production)
    wp_enqueue_style(
        'skyyrose-components',
        skyyrose_asset_url('css', 'components'),
        ['skyyrose-style'],
        SKYYROSE_VERSION
    );

    // WooCommerce styles (if active)
    if (class_exists('WooCommerce')) {
        wp_enqueue_style(
            'skyyrose-woocommerce',
            skyyrose_asset_url('css', 'woocommerce'),
            ['skyyrose-components'],
            SKYYROSE_VERSION
        );
    }

    // Page styles
    wp_enqueue_style(
        'skyyrose-pages',
        skyyrose_asset_url('css', 'pages'),
        ['skyyrose-components'],
        SKYYROSE_VERSION
    );

    // Main JavaScript (minified in production)
    wp_enqueue_script(
        'skyyrose-main',
        skyyrose_asset_url('js', 'main'),
        [],
        SKYYROSE_VERSION,
        ['strategy' => 'defer', 'in_footer' => true]
    );

    // Conversion Boosters (sales-driving features)
    wp_enqueue_style(
        'skyyrose-conversion',
        skyyrose_asset_url('css', 'conversion-boosters'),
        ['skyyrose-style'],
        SKYYROSE_VERSION
    );

    wp_enqueue_script(
        'skyyrose-conversion',
        skyyrose_asset_url('js', 'conversion-boosters'),
        ['skyyrose-main'],
        SKYYROSE_VERSION,
        ['strategy' => 'defer', 'in_footer' => true]
    );

    // Luxury Aesthetics (premium visual effects)
    wp_enqueue_style(
        'skyyrose-aesthetics',
        skyyrose_asset_url('css', 'luxury-aesthetics'),
        ['skyyrose-style'],
        SKYYROSE_VERSION
    );

    wp_enqueue_script(
        'skyyrose-aesthetics',
        skyyrose_asset_url('js', 'luxury-aesthetics'),
        ['skyyrose-main'],
        SKYYROSE_VERSION,
        ['strategy' => 'defer', 'in_footer' => true]
    );

    // Localize script for AJAX
    wp_localize_script('skyyrose-main', 'skyyrose', [
        'ajax_url' => admin_url('admin-ajax.php'),
        'nonce'    => wp_create_nonce('skyyrose_nonce'),
        'cart_url' => function_exists('wc_get_cart_url') ? wc_get_cart_url() : '',
    ]);
}
add_action('wp_enqueue_scripts', 'skyyrose_scripts');

/**
 * Remove WooCommerce Default Styles
 */
function skyyrose_dequeue_wc_styles($styles): array {
    // Keep only essential WooCommerce styles, remove the rest
    unset($styles['woocommerce-general']);
    unset($styles['woocommerce-layout']);
    unset($styles['woocommerce-smallscreen']);
    return $styles;
}
add_filter('woocommerce_enqueue_styles', 'skyyrose_dequeue_wc_styles');

/**
 * Collection Data
 */
function skyyrose_get_collections(): array {
    return [
        'black-rose' => [
            'name'        => 'BLACK ROSE',
            'tagline'     => 'Dark elegance for the bold',
            'color'       => '#8B0000',
            'category_id' => get_option('skyyrose_blackrose_cat', 0),
            'logo'        => SKYYROSE_URI . '/assets/images/logos/black-rose-logo.jpg',
        ],
        'love-hurts' => [
            'name'        => 'LOVE HURTS',
            'tagline'     => 'Where emotion meets fashion',
            'color'       => '#B76E79',
            'category_id' => get_option('skyyrose_lovehurts_cat', 0),
            'logo'        => SKYYROSE_URI . '/assets/images/logos/love-hurts-logo.jpg',
        ],
        'signature' => [
            'name'        => 'SIGNATURE',
            'tagline'     => 'Timeless luxury essentials',
            'color'       => '#D4AF37',
            'category_id' => get_option('skyyrose_signature_cat', 0),
            'logo'        => SKYYROSE_URI . '/assets/images/logos/signature-logo.png',
        ],
    ];
}

/**
 * Get Collection by Product
 */
function skyyrose_get_product_collection($product_id): ?array {
    $collections = skyyrose_get_collections();
    $terms = get_the_terms($product_id, 'product_cat');

    if (!$terms || is_wp_error($terms)) {
        return $collections['signature']; // Default
    }

    foreach ($terms as $term) {
        $slug = strtolower($term->slug);
        if (strpos($slug, 'black') !== false || strpos($slug, 'rose') !== false) {
            return $collections['black-rose'];
        }
        if (strpos($slug, 'love') !== false || strpos($slug, 'hurt') !== false) {
            return $collections['love-hurts'];
        }
        if (strpos($slug, 'signature') !== false) {
            return $collections['signature'];
        }
    }

    return $collections['signature'];
}

/**
 * Get Collection Slug by Product
 */
function skyyrose_get_product_collection_slug($product_id): string {
    $terms = get_the_terms($product_id, 'product_cat');

    if (!$terms || is_wp_error($terms)) {
        return 'signature';
    }

    foreach ($terms as $term) {
        $slug = strtolower($term->slug);
        if (strpos($slug, 'black') !== false || strpos($slug, 'rose') !== false) {
            return 'black-rose';
        }
        if (strpos($slug, 'love') !== false || strpos($slug, 'hurt') !== false) {
            return 'love-hurts';
        }
        if (strpos($slug, 'signature') !== false) {
            return 'signature';
        }
    }

    return 'signature';
}

/**
 * AJAX Add to Cart
 */
function skyyrose_ajax_add_to_cart(): void {
    check_ajax_referer('skyyrose_nonce', 'nonce');

    $product_id = absint($_POST['product_id'] ?? 0);
    $quantity = absint($_POST['quantity'] ?? 1);

    if (!$product_id) {
        wp_send_json_error(['message' => 'Invalid product']);
    }

    $added = WC()->cart->add_to_cart($product_id, $quantity);

    if ($added) {
        wp_send_json_success([
            'message'    => 'Added to cart!',
            'cart_count' => WC()->cart->get_cart_contents_count(),
            'cart_total' => WC()->cart->get_cart_total(),
        ]);
    } else {
        wp_send_json_error(['message' => 'Could not add to cart']);
    }
}
add_action('wp_ajax_skyyrose_add_to_cart', 'skyyrose_ajax_add_to_cart');
add_action('wp_ajax_nopriv_skyyrose_add_to_cart', 'skyyrose_ajax_add_to_cart');

/**
 * Update Cart Fragment for Header
 */
function skyyrose_cart_fragment($fragments): array {
    ob_start();
    ?>
    <span class="cart-count" id="cartCount"><?php echo WC()->cart->get_cart_contents_count(); ?></span>
    <?php
    $fragments['.cart-count'] = ob_get_clean();
    return $fragments;
}
add_filter('woocommerce_add_to_cart_fragments', 'skyyrose_cart_fragment');

/**
 * Newsletter Signup (Klaviyo)
 */
function skyyrose_newsletter_signup(): void {
    check_ajax_referer('skyyrose_nonce', 'nonce');

    $email = sanitize_email($_POST['email'] ?? '');

    if (!is_email($email)) {
        wp_send_json_error(['message' => 'Please enter a valid email']);
    }

    // Klaviyo API integration
    $klaviyo_key = get_option('skyyrose_klaviyo_key', '');
    $klaviyo_list = get_option('skyyrose_klaviyo_list', '');

    if ($klaviyo_key && $klaviyo_list) {
        $response = wp_remote_post('https://a.klaviyo.com/api/v2/list/' . $klaviyo_list . '/subscribe', [
            'headers' => [
                'Content-Type' => 'application/json',
                'api-key'      => $klaviyo_key,
            ],
            'body'    => wp_json_encode([
                'profiles' => [
                    ['email' => $email],
                ],
            ]),
        ]);

        if (is_wp_error($response)) {
            wp_send_json_error(['message' => 'Subscription failed. Please try again.']);
        }
    }

    // Store locally as backup
    $subscribers = get_option('skyyrose_subscribers', []);
    $subscribers[] = [
        'email' => $email,
        'date'  => current_time('mysql'),
    ];
    update_option('skyyrose_subscribers', $subscribers);

    wp_send_json_success(['message' => 'Welcome to the SkyyRose family!']);
}
add_action('wp_ajax_skyyrose_newsletter', 'skyyrose_newsletter_signup');
add_action('wp_ajax_nopriv_skyyrose_newsletter', 'skyyrose_newsletter_signup');

/**
 * Contact Form Handler
 */
function skyyrose_contact_form(): void {
    check_ajax_referer('skyyrose_contact', 'contact_nonce');

    $name = sanitize_text_field($_POST['name'] ?? '');
    $email = sanitize_email($_POST['email'] ?? '');
    $subject = sanitize_text_field($_POST['subject'] ?? '');
    $message = sanitize_textarea_field($_POST['message'] ?? '');

    if (!$name || !$email || !$message) {
        wp_send_json_error(['message' => 'Please fill in all required fields.']);
    }

    if (!is_email($email)) {
        wp_send_json_error(['message' => 'Please enter a valid email address.']);
    }

    // Send email to admin
    $to = get_option('admin_email');
    $email_subject = sprintf('[SkyyRose Contact] %s', $subject ?: 'New Message');
    $email_body = sprintf(
        "Name: %s\nEmail: %s\n\nMessage:\n%s",
        $name,
        $email,
        $message
    );
    $headers = [
        'Content-Type: text/plain; charset=UTF-8',
        sprintf('Reply-To: %s <%s>', $name, $email),
    ];

    $sent = wp_mail($to, $email_subject, $email_body, $headers);

    if ($sent) {
        wp_send_json_success(['message' => 'Thank you for your message! We\'ll get back to you soon.']);
    } else {
        wp_send_json_error(['message' => 'Failed to send message. Please try again.']);
    }
}
add_action('wp_ajax_skyyrose_contact', 'skyyrose_contact_form');
add_action('wp_ajax_nopriv_skyyrose_contact', 'skyyrose_contact_form');

/**
 * WooCommerce: Products per page
 */
add_filter('loop_shop_per_page', fn() => 12);

/**
 * WooCommerce: Remove breadcrumbs (we use custom)
 */
remove_action('woocommerce_before_main_content', 'woocommerce_breadcrumb', 20);

/**
 * WooCommerce: Remove sidebar from shop
 */
remove_action('woocommerce_sidebar', 'woocommerce_get_sidebar', 10);

/**
 * WooCommerce: Custom single product layout
 */
remove_action('woocommerce_single_product_summary', 'woocommerce_template_single_title', 5);
remove_action('woocommerce_single_product_summary', 'woocommerce_template_single_price', 10);
remove_action('woocommerce_single_product_summary', 'woocommerce_template_single_excerpt', 20);
remove_action('woocommerce_single_product_summary', 'woocommerce_template_single_meta', 40);

/**
 * WooCommerce: Remove related products heading
 */
add_filter('woocommerce_product_related_products_heading', fn() => 'Complete the Look');

/**
 * Body Classes
 */
function skyyrose_body_classes($classes): array {
    // Add collection class on single product
    if (is_singular('product')) {
        global $post;
        $collection = skyyrose_get_product_collection($post->ID);
        $classes[] = 'collection-' . sanitize_html_class(strtolower(str_replace(' ', '-', $collection['name'])));
    }

    // Add page template class
    if (is_page_template()) {
        $template = get_page_template_slug();
        $classes[] = 'template-' . sanitize_html_class(basename($template, '.php'));
    }

    return $classes;
}
add_filter('body_class', 'skyyrose_body_classes');

/**
 * Customizer Settings
 */
function skyyrose_customizer($wp_customize): void {
    // SkyyRose Settings Section
    $wp_customize->add_section('skyyrose_settings', [
        'title'    => __('SkyyRose Settings', 'skyyrose'),
        'priority' => 30,
    ]);

    // Hero Video URL
    $wp_customize->add_setting('skyyrose_hero_video', [
        'default'           => '',
        'sanitize_callback' => 'esc_url_raw',
    ]);
    $wp_customize->add_control('skyyrose_hero_video', [
        'label'   => __('Hero Video URL', 'skyyrose'),
        'section' => 'skyyrose_settings',
        'type'    => 'url',
    ]);

    // Hero Title
    $wp_customize->add_setting('skyyrose_hero_title', [
        'default'           => 'Where Love Meets Luxury',
        'sanitize_callback' => 'sanitize_text_field',
    ]);
    $wp_customize->add_control('skyyrose_hero_title', [
        'label'   => __('Hero Title', 'skyyrose'),
        'section' => 'skyyrose_settings',
        'type'    => 'text',
    ]);

    // Klaviyo API Key
    $wp_customize->add_setting('skyyrose_klaviyo_key', [
        'default'           => '',
        'sanitize_callback' => 'sanitize_text_field',
    ]);
    $wp_customize->add_control('skyyrose_klaviyo_key', [
        'label'   => __('Klaviyo API Key', 'skyyrose'),
        'section' => 'skyyrose_settings',
        'type'    => 'password',
    ]);

    // Klaviyo List ID
    $wp_customize->add_setting('skyyrose_klaviyo_list', [
        'default'           => '',
        'sanitize_callback' => 'sanitize_text_field',
    ]);
    $wp_customize->add_control('skyyrose_klaviyo_list', [
        'label'   => __('Klaviyo List ID', 'skyyrose'),
        'section' => 'skyyrose_settings',
        'type'    => 'text',
    ]);
}
add_action('customize_register', 'skyyrose_customizer');

/**
 * Custom Walker for Primary Navigation
 */
class SkyyRose_Nav_Walker extends Walker_Nav_Menu {
    public function start_el(&$output, $item, $depth = 0, $args = null, $id = 0): void {
        $classes = empty($item->classes) ? [] : (array) $item->classes;
        $class_names = implode(' ', array_filter($classes));

        $output .= '<li class="' . esc_attr($class_names) . '">';

        $attributes = '';
        if (!empty($item->url)) {
            $attributes .= ' href="' . esc_attr($item->url) . '"';
        }

        $output .= '<a' . $attributes . '>';
        $output .= esc_html($item->title);
        $output .= '</a>';
    }
}

/**
 * Elementor Compatibility
 */
function skyyrose_elementor_support(): void {
    // Register Elementor locations for theme builder
    if (did_action('elementor/loaded')) {
        add_action('elementor/theme/register_locations', function($elementor_theme_manager) {
            $elementor_theme_manager->register_location('header');
            $elementor_theme_manager->register_location('footer');
            $elementor_theme_manager->register_location('single');
            $elementor_theme_manager->register_location('archive');
        });
    }
}
add_action('after_setup_theme', 'skyyrose_elementor_support');

/**
 * Enqueue Elementor-specific styles
 */
function skyyrose_elementor_styles(): void {
    if (did_action('elementor/loaded')) {
        wp_enqueue_style(
            'skyyrose-elementor',
            SKYYROSE_URI . '/assets/css/elementor-overrides.css',
            ['skyyrose-style'],
            SKYYROSE_VERSION
        );
    }
}
add_action('wp_enqueue_scripts', 'skyyrose_elementor_styles', 20);

/**
 * Add SkyyRose color palette to Elementor
 */
function skyyrose_elementor_colors($config) {
    $config['default_schemes']['color']['items'] = [
        '1' => ['value' => '#B76E79'],  // Love Hurts Rose
        '2' => ['value' => '#8B0000'],  // Black Rose
        '3' => ['value' => '#D4AF37'],  // Signature Gold
        '4' => ['value' => '#0D0D0D'],  // Dark Background
    ];
    return $config;
}
add_filter('elementor/schemes/default_colors', 'skyyrose_elementor_colors');

/**
 * Include Template Parts
 */
require_once SKYYROSE_DIR . '/inc/template-tags.php';

// ============================================
// PERFORMANCE OPTIMIZATIONS
// ============================================

/**
 * Add Resource Hints (preconnect, dns-prefetch)
 */
function skyyrose_resource_hints($hints, $relation_type): array {
    if ($relation_type === 'preconnect') {
        $hints[] = [
            'href'        => 'https://fonts.googleapis.com',
            'crossorigin' => 'anonymous',
        ];
        $hints[] = [
            'href'        => 'https://fonts.gstatic.com',
            'crossorigin' => 'anonymous',
        ];
    }

    if ($relation_type === 'dns-prefetch') {
        $hints[] = '//fonts.googleapis.com';
        $hints[] = '//fonts.gstatic.com';
        $hints[] = '//www.googletagmanager.com';
    }

    return $hints;
}
add_filter('wp_resource_hints', 'skyyrose_resource_hints', 10, 2);

/**
 * Preload Critical Assets
 */
function skyyrose_preload_assets(): void {
    // Preload main CSS
    $css_url = skyyrose_asset_url('css', 'components');
    echo '<link rel="preload" href="' . esc_url($css_url) . '" as="style">' . "\n";

    // Preload logo (WebP with fallback)
    $logo_webp = SKYYROSE_URI . '/assets/images/logos/skyyrose-logo.webp';
    echo '<link rel="preload" href="' . esc_url($logo_webp) . '" as="image" type="image/webp">' . "\n";
}
add_action('wp_head', 'skyyrose_preload_assets', 1);

/**
 * Add defer attribute to non-critical scripts
 */
function skyyrose_defer_scripts($tag, $handle, $src): string {
    $defer_scripts = ['skyyrose-conversion', 'skyyrose-aesthetics'];

    if (in_array($handle, $defer_scripts, true)) {
        return str_replace(' src', ' defer src', $tag);
    }

    return $tag;
}
add_filter('script_loader_tag', 'skyyrose_defer_scripts', 10, 3);

/**
 * Add lazy loading to images
 */
function skyyrose_lazy_load_images($attr, $attachment, $size): array {
    $attr['loading'] = 'lazy';
    $attr['decoding'] = 'async';
    return $attr;
}
add_filter('wp_get_attachment_image_attributes', 'skyyrose_lazy_load_images', 10, 3);

/**
 * Disable emoji scripts (performance)
 */
function skyyrose_disable_emojis(): void {
    remove_action('wp_head', 'print_emoji_detection_script', 7);
    remove_action('admin_print_scripts', 'print_emoji_detection_script');
    remove_action('wp_print_styles', 'print_emoji_styles');
    remove_action('admin_print_styles', 'print_emoji_styles');
    remove_filter('the_content_feed', 'wp_staticize_emoji');
    remove_filter('comment_text_rss', 'wp_staticize_emoji');
    remove_filter('wp_mail', 'wp_staticize_emoji_for_email');
}
add_action('init', 'skyyrose_disable_emojis');

/**
 * Remove jQuery migrate (if not needed)
 */
function skyyrose_remove_jquery_migrate($scripts): void {
    if (!is_admin() && isset($scripts->registered['jquery'])) {
        $script = $scripts->registered['jquery'];
        if ($script->deps) {
            $script->deps = array_diff($script->deps, ['jquery-migrate']);
        }
    }
}
add_action('wp_default_scripts', 'skyyrose_remove_jquery_migrate');

/**
 * WebP Image Helper - Returns picture element with WebP and fallback
 */
function skyyrose_webp_image(string $image_path, string $alt = '', array $attrs = []): string {
    $webp_path = preg_replace('/\.(jpg|jpeg|png)$/i', '.webp', $image_path);
    $webp_exists = file_exists(str_replace(SKYYROSE_URI, SKYYROSE_DIR, $webp_path));

    $attr_string = '';
    foreach ($attrs as $key => $value) {
        $attr_string .= ' ' . esc_attr($key) . '="' . esc_attr($value) . '"';
    }

    if ($webp_exists) {
        return sprintf(
            '<picture>
                <source srcset="%s" type="image/webp">
                <img src="%s" alt="%s" loading="lazy" decoding="async"%s>
            </picture>',
            esc_url($webp_path),
            esc_url($image_path),
            esc_attr($alt),
            $attr_string
        );
    }

    return sprintf(
        '<img src="%s" alt="%s" loading="lazy" decoding="async"%s>',
        esc_url($image_path),
        esc_attr($alt),
        $attr_string
    );
}

/**
 * Remove unnecessary WordPress features for performance
 */
function skyyrose_cleanup_head(): void {
    // Remove RSD link
    remove_action('wp_head', 'rsd_link');
    // Remove Windows Live Writer link
    remove_action('wp_head', 'wlwmanifest_link');
    // Remove shortlink
    remove_action('wp_head', 'wp_shortlink_wp_head');
    // Remove WordPress version
    remove_action('wp_head', 'wp_generator');
    // Remove REST API link
    remove_action('wp_head', 'rest_output_link_wp_head');
    // Remove oEmbed discovery links
    remove_action('wp_head', 'wp_oembed_add_discovery_links');
}
add_action('init', 'skyyrose_cleanup_head');

/**
 * Optimize WooCommerce scripts loading
 */
function skyyrose_wc_script_optimization(): void {
    // Only load WooCommerce scripts on relevant pages
    if (function_exists('is_woocommerce')) {
        if (!is_woocommerce() && !is_cart() && !is_checkout() && !is_account_page()) {
            // Dequeue WooCommerce scripts on non-shop pages
            wp_dequeue_script('wc-cart-fragments');
            wp_dequeue_script('woocommerce');
            wp_dequeue_script('wc-add-to-cart');
        }
    }
}
add_action('wp_enqueue_scripts', 'skyyrose_wc_script_optimization', 99);
