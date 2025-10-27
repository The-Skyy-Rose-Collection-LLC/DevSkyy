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
 * @package WP_Mastery_WooCommerce_Luxury
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
		<?php if (is_home() && is_front_page() && wp_mastery_woocommerce_luxury_is_woocommerce_active()) : ?>
			<!-- Luxury eCommerce Homepage Hero Section -->
			<section class="luxury-hero">
				<div class="luxury-hero-content">
					<h1 class="luxury-hero-title">
						<?php 
						$hero_title = get_theme_mod('luxury_hero_title', get_bloginfo('name'));
						echo esc_html($hero_title);
						?>
					</h1>
					<p class="luxury-hero-subtitle">
						<?php 
						$hero_subtitle = get_theme_mod('luxury_hero_subtitle', get_bloginfo('description'));
						echo esc_html($hero_subtitle);
						?>
					</p>
					<div class="luxury-hero-actions">
						<a href="<?php echo esc_url(wc_get_page_permalink('shop')); ?>" class="btn-luxury">
							<?php esc_html_e('Explore Collection', 'wp-mastery-woocommerce-luxury'); ?>
						</a>
					</div>
				</div>
			</section>

			<?php if (function_exists('woocommerce_output_featured_products')) : ?>
				<!-- Featured Products Section -->
				<section class="luxury-featured-products">
					<div class="container-narrow">
						<header class="section-header">
							<h2 class="section-title"><?php esc_html_e('Featured Collection', 'wp-mastery-woocommerce-luxury'); ?></h2>
							<hr class="luxury-divider">
						</header>
						
						<?php
						// Display featured products
						echo do_shortcode('[featured_products limit="4" columns="2"]');
						?>
						
						<div class="section-footer text-center">
							<a href="<?php echo esc_url(wc_get_page_permalink('shop')); ?>" class="btn-luxury">
								<?php esc_html_e('View All Products', 'wp-mastery-woocommerce-luxury'); ?>
							</a>
						</div>
					</div>
				</section>
			<?php endif; ?>

		<?php endif; ?>

		<div class="content-area">
			<?php if (have_posts()) : ?>

				<?php if (is_home() && !is_front_page()) : ?>
					<header class="page-header">
						<h1 class="page-title screen-reader-text"><?php single_post_title(); ?></h1>
					</header>
				<?php endif; ?>

				<?php if (!is_front_page() || !wp_mastery_woocommerce_luxury_is_woocommerce_active()) : ?>
					<div class="posts-container">
						<?php
						// Start the Loop
						while (have_posts()) :
							the_post();
							?>

							<article id="post-<?php the_ID(); ?>" <?php post_class('entry luxury-post'); ?>>
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
											<time class="entry-date published updated" datetime="<?php echo esc_attr(get_the_date(DATE_W3C)); ?>">
												<?php echo esc_html(get_the_date()); ?>
											</time>
											<?php if (get_the_author()) : ?>
												<span class="author-meta">
													<?php esc_html_e('by', 'wp-mastery-woocommerce-luxury'); ?>
													<a href="<?php echo esc_url(get_author_posts_url(get_the_author_meta('ID'))); ?>" class="author-link">
														<?php echo esc_html(get_the_author()); ?>
													</a>
												</span>
											<?php endif; ?>
										</div><!-- .entry-meta -->
									<?php endif; ?>
								</header><!-- .entry-header -->

								<?php if (has_post_thumbnail() && !is_singular()) : ?>
									<div class="post-thumbnail">
										<a href="<?php the_permalink(); ?>" aria-hidden="true" tabindex="-1">
											<?php
											the_post_thumbnail('luxury-gallery', array(
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
												__('Continue reading<span class="screen-reader-text"> "%s"</span>', 'wp-mastery-woocommerce-luxury'),
												array(
													'span' => array(
														'class' => array(),
													),
												)
											),
											wp_kses_post(get_the_title())
										));

										wp_link_pages(array(
											'before' => '<div class="page-links">' . esc_html__('Pages:', 'wp-mastery-woocommerce-luxury'),
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
										$categories_list = get_the_category_list(esc_html__(', ', 'wp-mastery-woocommerce-luxury'));
										if ($categories_list) {
											/* translators: 1: list of categories. */
											printf('<span class="cat-links luxury-accent">' . esc_html__('Posted in %1$s', 'wp-mastery-woocommerce-luxury') . '</span>', $categories_list);
										}

										$tags_list = get_the_tag_list('', esc_html_x(', ', 'list item separator', 'wp-mastery-woocommerce-luxury'));
										if ($tags_list) {
											/* translators: 1: list of tags. */
											printf('<span class="tags-links luxury-accent">' . esc_html__('Tagged %1$s', 'wp-mastery-woocommerce-luxury') . '</span>', $tags_list);
										}

										if (!is_single() && !post_password_required() && (comments_open() || get_comments_number())) {
											echo '<span class="comments-link">';
											comments_popup_link(
												sprintf(
													wp_kses(
														/* translators: %s: post title */
														__('Leave a Comment<span class="screen-reader-text"> on %s</span>', 'wp-mastery-woocommerce-luxury'),
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
													__('Edit <span class="screen-reader-text">%s</span>', 'wp-mastery-woocommerce-luxury'),
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
							'prev_text' => esc_html__('&larr; Previous Posts', 'wp-mastery-woocommerce-luxury'),
							'next_text' => esc_html__('Next Posts &rarr;', 'wp-mastery-woocommerce-luxury'),
						));
						?>
					</div><!-- .posts-container -->
				<?php endif; ?>

			<?php else : ?>

				<section class="no-results not-found">
					<header class="page-header">
						<h1 class="page-title"><?php esc_html_e('Nothing Found', 'wp-mastery-woocommerce-luxury'); ?></h1>
					</header><!-- .page-header -->

					<div class="page-content">
						<?php
						if (is_home() && current_user_can('publish_posts')) :
							printf(
								'<p>' . wp_kses(
									/* translators: 1: link to WP admin new post page. */
									__('Ready to publish your first post? <a href="%1$s">Get started here</a>.', 'wp-mastery-woocommerce-luxury'),
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

							<p><?php esc_html_e('Sorry, but nothing matched your search terms. Please try again with different keywords.', 'wp-mastery-woocommerce-luxury'); ?></p>
							<?php
							get_search_form();

						else :
							?>

							<p><?php esc_html_e('It seems we can&rsquo;t find what you&rsquo;re looking for. Perhaps searching can help.', 'wp-mastery-woocommerce-luxury'); ?></p>
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
