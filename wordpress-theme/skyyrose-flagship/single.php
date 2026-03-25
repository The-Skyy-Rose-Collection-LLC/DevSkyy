<?php
/**
 * The template for displaying single posts.
 *
 * Dark luxury single post layout with brand typography,
 * featured image hero, post navigation, and author info.
 *
 * @package SkyyRose_Flagship
 * @since   4.2.0
 */

get_header();
?>

<main id="primary" class="site-main skr-single" role="main" tabindex="-1">

	<?php while ( have_posts() ) : the_post(); ?>

	<article id="post-<?php the_ID(); ?>" <?php post_class( 'skr-single__article' ); ?>>

		<!-- Hero / Featured Image -->
		<?php if ( has_post_thumbnail() ) : ?>
		<div class="skr-single__hero">
			<?php the_post_thumbnail( 'full', array(
				'class'    => 'skr-single__hero-img',
				'loading'  => 'eager',
				'decoding' => 'async',
			) ); ?>
			<div class="skr-single__hero-overlay"></div>
		</div>
		<?php endif; ?>

		<div class="skr-single__inner">
			<header class="skr-single__header">
				<div class="skr-single__meta">
					<time datetime="<?php echo esc_attr( get_the_date( 'c' ) ); ?>" class="skr-single__date">
						<?php echo esc_html( get_the_date() ); ?>
					</time>
					<?php
					$categories = get_the_category();
					if ( ! empty( $categories ) ) :
					?>
					<span class="skr-single__cat">
						<?php echo esc_html( $categories[0]->name ); ?>
					</span>
					<?php endif; ?>
				</div>
				<?php the_title( '<h1 class="skr-single__title">', '</h1>' ); ?>
			</header>

			<div class="skr-single__content entry-content">
				<?php
				the_content();

				wp_link_pages( array(
					'before' => '<nav class="skr-page-links" aria-label="' . esc_attr__( 'Page navigation', 'skyyrose-flagship' ) . '">',
					'after'  => '</nav>',
				) );
				?>
			</div>

			<!-- Post Navigation -->
			<nav class="skr-single__nav" aria-label="<?php esc_attr_e( 'Post navigation', 'skyyrose-flagship' ); ?>">
				<?php
				the_post_navigation( array(
					'prev_text' => '<span class="skr-single__nav-label">' . esc_html__( 'Previous', 'skyyrose-flagship' ) . '</span><span class="skr-single__nav-title">%title</span>',
					'next_text' => '<span class="skr-single__nav-label">' . esc_html__( 'Next', 'skyyrose-flagship' ) . '</span><span class="skr-single__nav-title">%title</span>',
				) );
				?>
			</nav>
		</div>
	</article>

	<?php
		if ( comments_open() || get_comments_number() ) :
			comments_template();
		endif;

	endwhile;
	?>

</main>

<?php
get_footer();
