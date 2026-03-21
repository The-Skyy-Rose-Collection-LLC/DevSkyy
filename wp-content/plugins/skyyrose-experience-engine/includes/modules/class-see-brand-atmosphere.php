<?php
/**
 * Brand Atmosphere — Ambient particles, cursor glow, cinematic mode.
 *
 * Creates an emotional connection no competitor achieves through subtle
 * ambient effects: collection-specific particles (rose petals, ember sparks,
 * gold dust), custom cursor glow, and a cinematic mode toggle.
 *
 * Defaults to disabled in standalone mode, auto-enables with flagship theme.
 * All effects auto-pause when Performance Guardian signals budget exceeded.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SEE_Brand_Atmosphere {

	private SEE_Plugin $plugin;

	public function __construct( SEE_Plugin $plugin ) {
		$this->plugin = $plugin;
	}

	public function register( SEE_Loader $loader ): void {
		$loader->add_action( 'wp_enqueue_scripts', $this, 'enqueue_assets', 57 );
		$loader->add_action( 'wp_footer', $this, 'render_atmosphere_canvas', 20 );
	}

	public function enqueue_assets(): void {
		if ( is_admin() ) {
			return;
		}

		wp_enqueue_style(
			'see-brand-atmosphere',
			SEE_URI . 'public/css/see-brand-atmosphere.css',
			array(),
			SEE_VERSION
		);

		wp_enqueue_script(
			'see-brand-atmosphere',
			SEE_URI . 'public/js/see-brand-atmosphere.js',
			array( 'see-core' ),
			SEE_VERSION,
			true
		);
	}

	/**
	 * Render the particle canvas overlay and cinematic mode toggle.
	 */
	public function render_atmosphere_canvas(): void {
		if ( is_admin() ) {
			return;
		}
		?>
		<canvas id="see-atmosphere-canvas" class="see-atmosphere-canvas" aria-hidden="true"></canvas>
		<button id="see-cinematic-toggle" class="see-cinematic-toggle" aria-label="Toggle cinematic mode" title="Cinematic Mode">
			<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<rect x="2" y="2" width="20" height="20" rx="2" />
				<line x1="7" y1="2" x2="7" y2="22" />
				<line x1="17" y1="2" x2="17" y2="22" />
				<line x1="2" y1="12" x2="22" y2="12" />
			</svg>
		</button>
		<?php
	}
}
