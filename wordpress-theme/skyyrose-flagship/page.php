<?php
/**
 * The template for displaying all pages.
 *
 * Dark luxury page layout with brand-consistent typography
 * and spacing. Falls back to this for any page without a
 * custom page template assigned.
 *
 * @package SkyyRose_Flagship
 * @since   4.2.0
 */

get_header();
?>

<main id="primary" class="site-main skr-page" role="main" tabindex="-1">
	<div class="skr-page__inner">
		<?php
		while ( have_posts() ) :
			the_post();
		?>
		<article id="post-<?php the_ID(); ?>" <?php post_class( 'skr-page__article' ); ?>>
			<header class="skr-page__header">
				<?php the_title( '<h1 class="skr-page__title">', '</h1>' ); ?>
			</header>

			<div class="skr-page__content entry-content">
				<?php
				the_content();

				wp_link_pages( array(
					'before' => '<nav class="skr-page-links" aria-label="' . esc_attr__( 'Page navigation', 'skyyrose-flagship' ) . '">',
					'after'  => '</nav>',
				) );
				?>
			</div>
		</article>
		<?php
			if ( comments_open() || get_comments_number() ) :
				comments_template();
			endif;

		endwhile;
		?>
	</div>
</main>

<?php
get_footer();
