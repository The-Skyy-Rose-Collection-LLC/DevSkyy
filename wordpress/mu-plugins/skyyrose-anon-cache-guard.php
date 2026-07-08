<?php
/**
 * Plugin Name: SkyyRose — Keep anonymous page views edge-cacheable
 * Description: WooCommerce (triggered by CommerceKit's session-bound nonce)
 *   starts a session and emits `Set-Cookie: wp_woocommerce_session_*` on
 *   EVERY anonymous front-end page view. The Atomic/Batcache edge refuses to
 *   cache any response that sets cookies, so every visitor pays the full
 *   ~1.6s PHP render (measured: `x-ac: MISS`,
 *   `server-timing: cache;desc=MISS;dur=1603`, TTFB 1.8-2.5s = 81% of LCP).
 *   This guard swaps in a session handler that refuses to SEND the session
 *   cookie on anonymous cacheable GET page views, and suppresses the cart
 *   count/hash cookies for the same views. Sessions still start the moment
 *   they matter: wc-ajax calls (add-to-cart POSTs), commercekit-ajax nonce
 *   fetches, cart/checkout/account pages, logged-in users, and visitors
 *   already holding a session cookie are all exempt.
 * Version: 1.0.0
 * Author: SkyyRose Dev Team
 *
 * Why an MU-plugin: the cookie comes from WooCommerce core session handling
 * triggered by plugin code — the theme has no seam. The supported seams are
 * `woocommerce_session_handler` (handler class swap) and
 * `woocommerce_set_cart_cookies`.
 *
 * CommerceKit interaction (verified): its nonce is fetched client-side via
 * `?commercekit-ajax=commercekit_get_nonce` (see skyyrose-ally-ajax-guard),
 * which is exempt here — the session it needs is created on that request,
 * not on the cached page HTML.
 *
 * @package SkyyRose
 */

defined( 'ABSPATH' ) || exit;

/**
 * Whether the current request is an anonymous, cacheable front-end GET
 * page view. Evaluated lazily (at cookie-send time), so WP conditionals
 * are safe to use.
 *
 * @return bool
 */
function skyyrose_is_cacheable_anon_pageview() {
	if ( is_admin() || wp_doing_ajax() || wp_doing_cron() ) {
		return false;
	}
	if ( defined( 'WP_CLI' ) && WP_CLI ) {
		return false;
	}
	if ( defined( 'REST_REQUEST' ) && REST_REQUEST ) {
		return false;
	}
	if ( isset( $_GET['wc-ajax'] ) || isset( $_GET['commercekit-ajax'] ) || isset( $_GET['rest_route'] ) ) {
		return false;
	}
	if ( ! isset( $_SERVER['REQUEST_METHOD'] ) || 'GET' !== $_SERVER['REQUEST_METHOD'] ) {
		return false;
	}
	if ( is_user_logged_in() ) {
		return false;
	}
	// A visitor already holding a WooCommerce session keeps it (active cart).
	foreach ( array_keys( $_COOKIE ) as $cookie_name ) {
		if ( 0 === strpos( (string) $cookie_name, 'wp_woocommerce_session_' ) ) {
			return false;
		}
	}
	if ( function_exists( 'is_cart' ) && did_action( 'wp' ) && ( is_cart() || is_checkout() || is_account_page() ) ) {
		return false;
	}
	if ( function_exists( 'WC' ) && null !== WC()->cart && ! WC()->cart->is_empty() ) {
		return false;
	}
	return true;
}

/**
 * Swap in a session handler whose cookie setter no-ops on cacheable
 * anonymous views. Session DATA still saves server-side; only the
 * cache-busting Set-Cookie header is withheld.
 */
add_filter(
	'woocommerce_session_handler',
	static function ( $handler ) {
		if ( ! class_exists( 'WC_Session_Handler' ) ) {
			return $handler;
		}
		if ( ! class_exists( 'SkyyRose_Cacheable_Session_Handler' ) ) {
			/**
			 * WC_Session_Handler that withholds the session cookie on
			 * anonymous cacheable page views.
			 */
			class SkyyRose_Cacheable_Session_Handler extends WC_Session_Handler {
				/**
				 * Set the session cookie unless this view must stay cacheable.
				 *
				 * @param bool $set Whether the cookie should be set.
				 */
				public function set_customer_session_cookie( $set ) {
					if ( $set && skyyrose_is_cacheable_anon_pageview() ) {
						return;
					}
					parent::set_customer_session_cookie( $set );
				}
			}
		}
		return 'SkyyRose_Cacheable_Session_Handler';
	}
);

/**
 * Suppress woocommerce_items_in_cart / woocommerce_cart_hash cookies on the
 * same views (WC core already routes these through this filter).
 */
add_filter(
	'woocommerce_set_cart_cookies',
	static function ( $set ) {
		return skyyrose_is_cacheable_anon_pageview() ? false : $set;
	}
);
