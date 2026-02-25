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

// Try context-specific PNG first, then reference PNG, then SVG fallback.
$skyyrose_context_file = 'skyyrose-mascot-' . $skyyrose_mascot_context . '.png';
if ( file_exists( $skyyrose_mascot_dir . $skyyrose_context_file ) ) {
	$skyyrose_mascot_img = $skyyrose_mascot_uri . $skyyrose_context_file;
} elseif ( file_exists( $skyyrose_mascot_dir . 'skyyrose-mascot-reference.png' ) ) {
	$skyyrose_mascot_img = $skyyrose_mascot_uri . 'skyyrose-mascot-reference.png';
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
		aria-label="<?php esc_attr_e( 'Brand Ambassador Panel', 'skyyrose-flagship' ); ?>"
		aria-hidden="true"
	>
		<div class="skyyrose-mascot__panel-header">
			<span class="skyyrose-mascot__panel-title">
				<?php esc_html_e( 'SkyyRose Guide', 'skyyrose-flagship' ); ?>
			</span>
			<button
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
					<span class="skyyrose-mascot__action-icon">&#x1f6cd;</span>
					<span><?php esc_html_e( 'Shop Collections', 'skyyrose-flagship' ); ?></span>
				</a>
				<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" class="skyyrose-mascot__action skyyrose-mascot__action--highlight">
					<span class="skyyrose-mascot__action-icon">&#x2728;</span>
					<span><?php esc_html_e( 'Pre-Order Now', 'skyyrose-flagship' ); ?></span>
				</a>
				<a href="<?php echo esc_url( home_url( '/contact/' ) ); ?>" class="skyyrose-mascot__action">
					<span class="skyyrose-mascot__action-icon">&#x1f4ac;</span>
					<span><?php esc_html_e( 'Get Help', 'skyyrose-flagship' ); ?></span>
				</a>
				<a href="<?php echo esc_url( home_url( '/about/' ) ); ?>" class="skyyrose-mascot__action">
					<span class="skyyrose-mascot__action-icon">&#x1f48e;</span>
					<span><?php esc_html_e( 'Our Story', 'skyyrose-flagship' ); ?></span>
				</a>
			</div>
		</div>
	</div>

	<!-- Recall Button (when minimized) -->
	<button
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
		class="skyyrose-mascot__minimize"
		id="skyyrose-mascot-minimize"
		aria-label="<?php esc_attr_e( 'Dismiss brand ambassador', 'skyyrose-flagship' ); ?>"
	>
		<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
	</button>
</div>
