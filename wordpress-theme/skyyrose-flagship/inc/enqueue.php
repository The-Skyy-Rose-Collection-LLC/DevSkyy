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

	// Comment reply script (WordPress built-in).
	if ( is_singular() && comments_open() && get_option( 'thread_comments' ) ) {
		wp_enqueue_script( 'comment-reply' );
	}

	// Brand mascot interactive widget (walks on from right side).
	$mascot_js_file = $use_min && file_exists( $js_dir . '/mascot.min.js' ) ? 'mascot.min.js' : 'mascot.js';
	if ( file_exists( $js_dir . '/' . $mascot_js_file ) && ! is_admin() ) {
		wp_enqueue_script(
			'skyyrose-mascot',
			$js_uri . '/' . $mascot_js_file,
			array(),
			SKYYROSE_VERSION,
			true
		);

		// Pass page context for collection-aware outfit switching.
		$mascot_context = 'default';
		$template_file  = get_page_template_slug();
		if ( is_front_page() ) {
			$mascot_context = 'homepage';
		} elseif ( is_404() ) {
			$mascot_context = '404';
		} elseif ( strpos( $template_file, 'black-rose' ) !== false ) {
			$mascot_context = 'black-rose';
		} elseif ( strpos( $template_file, 'love-hurts' ) !== false ) {
			$mascot_context = 'love-hurts';
		} elseif ( strpos( $template_file, 'signature' ) !== false ) {
			$mascot_context = 'signature';
		} elseif ( strpos( $template_file, 'kids-capsule' ) !== false ) {
			$mascot_context = 'kids-capsule';
		} elseif ( strpos( $template_file, 'preorder' ) !== false ) {
			$mascot_context = 'preorder';
		}

		wp_localize_script(
			'skyyrose-mascot',
			'skyyroseMascotData',
			array(
				'context'   => $mascot_context,
				'assetsUri' => SKYYROSE_ASSETS_URI . '/images/mascot/',
				'ajaxUrl'   => admin_url( 'admin-ajax.php' ),
				'nonce'     => wp_create_nonce( 'skyyrose-nonce' ),
				'homeUrl'   => home_url( '/' ),
			)
		);
	}

	// Brand Ambassador — Skyy Rose chatbot widget (site-wide).
	$amb_css_file = $use_min && file_exists( $css_dir . '/brand-ambassador.min.css' ) ? 'brand-ambassador.min.css' : 'brand-ambassador.css';
	if ( file_exists( $css_dir . '/' . $amb_css_file ) && ! is_admin() ) {
		wp_enqueue_style(
			'skyyrose-brand-ambassador',
			$css_uri . '/' . $amb_css_file,
			array(),
			SKYYROSE_VERSION
		);
	}

	$amb_js_file = $use_min && file_exists( $js_dir . '/brand-ambassador.min.js' ) ? 'brand-ambassador.min.js' : 'brand-ambassador.js';
	if ( file_exists( $js_dir . '/' . $amb_js_file ) && ! is_admin() ) {
		wp_enqueue_script(
			'skyyrose-brand-ambassador',
			$js_uri . '/' . $amb_js_file,
			array(),
			SKYYROSE_VERSION,
			true
		);
	}

	// Progressive image loading — blur-up effect for product images (v4.0.0 bonus).
	$prog_js_file = $use_min && file_exists( $js_dir . '/progressive-images.min.js' ) ? 'progressive-images.min.js' : 'progressive-images.js';
	if ( file_exists( $js_dir . '/' . $prog_js_file ) && ! is_admin() ) {
		wp_enqueue_script(
			'skyyrose-progressive-images',
			$js_uri . '/' . $prog_js_file,
			array(),
			SKYYROSE_VERSION,
			true
		);
	}

	// Smart link prefetching — preloads pages on hover for instant navigation (v4.0.0 bonus).
	$prefetch_js_file = $use_min && file_exists( $js_dir . '/smart-prefetch.min.js' ) ? 'smart-prefetch.min.js' : 'smart-prefetch.js';
	if ( file_exists( $js_dir . '/' . $prefetch_js_file ) && ! is_admin() ) {
		wp_enqueue_script(
			'skyyrose-smart-prefetch',
			$js_uri . '/' . $prefetch_js_file,
			array(),
			SKYYROSE_VERSION,
			true
		);
	}

	// Scroll enhancements — progress indicator + back-to-top button (v4.0.0 S6 bonus).
	$scroll_js_file = $use_min && file_exists( $js_dir . '/scroll-enhancements.min.js' ) ? 'scroll-enhancements.min.js' : 'scroll-enhancements.js';
	if ( file_exists( $js_dir . '/' . $scroll_js_file ) && ! is_admin() ) {
		wp_enqueue_script(
			'skyyrose-scroll-enhancements',
			$js_uri . '/' . $scroll_js_file,
			array(),
			SKYYROSE_VERSION,
			true
		);
	}

	// Web Vitals Monitor — tracks LCP, FID/INP, CLS for SEO (v4.0.0 S7 bonus).
	$vitals_js_file = $use_min && file_exists( $js_dir . '/web-vitals-monitor.min.js' ) ? 'web-vitals-monitor.min.js' : 'web-vitals-monitor.js';
	if ( file_exists( $js_dir . '/' . $vitals_js_file ) && ! is_admin() ) {
		wp_enqueue_script(
			'skyyrose-web-vitals',
			$js_uri . '/' . $vitals_js_file,
			array(),
			SKYYROSE_VERSION,
			true
		);
	}

	// Schema Validator — dev-mode JSON-LD checker (v4.0.0 S7 bonus).
	$schema_js_file = $use_min && file_exists( $js_dir . '/schema-validator.min.js' ) ? 'schema-validator.min.js' : 'schema-validator.js';
	if ( file_exists( $js_dir . '/' . $schema_js_file ) && ! is_admin() && ( defined( 'WP_DEBUG' ) && WP_DEBUG ) ) {
		wp_enqueue_script(
			'skyyrose-schema-validator',
			$js_uri . '/' . $schema_js_file,
			array(),
			SKYYROSE_VERSION,
			true
		);
	}

	// Exit-intent overlay — only on product-facing pages (v4.0.0 S2 bonus).
	$exit_slugs = array( 'front-page', 'collection', 'collection-v4', 'single-product', 'preorder-gateway', 'landing' );
	if ( ! is_admin() && in_array( skyyrose_get_current_template_slug(), $exit_slugs, true ) ) {
		$exit_css_file = $use_min && file_exists( $css_dir . '/exit-intent.min.css' ) ? 'exit-intent.min.css' : 'exit-intent.css';
		if ( file_exists( $css_dir . '/' . $exit_css_file ) ) {
			wp_enqueue_style(
				'skyyrose-exit-intent',
				$css_uri . '/' . $exit_css_file,
				array(),
				SKYYROSE_VERSION
			);
		}

		$exit_js_file = $use_min && file_exists( $js_dir . '/exit-intent.min.js' ) ? 'exit-intent.min.js' : 'exit-intent.js';
		if ( file_exists( $js_dir . '/' . $exit_js_file ) ) {
			wp_enqueue_script(
				'skyyrose-exit-intent',
				$js_uri . '/' . $exit_js_file,
				array(),
				SKYYROSE_VERSION,
				true
			);
		}
	}

	// Urgency countdown banner — only on product-facing pages (v4.0.0 S2 bonus).
	$urgency_slugs = array( 'front-page', 'collection', 'collection-v4', 'single-product', 'preorder-gateway', 'landing' );
	if ( ! is_admin() && in_array( skyyrose_get_current_template_slug(), $urgency_slugs, true ) ) {
		$urg_css_file = $use_min && file_exists( $css_dir . '/urgency-banner.min.css' ) ? 'urgency-banner.min.css' : 'urgency-banner.css';
		if ( file_exists( $css_dir . '/' . $urg_css_file ) ) {
			wp_enqueue_style(
				'skyyrose-urgency-banner',
				$css_uri . '/' . $urg_css_file,
				array(),
				SKYYROSE_VERSION
			);
		}

		$urg_js_file = $use_min && file_exists( $js_dir . '/urgency-banner.min.js' ) ? 'urgency-banner.min.js' : 'urgency-banner.js';
		if ( file_exists( $js_dir . '/' . $urg_js_file ) ) {
			wp_enqueue_script(
				'skyyrose-urgency-banner',
				$js_uri . '/' . $urg_js_file,
				array(),
				SKYYROSE_VERSION,
				true
			);

			// Pass deadline from WordPress option (set via admin or wp-cli).
			$preorder_deadline = get_option( 'skyyrose_preorder_deadline', '' );
			if ( ! $preorder_deadline ) {
				// Fallback: 30 days from now if no deadline is set.
				$preorder_deadline = gmdate( 'c', strtotime( '+30 days' ) );
			}

			wp_localize_script( 'skyyrose-urgency-banner', 'skyyRoseUrgency', array(
				'deadline' => $preorder_deadline,
				'message'  => __( 'Pre-Order closes in', 'skyyrose-flagship' ),
				'ctaUrl'   => home_url( '/pre-order/' ),
				'ctaText'  => __( 'Shop Now', 'skyyrose-flagship' ),
			) );
		}
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

	// Homepage V2 — localize AJAX URL, nonce, and cart URL for homepage-v2.js.
	if ( is_front_page() && wp_script_is( 'skyyrose-template-homepage-v2', 'enqueued' ) ) {
		wp_localize_script(
			'skyyrose-template-homepage-v2',
			'skyyrose_homepage',
			array(
				'ajax_url'         => admin_url( 'admin-ajax.php' ),
				'newsletter_nonce' => wp_create_nonce( 'skyyrose_newsletter' ),
				'cart_url'         => function_exists( 'wc_get_cart_url' ) ? wc_get_cart_url() : home_url( '/cart/' ),
			)
		);
	}
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
			'template-collection-black-rose.php'   => 'collection-v4',
			'template-collection-love-hurts.php'   => 'collection-v4',
			'template-collection-signature.php'    => 'collection-v4',
			'template-collection-kids-capsule.php' => 'collection',
			'template-immersive-black-rose.php'    => 'immersive',
			'template-immersive-love-hurts.php'    => 'immersive',
			'template-immersive-signature.php'     => 'immersive',
			'template-about.php'                   => 'about',
			'template-contact.php'                 => 'contact',
			'template-preorder-gateway.php'        => 'preorder-gateway',
			'template-homepage-luxury.php'         => 'front-page',
			'template-style-quiz.php'              => 'style-quiz',
			'skyyrose-canvas.php'                  => 'collections-shop',
			'template-landing-black-rose.php'      => 'landing',
			'template-landing-love-hurts.php'      => 'landing',
			'template-landing-signature.php'       => 'landing',
			'template-experiences.php'             => 'experiences',
			'template-spatial-home.php'            => 'spatial-home',
			'template-collections.php'             => 'collection',
		);

		if ( isset( $template_map[ $page_template ] ) ) {
			return $template_map[ $page_template ];
		}
	}

	// Single post.
	if ( is_single() ) {
		return 'single';
	}

	// Blog index / archive.
	if ( is_home() || is_archive() || is_search() ) {
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
		'collection'      => 'collections.css',
		'collection-v4'   => 'collection-v4.css',
		'immersive'       => 'immersive.css',
		'experiences'     => 'immersive.css',
		'spatial-home'    => 'spatial-home.css',
		'single-product'  => 'single-product.css',
		'cart'            => 'woocommerce.css',
		'checkout'        => 'woocommerce.css',
		'shop-archive'    => 'woocommerce.css',
		'about'           => 'about.css',
		'contact'         => 'contact.css',
		'preorder-gateway'  => 'preorder-gateway.css',
		'style-quiz'       => 'style-quiz.css',
		'collections-shop' => 'collections-shop.css',
		'landing'          => 'landing.css',
		'404'              => '404.css',
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

	// Brand mascot styles — loaded globally (widget appears on all pages).
	$mascot_css = $use_min && file_exists( $base_css_dir . '/mascot.min.css' ) ? 'mascot.min.css' : 'mascot.css';
	if ( file_exists( $base_css_dir . '/' . $mascot_css ) ) {
		wp_enqueue_style(
			'skyyrose-mascot',
			$base_css_uri . '/' . $mascot_css,
			$global_deps,
			SKYYROSE_VERSION
		);
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

	$template_scripts = array(
		'front-page'       => 'homepage-v2.js',
		'collection'       => 'collections.js',
		'collection-v4'    => 'collection-v4.js',
		'immersive'        => 'immersive.js',
		'single-product'   => 'single-product.js',
		'cart'             => 'woocommerce.js',
		'checkout'         => 'woocommerce.js',
		'contact'          => 'contact.js',
		'preorder-gateway'  => 'preorder-gateway.js',
		'style-quiz'       => 'style-quiz.js',
		'collections-shop' => 'collections-shop.js',
		'landing'          => 'landing-engine.js',
		'about'            => 'about.js',
	);

	$use_min = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;

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
				)
			);
		}

		// Enqueue Three.js immersive world engine (progressive enhancement over 2D).
		if ( 'immersive' === $slug ) {
			$world_path = $base_js_dir . '/immersive-world.js';
			if ( file_exists( $world_path ) ) {
				wp_enqueue_script(
					'skyyrose-immersive-world',
					$base_js_uri . '/immersive-world.js',
					array( $handle ),
					SKYYROSE_VERSION,
					true
				);
			}

			// World-specific styles (narrative panels, canvas, scroll spacer).
			$world_css = $base_css_dir . '/immersive-world.css';
			if ( file_exists( $world_css ) ) {
				wp_enqueue_style(
					'skyyrose-immersive-world',
					$base_css_uri . '/immersive-world.css',
					array( 'skyyrose-template-immersive' ),
					SKYYROSE_VERSION
				);
			}
		}

		// Enqueue immersive WooCommerce bridge + localize skyyRoseImmersive data.
		if ( 'immersive' === $slug ) {
			$bridge_path = $base_js_dir . '/immersive-wc-bridge.js';
			if ( file_exists( $bridge_path ) ) {
				wp_enqueue_script(
					'skyyrose-immersive-wc-bridge',
					$base_js_uri . '/immersive-wc-bridge.js',
					array( $handle ),
					SKYYROSE_VERSION,
					true
				);

				wp_localize_script(
					'skyyrose-immersive-wc-bridge',
					'skyyRoseImmersive',
					array(
						'ajaxUrl'  => admin_url( 'admin-ajax.php' ),
						'nonce'    => wp_create_nonce( 'skyyrose-immersive-nonce' ),
						'wcActive' => class_exists( 'WooCommerce' ),
						'cartUrl'  => function_exists( 'wc_get_cart_url' ) ? wc_get_cart_url() : home_url( '/cart/' ),
					)
				);
			}
		}

		// Holo product cards — loaded on collection pages, shop archives, and WC loop.
		if ( in_array( $slug, array( 'collection', 'collection-v4', 'collections-shop', 'front-page', 'shop-archive' ), true ) ) {
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
}


/**
 * Enqueue admin styles and scripts.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_admin_scripts() {
	$admin_css = SKYYROSE_DIR . '/assets/css/admin.css';
	if ( file_exists( $admin_css ) ) {
		wp_enqueue_style(
			'skyyrose-admin',
			SKYYROSE_ASSETS_URI . '/css/admin.css',
			array(),
			SKYYROSE_VERSION
		);
	}

	$admin_js = SKYYROSE_DIR . '/assets/js/admin.js';
	if ( file_exists( $admin_js ) ) {
		wp_enqueue_script(
			'skyyrose-admin',
			SKYYROSE_ASSETS_URI . '/js/admin.js',
			array( 'jquery' ),
			SKYYROSE_VERSION,
			true
		);
	}
}

/*--------------------------------------------------------------
 * Hook Registration
 *
 * Feature hooks → inc/enqueue-features.php
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

// Admin scripts.
add_action( 'admin_enqueue_scripts', 'skyyrose_admin_scripts' );
