<?php
/**
 * The main template file
 *
 * This is the most generic template file in a WordPress theme
 * and one of the two required files for a theme (the other being style.css).
 * It is used to display a page when nothing more specific matches a query.
 * E.g., it puts together the home page when no home.php file exists.
 *
 * @link https://developer.wordpress.org/themes/basics/template-hierarchy/
 *
 * @package WP_Mastery_Boilerplate
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
	exit;
}

get_header();
?>

<main id="main" class="site-main">
	<div class="container">
		<div class="content-area">
			<?php if (have_posts()) : ?>

				<?php if (is_home() && !is_front_page()) : ?>
					<header class="page-header">
						<h1 class="page-title screen-reader-text"><?php single_post_title(); ?></h1>
					</header>
				<?php endif; ?>

				<?php
				// Start the Loop
				while (have_posts()) :
					the_post();
					?>

					<article id="post-<?php the_ID(); ?>" <?php post_class('entry'); ?>>
						<header class="entry-header">
							<?php
							if (is_singular()) :
								the_title('<h1 class="entry-title">', '</h1>');
							else :
								the_title('<h2 class="entry-title"><a href="' . esc_url(get_permalink()) . '" rel="bookmark">', '</a></h2>');
							endif;

							if ('post' === get_post_type()) :
								?>
								<div class="entry-meta">
									<?php
									wp_mastery_boilerplate_posted_on();
									echo ' ';
									wp_mastery_boilerplate_posted_by();
									?>
								</div><!-- .entry-meta -->
							<?php endif; ?>
						</header><!-- .entry-header -->

						<?php if (has_post_thumbnail() && !is_singular()) : ?>
							<div class="post-thumbnail">
								<a href="<?php the_permalink(); ?>" aria-hidden="true" tabindex="-1">
									<?php
									the_post_thumbnail('post-thumbnail', array(
										'alt' => the_title_attribute(array(
											'echo' => false,
										)),
									));
									?>
								</a>
							</div><!-- .post-thumbnail -->
						<?php endif; ?>

						<div class="entry-content">
							<?php
							if (is_singular() || is_search()) {
								the_content(sprintf(
									wp_kses(
										/* translators: %s: Name of current post. Only visible to screen readers */
										__('Continue reading<span class="screen-reader-text"> "%s"</span>', 'wp-mastery-boilerplate'),
										array(
											'span' => array(
												'class' => array(),
											),
										)
									),
									wp_kses_post(get_the_title())
								));

								wp_link_pages(array(
									'before' => '<div class="page-links">' . esc_html__('Pages:', 'wp-mastery-boilerplate'),
									'after'  => '</div>',
								));
							} else {
								the_excerpt();
							}
							?>
						</div><!-- .entry-content -->

						<?php if (is_singular()) : ?>
							<footer class="entry-footer">
								<?php
								$categories_list = get_the_category_list(esc_html__(', ', 'wp-mastery-boilerplate'));
								if ($categories_list) {
									/* translators: 1: list of categories. */
									printf('<span class="cat-links">' . esc_html__('Posted in %1$s', 'wp-mastery-boilerplate') . '</span>', $categories_list);
								}

								$tags_list = get_the_tag_list('', esc_html_x(', ', 'list item separator', 'wp-mastery-boilerplate'));
								if ($tags_list) {
									/* translators: 1: list of tags. */
									printf('<span class="tags-links">' . esc_html__('Tagged %1$s', 'wp-mastery-boilerplate') . '</span>', $tags_list);
								}

								if (!is_single() && !post_password_required() && (comments_open() || get_comments_number())) {
									echo '<span class="comments-link">';
									comments_popup_link(
										sprintf(
											wp_kses(
												/* translators: %s: post title */
												__('Leave a Comment<span class="screen-reader-text"> on %s</span>', 'wp-mastery-boilerplate'),
												array(
													'span' => array(
														'class' => array(),
													),
												)
											),
											wp_kses_post(get_the_title())
										)
									);
									echo '</span>';
								}

								edit_post_link(
									sprintf(
										wp_kses(
											/* translators: %s: Name of current post. Only visible to screen readers */
											__('Edit <span class="screen-reader-text">%s</span>', 'wp-mastery-boilerplate'),
											array(
												'span' => array(
													'class' => array(),
												),
											)
										),
										wp_kses_post(get_the_title())
									),
									'<span class="edit-link">',
									'</span>'
								);
								?>
							</footer><!-- .entry-footer -->
						<?php endif; ?>
					</article><!-- #post-<?php the_ID(); ?> -->

					<?php
					// If comments are open or we have at least one comment, load up the comment template.
					if (is_singular() && (comments_open() || get_comments_number())) :
						comments_template();
					endif;

				endwhile;

				// Previous/next page navigation
				the_posts_navigation(array(
					'prev_text' => esc_html__('&larr; Older posts', 'wp-mastery-boilerplate'),
					'next_text' => esc_html__('Newer posts &rarr;', 'wp-mastery-boilerplate'),
				));

			else :
				?>

				<section class="no-results not-found">
					<header class="page-header">
						<h1 class="page-title"><?php esc_html_e('Nothing here', 'wp-mastery-boilerplate'); ?></h1>
					</header><!-- .page-header -->

					<div class="page-content">
						<?php
						if (is_home() && current_user_can('publish_posts')) :
							printf(
								'<p>' . wp_kses(
									/* translators: 1: link to WP admin new post page. */
									__('Ready to publish your first post? <a href="%1$s">Get started here</a>.', 'wp-mastery-boilerplate'),
									array(
										'a' => array(
											'href' => array(),
										),
									)
								) . '</p>',
								esc_url(admin_url('post-new.php'))
							);

						elseif (is_search()) :
							?>

							<p><?php esc_html_e('Sorry, but nothing matched your search terms. Please try again with some different keywords.', 'wp-mastery-boilerplate'); ?></p>
							<?php
							get_search_form();

						else :
							?>

							<p><?php esc_html_e('It seems we can&rsquo;t find what you&rsquo;re looking for. Perhaps searching can help.', 'wp-mastery-boilerplate'); ?></p>
							<?php
							get_search_form();

						endif;
						?>
					</div><!-- .page-content -->
				</section><!-- .no-results -->

			<?php endif; ?>
		</div><!-- .content-area -->
	</div><!-- .container -->
</main><!-- #main -->

<?php
get_footer();
