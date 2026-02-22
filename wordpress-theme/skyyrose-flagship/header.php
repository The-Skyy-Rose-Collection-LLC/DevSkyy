<?php
/**
 * The header for the SkyyRose Flagship theme
 *
 * Displays the fixed dark navbar with SR monogram logo, gradient text branding,
 * navigation with collections dropdown, icon buttons, and mobile hamburger menu.
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
	<a class="skip-link screen-reader-text" href="#primary">
		<?php esc_html_e( 'Skip to content', 'skyyrose-flagship' ); ?>
	</a>

	<header id="masthead" class="site-header" role="banner">
		<nav class="navbar" id="navbar" aria-label="<?php esc_attr_e( 'Primary Navigation', 'skyyrose-flagship' ); ?>">
			<div class="navbar__container">

				<!-- Logo / Brand -->
				<div class="navbar__brand">
					<a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="navbar__logo-link" rel="home" aria-label="<?php esc_attr_e( 'SkyyRose Home', 'skyyrose-flagship' ); ?>">
						<img
							src="<?php echo esc_url( get_template_directory_uri() . '/assets/images/sr-monogram.png' ); ?>"
							alt="<?php esc_attr_e( 'SR Monogram', 'skyyrose-flagship' ); ?>"
							class="navbar__monogram"
							width="48"
							height="48"
							loading="eager"
						>
						<span class="navbar__brand-text">
							<?php if ( is_front_page() && is_home() ) : ?>
								<h1 class="navbar__site-title">
									<span class="navbar__gradient-text"><?php esc_html_e( 'SKYY ROSE', 'skyyrose-flagship' ); ?></span>
								</h1>
							<?php else : ?>
								<span class="navbar__site-title">
									<span class="navbar__gradient-text"><?php esc_html_e( 'SKYY ROSE', 'skyyrose-flagship' ); ?></span>
								</span>
							<?php endif; ?>
						</span>
					</a>
				</div>

				<!-- Desktop Navigation -->
				<div class="navbar__nav-wrapper" role="navigation">
					<?php
					wp_nav_menu(
						array(
							'theme_location'  => 'primary',
							'menu_id'         => 'primary-menu',
							'menu_class'      => 'navbar__menu',
							'container'       => false,
							'fallback_cb'     => 'skyyrose_flagship_nav_fallback',
							'depth'           => 2,
							'items_wrap'      => '<ul id="%1$s" class="%2$s" role="menubar">%3$s</ul>',
						)
					);
					?>
				</div>

				<!-- Header Actions (Search, Account, Cart) -->
				<div class="navbar__actions">
					<!-- Search Button -->
					<button
						class="navbar__action-btn navbar__search-btn"
						id="search-toggle"
						aria-label="<?php esc_attr_e( 'Search', 'skyyrose-flagship' ); ?>"
						aria-expanded="false"
						aria-controls="search-overlay"
						type="button"
					>
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
							<circle cx="11" cy="11" r="8"/>
							<path d="m21 21-4.35-4.35"/>
						</svg>
					</button>

					<!-- Account Link -->
					<?php
					$account_url = class_exists( 'WooCommerce' )
						? wc_get_page_permalink( 'myaccount' )
						: wp_login_url();
					?>
					<a
						href="<?php echo esc_url( $account_url ); ?>"
						class="navbar__action-btn navbar__account-btn"
						aria-label="<?php esc_attr_e( 'My Account', 'skyyrose-flagship' ); ?>"
					>
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
							<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
							<circle cx="12" cy="7" r="4"/>
						</svg>
					</a>

					<!-- Cart -->
					<?php if ( class_exists( 'WooCommerce' ) ) : ?>
						<?php $cart_count = WC()->cart ? WC()->cart->get_cart_contents_count() : 0; ?>
						<a
							href="<?php echo esc_url( wc_get_cart_url() ); ?>"
							class="navbar__action-btn navbar__cart-btn"
							aria-label="<?php echo esc_attr( sprintf(
								/* translators: %d: number of items in cart */
								_n( '%d item in cart', '%d items in cart', $cart_count, 'skyyrose-flagship' ),
								$cart_count
							) ); ?>"
						>
							<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
								<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/>
								<path d="M3 6h18"/>
								<path d="M16 10a4 4 0 0 1-8 0"/>
							</svg>
							<span class="navbar__cart-badge<?php echo $cart_count > 0 ? ' navbar__cart-badge--visible' : ''; ?>">
								<?php echo esc_html( $cart_count ); ?>
							</span>
						</a>
					<?php endif; ?>

					<!-- Mobile Hamburger Toggle -->
					<button
						class="navbar__hamburger"
						id="mobile-menu-toggle"
						aria-controls="mobile-menu"
						aria-expanded="false"
						aria-label="<?php esc_attr_e( 'Open Menu', 'skyyrose-flagship' ); ?>"
						type="button"
					>
						<span class="navbar__hamburger-line" aria-hidden="true"></span>
						<span class="navbar__hamburger-line" aria-hidden="true"></span>
						<span class="navbar__hamburger-line" aria-hidden="true"></span>
					</button>
				</div>

			</div><!-- .navbar__container -->
		</nav>

		<!-- Search Overlay -->
		<div class="search-overlay" id="search-overlay" aria-hidden="true" role="dialog" aria-label="<?php esc_attr_e( 'Search', 'skyyrose-flagship' ); ?>">
			<div class="search-overlay__container">
				<form role="search" method="get" class="search-overlay__form" action="<?php echo esc_url( home_url( '/' ) ); ?>">
					<label class="screen-reader-text" for="search-overlay-input">
						<?php esc_html_e( 'Search for:', 'skyyrose-flagship' ); ?>
					</label>
					<input
						type="search"
						id="search-overlay-input"
						class="search-overlay__input"
						placeholder="<?php esc_attr_e( 'Search the collection...', 'skyyrose-flagship' ); ?>"
						value="<?php echo esc_attr( get_search_query() ); ?>"
						name="s"
						autocomplete="off"
					>
					<button type="submit" class="search-overlay__submit" aria-label="<?php esc_attr_e( 'Submit search', 'skyyrose-flagship' ); ?>">
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
							<circle cx="11" cy="11" r="8"/>
							<path d="m21 21-4.35-4.35"/>
						</svg>
					</button>
				</form>
				<button class="search-overlay__close" id="search-close" aria-label="<?php esc_attr_e( 'Close Search', 'skyyrose-flagship' ); ?>" type="button">
					<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
						<path d="M18 6 6 18"/>
						<path d="m6 6 12 12"/>
					</svg>
				</button>
			</div>
		</div>

		<!-- Mobile Menu Slide-In -->
		<div class="mobile-menu" id="mobile-menu" aria-hidden="true">
			<div class="mobile-menu__overlay" id="mobile-menu-overlay" aria-hidden="true"></div>
			<div class="mobile-menu__panel" role="dialog" aria-label="<?php esc_attr_e( 'Mobile Navigation', 'skyyrose-flagship' ); ?>">
				<div class="mobile-menu__header">
					<span class="mobile-menu__brand navbar__gradient-text"><?php esc_html_e( 'SKYY ROSE', 'skyyrose-flagship' ); ?></span>
					<button
						class="mobile-menu__close"
						id="mobile-menu-close"
						aria-label="<?php esc_attr_e( 'Close Menu', 'skyyrose-flagship' ); ?>"
						type="button"
					>
						<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
							<path d="M18 6 6 18"/>
							<path d="m6 6 12 12"/>
						</svg>
					</button>
				</div>

				<div class="mobile-menu__nav">
					<?php
					wp_nav_menu(
						array(
							'theme_location'  => 'mobile',
							'menu_id'         => 'mobile-primary-menu',
							'menu_class'      => 'mobile-menu__list',
							'container'       => false,
							'fallback_cb'     => 'skyyrose_flagship_nav_fallback',
							'depth'           => 2,
						)
					);
					?>
				</div>

				<div class="mobile-menu__footer">
					<?php if ( class_exists( 'WooCommerce' ) ) : ?>
						<a href="<?php echo esc_url( wc_get_page_permalink( 'myaccount' ) ); ?>" class="mobile-menu__link">
							<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
								<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
								<circle cx="12" cy="7" r="4"/>
							</svg>
							<?php esc_html_e( 'My Account', 'skyyrose-flagship' ); ?>
						</a>
					<?php endif; ?>

					<?php
					$wishlist_page = get_page_by_path( 'wishlist' );
					if ( $wishlist_page ) :
						?>
						<a href="<?php echo esc_url( get_permalink( $wishlist_page ) ); ?>" class="mobile-menu__link">
							<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
								<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
							</svg>
							<?php esc_html_e( 'Wishlist', 'skyyrose-flagship' ); ?>
						</a>
					<?php endif; ?>

					<?php if ( class_exists( 'WooCommerce' ) ) : ?>
						<a href="<?php echo esc_url( wc_get_cart_url() ); ?>" class="mobile-menu__link">
							<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
								<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/>
								<path d="M3 6h18"/>
								<path d="M16 10a4 4 0 0 1-8 0"/>
							</svg>
							<?php esc_html_e( 'Cart', 'skyyrose-flagship' ); ?>
							<?php if ( $cart_count > 0 ) : ?>
								<span class="mobile-menu__badge"><?php echo esc_html( $cart_count ); ?></span>
							<?php endif; ?>
						</a>
					<?php endif; ?>
				</div>
			</div>
		</div>

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
