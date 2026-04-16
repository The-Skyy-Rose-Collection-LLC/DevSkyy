<?php
/**
 * Performance Guardian — Phase 2
 *
 * Injects CLS-prevention inline CSS and localizes the animation budget config
 * for the JS FPS watchdog. Operates only when the 'performance_guardian' module
 * is active in the Experience Engine registry.
 *
 * @package SkyyRose_Flagship
 * @since   6.4.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Inject CLS-prevention inline CSS for known dynamic content regions.
 *
 * Attaches to the always-loaded skyyrose-design-tokens handle so it ships
 * in a single HTTP request. Uses CSS `contain` to prevent reflow propagation
 * from async-loaded product grids and atmosphere canvas.
 */
function skyyrose_pg_inject_cls_prevention(): void {
	if ( ! function_exists( 'skyyrose_see_is_module_active' ) ) {
		return;
	}
	if ( ! skyyrose_see_is_module_active( 'performance_guardian' ) ) {
		return;
	}

	$css = '
		/* Performance Guardian — CLS Prevention */
		.product-grid__items,
		.br-product-grid__items,
		.col-product-grid {
			contain: layout style;
		}
		.product-card-holo {
			min-height: 380px;
			contain: content;
		}
		.skyy-hero,
		.col-hero,
		.lp-hero {
			min-height: 60vh;
			contain: layout;
		}
		.skyy-atmosphere-canvas {
			contain: strict;
		}

		/* Throttle non-critical animations when FPS drops below threshold */
		.skyy-motion-reduced .magnetic,
		.skyy-motion-reduced .btn-sweep,
		.skyy-motion-reduced .btn-border-draw {
			transition: none !important;
		}
		.skyy-motion-reduced .rv-clip-left,
		.skyy-motion-reduced .rv-clip-right,
		.skyy-motion-reduced .rv-blur-in,
		.skyy-motion-reduced .rv-split-word,
		.skyy-motion-reduced .col-reveal,
		.skyy-motion-reduced .lp-rv {
			opacity: 1 !important;
			transform: none !important;
			clip-path: none !important;
		}

		/* OS-level reduced motion: disable all non-essential animation */
		@media (prefers-reduced-motion: reduce) {
			.skyy-atmosphere-canvas { display: none !important; }
			.magnetic,
			.btn-sweep,
			.btn-border-draw,
			.rv-clip-left,
			.rv-clip-right,
			.rv-blur-in,
			.rv-split-word,
			.col-reveal,
			.lp-rv {
				transition: none !important;
				animation: none !important;
				opacity: 1 !important;
				transform: none !important;
				clip-path: none !important;
			}
		}
	';

	wp_add_inline_style( 'skyyrose-design-tokens', $css );
}
add_action( 'wp_enqueue_scripts', 'skyyrose_pg_inject_cls_prevention', 20 );

/**
 * Localize the animation budget config for the JS FPS watchdog.
 *
 * Attaches to the skyyrose-performance-guardian script handle (registered in
 * enqueue.php). The watchdog reads window.SkyyPerformanceBudget on init.
 */
function skyyrose_pg_localize_budget(): void {
	if ( ! function_exists( 'skyyrose_see_is_module_active' ) ) {
		return;
	}
	if ( ! skyyrose_see_is_module_active( 'performance_guardian' ) ) {
		return;
	}

	wp_localize_script(
		'skyyrose-performance-guardian',
		'SkyyPerformanceBudget',
		array(
			'fpsThreshold'       => 30,
			'maxConcurrentAnims' => 8,
			'checkInterval'      => 2000,
			'throttleDuration'   => 5000,
			'debug'              => defined( 'WP_DEBUG' ) && WP_DEBUG,
		)
	);
}
add_action( 'wp_enqueue_scripts', 'skyyrose_pg_localize_budget', 35 );
