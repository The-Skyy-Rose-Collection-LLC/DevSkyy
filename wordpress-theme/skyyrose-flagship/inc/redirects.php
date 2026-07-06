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
 * Collection slugs served under the canonical /collections/{slug}/ routes.
 *
 * @since 1.8.0
 * @return string[] Collection slugs.
 */
function skyyrose_canonical_collection_slugs() {
	return array( 'black-rose', 'love-hurts', 'signature', 'kids-capsule' );
}

/**
 * Rewrite canonical /collections/{slug}/ routes onto the existing
 * collection-{slug} pages.
 *
 * Route architecture (structural remediation WS2): /collections/{slug}/ is
 * the LOCKED canonical URL for every collection. The underlying WordPress
 * pages still carry their legacy collection-{slug} slugs, so these rewrites
 * resolve the canonical routes without touching site state. The follow-up
 * page-slug migration is logged in REMEDIATION_MAP.md.
 *
 * Requires a permalink flush on deploy (HG-4).
 *
 * @since 1.8.0
 * @return void
 */
function skyyrose_collection_route_rewrites() {
	$slugs = implode( '|', array_map( 'preg_quote', skyyrose_canonical_collection_slugs() ) );
	add_rewrite_rule(
		'^collections/(' . $slugs . ')/?$',
		'index.php?pagename=collection-$matches[1]',
		'top'
	);
}
add_action( 'init', 'skyyrose_collection_route_rewrites' );

/**
 * Stop WP core from canonical-redirecting /collections/{slug}/ back to the
 * legacy page permalink (/collection-{slug}/), which would loop against the
 * 301 flip below.
 *
 * @since 1.8.0
 * @param string|false $redirect_url  Proposed canonical redirect target.
 * @param string       $requested_url Originally requested URL.
 * @return string|false
 */
function skyyrose_collections_keep_canonical_route( $redirect_url, $requested_url ) {
	// Scope to the exact canonical routes (trailing-slash + query tolerant) so
	// WP's normal canonicalization — e.g. trailing-slash normalization on
	// /collections/ itself or unknown child paths — keeps working.
	$slugs = implode( '|', array_map( 'preg_quote', skyyrose_canonical_collection_slugs() ) );
	if ( preg_match( '#/collections/(' . $slugs . ')/?($|\?)#', (string) $requested_url ) ) {
		return false;
	}
	return $redirect_url;
}
add_filter( 'redirect_canonical', 'skyyrose_collections_keep_canonical_route', 10, 2 );

/**
 * Emit canonical /collections/{slug}/ permalinks for the collection pages.
 *
 * Every get_permalink()/rel-canonical consumer (templates, sitemaps, menus,
 * breadcrumbs, JSON-LD) automatically produces the canonical route, so no
 * template can leak a legacy /collection-{slug}/ URL via the permalink API.
 *
 * @since 1.8.0
 * @param string      $link Page permalink.
 * @param int|WP_Post $post Page ID or object.
 * @return string
 */
function skyyrose_collections_page_link( $link, $post ) {
	$page = get_post( $post );
	if ( ! $page instanceof WP_Post ) {
		return $link;
	}
	foreach ( skyyrose_canonical_collection_slugs() as $slug ) {
		if ( 'collection-' . $slug === $page->post_name ) {
			return home_url( '/collections/' . $slug . '/' );
		}
	}
	return $link;
}
add_filter( 'page_link', 'skyyrose_collections_page_link', 10, 2 );

/**
 * 301 legacy collection + experience routes to canonical /collections/ URLs.
 *
 * Canonical direction FLIPPED (structural remediation WS2) — the site
 * previously 301'd /collections/{slug}/ → /collection-{slug}/; the locked
 * route map is the reverse. Experience pages merged into their collection
 * pages (WS3), so /experience-{slug}/ and /experiences/ 301 as well.
 *
 * @since 1.8.0
 * @return void
 */
function skyyrose_collection_redirects() {
	$redirects = array(
		'/collections/custom-collection/' => '/collections/',
		'/experiences/'                   => '/collections/',
	);
	foreach ( skyyrose_canonical_collection_slugs() as $slug ) {
		$redirects[ '/collection-' . $slug . '/' ] = '/collections/' . $slug . '/';
		$redirects[ '/experience-' . $slug . '/' ] = '/collections/' . $slug . '/';
	}

	$request_uri = isset( $_SERVER['REQUEST_URI'] ) ? sanitize_text_field( wp_unslash( $_SERVER['REQUEST_URI'] ) ) : '';

	// Strip query string for matching; preserve it on the redirect target.
	$path  = strtok( $request_uri, '?' );
	$query = strpos( $request_uri, '?' ) !== false ? substr( $request_uri, strpos( $request_uri, '?' ) ) : '';

	// Match trailing-slash and bare variants alike.
	$path = rtrim( $path, '/' ) . '/';

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
 * Salvage Shopify-era /products/{slug} URLs still in search indexes.
 *
 * Google still indexes www.skyyrose.co/products/… paths from the Shopify
 * storefront; they 404 on WordPress. Best-match: a WooCommerce product with
 * the same slug gets a 301 to its PDP; anything else lands on /collections/.
 *
 * @since 1.8.0
 * @return void
 */
function skyyrose_legacy_products_redirect() {
	$request_uri = isset( $_SERVER['REQUEST_URI'] ) ? sanitize_text_field( wp_unslash( $_SERVER['REQUEST_URI'] ) ) : '';
	$path        = strtok( $request_uri, '?' );

	if ( ! preg_match( '#^/products/([^/]+)/?$#', (string) $path, $matches ) ) {
		return;
	}

	$target  = home_url( '/collections/' );
	$product = get_page_by_path( sanitize_title( $matches[1] ), OBJECT, 'product' );
	if ( $product instanceof WP_Post && 'publish' === $product->post_status ) {
		$permalink = get_permalink( $product );
		if ( $permalink ) {
			$target = $permalink;
		}
	}

	wp_safe_redirect( $target, 301 );
	exit;
}
add_action( 'template_redirect', 'skyyrose_legacy_products_redirect', 1 );

/**
 * Virtual /size-guide/ route (structural remediation WS4).
 *
 * The canonical size-guide deep link previously 404'd (footer linked a dead
 * /contact/#size-guide anchor). No WP page object is required: a rewrite
 * maps the route to a query var and template_include serves
 * template-size-guide.php with a clean 200.
 *
 * Requires a permalink flush on deploy (HG-4).
 *
 * @since 1.8.0
 * @return void
 */
function skyyrose_size_guide_route() {
	add_rewrite_rule( '^size-guide/?$', 'index.php?skyyrose_virtual=size-guide', 'top' );
}
add_action( 'init', 'skyyrose_size_guide_route' );

/**
 * Register the virtual-route query var.
 *
 * @since 1.8.0
 * @param string[] $vars Public query vars.
 * @return string[]
 */
function skyyrose_virtual_query_var( $vars ) {
	$vars[] = 'skyyrose_virtual';
	return $vars;
}
add_filter( 'query_vars', 'skyyrose_virtual_query_var' );

/**
 * Serve the size-guide template on the virtual route.
 *
 * @since 1.8.0
 * @param string $template Resolved template path.
 * @return string
 */
function skyyrose_virtual_template( $template ) {
	if ( 'size-guide' !== get_query_var( 'skyyrose_virtual' ) ) {
		return $template;
	}

	global $wp_query;
	$wp_query->is_404 = false;
	status_header( 200 );

	$virtual = get_theme_file_path( 'template-size-guide.php' );
	return file_exists( $virtual ) ? $virtual : $template;
}
add_filter( 'template_include', 'skyyrose_virtual_template' );

/**
 * Canonical + title for the virtual size-guide route (no page object means
 * core emits neither).
 *
 * @since 1.8.0
 * @return void
 */
function skyyrose_virtual_head_meta() {
	if ( 'size-guide' !== get_query_var( 'skyyrose_virtual' ) ) {
		return;
	}
	echo '<link rel="canonical" href="' . esc_url( home_url( '/size-guide/' ) ) . '" />' . "\n";
}
add_action( 'wp_head', 'skyyrose_virtual_head_meta', 5 );

/**
 * Document title for the virtual route.
 *
 * @since 1.8.0
 * @param array $title Title parts.
 * @return array
 */
function skyyrose_virtual_document_title( $title ) {
	if ( 'size-guide' === get_query_var( 'skyyrose_virtual' ) ) {
		$title['title'] = __( 'Size Guide', 'skyyrose' );
	}
	return $title;
}
add_filter( 'document_title_parts', 'skyyrose_virtual_document_title' );

/**
 * One-shot rewrite flush per theme version.
 *
 * The rewrite rules above (/collections/{slug}/, /size-guide/) need a
 * permalink flush to take effect, but the SFTP deploy never triggers the
 * switch-theme lifecycle where the theme's only other flush lives. Mirror
 * the menu-rebuild pattern: flush once when SKYYROSE_VERSION changes.
 * Runs at init 30 — after every add_rewrite_rule() registered at init 10.
 *
 * @since 1.8.0
 * @return void
 */
function skyyrose_flush_rewrites_once() {
	if ( get_option( 'skyyrose_rewrites_flushed_v' ) === SKYYROSE_VERSION ) {
		return;
	}
	flush_rewrite_rules();
	update_option( 'skyyrose_rewrites_flushed_v', SKYYROSE_VERSION );
}
add_action( 'init', 'skyyrose_flush_rewrites_once', 30 );

/**
 * Case-normalize 404ing uppercase paths (e.g. /PRE-ORDER/ → /pre-order/).
 *
 * Runs at priority 5 — after the explicit slug maps above — and only rescues
 * requests that would otherwise 404, so mixed-case media/file URLs that
 * resolve are never touched.
 *
 * @since 1.8.0
 * @return void
 */
function skyyrose_case_normalize_redirect() {
	if ( ! is_404() ) {
		return;
	}

	$request_uri = isset( $_SERVER['REQUEST_URI'] ) ? sanitize_text_field( wp_unslash( $_SERVER['REQUEST_URI'] ) ) : '';
	$path        = (string) strtok( $request_uri, '?' );
	$lower       = strtolower( $path );

	if ( $path === $lower || '' === $path ) {
		return;
	}

	$query  = strpos( $request_uri, '?' ) !== false ? substr( $request_uri, strpos( $request_uri, '?' ) ) : '';
	$target = home_url( $lower ) . $query;
	wp_safe_redirect( $target, 301 );
	exit;
}
add_action( 'template_redirect', 'skyyrose_case_normalize_redirect', 5 );

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
