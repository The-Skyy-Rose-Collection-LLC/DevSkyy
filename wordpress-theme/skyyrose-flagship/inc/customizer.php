<?php
/**
 * Theme Customizer
 *
 * Registers brand color controls, logo upload, social media URLs,
 * and live preview with postMessage transport.
 *
 * @package SkyyRose_Flagship
 * @since   1.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Register Customizer settings, sections, and controls.
 *
 * @since 1.0.0
 *
 * @param WP_Customize_Manager $wp_customize Theme Customizer object.
 * @return void
 */
function skyyrose_customize_register( $wp_customize ) {

	/*--------------------------------------------------------------
	 * Core settings transport
	 *--------------------------------------------------------------*/
	$wp_customize->get_setting( 'blogname' )->transport         = 'postMessage';
	$wp_customize->get_setting( 'blogdescription' )->transport  = 'postMessage';
	$wp_customize->get_setting( 'header_textcolor' )->transport = 'postMessage';

	if ( isset( $wp_customize->selective_refresh ) ) {
		$wp_customize->selective_refresh->add_partial(
			'blogname',
			array(
				'selector'        => '.site-title a',
				'render_callback' => 'skyyrose_customize_partial_blogname',
			)
		);
		$wp_customize->selective_refresh->add_partial(
			'blogdescription',
			array(
				'selector'        => '.site-description',
				'render_callback' => 'skyyrose_customize_partial_blogdescription',
			)
		);
	}

	/*--------------------------------------------------------------
	 * Section: Brand Identity
	 *--------------------------------------------------------------*/
	$wp_customize->add_section(
		'skyyrose_brand',
		array(
			'title'       => esc_html__( 'Brand Identity', 'skyyrose-flagship' ),
			'description' => esc_html__( 'Customize brand colors, logo, and social media links.', 'skyyrose-flagship' ),
			'priority'    => 30,
		)
	);

	/*--------------------------------------------------------------
	 * Setting + Control: Primary Brand Color (Rose Gold)
	 *--------------------------------------------------------------*/
	$wp_customize->add_setting(
		'skyyrose_primary_color',
		array(
			'default'           => '#B76E79',
			'transport'         => 'postMessage',
			'sanitize_callback' => 'sanitize_hex_color',
		)
	);

	$wp_customize->add_control(
		new WP_Customize_Color_Control(
			$wp_customize,
			'skyyrose_primary_color',
			array(
				'label'       => esc_html__( 'Primary Brand Color', 'skyyrose-flagship' ),
				'description' => esc_html__( 'Rose gold accent used for headings, links, and highlights.', 'skyyrose-flagship' ),
				'section'     => 'skyyrose_brand',
				'settings'    => 'skyyrose_primary_color',
			)
		)
	);

	/*--------------------------------------------------------------
	 * Setting + Control: Gold Accent Color
	 *--------------------------------------------------------------*/
	$wp_customize->add_setting(
		'skyyrose_gold_accent',
		array(
			'default'           => '#D4AF37',
			'transport'         => 'postMessage',
			'sanitize_callback' => 'sanitize_hex_color',
		)
	);

	$wp_customize->add_control(
		new WP_Customize_Color_Control(
			$wp_customize,
			'skyyrose_gold_accent',
			array(
				'label'       => esc_html__( 'Gold Accent Color', 'skyyrose-flagship' ),
				'description' => esc_html__( 'Used for buttons, CTA accents, and luxury highlights.', 'skyyrose-flagship' ),
				'section'     => 'skyyrose_brand',
				'settings'    => 'skyyrose_gold_accent',
			)
		)
	);

	/*--------------------------------------------------------------
	 * Setting + Control: Dark Background Color
	 *--------------------------------------------------------------*/
	$wp_customize->add_setting(
		'skyyrose_dark_bg',
		array(
			'default'           => '#0A0A0A',
			'transport'         => 'postMessage',
			'sanitize_callback' => 'sanitize_hex_color',
		)
	);

	$wp_customize->add_control(
		new WP_Customize_Color_Control(
			$wp_customize,
			'skyyrose_dark_bg',
			array(
				'label'       => esc_html__( 'Dark Background', 'skyyrose-flagship' ),
				'description' => esc_html__( 'Primary dark background for header, footer, and immersive sections.', 'skyyrose-flagship' ),
				'section'     => 'skyyrose_brand',
				'settings'    => 'skyyrose_dark_bg',
			)
		)
	);

	/*--------------------------------------------------------------
	 * Setting + Control: Brand Logo Upload
	 *--------------------------------------------------------------*/
	$wp_customize->add_setting(
		'skyyrose_brand_logo',
		array(
			'default'           => '',
			'transport'         => 'refresh',
			'sanitize_callback' => 'esc_url_raw',
		)
	);

	$wp_customize->add_control(
		new WP_Customize_Image_Control(
			$wp_customize,
			'skyyrose_brand_logo',
			array(
				'label'       => esc_html__( 'Brand Logo (SVG or PNG)', 'skyyrose-flagship' ),
				'description' => esc_html__( 'Upload a transparent-background logo for the footer and email templates. Use Custom Logo (above) for the header.', 'skyyrose-flagship' ),
				'section'     => 'skyyrose_brand',
				'settings'    => 'skyyrose_brand_logo',
			)
		)
	);

	/*--------------------------------------------------------------
	 * Section: Social Media
	 *--------------------------------------------------------------*/
	$wp_customize->add_section(
		'skyyrose_social',
		array(
			'title'       => esc_html__( 'Social Media', 'skyyrose-flagship' ),
			'description' => esc_html__( 'Add your social media profile URLs for the footer and Open Graph.', 'skyyrose-flagship' ),
			'priority'    => 35,
		)
	);

	$social_networks = array(
		'instagram' => array(
			'label'   => esc_html__( 'Instagram URL', 'skyyrose-flagship' ),
			'default' => '',
		),
		'tiktok'    => array(
			'label'   => esc_html__( 'TikTok URL', 'skyyrose-flagship' ),
			'default' => '',
		),
		'facebook'  => array(
			'label'   => esc_html__( 'Facebook URL', 'skyyrose-flagship' ),
			'default' => '',
		),
		'twitter'   => array(
			'label'   => esc_html__( 'X (Twitter) URL', 'skyyrose-flagship' ),
			'default' => '',
		),
		'pinterest' => array(
			'label'   => esc_html__( 'Pinterest URL', 'skyyrose-flagship' ),
			'default' => '',
		),
		'youtube'   => array(
			'label'   => esc_html__( 'YouTube URL', 'skyyrose-flagship' ),
			'default' => '',
		),
		'linkedin'  => array(
			'label'   => esc_html__( 'LinkedIn URL', 'skyyrose-flagship' ),
			'default' => '',
		),
	);

	foreach ( $social_networks as $network_id => $config ) {
		$setting_id = 'skyyrose_social_' . $network_id;

		$wp_customize->add_setting(
			$setting_id,
			array(
				'default'           => $config['default'],
				'transport'         => 'postMessage',
				'sanitize_callback' => 'esc_url_raw',
			)
		);

		$wp_customize->add_control(
			$setting_id,
			array(
				'label'   => $config['label'],
				'section' => 'skyyrose_social',
				'type'    => 'url',
			)
		);
	}

	/*--------------------------------------------------------------
	 * Setting + Control: Twitter Handle (for Twitter Cards meta)
	 *--------------------------------------------------------------*/
	$wp_customize->add_setting(
		'twitter_handle',
		array(
			'default'           => '',
			'transport'         => 'postMessage',
			'sanitize_callback' => 'sanitize_text_field',
		)
	);

	$wp_customize->add_control(
		'twitter_handle',
		array(
			'label'       => esc_html__( 'Twitter/X Handle', 'skyyrose-flagship' ),
			'description' => esc_html__( 'Without the @ symbol (e.g., "SkyyRose").', 'skyyrose-flagship' ),
			'section'     => 'skyyrose_social',
			'type'        => 'text',
		)
	);

	/*--------------------------------------------------------------
	 * Setting + Control: Contact Email
	 *--------------------------------------------------------------*/
	$wp_customize->add_setting(
		'contact_email',
		array(
			'default'           => '',
			'transport'         => 'postMessage',
			'sanitize_callback' => 'sanitize_email',
		)
	);

	$wp_customize->add_control(
		'contact_email',
		array(
			'label'   => esc_html__( 'Contact Email', 'skyyrose-flagship' ),
			'section' => 'skyyrose_social',
			'type'    => 'email',
		)
	);

	/*--------------------------------------------------------------
	 * Setting + Control: Contact Phone
	 *--------------------------------------------------------------*/
	$wp_customize->add_setting(
		'contact_phone',
		array(
			'default'           => '',
			'transport'         => 'postMessage',
			'sanitize_callback' => 'sanitize_text_field',
		)
	);

	$wp_customize->add_control(
		'contact_phone',
		array(
			'label'   => esc_html__( 'Contact Phone', 'skyyrose-flagship' ),
			'section' => 'skyyrose_social',
			'type'    => 'tel',
		)
	);
}
add_action( 'customize_register', 'skyyrose_customize_register' );

/**
 * Output custom CSS from Customizer brand color settings.
 *
 * Generates CSS custom properties so all templates inherit the brand palette.
 *
 * @since 3.0.0
 * @return void
 */
function skyyrose_customizer_css_output() {

	$primary_color = get_theme_mod( 'skyyrose_primary_color', '#B76E79' );
	$gold_accent   = get_theme_mod( 'skyyrose_gold_accent', '#D4AF37' );
	$dark_bg       = get_theme_mod( 'skyyrose_dark_bg', '#0A0A0A' );

	// Only output if any value differs from defaults.
	if ( '#B76E79' === $primary_color && '#D4AF37' === $gold_accent && '#0A0A0A' === $dark_bg ) {
		return;
	}

	$css = ':root {';
	if ( '#B76E79' !== $primary_color ) {
		$css .= '--skyyrose-primary: ' . esc_attr( $primary_color ) . ';';
		$css .= '--rose-gold: ' . esc_attr( $primary_color ) . ';';
	}
	if ( '#D4AF37' !== $gold_accent ) {
		$css .= '--skyyrose-gold: ' . esc_attr( $gold_accent ) . ';';
		$css .= '--gold: ' . esc_attr( $gold_accent ) . ';';
	}
	if ( '#0A0A0A' !== $dark_bg ) {
		$css .= '--skyyrose-dark-bg: ' . esc_attr( $dark_bg ) . ';';
	}
	$css .= '}';

	wp_add_inline_style( 'skyyrose-design-tokens', $css );
}
add_action( 'wp_enqueue_scripts', 'skyyrose_customizer_css_output', 25 );

/**
 * Render site title for selective refresh partial.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_customize_partial_blogname() {
	bloginfo( 'name' );
}

/**
 * Render site tagline for selective refresh partial.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_customize_partial_blogdescription() {
	bloginfo( 'description' );
}

/**
 * Enqueue Customizer preview JS for live postMessage updates.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_customize_preview_js() {

	$customizer_js = SKYYROSE_DIR . '/assets/js/customizer.js';
	if ( file_exists( $customizer_js ) ) {
		wp_enqueue_script(
			'skyyrose-customizer',
			SKYYROSE_ASSETS_URI . '/js/customizer.js',
			array( 'customize-preview' ),
			SKYYROSE_VERSION,
			true
		);
	}
}
add_action( 'customize_preview_init', 'skyyrose_customize_preview_js' );

/**
 * Retrieve all social media URLs configured in the Customizer.
 *
 * Returns an immutable array (new copy) of network => URL pairs,
 * filtering out empty values.
 *
 * @since  3.0.0
 * @return array Associative array of network_id => URL.
 */
function skyyrose_get_social_urls() {

	$networks = array( 'instagram', 'tiktok', 'facebook', 'twitter', 'pinterest', 'youtube', 'linkedin' );
	$urls     = array();

	foreach ( $networks as $network ) {
		$url = get_theme_mod( 'skyyrose_social_' . $network, '' );
		if ( ! empty( $url ) ) {
			$urls[ $network ] = esc_url( $url );
		}
	}

	return $urls;
}
