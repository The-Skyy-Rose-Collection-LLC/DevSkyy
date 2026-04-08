<?php
/**
 * Enqueue Scripts & Styles
 *
 * Handles all CSS and JS enqueue logic with conditional loading per template.
 * Global assets load on every page; template-specific assets load only where needed.
 *
 * @package SkyyRose_Flagship
 * @since   3.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Enqueue self-hosted fonts (all brand typography).
 *
 * GDPR-compliant: zero external requests to Google Fonts.
 * All 9 font families served locally from assets/fonts/ as woff2.
 * Fonts: Inter, Playfair Display, Cinzel, Cormorant Garamond,
 *        Oswald, Barlow, Bebas Neue, Space Mono, Instrument Serif.
 *
 * @since 3.2.1
 * @updated 4.1.0 — self-hosted all Google Fonts families
 * @return void
 */
function skyyrose_enqueue_local_fonts() {
	wp_enqueue_style(
		'skyyrose-fonts',
		SKYYROSE_ASSETS_URI . '/css/fonts.css',
		array(),
		SKYYROSE_VERSION
	);
}

/**
 * Enqueue global styles that load on every page.
 *
 * @since 3.0.0
 * @return void
 */
function skyyrose_enqueue_global_styles() {

	$base_uri = SKYYROSE_ASSETS_URI . '/css';
	$base_dir = SKYYROSE_DIR . '/assets/css';
	$use_min  = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;

	// Main theme stylesheet (style.css with WordPress header).
	wp_enqueue_style(
		'skyyrose-style',
		get_stylesheet_uri(),
		array(),
		SKYYROSE_VERSION
	);

	// Elite Web Builder global styles: font vars, grain overlay, sr-container.
	$main_file = $use_min && file_exists( $base_dir . '/main.min.css' ) ? 'main.min.css' : 'main.css';
	if ( file_exists( $base_dir . '/' . $main_file ) ) {
		wp_enqueue_style(
			'skyyrose-main',
			$base_uri . '/' . $main_file,
			array( 'skyyrose-style', 'skyyrose-fonts' ),
			SKYYROSE_VERSION
		);
	}

	// Design tokens: CSS custom properties for colors, spacing, typography.
	$tokens_file = $use_min && file_exists( $base_dir . '/design-tokens.min.css' ) ? 'design-tokens.min.css' : 'design-tokens.css';
	wp_enqueue_style(
		'skyyrose-design-tokens',
		$base_uri . '/' . $tokens_file,
		array( 'skyyrose-style' ),
		SKYYROSE_VERSION
	);

	// Components: reusable component styles (buttons, cards, forms, etc.).
	$comp_file = $use_min && file_exists( $base_dir . '/components.min.css' ) ? 'components.min.css' : 'components.css';
	if ( file_exists( $base_dir . '/' . $comp_file ) ) {
		wp_enqueue_style(
			'skyyrose-components',
			$base_uri . '/' . $comp_file,
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	// Animations: unified scroll-reveal system (.rv, .rv-left, .rv-right, .rv-scale).
	$anim_file = $use_min && file_exists( $base_dir . '/system/animations.min.css' ) ? 'system/animations.min.css' : 'system/animations.css';
	if ( file_exists( $base_dir . '/' . $anim_file ) ) {
		wp_enqueue_style(
			'skyyrose-animations',
			$base_uri . '/' . $anim_file,
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	// Premium animations: clip-path reveals, split-text, stagger, magnetic, parallax.
	// Conditionally loaded — skip on lightweight pages where the extra CSS is wasted
	// (cart, checkout, blog, search, 404, generic pages, contact).
	// Loaded on: front-page, about, immersive, preorder-gateway, collection pages,
	//            single-product, shop-archive (footer uses stagger-grid + rv-clip-up).
	$prem_anim = $use_min && file_exists( $base_dir . '/system/animations-premium.min.css' )
		? 'system/animations-premium.min.css' : 'system/animations-premium.css';
	if ( file_exists( $base_dir . '/' . $prem_anim ) ) {
		$prem_slug     = skyyrose_get_current_template_slug();
		$prem_skip     = array( 'cart', 'checkout', 'blog', 'single', 'page', 'contact', '404', 'default' );
		$skip_premium  = in_array( $prem_slug, $prem_skip, true );
		if ( ! $skip_premium ) {
			wp_enqueue_style(
				'skyyrose-animations-premium',
				$base_uri . '/' . $prem_anim,
				array( 'skyyrose-animations' ),
				SKYYROSE_VERSION
			);
		}
	}

	// Header: navbar, search overlay, mobile menu, dropdowns.
	$header_file = $use_min && file_exists( $base_dir . '/header.min.css' ) ? 'header.min.css' : 'header.css';
	if ( file_exists( $base_dir . '/' . $header_file ) ) {
		wp_enqueue_style(
			'skyyrose-header',
			$base_uri . '/' . $header_file,
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	// Footer: newsletter bar, grid columns, copyright bar, brand column.
	$footer_file = $use_min && file_exists( $base_dir . '/footer.min.css' ) ? 'footer.min.css' : 'footer.css';
	if ( file_exists( $base_dir . '/' . $footer_file ) ) {
		wp_enqueue_style(
			'skyyrose-footer',
			$base_uri . '/' . $footer_file,
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	// Mobile bottom navigation bar (hidden via CSS on desktop ≥769px).
	$mobnav_file = $use_min && file_exists( $base_dir . '/mobile-bottom-nav.min.css' ) ? 'mobile-bottom-nav.min.css' : 'mobile-bottom-nav.css';
	if ( file_exists( $base_dir . '/' . $mobnav_file ) ) {
		wp_enqueue_style(
			'skyyrose-mobile-nav',
			$base_uri . '/' . $mobnav_file,
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	// Cookie consent banner (GDPR).
	if ( file_exists( $base_dir . '/cookie-consent.css' ) ) {
		wp_enqueue_style(
			'skyyrose-cookie-consent',
			$base_uri . '/cookie-consent.css',
			array(),
			SKYYROSE_VERSION
		);
	}

	// Size guide modal (global — trigger via [data-open-size-guide] or .js-size-guide-trigger).
	if ( file_exists( $base_dir . '/size-guide.css' ) ) {
		wp_enqueue_style(
			'skyyrose-size-guide',
			$base_uri . '/size-guide.css',
			array(),
			SKYYROSE_VERSION
		);
	}

	// Luxury cursor — dot follower (desktop only, CSS hidden on touch/mobile).
	if ( file_exists( $base_dir . '/luxury-cursor.css' ) ) {
		wp_enqueue_style(
			'skyyrose-luxury-cursor',
			$base_uri . '/luxury-cursor.css',
			array(),
			SKYYROSE_VERSION
		);
	}

	// Skeleton loading states — shimmer placeholders for images and cards.
	if ( file_exists( $base_dir . '/skeleton.css' ) ) {
		wp_enqueue_style(
			'skyyrose-skeleton',
			$base_uri . '/skeleton.css',
			array(),
			SKYYROSE_VERSION
		);
	}
}

/**
 * Enqueue global scripts that load on every page.
 *
 * @since 3.0.0
 * @return void
 */
function skyyrose_enqueue_global_scripts() {

	$js_uri  = SKYYROSE_ASSETS_URI . '/js';
	$js_dir  = SKYYROSE_DIR . '/assets/js';
	$css_uri = SKYYROSE_ASSETS_URI . '/css';
	$css_dir = SKYYROSE_DIR . '/assets/css';
	$use_min = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;

	// Navigation script (hamburger toggle, keyboard nav, dropdowns).
	$nav_file = $use_min && file_exists( $js_dir . '/navigation.min.js' ) ? 'navigation.min.js' : 'navigation.js';
	if ( file_exists( $js_dir . '/' . $nav_file ) ) {
		wp_enqueue_script(
			'skyyrose-navigation',
			$js_uri . '/' . $nav_file,
			array(),
			SKYYROSE_VERSION,
			true
		);
	}

	// Toast notification utility (global, used by wishlist, add-to-cart, newsletter).
	$toast_file = $use_min && file_exists( $js_dir . '/toast.min.js' ) ? 'toast.min.js' : 'toast.js';
	if ( file_exists( $js_dir . '/' . $toast_file ) ) {
		wp_enqueue_script(
			'skyyrose-toast',
			$js_uri . '/' . $toast_file,
			array(),
			SKYYROSE_VERSION,
			true
		);
	}

	// Luxury cursor — dot follower (desktop only, self-disables on touch/mobile).
	$cursor_file = $use_min && file_exists( $js_dir . '/luxury-cursor.min.js' ) ? 'luxury-cursor.min.js' : 'luxury-cursor.js';
	if ( file_exists( $js_dir . '/' . $cursor_file ) ) {
		wp_enqueue_script(
			'skyyrose-luxury-cursor',
			$js_uri . '/' . $cursor_file,
			array(),
			SKYYROSE_VERSION,
			true
		);
	}

	// Premium interactions: parallax, split-text, magnetic, stagger, scroll-fade.
	$prem_js = $use_min && file_exists( $js_dir . '/premium-interactions.min.js' )
		? 'premium-interactions.min.js' : 'premium-interactions.js';
	if ( file_exists( $js_dir . '/' . $prem_js ) ) {
		wp_enqueue_script(
			'skyyrose-premium-interactions',
			$js_uri . '/' . $prem_js,
			array(),
			SKYYROSE_VERSION,
			true
		);
	}

	// Page transitions + skeleton screens + scarcity bars.
	$pt_file = $use_min && file_exists( $js_dir . '/page-transitions.min.js' )
		? 'page-transitions.min.js' : 'page-transitions.js';
	if ( file_exists( $js_dir . '/' . $pt_file ) ) {
		wp_enqueue_script(
			'skyyrose-page-transitions',
			$js_uri . '/' . $pt_file,
			array(),
			SKYYROSE_VERSION,
			true
		);
	}

	// Comment reply script (WordPress built-in).
	if ( is_singular() && comments_open() && get_option( 'thread_comments' ) ) {
		wp_enqueue_script( 'comment-reply' );
	}

}

/**
 * Localize script data for AJAX URLs, nonces, and theme URIs.
 *
 * @since 3.0.0
 * @return void
 */
function skyyrose_localize_scripts() {

	// navigation.js is always enqueued (see skyyrose_scripts); fall back to
	// jquery only as a last resort to ensure skyyRoseData is always available.
	$handle = 'skyyrose-navigation';
	if ( ! wp_script_is( $handle, 'enqueued' ) ) {
		wp_enqueue_script( 'jquery' );
		$handle = 'jquery';
	}

	wp_localize_script(
		$handle,
		'skyyRoseData',
		array(
			'ajaxUrl'   => admin_url( 'admin-ajax.php' ),
			'nonce'     => wp_create_nonce( 'skyyrose-nonce' ),
			'themeUri'  => SKYYROSE_URI,
			'assetsUri' => SKYYROSE_ASSETS_URI,
		)
	);

}

/**
 * Determine the current page template slug.
 *
 * Returns a normalized identifier that can be used for conditional enqueue.
 * Checks page template files, WooCommerce conditionals, and front-page.
 *
 * @since  3.0.0
 * @return string Template identifier slug (e.g., 'front-page', 'collection', 'about').
 */
function skyyrose_get_current_template_slug() {

	// Front page detection.
	if ( is_front_page() ) {
		return 'front-page';
	}

	// 404 detection.
	if ( is_404() ) {
		return '404';
	}

	// WooCommerce single product.
	if ( function_exists( 'is_product' ) && is_product() ) {
		return 'single-product';
	}

	// WooCommerce cart.
	if ( function_exists( 'is_cart' ) && is_cart() ) {
		return 'cart';
	}

	// WooCommerce checkout.
	if ( function_exists( 'is_checkout' ) && is_checkout() ) {
		return 'checkout';
	}

	// WooCommerce shop / archive.
	if ( function_exists( 'is_shop' ) && ( is_shop() || is_product_category() || is_product_tag() ) ) {
		return 'shop-archive';
	}

	// Page template detection by file name.
	$page_template = get_page_template_slug();

	if ( ! empty( $page_template ) ) {
		$template_map = array(
			'template-collection-black-rose.php'   => 'collection-standalone',
			'template-collection-love-hurts.php'   => 'collection-standalone',
			'template-collection-signature.php'    => 'collection-standalone',
			'template-collection-kids-capsule.php' => 'collection-standalone',
			'template-immersive-black-rose.php'    => 'immersive',
			'template-immersive-love-hurts.php'    => 'immersive',
			'template-immersive-signature.php'     => 'immersive',
			'template-immersive-kids-capsule.php'  => 'immersive',
			'template-about.php'                   => 'about',
			'template-contact.php'                 => 'contact',
			'template-preorder-gateway.php'        => 'preorder-gateway',
			'template-faq.php'                     => 'faq',
			'template-shipping-returns.php'        => 'shipping-returns',
			'template-landing-black-rose.php'      => 'landing',
			'template-landing-love-hurts.php'      => 'landing',
			'template-landing-signature.php'       => 'landing',
			'template-elementor-editorial.php'     => 'elementor-editorial',
		);

		if ( isset( $template_map[ $page_template ] ) ) {
			return $template_map[ $page_template ];
		}
	}

	// Single post.
	if ( is_single() ) {
		return 'single';
	}

	// Search results.
	if ( is_search() ) {
		return 'search';
	}

	// Blog index / archive.
	if ( is_home() || is_archive() ) {
		return 'blog';
	}

	// Generic page (no custom template assigned).
	if ( is_page() ) {
		return 'page';
	}

	return 'default';
}

/**
 * Conditionally enqueue template-specific CSS.
 *
 * Only loads the stylesheet that matches the current page template.
 *
 * @since 3.0.0
 * @return void
 */
function skyyrose_enqueue_template_styles() {

	$slug         = skyyrose_get_current_template_slug();
	$base_css_uri = SKYYROSE_ASSETS_URI . '/css';
	$base_css_dir = SKYYROSE_DIR . '/assets/css';
	$global_deps  = array( 'skyyrose-design-tokens' );
	$use_min      = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;

	$template_styles = array(
		'front-page'      => 'homepage-v2.css',
		'immersive'       => 'immersive.css',
		'single-product'  => 'single-product.css',
		'cart'            => 'woocommerce.css',
		'checkout'        => 'woocommerce.css',
		'shop-archive'    => 'woocommerce.css',
		'about'           => 'about.css',
		'contact'         => 'contact.css',
		'preorder-gateway'  => 'preorder-gateway.css',
		'404'              => '404.css',
		'search'           => 'search-results.css',
		'faq'              => 'info-pages.css',
		'shipping-returns' => 'info-pages.css',
		'landing'              => 'landing-pages.css',
		'elementor-editorial'  => 'landing-pages.css',
		'single'           => 'generic-pages.css',
		'blog'             => 'generic-pages.css',
		'page'             => 'generic-pages.css',
	);

	if ( isset( $template_styles[ $slug ] ) ) {
		$css_file = $template_styles[ $slug ];
		$handle   = 'skyyrose-template-' . sanitize_title( pathinfo( $css_file, PATHINFO_FILENAME ) );
		$min_file = str_replace( '.css', '.min.css', $css_file );

		// Prefer minified version in production.
		if ( $use_min && file_exists( $base_css_dir . '/' . $min_file ) ) {
			$css_file = $min_file;
		}

		if ( file_exists( $base_css_dir . '/' . $css_file ) ) {
			wp_enqueue_style(
				$handle,
				$base_css_uri . '/' . $css_file,
				$global_deps,
				SKYYROSE_VERSION
			);
		}
	}

	// Immersive scene images — overlays, tab bar, cinematic toggle, particles.
	if ( 'immersive' === $slug ) {
		$scenes_file = $use_min && file_exists( $base_css_dir . '/immersive-scenes.min.css' )
			? 'immersive-scenes.min.css' : 'immersive-scenes.css';
		if ( file_exists( $base_css_dir . '/' . $scenes_file ) ) {
			wp_enqueue_style(
				'skyyrose-immersive-scenes',
				$base_css_uri . '/' . $scenes_file,
				array( 'skyyrose-template-immersive' ),
				SKYYROSE_VERSION
			);
		}
	}

	// Unified collection page CSS — single stylesheet for all 4 collection templates.
	if ( 'collection-standalone' === $slug ) {
		$col_css = $use_min && file_exists( $base_css_dir . '/collection-pages.min.css' )
			? 'collection-pages.min.css' : 'collection-pages.css';
		if ( file_exists( $base_css_dir . '/' . $col_css ) ) {
			wp_enqueue_style(
				'skyyrose-collection-pages',
				$base_css_uri . '/' . $col_css,
				$global_deps,
				SKYYROSE_VERSION
			);
		}
	}

	// WooCommerce page-specific CSS (loaded ON TOP of the base woocommerce.css).
	$woo_page_styles = array(
		// single-product.css is the primary stylesheet (replaces woocommerce-single.css).
		'cart'           => 'woocommerce-cart.css',
		'checkout'       => 'woocommerce-checkout.css',
	);

	if ( isset( $woo_page_styles[ $slug ] ) ) {
		$woo_file   = $woo_page_styles[ $slug ];
		$woo_handle = 'skyyrose-' . sanitize_title( pathinfo( $woo_file, PATHINFO_FILENAME ) );
		$woo_min    = str_replace( '.css', '.min.css', $woo_file );

		// Prefer minified version in production.
		if ( $use_min && file_exists( $base_css_dir . '/' . $woo_min ) ) {
			$woo_file = $woo_min;
		}

		if ( file_exists( $base_css_dir . '/' . $woo_file ) ) {
			wp_enqueue_style(
				$woo_handle,
				$base_css_uri . '/' . $woo_file,
				array( 'skyyrose-template-woocommerce' ),
				SKYYROSE_VERSION
			);
		}
	}

}

/**
 * Conditionally enqueue template-specific JS.
 *
 * Only loads the script that matches the current page template.
 *
 * @since 3.0.0
 * @return void
 */
function skyyrose_enqueue_template_scripts() {

	$slug        = skyyrose_get_current_template_slug();
	$base_js_uri = SKYYROSE_ASSETS_URI . '/js';
	$base_js_dir = SKYYROSE_DIR . '/assets/js';
	$base_css_uri = SKYYROSE_ASSETS_URI . '/css';
	$base_css_dir = SKYYROSE_DIR . '/assets/css';
	$use_min     = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;

	// Landing pages JS — countdown, parallax, FAQ accordion, scroll reveal.
	if ( in_array( $slug, array( 'landing', 'elementor-editorial' ), true ) ) {
		$lp_js = $use_min && file_exists( $base_js_dir . '/landing-pages.min.js' )
			? 'landing-pages.min.js' : 'landing-pages.js';
		if ( file_exists( $base_js_dir . '/' . $lp_js ) ) {
			wp_enqueue_script(
				'skyyrose-landing-pages',
				$base_js_uri . '/' . $lp_js,
				array(),
				SKYYROSE_VERSION,
				true
			);
		}
	}

	// Collection pages JS — IntersectionObserver scroll-reveal (no GSAP dependency).
	if ( 'collection-standalone' === $slug ) {
		$col_js = $use_min && file_exists( $base_js_dir . '/collection-pages.min.js' )
			? 'collection-pages.min.js' : 'collection-pages.js';
		if ( file_exists( $base_js_dir . '/' . $col_js ) ) {
			wp_enqueue_script(
				'skyyrose-collection-pages',
				$base_js_uri . '/' . $col_js,
				array(),
				SKYYROSE_VERSION,
				true
			);
		}
	}

	// GSAP — loaded on pages that use scroll animations (NOT collection pages — they use IntersectionObserver).
	$gsap_slugs = array( 'preorder-gateway', 'about', 'immersive' );
	if ( in_array( $slug, $gsap_slugs, true ) ) {
		wp_enqueue_script( 'skyyrose-gsap', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js', array(), '3.12.2', true );
		wp_enqueue_script( 'skyyrose-gsap-st', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/ScrollTrigger.min.js', array( 'skyyrose-gsap' ), '3.12.2', true );
	}

	$template_scripts = array(
		'front-page'       => 'homepage-v2.js',
		'immersive'        => 'immersive.js',
		'single-product'   => 'single-product.js',
		'cart'             => 'woocommerce.js',
		'checkout'         => 'woocommerce.js',
		'contact'          => 'contact.js',
		'preorder-gateway'  => 'preorder-gateway.js',
		'about'            => 'about.js',
	);

	if ( isset( $template_scripts[ $slug ] ) ) {
		$js_file = $template_scripts[ $slug ];
		$handle  = 'skyyrose-template-' . sanitize_title( pathinfo( $js_file, PATHINFO_FILENAME ) );

		// WooCommerce + single-product JS depend on jQuery for cart/gallery interactions.
		$wc_js_files = array( 'woocommerce.js', 'single-product.js' );
		$js_deps     = in_array( $js_file, $wc_js_files, true ) ? array( 'jquery', 'wc-add-to-cart-variation' ) : array();

		// Prefer minified version in production.
		$min_file = str_replace( '.js', '.min.js', $js_file );
		if ( $use_min && file_exists( $base_js_dir . '/' . $min_file ) ) {
			$js_file = $min_file;
		}

		if ( file_exists( $base_js_dir . '/' . $js_file ) ) {
			wp_enqueue_script(
				$handle,
				$base_js_uri . '/' . $js_file,
				$js_deps,
				SKYYROSE_VERSION,
				true
			);
		}

		// Localize preorder gateway with WooCommerce cart sync data.
		if ( 'preorder-gateway' === $slug && wp_script_is( $handle, 'enqueued' ) ) {
			wp_localize_script(
				$handle,
				'skyyRoseGateway',
				array(
					'ajaxUrl'     => admin_url( 'admin-ajax.php' ),
					'nonce'       => wp_create_nonce( 'skyyrose-immersive-nonce' ),
					'wcActive'    => class_exists( 'WooCommerce' ),
					'checkoutUrl' => function_exists( 'wc_get_checkout_url' ) ? wc_get_checkout_url() : home_url( '/checkout/' ),
					'cartUrl'     => function_exists( 'wc_get_cart_url' ) ? wc_get_cart_url() : home_url( '/cart/' ),
					'i18n'        => array(
						'item'  => __( 'item', 'skyyrose-flagship' ),
						'items' => __( 'items', 'skyyrose-flagship' ),
					),
				)
			);
		}

		/* Immersive world + WC bridge — will be re-added when immersive rooms v6.0 ships */
	}

	// Holo product cards — loaded on collection pages, shop archives, and WC loop.
	// NOTE: This must be OUTSIDE the $template_scripts check above.
	if ( in_array( $slug, array( 'collection', 'collection-v4', 'collection-standalone', 'collections-shop', 'front-page', 'shop-archive', 'preorder-gateway', 'search', 'landing', 'elementor-editorial' ), true ) ) {
			$holo_css_file = $use_min && file_exists( $base_css_dir . '/product-card-holo.min.css' )
				? 'product-card-holo.min.css' : 'product-card-holo.css';
			if ( file_exists( $base_css_dir . '/' . $holo_css_file ) ) {
				wp_enqueue_style(
					'skyyrose-product-card-holo',
					$base_css_uri . '/' . $holo_css_file,
					array( 'skyyrose-design-tokens' ),
					SKYYROSE_VERSION
				);
			}
			$holo_js_file = $use_min && file_exists( $base_js_dir . '/product-card-holo.min.js' )
				? 'product-card-holo.min.js' : 'product-card-holo.js';
			if ( file_exists( $base_js_dir . '/' . $holo_js_file ) ) {
				wp_enqueue_script(
					'skyyrose-product-card-holo',
					$base_js_uri . '/' . $holo_js_file,
					array(),
					SKYYROSE_VERSION,
					true
				);
			}
	}
}


/**
 * Enqueue admin styles and scripts.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_admin_scripts() {
	$css_dir = SKYYROSE_DIR . '/assets/css';
	$css_uri = SKYYROSE_ASSETS_URI . '/css';
	$js_dir  = SKYYROSE_DIR . '/assets/js';
	$js_uri  = SKYYROSE_ASSETS_URI . '/js';
	$use_min = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;

	$admin_css_file = $use_min && file_exists( $css_dir . '/admin.min.css' )
		? 'admin.min.css' : 'admin.css';
	if ( file_exists( $css_dir . '/' . $admin_css_file ) ) {
		wp_enqueue_style(
			'skyyrose-admin',
			$css_uri . '/' . $admin_css_file,
			array(),
			SKYYROSE_VERSION
		);
	}

	$admin_js_file = $use_min && file_exists( $js_dir . '/admin.min.js' )
		? 'admin.min.js' : 'admin.js';
	if ( file_exists( $js_dir . '/' . $admin_js_file ) ) {
		wp_enqueue_script(
			'skyyrose-admin',
			$js_uri . '/' . $admin_js_file,
			array( 'jquery' ),
			SKYYROSE_VERSION,
			true
		);
	}
}

/*--------------------------------------------------------------
 * Collection Experience Scenes — Three.js Per-Collection Worlds
 *
 * Loads Three.js r160 + add-ons + experience base class + per-collection
 * scene on immersive template pages. Each collection gets its own world.
 *
 * @since 5.2.0
 *--------------------------------------------------------------*/

/**
 * Enqueue collection-specific Three.js experience scenes.
 *
 * @since 5.2.0
 * @return void
 */
function skyyrose_enqueue_collection_experiences() {
	if ( is_admin() ) {
		return;
	}

	$experience_map = array(
		'template-immersive-black-rose.php'  => 'experiences/blackrose-experience',
		'template-immersive-love-hurts.php'  => 'experiences/lovehurts-experience',
		'template-immersive-signature.php'   => 'experiences/signature-experience',
	);

	$current_template = get_page_template_slug();

	if ( ! $current_template || ! isset( $experience_map[ $current_template ] ) ) {
		return;
	}

	$use_min = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;
	$js_dir  = SKYYROSE_DIR . '/assets/js';
	$js_uri  = SKYYROSE_ASSETS_URI . '/js';

	// Three.js r160 via CDN with add-on scripts.
	$threejs_ver = '0.160.0';
	$threejs_cdn = 'https://cdn.jsdelivr.net/npm/three@' . $threejs_ver;

	if ( ! wp_script_is( 'threejs', 'enqueued' ) ) {
		wp_enqueue_script( 'threejs', $threejs_cdn . '/build/three.min.js', array(), $threejs_ver, true );
	}

	$addons = array(
		'threejs-orbit-controls'  => '/examples/js/controls/OrbitControls.js',
		'threejs-gltf-loader'     => '/examples/js/loaders/GLTFLoader.js',
		'threejs-draco-loader'    => '/examples/js/loaders/DRACOLoader.js',
		'threejs-rgbe-loader'     => '/examples/js/loaders/RGBELoader.js',
		'threejs-effect-composer'  => '/examples/js/postprocessing/EffectComposer.js',
		'threejs-render-pass'     => '/examples/js/postprocessing/RenderPass.js',
		'threejs-unreal-bloom'    => '/examples/js/postprocessing/UnrealBloomPass.js',
		'threejs-shader-pass'     => '/examples/js/postprocessing/ShaderPass.js',
		'threejs-copy-shader'     => '/examples/js/shaders/CopyShader.js',
	);

	foreach ( $addons as $handle => $path ) {
		if ( ! wp_script_is( $handle, 'enqueued' ) ) {
			wp_enqueue_script( $handle, $threejs_cdn . $path, array( 'threejs' ), $threejs_ver, true );
		}
	}

	// Experience base class.
	$base_file = $use_min && file_exists( $js_dir . '/experiences/experience-base.min.js' )
		? 'experiences/experience-base.min.js' : 'experiences/experience-base.js';
	if ( file_exists( $js_dir . '/' . $base_file ) ) {
		wp_enqueue_script( 'skyyrose-experience-base', $js_uri . '/' . $base_file, array( 'threejs' ), SKYYROSE_VERSION, true );
	}

	// Luxury animations.
	$anim_file = $use_min && file_exists( $js_dir . '/experiences/luxury-animations.min.js' )
		? 'experiences/luxury-animations.min.js' : 'experiences/luxury-animations.js';
	if ( file_exists( $js_dir . '/' . $anim_file ) ) {
		wp_enqueue_script( 'skyyrose-luxury-animations', $js_uri . '/' . $anim_file, array( 'skyyrose-experience-base' ), SKYYROSE_VERSION, true );
	}

	// Collection-specific scene.
	$scene_slug = $experience_map[ $current_template ];
	$scene_file = $use_min && file_exists( $js_dir . '/' . $scene_slug . '.min.js' )
		? $scene_slug . '.min.js' : $scene_slug . '.js';
	if ( file_exists( $js_dir . '/' . $scene_file ) ) {
		wp_enqueue_script( 'skyyrose-collection-experience', $js_uri . '/' . $scene_file, array( 'skyyrose-experience-base', 'skyyrose-luxury-animations' ), SKYYROSE_VERSION, true );
	}

	// Init-3D orchestrator.
	$init_file = $use_min && file_exists( $js_dir . '/experiences/init-3d.min.js' )
		? 'experiences/init-3d.min.js' : 'experiences/init-3d.js';
	if ( file_exists( $js_dir . '/' . $init_file ) ) {
		wp_enqueue_script( 'skyyrose-3d-init', $js_uri . '/' . $init_file, array( 'skyyrose-collection-experience' ), SKYYROSE_VERSION, true );
	}
}

/*--------------------------------------------------------------
 * Hook Registration
 *
 * Performance hooks → inc/enqueue-performance.php
 *--------------------------------------------------------------*/

// Self-hosted fonts (priority 5 so they load before template styles).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_local_fonts', 5 );

// Global styles (priority 10 - default).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_global_styles', 10 );

// Global scripts (priority 10).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_global_scripts', 10 );

// Localize scripts (priority 15, after scripts are registered).
add_action( 'wp_enqueue_scripts', 'skyyrose_localize_scripts', 15 );

// Template-specific styles (priority 20, after globals).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_template_styles', 20 );

// Template-specific scripts (priority 20).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_template_scripts', 20 );

// Collection experience scenes (priority 65, after all template assets).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_collection_experiences', 65 );

// Admin scripts.
add_action( 'admin_enqueue_scripts', 'skyyrose_admin_scripts' );
