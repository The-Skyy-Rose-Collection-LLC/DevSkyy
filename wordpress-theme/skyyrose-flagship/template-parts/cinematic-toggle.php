<?php
/**
 * Cinematic Mode Toggle — Reusable Template Partial
 *
 * Renders the cinematic toggle button and vignette overlay.
 * Include via get_template_part( 'template-parts/cinematic-toggle' )
 * on immersive pages, pre-order gateway, and single product.
 *
 * @package SkyyRose_Flagship
 * @since   3.1.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
?>

<!-- Cinematic Mode Toggle -->
<button class="cinematic-toggle" aria-label="<?php esc_attr_e( 'Toggle Cinematic Mode', 'skyyrose-flagship' ); ?>" aria-pressed="false" type="button">
	<span class="cinematic-toggle__icon" aria-hidden="true">
		<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
			<path d="M4 11v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>
			<path d="M4 11l2-6h12l2 6"/>
			<path d="M8 5l-1 6"/>
			<path d="M16 5l1 6"/>
			<path d="M12 5v6"/>
			<circle cx="12" cy="16" r="2"/>
		</svg>
	</span>
	<span class="cinematic-toggle__text"><?php esc_html_e( 'Cinematic Mode', 'skyyrose-flagship' ); ?></span>
</button>
<div class="cinematic-vignette" aria-hidden="true"></div>
