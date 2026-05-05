<?php
/**
 * Divi Builder Compatibility
 *
 * Theme support, brand palette injection, and custom element allow-listing
 * for sites running the Divi Builder. Design-tokens.css is enqueued
 * globally by inc/enqueue.php — this file does NOT enqueue it.
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

/**
 * Map skyyrose_brand_colors() to Divi's default-palette filter shape.
 *
 * @since 1.0.0
 *
 * @param array $colors  skyyrose_brand_colors() output.
 * @param mixed $existing  Current palette (ignored — Divi expects a full replacement).
 * @return array Brand-aligned palette.
 */
function skyyrose_divi_color_palette_callback( array $colors, $existing = null ) {
	unset( $existing );

	return array(
		$colors['dark'],      // Dark base.
		$colors['rose_gold'], // Rose gold.
		'#FFFFFF',            // White (not a brand color — explicit constant).
		$colors['gold'],      // Gold (Signature).
		$colors['silver'],    // Silver (Black Rose).
		$colors['crimson'],   // Crimson (Love Hurts).
	);
}

/**
 * Allow the <model-viewer> custom element inside Divi modules.
 *
 * @since 1.0.0
 *
 * @param array $tags Allowed HTML tags.
 * @return array Modified tags list.
 */
function skyyrose_divi_allowed_tags( $tags ) {
	$tags[] = 'model-viewer';
	return $tags;
}
add_filter( 'et_pb_allowed_tags', 'skyyrose_divi_allowed_tags' );

skyyrose_register_builder_compat(
	'divi',
	array(
		'theme_support'    => 'skyyrose_divi_add_support',
		'palette_hook'     => 'et_default_color_palette',
		'palette_callback' => 'skyyrose_divi_color_palette_callback',
	)
);
