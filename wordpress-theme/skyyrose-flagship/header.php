<?php
/**
 * SkyyRose Flagship — Luxury Header
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
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

	<!-- Top Bar -->
	<div class="top-bar">
		<div class="top-bar-container">
			<span class="top-bar-message">Where Love Meets Luxury&trade; &mdash; Free Shipping on Orders Over $500</span>
			<?php if ( has_nav_menu( 'top-bar' ) ) : ?>
				<?php
				wp_nav_menu(
					array(
						'theme_location' => 'top-bar',
						'menu_id'        => 'top-bar-menu',
						'container'      => 'nav',
						'container_class' => 'top-bar-nav',
						'depth'          => 1,
						'fallback_cb'    => false,
					)
				);
				?>
			<?php endif; ?>
		</div>
	</div>

	<header id="masthead" class="site-header">
		<div class="header-container">
			<!-- Logo / Brand -->
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
				?>
			</div>

			<!-- Primary Navigation -->
			<nav id="site-navigation" class="main-navigation" role="navigation" aria-label="<?php esc_attr_e( 'Primary Menu', 'skyyrose-flagship' ); ?>">
				<button class="menu-toggle" aria-controls="primary-menu" aria-expanded="false">
					<span class="hamburger-line"></span>
					<span class="hamburger-line"></span>
					<span class="hamburger-line"></span>
					<span class="screen-reader-text"><?php esc_html_e( 'Menu', 'skyyrose-flagship' ); ?></span>
				</button>

				<?php if ( has_nav_menu( 'primary' ) ) : ?>
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
				<?php else : ?>
					<!-- Fallback Navigation -->
					<div class="primary-menu-container">
						<ul id="primary-menu" class="menu">
							<li class="menu-item"><a href="<?php echo esc_url( home_url( '/' ) ); ?>">Home</a></li>
							<li class="menu-item menu-item-has-children">
								<a href="#">Collections</a>
								<ul class="sub-menu">
									<li class="menu-item collection-black-rose">
										<a href="<?php echo esc_url( home_url( '/black-rose-collection/' ) ); ?>">
											<span class="collection-dot" style="background:#C0C0C0;"></span>
											Black Rose
										</a>
									</li>
									<li class="menu-item collection-love-hurts">
										<a href="<?php echo esc_url( home_url( '/love-hurts-collection/' ) ); ?>">
											<span class="collection-dot" style="background:#DC143C;"></span>
											Love Hurts
										</a>
									</li>
									<li class="menu-item collection-signature">
										<a href="<?php echo esc_url( home_url( '/signature-collection/' ) ); ?>">
											<span class="collection-dot" style="background:#B76E79;"></span>
											Signature
										</a>
									</li>
								</ul>
							</li>
							<li class="menu-item"><a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>">Pre-Order</a></li>
							<li class="menu-item"><a href="<?php echo esc_url( home_url( '/about/' ) ); ?>">Our Story</a></li>
							<li class="menu-item"><a href="<?php echo esc_url( home_url( '/contact/' ) ); ?>">Contact</a></li>
						</ul>
					</div>
				<?php endif; ?>
			</nav>

			<!-- Header Actions -->
			<div class="header-actions">
				<?php if ( class_exists( 'WooCommerce' ) ) : ?>
					<a href="<?php echo esc_url( get_permalink( get_page_by_path( 'wishlist' ) ) ); ?>" class="header-action wishlist-link" aria-label="<?php esc_attr_e( 'Wishlist', 'skyyrose-flagship' ); ?>">
						<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
							<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
						</svg>
						<?php $wishlist_count = skyyrose_get_wishlist_count(); ?>
						<?php if ( $wishlist_count > 0 ) : ?>
							<span class="action-count"><?php echo esc_html( $wishlist_count ); ?></span>
						<?php endif; ?>
					</a>
					<a href="<?php echo esc_url( wc_get_cart_url() ); ?>" class="header-action cart-link" aria-label="<?php esc_attr_e( 'Cart', 'skyyrose-flagship' ); ?>">
						<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
							<path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/>
							<line x1="3" y1="6" x2="21" y2="6"/>
							<path d="M16 10a4 4 0 0 1-8 0"/>
						</svg>
						<?php $cart_count = WC()->cart->get_cart_contents_count(); ?>
						<?php if ( $cart_count > 0 ) : ?>
							<span class="action-count"><?php echo esc_html( $cart_count ); ?></span>
						<?php endif; ?>
					</a>
				<?php endif; ?>
			</div>

		</div>
	</header>

	<?php do_action( 'skyyrose_after_header' ); ?>

	<div id="content" class="site-content">
