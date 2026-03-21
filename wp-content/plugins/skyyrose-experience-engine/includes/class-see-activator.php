<?php
/**
 * Plugin activation handler.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SEE_Activator {

	public static function activate(): void {
		self::create_analytics_table();
		self::set_defaults();
		flush_rewrite_rules();
	}

	/**
	 * Create the analytics rollup table for Experience Analyzer.
	 */
	private static function create_analytics_table(): void {
		global $wpdb;

		$table   = $wpdb->prefix . 'see_analytics';
		$charset = $wpdb->get_charset_collate();

		$sql = "CREATE TABLE IF NOT EXISTS {$table} (
			id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
			event_date DATE NOT NULL,
			event_type VARCHAR(50) NOT NULL,
			event_target VARCHAR(255) NOT NULL DEFAULT '',
			page_type VARCHAR(50) NOT NULL DEFAULT '',
			collection_slug VARCHAR(50) NOT NULL DEFAULT '',
			event_count INT UNSIGNED NOT NULL DEFAULT 1,
			event_value DECIMAL(10,2) NOT NULL DEFAULT 0.00,
			metadata JSON DEFAULT NULL,
			created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
			PRIMARY KEY (id),
			INDEX idx_date_type (event_date, event_type),
			INDEX idx_collection (collection_slug, event_date),
			INDEX idx_page_type (page_type, event_date)
		) {$charset};";

		require_once ABSPATH . 'wp-admin/includes/upgrade.php';
		dbDelta( $sql );

		update_option( 'see_db_version', SEE_VERSION );
	}

	private static function set_defaults(): void {
		if ( false === get_option( 'see_settings' ) ) {
			add_option( 'see_settings', array() );
		}
	}
}
