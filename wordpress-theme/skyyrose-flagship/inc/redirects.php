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
		// $query is '' or begins with '?' — append AFTER home_url(), never into the
		// path (path-concatenation turned ?utm_… links into unknown-slug 404s).
		$target = home_url( $redirects[ $path ] ) . $query;
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

/**
 * Redirect legacy /shop-2/ slug to /shop/.
 *
 * The shop-2 page is a Woo-created duplicate of /shop/ that drifted into
 * production. P0·4 of the 2026-05-20 audit. Canonical shop is /shop/;
 * shop-2 ships a 301 to it. The shop-2 page is also deleted via WP CLI
 * after this redirect ships (so direct DB queries don't surface it),
 * but this redirect remains as the source-of-truth slug map.
 *
 * Mirrors the structure of skyyrose_preorder_slug_redirect() above.
 *
 * @since 1.5.4
 * @return void
 */
function skyyrose_shop2_slug_redirect() {
	$request_uri = isset( $_SERVER['REQUEST_URI'] )
		? sanitize_text_field( wp_unslash( $_SERVER['REQUEST_URI'] ) )
		: '';
	$path        = strtok( $request_uri, '?' );

	if ( '/shop-2/' !== $path && '/shop-2' !== $path ) {
		return;
	}

	$target = home_url( '/shop/' );
	$qs_pos = strpos( $request_uri, '?' );
	if ( false !== $qs_pos ) {
		$target .= substr( $request_uri, $qs_pos );
	}
	wp_safe_redirect( $target, 301 );
	exit;
}
add_action( 'template_redirect', 'skyyrose_shop2_slug_redirect', 1 );

/**
 * Redirect legacy /immersive-{collection}/ URLs to canonical /experience-{collection}/.
 *
 * The immersive pages were renamed to "experience" during v6 navigation rework.
 * External links, sitemap entries, and social referrers that use the old /immersive-{slug}/
 * pattern get a 301 so link equity and bookmarks are preserved.
 *
 * Mirrors skyyrose_collection_redirects() — same query-string pass-through pattern.
 *
 * @since 1.5.5
 * @return void
 */
function skyyrose_immersive_experience_redirects() {
	$redirects = array(
		'/immersive-signature/'    => '/experience-signature/',
		'/immersive-black-rose/'   => '/experience-black-rose/',
		'/immersive-love-hurts/'   => '/experience-love-hurts/',
		'/immersive-kids-capsule/' => '/experience-kids-capsule/',
	);

	$request_uri = isset( $_SERVER['REQUEST_URI'] ) ? sanitize_text_field( wp_unslash( $_SERVER['REQUEST_URI'] ) ) : '';
	$path        = strtok( $request_uri, '?' );
	$query       = strpos( $request_uri, '?' ) !== false ? substr( $request_uri, strpos( $request_uri, '?' ) ) : '';

	if ( isset( $redirects[ $path ] ) ) {
		// $query is '' or begins with '?' — append AFTER home_url(), never into the
		// path (path-concatenation turned ?utm_… links into unknown-slug 404s).
		$target = home_url( $redirects[ $path ] ) . $query;
		wp_safe_redirect( $target, 301 );
		exit;
	}
}
add_action( 'template_redirect', 'skyyrose_immersive_experience_redirects', 1 );
