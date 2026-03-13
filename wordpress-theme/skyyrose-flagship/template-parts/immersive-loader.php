<?php
/**
 * Immersive Loader — Shared Loading Screen
 *
 * Displays the SR monogram and "Entering [World]" text during scene load.
 * Used by all immersive templates and the spatial home.
 *
 * @param array $args {
 *     @type string $world_name The display name of the world (e.g., "The Garden").
 * }
 *
 * @package SkyyRose_Flagship
 * @since   4.4.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$world_name   = isset( $args['world_name'] ) ? $args['world_name'] : '';
$loading_text = $world_name
	/* translators: %s: world name, e.g. "The Garden" */
	? sprintf( esc_html__( 'Entering %s', 'skyyrose-flagship' ), esc_html( $world_name ) )
	: esc_html__( 'Loading', 'skyyrose-flagship' );
?>
<div class="scene-loading" aria-hidden="true">
	<div class="scene-loading-monogram"><?php echo esc_html__( 'SR', 'skyyrose-flagship' ); ?></div>
	<div class="scene-loading-text"><?php echo $loading_text; // Already escaped above. ?></div>
</div>
