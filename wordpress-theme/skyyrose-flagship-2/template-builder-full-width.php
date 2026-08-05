<?php
/**
 * Template Name: Builder Full Width
 * Template Post Type: page
 *
 * Builder-owned content with the SkyyRose header, footer, tokens, and scripts.
 *
 * @package SkyyRoseFlagship2
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>
<main id="primary" class="<?php echo esc_attr( skyyrose2_builder_content_class() ); ?>">
	<?php
	while ( have_posts() ) :
		the_post();
		the_content();
	endwhile;
	?>
</main>
<?php
get_footer();
