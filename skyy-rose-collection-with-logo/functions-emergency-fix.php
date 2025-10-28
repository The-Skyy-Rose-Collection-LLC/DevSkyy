<?php
/**
 * Skyy Rose Collection Theme Functions - EMERGENCY FIX VERSION
 *
 * Error-resistant luxury fashion WordPress theme functions with comprehensive error handling
 *
 * @package Skyy_Rose_Collection
 * @version 1.0.1
 * @author DevSkyy WordPress Development Specialist
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Theme version constant
 */
if (!defined('SKYY_ROSE_COLLECTION_VERSION')) {
    define('SKYY_ROSE_COLLECTION_VERSION', '1.0.1');
}

/**
 * Error logging function
 */
if (!function_exists('skyy_rose_log_error')) {
    function skyy_rose_log_error($message, $context = '') {
        if (defined('WP_DEBUG') && WP_DEBUG) {
            error_log('Skyy Rose Collection Theme Error: ' . $message . ($context ? ' Context: ' . $context : ''));
        }
    }
}

/**
 * Safe function existence check
 */
if (!function_exists('skyy_rose_function_exists')) {
    function skyy_rose_function_exists($function_name) {
        return function_exists($function_name);
    }
}

/**
 * Theme setup with error handling
 */
if (!function_exists('skyy_rose_collection_setup')) {
    function skyy_rose_collection_setup() {
        try {
            // Make theme available for translation
            load_theme_textdomain('skyy-rose-collection', get_template_directory() . '/languages');

            // Add default posts and comments RSS feed links to head
            add_theme_support('automatic-feed-links');

            // Let WordPress manage the document title
            add_theme_support('title-tag');

            // Enable support for Post Thumbnails on posts and pages
            add_theme_support('post-thumbnails');

            // Set default thumbnail size for luxury product images
            set_post_thumbnail_size(600, 600, true);

            // Add custom image sizes for luxury eCommerce
            add_image_size('luxury-product-thumb', 300, 300, true);
            add_image_size('luxury-product-medium', 600, 600, true);
            add_image_size('luxury-product-large', 1200, 1200, true);
            add_image_size('luxury-hero', 1920, 800, true);

            // Register navigation menus
            register_nav_menus(array(
                'primary' => esc_html__('Primary Menu', 'skyy-rose-collection'),
                'footer' => esc_html__('Footer Menu', 'skyy-rose-collection'),
                'mobile' => esc_html__('Mobile Menu', 'skyy-rose-collection'),
            ));

            // Add theme support for WooCommerce (with existence check)
            if (class_exists('WooCommerce')) {
                add_theme_support('woocommerce');
                add_theme_support('wc-product-gallery-zoom');
                add_theme_support('wc-product-gallery-lightbox');
                add_theme_support('wc-product-gallery-slider');
            }

            // Add theme support for custom backgrounds and headers
            add_theme_support('custom-background', array(
                'default-color' => 'f8f6f0',
            ));

            add_theme_support('custom-header', array(
                'default-image' => get_template_directory_uri() . '/assets/images/header-bg.jpg',
                'width' => 1920,
                'height' => 1080,
                'flex-height' => true,
                'flex-width' => true,
            ));

            // Add support for HTML5 markup
            add_theme_support('html5', array(
                'search-form',
                'comment-form',
                'comment-list',
                'gallery',
                'caption',
                'style',
                'script'
            ));

            // Add support for editor styles
            add_theme_support('editor-styles');
            if (file_exists(get_template_directory() . '/assets/css/editor-style.css')) {
                add_editor_style('assets/css/editor-style.css');
            }

            // Add support for responsive embeds
            add_theme_support('responsive-embeds');

            // Add support for block styles
            add_theme_support('wp-block-styles');

            // Add support for wide alignment
            add_theme_support('align-wide');

        } catch (Exception $e) {
            skyy_rose_log_error('Theme setup failed: ' . $e->getMessage());
        }
    }
}
add_action('after_setup_theme', 'skyy_rose_collection_setup');

/**
 * Set the content width in pixels
 */
if (!function_exists('skyy_rose_collection_content_width')) {
    function skyy_rose_collection_content_width() {
        $GLOBALS['content_width'] = apply_filters('skyy_rose_collection_content_width', 1200);
    }
}
add_action('after_setup_theme', 'skyy_rose_collection_content_width', 0);

/**
 * Register widget areas with error handling
 */
if (!function_exists('skyy_rose_collection_widgets_init')) {
    function skyy_rose_collection_widgets_init() {
        try {
            register_sidebar(array(
                'name' => esc_html__('Primary Sidebar', 'skyy-rose-collection'),
                'id' => 'sidebar-1',
                'description' => esc_html__('Add widgets here.', 'skyy-rose-collection'),
                'before_widget' => '<section id="%1$s" class="widget %2$s">',
                'after_widget' => '</section>',
                'before_title' => '<h3 class="widget-title">',
                'after_title' => '</h3>',
            ));

            // Footer widget areas
            for ($i = 1; $i <= 4; $i++) {
                register_sidebar(array(
                    'name' => sprintf(esc_html__('Footer Widget Area %d', 'skyy-rose-collection'), $i),
                    'id' => 'footer-' . $i,
                    'description' => esc_html__('Add widgets here.', 'skyy-rose-collection'),
                    'before_widget' => '<div id="%1$s" class="widget %2$s">',
                    'after_widget' => '</div>',
                    'before_title' => '<h4 class="widget-title">',
                    'after_title' => '</h4>',
                ));
            }
        } catch (Exception $e) {
            skyy_rose_log_error('Widget registration failed: ' . $e->getMessage());
        }
    }
}
add_action('widgets_init', 'skyy_rose_collection_widgets_init');

/**
 * Enqueue scripts and styles with error handling
 */
if (!function_exists('skyy_rose_collection_scripts')) {
    function skyy_rose_collection_scripts() {
        try {
            // Enqueue Google Fonts
            wp_enqueue_style(
                'skyy-rose-collection-fonts',
                'https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,300;0,400;0,600;0,700;1,300;1,400&family=Inter:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=Dancing+Script:wght@400;500;600;700&display=swap',
                array(),
                null
            );

            // Enqueue main stylesheet
            wp_enqueue_style(
                'skyy-rose-collection-style',
                get_stylesheet_uri(),
                array('skyy-rose-collection-fonts'),
                SKYY_ROSE_COLLECTION_VERSION
            );

            // Enqueue main JavaScript file (with existence check)
            $js_file = get_template_directory() . '/assets/js/theme.js';
            if (file_exists($js_file)) {
                wp_enqueue_script(
                    'skyy-rose-collection-script',
                    get_template_directory_uri() . '/assets/js/theme.js',
                    array('jquery'),
                    SKYY_ROSE_COLLECTION_VERSION,
                    true
                );

                // Localize script for AJAX
                wp_localize_script('skyy-rose-collection-script', 'skyy_rose_ajax', array(
                    'ajax_url' => admin_url('admin-ajax.php'),
                    'nonce' => wp_create_nonce('skyy_rose_nonce'),
                    'theme_url' => get_template_directory_uri(),
                ));
            }

            // Enqueue comment reply script on single posts with comments open and threaded comments
            if (is_singular() && comments_open() && get_option('thread_comments')) {
                wp_enqueue_script('comment-reply');
            }

        } catch (Exception $e) {
            skyy_rose_log_error('Script enqueue failed: ' . $e->getMessage());
        }
    }
}
add_action('wp_enqueue_scripts', 'skyy_rose_collection_scripts');

/**
 * WooCommerce specific enqueues with error handling
 */
if (!function_exists('skyy_rose_collection_woocommerce_scripts')) {
    function skyy_rose_collection_woocommerce_scripts() {
        if (!class_exists('WooCommerce')) {
            return;
        }

        try {
            // Enqueue WooCommerce specific styles (with existence check)
            $wc_css_file = get_template_directory() . '/assets/css/woocommerce.css';
            if (file_exists($wc_css_file)) {
                wp_enqueue_style(
                    'skyy-rose-collection-woocommerce',
                    get_template_directory_uri() . '/assets/css/woocommerce.css',
                    array('skyy-rose-collection-style'),
                    SKYY_ROSE_COLLECTION_VERSION
                );
            }

            // Enqueue WooCommerce specific JavaScript (with existence check)
            $wc_js_file = get_template_directory() . '/assets/js/woocommerce.js';
            if (file_exists($wc_js_file)) {
                wp_enqueue_script(
                    'skyy-rose-collection-woocommerce-js',
                    get_template_directory_uri() . '/assets/js/woocommerce.js',
                    array('jquery', 'skyy-rose-collection-script'),
                    SKYY_ROSE_COLLECTION_VERSION,
                    true
                );
            }

        } catch (Exception $e) {
            skyy_rose_log_error('WooCommerce script enqueue failed: ' . $e->getMessage());
        }
    }
}
add_action('wp_enqueue_scripts', 'skyy_rose_collection_woocommerce_scripts');

/**
 * Custom excerpt length
 */
if (!function_exists('skyy_rose_collection_excerpt_length')) {
    function skyy_rose_collection_excerpt_length($length) {
        if (function_exists('is_shop') && (is_shop() || is_product_category() || is_product_tag())) {
            return 20;
        }
        return 25;
    }
}
add_filter('excerpt_length', 'skyy_rose_collection_excerpt_length', 999);

/**
 * Custom excerpt more string
 */
if (!function_exists('skyy_rose_collection_excerpt_more')) {
    function skyy_rose_collection_excerpt_more($more) {
        if (is_admin()) {
            return $more;
        }

        return sprintf(
            '&hellip; <a href="%1$s" class="read-more luxury-accent">%2$s</a>',
            esc_url(get_permalink()),
            esc_html__('Read More', 'skyy-rose-collection')
        );
    }
}
add_filter('excerpt_more', 'skyy_rose_collection_excerpt_more');

/**
 * Safe WooCommerce function calls
 */
if (!function_exists('skyy_rose_safe_wc_function')) {
    function skyy_rose_safe_wc_function($function_name, $args = array(), $default = null) {
        if (class_exists('WooCommerce') && function_exists($function_name)) {
            try {
                return call_user_func_array($function_name, $args);
            } catch (Exception $e) {
                skyy_rose_log_error('WooCommerce function call failed: ' . $function_name . ' - ' . $e->getMessage());
                return $default;
            }
        }
        return $default;
    }
}

/**
 * Theme activation hook with error handling
 */
if (!function_exists('skyy_rose_collection_activation')) {
    function skyy_rose_collection_activation() {
        try {
            // Flush rewrite rules
            flush_rewrite_rules();

            // Set default theme options
            if (!get_theme_mod('custom_logo')) {
                // Set default customizer values if needed
            }

        } catch (Exception $e) {
            skyy_rose_log_error('Theme activation failed: ' . $e->getMessage());
        }
    }
}
add_action('after_switch_theme', 'skyy_rose_collection_activation');

/**
 * Theme deactivation hook
 */
if (!function_exists('skyy_rose_collection_deactivation')) {
    function skyy_rose_collection_deactivation() {
        try {
            flush_rewrite_rules();
        } catch (Exception $e) {
            skyy_rose_log_error('Theme deactivation failed: ' . $e->getMessage());
        }
    }
}
add_action('switch_theme', 'skyy_rose_collection_deactivation');
