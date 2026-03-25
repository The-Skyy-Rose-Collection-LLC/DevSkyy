<?php
/**
 * Splite Scene — 3D Spline split-screen with spotlight effect.
 *
 * Adapted from 21st.dev/serafimcloud/splite for WordPress.
 * Uses the vanilla <spline-viewer> web component (no React/build needed).
 *
 * Usage in any template:
 *   get_template_part( 'template-parts/splite-scene', null, array(
 *       'scene'    => 'https://prod.spline.design/kZDDjO5HuC9GJUM2/scene.splinecode',
 *       'heading'  => 'Interactive 3D',
 *       'text'     => 'Bring your UI to life…',
 *       'cta_text' => 'Explore Collection',
 *       'cta_url'  => '/collections/',
 *   ) );
 *
 * @package SkyyRose_Flagship
 * @since   4.1.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$defaults = array(
	'scene'    => '',
	'heading'  => esc_html__( 'Interactive 3D', 'skyyrose-flagship' ),
	'text'     => esc_html__( 'Step inside the world of SkyyRose. Explore our collections in an immersive 3D experience that brings luxury streetwear to life.', 'skyyrose-flagship' ),
	'eyebrow'  => esc_html__( 'SkyyRose Experience', 'skyyrose-flagship' ),
	'cta_text' => '',
	'cta_url'  => '',
	'id'       => 'splite-' . wp_unique_id(),
);

$args = wp_parse_args( $args ?? array(), $defaults );

// Bail if no scene URL provided.
if ( empty( $args['scene'] ) ) {
	return;
}
?>

<section class="splite" id="<?php echo esc_attr( $args['id'] ); ?>" aria-label="<?php echo esc_attr( $args['heading'] ); ?>">
	<div class="splite__card">

		<?php $filter_id = esc_attr( $args['id'] ) . '-blur'; ?>
		<!-- Spotlight SVG (Aceternity-style — pure CSS animation, no JS) -->
		<svg class="splite__spotlight" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3787 2842" fill="none" aria-hidden="true">
			<g filter="url(#<?php echo $filter_id; ?>)">
				<ellipse
					cx="1924.71" cy="273.501"
					rx="1924.71" ry="273.501"
					transform="matrix(-0.822377 -0.568943 -0.568943 0.822377 3631.88 2291.09)"
					fill="#B76E79"
					fill-opacity="0.18"
				/>
			</g>
			<defs>
				<filter id="<?php echo $filter_id; ?>" x="0.86" y="0.84" width="3785.16" height="2840.26"
				        filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">
					<feFlood flood-opacity="0" result="bg"/>
					<feBlend mode="normal" in="SourceGraphic" in2="bg" result="shape"/>
					<feGaussianBlur stdDeviation="151" result="glow"/>
				</filter>
			</defs>
		</svg>

		<!-- Mouse-tracking spotlight (ibelick-style — vanilla JS) -->
		<div class="splite__glow" aria-hidden="true"></div>

		<div class="splite__layout">

			<!-- Left: Content -->
			<div class="splite__content">
				<?php if ( ! empty( $args['eyebrow'] ) ) : ?>
					<p class="splite__eyebrow"><?php echo esc_html( $args['eyebrow'] ); ?></p>
				<?php endif; ?>

				<h2 class="splite__heading"><?php echo esc_html( $args['heading'] ); ?></h2>

				<p class="splite__text"><?php echo esc_html( $args['text'] ); ?></p>

				<?php if ( ! empty( $args['cta_text'] ) && ! empty( $args['cta_url'] ) ) : ?>
					<a href="<?php echo esc_url( $args['cta_url'] ); ?>" class="splite__cta">
						<?php echo esc_html( $args['cta_text'] ); ?>
						<span aria-hidden="true">&rarr;</span>
					</a>
				<?php endif; ?>
			</div>

			<!-- Right: 3D Scene -->
			<div class="splite__scene">
				<div class="splite__loader" aria-label="<?php esc_attr_e( 'Loading 3D scene', 'skyyrose-flagship' ); ?>">
					<span class="splite__spinner"></span>
				</div>
				<spline-viewer
					url="<?php echo esc_url( $args['scene'] ); ?>"
					loading-anim-type="none"
					events-target="local"
				></spline-viewer>
			</div>

		</div>
	</div>
</section>
