<?php
/**
 * Template Name: Elementor Canvas (SkyyRose)
 * Template Post Type: page
 *
 * Blank canvas for Elementor — no header, footer, or theme wrapper.
 * Design tokens and fonts still load via wp_head() so Elementor
 * sections inherit the SkyyRose brand system.
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

<?php wp_footer(); ?>
</body>
</html>
