<?php
/**
 * Core plugin orchestrator — singleton.
 *
 * Detects theme mode (enhanced vs standalone), registers all modules,
 * wires hooks, and manages the Design Narrative pipeline.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

final class SEE_Plugin {

	/** @var self|null */
	private static ?self $instance = null;

	/** @var SEE_Loader */
	private SEE_Loader $loader;

	/** @var bool Whether skyyrose-flagship is the active theme. */
	private bool $is_flagship = false;

	/** @var array<string, object> Registered module instances keyed by slug. */
	private array $modules = array();

	/** @var array Plugin settings merged with defaults. */
	private array $settings = array();

	/**
	 * Default settings — every module enabled, Brand Atmosphere opt-in only
	 * on standalone (auto-enabled when flagship theme detected).
	 */
	private const DEFAULTS = array(
		'module_experience_analyzer'  => true,
		'module_scroll_storyteller'   => true,
		'module_smart_showcase'       => true,
		'module_personalization'      => true,
		'module_micro_interactions'   => true,
		'module_performance_guardian' => true,
		'module_brand_atmosphere'     => 'auto', // true | false | 'auto'
		'fastapi_url'                => '',
		'narrative_directives'       => array(),
		'narrative_history'          => array(),
		'engine_overrides'           => array(),
	);

	private function __construct() {}

	public static function instance(): self {
		if ( null === self::$instance ) {
			self::$instance = new self();
		}
		return self::$instance;
	}

	/**
	 * Boot the plugin.
	 */
	public function run(): void {
		$this->detect_theme();
		$this->load_settings();
		$this->loader = new SEE_Loader();

		$this->register_modules();
		$this->register_integrations();
		$this->register_rest_api();

		if ( is_admin() ) {
			$this->register_admin();
		}

		$this->loader->run();
	}

	/*--------------------------------------------------------------
	 * Theme Detection
	 *--------------------------------------------------------------*/

	private function detect_theme(): void {
		$theme = wp_get_theme();
		$this->is_flagship = ( 'skyyrose-flagship' === $theme->get_template() );
	}

	public function is_flagship(): bool {
		return $this->is_flagship;
	}

	/*--------------------------------------------------------------
	 * Settings
	 *--------------------------------------------------------------*/

	private function load_settings(): void {
		$stored        = get_option( 'see_settings', array() );
		$this->settings = wp_parse_args( $stored, self::DEFAULTS );

		// Auto-resolve Brand Atmosphere.
		if ( 'auto' === $this->settings['module_brand_atmosphere'] ) {
			$this->settings['module_brand_atmosphere'] = $this->is_flagship;
		}
	}

	public function get_settings(): array {
		return $this->settings;
	}

	public function get_setting( string $key, mixed $default = null ): mixed {
		return $this->settings[ $key ] ?? $default;
	}

	public function update_settings( array $partial ): void {
		$this->settings = array_merge( $this->settings, $partial );
		update_option( 'see_settings', $this->settings );
	}

	/*--------------------------------------------------------------
	 * Module Registration
	 *--------------------------------------------------------------*/

	private function register_modules(): void {
		$module_map = array(
			'experience_analyzer'  => 'SEE_Experience_Analyzer',
			'scroll_storyteller'   => 'SEE_Scroll_Storyteller',
			'smart_showcase'       => 'SEE_Smart_Showcase',
			'personalization'      => 'SEE_Personalization',
			'micro_interactions'   => 'SEE_Micro_Interactions',
			'performance_guardian' => 'SEE_Performance_Guardian',
			'brand_atmosphere'     => 'SEE_Brand_Atmosphere',
		);

		foreach ( $module_map as $slug => $class ) {
			$setting_key = 'module_' . $slug;
			if ( ! empty( $this->settings[ $setting_key ] ) && class_exists( $class ) ) {
				$module = new $class( $this );
				$module->register( $this->loader );
				$this->modules[ $slug ] = $module;
			}
		}
	}

	public function get_module( string $slug ): ?object {
		return $this->modules[ $slug ] ?? null;
	}

	public function get_active_modules(): array {
		return array_keys( $this->modules );
	}

	/*--------------------------------------------------------------
	 * Integrations
	 *--------------------------------------------------------------*/

	private function register_integrations(): void {
		// Theme Bridge — always loaded, handles engine orchestration.
		$bridge = new SEE_Theme_Bridge( $this );
		$bridge->register( $this->loader );

		// WooCommerce — conditional.
		if ( class_exists( 'WooCommerce' ) ) {
			$wc = new SEE_Woocommerce( $this );
			$wc->register( $this->loader );
		}

		// FastAPI client — always available, degrades gracefully.
		$fastapi = new SEE_Fastapi_Client( $this );
		$fastapi->register( $this->loader );
	}

	/*--------------------------------------------------------------
	 * REST API
	 *--------------------------------------------------------------*/

	private function register_rest_api(): void {
		$this->loader->add_action( 'rest_api_init', $this, 'register_rest_routes' );
	}

	public function register_rest_routes(): void {
		$analytics       = new SEE_Rest_Analytics( $this );
		$personalization = new SEE_Rest_Personalization( $this );
		$settings_ctrl   = new SEE_Rest_Settings( $this );

		$analytics->register_routes();
		$personalization->register_routes();
		$settings_ctrl->register_routes();
	}

	/*--------------------------------------------------------------
	 * Admin
	 *--------------------------------------------------------------*/

	private function register_admin(): void {
		$admin = new SEE_Admin( $this );
		$admin->register( $this->loader );
	}

	/*--------------------------------------------------------------
	 * Design Narrative Pipeline
	 *--------------------------------------------------------------*/

	/**
	 * Accept or decline a design narrative directive.
	 *
	 * @param array $directive {
	 *     @type string $id          Unique directive ID.
	 *     @type string $description Human-readable description.
	 *     @type string $target      Module slug or 'all'.
	 *     @type array  $config      Key-value config overrides.
	 *     @type int    $priority    1-10, higher = more important.
	 *     @type string $expires     ISO 8601 expiration or empty for permanent.
	 * }
	 * @return array { status: 'accepted'|'declined', reason?: string }
	 */
	public function process_narrative( array $directive ): array {
		$id = sanitize_text_field( $directive['id'] ?? wp_generate_uuid4() );

		// Validate target module exists or is 'all'.
		$target = sanitize_text_field( $directive['target'] ?? 'all' );
		if ( 'all' !== $target && ! isset( $this->modules[ $target ] ) ) {
			return $this->decline_narrative( $id, $directive, "Module '{$target}' is not active." );
		}

		// Check for conflicts with existing active directives.
		$active = $this->get_active_directives();
		foreach ( $active as $existing ) {
			if ( $existing['target'] === $target && $existing['id'] !== $id ) {
				$existing_priority = (int) ( $existing['priority'] ?? 5 );
				$new_priority      = (int) ( $directive['priority'] ?? 5 );
				if ( $new_priority <= $existing_priority ) {
					return $this->decline_narrative(
						$id,
						$directive,
						"Conflicts with active directive '{$existing['id']}' (priority {$existing_priority})."
					);
				}
				// New directive has higher priority — deactivate the old one.
				$this->deactivate_directive( $existing['id'] );
			}
		}

		// Accept.
		$directive['id']     = $id;
		$directive['status'] = 'accepted';
		$directive['accepted_at'] = gmdate( 'c' );

		$directives   = $this->settings['narrative_directives'];
		$directives[] = $directive;
		$this->update_settings( array( 'narrative_directives' => $directives ) );

		// Log to history.
		$this->log_narrative_event( $id, 'accepted', $directive['description'] ?? '' );

		return array( 'status' => 'accepted', 'id' => $id );
	}

	private function decline_narrative( string $id, array $directive, string $reason ): array {
		$this->log_narrative_event( $id, 'declined', $reason );
		return array( 'status' => 'declined', 'id' => $id, 'reason' => $reason );
	}

	private function deactivate_directive( string $id ): void {
		$directives = array_filter(
			$this->settings['narrative_directives'],
			fn( $d ) => ( $d['id'] ?? '' ) !== $id
		);
		$this->update_settings( array( 'narrative_directives' => array_values( $directives ) ) );
		$this->log_narrative_event( $id, 'superseded', 'Replaced by higher-priority directive.' );
	}

	public function get_active_directives(): array {
		$now = time();
		return array_filter(
			$this->settings['narrative_directives'],
			function ( $d ) use ( $now ) {
				if ( ( $d['status'] ?? '' ) !== 'accepted' ) {
					return false;
				}
				if ( ! empty( $d['expires'] ) && strtotime( $d['expires'] ) < $now ) {
					return false;
				}
				return true;
			}
		);
	}

	/**
	 * Get directive config for a specific module (merged from all applicable directives).
	 */
	public function get_directive_config( string $module_slug ): array {
		$config = array();
		$active = $this->get_active_directives();

		// Sort by priority ascending so higher priority overrides.
		usort( $active, fn( $a, $b ) => ( $a['priority'] ?? 5 ) <=> ( $b['priority'] ?? 5 ) );

		foreach ( $active as $directive ) {
			$target = $directive['target'] ?? 'all';
			if ( 'all' === $target || $target === $module_slug ) {
				$config = array_merge( $config, $directive['config'] ?? array() );
			}
		}

		return $config;
	}

	private function log_narrative_event( string $id, string $action, string $detail ): void {
		$history   = $this->settings['narrative_history'];
		$history[] = array(
			'id'        => $id,
			'action'    => $action,
			'detail'    => $detail,
			'timestamp' => gmdate( 'c' ),
		);

		// Keep last 100 entries.
		if ( count( $history ) > 100 ) {
			$history = array_slice( $history, -100 );
		}

		$this->update_settings( array( 'narrative_history' => $history ) );
	}
}
