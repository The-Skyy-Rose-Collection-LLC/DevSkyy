<?php
/**
 * Template Part: Brand Avatar (3D Model Viewer)
 *
 * Displays the SkyyRose brand avatar using Google model-viewer for 3D (GLB)
 * with automatic 2D poster fallback when the GLB file is not yet available.
 *
 * Usage:
 *   get_template_part( 'template-parts/brand-avatar', null, $args );
 *
 * @param array $args {
 *     Brand avatar arguments.
 *
 *     @type string $glb_src    Path to the .glb 3D model file (optional).
 *     @type string $poster_src Path to the 2D poster/fallback image (required).
 *     @type string $alt        Alt text for the poster image.
 *     @type string $class      Additional CSS classes.
 * }
 *
 * @package SkyyRose_Flagship
 * @since   3.2.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$defaults = array(
	'glb_src'    => '',
	'poster_src' => SKYYROSE_ASSETS_URI . '/images/avatar/skyyrose-model-front.png',
	'alt'        => __( 'SkyyRose brand model', 'skyyrose-flagship' ),
	'class'      => '',
);

$args = wp_parse_args( $args ?? array(), $defaults );

$glb_relative = ltrim( str_replace( SKYYROSE_ASSETS_URI, '', $args['glb_src'] ?? '' ), '/' );
$glb_realbase = realpath( SKYYROSE_DIR . '/assets/' );
$glb_realpath = $glb_relative ? realpath( SKYYROSE_DIR . '/assets/' . $glb_relative ) : false;
$has_glb      = ! empty( $glb_relative )
	&& false !== $glb_realpath
	&& false !== $glb_realbase
	&& 0 === strpos( $glb_realpath, $glb_realbase . DIRECTORY_SEPARATOR )
	&& file_exists( $glb_realpath );
if ( ! empty( $args['class'] ) ) {
	$extra_class = ' ' . implode( ' ', array_map( 'sanitize_html_class', array_filter( explode( ' ', $args['class'] ) ) ) );
} else {
	$extra_class = '';
}
?>

<div class="brand-avatar<?php echo esc_attr( $extra_class ); ?>">
	<?php if ( $has_glb ) : ?>
		<model-viewer
			src="<?php echo esc_url( $args['glb_src'] ); ?>"
			poster="<?php echo esc_url( $args['poster_src'] ); ?>"
			alt="<?php echo esc_attr( $args['alt'] ); ?>"
			camera-controls
			touch-action="pan-y"
			auto-rotate
			auto-rotate-delay="3000"
			rotation-per-second="15deg"
			shadow-intensity="0.4"
			exposure="1"
			loading="lazy"
			reveal="auto"
			ar
			ar-modes="webxr scene-viewer quick-look"
		>
			<div class="progress-bar" slot="progress-bar"></div>
		</model-viewer>
		<span class="brand-avatar__hint" aria-hidden="true">
			<?php esc_html_e( 'Drag to rotate', 'skyyrose-flagship' ); ?>
		</span>
	<?php else : ?>
		<img
			src="<?php echo esc_url( $args['poster_src'] ); ?>"
			alt="<?php echo esc_attr( $args['alt'] ); ?>"
			class="brand-avatar__fallback"
			loading="lazy"
			decoding="async"
		>
	<?php endif; ?>
</div>
