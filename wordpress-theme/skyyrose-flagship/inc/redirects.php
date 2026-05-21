<?php
/**
 * URL Redirects
 *
 * Handles 301 redirects for legacy URL patterns so incoming links and
 * bookmarks to old paths continue to resolve without a 404.
 *
 * Fires on template_redirect (priority 1) — before WordPress outputs
 * any content — so the redirect header is always clean.
 *
 * @package SkyyRose
 * @since   1.1.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Map legacy /collections/{slug}/ URLs to canonical /collection-{slug}/ URLs.
 *
 * The site previously linked to /collections/black-rose/ etc. The canonical
 * WordPress page slug is /collection-black-rose/. Any hit to the old pattern
 * gets a permanent 301 redirect so link equity and bookmarks are preserved.
 *
 * @since 1.1.0
 * @return void
 */
function skyyrose_collection_redirects() {
	$redirects = array(
		'/collections/black-rose/'   => '/collection-black-rose/',
		'/collections/love-hurts/'   => '/collection-love-hurts/',
		'/collections/signature/'    => '/collection-signature/',
		'/collections/kids-capsule/' => '/collection-kids-capsule/',
	);

	$request_uri = isset( $_SERVER['REQUEST_URI'] ) ? sanitize_text_field( wp_unslash( $_SERVER['REQUEST_URI'] ) ) : '';

	// Strip query string for matching; preserve it on the redirect target.
	$path  = strtok( $request_uri, '?' );
	$query = strpos( $request_uri, '?' ) !== false ? substr( $request_uri, strpos( $request_uri, '?' ) ) : '';

	if ( isset( $redirects[ $path ] ) ) {
		$target = home_url( $redirects[ $path ] . ltrim( $query, '?' ) );
		wp_safe_redirect( $target, 301 );
		exit;
	}
}
add_action( 'template_redirect', 'skyyrose_collection_redirects', 1 );

/**
 * Redirect /preorder/ to /pre-order/ (canonical hyphenated slug).
 *
 * The Pre-Order Gateway page is published at /pre-order/. External links,
 * sitemap entries, and social referrers occasionally use the un-hyphenated
 * /preorder/ form, which 404s. Permanent 301 preserves link equity and
 * keeps inbound traffic resolving to the gateway. Both trailing-slash
 * and no-trailing-slash variants are handled.
 *
 * @since 6.7.0
 * @return void
 */
function skyyrose_preorder_slug_redirect() {
	$request_uri = isset( $_SERVER['REQUEST_URI'] )
		? sanitize_text_field( wp_unslash( $_SERVER['REQUEST_URI'] ) )
		: '';
	$path        = strtok( $request_uri, '?' );

	if ( '/preorder/' !== $path && '/preorder' !== $path ) {
		return;
	}

	$target = home_url( '/pre-order/' );
	$qs_pos = strpos( $request_uri, '?' );
	if ( false !== $qs_pos ) {
		$target .= substr( $request_uri, $qs_pos );
	}
	wp_safe_redirect( $target, 301 );
	exit;
}
add_action( 'template_redirect', 'skyyrose_preorder_slug_redirect', 1 );
