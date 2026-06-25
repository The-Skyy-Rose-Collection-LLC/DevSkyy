<?php
/**
 * Bricks Builder Compatibility
 *
 * Brand color injection into Bricks global defaults. Bricks reads
 * theme.json natively, so no further integration is required.
 * Design-tokens.css is enqueued globally by inc/enqueue.php.
 *
 * @package SkyyRose
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) || ! defined( 'BRICKS_VERSION' ) ) {
	return;
}

/**
 * Map skyyrose_brand_colors() to Bricks' global-defaults shape.
 *
 * @since 1.0.0
 *
 * @param array $colors    skyyrose_brand_colors() output.
 * @param array $defaults  Existing Bricks defaults (merged with brand colors).
 * @return array Defaults with brand colors prepended.
 */
function skyyrose_bricks_default_globals_callback( array $colors, $defaults = array() ) {
	if ( ! is_array( $defaults ) ) {
		$defaults = array();
	}
	if ( ! isset( $defaults['colors'] ) || ! is_array( $defaults['colors'] ) ) {
		$defaults['colors'] = array();
	}

	$brand_colors = array(
		array(
			'id'   => 'skyyrose-dark',
			'name' => 'Dark Base',
			'raw'  => $colors['dark'],
		),
		array(
			'id'   => 'skyyrose-rose-gold',
			'name' => 'Rose Gold',
			'raw'  => $colors['rose_gold'],
		),
		array(
			'id'   => 'skyyrose-white',
			'name' => 'White',
			'raw'  => '#FFFFFF',
		),
		array(
			'id'   => 'skyyrose-gold',
			'name' => 'Gold',
			'raw'  => $colors['gold'],
		),
		array(
			'id'   => 'skyyrose-silver',
			'name' => 'Silver',
			'raw'  => $colors['silver'],
		),
		array(
			'id'   => 'skyyrose-crimson',
			'name' => 'Crimson',
			'raw'  => $colors['crimson'],
		),
	);

	$defaults['colors'] = array_merge( $brand_colors, $defaults['colors'] );

	return $defaults;
}

skyyrose_register_builder_compat(
	'bricks',
	array(
		'palette_hook'     => 'bricks/setup/default_globals',
		'palette_callback' => 'skyyrose_bricks_default_globals_callback',
	)
);
