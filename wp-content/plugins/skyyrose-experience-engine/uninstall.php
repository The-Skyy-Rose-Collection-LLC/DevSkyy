<?php
/**
 * Clean removal of all plugin data.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

if ( ! defined( 'WP_UNINSTALL_PLUGIN' ) ) {
	exit;
}

global $wpdb;

// Remove options.
delete_option( 'see_settings' );
delete_option( 'see_db_version' );

// Remove analytics table.
$table = $wpdb->prefix . 'see_analytics';
$wpdb->query( $wpdb->prepare( 'DROP TABLE IF EXISTS %i', $table ) );

// Remove transients.
$wpdb->query(
	"DELETE FROM {$wpdb->options}
	 WHERE option_name LIKE '_transient_see_%'
	    OR option_name LIKE '_transient_timeout_see_%'"
);
