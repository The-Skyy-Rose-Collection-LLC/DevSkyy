<?php
/**
 * Personalization Engine — Affinity scoring, Curated For You section.
 *
 * Tracks collection affinity via localStorage, renders "Curated For You"
 * product section, recognizes returning visitors. When FastAPI backend is
 * available, upgrades to ML-powered recommendations.
 *
 * Extends the theme's adaptive-personalization.js BehaviorTracker pattern.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SEE_Personalization {

	private SEE_Plugin $plugin;

	public function __construct( SEE_Plugin $plugin ) {
		$this->plugin = $plugin;
	}

	public function register( SEE_Loader $loader ): void {
		$loader->add_action( 'wp_enqueue_scripts', $this, 'enqueue_assets', 55 );
	}

	public function enqueue_assets(): void {
		if ( is_admin() ) {
			return;
		}

		wp_enqueue_style(
			'see-personalization',
			SEE_URI . 'public/css/see-personalization.css',
			array(),
			SEE_VERSION
		);

		wp_enqueue_script(
			'see-personalization',
			SEE_URI . 'public/js/see-personalization.js',
			array( 'see-core' ),
			SEE_VERSION,
			true
		);
	}
}
