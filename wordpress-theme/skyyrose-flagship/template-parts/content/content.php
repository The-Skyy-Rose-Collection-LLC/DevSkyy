<?php
/**
 * Default post card for blog and archive loops.
 *
 * @package SkyyRose
 * @since   2.1.0
 */

defined( 'ABSPATH' ) || exit;
?>

<article id="post-<?php the_ID(); ?>" <?php post_class( 'skr-blog-card' ); ?>>
	<?php if ( has_post_thumbnail() ) : ?>
		<a href="<?php the_permalink(); ?>" class="skr-blog-card__img" aria-hidden="true" tabindex="-1">
			<?php
			the_post_thumbnail(
				'medium_large',
				array(
					'class'   => 'skr-blog-card__thumb',
					'loading' => 'lazy',
				)
			);
			?>
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
			<?php esc_html_e( 'Read More', 'skyyrose' ); ?>
			<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
		</a>
	</div>
</article>
