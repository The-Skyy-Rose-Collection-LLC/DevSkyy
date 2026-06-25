<?php
/**
 * Personalization — Curated For You
 *
 * Phase 4 of the SkyyRose Experience Engine.
 *
 * Manages the visitor hash cookie that anchors all behavioral tracking to a
 * single anonymous visitor across sessions. Localizes the hash and REST base
 * URL for personalization.js. The JS module calls the REST endpoint to fetch
 * recommendations, then injects the "Curated For You" grid into the page.
 *
 * @package SkyyRose_Flagship
 * @since   6.4.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

// ---------------------------------------------------------------------------
// Visitor hash management
// ---------------------------------------------------------------------------

/**
 * Get or create a persistent visitor hash stored in a first-party cookie.
 *
 * The hash is 16 hex characters (64-bit) — enough to uniquely identify a
 * browser session without storing any personally identifiable information.
 * Cookie lifespan: 90 days, renewed on each visit.
 *
 * @return string Hex visitor hash.
 */
function skyyrose_see_get_visitor_hash(): string {
	$cookie_name = 'skyy_visitor';

	if ( ! empty( $_COOKIE[ $cookie_name ] ) ) {
		$candidate = sanitize_text_field( wp_unslash( $_COOKIE[ $cookie_name ] ) );
		if ( preg_match( '/^[a-f0-9]{16,64}$/', $candidate ) ) {
			return $candidate;
		}
	}

	$hash    = bin2hex( random_bytes( 8 ) );
	$expires = time() + ( 90 * DAY_IN_SECONDS );

	// phpcs:ignore WordPressVIPMinimum.Functions.RestrictedFunctions.cookies_setcookie
	setcookie(
		$cookie_name,
		$hash,
		array(
			'expires'  => $expires,
			'path'     => '/',
			'secure'   => is_ssl(),
			'httponly' => false, // JS must read it to pass to the REST endpoint.
			'samesite' => 'Lax',
		)
	);

	return $hash;
}

// ---------------------------------------------------------------------------
// JS localization
// ---------------------------------------------------------------------------

/**
 * Localize visitor data for personalization.js.
 *
 * Runs at priority 45 so the skyyrose-personalization handle is already
 * registered (enqueued at priority 42 in skyyrose_enqueue_phase4_assets).
 */
function skyyrose_pg_localize_personalization(): void {
	if ( ! function_exists( 'skyyrose_see_is_module_active' ) ) {
		return;
	}
	if ( ! skyyrose_see_is_module_active( 'personalization' ) ) {
		return;
	}

	// Resolve current collection from page template slug.
	$collection = '';
	if ( is_page() ) {
		$tpl_map    = array(
			'template-collection-black-rose.php'   => 'black-rose',
			'template-collection-love-hurts.php'   => 'love-hurts',
			'template-collection-signature.php'    => 'signature',
			'template-collection-kids-capsule.php' => 'kids-capsule',
		);
		$collection = $tpl_map[ get_page_template_slug() ] ?? '';
	}

	wp_localize_script(
		'skyyrose-personalization',
		'SkyyCurated',
		array(
			'visitorHash' => skyyrose_see_get_visitor_hash(),
			'collection'  => $collection,
			'restBase'    => '/?rest_route=/skyyrose/v1',
			'restNonce'   => wp_create_nonce( 'wp_rest' ),
			'limit'       => 4,
		)
	);
}
add_action( 'wp_enqueue_scripts', 'skyyrose_pg_localize_personalization', 45 );
