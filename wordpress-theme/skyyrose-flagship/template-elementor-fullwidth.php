<?php
/**
 * Template Name: Full Width (SkyyRose)
 * Template Post Type: page
 *
 * Full-width layout — theme header and footer preserved, no sidebar.
 * Ideal for builder pages that need the SkyyRose navigation and footer
 * but full control over the content area.
 *
 * @package SkyyRose
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

get_header();
?>
<main id="primary" class="site-content skyyrose-full-width">
	<?php
	while ( have_posts() ) :
		the_post();
		the_content();
	endwhile;
	?>
</main>
<?php
get_footer();
