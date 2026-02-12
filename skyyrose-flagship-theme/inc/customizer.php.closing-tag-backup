<?php
/**
 * Theme Customizer
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Add postMessage support for site title and description.
 *
 * @since 1.0.0
 * @param WP_Customize_Manager $wp_customize Theme Customizer object.
 */
function skyyrose_customize_register( $wp_customize ) {
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
}
add_action( 'customize_register', 'skyyrose_customize_register' );

/**
 * Render the site title for the selective refresh partial.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_customize_partial_blogname() {
	bloginfo( 'name' );
}

/**
 * Render the site tagline for the selective refresh partial.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_customize_partial_blogdescription() {
	bloginfo( 'description' );
}

/**
 * Binds JS handlers to make Theme Customizer preview reload changes asynchronously.
 *
 * @since 1.0.0
 */
function skyyrose_customize_preview_js() {
	// Use minified assets in production.
	$suffix = ( defined( 'SCRIPT_DEBUG' ) && SCRIPT_DEBUG ) ? '' : '.min';

	wp_enqueue_script(
		'skyyrose-customizer',
		SKYYROSE_ASSETS_URI . '/js/customizer' . $suffix . '.js',
		array( 'customize-preview' ),
		SKYYROSE_VERSION,
		true
	);
}
add_action( 'customize_preview_init', 'skyyrose_customize_preview_js' );
