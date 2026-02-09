<?php
/**
 * The template for displaying all single posts
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

get_header();
?>

<main id="primary" class="site-main">

	<?php
	while ( have_posts() ) :
		the_post();

		get_template_part( 'template-parts/content/content', get_post_type() );

		the_post_navigation(
			array(
				'prev_text' => '<span class="nav-subtitle">' . esc_html__( 'Previous:', 'skyyrose-flagship' ) . '</span> <span class="nav-title">%title</span>',
				'next_text' => '<span class="nav-subtitle">' . esc_html__( 'Next:', 'skyyrose-flagship' ) . '</span> <span class="nav-title">%title</span>',
			)
		);

		// If comments are open or we have at least one comment, load up the comment template.
		if ( comments_open() || get_comments_number() ) :
			comments_template();
		endif;

	endwhile; // End of the loop.
	?>

</main><!-- #primary -->

<?php
get_sidebar();
get_footer();
