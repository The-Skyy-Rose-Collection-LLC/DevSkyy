<?php
/**
 * Theme Bridge — Detects skyyrose-flagship and orchestrates existing engines.
 *
 * The theme has 10 powerful conversion/engagement engines that are DISABLED
 * at enqueue-engines.php:210-221 pending a Lighthouse audit. This bridge
 * re-enables them conditionally per page context with Performance Guardian
 * ensuring animation budgets are respected.
 *
 * In standalone mode (any other theme), this class enqueues the plugin's
 * own CSS/JS modules and passes brand defaults via wp_localize_script.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SEE_Theme_Bridge {

	private SEE_Plugin $plugin;

	/**
	 * Engine-to-page-type mapping.
	 * Keys are theme function names, values are arrays of page types where they activate.
	 */
	private const ENGINE_MAP = array(
		'skyyrose_enqueue_aurora_engine'              => array( 'home', 'collection', 'immersive', 'page' ),
		'skyyrose_enqueue_magnetic_obsidian'          => array( 'product', 'collection' ),
		'skyyrose_enqueue_conversion_engine'          => array( 'product', 'cart', 'checkout' ),
		'skyyrose_enqueue_adaptive_personalization'   => array( 'product', 'collection', 'shop', 'home' ),
		'skyyrose_enqueue_journey_gamification'       => array( 'immersive', 'collection' ),
		'skyyrose_enqueue_momentum_commerce'          => array( 'home', 'collection' ),
		'skyyrose_enqueue_velocity_scroll'            => array( 'immersive', 'product' ),
		'skyyrose_enqueue_pulse_engine'               => array( 'home', 'shop', 'collection' ),
		'skyyrose_enqueue_the_pulse'                  => array( 'product', 'shop', 'collection' ),
		'skyyrose_enqueue_social_proof'               => array( 'product', 'cart' ),
	);

	/**
	 * Priority map matching the original commented-out values in enqueue-engines.php.
	 */
	private const PRIORITY_MAP = array(
		'skyyrose_enqueue_social_proof'             => 30,
		'skyyrose_enqueue_the_pulse'                => 32,
		'skyyrose_enqueue_aurora_engine'             => 34,
		'skyyrose_enqueue_magnetic_obsidian'         => 36,
		'skyyrose_enqueue_conversion_engine'         => 38,
		'skyyrose_enqueue_adaptive_personalization'  => 42,
		'skyyrose_enqueue_journey_gamification'      => 44,
		'skyyrose_enqueue_momentum_commerce'         => 45,
		'skyyrose_enqueue_velocity_scroll'           => 46,
		'skyyrose_enqueue_pulse_engine'              => 47,
	);

	public function __construct( SEE_Plugin $plugin ) {
		$this->plugin = $plugin;
	}

	public function register( SEE_Loader $loader ): void {
		$loader->add_action( 'wp_enqueue_scripts', $this, 'enqueue_core_assets', 50 );

		if ( $this->plugin->is_flagship() ) {
			$loader->add_action( 'wp_enqueue_scripts', $this, 'orchestrate_theme_engines', 55 );
		}

		$loader->add_action( 'wp_enqueue_scripts', $this, 'localize_config', 60 );
	}

	/**
	 * Enqueue the plugin's own core assets (always loaded).
	 */
	public function enqueue_core_assets(): void {
		if ( is_admin() ) {
			return;
		}

		// Design tokens — only in standalone mode. In enhanced mode, theme tokens take precedence.
		if ( ! $this->plugin->is_flagship() ) {
			wp_enqueue_style(
				'see-tokens',
				SEE_URI . 'public/css/see-tokens.css',
				array(),
				SEE_VERSION
			);
		}

		// Core event bus.
		wp_enqueue_script(
			'see-core',
			SEE_URI . 'public/js/see-core.js',
			array(),
			SEE_VERSION,
			true
		);
	}

	/**
	 * Re-enable theme engines contextually based on current page type.
	 * Only runs when skyyrose-flagship is the active theme.
	 */
	public function orchestrate_theme_engines(): void {
		if ( is_admin() ) {
			return;
		}

		$page_type = $this->detect_page_type();
		$overrides = $this->plugin->get_setting( 'engine_overrides', array() );

		// Check directive overrides for engine activation.
		$directive_config = $this->plugin->get_directive_config( 'theme_bridge' );
		$force_engines    = $directive_config['force_engines'] ?? array();
		$block_engines    = $directive_config['block_engines'] ?? array();

		foreach ( self::ENGINE_MAP as $function_name => $page_types ) {
			// Skip if function doesn't exist in theme.
			if ( ! function_exists( $function_name ) ) {
				continue;
			}

			// Check manual overrides from settings.
			$engine_slug = str_replace( 'skyyrose_enqueue_', '', $function_name );
			if ( isset( $overrides[ $engine_slug ] ) ) {
				if ( ! $overrides[ $engine_slug ] ) {
					continue; // Explicitly disabled.
				}
				// Explicitly enabled — skip page type check.
				$this->activate_engine( $function_name );
				continue;
			}

			// Check directive blocks.
			if ( in_array( $engine_slug, $block_engines, true ) ) {
				continue;
			}

			// Check directive force-enable.
			if ( in_array( $engine_slug, $force_engines, true ) ) {
				$this->activate_engine( $function_name );
				continue;
			}

			// Default: activate if page type matches.
			if ( in_array( $page_type, $page_types, true ) ) {
				$this->activate_engine( $function_name );
			}
		}
	}

	/**
	 * Call the theme's enqueue function directly (same as what the commented-out
	 * add_action calls would have done).
	 */
	private function activate_engine( string $function_name ): void {
		call_user_func( $function_name );
	}

	/**
	 * Detect the current page type for engine routing.
	 */
	private function detect_page_type(): string {
		if ( function_exists( 'is_product' ) && is_product() ) {
			return 'product';
		}
		if ( function_exists( 'is_cart' ) && is_cart() ) {
			return 'cart';
		}
		if ( function_exists( 'is_checkout' ) && is_checkout() ) {
			return 'checkout';
		}
		if ( function_exists( 'is_shop' ) && is_shop() ) {
			return 'shop';
		}
		if ( is_front_page() || is_home() ) {
			return 'home';
		}
		if ( function_exists( 'is_product_category' ) && is_product_category() ) {
			return 'collection';
		}

		// Detect immersive experience templates.
		if ( is_page() ) {
			$template = get_page_template_slug();
			if ( $template && str_contains( $template, 'immersive' ) ) {
				return 'immersive';
			}
			if ( $template && str_contains( $template, 'collection' ) ) {
				return 'collection';
			}
		}

		return 'page';
	}

	/**
	 * Pass configuration to JS via wp_localize_script on see-core.
	 */
	public function localize_config(): void {
		if ( is_admin() || ! wp_script_is( 'see-core', 'enqueued' ) ) {
			return;
		}

		$page_type   = $this->detect_page_type();
		$collection  = $this->get_current_collection();
		$col_config  = $this->get_collection_config( $collection );

		$data = array(
			'version'          => SEE_VERSION,
			'isFlagship'       => $this->plugin->is_flagship(),
			'isWooCommerce'    => class_exists( 'WooCommerce' ),
			'pageType'         => $page_type,
			'collection'       => $collection,
			'collectionConfig' => $col_config,
			'productId'        => $this->get_current_product_id(),
			'productSku'       => $this->get_current_product_sku(),
			'restUrl'          => esc_url_raw( rest_url( 'see/v1/' ) ),
			'restNonce'        => wp_create_nonce( 'wp_rest' ),
			'directives'       => $this->plugin->get_active_directives(),
			'modules'          => $this->get_module_configs(),
			'activeModules'    => $this->plugin->get_active_modules(),
		);

		wp_localize_script( 'see-core', 'seeConfig', $data );
	}

	private function get_current_collection(): string {
		if ( function_exists( 'skyyrose_get_product_collection' ) && function_exists( 'is_product' ) && is_product() ) {
			global $product;
			if ( $product ) {
				return skyyrose_get_product_collection( $product->get_id() );
			}
		}

		// Detect from page template slug.
		if ( is_page() ) {
			$template = get_page_template_slug();
			if ( preg_match( '/collection-([a-z-]+)/', $template, $m ) ) {
				return $m[1];
			}
			if ( preg_match( '/immersive-([a-z-]+)/', $template, $m ) ) {
				return $m[1];
			}
		}

		return '';
	}

	private function get_collection_config( string $collection ): array {
		if ( $collection && function_exists( 'skyyrose_collection_config' ) ) {
			return skyyrose_collection_config( $collection );
		}

		// Standalone fallback defaults.
		$defaults = array(
			'black-rose'   => array( 'accent' => '#C0C0C0', 'label' => 'Black Rose', 'mood' => 'gothic' ),
			'love-hurts'   => array( 'accent' => '#DC143C', 'label' => 'Love Hurts', 'mood' => 'passionate' ),
			'signature'    => array( 'accent' => '#D4AF37', 'label' => 'Signature', 'mood' => 'refined' ),
			'kids-capsule' => array( 'accent' => '#FFB6C1', 'label' => 'Kids Capsule', 'mood' => 'playful' ),
		);

		return $defaults[ $collection ] ?? array();
	}

	private function get_current_product_id(): int {
		if ( function_exists( 'is_product' ) && is_product() ) {
			global $product;
			return $product ? $product->get_id() : 0;
		}
		return 0;
	}

	private function get_current_product_sku(): string {
		if ( function_exists( 'is_product' ) && is_product() ) {
			global $product;
			return $product ? $product->get_sku() : '';
		}
		return '';
	}

	/**
	 * Gather per-module config objects for JS consumption.
	 */
	private function get_module_configs(): array {
		$configs = array();
		foreach ( $this->plugin->get_active_modules() as $slug ) {
			$configs[ $slug ] = $this->plugin->get_directive_config( $slug );
		}
		return $configs;
	}
}
