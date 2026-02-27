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

	// Skip admin page loads but not AJAX requests (they need CSP protection too).
	if ( is_admin() && ! wp_doing_ajax() ) {
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
		"script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://cdn.babylonjs.com https://stats.wp.com https://widgets.wp.com https://s0.wp.com https://cdn.elementor.com https://ajax.googleapis.com https://unpkg.com https://connect.facebook.net blob:",
		"style-src 'self' 'unsafe-inline' https://fonts-api.wp.com https://fonts.wp.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
		"img-src 'self' data: blob: https://*.wp.com https://secure.gravatar.com https://i0.wp.com https://i1.wp.com https://i2.wp.com https://*.skyyrose.co https://www.facebook.com",
		"font-src 'self' data: https://fonts.wp.com https://cdn.jsdelivr.net",
		"connect-src 'self' https://stats.wp.com https://public-api.wordpress.com https://api.skyyrose.co https://pixel.wp.com https://devskyy.app https://www.facebook.com https://connect.facebook.net",
		"frame-src 'self' https://www.youtube.com https://player.vimeo.com https://widgets.wp.com",
		"frame-ancestors 'self'",
		"worker-src 'self' blob:",
		"child-src 'self' blob:",
		"object-src 'none'",
		"base-uri 'self'",
		"form-action 'self'",
		"upgrade-insecure-requests",
	);

	$csp_policy = implode( '; ', $csp_directives );

	header( 'Content-Security-Policy: ' . $csp_policy );

	// Prevent MIME-type sniffing.
	header( 'X-Content-Type-Options: nosniff' );

	// Prevent clickjacking.
	header( 'X-Frame-Options: SAMEORIGIN' );

	// Enforce HTTPS via HSTS (1 year including subdomains, preload-ready).
	// Only send on HTTPS — sending on HTTP bricks access for max-age duration.
	if ( is_ssl() ) {
		header( 'Strict-Transport-Security: max-age=31536000; includeSubDomains; preload' );
	}

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
 * Disable XML-RPC unconditionally.
 *
 * Jetpack 10.x+ communicates via the REST API, not XML-RPC.
 * The xmlrpc_methods filter below further restricts to jetpack.*
 * methods as a defence-in-depth measure in case this filter is
 * removed by a third-party plugin.
 *
 * Previous implementation checked defined('JETPACK__VERSION') and
 * returned true, which re-enabled XML-RPC for ALL callers whenever
 * Jetpack was merely installed — exposing the site to brute-force
 * and pingback DDoS attacks.  Fixed in v3.2.2.
 *
 * @since 1.0.0
 * @since 3.2.1 Whitelisted Jetpack methods.
 * @since 3.2.2 Disabled unconditionally — Jetpack uses REST API.
 */
function skyyrose_xmlrpc_enabled( $enabled ) {
	return false;
}
add_filter( 'xmlrpc_enabled', 'skyyrose_xmlrpc_enabled' );

/**
 * Remove XML-RPC discovery links and restrict methods to Jetpack only.
 *
 * @since 2.0.0
 * @since 3.2.1 Preserve Jetpack methods.
 * @return void
 */
function skyyrose_remove_xmlrpc_links() {
	remove_action( 'wp_head', 'rsd_link' );
	remove_action( 'wp_head', 'wlwmanifest_link' );
	remove_action( 'xmlrpc_rsd_apis', 'rest_output_rsd' );

	// Keep only Jetpack methods, block all others.
	add_filter(
		'xmlrpc_methods',
		function ( $methods ) {
			$allowed = array();
			foreach ( $methods as $method => $callback ) {
				if ( 0 === strpos( $method, 'jetpack.' ) ) {
					$allowed[ $method ] = $callback;
				}
			}
			return $allowed;
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
 * Remove unnecessary meta tags, links, and HTTP headers from wp_head.
 *
 * @since 1.0.0
 * @since 3.2.2 Remove shortlink from HTTP headers, remove feed links.
 * @return void
 */
function skyyrose_clean_wp_head() {
	// Remove shortlink from HTML head and HTTP Link header.
	remove_action( 'wp_head', 'wp_shortlink_wp_head' );
	remove_action( 'template_redirect', 'wp_shortlink_header', 11 );

	// Remove REST API discovery link (still accessible, just not advertised).
	remove_action( 'wp_head', 'rest_output_link_wp_head' );

	// Remove oEmbed discovery links.
	remove_action( 'wp_head', 'wp_oembed_add_discovery_links' );
	remove_action( 'wp_head', 'wp_oembed_add_host_js' );

	// Remove emoji detection and inline styles.
	remove_action( 'wp_head', 'print_emoji_detection_script', 7 );
	remove_action( 'wp_print_styles', 'print_emoji_styles' );
	remove_action( 'admin_print_scripts', 'print_emoji_detection_script' );
	remove_action( 'admin_print_styles', 'print_emoji_styles' );

	// Remove RSS feed links (not a blog, reduces attack surface).
	remove_action( 'wp_head', 'feed_links', 2 );
	remove_action( 'wp_head', 'feed_links_extra', 3 );

	// Remove Windows Live Writer link.
	remove_action( 'wp_head', 'wlwmanifest_link' );

	// Remove adjacent post links (prev/next).
	remove_action( 'wp_head', 'adjacent_posts_rel_link_wp_head' );
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
 * REST API User Enumeration Block
 *
 * Unauthenticated users must not be able to list usernames,
 * Gravatar hashes, or admin roles via the REST API.
 *--------------------------------------------------------------*/

/**
 * Block REST API user endpoints for unauthenticated requests.
 *
 * @since 3.2.2
 *
 * @param  WP_REST_Response|WP_Error $response Response object.
 * @param  WP_REST_Server            $server   Server instance.
 * @param  WP_REST_Request           $request  Request object.
 * @return WP_REST_Response|WP_Error Filtered response.
 */
function skyyrose_restrict_rest_users( $response, $server, $request ) {
	$route = $request->get_route();

	// Block /wp/v2/users and /wp/v2/users/N for non-logged-in users.
	if ( preg_match( '#^/wp/v2/users#', $route ) && ! is_user_logged_in() ) {
		return new WP_Error(
			'rest_forbidden',
			__( 'Access denied.', 'skyyrose-flagship' ),
			array( 'status' => 403 )
		);
	}

	return $response;
}
add_filter( 'rest_pre_dispatch', 'skyyrose_restrict_rest_users', 10, 3 );

/**
 * Remove REST API user link from HTTP headers and HTML head.
 *
 * Prevents advertising /wp-json/wp/v2/users/1 in Link headers.
 *
 * @since 3.2.2
 */
function skyyrose_remove_rest_user_links() {
	remove_action( 'template_redirect', 'rest_output_link_header', 11 );
	remove_action( 'wp_head', 'rest_output_link_wp_head', 10 );
}
add_action( 'init', 'skyyrose_remove_rest_user_links' );

/*--------------------------------------------------------------
 * Author Enumeration Block
 *
 * Prevent ?author=N from revealing usernames via redirect.
 *--------------------------------------------------------------*/

/**
 * Block author archive enumeration for non-logged-in visitors.
 *
 * @since 3.2.2
 * @return void
 */
function skyyrose_block_author_enumeration() {
	if ( is_admin() ) {
		return;
	}

	// Block ?author=N query parameter.
	if ( isset( $_GET['author'] ) && ! is_user_logged_in() ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended
		wp_safe_redirect( home_url( '/' ), 301 );
		exit;
	}
}
add_action( 'template_redirect', 'skyyrose_block_author_enumeration', 1 );

/**
 * Block author archive pages entirely for non-logged-in visitors.
 *
 * @since 3.2.2
 * @return void
 */
function skyyrose_block_author_archives() {
	if ( is_author() && ! is_user_logged_in() ) {
		wp_safe_redirect( home_url( '/' ), 301 );
		exit;
	}
}
add_action( 'template_redirect', 'skyyrose_block_author_archives', 1 );

/*--------------------------------------------------------------
 * Disable File Editor
 *
 * Prevent editing theme/plugin files from wp-admin.
 * Even if an attacker compromises an admin account, they
 * cannot inject code via Appearance → Theme File Editor.
 *--------------------------------------------------------------*/
if ( ! defined( 'DISALLOW_FILE_EDIT' ) ) {
	define( 'DISALLOW_FILE_EDIT', true );
}

/*--------------------------------------------------------------
 * Disable Application Passwords for non-admin users
 *
 * Reduces attack surface by restricting REST API auth tokens.
 *--------------------------------------------------------------*/
add_filter( 'wp_is_application_passwords_available_for_user', function ( $available, $user ) {
	return user_can( $user, 'manage_options' );
}, 10, 2 );

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
