<?php
/**
 * Base REST controller for SEE endpoints.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

abstract class SEE_Rest_Controller extends WP_REST_Controller {

	protected string $namespace = 'see/v1';

	protected SEE_Plugin $plugin;

	public function __construct( SEE_Plugin $plugin ) {
		$this->plugin = $plugin;
	}

	/**
	 * Check if the current user has admin capabilities.
	 */
	public function admin_permission_check( WP_REST_Request $request ): bool {
		return current_user_can( 'manage_options' );
	}

	/**
	 * Public endpoint — no auth required (for analytics beacons).
	 */
	public function public_permission_check( WP_REST_Request $request ): bool {
		return true;
	}

	/**
	 * Sanitize a string parameter.
	 */
	protected function sanitize_param( string $value ): string {
		return sanitize_text_field( wp_unslash( $value ) );
	}
}
