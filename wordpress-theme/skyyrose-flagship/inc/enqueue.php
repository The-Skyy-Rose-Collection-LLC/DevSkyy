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
 * Enqueue self-hosted fonts (Inter + Playfair Display).
 *
 * GDPR-compliant: no external requests to Google Fonts.
 * Font files are served from assets/fonts/ as woff2 variable fonts.
 *
 * @since 3.2.1
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

	// Header: navbar, search overlay, mobile menu, dropdowns.
	$header_path = SKYYROSE_DIR . '/assets/css/header.css';
	if ( file_exists( $header_path ) ) {
		wp_enqueue_style(
			'skyyrose-header',
			SKYYROSE_ASSETS_URI . '/css/header.css',
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	// Footer: newsletter bar, grid columns, copyright bar, brand column.
	$footer_path = SKYYROSE_DIR . '/assets/css/footer.css';
	if ( file_exists( $footer_path ) ) {
		wp_enqueue_style(
			'skyyrose-footer',
			SKYYROSE_ASSETS_URI . '/css/footer.css',
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

	// Brand mascot interactive widget (walks on from right side).
	$mascot_js_path = SKYYROSE_DIR . '/assets/js/mascot.js';
	if ( file_exists( $mascot_js_path ) && ! is_admin() ) {
		wp_enqueue_script(
			'skyyrose-mascot',
			SKYYROSE_ASSETS_URI . '/js/mascot.js',
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
			)
		);
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
			'template-collection-black-rose.php'   => 'collection',
			'template-collection-love-hurts.php'   => 'collection',
			'template-collection-signature.php'    => 'collection',
			'template-collection-kids-capsule.php' => 'collection',
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
	$use_min      = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;

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
		'single-product' => 'woocommerce-single.css',
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
	if ( file_exists( $base_css_dir . '/mascot.css' ) ) {
		wp_enqueue_style(
			'skyyrose-mascot',
			$base_css_uri . '/mascot.css',
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
				)
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
			SKYYROSE_VERSION
		);
	}

	// Collection color schemes (per-collection CSS custom properties).
	$colors_path = SKYYROSE_DIR . '/assets/css/collection-colors.css';
	if ( file_exists( $colors_path ) ) {
		wp_enqueue_style(
			'skyyrose-collection-colors',
			SKYYROSE_ASSETS_URI . '/css/collection-colors.css',
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
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
 * Enqueue Model Viewer — 3D Brand Avatar.
 *
 * Loads Google model-viewer web component and the brand-avatar stylesheet
 * on pages that include the brand-avatar template part (immersive scenes,
 * collection pages, and the pre-order gateway).
 *
 * @since 3.2.0
 * @return void
 */
function skyyrose_enqueue_model_viewer() {

	$slug              = skyyrose_get_current_template_slug();
	$model_viewer_slugs = array( 'immersive', 'collection', 'preorder-gateway', 'front-page' );

	if ( ! in_array( $slug, $model_viewer_slugs, true ) ) {
		return;
	}

	// Google model-viewer web component (type="module").
	wp_enqueue_script(
		'google-model-viewer',
		'https://ajax.googleapis.com/ajax/libs/model-viewer/4.0/model-viewer.min.js',
		array(),
		'4.0',
		true
	);

	// Brand avatar styles.
	$css_path = SKYYROSE_DIR . '/assets/css/model-viewer.css';
	if ( file_exists( $css_path ) ) {
		wp_enqueue_style(
			'skyyrose-model-viewer',
			SKYYROSE_ASSETS_URI . '/css/model-viewer.css',
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}
}

/**
 * Add type="module" to model-viewer script tag.
 *
 * model-viewer requires ES module loading via type="module".
 *
 * @since  3.2.0
 * @param  string $tag    Full script tag HTML.
 * @param  string $handle Script handle.
 * @return string Modified tag.
 */
function skyyrose_model_viewer_module_type( $tag, $handle ) {
	if ( 'google-model-viewer' === $handle ) {
		// Remove existing type attribute before adding type="module" to avoid duplication.
		$tag = preg_replace( '/(<script)\s+type=[\'"]text\/javascript[\'"]/', '$1', $tag );
		$tag = str_replace( '<script ', '<script type="module" crossorigin="anonymous" ', $tag );
		return $tag;
	}
	return $tag;
}

/**
 * Enqueue Analytics Beacon — Unified Event Relay.
 *
 * Collects conversion events from all SkyyRose engines (CIE, Aurora,
 * Pulse, Magnetic Obsidian, Cross-Sell, Journey Gamification, APE)
 * and batches them to the devskyy.app Conversion Analytics API.
 * Uses navigator.sendBeacon for reliable page-unload delivery.
 *
 * @since 3.9.0
 * @return void
 */
function skyyrose_enqueue_analytics_beacon() {

	// Skip admin context.
	if ( is_admin() ) {
		return;
	}

	$js_path = SKYYROSE_DIR . '/assets/js/analytics-beacon.js';
	if ( file_exists( $js_path ) ) {
		wp_enqueue_script(
			'skyyrose-analytics-beacon',
			SKYYROSE_ASSETS_URI . '/js/analytics-beacon.js',
			array(),
			SKYYROSE_VERSION,
			true
		);

		wp_localize_script( 'skyyrose-analytics-beacon', 'skyyBeaconConfig', array(
			'endpoint'      => 'https://devskyy.app/api/conversion',
			'flushInterval' => 5000,
		) );
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
 * Add font preload hints for critical above-fold fonts.
 *
 * Preloads latin subsets (used by all page content) for fastest
 * first-paint. Latin-ext subsets load on demand via unicode-range.
 *
 * @since  3.2.1
 * @return void
 */
function skyyrose_preload_fonts() {
	$fonts_dir = SKYYROSE_ASSETS_URI . '/fonts';
	?>
	<link rel="preload" href="<?php echo esc_url( $fonts_dir . '/inter-latin.woff2' ); ?>" as="font" type="font/woff2" crossorigin>
	<link rel="preload" href="<?php echo esc_url( $fonts_dir . '/playfair-display-latin.woff2' ); ?>" as="font" type="font/woff2" crossorigin>
	<?php
}

/**
 * Resource hints for external services.
 *
 * Google Fonts preconnects removed in 3.2.1 (fonts self-hosted for GDPR).
 * Kept as filter hook point for future external service preconnects.
 *
 * @since  3.2.1
 * @param  array  $urls          URLs to print for resource hint.
 * @param  string $relation_type The resource hint relation (dns-prefetch, preconnect, etc.).
 * @return array Modified URLs.
 */
function skyyrose_resource_hints( $urls, $relation_type ) {
	// Preconnect to Google model-viewer CDN (used on avatar pages).
	if ( 'preconnect' === $relation_type ) {
		$urls[] = array(
			'href'        => 'https://ajax.googleapis.com',
			'crossorigin' => 'anonymous',
		);
	}
	return $urls;
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
		'skyyrose-journey-gamification',
		'skyyrose-momentum-commerce',
		'skyyrose-velocity-scroll',
		'skyyrose-analytics-beacon',
		'skyyrose-immersive-wc-bridge',
	);

	if ( in_array( $handle, $defer_handles, true ) && strpos( $tag, ' defer' ) === false ) {
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

// Resource hints for external services (model-viewer CDN, etc.).
add_filter( 'wp_resource_hints', 'skyyrose_resource_hints', 10, 2 );

// Preload critical font files in <head>.
add_action( 'wp_head', 'skyyrose_preload_fonts', 3 );

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

// Collection logo 3D rotation styles (priority 22, after template styles).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_collection_logos', 22 );

// Cinematic Mode assets on interactive pages (priority 25, after template assets).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_cinematic_mode', 25 );

// Luxury cursor on static pages (priority 12, after global styles so design-tokens dep is met).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_luxury_cursor', 12 );

// Dequeue conflicting WooCommerce default styles.
add_filter( 'woocommerce_enqueue_styles', 'skyyrose_dequeue_woocommerce_styles' );

// Defer non-critical scripts.
add_filter( 'script_loader_tag', 'skyyrose_defer_scripts', 10, 2 );

// Model Viewer — 3D brand avatar on immersive/collection/preorder pages.
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_model_viewer', 28 );

// Model Viewer — type="module" attribute for ES module loading.
add_filter( 'script_loader_tag', 'skyyrose_model_viewer_module_type', 10, 2 );

// Cross-Sell Engine — only on immersive pages (lightweight, high ROI).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_cross_sell_engine', 40 );

// Analytics Beacon — small footprint, essential for tracking.
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_analytics_beacon', 50 );

// Admin scripts.
add_action( 'admin_enqueue_scripts', 'skyyrose_admin_scripts' );
