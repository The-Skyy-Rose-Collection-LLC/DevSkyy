<?php
/**
 * Bricks Builder Compatibility
 *
 * Provides brand color injection and design token loading for sites
 * using Bricks Builder. Bricks reads theme.json natively, so minimal
 * integration code is needed.
 *
 * @package SkyyRose
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) || ! defined( 'BRICKS_VERSION' ) ) {
	return;
}

/**
 * Inject SkyyRose brand colors into Bricks global settings defaults.
 *
 * @since 1.0.0
 * @param array $defaults Bricks global defaults.
 * @return array Modified defaults with brand colors.
 */
function skyyrose_bricks_default_globals( $defaults ) {
	if ( ! isset( $defaults['colors'] ) ) {
		$defaults['colors'] = array();
	}

	$brand_colors = array(
		array(
			'id'   => 'skyyrose-dark',
			'name' => 'Dark Base',
			'raw'  => '#0A0A0A',
		),
		array(
			'id'   => 'skyyrose-rose-gold',
			'name' => 'Rose Gold',
			'raw'  => '#B76E79',
		),
		array(
			'id'   => 'skyyrose-white',
			'name' => 'White',
			'raw'  => '#FFFFFF',
		),
		array(
			'id'   => 'skyyrose-gold',
			'name' => 'Gold',
			'raw'  => '#D4AF37',
		),
		array(
			'id'   => 'skyyrose-silver',
			'name' => 'Silver',
			'raw'  => '#C0C0C0',
		),
		array(
			'id'   => 'skyyrose-crimson',
			'name' => 'Crimson',
			'raw'  => '#DC143C',
		),
	);

	$defaults['colors'] = array_merge( $brand_colors, $defaults['colors'] );

	return $defaults;
}
add_filter( 'bricks/setup/default_globals', 'skyyrose_bricks_default_globals' );

/**
 * Enqueue design tokens when Bricks renders a page.
 *
 * @since 1.0.0
 */
function skyyrose_bricks_enqueue_styles() {
	$post_id = get_the_ID();
	if ( $post_id && 'bricks' === get_post_meta( $post_id, '_bricks_editor_mode', true ) ) {
		wp_enqueue_style(
			'skyyrose-design-tokens',
			SKYYROSE_ASSETS_URI . '/css/design-tokens.css',
			array(),
			SKYYROSE_VERSION
		);
	}
}
add_action( 'wp_enqueue_scripts', 'skyyrose_bricks_enqueue_styles', 20 );
