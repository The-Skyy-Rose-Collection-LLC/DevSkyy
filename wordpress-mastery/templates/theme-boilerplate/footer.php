<?php
/**
 * The template for displaying the footer
 *
 * Contains the closing of the #content div and all content after.
 *
 * @link https://developer.wordpress.org/themes/basics/template-files/#template-partials
 *
 * @package WP_Mastery_Boilerplate
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
	exit;
}

?>

	<footer id="colophon" class="site-footer">
		<div class="container">
			<?php if (has_nav_menu('footer')) : ?>
				<nav class="footer-navigation" role="navigation" aria-label="<?php esc_attr_e('Footer Menu', 'wp-mastery-boilerplate'); ?>">
					<?php
					wp_nav_menu(array(
						'theme_location' => 'footer',
						'menu_id'        => 'footer-menu',
						'container'      => false,
						'depth'          => 1,
					));
					?>
				</nav><!-- .footer-navigation -->
			<?php endif; ?>

			<div class="site-info">
				<p>
					<?php
					/* translators: 1: Theme name, 2: Theme author. */
					printf(esc_html__('Theme: %1$s by %2$s.', 'wp-mastery-boilerplate'), 'WordPress Mastery Boilerplate', '<a href="https://devskyy.com">DevSkyy</a>');
					?>
				</p>
				<p>
					&copy; <?php echo esc_html(date('Y')); ?> 
					<a href="<?php echo esc_url(home_url('/')); ?>"><?php bloginfo('name'); ?></a>. 
					<?php esc_html_e('All rights reserved.', 'wp-mastery-boilerplate'); ?>
				</p>
			</div><!-- .site-info -->
		</div><!-- .container -->
	</footer><!-- #colophon -->
</div><!-- #page -->

<?php wp_footer(); ?>

</body>
</html>
