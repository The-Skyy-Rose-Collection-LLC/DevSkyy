<?php
/**
 * The header for the SkyyRose theme — Impeccable Refinement
 * Action icons left, Navigation right.
 */
defined( 'ABSPATH' ) || exit;
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

<!-- Global Grain & Vignette for Cinematic Depth -->
<div class="global-grain" aria-hidden="true"></div>
<div class="global-vignette" aria-hidden="true"></div>

<div id="page" class="site">
	<header id="masthead" class="site-header" role="banner">
		<nav class="navbar" id="navbar" aria-label="<?php esc_attr_e( 'Primary Navigation', 'skyyrose' ); ?>">
			<div class="navbar__container">

				<!-- LEFT: Actions (Search, Account, Bag) -->
				<?php $cart_count = 0; ?>
				<div class="navbar__actions">
					<button class="navbar__action-btn" id="search-toggle" aria-expanded="false" type="button">
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
						<span><?php esc_html_e('Search', 'skyyrose'); ?></span>
					</button>

					<?php $account_url = class_exists( 'WooCommerce' ) ? wc_get_page_permalink( 'myaccount' ) : wp_login_url(); ?>
					<a href="<?php echo esc_url( $account_url ); ?>" class="navbar__action-btn">
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
						<span><?php esc_html_e('Account', 'skyyrose'); ?></span>
					</a>

					<?php if ( class_exists( 'WooCommerce' ) && function_exists( 'WC' ) && WC() && WC()->cart ) : 
						$cart_count = WC()->cart->get_cart_contents_count(); ?>
						<a href="<?php echo esc_url( wc_get_cart_url() ); ?>" class="navbar__action-btn navbar__cart-btn">
							<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>
							<span><?php esc_html_e('Bag', 'skyyrose'); ?></span>
							<span class="navbar__cart-badge<?php echo esc_attr( $cart_count > 0 ? ' navbar__cart-badge--visible' : '' ); ?>"><?php echo esc_html( $cart_count ); ?></span>
						</a>
					<?php endif; ?>
				</div>

				<!-- CENTER: Logo -->
				<div class="navbar__brand">
					<a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="navbar__logo-link">
						<span class="navbar__site-title">SKYY ROSE</span>
					</a>
				</div>

				<!-- RIGHT: Desktop Navigation -->
				<div class="navbar__nav-wrapper">
					<?php
					wp_nav_menu( array(
						'theme_location' => 'primary',
						'menu_class'     => 'navbar__menu',
						'container'      => false,
						'depth'          => 2,
					) );
					?>
				</div>
                
                <!-- Mobile Menu Toggle (Right aligned on Mobile) -->
                <button class="navbar__hamburger" id="mobile-menu-toggle" type="button">
                    <span class="navbar__hamburger-line"></span>
                    <span class="navbar__hamburger-line"></span>
                    <span class="navbar__hamburger-line"></span>
                </button>

			</div>
		</nav>

		<!-- Mobile Menu Slide-In -->
		<div class="mobile-menu" id="mobile-menu" aria-hidden="true" inert>
			<div class="mobile-menu__overlay" id="mobile-menu-overlay" aria-hidden="true"></div>
			<div class="mobile-menu__panel">
				<div class="mobile-menu__header">
					<span class="mobile-menu__brand">SKYY ROSE</span>
					<button class="mobile-menu__close" id="mobile-menu-close" type="button">
						<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
					</button>
				</div>
				<div class="mobile-menu__nav">
					<?php wp_nav_menu( array( 'theme_location' => 'primary', 'container' => false ) ); ?>
				</div>
			</div>
		</div>

        <!-- Search Overlay -->
        <div class="search-overlay" id="search-overlay" aria-hidden="true" inert>
            <div class="search-overlay__container">
                <form role="search" method="get" class="search-overlay__form" action="<?php echo esc_url( home_url( '/' ) ); ?>">
                    <input type="search" class="search-overlay__input" placeholder="SEARCH THE COLLECTION..." name="s" autocomplete="off">
                </form>
                <button class="search-overlay__close" id="search-close" type="button">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                </button>
            </div>
        </div>

	</header>
	<div id="content" class="site-content">
