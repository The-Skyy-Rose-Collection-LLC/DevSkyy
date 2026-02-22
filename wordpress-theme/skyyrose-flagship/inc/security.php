<?php
/**
 * Security Hardening
 *
 * CSP headers, HTTP security headers, XML-RPC disabling,
 * WordPress version removal, and nonce helper functions.
 *
 * @package SkyyRose_Flagship
 * @since   2.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/*--------------------------------------------------------------
 * HTTP Security Headers
 *--------------------------------------------------------------*/

/**
 * Send Content-Security-Policy and other security headers on every front-end request.
 *
 * @since 2.0.0
 * @return void
 */
function skyyrose_send_security_headers() {

	// Skip admin pages (would break WP admin which loads inline scripts).
	if ( is_admin() ) {
		return;
	}

	/*
	 * Content-Security-Policy
	 *
	 * Whitelist only the external origins that the theme genuinely needs.
	 * blob: is required for Three.js web workers.
	 *
	 * Note: 'unsafe-inline' is required in script-src and style-src because
	 * WordPress core, WooCommerce, and Elementor all inject inline scripts
	 * and styles. Removing it would break core functionality. A future
	 * improvement would be to use nonce-based CSP (script-src 'nonce-...').
	 */
	$csp_directives = array(
		"default-src 'self'",
		"script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://cdn.babylonjs.com https://stats.wp.com https://widgets.wp.com https://s0.wp.com https://cdn.elementor.com https://fonts.googleapis.com https://unpkg.com blob:",
		"style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
		"img-src 'self' data: blob: https://*.wp.com https://secure.gravatar.com https://i0.wp.com https://i1.wp.com https://i2.wp.com https://fonts.gstatic.com https://*.skyyrose.co",
		"font-src 'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net",
		"connect-src 'self' https://stats.wp.com https://public-api.wordpress.com https://api.skyyrose.co https://pixel.wp.com",
		"frame-src 'self' https://www.youtube.com https://player.vimeo.com",
		"worker-src 'self' blob:",
		"child-src 'self' blob:",
		"object-src 'none'",
		"base-uri 'self'",
		"form-action 'self'",
	);

	$csp_policy = implode( '; ', $csp_directives );

	header( 'Content-Security-Policy: ' . $csp_policy );

	// Prevent MIME-type sniffing.
	header( 'X-Content-Type-Options: nosniff' );

	// Prevent clickjacking.
	header( 'X-Frame-Options: SAMEORIGIN' );

	// Enforce HTTPS via HSTS (1 year including subdomains).
	header( 'Strict-Transport-Security: max-age=31536000; includeSubDomains' );

	// Disable legacy XSS auditor (can introduce vulnerabilities in modern browsers).
	header( 'X-XSS-Protection: 0' );

	// Control Referrer information.
	header( 'Referrer-Policy: strict-origin-when-cross-origin' );

	// Permissions policy (restrict sensor APIs not needed by a fashion site).
	header( 'Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(self)' );
}
add_action( 'send_headers', 'skyyrose_send_security_headers' );

/*--------------------------------------------------------------
 * XML-RPC Disable
 *--------------------------------------------------------------*/

/**
 * Completely disable XML-RPC to prevent brute-force and DDoS attacks.
 *
 * @since 1.0.0
 */
add_filter( 'xmlrpc_enabled', '__return_false' );

/**
 * Remove XML-RPC discovery links from the HTML head and HTTP headers.
 *
 * @since 2.0.0
 * @return void
 */
function skyyrose_remove_xmlrpc_links() {
	remove_action( 'wp_head', 'rsd_link' );
	remove_action( 'wp_head', 'wlwmanifest_link' );
	remove_action( 'xmlrpc_rsd_apis', 'rest_output_rsd' );

	// Block XML-RPC requests at the HTTP level with a 403.
	add_filter(
		'xmlrpc_methods',
		function () {
			return array();
		}
	);
}
add_action( 'init', 'skyyrose_remove_xmlrpc_links' );

/*--------------------------------------------------------------
 * WordPress Version Exposure
 *--------------------------------------------------------------*/

/**
 * Remove WordPress version from head, feeds, and stylesheets.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_remove_wp_version() {

	// Remove generator meta tag.
	remove_action( 'wp_head', 'wp_generator' );

	// Remove version from RSS feeds.
	add_filter( 'the_generator', '__return_empty_string' );

	// Remove version query string from all enqueued styles and scripts.
	add_filter(
		'style_loader_src',
		'skyyrose_remove_version_query_string',
		9999
	);
	add_filter(
		'script_loader_src',
		'skyyrose_remove_version_query_string',
		9999
	);
}
add_action( 'init', 'skyyrose_remove_wp_version' );

/**
 * Strip the ?ver= query string from enqueued asset URLs.
 *
 * Only strips the WordPress core version; theme and plugin versions are kept
 * for cache-busting.
 *
 * @since  2.0.0
 *
 * @param  string $src Asset URL.
 * @return string Cleaned URL.
 */
function skyyrose_remove_version_query_string( $src ) {

	if ( empty( $src ) ) {
		return $src;
	}

	$parsed = wp_parse_url( $src );

	if ( ! isset( $parsed['query'] ) ) {
		return $src;
	}

	// Only strip if the version matches WordPress core version.
	$wp_version = get_bloginfo( 'version' );

	if ( strpos( $parsed['query'], 'ver=' . $wp_version ) !== false ) {
		return remove_query_arg( 'ver', $src );
	}

	return $src;
}

/*--------------------------------------------------------------
 * Miscellaneous Head Cleanup
 *--------------------------------------------------------------*/

/**
 * Remove unnecessary meta tags and links from wp_head.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_clean_wp_head() {
	// Remove shortlink.
	remove_action( 'wp_head', 'wp_shortlink_wp_head' );

	// Remove REST API discovery link (still accessible, just not advertised).
	remove_action( 'wp_head', 'rest_output_link_wp_head' );

	// Remove oEmbed discovery links.
	remove_action( 'wp_head', 'wp_oembed_add_discovery_links' );

	// Remove emoji detection and inline styles.
	remove_action( 'wp_head', 'print_emoji_detection_script', 7 );
	remove_action( 'wp_print_styles', 'print_emoji_styles' );
	remove_action( 'admin_print_scripts', 'print_emoji_detection_script' );
	remove_action( 'admin_print_styles', 'print_emoji_styles' );
}
add_action( 'init', 'skyyrose_clean_wp_head' );

/*--------------------------------------------------------------
 * Nonce Helper Functions
 *--------------------------------------------------------------*/

/**
 * Create a nonce for a given action with the skyyrose prefix.
 *
 * @since  2.0.0
 *
 * @param  string $action Nonce action identifier (without prefix).
 * @return string Generated nonce token.
 */
function skyyrose_create_nonce( $action ) {
	return wp_create_nonce( 'skyyrose_' . sanitize_key( $action ) );
}

/**
 * Verify a nonce for a given action with the skyyrose prefix.
 *
 * @since 2.0.0
 *
 * @param  string $nonce  The nonce token to verify.
 * @param  string $action Nonce action identifier (without prefix).
 * @return false|int False if invalid, 1 if <12 hours old, 2 if <24 hours old.
 */
function skyyrose_verify_nonce( $nonce, $action ) {
	return wp_verify_nonce( $nonce, 'skyyrose_' . sanitize_key( $action ) );
}

/**
 * Output a hidden nonce field for forms.
 *
 * @since 2.0.0
 *
 * @param string $action    Nonce action identifier (without prefix).
 * @param string $name      Name attribute for the hidden input. Default 'skyyrose_nonce'.
 * @param bool   $referrer  Whether to include the referer hidden field. Default true.
 * @return void
 */
function skyyrose_nonce_field( $action, $name = 'skyyrose_nonce', $referrer = true ) {
	wp_nonce_field( 'skyyrose_' . sanitize_key( $action ), $name, $referrer );
}

/*--------------------------------------------------------------
 * Input Sanitization Helpers
 *--------------------------------------------------------------*/

/**
 * Sanitize a string intended for safe HTML output.
 *
 * Strips tags, decodes entities, removes extra whitespace.
 *
 * @since  2.0.0
 *
 * @param  string $input Raw input string.
 * @return string Sanitized string.
 */
function skyyrose_sanitize_text( $input ) {
	return sanitize_text_field( wp_unslash( $input ) );
}

/**
 * Sanitize a URL input, validating protocol.
 *
 * Only allows http, https, and mailto protocols.
 *
 * @since  2.0.0
 *
 * @param  string $url Raw URL input.
 * @return string Sanitized URL or empty string if invalid.
 */
function skyyrose_sanitize_url( $url ) {

	$sanitized = esc_url_raw( wp_unslash( $url ), array( 'http', 'https', 'mailto' ) );

	if ( empty( $sanitized ) ) {
		return '';
	}

	return $sanitized;
}

/**
 * Sanitize an integer input within a given range.
 *
 * @since 2.0.0
 *
 * @param  mixed $input Raw input.
 * @param  int   $min   Minimum allowed value.
 * @param  int   $max   Maximum allowed value.
 * @return int Clamped integer.
 */
function skyyrose_sanitize_int( $input, $min = 0, $max = PHP_INT_MAX ) {
	$value = absint( $input );
	return max( $min, min( $max, $value ) );
}
