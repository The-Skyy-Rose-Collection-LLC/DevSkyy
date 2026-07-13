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

/*
--------------------------------------------------------------
 * Elementor Telemetry Opt-Out
 *--------------------------------------------------------------*/

// Elementor sends usage data to Mixpanel. Disable via the experiments
// opt-in filter — fires before Elementor initializes its tracking module.
add_filter( 'elementor/experiments/usage_data_opt_in', '__return_false' );

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
 * Resolve next-gen sibling URLs for an image URL.
 *
 * Checks the filesystem for AVIF + WebP siblings of a given source.
 * Returns sibling URLs only when the file exists on disk, so missing
 * variants never produce broken <source> tags.
 *
 * Covers two URL roots:
 * - Theme assets: get_template_directory_uri() → get_template_directory()
 * - WP Media Library uploads: wp_get_upload_dir() baseurl → basedir
 *
 * External URLs (CDN, plugins outside theme + uploads) pass through unchanged.
 *
 * @since  1.5.8
 * @since  1.5.10 Media Library support added.
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

	// Jetpack Photon rewrites every upload URL to i[0-2].wp.com — and silently
	// TRANSCODES .avif and .webp back to image/jpeg (verified 2026-05-21:
	// i0.wp.com/.../file.avif?fit=… returns content-type: image/jpeg). Routing
	// next-gen sources through Photon defeats the entire optimization. So:
	// strip the Photon prefix entirely on <source> emit; serve AVIF/WebP
	// direct from skyyrose.co so the browser receives the actual encoded
	// format. The fallback <img> keeps its original (Photon-rewritten) src,
	// so non-AVIF browsers still hit Photon's CDN for the JPG.
	//
	// Photon uses i0/i1/i2 shards only (verified 2026-05). If Jetpack ever
	// expands to i3+, this regex silently fails to strip the prefix → the
	// picture wrap no-ops (returns plain <img>), no broken sources emitted.
	$canonical_src = $src;
	if ( preg_match( '#^https?://i[0-2]\.wp\.com(/.+)$#', $src, $matches ) ) {
		$canonical_src = 'https://' . ltrim( $matches[1], '/' );
	}

	// Drop query string — Photon resize args (fit=…) only apply to Photon;
	// direct skyyrose.co serving uses the file as-is. AVIF compresses so
	// well that full-size variants are typically < 200KB.
	$canonical_path_url = strtok( $canonical_src, '?' );
	if ( false === $canonical_path_url ) {
		return $result;
	}

	$abs_path = skyyrose_url_to_path( $canonical_path_url );
	if ( null === $abs_path ) {
		return $result;
	}

	$path_no_ext = preg_replace( '/\.(jpe?g|png|webp|avif)$/i', '', $abs_path );
	if ( null === $path_no_ext || $path_no_ext === $abs_path ) {
		return $result;
	}

	$url_no_ext = preg_replace( '/\.(jpe?g|png|webp|avif)$/i', '', $canonical_path_url );

	if ( file_exists( $path_no_ext . '.avif' ) ) {
		$result['avif'] = $url_no_ext . '.avif';
	}
	if ( file_exists( $path_no_ext . '.webp' ) ) {
		$result['webp'] = $url_no_ext . '.webp';
	}

	return $result;
}

/**
 * Map an image URL to its absolute filesystem path.
 *
 * Supports theme assets + WP Media Library uploads. Returns null
 * when the URL is outside both roots (CDN, plugin, external).
 *
 * @since  1.5.10
 * @param  string $url Absolute URL.
 * @return string|null Absolute path, or null when unmappable.
 */
function skyyrose_url_to_path( $url ) {
	$theme_uri = trailingslashit( get_template_directory_uri() );
	if ( 0 === strpos( $url, $theme_uri ) ) {
		$relative = strtok( substr( $url, strlen( $theme_uri ) ), '?' );
		return get_template_directory() . '/' . $relative;
	}

	$upload = wp_get_upload_dir();
	if ( ! empty( $upload['baseurl'] ) && 0 === strpos( $url, $upload['baseurl'] ) ) {
		$relative = strtok( substr( $url, strlen( $upload['baseurl'] ) ), '?' );
		return rtrim( $upload['basedir'], '/' ) . '/' . ltrim( (string) $relative, '/' );
	}

	return null;
}

/**
 * Wrap wp_get_attachment_image output in <picture> when AVIF/WebP exist.
 *
 * Hooks the canonical WP image-render path so WC product galleries, post
 * thumbnails, and any plugin using wp_get_attachment_image() automatically
 * benefit from next-gen format negotiation.
 *
 * No-ops gracefully when AVIF/WebP siblings don't exist on disk — picture
 * coverage degrades to the standard <img> tag the filter received.
 *
 * @since  1.5.10
 * @param  string       $html          Original <img> markup.
 * @param  int          $attachment_id Attachment ID.
 * @param  string|array $size          Requested size (thumbnail|medium|large|...).
 * @param  bool         $icon          Whether the image is a media icon.
 * @param  array        $attr          Attributes passed to wp_get_attachment_image_attributes.
 * @return string                      Wrapped markup or unchanged input.
 */
function skyyrose_wrap_attachment_in_picture( $html, $attachment_id, $size, $icon, $attr ) {
	unset( $icon, $attr );

	if ( empty( $html ) || false !== strpos( $html, '<picture' ) ) {
		return $html;
	}

	$image = wp_get_attachment_image_src( $attachment_id, $size );
	if ( ! is_array( $image ) || empty( $image[0] ) ) {
		return $html;
	}

	$sources = skyyrose_picture_sources( $image[0] );
	if ( empty( $sources['avif'] ) && empty( $sources['webp'] ) ) {
		return $html;
	}

	$out = '<picture>';
	if ( ! empty( $sources['avif'] ) ) {
		$out .= sprintf( '<source type="image/avif" srcset="%s">', esc_url( $sources['avif'] ) );
	}
	if ( ! empty( $sources['webp'] ) ) {
		$out .= sprintf( '<source type="image/webp" srcset="%s">', esc_url( $sources['webp'] ) );
	}
	$out .= $html;
	$out .= '</picture>';

	return $out;
}
add_filter( 'wp_get_attachment_image', 'skyyrose_wrap_attachment_in_picture', 10, 5 );

/**
 * Generate AVIF + WebP siblings for new image uploads.
 *
 * Runs once per upload via wp_generate_attachment_metadata. Produces
 * a next-gen sibling for the full-size original AND every generated
 * size (thumbnail, medium, large, plus theme-registered sizes), so
 * srcset-aware code paths get full coverage.
 *
 * AVIF generation requires:
 * - PHP Imagick with libavif (check via imagick_supports_format), OR
 * - GD ≥ 8.1 with imageavif()
 *
 * Falls back to WebP-only when AVIF unsupported. Both no-op when
 * neither is available (filter returns unchanged metadata).
 *
 * @since  1.5.10
 * @param  array $metadata      Attachment metadata.
 * @param  int   $attachment_id Attachment ID.
 * @return array                Unchanged metadata.
 */
function skyyrose_generate_nextgen_siblings( $metadata, $attachment_id ) {
	if ( ! is_array( $metadata ) || empty( $metadata['file'] ) ) {
		return $metadata;
	}

	$file = get_attached_file( $attachment_id );
	if ( ! $file || ! file_exists( $file ) ) {
		return $metadata;
	}

	// Only run on raster image attachments we can decode.
	$ext = strtolower( pathinfo( $file, PATHINFO_EXTENSION ) );
	if ( ! in_array( $ext, array( 'jpg', 'jpeg', 'png' ), true ) ) {
		return $metadata;
	}

	$base_dir = dirname( $file );

	// Collect full-size + all generated sizes.
	$targets = array( basename( $file ) );
	if ( ! empty( $metadata['sizes'] ) && is_array( $metadata['sizes'] ) ) {
		foreach ( $metadata['sizes'] as $size_data ) {
			if ( ! empty( $size_data['file'] ) ) {
				$targets[] = $size_data['file'];
			}
		}
	}

	$gd_supports_avif = function_exists( 'imageavif' );
	$gd_supports_webp = function_exists( 'imagewebp' );

	foreach ( $targets as $name ) {
		$src_path = $base_dir . '/' . $name;
		if ( ! file_exists( $src_path ) ) {
			continue;
		}
		$base_no_ext = preg_replace( '/\.(jpe?g|png)$/i', '', $src_path );
		if ( null === $base_no_ext ) {
			continue;
		}

		if ( $gd_supports_webp && ! file_exists( $base_no_ext . '.webp' ) ) {
			skyyrose_gd_convert( $src_path, $base_no_ext . '.webp', 'webp' );
		}
		if ( $gd_supports_avif && ! file_exists( $base_no_ext . '.avif' ) ) {
			skyyrose_gd_convert( $src_path, $base_no_ext . '.avif', 'avif' );
		}
	}

	return $metadata;
}
add_filter( 'wp_generate_attachment_metadata', 'skyyrose_generate_nextgen_siblings', 20, 2 );

/**
 * Convert a JPG/PNG source to AVIF or WebP via GD.
 *
 * Quality tuned for product photography (q=82 WebP, q=62 AVIF —
 * matches the local batch script that generated v1.5.8 assets).
 *
 * @since  1.5.10
 * @param  string $src_path Absolute source path (jpg or png).
 * @param  string $dst_path Absolute output path.
 * @param  string $format   Target format: 'webp' | 'avif'.
 * @return bool             True on success, false on failure.
 */
function skyyrose_gd_convert( $src_path, $dst_path, $format ) {
	$ext = strtolower( pathinfo( $src_path, PATHINFO_EXTENSION ) );

	// Pre-flight: skip if source is absurdly large. GD will OOM the PHP-FPM
	// worker on WordPress.com hosting if we try to AVIF-encode a 12MP+ image
	// (RAM peaks ~4× pixel count + alpha). Symptom: SSH session dies exit
	// 130 mid-batch. Files this large should be handled out-of-band via
	// cwebp/avifenc locally and uploaded.
	$size_info = @getimagesize( $src_path ); // phpcs:ignore WordPress.PHP.NoSilencedErrors
	if ( false === $size_info ) {
		return false;
	}
	$pixels         = (int) $size_info[0] * (int) $size_info[1];
	$max_pixels     = 3500 * 3500; // ~12 megapixels — safe headroom on 256MB PHP-FPM.
	$needs_downsize = $pixels > $max_pixels;

	if ( 'png' === $ext ) {
		$image = @imagecreatefrompng( $src_path ); // phpcs:ignore WordPress.PHP.NoSilencedErrors
		if ( $image ) {
			imagepalettetotruecolor( $image );
			imagealphablending( $image, true );
			imagesavealpha( $image, true );
		}
	} else {
		$image = @imagecreatefromjpeg( $src_path ); // phpcs:ignore WordPress.PHP.NoSilencedErrors
	}

	if ( ! $image ) {
		return false;
	}

	// Downsize when source exceeds the safe pixel cap. Constrain to 2400px
	// long-edge (sufficient for any product card or hero on 4K display).
	if ( $needs_downsize ) {
		$src_w  = (int) $size_info[0];
		$src_h  = (int) $size_info[1];
		$ratio  = 2400 / max( $src_w, $src_h );
		$new_w  = (int) round( $src_w * $ratio );
		$new_h  = (int) round( $src_h * $ratio );
		$scaled = @imagescale( $image, $new_w, $new_h ); // phpcs:ignore WordPress.PHP.NoSilencedErrors
		if ( $scaled ) {
			unset( $image );
			$image = $scaled;
		}
	}

	$result = false;
	if ( 'avif' === $format && function_exists( 'imageavif' ) ) {
		$result = imageavif( $image, $dst_path, 62 );
	} elseif ( 'webp' === $format && function_exists( 'imagewebp' ) ) {
		$result = imagewebp( $image, $dst_path, 82 );
	}

	// imagedestroy() removed in PHP 8.0 — GD now auto-frees the resource.
	unset( $image );
	return (bool) $result;
}

/**
 * Render a <picture> element with AVIF + WebP sources when available.
 *
 * Falls back to a plain <img> when no next-gen siblings exist on disk.
 * The fallback <img> always uses the original URL.
 *
 * ### Placement support (optional)
 *
 * Pass a 'placement' key in $attrs to activate sizing-by-surface mode.
 * The key is consumed as a directive — it is NOT emitted as an HTML attribute.
 *
 * When 'placement' matches a registered contract in skyyrose_image_placements():
 *  - The <source> and <img> tags receive a `sizes` attribute from the contract.
 *  - A responsive `srcset` is built from on-disk width-suffixed siblings via
 *    skyyrose_image_srcset(); this supplements (not replaces) the AVIF/WebP
 *    next-gen source handling.
 *  - Baseline `width` and `height` attributes are derived from the contract's
 *    aspect ratio string (e.g. '16 / 9') to eliminate CLS before the image loads.
 *  - `data-fit` and `data-position` attributes are emitted so CSS can apply
 *    object-fit / object-position without needing inline !important overrides.
 *
 * Backward compatibility: omitting 'placement' (or passing an unregistered key)
 * produces output identical to the pre-1.6.3 behaviour.
 *
 * @since  1.5.8
 * @since  1.6.3 Optional 'placement' directive; data-fit/data-position; srcset.
 * @param  string $src    Image source URL.
 * @param  string $alt    Alt text (pass '' for decorative).
 * @param  array  $attrs  Extra HTML attrs for the <img> plus optional 'placement' directive.
 * @return string         Rendered <picture> markup (already escaped).
 */
function skyyrose_render_picture( $src, $alt = '', $attrs = array() ) {
	// --- Placement directive ------------------------------------------------
	$placement_key      = isset( $attrs['placement'] ) ? (string) $attrs['placement'] : '';
	$placement_contract = array();

	if ( '' !== $placement_key && function_exists( 'skyyrose_image_placement' ) ) {
		$resolved = skyyrose_image_placement( $placement_key );
		if ( is_array( $resolved ) ) {
			$placement_contract = $resolved;
		}
	}

	// Remove the directive so it is never rendered as an HTML attribute.
	unset( $attrs['placement'] );

	// --- Placement: inject sizes, data-fit, data-position, width/height -----
	$sizes_attr  = '';
	$srcset_attr = '';

	if ( ! empty( $placement_contract ) ) {
		// sizes attribute.
		if ( ! empty( $placement_contract['sizes'] ) ) {
			$sizes_attr = (string) $placement_contract['sizes'];
		}

		// Responsive srcset from on-disk width-suffixed siblings.
		if ( ! empty( $placement_contract['widths'] ) && function_exists( 'skyyrose_image_srcset' ) ) {
			$srcset_attr = skyyrose_image_srcset( $src, (array) $placement_contract['widths'] );
		}

		// Baseline width/height from aspect ratio string to kill CLS.
		// Parse e.g. '16 / 9' → w=1600, h=900 (baseline units, not CSS px).
		if ( ! isset( $attrs['width'] ) && ! isset( $attrs['height'] )
			&& ! empty( $placement_contract['aspect'] ) ) {
			$parts = array_map( 'trim', explode( '/', (string) $placement_contract['aspect'] ) );
			if ( 2 === count( $parts ) && is_numeric( $parts[0] ) && is_numeric( $parts[1] ) && (float) $parts[1] > 0 ) {
				$ratio         = (float) $parts[0] / (float) $parts[1];
				$baseline_h    = 900;
				$attrs['width']  = (int) round( $baseline_h * $ratio );
				$attrs['height'] = $baseline_h;
			}
		}

		// data-fit / data-position — consumed by CSS, no inline !important needed.
		if ( ! isset( $attrs['data-fit'] ) && ! empty( $placement_contract['fit'] ) ) {
			$attrs['data-fit'] = (string) $placement_contract['fit'];
		}
		if ( ! isset( $attrs['data-position'] ) && ! empty( $placement_contract['position'] ) ) {
			$attrs['data-position'] = (string) $placement_contract['position'];
		}
	}
	// --- end placement -------------------------------------------------------

	$sources = skyyrose_picture_sources( $src );

	// Build the HTML attribute string for the <img> tag.
	$attr_html = '';
	foreach ( $attrs as $key => $val ) {
		if ( null === $val || false === $val ) {
			continue;
		}
		$attr_html .= ' ' . esc_attr( $key ) . '="' . esc_attr( (string) $val ) . '"';
	}

	// Append srcset + sizes to <img> when placement supplied them.
	if ( '' !== $srcset_attr ) {
		$attr_html .= ' srcset="' . esc_attr( $srcset_attr ) . '"';
	}
	if ( '' !== $sizes_attr ) {
		$attr_html .= ' sizes="' . esc_attr( $sizes_attr ) . '"';
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

	// Emit next-gen <source> tags, adding sizes + srcset when placement is active.
	if ( ! empty( $sources['avif'] ) ) {
		$avif_srcset = '' !== $srcset_attr ? ' srcset="' . esc_attr( $srcset_attr ) . '"' : sprintf( ' srcset="%s"', esc_url( $sources['avif'] ) );
		$avif_sizes  = '' !== $sizes_attr ? ' sizes="' . esc_attr( $sizes_attr ) . '"' : '';
		$out        .= sprintf( '<source type="image/avif"%s%s>', $avif_srcset, $avif_sizes );
	}
	if ( ! empty( $sources['webp'] ) ) {
		$webp_srcset = '' !== $srcset_attr ? ' srcset="' . esc_attr( $srcset_attr ) . '"' : sprintf( ' srcset="%s"', esc_url( $sources['webp'] ) );
		$webp_sizes  = '' !== $sizes_attr ? ' sizes="' . esc_attr( $sizes_attr ) . '"' : '';
		$out        .= sprintf( '<source type="image/webp"%s%s>', $webp_srcset, $webp_sizes );
	}

	$out .= $img_tag;
	$out .= '</picture>';

	return $out;
}
add_action( 'send_headers', 'skyyrose_send_cache_headers' );

/*
--------------------------------------------------------------
 * WP-CLI Backfill: AVIF/WebP for existing Media Library uploads
 *--------------------------------------------------------------*/

if ( defined( 'WP_CLI' ) && WP_CLI ) {
	/**
	 * Register `wp skyyrose nextgen-backfill` for one-shot bulk conversion.
	 *
	 * Walks every image attachment, generates AVIF + WebP siblings for the
	 * full-size original and each generated size, skipping any that already
	 * exist. Idempotent — safe to re-run.
	 *
	 * Usage:
	 *   wp skyyrose nextgen-backfill           # all attachments
	 *   wp skyyrose nextgen-backfill --limit=50 # batch test
	 *   wp skyyrose nextgen-backfill --dry-run  # report what would convert
	 *
	 * @since 1.5.10
	 */
	WP_CLI::add_command( 'skyyrose nextgen-backfill', 'skyyrose_nextgen_backfill_cli' );
}

/**
 * WP-CLI entry point for `wp skyyrose nextgen-backfill`.
 *
 * Drives the backfill loop: capability gate → pending-attachment query →
 * per-attachment delegation → progress + summary. Heavy lifting lives in
 * skyyrose_nextgen_backfill_targets() and skyyrose_nextgen_backfill_one()
 * to keep this entry under the project's 50-line function rule.
 *
 * @since 1.5.16 Extracted from inline closure (was 130 lines).
 * @param array $args       Positional args (unused).
 * @param array $assoc_args --limit=N, --dry-run.
 * @return void
 */
function skyyrose_nextgen_backfill_cli( $args, $assoc_args ) {
	unset( $args );

	$limit   = isset( $assoc_args['limit'] ) ? (int) $assoc_args['limit'] : -1;
	$dry_run = ! empty( $assoc_args['dry-run'] );
	$gd_avif = function_exists( 'imageavif' );
	$gd_webp = function_exists( 'imagewebp' );

	if ( ! $gd_avif && ! $gd_webp ) {
		WP_CLI::error( 'GD lacks both imageavif() and imagewebp() — install libavif + libwebp on PHP.' );
	}

	$pending  = skyyrose_nextgen_backfill_pending_ids();
	$total    = count( $pending );
	$counters = array(
		'converted'   => 0,
		'marked_done' => 0,
		'processed'   => 0,
		'skipped'     => 0,
	);
	$progress = WP_CLI\Utils\make_progress_bar(
		"Backfilling AVIF/WebP for {$total} pending attachments",
		( $limit > 0 ) ? min( $total, $limit ) : $total
	);

	foreach ( $pending as $attachment_id ) {
		if ( $limit > 0 && $counters['converted'] >= $limit ) {
			break;
		}
		skyyrose_nextgen_backfill_one( (int) $attachment_id, $dry_run, $gd_avif, $gd_webp, $counters );
		$progress->tick();
	}

	$progress->finish();
	$verb = $dry_run ? 'Would convert' : 'Converted';
	WP_CLI::success(
		"{$verb} {$counters['converted']} files. Processed {$counters['processed']} of {$total} pending; "
		. "marked {$counters['marked_done']} attachments complete; skipped {$counters['skipped']} missing originals."
	);
}

/**
 * Query attachment IDs still needing AVIF/WebP siblings.
 *
 * Excludes attachments already marked done via _skyyrose_nextgen_done meta.
 * Without this exclusion the loop would re-check the same head-of-queue
 * attachments each batch and never advance.
 *
 * @since 1.5.16
 * @return int[] Attachment IDs, ordered ASC by ID.
 */
function skyyrose_nextgen_backfill_pending_ids(): array {
	$query = new WP_Query(
		array(
			'post_type'      => 'attachment',
			'post_status'    => 'inherit',
			'post_mime_type' => array( 'image/jpeg', 'image/png' ),
			'posts_per_page' => -1,
			'fields'         => 'ids',
			'no_found_rows'  => true,
			'orderby'        => 'ID',
			'order'          => 'ASC',
			'meta_query'     => array( // phpcs:ignore WordPress.DB.SlowDBQuery.slow_db_query_meta_query
				array(
					'key'     => '_skyyrose_nextgen_done',
					'compare' => 'NOT EXISTS',
				),
			),
		)
	);
	return array_map( 'intval', (array) $query->posts );
}

/**
 * Resolve the size-whitelisted target filenames for an attachment.
 *
 * Memory-safe size whitelist: only convert sizes that templates actually
 * request. Full + the four canonical WP sizes covers every <img src=…>
 * the picture filter sees. Skipping rare or custom sizes (medium_large,
 * 1536x1536, theme-registered) keeps each attachment's total GD ops under
 * ~10, avoiding PHP-FPM worker death on WordPress.com (256MB cap, exit
 * 130 symptom).
 *
 * @since 1.5.16
 * @param string $file     Absolute path to full-size source file.
 * @param array  $metadata wp_get_attachment_metadata() return value.
 * @return string[] Basenames of files to convert (full + whitelisted sizes).
 */
function skyyrose_nextgen_backfill_targets( string $file, $metadata ): array {
	$size_whitelist = array( 'thumbnail', 'medium', 'large', 'skyyrose-product-avif' );
	$targets        = array( basename( $file ) );

	if ( ! is_array( $metadata ) || empty( $metadata['sizes'] ) || ! is_array( $metadata['sizes'] ) ) {
		return $targets;
	}
	foreach ( $size_whitelist as $size_key ) {
		if ( ! empty( $metadata['sizes'][ $size_key ]['file'] ) ) {
			$targets[] = $metadata['sizes'][ $size_key ]['file'];
		}
	}
	return $targets;
}

/**
 * Backfill AVIF/WebP siblings for one attachment, in-place.
 *
 * Iterates the size-whitelisted targets, converts missing siblings via
 * GD (with per-encode gc_collect_cycles to bound peak RAM), and marks
 * the attachment done in post meta when every target has both siblings.
 *
 * Mutates $counters by reference: converted, processed, skipped, marked_done.
 *
 * @since 1.5.16
 * @param int   $attachment_id WP attachment ID.
 * @param bool  $dry_run       When true, count conversions but don't write.
 * @param bool  $gd_avif       GD's imageavif() available.
 * @param bool  $gd_webp       GD's imagewebp() available.
 * @param array $counters      Reference: 'converted','processed','skipped','marked_done'.
 * @return void
 */
function skyyrose_nextgen_backfill_one( int $attachment_id, bool $dry_run, bool $gd_avif, bool $gd_webp, array &$counters ): void {
	$file = get_attached_file( $attachment_id );
	if ( ! $file || ! file_exists( $file ) ) {
		++$counters['skipped'];
		return;
	}

	$base_dir = dirname( $file );
	$targets  = skyyrose_nextgen_backfill_targets( $file, wp_get_attachment_metadata( $attachment_id ) );
	$all_done = true;

	foreach ( $targets as $name ) {
		$src_path    = $base_dir . '/' . $name;
		$base_no_ext = preg_replace( '/\.(jpe?g|png)$/i', '', $src_path );
		if ( ! file_exists( $src_path ) || null === $base_no_ext ) {
			continue;
		}

		if ( $gd_webp && ! file_exists( $base_no_ext . '.webp' ) ) {
			if ( $dry_run ) {
				++$counters['converted'];
				$all_done = false;
			} elseif ( skyyrose_gd_convert( $src_path, $base_no_ext . '.webp', 'webp' ) ) {
				++$counters['converted'];
			} else {
				$all_done = false;
			}
		}
		if ( $gd_avif && ! file_exists( $base_no_ext . '.avif' ) ) {
			if ( $dry_run ) {
				++$counters['converted'];
				$all_done = false;
			} elseif ( skyyrose_gd_convert( $src_path, $base_no_ext . '.avif', 'avif' ) ) {
				++$counters['converted'];
			} else {
				$all_done = false;
			}
		}
		// Force GC after each encode — keeps peak RAM bounded so the
		// PHP-FPM worker survives multi-size loops.
		if ( function_exists( 'gc_collect_cycles' ) ) {
			gc_collect_cycles();
		}
	}

	if ( $all_done && ! $dry_run ) {
		update_post_meta( $attachment_id, '_skyyrose_nextgen_done', 1 );
		++$counters['marked_done'];
	}
	++$counters['processed'];
}

/**
 * Derive the AVIF sibling path + URL for a given WebP/JPG/PNG asset URL.
 *
 * Returns BOTH the filesystem path (for existence probing) AND the public
 * URL (for emit) computed from the same source. Prevents the path-coupling
 * bug where a `file_exists()` check and a `<source>` URL drift apart when
 * the source URL is filtered (CDN swap, asset hash, etc.).
 *
 * Returns null when the URL doesn't map to the theme assets directory.
 *
 * @since 1.5.19 Extracted to fix code-review MEDIUM finding.
 * @param string $src_url Source image URL (typically .webp or .jpg).
 * @return array|null     { 'path' => string, 'url' => string } or null.
 */
function skyyrose_avif_sibling_pair( string $src_url ): ?array {
	$abs_path = skyyrose_url_to_path( strtok( $src_url, '?' ) );
	if ( null === $abs_path ) {
		return null;
	}
	$path_no_ext = preg_replace( '/\.(jpe?g|png|webp)$/i', '', $abs_path );
	$url_no_ext  = preg_replace( '/\.(jpe?g|png|webp)$/i', '', $src_url );
	if ( null === $path_no_ext || $path_no_ext === $abs_path ) {
		return null;
	}
	return array(
		'path' => $path_no_ext . '.avif',
		'url'  => $url_no_ext . '.avif',
	);
}
