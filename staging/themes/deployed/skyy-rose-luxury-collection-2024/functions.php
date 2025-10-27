<?php
function skyy_rose_luxury_collection_2024_setup() {
    add_theme_support('post-thumbnails');
    add_theme_support('title-tag');
    add_theme_support('custom-logo');
    add_theme_support('woocommerce');
    
    register_nav_menus(array(
        'primary' => __('Primary Menu', 'skyy-rose-luxury-collection-2024'),
    ));
}
add_action('after_setup_theme', 'skyy_rose_luxury_collection_2024_setup');

function skyy_rose_luxury_collection_2024_scripts() {
    wp_enqueue_style('skyy-rose-luxury-collection-2024-style', get_stylesheet_uri(), array(), '1.0.0');
}
add_action('wp_enqueue_scripts', 'skyy_rose_luxury_collection_2024_scripts');
?>
