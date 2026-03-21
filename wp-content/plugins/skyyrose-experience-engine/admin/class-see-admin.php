<?php
/**
 * Admin Dashboard — Analytics display + Design Narrative accept/decline UI.
 *
 * Zero config: works automatically. The dashboard shows what the engine
 * is doing, accepts design narrative input, and displays behavioral data.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SEE_Admin {

	private SEE_Plugin $plugin;

	public function __construct( SEE_Plugin $plugin ) {
		$this->plugin = $plugin;
	}

	public function register( SEE_Loader $loader ): void {
		$loader->add_action( 'admin_menu', $this, 'add_menu_pages' );
		$loader->add_action( 'admin_enqueue_scripts', $this, 'enqueue_admin_assets' );
	}

	public function add_menu_pages(): void {
		// Add under SkyyRose parent menu if it exists, otherwise create top-level.
		$parent_slug = 'skyyrose';
		$parent_exists = ! empty( $GLOBALS['admin_page_hooks'][ $parent_slug ] ?? '' );

		if ( $parent_exists ) {
			add_submenu_page(
				$parent_slug,
				__( 'Experience Engine', 'skyyrose-experience-engine' ),
				__( 'Experience Engine', 'skyyrose-experience-engine' ),
				'manage_options',
				'see-dashboard',
				array( $this, 'render_dashboard' )
			);
		} else {
			add_menu_page(
				__( 'Experience Engine', 'skyyrose-experience-engine' ),
				__( 'Experience Engine', 'skyyrose-experience-engine' ),
				'manage_options',
				'see-dashboard',
				array( $this, 'render_dashboard' ),
				'dashicons-visibility',
				58
			);
		}
	}

	public function enqueue_admin_assets( string $hook ): void {
		if ( 'toplevel_page_see-dashboard' !== $hook && 'skyyrose_page_see-dashboard' !== $hook ) {
			return;
		}

		wp_enqueue_style(
			'see-admin',
			SEE_URI . 'admin/css/see-admin.css',
			array(),
			SEE_VERSION
		);

		wp_enqueue_script(
			'see-admin',
			SEE_URI . 'admin/js/see-admin.js',
			array( 'wp-api-fetch' ),
			SEE_VERSION,
			true
		);

		wp_localize_script( 'see-admin', 'seeAdmin', array(
			'restUrl'   => esc_url_raw( rest_url( 'see/v1/' ) ),
			'restNonce' => wp_create_nonce( 'wp_rest' ),
			'version'   => SEE_VERSION,
		) );
	}

	public function render_dashboard(): void {
		include SEE_DIR . 'admin/partials/see-admin-dashboard.php';
	}
}
