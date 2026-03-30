<?php
/**
 * Immersive Loader — Loading Screen
 *
 * @package SkyyRose_Flagship
 * @since   6.0.0
 * @param array $args { @type string $world_name Scene title. }
 */
if ( ! defined( 'ABSPATH' ) ) { exit; }
$world_name = isset( $args['world_name'] ) ? $args['world_name'] : '';
?>
<div class="scene-loading" aria-live="polite">
	<div class="scene-loading-monogram" aria-hidden="true">SR</div>
	<p class="scene-loading-label"><?php echo esc_html( $world_name ); ?></p>
</div>
