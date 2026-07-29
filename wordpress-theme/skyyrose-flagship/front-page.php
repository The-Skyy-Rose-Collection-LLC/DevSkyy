<?php
/**
 * Front Page — SkyyRose v3 editorial homepage.
 *
 * Pure orchestration: eight acts, each in its own template part under
 * template-parts/home/, so no single file carries the whole page.
 *
 *   I    hero          masthead poster — portrait film, marquee-as-nav
 *   II   ticker        counter-scrolling shear band
 *   III  index-rooms   THE collection chooser (scroll-snap corridor)
 *   IV   drop          conditional pre-order proclamation (Customizer-gated)
 *   V    receipts      press wall + struck award seal + live piece count
 *   VI   origin        full-bleed founder testimony
 *   VII  letter        Kids Capsule keepsake board + 3D child character
 *   VIII close         closing statement, capture set inside the line
 *
 * Cut in this rebuild: the simulated loader (it covered the LCP and needed a
 * 2.5s self-dismiss safety net), the commercial runway, the collections grid
 * and the style atelier (three choosers answering one question), the craft
 * icon grid, the standalone quote block and the duplicate scroll-progress bar.
 *
 * Data: inc/homepage-data.php. CSS: assets/css/homepage-v3.css +
 * homepage-v3-editorial.css. JS: assets/js/homepage-v3.js + kc-mascot.js.
 *
 * @package SkyyRose
 * @since   1.13.0
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>

<main id="primary" class="site-main homepage-v3" role="main" tabindex="-1">

	<?php get_template_part( 'template-parts/home/hero' ); ?>

	<?php get_template_part( 'template-parts/home/ticker' ); ?>

	<?php get_template_part( 'template-parts/home/index-rooms' ); ?>

	<?php
	/*
	 * Act IV — the drop band. Double-gated inside the renderer (Customizer
	 * toggle + "has a title or an image"), so it stays out of the DOM entirely
	 * unless a drop is genuinely live. No countdown timers: manufactured
	 * urgency is not SkyyRose canon. homepage-v3-editorial.css restyles this
	 * existing markup into the full-bleed proclamation.
	 */
	if ( function_exists( 'skyyrose_render_drop_block' ) ) {
		skyyrose_render_drop_block();
	}
	?>

	<?php get_template_part( 'template-parts/home/receipts' ); ?>

	<?php get_template_part( 'template-parts/home/origin' ); ?>

	<?php get_template_part( 'template-parts/home/letter' ); ?>

	<?php get_template_part( 'template-parts/home/close' ); ?>

	<script data-jetpack-boost="ignore" type="application/ld+json">
	<?php
	echo wp_json_encode(
		array(
			'@context'     => 'https://schema.org',
			'@type'        => 'Organization',
			'name'         => 'SkyyRose',
			'url'          => home_url( '/' ),
			'logo'         => SKYYROSE_ASSETS_URI . '/branding/skyyrose-monogram.webp',
			'description'  => 'Oakland luxury streetwear. Gender-neutral, limited edition designs. Built by a father, named after a daughter.',
			'foundingDate' => '2020',
			'founder'      => array(
				'@type' => 'Person',
				'name'  => 'Corey Foster',
			),
			'address'      => array(
				'@type'           => 'PostalAddress',
				'addressLocality' => 'Oakland',
				'addressRegion'   => 'CA',
				'addressCountry'  => 'US',
			),
			'sameAs'       => array( 'https://instagram.com/skyyrose.co' ),
		),
		JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT
	);
	?>
	</script>

</main><!-- .homepage-v3 -->

<?php
/*
 * Homepage JS is inlined rather than enqueued: the host's page-optimize plugin
 * strips separately enqueued homepage scripts. Production serves the .min
 * build; source is used only when SCRIPT_DEBUG is on, or when the min file is
 * missing (i.e. right after a source edit, before `npm run build`).
 */
$hp_use_min = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;
$hp_scripts = array( 'homepage-v3', 'kc-mascot' );

foreach ( $hp_scripts as $hp_handle ) {
	$hp_min  = SKYYROSE_DIR . '/assets/js/' . $hp_handle . '.min.js';
	$hp_src  = SKYYROSE_DIR . '/assets/js/' . $hp_handle . '.js';
	$hp_path = ( $hp_use_min && file_exists( $hp_min ) ) ? $hp_min : $hp_src;
	if ( ! file_exists( $hp_path ) ) {
		continue;
	}
	// phpcs:ignore WordPress.WP.AlternativeFunctions.file_get_contents_file_get_contents -- inlining a local theme JS file for critical-path performance.
	$hp_body = file_get_contents( $hp_path );
	if ( ! $hp_body ) {
		continue;
	}
	echo '<script>' . $hp_body . '</script>'; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- raw local JS file inlined for critical-path performance.
}
?>

<?php get_footer(); ?>
