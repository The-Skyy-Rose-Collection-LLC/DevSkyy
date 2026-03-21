<?php
/**
 * Plugin deactivation handler.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SEE_Deactivator {

	public static function deactivate(): void {
		wp_clear_scheduled_hook( 'see_analytics_rollup' );
		wp_clear_scheduled_hook( 'see_directive_cleanup' );
		flush_rewrite_rules();
	}
}
