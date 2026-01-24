<?php
/**
 * Theme Customizer
 *
 * @package SkyyRose
 */

defined('ABSPATH') || exit;

/**
 * Register customizer settings
 */
function skyyrose_customize_register(WP_Customize_Manager $wp_customize): void {
    // SkyyRose Brand Panel
    $wp_customize->add_panel('skyyrose_brand', [
        'title'       => __('SkyyRose Brand', 'skyyrose'),
        'description' => __('Customize your SkyyRose brand settings', 'skyyrose'),
        'priority'    => 30,
    ]);

    // Hero Section
    $wp_customize->add_section('skyyrose_hero', [
        'title'    => __('Hero Section', 'skyyrose'),
        'panel'    => 'skyyrose_brand',
        'priority' => 10,
    ]);

    $wp_customize->add_setting('skyyrose_hero_video', [
        'default'           => '',
        'sanitize_callback' => 'esc_url_raw',
    ]);

    $wp_customize->add_control('skyyrose_hero_video', [
        'label'       => __('Hero Video URL', 'skyyrose'),
        'description' => __('URL to the hero background video (MP4)', 'skyyrose'),
        'section'     => 'skyyrose_hero',
        'type'        => 'url',
    ]);

    $wp_customize->add_setting('skyyrose_hero_tagline', [
        'default'           => 'Where Love Meets Luxury',
        'sanitize_callback' => 'sanitize_text_field',
    ]);

    $wp_customize->add_control('skyyrose_hero_tagline', [
        'label'   => __('Hero Tagline', 'skyyrose'),
        'section' => 'skyyrose_hero',
        'type'    => 'text',
    ]);

    // Social Links Section
    $wp_customize->add_section('skyyrose_social', [
        'title'    => __('Social Links', 'skyyrose'),
        'panel'    => 'skyyrose_brand',
        'priority' => 20,
    ]);

    $social_networks = ['instagram', 'tiktok', 'pinterest', 'facebook', 'twitter'];

    foreach ($social_networks as $network) {
        $wp_customize->add_setting("skyyrose_social_{$network}", [
            'default'           => '',
            'sanitize_callback' => 'esc_url_raw',
        ]);

        $wp_customize->add_control("skyyrose_social_{$network}", [
            'label'   => ucfirst($network) . ' URL',
            'section' => 'skyyrose_social',
            'type'    => 'url',
        ]);
    }

    // Pre-order Section
    $wp_customize->add_section('skyyrose_preorder', [
        'title'    => __('Pre-Order Settings', 'skyyrose'),
        'panel'    => 'skyyrose_brand',
        'priority' => 30,
    ]);

    $wp_customize->add_setting('skyyrose_preorder_klaviyo_list', [
        'default'           => '',
        'sanitize_callback' => 'sanitize_text_field',
    ]);

    $wp_customize->add_control('skyyrose_preorder_klaviyo_list', [
        'label'       => __('Klaviyo Early Access List ID', 'skyyrose'),
        'description' => __('List ID for early access signups', 'skyyrose'),
        'section'     => 'skyyrose_preorder',
        'type'        => 'text',
    ]);

    $wp_customize->add_setting('skyyrose_preorder_cta_text', [
        'default'           => 'Join the Waitlist',
        'sanitize_callback' => 'sanitize_text_field',
    ]);

    $wp_customize->add_control('skyyrose_preorder_cta_text', [
        'label'   => __('Pre-Order CTA Text', 'skyyrose'),
        'section' => 'skyyrose_preorder',
        'type'    => 'text',
    ]);

    // Newsletter Section
    $wp_customize->add_section('skyyrose_newsletter', [
        'title'    => __('Newsletter', 'skyyrose'),
        'panel'    => 'skyyrose_brand',
        'priority' => 40,
    ]);

    $wp_customize->add_setting('skyyrose_newsletter_heading', [
        'default'           => 'Join the Rose Garden',
        'sanitize_callback' => 'sanitize_text_field',
    ]);

    $wp_customize->add_control('skyyrose_newsletter_heading', [
        'label'   => __('Newsletter Heading', 'skyyrose'),
        'section' => 'skyyrose_newsletter',
        'type'    => 'text',
    ]);

    $wp_customize->add_setting('skyyrose_newsletter_description', [
        'default'           => 'Be the first to know about new collections, exclusive offers, and behind-the-scenes content.',
        'sanitize_callback' => 'sanitize_textarea_field',
    ]);

    $wp_customize->add_control('skyyrose_newsletter_description', [
        'label'   => __('Newsletter Description', 'skyyrose'),
        'section' => 'skyyrose_newsletter',
        'type'    => 'textarea',
    ]);

    $wp_customize->add_setting('skyyrose_klaviyo_list_id', [
        'default'           => '',
        'sanitize_callback' => 'sanitize_text_field',
    ]);

    $wp_customize->add_control('skyyrose_klaviyo_list_id', [
        'label'       => __('Klaviyo Newsletter List ID', 'skyyrose'),
        'description' => __('Enter your Klaviyo list ID for the footer newsletter signup', 'skyyrose'),
        'section'     => 'skyyrose_newsletter',
        'type'        => 'text',
    ]);

    // Footer Settings Section
    $wp_customize->add_section('skyyrose_footer', [
        'title'    => __('Footer Settings', 'skyyrose'),
        'panel'    => 'skyyrose_brand',
        'priority' => 50,
    ]);

    $wp_customize->add_setting('skyyrose_footer_tagline', [
        'default'           => 'Where Love Meets Luxury.',
        'sanitize_callback' => 'sanitize_text_field',
    ]);

    $wp_customize->add_control('skyyrose_footer_tagline', [
        'label'   => __('Footer Tagline', 'skyyrose'),
        'section' => 'skyyrose_footer',
        'type'    => 'text',
    ]);

    $wp_customize->add_setting('skyyrose_footer_location', [
        'default'           => 'Oakland, California',
        'sanitize_callback' => 'sanitize_text_field',
    ]);

    $wp_customize->add_control('skyyrose_footer_location', [
        'label'   => __('Footer Location', 'skyyrose'),
        'section' => 'skyyrose_footer',
        'type'    => 'text',
    ]);
}
add_action('customize_register', 'skyyrose_customize_register');

/**
 * Binds JS handlers to make Theme Customizer preview reload changes asynchronously.
 */
function skyyrose_customize_preview_js(): void {
    wp_enqueue_script(
        'skyyrose-customizer',
        SKYYROSE_URI . '/assets/js/customizer.js',
        ['customize-preview'],
        SKYYROSE_VERSION,
        true
    );
}
add_action('customize_preview_init', 'skyyrose_customize_preview_js');
