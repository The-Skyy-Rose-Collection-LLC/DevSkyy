<?php
/**
 * The main template file — blog index / archive.
 *
 * Dark luxury blog layout with card-based post grid
 * and brand-consistent typography.
 *
 * @package SkyyRose_Flagship
 * @since   4.2.0
 */

get_header();
?>

<main id="primary" class="site-main skr-blog" role="main" tabindex="-1">

	<header class="skr-blog__header">
		<?php if ( is_home() && ! is_front_page() ) : ?>
			<h1 class="skr-blog__title"><?php single_post_title(); ?></h1>
		<?php else : ?>
			<h1 class="skr-blog__title"><?php esc_html_e( 'Journal', 'skyyrose-flagship' ); ?></h1>
		<?php endif; ?>
		<p class="skr-blog__desc"><?php esc_html_e( 'Stories, drops, and behind-the-scenes from SkyyRose.', 'skyyrose-flagship' ); ?></p>
	</header>

	<?php if ( have_posts() ) : ?>
	<div class="skr-blog__grid">
		<?php
		while ( have_posts() ) :
			the_post();
		?>
		<article id="post-<?php the_ID(); ?>" <?php post_class( 'skr-blog-card' ); ?>>
			<?php if ( has_post_thumbnail() ) : ?>
			<a href="<?php the_permalink(); ?>" class="skr-blog-card__img" aria-hidden="true" tabindex="-1">
				<?php the_post_thumbnail( 'medium_large', array(
					'class'   => 'skr-blog-card__thumb',
					'loading' => 'lazy',
				) ); ?>
			</a>
			<?php endif; ?>
			<div class="skr-blog-card__body">
				<time datetime="<?php echo esc_attr( get_the_date( 'c' ) ); ?>" class="skr-blog-card__date">
					<?php echo esc_html( get_the_date() ); ?>
				</time>
				<?php the_title( '<h2 class="skr-blog-card__title"><a href="' . esc_url( get_permalink() ) . '">', '</a></h2>' ); ?>
				<div class="skr-blog-card__excerpt">
					<?php the_excerpt(); ?>
				</div>
				<a href="<?php the_permalink(); ?>" class="skr-blog-card__more">
					<?php esc_html_e( 'Read More', 'skyyrose-flagship' ); ?>
					<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
				</a>
			</div>
		</article>
		<?php endwhile; ?>
	</div>

	<nav class="skr-blog__pagination" aria-label="<?php esc_attr_e( 'Blog pagination', 'skyyrose-flagship' ); ?>">
		<?php the_posts_navigation( array(
			'prev_text' => esc_html__( 'Older Posts', 'skyyrose-flagship' ),
			'next_text' => esc_html__( 'Newer Posts', 'skyyrose-flagship' ),
		) ); ?>
	</nav>

	<?php else : ?>
	<div class="skr-blog__empty">
		<p><?php esc_html_e( 'No posts yet. Check back soon.', 'skyyrose-flagship' ); ?></p>
	</div>
	<?php endif; ?>

</main>

<?php
get_footer();
