<?php
/**
 * Enqueue Feature-Specific Assets
 *
 * Separated from enqueue.php to keep each file under 800 lines.
 * Contains conditional enqueue functions for feature-level CSS/JS:
 * luxury cursor, collection logos, cinematic mode, cross-sell engine,
 * model viewer, analytics beacon, and size guide.
 *
 * @package SkyyRose_Flagship
 * @since   4.1.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
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
	$use_min         = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;
	$cursor_css_file = $use_min && file_exists( SKYYROSE_DIR . '/assets/css/luxury-cursor.min.css' )
		? 'luxury-cursor.min.css' : 'luxury-cursor.css';
	if ( file_exists( SKYYROSE_DIR . '/assets/css/' . $cursor_css_file ) ) {
		wp_enqueue_style(
			'skyyrose-luxury-cursor',
			SKYYROSE_ASSETS_URI . '/css/' . $cursor_css_file,
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	// Luxury cursor JS (loaded in footer, deferred via skyyrose_defer_scripts).
	$cursor_js_file = $use_min && file_exists( SKYYROSE_DIR . '/assets/js/luxury-cursor.min.js' )
		? 'luxury-cursor.min.js' : 'luxury-cursor.js';
	if ( file_exists( SKYYROSE_DIR . '/assets/js/' . $cursor_js_file ) ) {
		wp_enqueue_script(
			'skyyrose-luxury-cursor',
			SKYYROSE_ASSETS_URI . '/js/' . $cursor_js_file,
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

	$use_min  = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;
	$logos_css = $use_min && file_exists( SKYYROSE_DIR . '/assets/css/collection-logos.min.css' )
		? 'collection-logos.min.css' : 'collection-logos.css';
	if ( file_exists( SKYYROSE_DIR . '/assets/css/' . $logos_css ) ) {
		wp_enqueue_style(
			'skyyrose-collection-logos',
			SKYYROSE_ASSETS_URI . '/css/' . $logos_css,
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	// Collection color schemes (per-collection CSS custom properties).
	$colors_css = $use_min && file_exists( SKYYROSE_DIR . '/assets/css/collection-colors.min.css' )
		? 'collection-colors.min.css' : 'collection-colors.css';
	if ( file_exists( SKYYROSE_DIR . '/assets/css/' . $colors_css ) ) {
		wp_enqueue_style(
			'skyyrose-collection-colors',
			SKYYROSE_ASSETS_URI . '/css/' . $colors_css,
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

	$use_min      = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;
	$cine_css     = $use_min && file_exists( SKYYROSE_DIR . '/assets/css/cinematic-mode.min.css' )
		? 'cinematic-mode.min.css' : 'cinematic-mode.css';
	if ( file_exists( SKYYROSE_DIR . '/assets/css/' . $cine_css ) ) {
		wp_enqueue_style(
			'skyyrose-cinematic-mode',
			SKYYROSE_ASSETS_URI . '/css/' . $cine_css,
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	$cine_js = $use_min && file_exists( SKYYROSE_DIR . '/assets/js/cinematic-mode.min.js' )
		? 'cinematic-mode.min.js' : 'cinematic-mode.js';
	if ( file_exists( SKYYROSE_DIR . '/assets/js/' . $cine_js ) ) {
		wp_enqueue_script(
			'skyyrose-cinematic-mode',
			SKYYROSE_ASSETS_URI . '/js/' . $cine_js,
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

	$use_min  = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;
	$xs_css   = $use_min && file_exists( SKYYROSE_DIR . '/assets/css/cross-sell-engine.min.css' )
		? 'cross-sell-engine.min.css' : 'cross-sell-engine.css';
	if ( file_exists( SKYYROSE_DIR . '/assets/css/' . $xs_css ) ) {
		wp_enqueue_style(
			'skyyrose-cross-sell-engine',
			SKYYROSE_ASSETS_URI . '/css/' . $xs_css,
			array( 'skyyrose-design-tokens', 'skyyrose-template-immersive' ),
			SKYYROSE_VERSION
		);
	}

	$xs_js = $use_min && file_exists( SKYYROSE_DIR . '/assets/js/cross-sell-engine.min.js' )
		? 'cross-sell-engine.min.js' : 'cross-sell-engine.js';
	if ( file_exists( SKYYROSE_DIR . '/assets/js/' . $xs_js ) ) {
		wp_enqueue_script(
			'skyyrose-cross-sell-engine',
			SKYYROSE_ASSETS_URI . '/js/' . $xs_js,
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
		'https://cdn.jsdelivr.net/npm/@google/model-viewer@4.0.0/dist/model-viewer.min.js',
		array(),
		null,
		true
	);

	// Brand avatar styles.
	$use_min  = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;
	$mv_css   = $use_min && file_exists( SKYYROSE_DIR . '/assets/css/model-viewer.min.css' )
		? 'model-viewer.min.css' : 'model-viewer.css';
	if ( file_exists( SKYYROSE_DIR . '/assets/css/' . $mv_css ) ) {
		wp_enqueue_style(
			'skyyrose-model-viewer',
			SKYYROSE_ASSETS_URI . '/css/' . $mv_css,
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}
}

/**
 * Add type="module" on model-viewer script tag.
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

	$use_min = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;
	$ab_js   = $use_min && file_exists( SKYYROSE_DIR . '/assets/js/analytics-beacon.min.js' )
		? 'analytics-beacon.min.js' : 'analytics-beacon.js';
	if ( file_exists( SKYYROSE_DIR . '/assets/js/' . $ab_js ) ) {
		wp_enqueue_script(
			'skyyrose-analytics-beacon',
			SKYYROSE_ASSETS_URI . '/js/' . $ab_js,
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
 * Enqueue Size & Fit Guide — Interactive Size Chart Modal.
 *
 * Loads the size guide CSS and JS on collection and pre-order pages.
 * The modal HTML is included via get_template_part() in the templates.
 *
 * @since 3.10.0
 * @return void
 */
function skyyrose_enqueue_size_guide() {

	$slug            = skyyrose_get_current_template_slug();
	$size_guide_slugs = array( 'collection', 'preorder-gateway', 'single-product' );

	if ( ! in_array( $slug, $size_guide_slugs, true ) ) {
		return;
	}

	$use_min = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;
	$sg_css  = $use_min && file_exists( SKYYROSE_DIR . '/assets/css/size-guide.min.css' )
		? 'size-guide.min.css' : 'size-guide.css';
	if ( file_exists( SKYYROSE_DIR . '/assets/css/' . $sg_css ) ) {
		wp_enqueue_style(
			'skyyrose-size-guide',
			SKYYROSE_ASSETS_URI . '/css/' . $sg_css,
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	$sg_js = $use_min && file_exists( SKYYROSE_DIR . '/assets/js/size-guide.min.js' )
		? 'size-guide.min.js' : 'size-guide.js';
	if ( file_exists( SKYYROSE_DIR . '/assets/js/' . $sg_js ) ) {
		wp_enqueue_script(
			'skyyrose-size-guide',
			SKYYROSE_ASSETS_URI . '/js/' . $sg_js,
			array(),
			SKYYROSE_VERSION,
			true
		);
	}
}

/*--------------------------------------------------------------
 * Hook Registration — Feature Enqueues
 *--------------------------------------------------------------*/

// Luxury cursor on static pages (priority 12, after global styles so design-tokens dep is met).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_luxury_cursor', 12 );

// Collection logo 3D rotation styles (priority 22, after template styles).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_collection_logos', 22 );

// Cinematic Mode assets on interactive pages (priority 25, after template assets).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_cinematic_mode', 25 );

// Model Viewer — 3D brand avatar on immersive/collection/preorder pages.
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_model_viewer', 28 );

// Model Viewer — type="module" attribute for ES module loading.
add_filter( 'script_loader_tag', 'skyyrose_model_viewer_module_type', 10, 2 );

// Size Guide modal on collection + preorder + single product pages.
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_size_guide', 30 );

// Cross-Sell Engine — only on immersive pages (lightweight, high ROI).
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_cross_sell_engine', 40 );

// Analytics Beacon — small footprint, essential for tracking.
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_analytics_beacon', 50 );

/*--------------------------------------------------------------
 * Social Proof + Momentum Commerce — Conversion Activation
 *--------------------------------------------------------------*/

/**
 * Enqueue Social Proof toasts and sticky CTA bar on product-facing pages.
 *
 * @since 5.0.0
 * @return void
 */
function skyyrose_enqueue_social_proof() {
	if ( is_admin() ) {
		return;
	}
	$slug         = skyyrose_get_current_template_slug();
	$active_slugs = array( 'front-page', 'collection', 'collection-v4', 'single-product', 'preorder-gateway', 'landing', 'immersive', 'collections-shop' );
	if ( ! in_array( $slug, $active_slugs, true ) ) {
		return;
	}
	$use_min = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;
	$sp_css  = $use_min && file_exists( SKYYROSE_DIR . '/assets/css/social-proof.min.css' ) ? 'social-proof.min.css' : 'social-proof.css';
	if ( file_exists( SKYYROSE_DIR . '/assets/css/' . $sp_css ) ) {
		wp_enqueue_style( 'skyyrose-social-proof', SKYYROSE_ASSETS_URI . '/css/' . $sp_css, array( 'skyyrose-design-tokens' ), SKYYROSE_VERSION );
	}
	$sp_js = $use_min && file_exists( SKYYROSE_DIR . '/assets/js/social-proof.min.js' ) ? 'social-proof.min.js' : 'social-proof.js';
	if ( file_exists( SKYYROSE_DIR . '/assets/js/' . $sp_js ) ) {
		wp_enqueue_script( 'skyyrose-social-proof', SKYYROSE_ASSETS_URI . '/js/' . $sp_js, array(), SKYYROSE_VERSION, true );
	}
}
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_social_proof', 55 );

/**
 * Enqueue Momentum Commerce (price anchoring + live ticker + spotlight) on product pages.
 *
 * @since 5.0.0
 * @return void
 */
function skyyrose_enqueue_momentum_commerce() {
	if ( is_admin() ) {
		return;
	}
	$slug         = skyyrose_get_current_template_slug();
	$active_slugs = array( 'front-page', 'collection', 'collection-v4', 'single-product', 'preorder-gateway', 'landing', 'immersive' );
	if ( ! in_array( $slug, $active_slugs, true ) ) {
		return;
	}
	$use_min = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;
	$mc_js   = $use_min && file_exists( SKYYROSE_DIR . '/assets/js/momentum-commerce.min.js' ) ? 'momentum-commerce.min.js' : 'momentum-commerce.js';
	if ( file_exists( SKYYROSE_DIR . '/assets/js/' . $mc_js ) ) {
		wp_enqueue_script( 'skyyrose-momentum-commerce', SKYYROSE_ASSETS_URI . '/js/' . $mc_js, array(), SKYYROSE_VERSION, true );
	}
}
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_momentum_commerce', 57 );
