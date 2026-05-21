<?php
/**
 * Enqueue — Experience Engine phases 2/3/4 + commercial polish
 *
 * Each phase function is gated by `skyyrose_see_is_module_active()` so the
 * features can be toggled from the WP admin without a code deploy. Extracted
 * from inc/enqueue.php in v1.5.0 to keep that file under the 800-line cap.
 *
 * Hook priority order:
 *   25 — commercial-polish (after template styles at 20, so it has highest
 *        CSS specificity for the typography/card refinement layer)
 *   30 — phase 2 (performance-guardian, brand-atmosphere)
 *   40 — phase 3 (experience-analyzer, smart-showcase, micro-interactions)
 *   42 — phase 4 (personalization) — before personalization.php's
 *        wp_localize_script at priority 45
 *
 * @package SkyyRose
 * @since   1.5.0
 */

defined( 'ABSPATH' ) || exit;

/**
 * Enqueue Phase 2 Experience Engine assets.
 *
 * - performance-guardian.js loads globally on every page (priority 30).
 * - brand-atmosphere.css + brand-atmosphere.js load on collection pages only.
 *
 * Both checks respect the Experience Engine module activation state.
 */
function skyyrose_enqueue_phase2_assets(): void {
	if ( ! function_exists( 'skyyrose_see_is_module_active' ) ) {
		return;
	}

	$base_js_dir  = SKYYROSE_DIR . '/assets/js';
	$base_css_dir = SKYYROSE_DIR . '/assets/css';
	$js_uri       = SKYYROSE_ASSETS_URI . '/js';
	$css_uri      = SKYYROSE_ASSETS_URI . '/css';

	// ------------------------------------------------------------------
	// Performance Guardian — all pages.
	// ------------------------------------------------------------------
	if ( skyyrose_see_is_module_active( 'performance_guardian' ) ) {
		if ( file_exists( $base_js_dir . '/performance-guardian.js' ) ) {
			wp_enqueue_script(
				'skyyrose-performance-guardian',
				$js_uri . '/performance-guardian.js',
				array(),
				SKYYROSE_VERSION,
				array(
					'strategy'  => 'defer',
					'in_footer' => true,
				)
			);
		}
	}

	// ------------------------------------------------------------------
	// Brand Atmosphere — collection pages only.
	// ------------------------------------------------------------------
	if ( skyyrose_see_is_module_active( 'brand_atmosphere' ) ) {
		$slug             = skyyrose_get_current_template_slug();
		$collection_slugs = array( 'collection-standalone', 'collection', 'collection-v4' );

		if ( in_array( $slug, $collection_slugs, true ) ) {
			if ( file_exists( $base_css_dir . '/brand-atmosphere.css' ) ) {
				wp_enqueue_style(
					'skyyrose-brand-atmosphere',
					$css_uri . '/brand-atmosphere.css',
					array( 'skyyrose-design-tokens' ),
					SKYYROSE_VERSION
				);
			}

			if ( file_exists( $base_js_dir . '/brand-atmosphere.js' ) ) {
				wp_enqueue_script(
					'skyyrose-brand-atmosphere',
					$js_uri . '/brand-atmosphere.js',
					array( 'skyyrose-performance-guardian' ),
					SKYYROSE_VERSION,
					array(
						'strategy'  => 'defer',
						'in_footer' => true,
					)
				);
			}
		}
	}
}

/**
 * Enqueue Phase 3 Experience Engine assets.
 *
 * Loads experience-analyzer, smart-showcase, and micro-interactions on any
 * page that renders product cards (collection, shop, search, front page, landing).
 * All three scripts depend on skyyrose-performance-guardian (Phase 2).
 */
function skyyrose_enqueue_phase3_assets(): void {
	if ( ! function_exists( 'skyyrose_see_is_module_active' ) ) {
		return;
	}

	$base_js_dir  = SKYYROSE_DIR . '/assets/js';
	$base_css_dir = SKYYROSE_DIR . '/assets/css';
	$js_uri       = SKYYROSE_ASSETS_URI . '/js';
	$css_uri      = SKYYROSE_ASSETS_URI . '/css';
	$use_min      = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;

	$product_slugs = array(
		'collection-standalone',
		'collection',
		'collection-v4',
		'collections-shop',
		'shop-archive',
		'search',
		'front-page',
		'landing',
		'preorder-gateway',
	);

	$slug = skyyrose_get_current_template_slug();
	if ( ! in_array( $slug, $product_slugs, true ) ) {
		return;
	}

	$phase2_dep = array( 'skyyrose-performance-guardian' );

	// ------------------------------------------------------------------
	// Experience Analyzer — behavioral tracking & event relay.
	// ------------------------------------------------------------------
	if ( skyyrose_see_is_module_active( 'experience_analyzer' ) ) {
		$ea_file = $use_min && file_exists( $base_js_dir . '/experience-analyzer.min.js' )
			? 'experience-analyzer.min.js' : 'experience-analyzer.js';
		if ( file_exists( $base_js_dir . '/' . $ea_file ) ) {
			wp_enqueue_script(
				'skyyrose-experience-analyzer',
				$js_uri . '/' . $ea_file,
				$phase2_dep,
				SKYYROSE_VERSION,
				array(
					'strategy'  => 'defer',
					'in_footer' => true,
				)
			);
		}
	}

	// ------------------------------------------------------------------
	// Smart Showcase — quick-view dialog + CSS.
	// ------------------------------------------------------------------
	if ( skyyrose_see_is_module_active( 'smart_showcase' ) ) {
		if ( file_exists( $base_css_dir . '/smart-showcase.css' ) ) {
			wp_enqueue_style(
				'skyyrose-smart-showcase',
				$css_uri . '/smart-showcase.css',
				array( 'skyyrose-design-tokens' ),
				SKYYROSE_VERSION
			);
		}

		$ss_file = $use_min && file_exists( $base_js_dir . '/smart-showcase.min.js' )
			? 'smart-showcase.min.js' : 'smart-showcase.js';
		if ( file_exists( $base_js_dir . '/' . $ss_file ) ) {
			wp_enqueue_script(
				'skyyrose-smart-showcase',
				$js_uri . '/' . $ss_file,
				$phase2_dep,
				SKYYROSE_VERSION,
				array(
					'strategy'  => 'defer',
					'in_footer' => true,
				)
			);
		}
	}

	// ------------------------------------------------------------------
	// Micro-Interactions — cart fly-to & wishlist burst.
	// ------------------------------------------------------------------
	if ( skyyrose_see_is_module_active( 'micro_interactions' ) ) {
		$mi_file = $use_min && file_exists( $base_js_dir . '/micro-interactions.min.js' )
			? 'micro-interactions.min.js' : 'micro-interactions.js';
		if ( file_exists( $base_js_dir . '/' . $mi_file ) ) {
			wp_enqueue_script(
				'skyyrose-micro-interactions',
				$js_uri . '/' . $mi_file,
				$phase2_dep,
				SKYYROSE_VERSION,
				array(
					'strategy'  => 'defer',
					'in_footer' => true,
				)
			);
		}
	}
}

/**
 * Enqueue Phase 4 Experience Engine assets — Personalization.
 *
 * Personalization.js + personalization.css load on pages that render product
 * grids or single products. Runs at priority 42 so personalization.php's
 * localize (priority 45) attaches to the already-registered handle.
 */
function skyyrose_enqueue_phase4_assets(): void {
	if ( ! function_exists( 'skyyrose_see_is_module_active' ) ) {
		return;
	}

	$product_slugs = array(
		'collection-standalone',
		'collection',
		'collection-v4',
		'collections-shop',
		'shop-archive',
		'search',
		'front-page',
		'landing',
		'preorder-gateway',
		'single-product',
	);

	if ( ! in_array( skyyrose_get_current_template_slug(), $product_slugs, true ) ) {
		return;
	}

	if ( ! skyyrose_see_is_module_active( 'personalization' ) ) {
		return;
	}

	$base_js_dir  = SKYYROSE_DIR . '/assets/js';
	$base_css_dir = SKYYROSE_DIR . '/assets/css';
	$js_uri       = SKYYROSE_ASSETS_URI . '/js';
	$css_uri      = SKYYROSE_ASSETS_URI . '/css';

	if ( file_exists( $base_css_dir . '/personalization.css' ) ) {
		wp_enqueue_style(
			'skyyrose-personalization',
			$css_uri . '/personalization.css',
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	if ( file_exists( $base_js_dir . '/personalization.js' ) ) {
		wp_enqueue_script(
			'skyyrose-personalization',
			$js_uri . '/personalization.js',
			array(),
			SKYYROSE_VERSION,
			array(
				'strategy'  => 'defer',
				'in_footer' => true,
			)
		);
	}
}

/**
 * Enqueue commercial polish CSS as the LAST stylesheet.
 *
 * Runs at priority 25 — after template-specific styles (priority 20).
 * Ensures the commercial polish layer can refine typography, cards,
 * collection story-world overrides, and focus states with highest specificity.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_enqueue_commercial_polish() {
	$base_uri = SKYYROSE_ASSETS_URI . '/css';
	$base_dir = SKYYROSE_DIR . '/assets/css';
	$use_min  = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;

	$polish_file = $use_min && file_exists( $base_dir . '/commercial-polish.min.css' )
		? 'commercial-polish.min.css' : 'commercial-polish.css';

	if ( file_exists( $base_dir . '/' . $polish_file ) ) {
		wp_enqueue_style(
			'skyyrose-commercial-polish',
			$base_uri . '/' . $polish_file,
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}
}

add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_commercial_polish', 25 );
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_phase2_assets', 30 );
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_phase3_assets', 40 );
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_phase4_assets', 42 );
