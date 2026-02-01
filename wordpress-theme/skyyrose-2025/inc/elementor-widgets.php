<?php
/**
 * Elementor Custom Widgets Loader
 * Registers all SkyyRose custom Elementor widgets
 *
 * @package SkyyRose_2025
 * @version 2.0.0
 */

if (!defined('ABSPATH')) exit;

/**
 * Check if Elementor is installed and activated
 */
if (!did_action('elementor/loaded')) {
    return;
}

/**
 * Register SkyyRose widgets category
 */
function skyyrose_add_elementor_widget_categories($elements_manager) {
    $elements_manager->add_category(
        'skyyrose',
        [
            'title' => esc_html__('SkyyRose Luxury', 'skyyrose'),
            'icon' => 'fa fa-gem',
        ]
    );
}
add_action('elementor/elements/categories_registered', 'skyyrose_add_elementor_widget_categories');

/**
 * Register custom widgets
 */
function skyyrose_register_elementor_widgets($widgets_manager) {
    // Immersive Scene Widget
    require_once(get_template_directory() . '/elementor-widgets/immersive-scene.php');
    $widgets_manager->register(new \SkyyRose\Elementor\Immersive_Scene_Widget());

    // Product Hotspot Widget
    require_once(get_template_directory() . '/elementor-widgets/product-hotspot.php');
    $widgets_manager->register(new \SkyyRose\Elementor\Product_Hotspot_Widget());

    // Collection Card Widget
    require_once(get_template_directory() . '/elementor-widgets/collection-card.php');
    $widgets_manager->register(new \SkyyRose\Elementor\Collection_Card_Widget());

    // Pre-Order Form Widget
    require_once(get_template_directory() . '/elementor-widgets/pre-order-form.php');
    $widgets_manager->register(new \SkyyRose\Elementor\PreOrder_Form_Widget());
}
add_action('elementor/widgets/register', 'skyyrose_register_elementor_widgets');

/**
 * Enqueue Elementor widget scripts and styles
 */
function skyyrose_elementor_widget_scripts() {
    // Three.js for immersive scenes
    wp_register_script(
        'threejs',
        'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js',
        [],
        '0.160.0',
        true
    );

    // Babylon.js for physics
    wp_register_script(
        'babylonjs',
        'https://cdn.babylonjs.com/babylon.js',
        [],
        '6.0.0',
        true
    );

    // GSAP with ScrollTrigger
    wp_register_script(
        'gsap',
        'https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js',
        [],
        '3.12.5',
        true
    );

    wp_register_script(
        'gsap-scrolltrigger',
        'https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/ScrollTrigger.min.js',
        ['gsap'],
        '3.12.5',
        true
    );

    // Custom scene configurations
    wp_enqueue_script(
        'skyyrose-three-scenes',
        get_template_directory_uri() . '/assets/js/three-scenes/scenes.js',
        ['threejs', 'babylonjs', 'gsap', 'gsap-scrolltrigger'],
        SKYYROSE_VERSION,
        true
    );

    // Pass theme customizer values to JavaScript
    wp_localize_script('skyyrose-three-scenes', 'skyyroseBrand', [
        'colors' => [
            'blackRose' => get_theme_mod('skyyrose_color_black_rose', '#8B0000'),
            'loveHurts' => get_theme_mod('skyyrose_color_love_hurts', '#B76E79'),
            'signature' => get_theme_mod('skyyrose_color_signature', '#D4AF37'),
        ],
        'brandName' => get_theme_mod('skyyrose_brand_name', 'SkyyRose'),
        'enableImmersive' => get_theme_mod('skyyrose_enable_immersive', true),
    ]);

    // Widget styles
    wp_enqueue_style(
        'skyyrose-elementor-widgets',
        get_template_directory_uri() . '/assets/css/elementor-widgets.css',
        [],
        SKYYROSE_VERSION
    );
}
add_action('elementor/frontend/after_register_scripts', 'skyyrose_elementor_widget_scripts');

/**
 * Add Elementor support for custom post types
 */
function skyyrose_add_elementor_support() {
    // Add Elementor support to pages
    add_post_type_support('page', 'elementor');

    // Add Elementor support to WooCommerce products if needed
    if (class_exists('WooCommerce')) {
        add_post_type_support('product', 'elementor');
    }
}
add_action('init', 'skyyrose_add_elementor_support');

/**
 * Register Elementor canvas template
 */
function skyyrose_register_elementor_locations($elementor_theme_manager) {
    $elementor_theme_manager->register_location('header');
    $elementor_theme_manager->register_location('footer');
}
add_action('elementor/theme/register_locations', 'skyyrose_register_elementor_locations');
