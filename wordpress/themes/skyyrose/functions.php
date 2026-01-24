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
