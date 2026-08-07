<?php
/**
 * Theme functions starter template.
 *
 * Follows WordPress.com Atomic best practices:
 * - Conditional asset loading
 * - Proper enqueue with dependencies
 * - Security headers
 * - WooCommerce support declaration
 *
 * @package theme-starter
 */

defined('ABSPATH') || exit;

/**
 * Theme setup — runs after theme is active.
 */
function theme_starter_setup(): void {
    // Add theme support
    add_theme_support('wp-block-styles');
    add_theme_support('responsive-embeds');
    add_theme_support('editor-styles');
    add_theme_support('html5', ['search-form', 'comment-form', 'comment-list', 'gallery', 'caption']);

    // WooCommerce support
    add_theme_support('woocommerce');
    add_theme_support('wc-product-gallery-zoom');
    add_theme_support('wc-product-gallery-lightbox');
    add_theme_support('wc-product-gallery-slider');

    // Navigation menus
    register_nav_menus([
        'primary'  => __('Primary Menu', 'theme-starter'),
        'footer'   => __('Footer Menu', 'theme-starter'),
    ]);
}
add_action('after_setup_theme', 'theme_starter_setup');

/**
 * Enqueue styles and scripts.
 */
function theme_starter_enqueue(): void {
    // Brand styles
    wp_enqueue_style(
        'brand-styles',
        get_template_directory_uri() . '/css/brand-variables.css',
        [],
        wp_get_theme()->get('Version')
    );

    // Main stylesheet
    wp_enqueue_style(
        'main-style',
        get_template_directory_uri() . '/css/style.css',
        ['brand-styles'],
        wp_get_theme()->get('Version')
    );
}
add_action('wp_enqueue_scripts', 'theme_starter_enqueue');

/**
 * Security headers.
 */
function theme_starter_security_headers(): void {
    header("X-Content-Type-Options: nosniff");
    header("X-Frame-Options: SAMEORIGIN");
    header("Referrer-Policy: strict-origin-when-cross-origin");
}
add_action('send_headers', 'theme_starter_security_headers');

// Hide WordPress version
remove_action('wp_head', 'wp_generator');
