<?php
/**
 * SkyyRose Theme Functions
 *
 * Main bootstrap file. Defines theme constants and loads modular inc/ files.
 * All heavy logic is delegated to individual inc/ modules for maintainability.
 *
 * @package SkyyRose
 * @since   1.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/*
--------------------------------------------------------------
 * Theme Constants
 *--------------------------------------------------------------*/
define( 'SKYYROSE_VERSION', '1.1.0' );
define( 'SKYYROSE_DIR', get_template_directory() );
define( 'SKYYROSE_URI', get_template_directory_uri() );

// Legacy aliases for backward compatibility with existing templates.
define( 'SKYYROSE_THEME_DIR', SKYYROSE_DIR );
define( 'SKYYROSE_THEME_URI', SKYYROSE_URI );
define( 'SKYYROSE_ASSETS_URI', SKYYROSE_URI . '/assets' );

/*
--------------------------------------------------------------
 * Disable WordPress.com CSS/JS Concatenation
 *
 * WordPress.com's concatenation service (_jb_static) can cause
 * MIME type errors and 404s. Disable it to serve files directly.
 *--------------------------------------------------------------*/
if ( ! defined( 'CONCATENATE_SCRIPTS' ) ) {
	define( 'CONCATENATE_SCRIPTS', false ); // phpcs:ignore WordPress.NamingConventions.PrefixAllGlobals.NonPrefixedConstantFound -- WP core constant.
}
$GLOBALS['concatenate_scripts'] = false;

/*
--------------------------------------------------------------
 * Core Includes (always loaded)
 *--------------------------------------------------------------*/
$skyyrose_core_includes = array(
	// SoT constants generated from assets/brand/brand.yaml — load FIRST so every
	// downstream include can reference SKYYROSE_BRAND_TAGLINE, SKYYROSE_COLOR_*,
	// skyyrose_brand_collections(), skyyrose_json_ld_organization(), etc.
	'/inc/brand.generated.php',
	'/inc/theme-setup.php',
	'/inc/brand-colors.php',
	'/inc/collections-config.php',
	'/inc/enqueue.php',
	'/inc/enqueue-performance.php',
	'/inc/customizer.php',
	'/inc/template-functions.php',
	'/inc/security.php',
	'/inc/accessibility-fix.php',
	'/inc/accessibility-seo.php',
	'/inc/seo.php',
	'/inc/ajax-handlers.php',
	'/inc/collection-content.php',
	'/inc/product-catalog.php',
	'/inc/product-catalog-display.php',
	'/inc/landing-data.php',
	'/inc/immersive-data.php',
	'/inc/immersive-product-adapter.php',
	'/inc/product-taxonomy.php',
	'/inc/facebook-sdk.php',
	'/inc/menu-setup.php',
	'/inc/theme-activation-setup.php',
	'/inc/klaviyo-integration.php',
	'/inc/experience-engine.php',
	'/inc/fastapi-client.php',
	'/inc/rest-api-experience.php',
	'/inc/personalization.php',
	'/inc/performance-guardian.php',
	'/inc/performance.php',
	'/inc/patterns.php',
	'/inc/garment-upload-shortcode.php',
	'/inc/visual-similarity-shortcode.php',
);

foreach ( $skyyrose_core_includes as $skyyrose_file ) {
	$skyyrose_filepath = SKYYROSE_DIR . $skyyrose_file;
	if ( file_exists( $skyyrose_filepath ) ) {
		require_once $skyyrose_filepath;
	}
}

/*
--------------------------------------------------------------
 * WooCommerce Includes (loaded only when WooCommerce is active)
 *--------------------------------------------------------------*/
if ( class_exists( 'WooCommerce' ) ) {
	$skyyrose_woo_includes = array(
		'/inc/woocommerce.php',
		'/inc/woocommerce-preorder.php',
		'/inc/wc-product-functions.php',
		'/inc/immersive-ajax.php',
		'/inc/wishlist-functions.php',
		'/inc/class-wishlist-widget.php',
		'/inc/experience-analyzer.php',
		'/inc/woocommerce-kids-capsule.php',
		'/inc/rest-kids-capsule.php',
	);

	foreach ( $skyyrose_woo_includes as $skyyrose_file ) {
		$skyyrose_filepath = SKYYROSE_DIR . $skyyrose_file;
		if ( file_exists( $skyyrose_filepath ) ) {
			require_once $skyyrose_filepath;
		}
	}
}

/*
--------------------------------------------------------------
 * Page Builder Includes
 *--------------------------------------------------------------*/
require_once SKYYROSE_DIR . '/inc/builders/detection.php';

// Elementor — preserve same hook timing as the original loading.
add_action(
	'elementor/loaded',
	function () {
		$files = array(
			'/inc/builders/elementor.php',
			'/inc/builders/elementor-compat.php',
		);
		foreach ( $files as $file ) {
			$path = SKYYROSE_DIR . $file;
			if ( file_exists( $path ) ) {
				require_once $path;
			}
		}
	}
);

// Divi, Beaver Builder, Bricks — self-guarded stubs.
$skyyrose_builder_stubs = array(
	'/inc/builders/divi.php',
	'/inc/builders/beaver-builder.php',
	'/inc/builders/bricks.php',
);
foreach ( $skyyrose_builder_stubs as $skyyrose_stub ) {
	$path = SKYYROSE_DIR . $skyyrose_stub;
	if ( file_exists( $path ) ) {
		require_once $path;
	}
}

/* Admin includes and brand styles removed in v5.2.0 — dead code cleanup. */

/* Mascot + brand-ambassador removed in v5.2.0. */
