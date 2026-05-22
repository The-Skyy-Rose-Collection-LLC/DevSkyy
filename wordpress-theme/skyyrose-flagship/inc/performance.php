<?php
/**
 * Performance Optimizations — Font, Image, and Cache
 *
 * Consolidates performance-related filters that are not tied to
 * script/style enqueuing (those live in enqueue-performance.php).
 *
 * Covers:
 * - AVIF upload support (WP 6.8+)
 * - Google Fonts removal (Elementor + generic dequeue)
 * - Image optimization hints
 * - Cache header helpers
 *
 * @package SkyyRose
 * @since   6.6.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/*
--------------------------------------------------------------
 * AVIF Image Support
 *--------------------------------------------------------------*/

/**
 * Allow AVIF uploads in the Media Library.
 *
 * WordPress 6.8 has partial AVIF support; this ensures the MIME
 * type is always allowed regardless of server-side detection.
 *
 * @since 6.6.0
 *
 * @param  array $mimes Allowed MIME types keyed by extension.
 * @return array Updated MIME types.
 */
function skyyrose_allow_avif_uploads( $mimes ) {
	$mimes['avif'] = 'image/avif';
	return $mimes;
}
add_filter( 'upload_mimes', 'skyyrose_allow_avif_uploads' );

/**
 * Fix AVIF file type detection for servers that lack libavif.
 *
 * Some hosting environments cannot detect AVIF via getimagesize().
 * This filter trusts the file extension when the server returns
 * an empty MIME type for .avif files.
 *
 * @since 6.6.0
 *
 * @param  array  $data     File data with 'ext' and 'type' keys.
 * @param  string $file     Full path to the file.
 * @param  string $filename Name of the file.
 * @param  array  $mimes    Allowed MIME types.
 * @return array  Updated file data.
 */
function skyyrose_fix_avif_mime_type( $data, $file, $filename, $mimes ) {
	if ( ! empty( $data['ext'] ) && ! empty( $data['type'] ) ) {
		return $data;
	}

	$ext = pathinfo( $filename, PATHINFO_EXTENSION );
	if ( 'avif' === strtolower( $ext ) ) {
		$data['ext']  = 'avif';
		$data['type'] = 'image/avif';
	}

	return $data;
}
add_filter( 'wp_check_filetype_and_ext', 'skyyrose_fix_avif_mime_type', 10, 4 );

/**
 * Register AVIF-optimized custom image sizes.
 *
 * These supplement the existing image sizes from theme-setup.php
 * with AVIF-friendly dimensions for modern browsers.
 *
 * @since 6.6.0
 * @return void
 */
function skyyrose_avif_image_sizes() {
	// Large hero for AVIF-capable browsers (same dimensions, WP generates AVIF if supported).
	add_image_size( 'skyyrose-hero-avif', 1920, 1080, true );
	// Product card optimized for next-gen formats.
	add_image_size( 'skyyrose-product-avif', 600, 800, true );
}
add_action( 'after_setup_theme', 'skyyrose_avif_image_sizes' );

/*
--------------------------------------------------------------
 * Google Fonts Removal
 *--------------------------------------------------------------*/

/**
 * Prevent Elementor from printing Google Fonts.
 *
 * Elementor injects Google Fonts links for any widget that uses
 * a Google font. Since all our fonts are self-hosted, we disable
 * this entirely to avoid GDPR issues and unnecessary requests.
 *
 * @since 6.6.0
 *
 * @param  bool $print Whether to print Google Fonts.
 * @return bool Always false.
 */
add_filter( 'elementor/frontend/print_google_fonts', '__return_false' );

/**
 * Dequeue any Google Fonts stylesheets that slip through.
 *
 * Catches Google Fonts loaded by plugins, child themes, or
 * Elementor global styles that bypass the print_google_fonts filter.
 *
 * @since 6.6.0
 * @return void
 */
function skyyrose_dequeue_google_fonts() {
	global $wp_styles;

	if ( empty( $wp_styles->registered ) ) {
		return;
	}

	foreach ( $wp_styles->registered as $handle => $style ) {
		if ( ! empty( $style->src ) && strpos( $style->src, 'fonts.googleapis.com' ) !== false ) {
			wp_dequeue_style( $handle );
			wp_deregister_style( $handle );
		}
	}
}
add_action( 'wp_enqueue_scripts', 'skyyrose_dequeue_google_fonts', 999 );
add_action( 'wp_print_styles', 'skyyrose_dequeue_google_fonts', 999 );

/**
 * Remove Google Fonts DNS prefetch hints.
 *
 * @since 6.6.0
 *
 * @param  array  $urls          Resource hint URLs.
 * @param  string $relation_type Hint type (dns-prefetch, preconnect, etc.).
 * @return array  Filtered URLs.
 */
function skyyrose_remove_google_fonts_hints( $urls, $relation_type ) {
	if ( 'dns-prefetch' === $relation_type || 'preconnect' === $relation_type ) {
		$urls = array_filter(
			$urls,
			function ( $url ) {
				$href = is_array( $url ) ? ( $url['href'] ?? '' ) : $url;
				return strpos( $href, 'fonts.googleapis.com' ) === false
					&& strpos( $href, 'fonts.gstatic.com' ) === false;
			}
		);
	}
	return $urls;
}
add_filter( 'wp_resource_hints', 'skyyrose_remove_google_fonts_hints', 10, 2 );

/*
--------------------------------------------------------------
 * Cache Optimization
 *--------------------------------------------------------------*/

/**
 * Add immutable cache headers for versioned theme assets.
 *
 * When served through WordPress.com or a CDN, versioned assets
 * should be cached aggressively since the version query string
 * changes on each theme update.
 *
 * @since 6.6.0
 * @return void
 */
function skyyrose_send_cache_headers() {
	// Only apply to front-end, non-admin, non-AJAX requests.
	if ( is_admin() || wp_doing_ajax() || wp_doing_cron() ) {
		return;
	}

	// Let caching plugins and CDNs handle this; we just suggest.
	if ( ! headers_sent() && apply_filters( 'skyyrose_send_cache_headers', true ) ) {
		header( 'X-Content-Type-Options: nosniff' );
	}
}

/*
--------------------------------------------------------------
 * Next-Gen Image Format Helpers (AVIF + WebP)
 *--------------------------------------------------------------*/

/**
 * Resolve next-gen sibling URLs for a theme-asset image URL.
 *
 * Checks the filesystem for AVIF + WebP siblings of a given source.
 * Returns sibling URLs only when the file exists on disk, so missing
 * variants never produce broken <source> tags.
 *
 * Only resolves URLs inside the theme's assets directory — external
 * URLs (CDN, plugins) pass through unchanged.
 *
 * @since  1.5.8
 * @param  string $src Absolute URL to an image asset.
 * @return array      { 'avif' => string|null, 'webp' => string|null, 'src' => string }
 */
function skyyrose_picture_sources( $src ) {
	$result = array(
		'avif' => null,
		'webp' => null,
		'src'  => $src,
	);

	if ( empty( $src ) ) {
		return $result;
	}

	$theme_uri = trailingslashit( get_template_directory_uri() );
	if ( 0 !== strpos( $src, $theme_uri ) ) {
		return $result;
	}

	$relative      = substr( $src, strlen( $theme_uri ) );
	$relative_path = strtok( $relative, '?' );
	$abs_path      = get_template_directory() . '/' . $relative_path;
	$path_no_ext   = preg_replace( '/\.(jpe?g|png|webp|avif)$/i', '', $abs_path );

	if ( null === $path_no_ext ) {
		return $result;
	}

	$url_no_ext = preg_replace( '/\.(jpe?g|png|webp|avif)$/i', '', $src );

	if ( file_exists( $path_no_ext . '.avif' ) ) {
		$result['avif'] = $url_no_ext . '.avif';
	}
	if ( file_exists( $path_no_ext . '.webp' ) ) {
		$result['webp'] = $url_no_ext . '.webp';
	}

	return $result;
}

/**
 * Render a <picture> element with AVIF + WebP sources when available.
 *
 * Falls back to a plain <img> when no next-gen siblings exist on disk.
 * The fallback <img> always uses the original URL.
 *
 * @since  1.5.8
 * @param  string $src    Image source URL.
 * @param  string $alt    Alt text (pass '' for decorative).
 * @param  array  $attrs  Extra HTML attrs for the <img> (class, loading, etc.).
 * @return string         Rendered <picture> markup (already escaped).
 */
function skyyrose_render_picture( $src, $alt = '', $attrs = array() ) {
	$sources = skyyrose_picture_sources( $src );

	$attr_html = '';
	foreach ( $attrs as $key => $val ) {
		if ( null === $val || false === $val ) {
			continue;
		}
		$attr_html .= ' ' . esc_attr( $key ) . '="' . esc_attr( (string) $val ) . '"';
	}

	$img_tag = sprintf(
		'<img src="%s" alt="%s"%s>',
		esc_url( $sources['src'] ),
		esc_attr( $alt ),
		$attr_html // pre-escaped via esc_attr loop above.
	);

	if ( empty( $sources['avif'] ) && empty( $sources['webp'] ) ) {
		return $img_tag;
	}

	$out = '<picture>';
	if ( ! empty( $sources['avif'] ) ) {
		$out .= sprintf( '<source type="image/avif" srcset="%s">', esc_url( $sources['avif'] ) );
	}
	if ( ! empty( $sources['webp'] ) ) {
		$out .= sprintf( '<source type="image/webp" srcset="%s">', esc_url( $sources['webp'] ) );
	}
	$out .= $img_tag;
	$out .= '</picture>';

	return $out;
}
add_action( 'send_headers', 'skyyrose_send_cache_headers' );
