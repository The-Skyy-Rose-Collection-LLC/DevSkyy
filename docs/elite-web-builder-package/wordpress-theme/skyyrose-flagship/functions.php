<?php
/**
 * SkyyRose Flagship Theme Functions
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

defined('ABSPATH') || exit;

/* ═══════════════════════════════════════════
   THEME SETUP
   ═══════════════════════════════════════════ */

function skyyrose_setup() {
    add_theme_support('woocommerce');
    add_theme_support('wc-product-gallery-zoom');
    add_theme_support('wc-product-gallery-lightbox');
    add_theme_support('wc-product-gallery-slider');
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('html5', ['search-form', 'comment-form', 'gallery', 'caption']);

    register_nav_menus([
        'primary'    => 'Primary Navigation',
        'footer'     => 'Footer Navigation',
        'collection' => 'Collection Navigation',
    ]);
}
add_action('after_setup_theme', 'skyyrose_setup');

/* ═══════════════════════════════════════════
   ENQUEUE STYLES & SCRIPTS
   ═══════════════════════════════════════════ */

function skyyrose_enqueue_assets() {
    // Google Fonts
    wp_enqueue_style('skyyrose-fonts',
        'https://fonts.googleapis.com/css2?' . implode('&', [
            'family=Cinzel:wght@400;500;600;700;800;900',
            'family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400;1,500;1,600',
            'family=Bebas+Neue',
            'family=Space+Mono:wght@400;700',
            'family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400;1,700',
            'display=swap',
        ]),
        [], null
    );

    // Main theme stylesheet
    wp_enqueue_style('skyyrose-main',
        get_template_directory_uri() . '/assets/css/main.css',
        ['skyyrose-fonts'],
        filemtime(get_template_directory() . '/assets/css/main.css')
    );
}
add_action('wp_enqueue_scripts', 'skyyrose_enqueue_assets');

/* ═══════════════════════════════════════════
   WOOCOMMERCE INCLUDES
   ═══════════════════════════════════════════ */

require_once get_template_directory() . '/inc/wc-product-functions.php';

/* ═══════════════════════════════════════════
   WOOCOMMERCE OVERRIDES
   ═══════════════════════════════════════════ */

// Remove default WC wrapper
remove_action('woocommerce_before_main_content', 'woocommerce_output_content_wrapper', 10);
remove_action('woocommerce_after_main_content', 'woocommerce_output_content_wrapper_end', 10);

// Remove sidebar from product pages
function skyyrose_remove_sidebar() {
    if (is_product()) {
        remove_action('woocommerce_sidebar', 'woocommerce_get_sidebar', 10);
    }
}
add_action('wp', 'skyyrose_remove_sidebar');

// Custom add-to-cart button text
function skyyrose_add_to_cart_text($text, $product) {
    if ($product->get_stock_status() === 'onbackorder') {
        return 'PRE-ORDER';
    }
    return 'ADD TO BAG';
}
add_filter('woocommerce_product_single_add_to_cart_text', 'skyyrose_add_to_cart_text', 10, 2);

// Custom WC body classes
function skyyrose_wc_body_class($classes) {
    if (is_woocommerce() || is_cart() || is_checkout()) {
        $classes[] = 'skyyrose-wc';
    }
    return $classes;
}
add_filter('body_class', 'skyyrose_wc_body_class');

/* ═══════════════════════════════════════════
   AJAX ADD TO CART (support fragments)
   ═══════════════════════════════════════════ */

function skyyrose_cart_count_fragment($fragments) {
    $fragments['.cart-count-fragment'] = WC()->cart->get_cart_contents_count();
    return $fragments;
}
add_filter('woocommerce_add_to_cart_fragments', 'skyyrose_cart_count_fragment');

/* ═══════════════════════════════════════════
   PRELOAD CRITICAL ASSETS
   ═══════════════════════════════════════════ */

function skyyrose_preload_fonts() {
    if (!is_product()) return;
    echo '<link rel="preconnect" href="https://fonts.googleapis.com">' . "\n";
    echo '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>' . "\n";
}
add_action('wp_head', 'skyyrose_preload_fonts', 1);
