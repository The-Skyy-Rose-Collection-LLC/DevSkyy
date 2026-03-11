<?php
/**
 * SkyyRose Flagship Theme Functions
 *
 * Main bootstrap file. Defines theme constants and loads modular inc/ files.
 * All heavy logic is delegated to individual inc/ modules for maintainability.
 *
 * @package SkyyRose_Flagship
 * @since   1.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/*--------------------------------------------------------------
 * Theme Constants
 *--------------------------------------------------------------*/
define( 'SKYYROSE_VERSION', '4.0.0' );
define( 'SKYYROSE_DIR', get_template_directory() );
define( 'SKYYROSE_URI', get_template_directory_uri() );

// Legacy aliases for backward compatibility with existing templates.
define( 'SKYYROSE_THEME_DIR', SKYYROSE_DIR );
define( 'SKYYROSE_THEME_URI', SKYYROSE_URI );
define( 'SKYYROSE_ASSETS_URI', SKYYROSE_URI . '/assets' );

/*--------------------------------------------------------------
 * Disable WordPress.com CSS/JS Concatenation
 *
 * WordPress.com's concatenation service (_jb_static) can cause
 * MIME type errors and 404s. Disable it to serve files directly.
 *--------------------------------------------------------------*/
if ( ! defined( 'CONCATENATE_SCRIPTS' ) ) {
	define( 'CONCATENATE_SCRIPTS', false );
}
$GLOBALS['concatenate_scripts'] = false;

/*--------------------------------------------------------------
 * Core Includes (always loaded)
 *--------------------------------------------------------------*/
$skyyrose_core_includes = array(
	'/inc/ai-providers.php',
	'/inc/theme-setup.php',
	'/inc/product-catalog.php',
	'/inc/interactive-grid.php',
	'/inc/enqueue.php',
	'/inc/enqueue-features.php',
	'/inc/enqueue-performance.php',
	'/inc/enqueue-engines.php',
	'/inc/customizer.php',
	'/inc/template-functions.php',
	'/inc/security.php',
	'/inc/accessibility-seo.php',
	'/inc/seo.php',
	'/inc/ajax-handlers.php',
	'/inc/product-taxonomy.php',
	'/inc/branded-content.php',
	'/inc/facebook-sdk.php',
	'/inc/menu-setup.php',
	'/inc/theme-activation-setup.php',
);

foreach ( $skyyrose_core_includes as $skyyrose_file ) {
	$skyyrose_filepath = SKYYROSE_DIR . $skyyrose_file;
	if ( file_exists( $skyyrose_filepath ) ) {
		require_once $skyyrose_filepath;
	}
}

/*--------------------------------------------------------------
 * WooCommerce Includes (loaded only when WooCommerce is active)
 *--------------------------------------------------------------*/
if ( class_exists( 'WooCommerce' ) ) {
	$skyyrose_woo_includes = array(
		'/inc/woocommerce.php',
		'/inc/wc-product-functions.php',
		'/inc/immersive-ajax.php',
		'/inc/wishlist-functions.php',
		'/inc/class-wishlist-widget.php',
	);

	foreach ( $skyyrose_woo_includes as $skyyrose_file ) {
		$skyyrose_filepath = SKYYROSE_DIR . $skyyrose_file;
		if ( file_exists( $skyyrose_filepath ) ) {
			require_once $skyyrose_filepath;
		}
	}
}

/*--------------------------------------------------------------
 * Elementor Include (loaded only when Elementor is active)
 *--------------------------------------------------------------*/
add_action( 'elementor/loaded', function () {
	$elementor_path = SKYYROSE_DIR . '/inc/elementor.php';
	if ( file_exists( $elementor_path ) ) {
		require_once $elementor_path;
	}
} );

/*--------------------------------------------------------------
 * Admin Includes (loaded only in wp-admin context)
 *--------------------------------------------------------------*/
if ( is_admin() ) {
	$skyyrose_admin_includes = array(
		'/inc/deployment-checklist.php',
	);

	foreach ( $skyyrose_admin_includes as $skyyrose_file ) {
		$skyyrose_filepath = SKYYROSE_DIR . $skyyrose_file;
		if ( file_exists( $skyyrose_filepath ) ) {
			require_once $skyyrose_filepath;
		}
	}
}

/*--------------------------------------------------------------
 * Brand Styles: variables, luxury theme, collection colors (priority 5)
 *--------------------------------------------------------------*/
$skyyrose_brand_styles_path = SKYYROSE_DIR . '/inc/enqueue-brand-styles.php';
if ( file_exists( $skyyrose_brand_styles_path ) ) {
	require_once $skyyrose_brand_styles_path;
}

/*--------------------------------------------------------------
 * Force Page Templates
 *
 * WordPress.com's block theme layer can override classic template
 * resolution. This filter ensures our custom page templates load
 * correctly for specific pages.
 *--------------------------------------------------------------*/
add_filter( 'template_include', function ( $template ) {
	// Collections "Shop All" page → skyyrose-canvas.php
	// Uses slug matching instead of hardcoded page ID (IDs differ between environments).
	if ( is_page( 'collections' ) ) {
		$canvas = SKYYROSE_DIR . '/skyyrose-canvas.php';
		if ( file_exists( $canvas ) ) {
			return $canvas;
		}
	}
	return $template;
}, 99 );

/*--------------------------------------------------------------
 * Brand Mascot Widget
 *
 * Loads the interactive mascot template part in the footer of
 * all front-end pages. Skips admin and REST API contexts.
 *--------------------------------------------------------------*/
add_action( 'wp_footer', function () {
	if ( is_admin() || ( defined( 'REST_REQUEST' ) && REST_REQUEST ) ) {
		return;
	}
	get_template_part( 'template-parts/mascot' );
	get_template_part( 'template-parts/brand-ambassador' );
} );
