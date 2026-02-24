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
 * Enqueue Google Fonts (Inter + Playfair Display) with font-display: swap.
 *
 * @since 3.0.0
 * @return void
 */
function skyyrose_enqueue_google_fonts() {
	$font_families = array(
		'Inter:wght@300;400;500;600;700',
		'Playfair+Display:wght@400;500;600;700;800',
	);

	$fonts_url = add_query_arg(
		array(
			'family'  => implode( '&family=', $font_families ),
			'display' => 'swap',
		),
		'https://fonts.googleapis.com/css2'
	);

	wp_enqueue_style(
		'skyyrose-google-fonts',
		esc_url_raw( $fonts_url ),
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

	// Main theme stylesheet (style.css with WordPress header).
	wp_enqueue_style(
		'skyyrose-style',
		get_stylesheet_uri(),
		array(),
		SKYYROSE_VERSION
	);

	// Design tokens: CSS custom properties for colors, spacing, typography.
	wp_enqueue_style(
		'skyyrose-design-tokens',
		SKYYROSE_ASSETS_URI . '/css/design-tokens.css',
		array( 'skyyrose-style' ),
		SKYYROSE_VERSION
	);

	// Components: reusable component styles (buttons, cards, forms, etc.).
	$components_path = SKYYROSE_DIR . '/assets/css/components.css';
	if ( file_exists( $components_path ) ) {
		wp_enqueue_style(
			'skyyrose-components',
			SKYYROSE_ASSETS_URI . '/css/components.css',
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

	// Navigation script (hamburger toggle, keyboard nav, dropdowns).
	$nav_path = SKYYROSE_DIR . '/assets/js/navigation.js';
	if ( file_exists( $nav_path ) ) {
		wp_enqueue_script(
			'skyyrose-navigation',
			SKYYROSE_ASSETS_URI . '/js/navigation.js',
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

	$handle = wp_script_is( 'skyyrose-navigation', 'enqueued' ) ? 'skyyrose-navigation' : 'jquery';

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
			'template-collection-black-rose.php'   => 'collection',
			'template-collection-love-hurts.php'   => 'collection',
			'template-collection-signature.php'    => 'collection',
			'template-collection-kids-capsule.php' => 'collection',
			'template-love-hurts.php'              => 'immersive',
			'template-immersive-black-rose.php'    => 'immersive',
			'template-immersive-love-hurts.php'    => 'immersive',
			'template-immersive-signature.php'     => 'immersive',
			'template-about.php'                   => 'about',
			'template-contact.php'                 => 'contact',
			'template-preorder-gateway.php'        => 'preorder-gateway',
			'template-homepage-luxury.php'         => 'front-page',
		);

		if ( isset( $template_map[ $page_template ] ) ) {
			return $template_map[ $page_template ];
		}
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

	$template_styles = array(
		'front-page'      => 'front-page.css',
		'collection'      => 'collections.css',
		'immersive'       => 'immersive.css',
		'single-product'  => 'woocommerce.css',
		'cart'            => 'woocommerce.css',
		'checkout'        => 'woocommerce.css',
		'shop-archive'    => 'woocommerce.css',
		'about'           => 'about.css',
		'contact'         => 'contact.css',
		'preorder-gateway' => 'preorder-gateway.css',
		'404'             => '404.css',
	);

	if ( isset( $template_styles[ $slug ] ) ) {
		$css_file = $template_styles[ $slug ];
		$handle   = 'skyyrose-template-' . sanitize_title( pathinfo( $css_file, PATHINFO_FILENAME ) );

		if ( file_exists( $base_css_dir . '/' . $css_file ) ) {
			wp_enqueue_style(
				$handle,
				$base_css_uri . '/' . $css_file,
				$global_deps,
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

	$template_scripts = array(
		'front-page'       => 'front-page.js',
		'collection'       => 'collections.js',
		'immersive'        => 'immersive.js',
		'single-product'   => 'woocommerce.js',
		'cart'             => 'woocommerce.js',
		'checkout'         => 'woocommerce.js',
		'contact'          => 'contact.js',
		'preorder-gateway' => 'preorder-gateway.js',
	);

	if ( isset( $template_scripts[ $slug ] ) ) {
		$js_file = $template_scripts[ $slug ];
		$handle  = 'skyyrose-template-' . sanitize_title( pathinfo( $js_file, PATHINFO_FILENAME ) );

		// WooCommerce JS depends on jQuery for cart/checkout/gallery interactions.
		$js_deps = ( 'woocommerce.js' === $js_file ) ? array( 'jquery' ) : array();

		if ( file_exists( $base_js_dir . '/' . $js_file ) ) {
			wp_enqueue_script(
				$handle,
				$base_js_uri . '/' . $js_file,
				$js_deps,
				SKYYROSE_VERSION,
				true
			);
		}
	}
}

/**
 * Enqueue the luxury cursor assets on all static (non-immersive) pages.
 *
 * Loads a custom animated cursor with a rose gold ring, gold center dot,
 * and sparkle trail on desktop devices. Skips immersive and preorder-gateway
 * templates where the cursor would conflict with full-screen experiences.
 *
 * @since 3.1.0
 * @return void
 */
function skyyrose_enqueue_luxury_cursor() {

	$slug = skyyrose_get_current_template_slug();

	// Skip templates where a custom cursor would conflict with the experience.
	$excluded_templates = array( 'immersive', 'preorder-gateway' );

	if ( in_array( $slug, $excluded_templates, true ) ) {
		return;
	}

	// Luxury cursor CSS.
	$cursor_css_path = SKYYROSE_DIR . '/assets/css/luxury-cursor.css';
	if ( file_exists( $cursor_css_path ) ) {
		wp_enqueue_style(
			'skyyrose-luxury-cursor',
			SKYYROSE_ASSETS_URI . '/css/luxury-cursor.css',
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	// Luxury cursor JS (loaded in footer, deferred via skyyrose_defer_scripts).
	$cursor_js_path = SKYYROSE_DIR . '/assets/js/luxury-cursor.js';
	if ( file_exists( $cursor_js_path ) ) {
		wp_enqueue_script(
			'skyyrose-luxury-cursor',
			SKYYROSE_ASSETS_URI . '/js/luxury-cursor.js',
			array(),
			SKYYROSE_VERSION,
			true
		);
	}
}

/**
 * Conditionally enqueue collection logo 3D rotation styles.
 *
 * Loads collection-logos.css only on collection template pages so the
 * rotating 3D logo animations and collection-specific card styles are available.
 *
 * @since 3.0.0
 * @return void
 */
function skyyrose_enqueue_collection_logos() {

	$slug = skyyrose_get_current_template_slug();

	if ( 'collection' !== $slug ) {
		return;
	}

	$css_path = SKYYROSE_DIR . '/assets/css/collection-logos.css';
	if ( file_exists( $css_path ) ) {
		wp_enqueue_style(
			'skyyrose-collection-logos',
			SKYYROSE_ASSETS_URI . '/css/collection-logos.css',
			array( 'skyyrose-design-tokens' ),
			'3.0.0'
		);
	}
}

/**
 * Conditionally enqueue Cinematic Mode assets.
 *
 * Loads cinematic-mode.css and cinematic-mode.js only on interactive pages:
 * immersive scenes, pre-order gateway, and WooCommerce single product.
 *
 * @since 3.1.0
 * @return void
 */
function skyyrose_enqueue_cinematic_mode() {

	$slug            = skyyrose_get_current_template_slug();
	$cinematic_slugs = array( 'immersive', 'preorder-gateway', 'single-product' );

	if ( ! in_array( $slug, $cinematic_slugs, true ) ) {
		return;
	}

	$css_path = SKYYROSE_DIR . '/assets/css/cinematic-mode.css';
	if ( file_exists( $css_path ) ) {
		wp_enqueue_style(
			'skyyrose-cinematic-mode',
			SKYYROSE_ASSETS_URI . '/css/cinematic-mode.css',
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	$js_path = SKYYROSE_DIR . '/assets/js/cinematic-mode.js';
	if ( file_exists( $js_path ) ) {
		wp_enqueue_script(
			'skyyrose-cinematic-mode',
			SKYYROSE_ASSETS_URI . '/js/cinematic-mode.js',
			array(),
			SKYYROSE_VERSION,
			true
		);
	}
}

/**
 * Enqueue the Social Proof + Urgency Engine on customer-facing pages.
 *
 * Loads purchase notification toasts, live viewer count, scarcity badges,
 * and a sticky pre-order CTA bar across all non-admin pages.
 *
 * @since 3.2.0
 * @return void
 */
function skyyrose_enqueue_social_proof() {

	// Skip admin context.
	if ( is_admin() ) {
		return;
	}

	$css_path = SKYYROSE_DIR . '/assets/css/social-proof.css';
	if ( file_exists( $css_path ) ) {
		wp_enqueue_style(
			'skyyrose-social-proof',
			SKYYROSE_ASSETS_URI . '/css/social-proof.css',
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	$js_path = SKYYROSE_DIR . '/assets/js/social-proof.js';
	if ( file_exists( $js_path ) ) {
		wp_enqueue_script(
			'skyyrose-social-proof',
			SKYYROSE_ASSETS_URI . '/js/social-proof.js',
			array(),
			SKYYROSE_VERSION,
			true
		);
	}
}

/**
 * Enqueue The Pulse — Real-Time Social Proof & Urgency Engine.
 *
 * Loads animated purchase notification toasts, live viewer counts, scarcity
 * badges, VIP countdown banner, and popularity heat on customer-facing pages.
 * This is the conversion-driving upgrade layer that spans immersive scenes,
 * collection pages, homepage, and the pre-order gateway.
 *
 * @since 3.2.0
 * @return void
 */
function skyyrose_enqueue_the_pulse() {

	// Skip admin context.
	if ( is_admin() ) {
		return;
	}

	$css_path = SKYYROSE_DIR . '/assets/css/the-pulse.css';
	if ( file_exists( $css_path ) ) {
		wp_enqueue_style(
			'skyyrose-the-pulse',
			SKYYROSE_ASSETS_URI . '/css/the-pulse.css',
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	$js_path = SKYYROSE_DIR . '/assets/js/the-pulse.js';
	if ( file_exists( $js_path ) ) {
		wp_enqueue_script(
			'skyyrose-the-pulse',
			SKYYROSE_ASSETS_URI . '/js/the-pulse.js',
			array(),
			SKYYROSE_VERSION,
			true
		);
	}
}

/**
 * Enqueue Aurora — Ambient Engagement Engine.
 *
 * Loads the conversion-driving Aurora layer on all customer-facing pages:
 * CTA shimmer, engagement depth tracking, scroll reveals, product card
 * 3D tilt, VIP countdown, and scarcity pulse indicators.
 *
 * @since 3.4.0
 * @return void
 */
function skyyrose_enqueue_aurora_engine() {

	// Skip admin context.
	if ( is_admin() ) {
		return;
	}

	$css_path = SKYYROSE_DIR . '/assets/css/aurora-engine.css';
	if ( file_exists( $css_path ) ) {
		wp_enqueue_style(
			'skyyrose-aurora-engine',
			SKYYROSE_ASSETS_URI . '/css/aurora-engine.css',
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	$js_path = SKYYROSE_DIR . '/assets/js/aurora-engine.js';
	if ( file_exists( $js_path ) ) {
		wp_enqueue_script(
			'skyyrose-aurora-engine',
			SKYYROSE_ASSETS_URI . '/js/aurora-engine.js',
			array(),
			SKYYROSE_VERSION,
			true
		);
	}
}

/**
 * Enqueue Magnetic Obsidian — Conversion Intelligence Engine.
 *
 * Loads magnetic 3D product card effects, immersive hotspot magnetism,
 * exit-intent capture overlay, A/B variant assignment, and conversion
 * tracking on all customer-facing pages.
 *
 * @since 3.5.0
 * @return void
 */
function skyyrose_enqueue_magnetic_obsidian() {

	// Skip admin context.
	if ( is_admin() ) {
		return;
	}

	$css_path = SKYYROSE_DIR . '/assets/css/magnetic-obsidian.css';
	if ( file_exists( $css_path ) ) {
		wp_enqueue_style(
			'skyyrose-magnetic-obsidian',
			SKYYROSE_ASSETS_URI . '/css/magnetic-obsidian.css',
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	$js_path = SKYYROSE_DIR . '/assets/js/magnetic-obsidian.js';
	if ( file_exists( $js_path ) ) {
		wp_enqueue_script(
			'skyyrose-magnetic-obsidian',
			SKYYROSE_ASSETS_URI . '/js/magnetic-obsidian.js',
			array(),
			SKYYROSE_VERSION,
			true
		);
	}
}

/**
 * Enqueue Cross-Sell Engine — "Complete the Look".
 *
 * Injects a glassmorphism cross-sell section into the immersive product
 * panel when a hotspot is opened. Shows 2-3 sibling products from the same
 * collection with Quick Add buttons and rose-gold particle celebrations.
 * Loaded only on immersive template pages to keep the payload minimal.
 *
 * @since 3.7.0
 * @return void
 */
function skyyrose_enqueue_cross_sell_engine() {

	$slug = skyyrose_get_current_template_slug();

	// Only active on immersive scene pages.
	if ( 'immersive' !== $slug ) {
		return;
	}

	$css_path = SKYYROSE_DIR . '/assets/css/cross-sell-engine.css';
	if ( file_exists( $css_path ) ) {
		wp_enqueue_style(
			'skyyrose-cross-sell-engine',
			SKYYROSE_ASSETS_URI . '/css/cross-sell-engine.css',
			array( 'skyyrose-design-tokens', 'skyyrose-template-immersive' ),
			SKYYROSE_VERSION
		);
	}

	$js_path = SKYYROSE_DIR . '/assets/js/cross-sell-engine.js';
	if ( file_exists( $js_path ) ) {
		wp_enqueue_script(
			'skyyrose-cross-sell-engine',
			SKYYROSE_ASSETS_URI . '/js/cross-sell-engine.js',
			array(),
			SKYYROSE_VERSION,
			true
		);
	}
}

/**
 * Enqueue Conversion Intelligence Engine.
 *
 * Real-time social proof toasts, urgency countdown timers, stock scarcity
 * indicators, floating pre-order CTA, exit-intent capture, and conversion
 * tracking. Proven to increase conversion 15-34% (Spiegel Research Center).
 *
 * @since 3.6.0
 * @return void
 */
function skyyrose_enqueue_conversion_engine() {

	// Skip admin context.
	if ( is_admin() ) {
		return;
	}

	$css_path = SKYYROSE_DIR . '/assets/css/conversion-engine.css';
	if ( file_exists( $css_path ) ) {
		wp_enqueue_style(
			'skyyrose-conversion-engine',
			SKYYROSE_ASSETS_URI . '/css/conversion-engine.css',
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	$js_path = SKYYROSE_DIR . '/assets/js/conversion-engine.js';
	if ( file_exists( $js_path ) ) {
		wp_enqueue_script(
			'skyyrose-conversion-engine',
			SKYYROSE_ASSETS_URI . '/js/conversion-engine.js',
			array(),
			SKYYROSE_VERSION,
			true
		);
	}
}

/**
 * Enqueue Adaptive Personalization Engine.
 *
 * Behavioral scoring, personalized "Your Picks" recommendations drawer,
 * ambient mood transitions on immersive pages, smart bundle suggestions,
 * and recently-viewed product strip. Research shows personalized
 * recommendations increase AOV by 10-30% (McKinsey, 2023).
 *
 * @since 3.8.0
 * @return void
 */
function skyyrose_enqueue_adaptive_personalization() {

	// Skip admin context.
	if ( is_admin() ) {
		return;
	}

	$css_path = SKYYROSE_DIR . '/assets/css/adaptive-personalization.css';
	if ( file_exists( $css_path ) ) {
		wp_enqueue_style(
			'skyyrose-adaptive-personalization',
			SKYYROSE_ASSETS_URI . '/css/adaptive-personalization.css',
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	$js_path = SKYYROSE_DIR . '/assets/js/adaptive-personalization.js';
	if ( file_exists( $js_path ) ) {
		wp_enqueue_script(
			'skyyrose-adaptive-personalization',
			SKYYROSE_ASSETS_URI . '/js/adaptive-personalization.js',
			array(),
			SKYYROSE_VERSION,
			true
		);
	}
}

/**
 * Dequeue WooCommerce default styles that conflict with theme design.
 *
 * WooCommerce loads 3 default stylesheets. We remove the general and
 * smallscreen styles to prevent layout conflicts with our design-token system,
 * but keep the layout stylesheet for grid compatibility.
 *
 * @since  3.0.0
 * @param  array $enqueue_styles WooCommerce styles to load.
 * @return array Filtered styles.
 */
function skyyrose_dequeue_woocommerce_styles( $enqueue_styles ) {

	// Remove the general WooCommerce stylesheet (buttons, forms, etc.).
	unset( $enqueue_styles['woocommerce-general'] );

	// Remove the small-screen / mobile stylesheet.
	unset( $enqueue_styles['woocommerce-smallscreen'] );

	// Keep woocommerce-layout for grid structure.
	return $enqueue_styles;
}

/**
 * Add font-display: swap to Google Fonts link tag for performance.
 *
 * @since  3.0.0
 * @param  string $html   Full link tag HTML.
 * @param  string $handle Stylesheet handle.
 * @return string Modified HTML.
 */
function skyyrose_add_font_display_swap( $html, $handle ) {
	if ( 'skyyrose-google-fonts' === $handle ) {
		$html = str_replace( "media='all'", "media='all' crossorigin", $html );
	}
	return $html;
}

/**
 * Preconnect to Google Fonts for faster font loading.
 *
 * @since 3.0.0
 * @return void
 */
function skyyrose_preconnect_fonts() {
	echo '<link rel="preconnect" href="https://fonts.googleapis.com">' . "\n";
	echo '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>' . "\n";
}

/**
 * Defer non-critical scripts for better page load performance.
 *
 * @since  3.0.0
 * @param  string $tag    Full script tag HTML.
 * @param  string $handle Script handle.
 * @return string Modified tag.
 */
function skyyrose_defer_scripts( $tag, $handle ) {

	$defer_handles = array(
		'skyyrose-navigation',
		'skyyrose-template-front-page',
		'skyyrose-template-collections',
		'skyyrose-template-immersive',
		'skyyrose-template-woocommerce',
		'skyyrose-template-contact',
		'skyyrose-template-preorder-gateway',
		'skyyrose-cinematic-mode',
		'skyyrose-luxury-cursor',
		'skyyrose-social-proof',
		'skyyrose-the-pulse',
		'skyyrose-aurora-engine',
		'skyyrose-magnetic-obsidian',
		'skyyrose-conversion-engine',
		'skyyrose-cross-sell-engine',
		'skyyrose-adaptive-personalization',
	);

	if ( in_array( $handle, $defer_handles, true ) ) {
		return str_replace( ' src', ' defer src', $tag );
	}

	return $tag;
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
 *--------------------------------------------------------------*/

// Preconnect (very early in <head>).
add_action( 'wp_head', 'skyyrose_preconnect_fonts', 1 );

// Google Fonts (priority 5 so they load before template styles).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_google_fonts', 5 );

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

// Collection logo 3D rotation styles (priority 22, after template styles).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_collection_logos', 22 );

// Cinematic Mode assets on interactive pages (priority 25, after template assets).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_cinematic_mode', 25 );

// Luxury cursor on static pages (priority 12, after global styles so design-tokens dep is met).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_luxury_cursor', 12 );

// Dequeue conflicting WooCommerce default styles.
add_filter( 'woocommerce_enqueue_styles', 'skyyrose_dequeue_woocommerce_styles' );

// Add crossorigin to Google Fonts link.
add_filter( 'style_loader_tag', 'skyyrose_add_font_display_swap', 10, 2 );

// Defer non-critical scripts.
add_filter( 'script_loader_tag', 'skyyrose_defer_scripts', 10, 2 );

// Social Proof + Urgency Engine on customer-facing pages (priority 30, after all template assets).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_social_proof', 30 );

// The Pulse — Real-Time Social Proof & Urgency Engine (priority 32, after social proof base).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_the_pulse', 32 );

// Aurora — Ambient Engagement Engine on customer-facing pages (priority 34, after Pulse).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_aurora_engine', 34 );

// Magnetic Obsidian — Conversion Intelligence Engine (priority 36, after Aurora).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_magnetic_obsidian', 36 );

// Conversion Intelligence Engine on customer-facing pages (priority 38, after Magnetic Obsidian).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_conversion_engine', 38 );

// Cross-Sell Engine — "Complete the Look" on immersive pages only (priority 40, after immersive template script).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_cross_sell_engine', 40 );

// Adaptive Personalization Engine — behavioral scoring, recommendations, mood engine (priority 42, after cross-sell).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_adaptive_personalization', 42 );

// Admin scripts.
add_action( 'admin_enqueue_scripts', 'skyyrose_admin_scripts' );
