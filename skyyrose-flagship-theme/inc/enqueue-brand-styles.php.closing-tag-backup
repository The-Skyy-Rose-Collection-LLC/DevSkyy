<?php
/**
 * Enqueue Brand Styles
 *
 * @package SkyyRose_Flagship
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Enqueue brand-specific stylesheets
 */
function skyyrose_enqueue_brand_styles() {
	// Brand variables (load first)
	wp_enqueue_style(
		'skyyrose-brand-variables',
		get_template_directory_uri() . '/assets/css/brand-variables.css',
		array(),
		SKYYROSE_VERSION
	);

	// Collection-specific colors
	wp_enqueue_style(
		'skyyrose-collection-colors',
		get_template_directory_uri() . '/assets/css/collection-colors.css',
		array( 'skyyrose-brand-variables' ),
		SKYYROSE_VERSION
	);

	// Luxury theme styles
	wp_enqueue_style(
		'skyyrose-luxury-theme',
		get_template_directory_uri() . '/assets/css/luxury-theme.css',
		array( 'skyyrose-brand-variables' ),
		SKYYROSE_VERSION
	);
}
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_brand_styles', 5 );
