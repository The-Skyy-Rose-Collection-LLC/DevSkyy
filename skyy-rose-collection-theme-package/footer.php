<?php
/**
 * The template for displaying the footer
 *
 * Contains the closing of the #content div and all content after.
 *
 * @link https://developer.wordpress.org/themes/basics/template-files/#template-partials
 *
 * @package WP_Mastery_WooCommerce_Luxury
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
	exit;
}
?>

	<footer id="colophon" class="site-footer">
		<div class="container">
			<div class="footer-content">
				<div class="footer-section footer-about">
					<h3 class="footer-title"><?php bloginfo('name'); ?></h3>
					<p class="footer-description">
						<?php 
						$footer_description = get_theme_mod('footer_description', get_bloginfo('description'));
						echo esc_html($footer_description);
						?>
					</p>
					
					<?php if (wp_mastery_woocommerce_luxury_is_woocommerce_active()) : ?>
						<div class="footer-contact">
							<?php 
							$contact_info = get_theme_mod('footer_contact_info', '');
							if ($contact_info) :
								echo '<p>' . esc_html($contact_info) . '</p>';
							endif;
							?>
						</div>
					<?php endif; ?>
				</div>

				<?php if (wp_mastery_woocommerce_luxury_is_woocommerce_active()) : ?>
					<div class="footer-section footer-shop">
						<h3 class="footer-title"><?php esc_html_e('Shop', 'wp-mastery-woocommerce-luxury'); ?></h3>
						<ul class="footer-links">
							<li><a href="<?php echo esc_url(wc_get_page_permalink('shop')); ?>"><?php esc_html_e('All Products', 'wp-mastery-woocommerce-luxury'); ?></a></li>
							<?php
							// Get product categories
							$product_categories = get_terms(array(
								'taxonomy' => 'product_cat',
								'hide_empty' => true,
								'number' => 4,
							));
							
							if (!is_wp_error($product_categories) && !empty($product_categories)) :
								foreach ($product_categories as $category) :
									?>
									<li><a href="<?php echo esc_url(get_term_link($category)); ?>"><?php echo esc_html($category->name); ?></a></li>
									<?php
								endforeach;
							endif;
							?>
						</ul>
					</div>

					<div class="footer-section footer-account">
						<h3 class="footer-title"><?php esc_html_e('Customer Care', 'wp-mastery-woocommerce-luxury'); ?></h3>
						<ul class="footer-links">
							<li><a href="<?php echo esc_url(wc_get_page_permalink('myaccount')); ?>"><?php esc_html_e('My Account', 'wp-mastery-woocommerce-luxury'); ?></a></li>
							<li><a href="<?php echo esc_url(wc_get_page_permalink('cart')); ?>"><?php esc_html_e('Shopping Cart', 'wp-mastery-woocommerce-luxury'); ?></a></li>
							<li><a href="<?php echo esc_url(wc_get_page_permalink('checkout')); ?>"><?php esc_html_e('Checkout', 'wp-mastery-woocommerce-luxury'); ?></a></li>
							<?php if (get_option('woocommerce_terms_page_id')) : ?>
								<li><a href="<?php echo esc_url(get_permalink(get_option('woocommerce_terms_page_id'))); ?>"><?php esc_html_e('Terms & Conditions', 'wp-mastery-woocommerce-luxury'); ?></a></li>
							<?php endif; ?>
							<?php if (get_option('woocommerce_privacy_policy_page_id')) : ?>
								<li><a href="<?php echo esc_url(get_permalink(get_option('woocommerce_privacy_policy_page_id'))); ?>"><?php esc_html_e('Privacy Policy', 'wp-mastery-woocommerce-luxury'); ?></a></li>
							<?php endif; ?>
						</ul>
					</div>
				<?php endif; ?>

				<div class="footer-section footer-info">
					<h3 class="footer-title"><?php esc_html_e('Information', 'wp-mastery-woocommerce-luxury'); ?></h3>
					<?php if (has_nav_menu('footer')) : ?>
						<nav class="footer-navigation" role="navigation" aria-label="<?php esc_attr_e('Footer Menu', 'wp-mastery-woocommerce-luxury'); ?>">
							<?php
							wp_nav_menu(array(
								'theme_location' => 'footer',
								'menu_id'        => 'footer-menu',
								'container'      => false,
								'depth'          => 1,
								'menu_class'     => 'footer-links',
							));
							?>
						</nav><!-- .footer-navigation -->
					<?php else : ?>
						<ul class="footer-links">
							<li><a href="<?php echo esc_url(home_url('/about/')); ?>"><?php esc_html_e('About Us', 'wp-mastery-woocommerce-luxury'); ?></a></li>
							<li><a href="<?php echo esc_url(home_url('/contact/')); ?>"><?php esc_html_e('Contact', 'wp-mastery-woocommerce-luxury'); ?></a></li>
							<li><a href="<?php echo esc_url(home_url('/blog/')); ?>"><?php esc_html_e('Blog', 'wp-mastery-woocommerce-luxury'); ?></a></li>
						</ul>
					<?php endif; ?>

					<?php
					// Social media links
					$social_links = array(
						'facebook' => get_theme_mod('social_facebook', ''),
						'instagram' => get_theme_mod('social_instagram', ''),
						'twitter' => get_theme_mod('social_twitter', ''),
						'pinterest' => get_theme_mod('social_pinterest', ''),
					);
					
					$has_social = array_filter($social_links);
					if (!empty($has_social)) :
						?>
						<div class="footer-social">
							<h4 class="social-title"><?php esc_html_e('Follow Us', 'wp-mastery-woocommerce-luxury'); ?></h4>
							<div class="social-links">
								<?php foreach ($social_links as $platform => $url) : ?>
									<?php if ($url) : ?>
										<a href="<?php echo esc_url($url); ?>" class="social-link social-<?php echo esc_attr($platform); ?>" target="_blank" rel="noopener noreferrer">
											<span class="screen-reader-text"><?php echo esc_html(ucfirst($platform)); ?></span>
											<span class="social-icon" aria-hidden="true">
												<?php
												switch ($platform) {
													case 'facebook':
														echo '📘';
														break;
													case 'instagram':
														echo '📷';
														break;
													case 'twitter':
														echo '🐦';
														break;
													case 'pinterest':
														echo '📌';
														break;
												}
												?>
											</span>
										</a>
									<?php endif; ?>
								<?php endforeach; ?>
							</div>
						</div>
					<?php endif; ?>
				</div>
			</div><!-- .footer-content -->

			<div class="footer-bottom">
				<div class="site-info">
					<p>
						&copy; <?php echo esc_html(date('Y')); ?> 
						<a href="<?php echo esc_url(home_url('/')); ?>"><?php bloginfo('name'); ?></a>. 
						<?php esc_html_e('All rights reserved.', 'wp-mastery-woocommerce-luxury'); ?>
					</p>
					<p class="luxury-accent">
						<?php esc_html_e('Luxury Fashion Redefined', 'wp-mastery-woocommerce-luxury'); ?>
					</p>
					<p class="theme-credit">
						<?php
						/* translators: 1: Theme name, 2: Theme author. */
						printf(esc_html__('Theme: %1$s by %2$s.', 'wp-mastery-woocommerce-luxury'), 'WordPress Mastery WooCommerce Luxury', '<a href="https://devskyy.com">DevSkyy</a>');
						?>
					</p>
				</div><!-- .site-info -->

				<?php if (wp_mastery_woocommerce_luxury_is_woocommerce_active()) : ?>
					<div class="footer-payments">
						<p class="payments-text"><?php esc_html_e('We Accept:', 'wp-mastery-woocommerce-luxury'); ?></p>
						<div class="payment-icons">
							<span class="payment-icon" aria-label="<?php esc_attr_e('Visa', 'wp-mastery-woocommerce-luxury'); ?>">💳</span>
							<span class="payment-icon" aria-label="<?php esc_attr_e('Mastercard', 'wp-mastery-woocommerce-luxury'); ?>">💳</span>
							<span class="payment-icon" aria-label="<?php esc_attr_e('American Express', 'wp-mastery-woocommerce-luxury'); ?>">💳</span>
							<span class="payment-icon" aria-label="<?php esc_attr_e('PayPal', 'wp-mastery-woocommerce-luxury'); ?>">💰</span>
						</div>
					</div>
				<?php endif; ?>
			</div><!-- .footer-bottom -->
		</div><!-- .container -->
	</footer><!-- #colophon -->
</div><!-- #page -->

<?php wp_footer(); ?>

</body>
</html>
