<?php
/**
 * Image Placement Registry — Sizing by Surface
 *
 * Defines a static map of placement keys to layout contracts so that
 * every image in the theme is fitted to the surface it occupies, rather
 * than stretching to fill arbitrary containers.
 *
 * Consumed by skyyrose_render_picture() in inc/performance.php via the
 * optional 'placement' key in the $attrs argument.
 *
 * Contract shape:
 *   'aspect'   => CSS aspect-ratio string, e.g. '16 / 9'
 *   'sizes'    => HTML sizes attribute string for the <source>/<img> tags
 *   'widths'   => int[] of pixel widths to probe for responsive srcset siblings
 *   'fit'      => CSS object-fit value, e.g. 'cover'
 *   'position' => CSS object-position value, e.g. 'center 30%'
 *
 * @package SkyyRose
 * @since   1.6.3
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Return the full placement registry.
 *
 * Uses a static local variable so the array is constructed only once per
 * request. Filtered via 'skyyrose_image_placements' to allow child themes
 * or plugins to register additional placements without modifying core.
 *
 * @since  1.6.3
 * @return array<string, array{aspect: string, sizes: string, widths: int[], fit: string, position: string}>
 */
function skyyrose_image_placements(): array {
	static $placements = null;

	if ( null !== $placements ) {
		return $placements;
	}

	$default = array(
		'experience-hero' => array(
			'aspect'   => '16 / 9',
			'sizes'    => '100vw',
			'widths'   => array( 640, 1024, 1536, 2048, 2560 ),
			'fit'      => 'cover',
			'position' => 'center',
		),
		'holo-card'       => array(
			'aspect'   => '4 / 5',
			'sizes'    => '(max-width:768px) 50vw, 25vw',
			'widths'   => array( 480, 600, 750 ),
			'fit'      => 'cover',
			'position' => 'center',
		),
		'collection-card' => array(
			'aspect'   => '1 / 1',
			'sizes'    => '(max-width:768px) 100vw, 33vw',
			'widths'   => array( 480, 800 ),
			'fit'      => 'cover',
			'position' => 'center',
		),
		'lookbook-tile'   => array(
			'aspect'   => '4 / 5',
			'sizes'    => '(max-width:768px) 100vw, 50vw',
			'widths'   => array( 480, 960 ),
			'fit'      => 'cover',
			'position' => 'center 30%',
		),
		'landing-hero'    => array(
			'aspect'   => '16 / 9',
			'sizes'    => '100vw',
			'widths'   => array( 768, 1280, 1920 ),
			'fit'      => 'cover',
			'position' => 'center',
		),
	);

	/**
	 * Filter the full placement registry.
	 *
	 * @since 1.6.3
	 * @param array $default Default placement contracts keyed by placement slug.
	 */
	$placements = (array) apply_filters( 'skyyrose_image_placements', $default );

	return $placements;
}

/**
 * Return a single placement contract by key.
 *
 * @since  1.6.3
 * @param  string $key Placement slug, e.g. 'holo-card'.
 * @return array<string, mixed>|null Contract array, or null when the key is not registered.
 */
function skyyrose_image_placement( string $key ): ?array {
	$all = skyyrose_image_placements();
	return isset( $all[ $key ] ) ? $all[ $key ] : null;
}

/**
 * Build a responsive srcset string from on-disk width-suffixed siblings.
 *
 * Given a base asset URL (e.g. the resolved URL of a theme image without
 * extension, or a concrete file URL) and an array of target widths, probes
 * the theme filesystem for files named `basename-<w>w.<ext>` and assembles
 * a srcset string from those that actually exist.
 *
 * Width-suffixed sibling convention (matches the render-pipeline output):
 *   /assets/images/hero/foo-640w.webp
 *   /assets/images/hero/foo-1024w.webp
 *   …
 *
 * When $src already points to a concrete file (has a recognised extension),
 * the extension is stripped and sibling detection proceeds on the stem.
 * When $src has no extension, it is treated as the stem directly.
 *
 * Only theme assets are supported (URL must begin with get_template_directory_uri()).
 * Non-theme URLs (CDN, media library) return '' immediately — callers should
 * fall back to the WP-generated srcset in those cases.
 *
 * @since  1.6.3
 * @param  string $src    Theme-relative or absolute URL of the source image.
 * @param  int[]  $widths Candidate pixel widths to probe.
 * @return string         Comma-separated srcset entries, or '' when none found.
 */
function skyyrose_image_srcset( string $src, array $widths ): string {
	if ( empty( $src ) || empty( $widths ) ) {
		return '';
	}

	$theme_uri  = trailingslashit( get_template_directory_uri() );
	$theme_dir  = trailingslashit( get_template_directory() );

	// Only handle theme assets — CDN / media-library paths are unsupported.
	if ( 0 !== strpos( $src, $theme_uri ) ) {
		return '';
	}

	// Strip query string.
	$clean_url = strtok( $src, '?' );
	if ( false === $clean_url ) {
		return '';
	}

	// Determine URL stem (no extension) and detected extension (if any).
	$known_exts = array( 'avif', 'webp', 'jpg', 'jpeg', 'png' );
	$ext        = strtolower( pathinfo( $clean_url, PATHINFO_EXTENSION ) );
	$has_ext    = in_array( $ext, $known_exts, true );

	$url_stem  = $has_ext ? preg_replace( '/\.[^.]+$/', '', $clean_url ) : $clean_url;
	if ( null === $url_stem ) {
		return '';
	}

	// Map URL stem → filesystem stem.
	$relative_stem = substr( $url_stem, strlen( $theme_uri ) );
	$path_stem     = rtrim( $theme_dir, '/' ) . '/' . ltrim( $relative_stem, '/' );

	// Preferred format order: avif > webp > original ext > jpg fallback.
	$probe_formats = array( 'avif', 'webp' );
	if ( $has_ext && ! in_array( $ext, $probe_formats, true ) ) {
		$probe_formats[] = $ext;
	}
	if ( ! in_array( 'jpg', $probe_formats, true ) ) {
		$probe_formats[] = 'jpg';
	}

	$entries = array();

	foreach ( $widths as $w ) {
		$w = (int) $w;
		if ( $w <= 0 ) {
			continue;
		}

		// Find the best-quality format that exists on disk for this width.
		$found_url = null;
		foreach ( $probe_formats as $fmt ) {
			$candidate_path = $path_stem . '-' . $w . 'w.' . $fmt;
			if ( file_exists( $candidate_path ) ) {
				$found_url = $url_stem . '-' . $w . 'w.' . $fmt;
				break;
			}
		}

		if ( null !== $found_url ) {
			$entries[] = esc_url( $found_url ) . ' ' . $w . 'w';
		}
	}

	return implode( ', ', $entries );
}
