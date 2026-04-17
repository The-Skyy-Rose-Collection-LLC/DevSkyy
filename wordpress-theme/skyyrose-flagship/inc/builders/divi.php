<?php
/**
 * Divi Builder Compatibility
 *
 * Provides theme support, brand palette injection, and custom element
 * allowlisting for sites using the Divi Builder.
 *
 * @package SkyyRose
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) || ! defined( 'ET_BUILDER_VERSION' ) ) {
	return;
}

/**
 * Add Divi Builder theme support.
 *
 * @since 1.0.0
 */
function skyyrose_divi_add_support() {
	add_theme_support( 'et-builder' );
}
add_action( 'after_setup_theme', 'skyyrose_divi_add_support' );

/**
 * Inject SkyyRose brand colors into Divi's default color palette.
 *
 * @since 1.0.0
 * @param array $colors Default color palette.
 * @return array Modified palette with brand colors.
 */
function skyyrose_divi_color_palette( $colors ) {
	return array(
		'#0A0A0A', // Dark base.
		'#B76E79', // Rose gold.
		'#FFFFFF', // White.
		'#D4AF37', // Gold (Signature).
		'#C0C0C0', // Silver (Black Rose).
		'#DC143C', // Crimson (Love Hurts).
	);
}
add_filter( 'et_default_color_palette', 'skyyrose_divi_color_palette' );

/**
 * Allow model-viewer custom element in Divi content.
 *
 * @since 1.0.0
 * @param array $tags Allowed HTML tags.
 * @return array Modified tags list.
 */
function skyyrose_divi_allowed_tags( $tags ) {
	$tags[] = 'model-viewer';
	return $tags;
}
add_filter( 'et_pb_allowed_tags', 'skyyrose_divi_allowed_tags' );

/**
 * Enqueue design tokens when Divi Builder is active on a page.
 *
 * @since 1.0.0
 */
function skyyrose_divi_enqueue_styles() {
	if ( ! function_exists( 'et_core_is_fb_enabled' ) ) {
		return;
	}

	if ( et_core_is_fb_enabled() || ( function_exists( 'et_pb_is_pagebuilder_used' ) && et_pb_is_pagebuilder_used( get_the_ID() ) ) ) {
		wp_enqueue_style(
			'skyyrose-design-tokens',
			SKYYROSE_ASSETS_URI . '/css/design-tokens.css',
			array(),
			SKYYROSE_VERSION
		);
	}
}
add_action( 'wp_enqueue_scripts', 'skyyrose_divi_enqueue_styles', 20 );
