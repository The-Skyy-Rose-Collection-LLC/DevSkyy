<?php
/**
 * SkyyRose Theme Customizer
 * Makes brand colors, fonts, and logos easily customizable
 *
 * @package SkyyRose_2025
 * @version 2.0.0
 */

if (!defined('ABSPATH')) exit;

/**
 * Register customizer settings
 */
function skyyrose_customize_register($wp_customize) {

    // ===== BRAND IDENTITY SECTION =====
    $wp_customize->add_section('skyyrose_brand_identity', array(
        'title'    => __('Brand Identity', 'skyyrose'),
        'priority' => 30,
    ));

    // Brand Name
    $wp_customize->add_setting('skyyrose_brand_name', array(
        'default'           => 'SkyyRose',
        'sanitize_callback' => 'sanitize_text_field',
    ));
    $wp_customize->add_control('skyyrose_brand_name', array(
        'label'    => __('Brand Name', 'skyyrose'),
        'section'  => 'skyyrose_brand_identity',
        'type'     => 'text',
    ));

    // Brand Tagline
    $wp_customize->add_setting('skyyrose_brand_tagline', array(
        'default'           => 'Where Love Meets Luxury',
        'sanitize_callback' => 'sanitize_text_field',
    ));
    $wp_customize->add_control('skyyrose_brand_tagline', array(
        'label'    => __('Brand Tagline', 'skyyrose'),
        'section'  => 'skyyrose_brand_identity',
        'type'     => 'text',
    ));

    // Brand Origin/Location
    $wp_customize->add_setting('skyyrose_brand_origin', array(
        'default'           => 'Oakland, California',
        'sanitize_callback' => 'sanitize_text_field',
    ));
    $wp_customize->add_control('skyyrose_brand_origin', array(
        'label'    => __('Brand Origin/Location', 'skyyrose'),
        'section'  => 'skyyrose_brand_identity',
        'type'     => 'text',
    ));

    // ===== BRAND COLORS SECTION =====
    $wp_customize->add_section('skyyrose_brand_colors', array(
        'title'    => __('Brand Colors', 'skyyrose'),
        'priority' => 31,
    ));

    // Collection Colors
    $colors = array(
        'black_rose'   => array('label' => 'Black Rose Collection', 'default' => '#8B0000'),
        'black_rose_glow' => array('label' => 'Black Rose Glow', 'default' => '#ff0000'),
        'love_hurts'   => array('label' => 'Love Hurts Collection', 'default' => '#B76E79'),
        'love_hurts_light' => array('label' => 'Love Hurts Light', 'default' => '#ffb6c1'),
        'signature'    => array('label' => 'Signature Collection', 'default' => '#D4AF37'),
        'signature_glow' => array('label' => 'Signature Glow', 'default' => '#ffd700'),
        'bg_dark'      => array('label' => 'Background Dark', 'default' => '#030303'),
        'bg_deep'      => array('label' => 'Background Deep', 'default' => '#000000'),
    );

    foreach ($colors as $key => $color) {
        $wp_customize->add_setting("skyyrose_color_{$key}", array(
            'default'           => $color['default'],
            'sanitize_callback' => 'sanitize_hex_color',
        ));
        $wp_customize->add_control(new WP_Customize_Color_Control($wp_customize, "skyyrose_color_{$key}", array(
            'label'    => __($color['label'], 'skyyrose'),
            'section'  => 'skyyrose_brand_colors',
        )));
    }

    // ===== TYPOGRAPHY SECTION =====
    $wp_customize->add_section('skyyrose_typography', array(
        'title'    => __('Typography', 'skyyrose'),
        'priority' => 32,
    ));

    // Heading Font
    $wp_customize->add_setting('skyyrose_heading_font', array(
        'default'           => 'Playfair Display',
        'sanitize_callback' => 'sanitize_text_field',
    ));
    $wp_customize->add_control('skyyrose_heading_font', array(
        'label'    => __('Heading Font', 'skyyrose'),
        'section'  => 'skyyrose_typography',
        'type'     => 'select',
        'choices'  => array(
            'Playfair Display' => 'Playfair Display (Luxury Serif)',
            'Cormorant Garamond' => 'Cormorant Garamond (Editorial)',
            'Bodoni Moda' => 'Bodoni Moda (Fashion)',
            'Libre Baskerville' => 'Libre Baskerville (Classic)',
        ),
    ));

    // Body Font
    $wp_customize->add_setting('skyyrose_body_font', array(
        'default'           => 'Inter',
        'sanitize_callback' => 'sanitize_text_field',
    ));
    $wp_customize->add_control('skyyrose_body_font', array(
        'label'    => __('Body Font', 'skyyrose'),
        'section'  => 'skyyrose_typography',
        'type'     => 'select',
        'choices'  => array(
            'Inter' => 'Inter (Modern Sans)',
            'Montserrat' => 'Montserrat (Clean)',
            'Work Sans' => 'Work Sans (Professional)',
            'Raleway' => 'Raleway (Elegant)',
        ),
    ));

    // ===== LAYOUT OPTIONS SECTION =====
    $wp_customize->add_section('skyyrose_layout', array(
        'title'    => __('Layout Options', 'skyyrose'),
        'priority' => 33,
    ));

    // Enable Immersive Experiences
    $wp_customize->add_setting('skyyrose_enable_immersive', array(
        'default'           => true,
        'sanitize_callback' => 'rest_sanitize_boolean',
    ));
    $wp_customize->add_control('skyyrose_enable_immersive', array(
        'label'    => __('Enable 3D Immersive Experiences', 'skyyrose'),
        'section'  => 'skyyrose_layout',
        'type'     => 'checkbox',
    ));

    // Enable Catalog Split View
    $wp_customize->add_setting('skyyrose_catalog_split_view', array(
        'default'           => true,
        'sanitize_callback' => 'rest_sanitize_boolean',
    ));
    $wp_customize->add_control('skyyrose_catalog_split_view', array(
        'label'    => __('Enable Hybrid Split View Catalogs', 'skyyrose'),
        'section'  => 'skyyrose_layout',
        'type'     => 'checkbox',
    ));

    // Homepage Hero Style
    $wp_customize->add_setting('skyyrose_hero_style', array(
        'default'           => 'video',
        'sanitize_callback' => 'sanitize_text_field',
    ));
    $wp_customize->add_control('skyyrose_hero_style', array(
        'label'    => __('Homepage Hero Style', 'skyyrose'),
        'section'  => 'skyyrose_layout',
        'type'     => 'select',
        'choices'  => array(
            'video'     => 'Video Background',
            'animation' => '3D Animation',
            'image'     => 'Static Image',
        ),
    ));

    // ===== SOCIAL MEDIA SECTION =====
    $wp_customize->add_section('skyyrose_social', array(
        'title'    => __('Social Media', 'skyyrose'),
        'priority' => 34,
    ));

    $social_networks = array(
        'instagram' => 'Instagram',
        'tiktok'    => 'TikTok',
        'twitter'   => 'Twitter/X',
        'pinterest' => 'Pinterest',
    );

    foreach ($social_networks as $key => $label) {
        $wp_customize->add_setting("skyyrose_social_{$key}", array(
            'default'           => '',
            'sanitize_callback' => 'esc_url_raw',
        ));
        $wp_customize->add_control("skyyrose_social_{$key}", array(
            'label'    => __("{$label} URL", 'skyyrose'),
            'section'  => 'skyyrose_social',
            'type'     => 'url',
        ));
    }

    // ===== PRE-ORDER SETTINGS =====
    $wp_customize->add_section('skyyrose_preorder', array(
        'title'    => __('Pre-Order Settings', 'skyyrose'),
        'priority' => 35,
    ));

    // Pre-Order Email Service
    $wp_customize->add_setting('skyyrose_email_service', array(
        'default'           => 'mailchimp',
        'sanitize_callback' => 'sanitize_text_field',
    ));
    $wp_customize->add_control('skyyrose_email_service', array(
        'label'    => __('Email Service', 'skyyrose'),
        'section'  => 'skyyrose_preorder',
        'type'     => 'select',
        'choices'  => array(
            'mailchimp' => 'Mailchimp',
            'klaviyo'   => 'Klaviyo',
            'convertkit' => 'ConvertKit',
        ),
    ));

    // Mailchimp API Key
    $wp_customize->add_setting('skyyrose_mailchimp_api', array(
        'default'           => '',
        'sanitize_callback' => 'sanitize_text_field',
    ));
    $wp_customize->add_control('skyyrose_mailchimp_api', array(
        'label'    => __('Mailchimp API Key', 'skyyrose'),
        'section'  => 'skyyrose_preorder',
        'type'     => 'text',
    ));
}
add_action('customize_register', 'skyyrose_customize_register');

/**
 * Output CSS variables for theme customizer values
 */
function skyyrose_customizer_css() {
    ?>
    <style type="text/css">
        :root {
            --brand-name: "<?php echo esc_attr(get_theme_mod('skyyrose_brand_name', 'SkyyRose')); ?>";
            --black-rose: <?php echo esc_attr(get_theme_mod('skyyrose_color_black_rose', '#8B0000')); ?>;
            --black-rose-glow: <?php echo esc_attr(get_theme_mod('skyyrose_color_black_rose_glow', '#ff0000')); ?>;
            --love-hurts: <?php echo esc_attr(get_theme_mod('skyyrose_color_love_hurts', '#B76E79')); ?>;
            --love-hurts-light: <?php echo esc_attr(get_theme_mod('skyyrose_color_love_hurts_light', '#ffb6c1')); ?>;
            --signature-gold: <?php echo esc_attr(get_theme_mod('skyyrose_color_signature', '#D4AF37')); ?>;
            --signature-gold-glow: <?php echo esc_attr(get_theme_mod('skyyrose_color_signature_glow', '#ffd700')); ?>;
            --bg-dark: <?php echo esc_attr(get_theme_mod('skyyrose_color_bg_dark', '#030303')); ?>;
            --bg-deep: <?php echo esc_attr(get_theme_mod('skyyrose_color_bg_deep', '#000000')); ?>;

            --font-heading: <?php echo esc_attr(get_theme_mod('skyyrose_heading_font', 'Playfair Display')); ?>, serif;
            --font-body: <?php echo esc_attr(get_theme_mod('skyyrose_body_font', 'Inter')); ?>, sans-serif;
        }
    </style>
    <?php
}
add_action('wp_head', 'skyyrose_customizer_css');
add_action('customize_preview_init', 'skyyrose_customizer_css');
