<?php
/**
 * Skyy Rose Luxury Fixed 2024 Functions
 * FIXED Luxury fashion theme for Skyy Rose Collection
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Theme setup
function skyy_rose_luxury_fixed_2024_setup() {
    // Add theme support
    add_theme_support('post-thumbnails');
    add_theme_support('title-tag');
    add_theme_support('custom-logo', array(
        'height' => 120,
        'width' => 400,
        'flex-height' => true,
        'flex-width' => true,
    ));
    add_theme_support('html5', array(
        'search-form',
        'comment-form',
        'comment-list',
        'gallery',
        'caption',
        'style',
        'script',
    ));

    // WooCommerce support for luxury fashion
    add_theme_support('woocommerce');
    add_theme_support('wc-product-gallery-zoom');
    add_theme_support('wc-product-gallery-lightbox');
    add_theme_support('wc-product-gallery-slider');

    // Register navigation menus
    register_nav_menus(array(
        'primary' => __('Primary Menu', 'skyy-rose-luxury-fixed-2024'),
        'footer' => __('Footer Menu', 'skyy-rose-luxury-fixed-2024'),
    ));

    // Add custom image sizes for luxury products
    add_image_size('luxury-product', 400, 500, true);
    add_image_size('luxury-hero', 1200, 600, true);
    add_image_size('luxury-thumbnail', 300, 300, true);

    // Add editor styles
    add_theme_support('editor-styles');
    add_editor_style('style.css');

    // Add responsive embeds
    add_theme_support('responsive-embeds');

    // Add wide alignment
    add_theme_support('align-wide');
}
add_action('after_setup_theme', 'skyy_rose_luxury_fixed_2024_setup');

// Enqueue styles and scripts
function skyy_rose_luxury_fixed_2024_scripts() {
    // Main stylesheet
    wp_enqueue_style('skyy-rose-luxury-fixed-2024-style', get_stylesheet_uri(), array(), '1.1.0');

    // Google Fonts with proper loading
    wp_enqueue_style('skyy-rose-luxury-fixed-2024-fonts',
        'https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,300;0,400;0,600;0,700;1,300;1,400&family=Source+Sans+Pro:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&display=swap',
        array(), null
    );

    // Add font-display: swap for better performance
    wp_add_inline_style('skyy-rose-luxury-fixed-2024-fonts', '
        @font-face {
            font-family: "Playfair Display";
            font-display: swap;
        }
        @font-face {
            font-family: "Source Sans Pro";
            font-display: swap;
        }
    ');

    // Custom JavaScript for luxury interactions
    wp_enqueue_script('skyy-rose-luxury-fixed-2024-script',
        get_template_directory_uri() . '/js/luxury-interactions.js',
        array('jquery'), '1.1.0', true
    );

    // Localize script for AJAX
    wp_localize_script('skyy-rose-luxury-fixed-2024-script', 'luxury_ajax', array(
        'ajax_url' => admin_url('admin-ajax.php'),
        'nonce' => wp_create_nonce('luxury_nonce')
    ));
}
add_action('wp_enqueue_scripts', 'skyy_rose_luxury_fixed_2024_scripts');

// Customize excerpt length for luxury content
function skyy_rose_luxury_fixed_2024_excerpt_length($length) {
    return 25;
}
add_filter('excerpt_length', 'skyy_rose_luxury_fixed_2024_excerpt_length');

// Custom excerpt more text
function skyy_rose_luxury_fixed_2024_excerpt_more($more) {
    return '...';
}
add_filter('excerpt_more', 'skyy_rose_luxury_fixed_2024_excerpt_more');

// Add luxury customizer options
function skyy_rose_luxury_fixed_2024_customize_register($wp_customize) {
    // Luxury Colors Section
    $wp_customize->add_section('luxury_colors', array(
        'title' => __('Luxury Colors', 'skyy-rose-luxury-fixed-2024'),
        'priority' => 30,
        'description' => __('Customize the luxury color palette for your Skyy Rose Collection theme.', 'skyy-rose-luxury-fixed-2024'),
    ));

    // Primary Color
    $wp_customize->add_setting('primary_color', array(
        'default' => '#1a1a1a',
        'sanitize_callback' => 'sanitize_hex_color',
        'transport' => 'postMessage',
    ));

    $wp_customize->add_control(new WP_Customize_Color_Control($wp_customize, 'primary_color', array(
        'label' => __('Primary Color', 'skyy-rose-luxury-fixed-2024'),
        'section' => 'luxury_colors',
        'description' => __('Main brand color for headings and accents.', 'skyy-rose-luxury-fixed-2024'),
    )));

    // Secondary Color
    $wp_customize->add_setting('secondary_color', array(
        'default' => '#d4af37',
        'sanitize_callback' => 'sanitize_hex_color',
        'transport' => 'postMessage',
    ));

    $wp_customize->add_control(new WP_Customize_Color_Control($wp_customize, 'secondary_color', array(
        'label' => __('Secondary Color (Gold)', 'skyy-rose-luxury-fixed-2024'),
        'section' => 'luxury_colors',
        'description' => __('Luxury gold accent color.', 'skyy-rose-luxury-fixed-2024'),
    )));

    // Accent Color
    $wp_customize->add_setting('accent_color', array(
        'default' => '#8b7355',
        'sanitize_callback' => 'sanitize_hex_color',
        'transport' => 'postMessage',
    ));

    $wp_customize->add_control(new WP_Customize_Color_Control($wp_customize, 'accent_color', array(
        'label' => __('Accent Color', 'skyy-rose-luxury-fixed-2024'),
        'section' => 'luxury_colors',
        'description' => __('Complementary accent color.', 'skyy-rose-luxury-fixed-2024'),
    )));
}
add_action('customize_register', 'skyy_rose_luxury_fixed_2024_customize_register');

// Output customizer CSS
function skyy_rose_luxury_fixed_2024_customizer_css() {
    $primary_color = get_theme_mod('primary_color', '#1a1a1a');
    $secondary_color = get_theme_mod('secondary_color', '#d4af37');
    $accent_color = get_theme_mod('accent_color', '#8b7355');

    ?>
    <style type="text/css">
        :root {
            --primary-color: <?php echo esc_attr($primary_color); ?>;
            --secondary-color: <?php echo esc_attr($secondary_color); ?>;
            --accent-color: <?php echo esc_attr($accent_color); ?>;
        }
    </style>
    <?php
}
add_action('wp_head', 'skyy_rose_luxury_fixed_2024_customizer_css');

// Skyy Rose Collection specific functions
function skyy_rose_get_featured_products($limit = 4) {
    if (!class_exists('WooCommerce')) {
        return array();
    }

    $args = array(
        'post_type' => 'product',
        'posts_per_page' => $limit,
        'meta_query' => array(
            array(
                'key' => '_featured',
                'value' => 'yes'
            )
        )
    );

    return get_posts($args);
}

// Add luxury schema markup
function skyy_rose_luxury_fixed_2024_add_schema_markup() {
    if (is_single() && get_post_type() === 'product') {
        echo '<script type="application/ld+json">';
        echo json_encode(array(
            '@context' => 'https://schema.org/',
            '@type' => 'Product',
            'name' => get_the_title(),
            'description' => get_the_excerpt(),
            'brand' => array(
                '@type' => 'Brand',
                'name' => 'Skyy Rose Collection'
            ),
            'offers' => array(
                '@type' => 'Offer',
                'availability' => 'https://schema.org/InStock',
                'priceCurrency' => 'USD'
            )
        ));
        echo '</script>';
    }
}
add_action('wp_head', 'skyy_rose_luxury_fixed_2024_add_schema_markup');

// Add fallback menu
function skyy_rose_luxury_fixed_2024_fallback_menu() {
    echo '<div class="menu-fallback">';
    echo '<a href="' . esc_url(home_url('/')) . '">Home</a>';
    echo '<a href="' . esc_url(home_url('/shop/')) . '">Shop</a>';
    echo '<a href="' . esc_url(home_url('/about/')) . '">About</a>';
    echo '<a href="' . esc_url(home_url('/contact/')) . '">Contact</a>';
    echo '</div>';
}

// Enhanced navigation walker for luxury styling
// Custom walker class removed for compatibility
}

// Add body classes for luxury styling
function skyy_rose_luxury_fixed_2024_body_classes($classes) {
    $classes[] = 'luxury-theme';
    $classes[] = 'skyy-rose-collection';

    if (is_woocommerce() || is_cart() || is_checkout()) {
        $classes[] = 'luxury-shop';
    }

    return $classes;
}
add_filter('body_class', 'skyy_rose_luxury_fixed_2024_body_classes');

// Add theme support for Gutenberg
function skyy_rose_luxury_fixed_2024_gutenberg_support() {
    // Add support for editor color palette
    add_theme_support('editor-color-palette', array(
        array(
            'name' => __('Primary Black', 'skyy-rose-luxury-fixed-2024'),
            'slug' => 'primary-black',
            'color' => '#1a1a1a',
        ),
        array(
            'name' => __('Luxury Gold', 'skyy-rose-luxury-fixed-2024'),
            'slug' => 'luxury-gold',
            'color' => '#d4af37',
        ),
        array(
            'name' => __('Warm Brown', 'skyy-rose-luxury-fixed-2024'),
            'slug' => 'warm-brown',
            'color' => '#8b7355',
        ),
    ));

    // Add support for custom font sizes
    add_theme_support('editor-font-sizes', array(
        array(
            'name' => __('Small', 'skyy-rose-luxury-fixed-2024'),
            'size' => 14,
            'slug' => 'small'
        ),
        array(
            'name' => __('Regular', 'skyy-rose-luxury-fixed-2024'),
            'size' => 18,
            'slug' => 'regular'
        ),
        array(
            'name' => __('Large', 'skyy-rose-luxury-fixed-2024'),
            'size' => 24,
            'slug' => 'large'
        ),
        array(
            'name' => __('Extra Large', 'skyy-rose-luxury-fixed-2024'),
            'size' => 32,
            'slug' => 'extra-large'
        )
    ));
}
add_action('after_setup_theme', 'skyy_rose_luxury_fixed_2024_gutenberg_support');
?>
