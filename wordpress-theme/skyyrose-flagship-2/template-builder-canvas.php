<?php
/**
 * Template Name: Builder Canvas
 * Template Post Type: page
 *
 * Blank builder canvas with WordPress lifecycle hooks and SkyyRose assets.
 *
 * @package SkyyRoseFlagship2
 */

defined( 'ABSPATH' ) || exit;
?><!doctype html>
<html <?php language_attributes(); ?>>
<head>
	<meta charset="<?php bloginfo( 'charset' ); ?>">
	<meta name="viewport" content="width=device-width,initial-scale=1">
	<?php wp_head(); ?>
</head>
<body <?php body_class( 'sr2-builder-canvas' ); ?>>
	<?php wp_body_open(); ?>
	<a class="sr2-skip" href="#primary"><?php esc_html_e( 'Skip to content', 'skyyrose-flagship-2' ); ?></a>
	<main id="primary" class="sr2-builder-content">
		<?php
		while ( have_posts() ) :
			the_post();
			the_content();
		endwhile;
		?>
	</main>
	<?php wp_footer(); ?>
</body>
</html>
