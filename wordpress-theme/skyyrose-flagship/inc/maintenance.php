<?php
/**
 * Coming-Soon / Maintenance Mode
 *
 * Active when SKYYROSE_COMING_SOON_MODE constant is true (defined in
 * functions.php). When active, every public request is routed to
 * template-coming-soon.php and responds HTTP 503 + Retry-After so
 * crawlers know the state is temporary. Logged-in users, admin pages,
 * AJAX, REST, cron, login, and theme assets bypass the redirect so
 * the operator can keep working behind the veil.
 *
 * Lift the veil by setting SKYYROSE_COMING_SOON_MODE to false in
 * functions.php and redeploying — that's the entire toggle.
 *
 * @package SkyyRose
 * @since   1.4.0
 */

defined( 'ABSPATH' ) || exit;

/**
 * Whether the coming-soon veil is currently active.
 *
 * Wraps the constant check so callers don't depend on the constant
 * being defined. Default: false (site is live).
 *
 * @return bool
 */
function skyyrose_is_coming_soon_active() {
	return defined( 'SKYYROSE_COMING_SOON_MODE' ) && SKYYROSE_COMING_SOON_MODE;
}

/**
 * Whether the current request should bypass the coming-soon redirect.
 *
 * Bypasses: admin, AJAX, REST, cron, login, theme assets, logged-in
 * users with edit_posts capability, and any request carrying the
 * ?preview=coming-soon query string (for unauthenticated QA).
 *
 * @return bool
 */
function skyyrose_coming_soon_should_bypass() {
	// WordPress internals — never veil.
	if ( is_admin() || wp_doing_ajax() || wp_doing_cron() ) {
		return true;
	}
	if ( defined( 'REST_REQUEST' ) && REST_REQUEST ) {
		return true;
	}
	if ( isset( $GLOBALS['pagenow'] ) && in_array( $GLOBALS['pagenow'], array( 'wp-login.php', 'wp-register.php' ), true ) ) {
		return true;
	}

	// Logged-in operators (anyone who can edit content) keep full site access.
	if ( is_user_logged_in() && current_user_can( 'edit_posts' ) ) {
		return true;
	}

	// QA preview via signed query string — allows unauthenticated link-share.
	// e.g. https://skyyrose.co/?preview=coming-soon (always allowed) OR
	// ?bypass-coming-soon=<token> (token must match COMING_SOON_BYPASS_TOKEN
	// constant if defined; otherwise this branch is inert).
	// phpcs:ignore WordPress.Security.NonceVerification.Recommended -- read-only query check; auth via hash_equals against server-side token constant.
	if ( isset( $_GET['bypass-coming-soon'] ) && defined( 'SKYYROSE_COMING_SOON_BYPASS_TOKEN' ) ) {
		// phpcs:ignore WordPress.Security.NonceVerification.Recommended -- same as above.
		$token = sanitize_text_field( wp_unslash( $_GET['bypass-coming-soon'] ) );
		if ( hash_equals( (string) SKYYROSE_COMING_SOON_BYPASS_TOKEN, $token ) ) {
			return true;
		}
	}

	return false;
}

/**
 * Route every public request to the coming-soon template while the veil is active.
 *
 * Hooks at template_redirect (priority 1) so it runs before any other
 * template logic. Responds 503 Service Unavailable + Retry-After so
 * search engines treat the state as temporary and do not deindex pages.
 */
function skyyrose_coming_soon_redirect() {
	if ( ! skyyrose_is_coming_soon_active() ) {
		return;
	}
	if ( skyyrose_coming_soon_should_bypass() ) {
		return;
	}

	// SEO-friendly temporary status. Retry-After in seconds (default 6 hours).
	$retry_after = (int) apply_filters( 'skyyrose_coming_soon_retry_after', 6 * HOUR_IN_SECONDS );
	status_header( 503 );
	nocache_headers();
	header( 'Retry-After: ' . max( 60, $retry_after ) );

	$template = SKYYROSE_DIR . '/template-coming-soon.php';
	if ( file_exists( $template ) ) {
		include $template;
		exit;
	}

	// Fail-safe: if the template is missing, emit a minimal HTML page.
	wp_die(
		esc_html__( 'The Skyy Rose Collection is preparing the next chapter. Please return shortly.', 'skyyrose' ),
		esc_html__( 'Coming soon — The Skyy Rose Collection', 'skyyrose' ),
		array( 'response' => 503 )
	);
}
add_action( 'template_redirect', 'skyyrose_coming_soon_redirect', 1 );

/**
 * Hide the admin bar on the coming-soon page even when an operator is logged in.
 *
 * Keeps the preview pixel-perfect for ops review. The admin bar is the
 * only WP chrome that would leak into the otherwise-bare coming-soon
 * template. Pair with `?preview=coming-soon` to QA as anonymous.
 */
function skyyrose_coming_soon_hide_admin_bar() {
	if ( ! skyyrose_is_coming_soon_active() ) {
		return;
	}
	// phpcs:ignore WordPress.Security.NonceVerification.Recommended -- read-only query check, no state mutation; just toggles admin bar visibility.
	if ( isset( $_GET['preview'] ) && 'coming-soon' === sanitize_key( wp_unslash( $_GET['preview'] ) ) ) {
		add_filter( 'show_admin_bar', '__return_false' );
	}
}
add_action( 'init', 'skyyrose_coming_soon_hide_admin_bar' );
