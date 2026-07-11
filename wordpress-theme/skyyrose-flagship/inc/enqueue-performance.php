<?php
/**
 * Enqueue Performance Optimizations
 *
 * Separated from enqueue.php to keep each file under 800 lines.
 * Contains WooCommerce style dequeuing, font preloading, resource hints,
 * and script defer logic.
 *
 * @package SkyyRose
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
	<link rel="preload" href="<?php echo esc_url( $fonts_dir . '/archivo-latin.woff2' ); ?>" as="font" type="font/woff2" crossorigin>
	<link rel="preload" href="<?php echo esc_url( $fonts_dir . '/hanken-grotesk-latin.woff2' ); ?>" as="font" type="font/woff2" crossorigin>
	<link rel="preload" href="<?php echo esc_url( $fonts_dir . '/anton-latin.woff2' ); ?>" as="font" type="font/woff2" crossorigin>
	<?php
	// Cinzel is above-fold ONLY on Black Rose pages (collection + immersive
	// templates). Skip the preload elsewhere so non-BR pages don't waste
	// bandwidth on a font they never render.
	$slug = function_exists( 'skyyrose_get_current_template_slug' ) ? skyyrose_get_current_template_slug() : '';
	if ( in_array( $slug, array( 'collection', 'collection-standalone', 'immersive' ), true ) ) {
		$queried = get_queried_object();
		$is_br   = $queried && isset( $queried->post_name )
			&& false !== strpos( (string) $queried->post_name, 'black-rose' );
		if ( $is_br ) {
			?>
			<link rel="preload" href="<?php echo esc_url( $fonts_dir . '/cinzel-latin.woff2' ); ?>" as="font" type="font/woff2" crossorigin>
			<?php
		}
	}
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
 * Preload the hero/LCP image for the current template.
 *
 * Front page: preloads the hero background from Customizer.
 * Single product: preloads the main product image (above-fold gallery).
 * Collection/immersive: preloads the featured image (hero banner).
 *
 * @since 4.1.0
 * @since 6.4.0 Extended to single product, collection, and immersive pages.
 * @return void
 */
function skyyrose_preload_hero_image() {
	$image_url = '';

	if ( is_front_page() ) {
		$image_url = get_theme_mod( 'skyyrose_hero_image', '' );
	} elseif ( function_exists( 'is_product' ) && is_product() ) {
		// Single product: the main gallery image is the LCP element.
		// $GLOBALS['product'] can hold non-WC_Product values when third-party
		// callbacks fire before wp_head priority 4 — only adopt a fresh
		// resolution when the helper returns a valid WC_Product so we never
		// write null/false back to the global.
		//
		// Jetpack Photon rewrites product image URLs to its CDN on delivery.
		// Preloading the local URL wastes a connection — the browser loads
		// the local URL then immediately redirects to the Photon CDN URL,
		// losing the preload benefit. Skip the preload entirely when Photon
		// is active so the browser's own LCP heuristic takes over.
		if ( ! function_exists( 'jetpack_photon_url' ) ) {
			global $product;
			if ( ! $product instanceof WC_Product ) {
				$resolved = skyyrose_current_wc_product();
				if ( $resolved instanceof WC_Product ) {
					$product = $resolved;
				}
			}
			if ( $product instanceof WC_Product && $product->get_image_id() ) {
				// Use WC's "woocommerce_single" sized variant (~300-600KB) instead
				// of wp_get_attachment_url() which returns the raw original
				// (often 2-3MB). Cuts PDP preload payload ~80%. (audit 2026-05-23)
				$image_url = wp_get_attachment_image_url( $product->get_image_id(), 'woocommerce_single' );
				if ( ! $image_url ) {
					$image_url = wp_get_attachment_url( $product->get_image_id() );
				}
			}
		}
	} elseif ( is_page() ) {
		// Collection and immersive pages: preload featured image if set.
		// 'large' (max 1024px) instead of 'full' — full is typically 2-4MB
		// and far exceeds what any viewport needs for a hero preload.
		$template       = get_page_template_slug();
		$hero_templates = array(
			'template-collection-black-rose.php',
			'template-collection-love-hurts.php',
			'template-collection-signature.php',
			'template-collection-kids-capsule.php',
			'template-immersive-black-rose.php',
			'template-immersive-love-hurts.php',
			'template-immersive-signature.php',
			'template-immersive-kids-capsule.php',
			'template-about.php',
		);
		if ( $template && in_array( $template, $hero_templates, true ) && has_post_thumbnail() ) {
			$image_url = get_the_post_thumbnail_url( get_the_ID(), 'large' );
		}
	}

	if ( $image_url ) {
		printf(
			'<link rel="preload" href="%s" as="image" fetchpriority="high">' . "\n",
			esc_url( $image_url )
		);
	}
}

/**
 * Remove jQuery Migrate on the frontend.
 *
 * Removes the jQuery Migrate compatibility shim for deprecated jQuery APIs.
 * Modern WooCommerce (9.0+) and WordPress (6.0+) do not require it.
 * Removing it saves ~12 KB and one blocking request.
 *
 * @since 6.6.0
 * @param \WP_Scripts $scripts Registered scripts.
 * @return void
 */
function skyyrose_remove_jquery_migrate( $scripts ) {
	if ( is_admin() ) {
		return;
	}
	if ( isset( $scripts->registered['jquery'] ) ) {
		$scripts->registered['jquery']->deps = array_diff(
			$scripts->registered['jquery']->deps,
			array( 'jquery-migrate' )
		);
	}
}

/**
 * Dequeue Gutenberg block library styles on pages that don't use blocks.
 *
 * The wp-block-library stylesheet (~40 KB) is loaded globally. On pages
 * that don't contain blocks (product pages, collection templates, etc.)
 * this is wasted bandwidth.
 *
 * @since 6.6.0
 * @return void
 */
function skyyrose_dequeue_block_styles() {
	if ( is_admin() ) {
		return;
	}

	// Keep block styles on pages that actually use blocks.
	if ( function_exists( 'has_blocks' ) && has_blocks() ) {
		return;
	}

	wp_dequeue_style( 'wp-block-library' );
	wp_dequeue_style( 'wp-block-library-theme' );
	wp_dequeue_style( 'wc-blocks-style' );
	wp_dequeue_style( 'global-styles' );
}

/**
 * Dequeue Jetpack and MediaElement styles not needed on most pages.
 *
 * Jetpack registers several feature-specific stylesheets globally even when
 * the corresponding feature is not used on the current page. This function
 * removes those whose context is clear:
 *
 * - Search chunk styles  → only needed on search results pages.
 * - Podcast player       → theme has no podcast pages; safe to remove globally.
 * - Grunion/forms CSS    → theme routes contact via Elementor, not Jetpack Forms.
 * - MediaElement.js      → only needed for native audio/video blocks; theme
 *                          uses YouTube embeds and Three.js, no <audio>/<video>.
 *
 * All wp_dequeue_style() / wp_dequeue_script() calls are no-ops when the
 * handle is not registered, so this is safe to run on all themes.
 *
 * @since 7.1.0
 * @return void
 */
function skyyrose_dequeue_jetpack_non_context_styles() {
	if ( is_admin() ) {
		return;
	}

	// Search chunk styles — only meaningful on search results pages.
	if ( ! is_search() ) {
		wp_dequeue_style( 'jetpack-search-widget' );
		wp_dequeue_style( 'jetpack-instant-search' );
		wp_dequeue_style( 'jetpack-search-chunk' );
	}

	// Podcast player — theme has no podcast pages; safe to remove globally.
	wp_dequeue_style( 'jetpack-podcast-player' );

	// Jetpack / Grunion contact forms — theme uses Elementor for contact pages.
	wp_dequeue_style( 'grunion-front-end' );
	wp_dequeue_style( 'jetpack-forms' );

	// MediaElement.js — only required for native audio/video blocks.
	// Theme uses YouTube embeds and custom Three.js scenes; no native players.
	if ( function_exists( 'has_blocks' ) && ! has_blocks() ) {
		wp_dequeue_style( 'wp-mediaelement' );
		wp_dequeue_script( 'wp-mediaelement' );
		wp_dequeue_script( 'mediaelement' );
	}
}

/*
--------------------------------------------------------------
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

// Remove jQuery Migrate on frontend (not needed since WC 9.0+ / WP 6.0+).
add_action( 'wp_default_scripts', 'skyyrose_remove_jquery_migrate' );

// Dequeue Gutenberg block styles on non-block pages.
add_action( 'wp_enqueue_scripts', 'skyyrose_dequeue_block_styles', 100 );

// Dequeue Jetpack feature styles not needed outside their context (search, podcast, forms, MediaElement).
add_action( 'wp_enqueue_scripts', 'skyyrose_dequeue_jetpack_non_context_styles', 101 );
