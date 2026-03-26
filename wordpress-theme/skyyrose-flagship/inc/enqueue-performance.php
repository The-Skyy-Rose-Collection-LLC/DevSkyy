<?php
/**
 * Enqueue Performance Optimizations
 *
 * Separated from enqueue.php to keep each file under 800 lines.
 * Contains WooCommerce style dequeuing, font preloading, resource hints,
 * and script defer logic.
 *
 * @package SkyyRose_Flagship
 * @since   4.1.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
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
 * All Google Fonts preconnects removed — fonts fully self-hosted since 4.1.0.
 * Only external preconnect remaining: cdn.jsdelivr.net (model-viewer CDN).
 *
 * @since  3.2.1
 * @param  array  $urls          URLs to print for resource hint.
 * @param  string $relation_type The resource hint relation (dns-prefetch, preconnect, etc.).
 * @return array Modified URLs.
 */
function skyyrose_resource_hints( $urls, $relation_type ) {
	// Preconnect to model-viewer CDN (used on avatar pages).
	if ( 'preconnect' === $relation_type ) {
		$urls[] = array(
			'href'        => 'https://cdn.jsdelivr.net',
			'crossorigin' => 'anonymous',
		);
		// Google Fonts preconnects removed in 4.1.0 — all fonts self-hosted.
	}
	return $urls;
}

/**
 * Defer non-critical scripts for better page load performance.
 *
 * Uses a prefix-based approach instead of a hardcoded list, so newly
 * added scripts with the skyyrose- prefix automatically get deferred.
 *
 * @since  3.0.0
 * @since  4.1.0 Switched from hardcoded list to prefix matching.
 * @param  string $tag    Full script tag HTML.
 * @param  string $handle Script handle.
 * @return string Modified tag.
 */
function skyyrose_defer_scripts( $tag, $handle ) {

	// All theme scripts should be deferred except critical inline.
	// Skip scripts that already have defer or async attributes.
	if ( strpos( $tag, ' defer' ) !== false || strpos( $tag, ' async' ) !== false ) {
		return $tag;
	}

	// Defer all skyyrose-prefixed scripts and WC variation scripts loaded in footer.
	$should_defer = (
		0 === strpos( $handle, 'skyyrose-' ) ||
		'wc-add-to-cart-variation' === $handle
	);

	// Never defer jQuery or WordPress core scripts that other scripts depend on synchronously.
	$never_defer = array( 'jquery', 'jquery-core', 'jquery-migrate', 'wp-polyfill' );
	if ( in_array( $handle, $never_defer, true ) ) {
		$should_defer = false;
	}

	if ( $should_defer ) {
		return preg_replace( '/(<script\b[^>]*)\ssrc=/i', '$1 defer src=', $tag, 1 );
	}

	return $tag;
}

/**
 * Add fetchpriority="high" to critical above-fold stylesheets.
 *
 * Tells the browser to prioritize design tokens and main styles that
 * affect First Contentful Paint (FCP) and Largest Contentful Paint (LCP).
 *
 * @since  4.1.0
 * @param  string $html   Link tag HTML.
 * @param  string $handle Style handle.
 * @return string Modified tag.
 */
function skyyrose_critical_style_priority( $html, $handle ) {
	$critical_handles = array(
		'skyyrose-design-tokens',
		'skyyrose-main',
		'skyyrose-fonts',
		'skyyrose-style',
		'skyyrose-brand-variables',
	);

	if ( in_array( $handle, $critical_handles, true ) ) {
		// Add media="all" fetchpriority hint via data attribute for resource prioritization.
		$html = str_replace( "media='all'", "media='all' fetchpriority='high'", $html );
	}

	return $html;
}

/**
 * Preload the hero image on the front page for faster LCP.
 *
 * @since 4.1.0
 * @return void
 */
function skyyrose_preload_hero_image() {
	if ( ! is_front_page() ) {
		return;
	}

	// Preload hero background — this is typically the LCP element.
	$hero_image = get_theme_mod( 'skyyrose_hero_image', '' );
	if ( $hero_image ) {
		printf(
			'<link rel="preload" href="%s" as="image" fetchpriority="high">' . "\n",
			esc_url( $hero_image )
		);
	}
}

/*--------------------------------------------------------------
 * Hook Registration — Performance Optimizations
 *--------------------------------------------------------------*/

// Resource hints for external services (model-viewer CDN, etc.).
add_filter( 'wp_resource_hints', 'skyyrose_resource_hints', 10, 2 );

// Preload critical font files in <head>.
add_action( 'wp_head', 'skyyrose_preload_fonts', 3 );

// Dequeue conflicting WooCommerce default styles.
add_filter( 'woocommerce_enqueue_styles', 'skyyrose_dequeue_woocommerce_styles' );

// Defer non-critical scripts.
add_filter( 'script_loader_tag', 'skyyrose_defer_scripts', 10, 2 );

// Prioritize critical stylesheets for faster FCP/LCP.
add_filter( 'style_loader_tag', 'skyyrose_critical_style_priority', 10, 2 );

// Preload hero image on front page for better LCP.
add_action( 'wp_head', 'skyyrose_preload_hero_image', 4 );
