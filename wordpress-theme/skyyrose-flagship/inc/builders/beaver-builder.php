<?php
/**
 * Beaver Builder Compatibility
 *
 * Theme support, header/footer location registration, and brand color
 * presets for sites running Beaver Builder. Design-tokens.css is
 * enqueued globally by inc/enqueue.php — this file does NOT enqueue it.
 *
 * @package SkyyRose
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) || ! class_exists( 'FLBuilderLoader' ) ) {
	return;
}

/**
 * Add Beaver Builder theme support (header/footer/parts via Theme Builder).
 *
 * @since 1.0.0
 */
function skyyrose_bb_add_support() {
	add_theme_support( 'fl-theme-builder-headers' );
	add_theme_support( 'fl-theme-builder-footers' );
	add_theme_support( 'fl-theme-builder-parts' );
}

/**
 * Register header/footer locations for the BB Theme Builder.
 *
 * @since 1.0.0
 */
function skyyrose_bb_register_locations() {
	if ( ! class_exists( 'FLThemeBuilderLayoutData' ) ) {
		return;
	}

	FLThemeBuilderLayoutData::register_location(
		'header',
		array( 'label' => esc_html__( 'Header', 'skyyrose' ) )
	);
	FLThemeBuilderLayoutData::register_location(
		'footer',
		array( 'label' => esc_html__( 'Footer', 'skyyrose' ) )
	);
}
add_action( 'init', 'skyyrose_bb_register_locations' );

/**
 * Map skyyrose_brand_colors() to BB's color-presets shape (hex without #).
 *
 * @since 1.0.0
 *
 * @param array $colors  skyyrose_brand_colors() output.
 * @param mixed $existing  Current presets (ignored — full replacement).
 * @return array Brand-aligned hex strings (no leading #).
 */
function skyyrose_bb_color_presets_callback( array $colors, $existing = null ) {
	unset( $existing );

	$strip = static fn( string $hex ): string => ltrim( $hex, '#' );

	return array(
		$strip( $colors['dark'] ),
		$strip( $colors['rose_gold'] ),
		'FFFFFF',
		$strip( $colors['gold'] ),
		$strip( $colors['silver'] ),
		$strip( $colors['crimson'] ),
	);
}

skyyrose_register_builder_compat(
	'beaver-builder',
	array(
		'theme_support'    => 'skyyrose_bb_add_support',
		'palette_hook'     => 'fl_builder_color_presets',
		'palette_callback' => 'skyyrose_bb_color_presets_callback',
	)
);
