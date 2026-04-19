<?php
/**
 * Experience Engine — Core Bootstrap & Module Registry
 *
 * Central coordinator for the SkyyRose Experience Engine. Manages module
 * registration, settings, design narrative pipeline, and admin menu.
 *
 * @package SkyyRose_Flagship
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

/*--------------------------------------------------------------
 * Constants
 *--------------------------------------------------------------*/
define( 'SKYYROSE_SEE_VERSION', '1.0.0' );
define( 'SKYYROSE_SEE_DB_VERSION', '1.0.0' );

/*--------------------------------------------------------------
 * Settings Helpers
 *--------------------------------------------------------------*/

/**
 * Get an Experience Engine setting.
 *
 * @param string $key     Setting key.
 * @param mixed  $default Default value.
 * @return mixed
 */
function skyyrose_see_get_option( string $key, $default = null ) {
	$settings = get_option( 'skyyrose_see_settings', array() );
	if ( ! is_array( $settings ) ) {
		$settings = array();
	}
	return $settings[ $key ] ?? $default;
}

/**
 * Update an Experience Engine setting.
 *
 * @param string $key   Setting key.
 * @param mixed  $value Setting value.
 */
function skyyrose_see_update_option( string $key, $value ): void {
	$settings = get_option( 'skyyrose_see_settings', array() );
	if ( ! is_array( $settings ) ) {
		$settings = array();
	}
	$settings[ $key ] = $value;
	update_option( 'skyyrose_see_settings', $settings );
}

/**
 * Batch-update multiple Experience Engine settings.
 *
 * @param array $updates Key-value pairs to merge into settings.
 */
function skyyrose_see_update_options( array $updates ): void {
	$settings = get_option( 'skyyrose_see_settings', array() );
	if ( ! is_array( $settings ) ) {
		$settings = array();
	}
	$settings = array_merge( $settings, $updates );
	update_option( 'skyyrose_see_settings', $settings );
}

/*--------------------------------------------------------------
 * Module Registry
 *--------------------------------------------------------------*/

/**
 * Module definitions with priorities and dependencies.
 *
 * Priority determines activation order (lower = first). Modules are sorted
 * by priority before activation to prevent sequencing bugs.
 *
 * @return array<string, array{priority: int, label: string, default: bool}>
 */
function skyyrose_see_get_modules(): array {
	return array(
		'performance_guardian' => array(
			'priority' => 10,
			'label'    => __( 'Performance Guardian', 'skyyrose-flagship' ),
			'default'  => true,
		),
		'experience_analyzer' => array(
			'priority' => 20,
			'label'    => __( 'Experience Analyzer', 'skyyrose-flagship' ),
			'default'  => true,
		),
		'brand_atmosphere'    => array(
			'priority' => 30,
			'label'    => __( 'Brand Atmosphere', 'skyyrose-flagship' ),
			'default'  => true,
		),
		'smart_showcase'      => array(
			'priority' => 40,
			'label'    => __( 'Smart Showcase', 'skyyrose-flagship' ),
			'default'  => true,
		),
		'micro_interactions'  => array(
			'priority' => 50,
			'label'    => __( 'Micro-Interactions', 'skyyrose-flagship' ),
			'default'  => true,
		),
		'personalization'     => array(
			'priority' => 60,
			'label'    => __( 'Personalization', 'skyyrose-flagship' ),
			'default'  => true,
		),
	);
}

/**
 * Check if a module is active.
 *
 * @param string $module_slug Module slug (e.g. 'performance_guardian').
 * @return bool
 */
function skyyrose_see_is_module_active( string $module_slug ): bool {
	$modules = skyyrose_see_get_modules();
	if ( ! isset( $modules[ $module_slug ] ) ) {
		return false;
	}
	$default = $modules[ $module_slug ]['default'];
	return (bool) skyyrose_see_get_option( 'module_' . $module_slug, $default );
}

/**
 * Get all active module slugs, sorted by priority.
 *
 * @return string[]
 */
function skyyrose_see_get_active_modules(): array {
	$modules = skyyrose_see_get_modules();

	// Sort by priority before checking activation state.
	uasort( $modules, function ( $a, $b ) {
		return $a['priority'] - $b['priority'];
	} );

	$active = array();
	foreach ( $modules as $slug => $config ) {
		if ( skyyrose_see_is_module_active( $slug ) ) {
			$active[] = $slug;
		}
	}
	return $active;
}

/*--------------------------------------------------------------
 * Design Narrative Pipeline
 *--------------------------------------------------------------*/

/**
 * Get active design narrative directives.
 *
 * @return array
 */
function skyyrose_see_get_active_directives(): array {
	$directives = skyyrose_see_get_option( 'narrative_directives', array() );
	if ( ! is_array( $directives ) ) {
		return array();
	}
	return array_filter( $directives, function ( $d ) {
		if ( ! is_array( $d ) ) {
			return false;
		}
		// Filter out expired directives.
		if ( ! empty( $d['expires'] ) && strtotime( $d['expires'] ) < time() ) {
			return false;
		}
		return 'accepted' === ( $d['status'] ?? '' );
	} );
}

/**
 * Process a new design narrative directive.
 *
 * @param array $directive Directive data with id, description, target, config, priority.
 * @return array{status: string, message: string}
 */
function skyyrose_see_process_narrative( array $directive ): array {
	$directives = skyyrose_see_get_option( 'narrative_directives', array() );
	if ( ! is_array( $directives ) ) {
		$directives = array();
	}

	// Check for conflicts (same target + active status).
	$target = sanitize_text_field( $directive['target'] ?? 'all' );
	foreach ( $directives as $existing ) {
		if ( ! is_array( $existing ) ) {
			continue;
		}
		if ( ( $existing['target'] ?? '' ) === $target && 'accepted' === ( $existing['status'] ?? '' ) ) {
			// Higher priority wins.
			$existing_priority = absint( $existing['priority'] ?? 5 );
			$new_priority      = absint( $directive['priority'] ?? 5 );
			if ( $new_priority <= $existing_priority ) {
				return array(
					'status'  => 'conflict',
					'message' => sprintf(
						'Conflicts with existing directive %s (priority %d)',
						esc_html( $existing['id'] ?? '?' ),
						$existing_priority
					),
				);
			}
		}
	}

	$directive['status']     = 'accepted';
	$directive['created_at'] = current_time( 'mysql' );
	$directives[]            = $directive;

	skyyrose_see_update_option( 'narrative_directives', $directives );

	return array(
		'status'  => 'accepted',
		'message' => 'Directive accepted',
	);
}

/*--------------------------------------------------------------
 * DB Setup (via theme activation pattern)
 *--------------------------------------------------------------*/

/**
 * Create the analytics table. Called from theme-activation-setup.php pattern.
 */
function skyyrose_see_create_tables(): void {
	if ( get_option( 'skyyrose_see_db_version' ) === SKYYROSE_SEE_DB_VERSION ) {
		return;
	}

	global $wpdb;

	$table   = $wpdb->prefix . 'skyyrose_analytics';
	$charset = $wpdb->get_charset_collate();

	$sql = "CREATE TABLE {$table} (
		id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
		event_date DATE NOT NULL,
		event_type VARCHAR(50) NOT NULL,
		event_target VARCHAR(255) NOT NULL DEFAULT '',
		page_type VARCHAR(50) NOT NULL DEFAULT '',
		collection_slug VARCHAR(50) NOT NULL DEFAULT '',
		event_count INT UNSIGNED NOT NULL DEFAULT 1,
		event_value DECIMAL(10,2) NOT NULL DEFAULT 0.00,
		visitor_hash VARCHAR(64) NOT NULL DEFAULT '',
		created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
		PRIMARY KEY (id),
		KEY idx_date_type (event_date, event_type),
		KEY idx_collection (collection_slug, event_date),
		KEY idx_visitor (visitor_hash, event_date)
	) {$charset};";

	require_once ABSPATH . 'wp-admin/includes/upgrade.php';
	dbDelta( $sql );

	update_option( 'skyyrose_see_db_version', SKYYROSE_SEE_DB_VERSION );
}

// Run DB setup on theme activation and via versioned init check.
add_action( 'after_switch_theme', 'skyyrose_see_create_tables' );
add_action( 'init', function () {
	if ( get_option( 'skyyrose_see_db_version' ) !== SKYYROSE_SEE_DB_VERSION ) {
		skyyrose_see_create_tables();
	}
}, 35 );

/*--------------------------------------------------------------
 * Admin Menu
 *--------------------------------------------------------------*/

add_action( 'admin_menu', function () {
	$parent_slug   = 'skyyrose';
	$parent_exists = ! empty( $GLOBALS['admin_page_hooks'][ $parent_slug ] ?? '' );

	$args = array(
		__( 'Experience Engine', 'skyyrose-flagship' ),
		__( 'Experience', 'skyyrose-flagship' ),
		'manage_options',
		'skyyrose-experience',
		'skyyrose_see_render_dashboard',
	);

	if ( $parent_exists ) {
		add_submenu_page( $parent_slug, ...$args );
	} else {
		add_menu_page(
			$args[0],
			$args[1],
			$args[2],
			$args[3],
			$args[4],
			'dashicons-visibility',
			58
		);
	}
} );

/**
 * Render the admin dashboard. Delegates to admin-experience-dashboard.php.
 */
function skyyrose_see_render_dashboard(): void {
	$dashboard_file = SKYYROSE_DIR . '/inc/admin-experience-dashboard.php';
	if ( file_exists( $dashboard_file ) ) {
		require_once $dashboard_file;
		skyyrose_see_dashboard_page();
	}
}
