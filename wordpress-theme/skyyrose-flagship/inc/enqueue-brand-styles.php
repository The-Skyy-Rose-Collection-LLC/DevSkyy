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
	// 1. Brand Variables (loaded first, no dependencies)
	wp_enqueue_style(
		'skyyrose-brand-variables',
		get_template_directory_uri() . '/assets/css/brand-variables.css',
		array(),
		SKYYROSE_VERSION
	);

	// 2. Luxury Theme (depends on brand-variables)
	wp_enqueue_style(
		'skyyrose-luxury-theme',
		get_template_directory_uri() . '/assets/css/luxury-theme.css',
		array( 'skyyrose-brand-variables' ),
		SKYYROSE_VERSION
	);

	// 3. Collection Colors (depends on brand-variables)
	wp_enqueue_style(
		'skyyrose-collection-colors',
		get_template_directory_uri() . '/assets/css/collection-colors.css',
		array( 'skyyrose-brand-variables' ),
		SKYYROSE_VERSION
	);
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
			--font-body: "Montserrat", "Helvetica Neue", Arial, sans-serif;
		}
	';

	wp_add_inline_style( 'skyyrose-brand-variables', $critical_css );
}
add_action( 'wp_enqueue_scripts', 'skyyrose_inline_critical_css', 6 );

/**
 * Preload brand fonts for performance.
 *
 * @since 2.0.0
 */
function skyyrose_preload_fonts() {
	?>
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
	<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Montserrat:wght@300;400;500;600;700&family=Cormorant+Garamond:wght@300;400;500;600;700&display=swap" rel="stylesheet">
	<?php
}
add_action( 'wp_head', 'skyyrose_preload_fonts', 1 );
