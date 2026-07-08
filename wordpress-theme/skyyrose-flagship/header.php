<?php
/**
 * The header for the SkyyRose theme — Impeccable Refinement
 * Action icons left, Navigation right.
 *
 * @package SkyyRose
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

<a class="skip-link" href="#content"><?php esc_html_e( 'Skip to the story', 'skyyrose' ); ?></a>

<div class="grain-overlay" aria-hidden="true"></div>

<?php // Global grain + vignette disabled — z-index 9999 overlay with .2s infinite animation hurts performance and obscures content. ?>

<div id="page" class="site">
	<header id="masthead" class="site-header" role="banner">
		<?php
		$skyyrose_ann_enabled = get_theme_mod( 'skyyrose_announcement_enabled', false );
		$skyyrose_ann_text    = get_theme_mod( 'skyyrose_announcement_text', '' );
		if ( $skyyrose_ann_enabled && ! empty( $skyyrose_ann_text ) ) :
			$skyyrose_ann_link = get_theme_mod( 'skyyrose_announcement_link', '' );
			?>
			<div class="announcement-bar" id="announcement-bar" role="note" aria-label="<?php esc_attr_e( 'Site announcement', 'skyyrose' ); ?>">
				<div class="announcement-bar__inner">
					<?php if ( ! empty( $skyyrose_ann_link ) ) : ?>
						<a href="<?php echo esc_url( $skyyrose_ann_link ); ?>" class="announcement-bar__content"><?php echo esc_html( $skyyrose_ann_text ); ?></a>
					<?php else : ?>
						<span class="announcement-bar__content"><?php echo esc_html( $skyyrose_ann_text ); ?></span>
					<?php endif; ?>
					<button class="announcement-bar__dismiss" type="button" aria-label="<?php esc_attr_e( 'Dismiss announcement', 'skyyrose' ); ?>">
						<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
					</button>
				</div>
			</div>
		<?php endif; ?>
		<nav class="navbar" id="navbar" aria-label="<?php esc_attr_e( 'Primary Navigation', 'skyyrose' ); ?>">
			<div class="navbar__container">

				<!-- LEFT: Actions (Search, Account, Bag) -->
				<?php $cart_count = 0; ?>
				<div class="navbar__actions">
					<button class="navbar__action-btn" id="search-toggle" aria-expanded="false" type="button">
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
						<span><?php esc_html_e( 'Search', 'skyyrose' ); ?></span>
					</button>

					<?php $account_url = class_exists( 'WooCommerce' ) ? wc_get_page_permalink( 'myaccount' ) : wp_login_url(); ?>
					<a href="<?php echo esc_url( $account_url ); ?>" class="navbar__action-btn">
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
						<span><?php esc_html_e( 'Account', 'skyyrose' ); ?></span>
					</a>

					<?php
					if ( class_exists( 'WooCommerce' ) && function_exists( 'WC' ) && WC() && WC()->cart ) :
						$cart_count = WC()->cart->get_cart_contents_count();
						?>
						<a href="<?php echo esc_url( wc_get_cart_url() ); ?>" class="navbar__action-btn navbar__cart-btn">
							<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>
							<span><?php esc_html_e( 'Bag', 'skyyrose' ); ?></span>
							<span class="navbar__cart-badge<?php echo esc_attr( $cart_count > 0 ? ' navbar__cart-badge--visible' : '' ); ?>"><?php echo esc_html( $cart_count ); ?></span>
						</a>
					<?php endif; ?>
				</div>

				<!-- CENTER: Brand Primary Logo (rotating TSRC rose-gold 3D lockup — webm+alpha, animated-webp <video> fallback; static poster substitutes under prefers-reduced-motion) -->
				<div class="navbar__brand">
					<a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="navbar__logo-link" aria-label="<?php esc_attr_e( 'SkyyRose — Home', 'skyyrose' ); ?>">
						<video
							class="navbar__logo-video"
							width="60"
							height="44"
							poster="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/branding/tsrc-lockup-static@2x.webp' ); ?>"
							autoplay
							muted
							loop
							playsinline
							disablepictureinpicture
							fetchpriority="low"
							aria-hidden="true">
							<source src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/branding/tsrc-lockup-rotating@2x.webm' ); ?>" type="video/webm">
							<?php // Fallback content only paints if no <source> is playable (e.g. Safari versions without WebM support) — same nav-logo weight class as the primary video, so it must not outrank real above-fold content either. ?>
							<img
								src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/branding/tsrc-lockup-rotating@2x.webp' ); ?>"
								alt=""
								class="navbar__logo-img"
								width="60"
								height="44"
								decoding="async"
								fetchpriority="low">
						</video>
						<img
							src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/branding/tsrc-lockup-static@2x.webp' ); ?>"
							alt=""
							class="navbar__logo-static"
							width="60"
							height="44"
							decoding="async">
						<span class="screen-reader-text"><?php esc_html_e( 'SkyyRose', 'skyyrose' ); ?></span>
					</a>
				</div>

				<!-- RIGHT: Desktop Navigation -->
				<div class="navbar__nav-wrapper">
					<?php
					wp_nav_menu(
						array(
							'theme_location' => 'primary',
							'menu_class'     => 'navbar__menu',
							'container'      => false,
							'depth'          => 2,
						)
					);
					?>
				</div>

				<?php
				// No-JS fallback: navigation.js relocates .navbar__menu into the
				// mobile drawer at <=1024px and drives the hamburger toggle. If JS
				// never runs (network/CSP/script error/disabled), the drawer stays
				// empty AND the hamburger button has no click handler, so mobile
				// visitors would have zero primary navigation. Force the desktop
				// nav wrapper back to visible at the same breakpoint so the menu
				// (already server-rendered above) stays reachable without JS.
				?>
				<noscript>
					<style>
						@media (max-width: 1024px) {
							.navbar__nav-wrapper { display: block; }
						}
					</style>
				</noscript>

				<!-- Mobile Menu Toggle (Right aligned on Mobile) -->
				<button class="navbar__hamburger" id="mobile-menu-toggle" type="button" aria-label="<?php esc_attr_e( 'Open navigation menu', 'skyyrose' ); ?>" aria-expanded="false" aria-controls="mobile-menu">
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
					<button class="mobile-menu__close" id="mobile-menu-close" type="button" aria-label="<?php esc_attr_e( 'Close navigation menu', 'skyyrose' ); ?>">
						<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
					</button>
				</div>
				<?php
				// Single-menu shell: the primary menu renders ONCE (desktop
				// .navbar__nav-wrapper above). navigation.js relocates that same
				// DOM node into this container at ≤1024px — never a second copy.
				?>
				<div class="mobile-menu__nav"></div>
			</div>
		</div>

		<!-- Search Overlay -->
		<div class="search-overlay" id="search-overlay"
			role="dialog"
			aria-modal="true"
			aria-labelledby="search-overlay-label"
			aria-hidden="true"
			inert>
			<div class="search-overlay__container">
				<span id="search-overlay-label" class="screen-reader-text"><?php esc_html_e( 'Search the collection', 'skyyrose' ); ?></span>
				<form role="search" method="get" class="search-overlay__form" action="<?php echo esc_url( home_url( '/' ) ); ?>">
					<label class="screen-reader-text" for="search-overlay-input"><?php esc_html_e( 'Search the collection', 'skyyrose' ); ?></label>
					<input id="search-overlay-input" type="search" class="search-overlay__input" placeholder="SEARCH THE COLLECTION..." name="s" autocomplete="off">
				</form>
				<button class="search-overlay__close" id="search-close" type="button" aria-label="<?php esc_attr_e( 'Close search', 'skyyrose' ); ?>">
					<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
				</button>
			</div>
		</div>

	</header>
	<div id="content" class="site-content" tabindex="-1">
