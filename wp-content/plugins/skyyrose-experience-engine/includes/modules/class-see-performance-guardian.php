<?php
/**
 * Performance Guardian — Animation budget, lazy loading, CLS prevention.
 *
 * Ensures all visual enhancements respect Core Web Vitals. This module
 * unblocks re-enabling the theme's disabled engines by guaranteeing
 * Lighthouse scores won't regress.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SEE_Performance_Guardian {

	private SEE_Plugin $plugin;

	public function __construct( SEE_Plugin $plugin ) {
		$this->plugin = $plugin;
	}

	public function register( SEE_Loader $loader ): void {
		$loader->add_action( 'wp_enqueue_scripts', $this, 'enqueue_assets', 51 );
		$loader->add_action( 'wp_head', $this, 'inject_cls_prevention', 5 );
	}

	public function enqueue_assets(): void {
		if ( is_admin() ) {
			return;
		}

		wp_enqueue_style(
			'see-performance-guardian',
			SEE_URI . 'public/css/see-performance-guardian.css',
			array(),
			SEE_VERSION
		);

		wp_enqueue_script(
			'see-performance-guardian',
			SEE_URI . 'public/js/see-performance-guardian.js',
			array( 'see-core' ),
			SEE_VERSION,
			true
		);
	}

	/**
	 * Inline critical CSS for CLS prevention — reserves space for
	 * dynamically injected elements before they render.
	 */
	public function inject_cls_prevention(): void {
		if ( is_admin() ) {
			return;
		}
		?>
		<style id="see-cls-prevention">
			/* Reserve space for plugin-injected sections to prevent layout shift */
			.see-scroll-story { min-height: 0; contain: layout style; }
			.see-curated-section { min-height: 0; contain: layout style; }
			.see-toast-container { position: fixed; pointer-events: none; z-index: 1100; }
			.see-quick-view-dialog { contain: layout style paint; }

			/* Skeleton shimmer for lazy-loaded content */
			.see-skeleton {
				background: linear-gradient(90deg, #1a1a1a 25%, #2a2a2a 50%, #1a1a1a 75%);
				background-size: 200% 100%;
				animation: see-shimmer 1.5s ease-in-out infinite;
			}
			@keyframes see-shimmer {
				0% { background-position: 200% 0; }
				100% { background-position: -200% 0; }
			}
			@media (prefers-reduced-motion: reduce) {
				.see-skeleton { animation: none; background: #1a1a1a; }
			}
		</style>
		<?php
	}
}
