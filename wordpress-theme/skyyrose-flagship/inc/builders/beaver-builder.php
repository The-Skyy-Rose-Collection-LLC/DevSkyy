<?php
/**
 * Beaver Builder Compatibility
 *
 * Provides theme support, header/footer location registration,
 * and brand color presets for sites using Beaver Builder.
 *
 * @package SkyyRose
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) || ! class_exists( 'FLBuilderLoader' ) ) {
	return;
}

/**
 * Add Beaver Builder theme support.
 *
 * @since 1.0.0
 */
function skyyrose_bb_add_support() {
	add_theme_support( 'fl-theme-builder-headers' );
	add_theme_support( 'fl-theme-builder-footers' );
	add_theme_support( 'fl-theme-builder-parts' );
}
add_action( 'after_setup_theme', 'skyyrose_bb_add_support' );

/**
 * Register header and footer locations for BB Theme Builder.
 *
 * @since 1.0.0
 */
function skyyrose_bb_register_locations() {
	if ( ! class_exists( 'FLThemeBuilderLayoutData' ) ) {
		return;
	}

	FLThemeBuilderLayoutData::register_location(
		'header',
		array(
			'label' => esc_html__( 'Header', 'skyyrose' ),
		)
	);

	FLThemeBuilderLayoutData::register_location(
		'footer',
		array(
			'label' => esc_html__( 'Footer', 'skyyrose' ),
		)
	);
}
add_action( 'init', 'skyyrose_bb_register_locations' );

/**
 * Inject SkyyRose brand colors into BB color presets.
 *
 * @since 1.0.0
 * @param array $colors Default color presets.
 * @return array Modified presets with brand colors.
 */
function skyyrose_bb_color_presets( $colors ) {
	return array(
		'0A0A0A', // Dark base.
		'B76E79', // Rose gold.
		'FFFFFF', // White.
		'D4AF37', // Gold (Signature).
		'C0C0C0', // Silver (Black Rose).
		'DC143C', // Crimson (Love Hurts).
	);
}
add_filter( 'fl_builder_color_presets', 'skyyrose_bb_color_presets' );

/**
 * Enqueue design tokens when Beaver Builder is active on a page.
 *
 * @since 1.0.0
 */
function skyyrose_bb_enqueue_styles() {
	if ( ! class_exists( 'FLBuilderModel' ) ) {
		return;
	}

	$post_id = get_the_ID();
	if ( $post_id && FLBuilderModel::is_builder_enabled( $post_id ) ) {
		wp_enqueue_style(
			'skyyrose-design-tokens',
			SKYYROSE_ASSETS_URI . '/css/design-tokens.css',
			array(),
			SKYYROSE_VERSION
		);
	}
}
add_action( 'wp_enqueue_scripts', 'skyyrose_bb_enqueue_styles', 20 );
