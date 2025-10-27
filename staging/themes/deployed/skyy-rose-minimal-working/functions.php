<?php
function skyy_rose_minimal_setup() {
    add_theme_support('post-thumbnails');
    add_theme_support('title-tag');
    add_theme_support('custom-logo');
}
add_action('after_setup_theme', 'skyy_rose_minimal_setup');

function skyy_rose_minimal_scripts() {
    wp_enqueue_style('skyy-rose-minimal-style', get_stylesheet_uri(), array(), '1.0.0');
}
add_action('wp_enqueue_scripts', 'skyy_rose_minimal_scripts');
?>
