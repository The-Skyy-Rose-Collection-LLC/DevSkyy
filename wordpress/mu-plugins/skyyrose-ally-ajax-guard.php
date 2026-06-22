<?php
/**
 * Plugin Name: SkyyRose — Keep Ally off non-HTML responses
 * Description: Ally (pojo-accessibility) runs an unconditional output buffer that
 *   injects its remediation <style id="ea11y-remediation-styles"> into EVERY
 *   response, including JSON. That corrupts CommerceKit's nonce endpoint
 *   (?commercekit-ajax=commercekit_get_nonce) and any AJAX/REST JSON body, which
 *   can break cart/checkout. We remove Ally from the active-plugins list ONLY for
 *   AJAX / WC-AJAX / REST requests, so it never loads its buffer there. Normal
 *   front-end HTML pages are untouched — Ally still runs everywhere it should.
 * Version: 1.0.0
 * Author: SkyyRose Dev Team
 *
 * Why an MU-plugin: this must run before the `active_plugins` option is consumed
 * (i.e. before regular plugins load). The theme and regular plugins are too late.
 *
 * @package SkyyRose
 */

defined( 'ABSPATH' ) || exit;

add_filter(
	'option_active_plugins',
	static function ( $plugins ) {
		if ( ! is_array( $plugins ) ) {
			return $plugins;
		}

		$uri        = isset( $_SERVER['REQUEST_URI'] ) ? (string) $_SERVER['REQUEST_URI'] : '';
		$is_ck_ajax = isset( $_GET['commercekit-ajax'] );
		$is_wc_ajax = isset( $_GET['wc-ajax'] );
		$is_rest    = ( '' !== $uri && false !== strpos( $uri, '/wp-json/' ) );

		if ( ! ( $is_ck_ajax || $is_wc_ajax || $is_rest ) ) {
			return $plugins;
		}

		return array_values(
			array_filter(
				$plugins,
				static function ( $plugin ) {
					return false === strpos( (string) $plugin, 'pojo-accessibility/' );
				}
			)
		);
	},
	1
);
