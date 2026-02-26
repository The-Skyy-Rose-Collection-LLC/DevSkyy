<?php
/**
 * Front Page: Hero Section
 *
 * 100vh hero with animated orbs, sparkles, brand name reveal,
 * rotating collection text, and CTAs.
 *
 * @package SkyyRose_Flagship
 * @since   3.2.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
?>

<section class="hero" aria-label="<?php esc_attr_e( 'Hero', 'skyyrose-flagship' ); ?>">
	<div class="hero__bg" aria-hidden="true">
		<div class="hero__orb hero__orb--1"></div>
		<div class="hero__orb hero__orb--2"></div>
		<div class="hero__orb hero__orb--3"></div>
	</div>

	<!-- Sparkle / particle layer -->
	<div class="hero__sparkles" aria-hidden="true" id="js-hero-sparkles"></div>

	<div class="hero__content">

		<!-- Brand Name — Upscale Script with Animated Reveal -->
		<h1 class="hero__brand-name" aria-label="<?php esc_attr_e( 'SkyyRose', 'skyyrose-flagship' ); ?>">
			<span class="hero__brand-letter" aria-hidden="true" style="--i:0">S</span><span
				class="hero__brand-letter" aria-hidden="true" style="--i:1">K</span><span
				class="hero__brand-letter" aria-hidden="true" style="--i:2">Y</span><span
				class="hero__brand-letter" aria-hidden="true" style="--i:3">Y</span><span
				class="hero__brand-letter hero__brand-letter--rose" aria-hidden="true" style="--i:4">R</span><span
				class="hero__brand-letter hero__brand-letter--rose" aria-hidden="true" style="--i:5">O</span><span
				class="hero__brand-letter hero__brand-letter--rose" aria-hidden="true" style="--i:6">S</span><span
				class="hero__brand-letter hero__brand-letter--rose" aria-hidden="true" style="--i:7">E</span>
		</h1>

		<!-- Rose gold divider line with expand animation -->
		<div class="hero__divider" aria-hidden="true">
			<span class="hero__divider-line"></span>
			<span class="hero__divider-diamond"></span>
			<span class="hero__divider-line"></span>
		</div>

		<!-- Tagline — Fades in after brand name reveals -->
		<p class="hero__tagline-main">
			<?php esc_html_e( 'Luxury Grows from Concrete.', 'skyyrose-flagship' ); ?>
		</p>

		<span class="hero__badge">
			<svg class="hero__badge-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
				<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
			</svg>
			<?php esc_html_e( 'Oakland Luxury Streetwear', 'skyyrose-flagship' ); ?>
		</span>

		<!-- Rotating text cycling through collection names -->
		<div class="hero__rotating" aria-hidden="true">
			<span class="hero__rotating-label">
				<?php esc_html_e( 'Now Featuring:', 'skyyrose-flagship' ); ?>
			</span>
			<span class="hero__rotating-text js-rotating-text" data-texts="<?php echo esc_attr( wp_json_encode( array(
				__( 'The Black Rose Collection', 'skyyrose-flagship' ),
				__( 'The Love Hurts Collection', 'skyyrose-flagship' ),
				__( 'The Signature Collection', 'skyyrose-flagship' ),
				__( 'Limited Edition Drops', 'skyyrose-flagship' ),
			) ) ); ?>">
				<?php esc_html_e( 'The Black Rose Collection', 'skyyrose-flagship' ); ?>
			</span>
		</div>

		<p class="hero__subtitle">
			<?php esc_html_e( 'Three distinct collections, one unified vision. Born in Oakland, crafted with passion, designed for those who wear their heart on their sleeve.', 'skyyrose-flagship' ); ?>
		</p>

		<div class="hero__cta">
			<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" class="btn btn--primary">
				<?php esc_html_e( 'Pre-Order Now', 'skyyrose-flagship' ); ?>
			</a>
			<a href="#collections" class="btn btn--outline js-smooth-scroll">
				<?php esc_html_e( 'Explore Collections', 'skyyrose-flagship' ); ?>
			</a>
		</div>
	</div>

	<div class="hero__scroll-indicator" aria-hidden="true">
		<span><?php esc_html_e( 'Scroll', 'skyyrose-flagship' ); ?></span>
	</div>
</section>
