<?php
/**
 * Smart Showcase — Interactive product cards with 3D effects.
 *
 * Adds 3D perspective tilt, quick-view dialog, hover zoom, and
 * collection-aware accent colors to product cards.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SEE_Smart_Showcase {

	private SEE_Plugin $plugin;

	public function __construct( SEE_Plugin $plugin ) {
		$this->plugin = $plugin;
	}

	public function register( SEE_Loader $loader ): void {
		$loader->add_action( 'wp_enqueue_scripts', $this, 'enqueue_assets', 54 );
		$loader->add_action( 'wp_footer', $this, 'render_quick_view_dialog', 30 );
	}

	public function enqueue_assets(): void {
		if ( is_admin() ) {
			return;
		}

		wp_enqueue_style(
			'see-smart-showcase',
			SEE_URI . 'public/css/see-smart-showcase.css',
			array(),
			SEE_VERSION
		);

		wp_enqueue_script(
			'see-smart-showcase',
			SEE_URI . 'public/js/see-smart-showcase.js',
			array( 'see-core' ),
			SEE_VERSION,
			true
		);
	}

	/**
	 * Render the quick-view dialog shell (populated by JS).
	 */
	public function render_quick_view_dialog(): void {
		if ( is_admin() ) {
			return;
		}
		?>
		<dialog id="see-quick-view" class="see-quick-view-dialog" aria-label="Quick Product View">
			<div class="see-qv-content">
				<button class="see-qv-close" aria-label="Close">&times;</button>
				<div class="see-qv-image"></div>
				<div class="see-qv-details">
					<h3 class="see-qv-title"></h3>
					<p class="see-qv-price"></p>
					<p class="see-qv-description"></p>
					<a class="see-qv-link" href="#">View Full Product</a>
				</div>
			</div>
		</dialog>
		<?php
	}
}
