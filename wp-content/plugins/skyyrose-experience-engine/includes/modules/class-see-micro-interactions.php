<?php
/**
 * Micro-Interactions — Cart fly, wishlist burst, toasts, hover feedback.
 *
 * Research shows micro-interactions increase conversion rate by 20%.
 * All animations respect prefers-reduced-motion and the Performance
 * Guardian's animation budget.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SEE_Micro_Interactions {

	private SEE_Plugin $plugin;

	public function __construct( SEE_Plugin $plugin ) {
		$this->plugin = $plugin;
	}

	public function register( SEE_Loader $loader ): void {
		$loader->add_action( 'wp_enqueue_scripts', $this, 'enqueue_assets', 56 );
		$loader->add_action( 'wp_footer', $this, 'render_toast_container', 25 );
	}

	public function enqueue_assets(): void {
		if ( is_admin() ) {
			return;
		}

		wp_enqueue_style(
			'see-micro-interactions',
			SEE_URI . 'public/css/see-micro-interactions.css',
			array(),
			SEE_VERSION
		);

		wp_enqueue_script(
			'see-micro-interactions',
			SEE_URI . 'public/js/see-micro-interactions.js',
			array( 'see-core' ),
			SEE_VERSION,
			true
		);
	}

	/**
	 * Render the toast notification container.
	 */
	public function render_toast_container(): void {
		if ( is_admin() ) {
			return;
		}
		echo '<div id="see-toast-container" class="see-toast-container" aria-live="polite" aria-atomic="true"></div>';
	}
}
