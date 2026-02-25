<?php
/**
 * Template Name: Homepage
 *
 * The homepage template for SkyyRose Flagship.
 * Hero with floating orbs and sparkle particles, social proof bar,
 * collections showcase, "Why SkyyRose" value props, featured products,
 * Instagram feed, press mentions, brand story with pull quote,
 * testimonials, and newsletter signup.
 *
 * Each section is extracted into its own template part under
 * template-parts/front-page/ for maintainability (< 800 lines per file).
 *
 * @package SkyyRose_Flagship
 * @since   3.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

get_header();
?>

<main id="primary" class="site-main front-page" role="main">

	<?php
	// Hero — 100vh with animated orbs, sparkles, brand name reveal.
	get_template_part( 'template-parts/front-page/section', 'hero' );

	// Social Proof — Animated stat counters.
	get_template_part( 'template-parts/front-page/section', 'social-proof' );

	// Collections Showcase — 3 collection cards.
	get_template_part( 'template-parts/front-page/section', 'collections' );

	// Why SkyyRose — 4 value proposition cards.
	get_template_part( 'template-parts/front-page/section', 'why-skyyrose' );

	// Featured Products — WooCommerce grid with static fallback.
	get_template_part( 'template-parts/front-page/section', 'featured-products' );

	// Instagram Feed — 6-square grid with hover overlay.
	get_template_part( 'template-parts/front-page/section', 'instagram' );

	// Press / As Seen In — Media mention logos.
	get_template_part( 'template-parts/front-page/section', 'press' );

	// Brand Story — 2-column layout with pull quote and stats.
	get_template_part( 'template-parts/front-page/section', 'brand-story' );

	// Testimonials — 3 customer review cards.
	get_template_part( 'template-parts/front-page/section', 'testimonials' );

	// Newsletter — Email signup with incentive.
	get_template_part( 'template-parts/front-page/section', 'newsletter' );
	?>

</main><!-- #primary -->

<?php
get_footer();
