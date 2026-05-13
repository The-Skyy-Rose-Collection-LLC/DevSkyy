<?php
/**
 * Scroll Storyteller — Apple-style scroll-driven product reveals.
 *
 * Products tell their story as users scroll: craftsmanship → materials →
 * details → price → CTA. Uses IntersectionObserver with progressive disclosure.
 * Something NO luxury competitor does on product pages.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SEE_Scroll_Storyteller {

	private SEE_Plugin $plugin;

	public function __construct( SEE_Plugin $plugin ) {
		$this->plugin = $plugin;
	}

	public function register( SEE_Loader $loader ): void {
		$loader->add_action( 'wp_enqueue_scripts', $this, 'enqueue_assets', 53 );
	}

	public function enqueue_assets(): void {
		if ( is_admin() ) {
			return;
		}

		wp_enqueue_style(
			'see-scroll-storyteller',
			SEE_URI . 'public/css/see-scroll-storyteller.css',
			array(),
			SEE_VERSION
		);

		wp_enqueue_script(
			'see-scroll-storyteller',
			SEE_URI . 'public/js/see-scroll-storyteller.js',
			array( 'see-core' ),
			SEE_VERSION,
			true
		);
	}
}
