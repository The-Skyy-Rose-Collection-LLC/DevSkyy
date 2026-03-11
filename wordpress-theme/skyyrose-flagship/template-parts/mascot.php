<?php
/**
 * Template Part: Interactive Brand Mascot Widget
 *
 * The SkyyRose brand mascot walks onto the screen from the right side,
 * stands in the bottom-right corner, and acts as an interactive brand
 * ambassador. She wears collection-specific outfits based on the current page.
 *
 * Usage: get_template_part( 'template-parts/mascot' );
 * Loaded automatically via functions.php wp_footer hook.
 *
 * @package SkyyRose_Flagship
 * @since   3.2.0
 */

defined( 'ABSPATH' ) || exit;

// Determine current collection context for outfit switching.
$skyyrose_mascot_context = 'default';
$skyyrose_template_file  = get_page_template_slug();

if ( is_front_page() ) {
	$skyyrose_mascot_context = 'homepage';
} elseif ( strpos( $skyyrose_template_file, 'black-rose' ) !== false ) {
	$skyyrose_mascot_context = 'black-rose';
} elseif ( strpos( $skyyrose_template_file, 'love-hurts' ) !== false ) {
	$skyyrose_mascot_context = 'love-hurts';
} elseif ( strpos( $skyyrose_template_file, 'signature' ) !== false ) {
	$skyyrose_mascot_context = 'signature';
} elseif ( strpos( $skyyrose_template_file, 'kids-capsule' ) !== false ) {
	$skyyrose_mascot_context = 'kids-capsule';
} elseif ( strpos( $skyyrose_template_file, 'preorder' ) !== false ) {
	$skyyrose_mascot_context = 'preorder';
} elseif ( is_404() ) {
	$skyyrose_mascot_context = '404';
}

// Mascot image paths — prefer collection-specific PNG, fallback to SVG.
$skyyrose_mascot_dir = SKYYROSE_DIR . '/assets/images/mascot/';
$skyyrose_mascot_uri = SKYYROSE_ASSETS_URI . '/images/mascot/';
$skyyrose_mascot_img = $skyyrose_mascot_uri . 'mascot-fallback.svg';

// Try context-specific PNG first, then reference PNG, then idle PNG, then SVG fallback.
$skyyrose_context_file = 'skyyrose-mascot-' . $skyyrose_mascot_context . '.png';
if ( file_exists( $skyyrose_mascot_dir . $skyyrose_context_file ) ) {
	$skyyrose_mascot_img = $skyyrose_mascot_uri . $skyyrose_context_file;
} elseif ( file_exists( $skyyrose_mascot_dir . 'skyyrose-mascot-reference.png' ) ) {
	$skyyrose_mascot_img = $skyyrose_mascot_uri . 'skyyrose-mascot-reference.png';
} elseif ( file_exists( $skyyrose_mascot_dir . 'skyy-idle.png' ) ) {
	$skyyrose_mascot_img = $skyyrose_mascot_uri . 'skyy-idle.png';
}
?>

<!-- Brand Mascot Widget -->
<div
	id="skyyrose-mascot"
	class="skyyrose-mascot"
	role="complementary"
	aria-label="<?php esc_attr_e( 'SkyyRose Brand Ambassador', 'skyyrose-flagship' ); ?>"
	data-context="<?php echo esc_attr( $skyyrose_mascot_context ); ?>"
	aria-hidden="true"
>
	<!-- Mascot Character -->
	<button
		type="button"
		class="skyyrose-mascot__character"
		id="skyyrose-mascot-trigger"
		aria-label="<?php esc_attr_e( 'Talk to our brand ambassador', 'skyyrose-flagship' ); ?>"
		aria-expanded="false"
		aria-controls="skyyrose-mascot-panel"
	>
		<img
			src="<?php echo esc_url( $skyyrose_mascot_img ); ?>"
			alt="<?php esc_attr_e( 'SkyyRose brand mascot', 'skyyrose-flagship' ); ?>"
			class="skyyrose-mascot__image"
			width="120"
			height="160"
			loading="lazy"
			decoding="async"
		/>
		<span class="skyyrose-mascot__greeting" aria-live="polite">
			<?php esc_html_e( 'Hey! Need help?', 'skyyrose-flagship' ); ?>
		</span>
	</button>

	<!-- Interaction Panel -->
	<div
		class="skyyrose-mascot__panel"
		id="skyyrose-mascot-panel"
		role="dialog"
		aria-modal="true"
		aria-label="<?php esc_attr_e( 'Brand Ambassador Panel', 'skyyrose-flagship' ); ?>"
		aria-hidden="true"
	>
		<div class="skyyrose-mascot__panel-header">
			<span class="skyyrose-mascot__panel-title">
				<?php esc_html_e( 'SkyyRose Guide', 'skyyrose-flagship' ); ?>
			</span>
			<button
				type="button"
				class="skyyrose-mascot__panel-close"
				aria-label="<?php esc_attr_e( 'Close panel', 'skyyrose-flagship' ); ?>"
			>
				&times;
			</button>
		</div>

		<div class="skyyrose-mascot__panel-body">
			<!-- Dynamic content based on page context -->
			<div class="skyyrose-mascot__actions">
				<a href="<?php echo esc_url( home_url( '/shop/' ) ); ?>" class="skyyrose-mascot__action">
					<span class="skyyrose-mascot__action-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg></span>
					<span><?php esc_html_e( 'Shop Collections', 'skyyrose-flagship' ); ?></span>
				</a>
				<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" class="skyyrose-mascot__action skyyrose-mascot__action--highlight">
					<span class="skyyrose-mascot__action-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg></span>
					<span><?php esc_html_e( 'Pre-Order Now', 'skyyrose-flagship' ); ?></span>
				</a>
				<a href="<?php echo esc_url( home_url( '/contact/' ) ); ?>" class="skyyrose-mascot__action">
					<span class="skyyrose-mascot__action-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg></span>
					<span><?php esc_html_e( 'Get Help', 'skyyrose-flagship' ); ?></span>
				</a>
				<a href="<?php echo esc_url( home_url( '/about/' ) ); ?>" class="skyyrose-mascot__action">
					<span class="skyyrose-mascot__action-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></span>
					<span><?php esc_html_e( 'Our Story', 'skyyrose-flagship' ); ?></span>
				</a>
			</div>
		</div>
	</div>

	<!-- Recall Button (when minimized) -->
	<button
		type="button"
		class="skyyrose-mascot__recall"
		id="skyyrose-mascot-recall"
		aria-label="<?php esc_attr_e( 'Bring back brand ambassador', 'skyyrose-flagship' ); ?>"
		aria-hidden="true"
		style="display: none;"
	>
		<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="8" r="4"/><path d="M20 21a8 8 0 1 0-16 0"/></svg>
	</button>

	<!-- Minimize Button -->
	<button
		type="button"
		class="skyyrose-mascot__minimize"
		id="skyyrose-mascot-minimize"
		aria-label="<?php esc_attr_e( 'Dismiss brand ambassador', 'skyyrose-flagship' ); ?>"
	>
		<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
	</button>
</div>
