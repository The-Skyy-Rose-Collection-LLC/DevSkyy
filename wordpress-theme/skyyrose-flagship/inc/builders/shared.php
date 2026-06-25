<?php
/**
 * Shared Builder-Integration Scaffold
 *
 * Each builder file (divi, beaver-builder, bricks, elementor) calls
 * `skyyrose_register_builder_compat( $slug, $config )` to wire up theme
 * support, palette injection, and any post-setup callbacks.
 *
 * Builder detection lives in `inc/builders/detection.php` and is NOT
 * invoked here — each builder file self-guards against its plugin's
 * absence before reaching this helper.
 *
 * @package SkyyRose
 * @since   1.1.0
 */

defined( 'ABSPATH' ) || exit;

/**
 * Register a builder integration: theme support + palette injection + optional setup.
 *
 * The palette callback receives `skyyrose_brand_colors()` as its first argument,
 * followed by whatever args the hook passes (filters get the existing value,
 * actions may pass none). The callback returns the new value for filters or
 * side-effects for actions — same shape as a normal hook callback after the
 * brand-colors prefix.
 *
 * @since 1.1.0
 *
 * @param string $slug   Builder identifier ('divi'|'beaver-builder'|'bricks'|'elementor').
 * @param array  $config  {
 *     Configuration array for the builder integration.
 *
 *     @type callable $theme_support     Optional. Callback fired on after_setup_theme.
 *     @type string   $palette_hook      Optional. Hook name for palette injection.
 *     @type callable $palette_callback  Optional. Receives skyyrose_brand_colors() + hook args.
 *     @type int      $palette_priority  Optional. add_action priority. Default 10.
 *     @type callable $post_setup        Optional. Synchronous callback executed immediately.
 * }
 * @return void
 */
function skyyrose_register_builder_compat( string $slug, array $config ): void {
	if ( ! empty( $config['theme_support'] ) && is_callable( $config['theme_support'] ) ) {
		add_action( 'after_setup_theme', $config['theme_support'] );
	}

	if (
		! empty( $config['palette_hook'] )
		&& ! empty( $config['palette_callback'] )
		&& is_callable( $config['palette_callback'] )
	) {
		$priority = isset( $config['palette_priority'] ) ? (int) $config['palette_priority'] : 10;
		add_action(
			$config['palette_hook'],
			static function ( ...$hook_args ) use ( $config ) {
				return call_user_func( $config['palette_callback'], skyyrose_brand_colors(), ...$hook_args );
			},
			$priority,
			10
		);
	}

	if ( ! empty( $config['post_setup'] ) && is_callable( $config['post_setup'] ) ) {
		$config['post_setup']();
	}

	unset( $slug ); // Reserved for future audit/logging hook.
}
