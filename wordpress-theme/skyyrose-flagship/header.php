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
				<?php if ( has_custom_logo() ) : ?>
					<?php the_custom_logo(); ?>
				<?php else : ?>
					<a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="brand-logo-link" rel="home">
						<?php
						// Check for optimized PNG/WebP logo first, then original
						$logo_webp = SKYYROSE_THEME_DIR . '/assets/images/brand/skyyrose-logo.webp';
						$logo_png  = SKYYROSE_THEME_DIR . '/assets/images/brand/skyyrose-logo.png';
						if ( file_exists( $logo_webp ) ) :
						?>
							<picture>
								<source srcset="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/brand/skyyrose-logo.webp' ); ?>" type="image/webp">
								<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/brand/skyyrose-logo.png' ); ?>" alt="<?php bloginfo( 'name' ); ?>" class="brand-logo-img" loading="eager" fetchpriority="high">
							</picture>
						<?php elseif ( file_exists( $logo_png ) ) : ?>
							<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/brand/skyyrose-logo.png' ); ?>" alt="<?php bloginfo( 'name' ); ?>" class="brand-logo-img" loading="eager" fetchpriority="high">
						<?php else : ?>
							<!-- SVG: SR rose gold monogram with rose accent -->
							<svg viewBox="0 0 140 56" xmlns="http://www.w3.org/2000/svg" class="brand-monogram-svg" aria-label="<?php echo esc_attr( get_bloginfo( 'name' ) ); ?>">
								<defs>
									<linearGradient id="sr-rg" x1="0%" y1="0%" x2="100%" y2="100%">
										<stop offset="0%" style="stop-color:#D8A7B1"/>
										<stop offset="30%" style="stop-color:#B76E79"/>
										<stop offset="60%" style="stop-color:#C48A93"/>
										<stop offset="100%" style="stop-color:#B76E79"/>
									</linearGradient>
									<linearGradient id="sr-rg-shine" x1="0%" y1="0%" x2="100%" y2="0%">
										<stop offset="0%" style="stop-color:#D8A7B1"/>
										<stop offset="40%" style="stop-color:#E8BCC5"/>
										<stop offset="50%" style="stop-color:#F0D0D8"/>
										<stop offset="60%" style="stop-color:#E8BCC5"/>
										<stop offset="100%" style="stop-color:#B76E79"/>
									</linearGradient>
									<filter id="sr-glow">
										<feGaussianBlur stdDeviation="1.5" result="blur"/>
										<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
									</filter>
								</defs>
								<!-- S letter -->
								<text x="4" y="44" fill="url(#sr-rg)" font-family="'Playfair Display', Georgia, serif" font-size="52" font-weight="700" font-style="italic" filter="url(#sr-glow)">S</text>
								<!-- R letter, slightly overlapping -->
								<text x="35" y="44" fill="url(#sr-rg)" font-family="'Playfair Display', Georgia, serif" font-size="52" font-weight="700" font-style="italic" filter="url(#sr-glow)">R</text>
								<!-- Rose accent (larger, more detailed) -->
								<g transform="translate(86,4) scale(0.42)">
									<!-- Outer petals -->
									<path d="M20 0 C26-9 38-6 32 6 C26 18 14 20 8 12 C2 4 14 9 20 0Z" fill="url(#sr-rg-shine)"/>
									<path d="M26 5 C32-4 42 0 36 12 C30 22 18 24 12 16 C6 8 20 14 26 5Z" fill="url(#sr-rg)" opacity="0.85"/>
									<!-- Inner petals -->
									<path d="M14 6 C20-2 10-6 4 3 C-2 12 8 20 16 14 C24 8 8 14 14 6Z" fill="url(#sr-rg-shine)" opacity="0.8"/>
									<!-- Rose center -->
									<circle cx="20" cy="10" r="4" fill="url(#sr-rg)" opacity="0.7"/>
									<circle cx="20" cy="10" r="2" fill="#D8A7B1" opacity="0.5"/>
									<!-- Stem -->
									<path d="M20 20 Q17 32 20 48" fill="none" stroke="#8B5E65" stroke-width="2" stroke-linecap="round"/>
									<!-- Leaves -->
									<ellipse cx="28" cy="32" rx="8" ry="3.5" fill="#8B5E65" opacity="0.6" transform="rotate(-30,28,32)"/>
									<ellipse cx="12" cy="38" rx="7" ry="3" fill="#8B5E65" opacity="0.5" transform="rotate(25,12,38)"/>
								</g>
							</svg>
						<?php endif; ?>
					</a>
				<?php endif; ?>
				<?php
				$tag = ( is_front_page() && is_home() ) ? 'h1' : 'p';
				?>
				<<?php echo $tag; ?> class="site-title sr-only"><a href="<?php echo esc_url( home_url( '/' ) ); ?>" rel="home"><?php bloginfo( 'name' ); ?></a></<?php echo $tag; ?>>
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
