<?php
/**
 * The header for the theme
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

?><!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
	<meta charset="<?php bloginfo( 'charset' ); ?>">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<link rel="profile" href="https://gmpg.org/xfn/11">
	<?php wp_head(); ?>
</head>

<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<div id="page" class="site">
	<a class="skip-link screen-reader-text" href="#primary"><?php esc_html_e( 'Skip to content', 'skyyrose-flagship' ); ?></a>

	<header id="masthead" class="site-header">
		<div class="header-container">
			<div class="site-branding">
				<?php
				the_custom_logo();
				if ( is_front_page() && is_home() ) :
					?>
					<h1 class="site-title"><a href="<?php echo esc_url( home_url( '/' ) ); ?>" rel="home"><?php bloginfo( 'name' ); ?></a></h1>
					<?php
				else :
					?>
					<p class="site-title"><a href="<?php echo esc_url( home_url( '/' ) ); ?>" rel="home"><?php bloginfo( 'name' ); ?></a></p>
					<?php
				endif;
				$skyyrose_description = get_bloginfo( 'description', 'display' );
				if ( $skyyrose_description || is_customize_preview() ) :
					?>
					<p class="site-description"><?php echo $skyyrose_description; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></p>
				<?php endif; ?>
			</div><!-- .site-branding -->

			<nav id="site-navigation" class="main-navigation">
				<button class="menu-toggle" aria-controls="primary-menu" aria-expanded="false">
					<span class="menu-toggle-icon"></span>
					<span class="screen-reader-text"><?php esc_html_e( 'Menu', 'skyyrose-flagship' ); ?></span>
				</button>
				<?php
				wp_nav_menu(
					array(
						'theme_location' => 'primary',
						'menu_id'        => 'primary-menu',
						'container'      => 'div',
						'container_class' => 'primary-menu-container',
						'fallback_cb'    => false,
					)
				);
				?>
			</nav><!-- #site-navigation -->

			<?php if ( class_exists( 'WooCommerce' ) ) : ?>
				<div class="header-actions">
					<div class="header-wishlist">
						<a href="<?php echo esc_url( get_permalink( get_page_by_path( 'wishlist' ) ) ); ?>" class="wishlist-link">
							<svg class="wishlist-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
								<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
							</svg>
							<span class="wishlist-count <?php echo skyyrose_get_wishlist_count() > 0 ? 'has-items' : ''; ?>"><?php echo esc_html( skyyrose_get_wishlist_count() ); ?></span>
						</a>
					</div>
					<div class="header-cart">
						<a href="<?php echo esc_url( wc_get_cart_url() ); ?>" class="cart-contents">
							<span class="cart-icon"></span>
							<span class="cart-count"><?php echo wp_kses_data( WC()->cart->get_cart_contents_count() ); ?></span>
						</a>
					</div>
				</div>
			<?php endif; ?>

		</div><!-- .header-container -->
	</header><!-- #masthead -->

	<?php
	/**
	 * Hook: skyyrose_after_header
	 *
	 * @hooked skyyrose_breadcrumb - 10
	 */
	do_action( 'skyyrose_after_header' );
	?>

	<div id="content" class="site-content">
