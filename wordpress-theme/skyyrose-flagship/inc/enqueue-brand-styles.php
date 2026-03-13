<?php
/**
 * Brand Styles Enqueue
 *
 * Enqueues brand CSS files in the correct order.
 * CRITICAL: NO @import statements in CSS files (WordPress.com CDN breaks them)
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Enqueue brand styles in proper dependency order.
 *
 * @since 2.0.0
 */
function skyyrose_enqueue_brand_styles() {

	$css_dir = SKYYROSE_DIR . '/assets/css';
	$css_uri = SKYYROSE_ASSETS_URI . '/css';
	$use_min = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;

	// 1. Brand Variables (loaded first, no dependencies).
	$bv_file = $use_min && file_exists( $css_dir . '/brand-variables.min.css' )
		? 'brand-variables.min.css' : 'brand-variables.css';
	if ( file_exists( $css_dir . '/' . $bv_file ) ) {
		wp_enqueue_style(
			'skyyrose-brand-variables',
			$css_uri . '/' . $bv_file,
			array(),
			SKYYROSE_VERSION
		);
	}

	// 2. Luxury Theme (depends on brand-variables).
	$lt_file = $use_min && file_exists( $css_dir . '/luxury-theme.min.css' )
		? 'luxury-theme.min.css' : 'luxury-theme.css';
	if ( file_exists( $css_dir . '/' . $lt_file ) ) {
		wp_enqueue_style(
			'skyyrose-luxury-theme',
			$css_uri . '/' . $lt_file,
			array( 'skyyrose-brand-variables' ),
			SKYYROSE_VERSION
		);
	}

	// 3. Collection Colors (depends on brand-variables).
	$cc_file = $use_min && file_exists( $css_dir . '/collection-colors.min.css' )
		? 'collection-colors.min.css' : 'collection-colors.css';
	if ( file_exists( $css_dir . '/' . $cc_file ) ) {
		wp_enqueue_style(
			'skyyrose-collection-colors',
			$css_uri . '/' . $cc_file,
			array( 'skyyrose-brand-variables' ),
			SKYYROSE_VERSION
		);
	}
}
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_brand_styles', 5 );

/**
 * Add inline style for critical CSS variables.
 * This ensures brand variables are available immediately.
 *
 * @since 2.0.0
 */
function skyyrose_inline_critical_css() {
	$critical_css = '
		:root {
			--rose-gold: #B76E79;
			--gold: #D4AF37;
			--silver: #C0C0C0;
			--font-heading: "Playfair Display", Georgia, serif;
			--font-body: "Cormorant Garamond", Georgia, serif;
		}
	';

	wp_add_inline_style( 'skyyrose-brand-variables', $critical_css );
}
add_action( 'wp_enqueue_scripts', 'skyyrose_inline_critical_css', 6 );

// Font preloading moved to inc/enqueue.php (self-hosted fonts, GDPR-compliant).
