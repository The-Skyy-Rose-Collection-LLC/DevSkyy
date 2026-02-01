<?php
/**
 * Performance Optimization
 * Asset loading, caching, and speed improvements
 *
 * @package SkyyRose_2025
 * @version 2.0.0
 */

if (!defined('ABSPATH')) exit;

/**
 * Dequeue unnecessary scripts and styles
 */
function skyyrose_dequeue_unnecessary_assets() {
    // Remove block library CSS if not using Gutenberg blocks
    if (!is_admin()) {
        wp_dequeue_style('wp-block-library');
        wp_dequeue_style('wp-block-library-theme');
        wp_dequeue_style('global-styles');
    }

    // Remove emoji detection script
    remove_action('wp_head', 'print_emoji_detection_script', 7);
    remove_action('wp_print_styles', 'print_emoji_styles');
}
add_action('wp_enqueue_scripts', 'skyyrose_dequeue_unnecessary_assets', 100);

/**
 * Defer non-critical JavaScript
 */
function skyyrose_defer_scripts($tag, $handle) {
    // Scripts that should NOT be deferred
    $skip = [
        'jquery',
        'jquery-core',
        'jquery-migrate',
        'elementor-frontend',
        'elementor-webpack-runtime',
    ];

    if (in_array($handle, $skip)) {
        return $tag;
    }

    return str_replace(' src', ' defer src', $tag);
}
add_filter('script_loader_tag', 'skyyrose_defer_scripts', 10, 2);

/**
 * Preload critical assets
 */
function skyyrose_preload_assets() {
    // Preload fonts
    echo '<link rel="preload" href="' . get_template_directory_uri() . '/assets/fonts/PlayfairDisplay-Bold.woff2" as="font" type="font/woff2" crossorigin>';

    // Preconnect to CDNs
    echo '<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>';
    echo '<link rel="dns-prefetch" href="https://cdn.babylonjs.com">';
}
add_action('wp_head', 'skyyrose_preload_assets', 1);

/**
 * Lazy load images
 */
function skyyrose_add_lazy_loading($content) {
    if (is_admin() || is_feed()) {
        return $content;
    }

    // Add loading="lazy" to images
    $content = preg_replace('/<img(.*?)>/i', '<img$1 loading="lazy">', $content);

    return $content;
}
add_filter('the_content', 'skyyrose_add_lazy_loading');
add_filter('post_thumbnail_html', 'skyyrose_add_lazy_loading');

/**
 * Optimize WooCommerce scripts
 */
function skyyrose_optimize_woocommerce_scripts() {
    if (!is_woocommerce() && !is_cart() && !is_checkout() && !is_account_page()) {
        // Dequeue WooCommerce scripts on non-shop pages
        wp_dequeue_script('wc-cart-fragments');
        wp_dequeue_script('woocommerce');
        wp_dequeue_script('wc-add-to-cart');

        wp_dequeue_style('woocommerce-general');
        wp_dequeue_style('woocommerce-layout');
        wp_dequeue_style('woocommerce-smallscreen');
    }
}
add_action('wp_enqueue_scripts', 'skyyrose_optimize_woocommerce_scripts', 99);

/**
 * Disable WordPress heartbeat on frontend
 */
function skyyrose_disable_heartbeat() {
    if (!is_admin()) {
        wp_deregister_script('heartbeat');
    }
}
add_action('init', 'skyyrose_disable_heartbeat', 1);

/**
 * Optimize database queries
 */
function skyyrose_limit_post_revisions() {
    if (!defined('WP_POST_REVISIONS')) {
        define('WP_POST_REVISIONS', 3);
    }
}
add_action('init', 'skyyrose_limit_post_revisions');

/**
 * Add cache headers for static assets
 */
function skyyrose_add_cache_headers() {
    if (!is_admin()) {
        header('Cache-Control: public, max-age=31536000');
    }
}
add_action('send_headers', 'skyyrose_add_cache_headers');

/**
 * WebP image support
 */
function skyyrose_webp_support($mimes) {
    $mimes['webp'] = 'image/webp';
    return $mimes;
}
add_filter('upload_mimes', 'skyyrose_webp_support');
