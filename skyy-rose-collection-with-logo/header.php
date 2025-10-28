<?php
/**
 * The header for our luxury eCommerce theme
 *
 * This is the template that displays all of the <head> section and everything up until <div id="content">
 *
 * @link https://developer.wordpress.org/themes/basics/template-files/#template-partials
 *
 * @package Skyy_Rose_Collection
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
	exit;
}
?>
<!doctype html>
<html <?php language_attributes(); ?>>
<head>
	<meta charset="<?php bloginfo('charset'); ?>">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<link rel="profile" href="https://gmpg.org/xfn/11">
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

	<?php wp_head(); ?>
</head>

<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<div id="page" class="site">
	<a class="skip-link screen-reader-text" href="#main"><?php esc_html_e('Skip to content', 'wp-mastery-woocommerce-luxury'); ?></a>

	<header id="masthead" class="site-header">
		<div class="container">
			<div class="header-top">
				<?php if (wp_mastery_woocommerce_luxury_is_woocommerce_active()) : ?>
					<div class="header-utilities">
						<div class="header-search">
							<?php if (function_exists('get_product_search_form')) : ?>
								<?php get_product_search_form(); ?>
							<?php else : ?>
								<?php get_search_form(); ?>
							<?php endif; ?>
						</div>
						
						<div class="header-account">
							<?php if (is_user_logged_in()) : ?>
								<a href="<?php echo esc_url(wc_get_page_permalink('myaccount')); ?>" class="account-link">
									<span class="account-icon" aria-hidden="true">👤</span>
									<span class="account-text"><?php esc_html_e('My Account', 'wp-mastery-woocommerce-luxury'); ?></span>
								</a>
							<?php else : ?>
								<a href="<?php echo esc_url(wc_get_page_permalink('myaccount')); ?>" class="account-link">
									<span class="account-icon" aria-hidden="true">👤</span>
									<span class="account-text"><?php esc_html_e('Login', 'wp-mastery-woocommerce-luxury'); ?></span>
								</a>
							<?php endif; ?>
						</div>
						
						<div class="header-cart">
							<a href="<?php echo esc_url(wc_get_cart_url()); ?>" class="cart-link">
								<span class="cart-icon" aria-hidden="true">🛍️</span>
								<span class="cart-text"><?php esc_html_e('Cart', 'wp-mastery-woocommerce-luxury'); ?></span>
								<span class="cart-count"><?php echo esc_html(WC()->cart->get_cart_contents_count()); ?></span>
							</a>
						</div>
					</div>
				<?php endif; ?>
			</div>

			<div class="header-main">
				<div class="site-branding">
					<?php if (has_custom_logo()) : ?>
						<div class="custom-logo-container">
							<?php the_custom_logo(); ?>
						</div>
					<?php else : ?>
						<?php
						// Display Skyy Rose Collection GIF Logo
						if (function_exists('skyy_rose_get_logo_html')) {
							echo skyy_rose_get_logo_html(); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
						} else {
							// Fallback if function doesn't exist
							?>
							<div class="skyy-rose-logo-container">
								<a href="<?php echo esc_url(home_url('/')); ?>" rel="home" class="skyy-rose-logo-link" aria-label="<?php echo esc_attr(get_bloginfo('name')); ?> - <?php esc_attr_e('Go to homepage', 'skyy-rose-collection'); ?>">
									<img src="<?php echo esc_url(get_template_directory_uri() . '/assets/images/TSRC-logo-60h.gif'); ?>"
										 alt="<?php echo esc_attr(get_bloginfo('name')); ?>"
										 class="skyy-rose-logo-gif"
										 width="60"
										 height="60"
										 loading="eager">
									<span class="skyy-rose-logo-text">
										<?php if (is_front_page() && is_home()) : ?>
											<span class="site-title-h1"><?php bloginfo('name'); ?></span>
										<?php else : ?>
											<span class="site-title"><?php bloginfo('name'); ?></span>
										<?php endif; ?>
									</span>
								</a>
							</div>
							<?php
						}
						?>
					<?php endif; ?>

					<?php
					$skyy_rose_description = get_bloginfo('description', 'display');
					if ($skyy_rose_description || is_customize_preview()) :
						?>
						<p class="site-description"><?php echo esc_html($skyy_rose_description); ?></p>
					<?php endif; ?>
				</div><!-- .site-branding -->

				<nav id="site-navigation" class="main-navigation" role="navigation" aria-label="<?php esc_attr_e('Primary Menu', 'wp-mastery-woocommerce-luxury'); ?>">
					<?php
					if (has_nav_menu('primary')) {
						wp_nav_menu(array(
							'theme_location' => 'primary',
							'menu_id'        => 'primary-menu',
							'container'      => false,
							'depth'          => 2,
						));
					} else {
						wp_mastery_woocommerce_luxury_fallback_menu();
					}
					?>
				</nav><!-- #site-navigation -->
			</div><!-- .header-main -->

			<?php if (wp_mastery_woocommerce_luxury_is_woocommerce_active() && (is_shop() || is_product_category() || is_product_tag())) : ?>
				<div class="header-breadcrumbs">
					<?php woocommerce_breadcrumb(); ?>
				</div>
			<?php endif; ?>
		</div><!-- .container -->
	</header><!-- #masthead -->
