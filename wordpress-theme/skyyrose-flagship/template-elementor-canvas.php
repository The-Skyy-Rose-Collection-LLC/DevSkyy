<?php
/**
 * Template Name: Elementor Canvas (SkyyRose)
 * Template Post Type: page
 *
 * Blank canvas for Elementor — no header, footer, or theme wrapper.
 * Design tokens and fonts still load via wp_head() so Elementor
 * sections inherit the SkyyRose brand system. Deliberate exception: the
 * Skyy mascot widget IS mounted (same kill-switch gate as every other
 * template) so the "no theme wrapper" contract doesn't create a sitewide
 * host coverage hole — see the gate before wp_footer() below.
 *
 * @package SkyyRose
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
?><!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
	<meta charset="<?php bloginfo( 'charset' ); ?>">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<?php wp_head(); ?>
</head>
<body <?php body_class( 'skyyrose-canvas' ); ?>>
<?php wp_body_open(); ?>

<a class="skip-link" href="#primary"><?php esc_html_e( 'Skip to the story', 'skyyrose' ); ?></a>

<div id="primary" tabindex="-1">
<?php
while ( have_posts() ) :
	the_post();
	the_content();
endwhile;
?>
</div>

<?php
// This template never calls get_footer(), so the sitewide mascot mount in
// footer.php never reaches it — mount independently here, same gate
// (Customizer kill switch, checkout excluded) as footer.php/front-page.php.
if ( function_exists( 'skyyrose_mascot_is_enabled' ) && skyyrose_mascot_is_enabled()
	&& ! ( function_exists( 'is_checkout' ) && is_checkout() ) ) {
	get_template_part( 'template-parts/skyy-mascot' );
}
?>

<?php wp_footer(); ?>
</body>
</html>
