<?php
/**
 * The main template file — blog index / archive.
 *
 * Dark luxury blog layout with card-based post grid
 * and brand-consistent typography.
 *
 * @package SkyyRose
 * @since   4.2.0
 */

get_header();
?>

<main id="primary" class="site-main skr-blog" role="main" tabindex="-1">

	<header class="skr-blog__header">
		<?php if ( is_home() && ! is_front_page() ) : ?>
			<h1 class="skr-blog__title"><?php single_post_title(); ?></h1>
		<?php else : ?>
			<h1 class="skr-blog__title"><?php esc_html_e( 'Journal', 'skyyrose' ); ?></h1>
		<?php endif; ?>
		<p class="skr-blog__desc"><?php esc_html_e( 'Stories, drops, and behind-the-scenes from SkyyRose.', 'skyyrose' ); ?></p>
	</header>

	<?php if ( have_posts() ) : ?>
	<div class="skr-blog__grid">
		<?php
		while ( have_posts() ) :
			the_post();
			get_template_part( 'template-parts/content/content', get_post_type() );
		endwhile;
		?>
	</div>

	<nav class="skr-blog__pagination" aria-label="<?php esc_attr_e( 'Blog pagination', 'skyyrose' ); ?>">
		<?php
		the_posts_navigation(
			array(
				'prev_text' => esc_html__( 'Older Posts', 'skyyrose' ),
				'next_text' => esc_html__( 'Newer Posts', 'skyyrose' ),
			)
		);
		?>
	</nav>

	<?php else : ?>
	<div class="skr-blog__empty">
		<p><?php esc_html_e( 'No posts yet. Check back soon.', 'skyyrose' ); ?></p>
	</div>
	<?php endif; ?>

</main>

<?php
get_footer();
