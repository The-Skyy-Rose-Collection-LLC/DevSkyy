<?php
/**
 * Template Part: Interactive Brand Mascot — Skyy
 *
 * Skyy walks cinematically onto the screen from the bottom-right, speaks
 * through contextual speech bubbles with choice chips, and guides visitors
 * through contextual paths. No panel, no chatbox — just Skyy talking.
 *
 * Usage: get_template_part( 'template-parts/mascot' );
 * Loaded automatically via functions.php wp_footer hook.
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
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

// Image selection:
// - Collection pages get outfit-specific PNGs (black-rose, love-hurts, signature, kids-capsule).
// - All other contexts use the canonical pointing/red-tee pose.
// - Fallback chain: pointing.png → reference.png → mascot-fallback.svg
$skyyrose_mascot_dir         = SKYYROSE_DIR . '/assets/images/mascot/';
$skyyrose_mascot_uri         = SKYYROSE_ASSETS_URI . '/images/mascot/';
$skyyrose_mascot_img         = $skyyrose_mascot_uri . 'mascot-fallback.svg';
$skyyrose_collection_ctxs    = array( 'black-rose', 'love-hurts', 'signature', 'kids-capsule' );

if ( in_array( $skyyrose_mascot_context, $skyyrose_collection_ctxs, true ) ) {
	// Try collection-specific PNG first.
	$skyyrose_context_file = 'skyyrose-mascot-' . $skyyrose_mascot_context . '.png';
	if ( file_exists( $skyyrose_mascot_dir . $skyyrose_context_file ) ) {
		$skyyrose_mascot_img = $skyyrose_mascot_uri . $skyyrose_context_file;
	} elseif ( file_exists( $skyyrose_mascot_dir . 'skyyrose-mascot-pointing.png' ) ) {
		$skyyrose_mascot_img = $skyyrose_mascot_uri . 'skyyrose-mascot-pointing.png';
	} elseif ( file_exists( $skyyrose_mascot_dir . 'skyyrose-mascot-reference.png' ) ) {
		$skyyrose_mascot_img = $skyyrose_mascot_uri . 'skyyrose-mascot-reference.png';
	}
} else {
	// Default: canonical pointing pose.
	if ( file_exists( $skyyrose_mascot_dir . 'skyyrose-mascot-pointing.png' ) ) {
		$skyyrose_mascot_img = $skyyrose_mascot_uri . 'skyyrose-mascot-pointing.png';
	} elseif ( file_exists( $skyyrose_mascot_dir . 'skyyrose-mascot-reference.png' ) ) {
		$skyyrose_mascot_img = $skyyrose_mascot_uri . 'skyyrose-mascot-reference.png';
	}
}
?>

<!-- Skyy — Living Brand Mascot -->
<div
	id="skyyrose-mascot"
	class="skyyrose-mascot"
	role="complementary"
	aria-label="<?php esc_attr_e( 'Skyy \xe2\x80\x94 SkyyRose Brand Ambassador', 'skyyrose-flagship' ); ?>"
	data-context="<?php echo esc_attr( $skyyrose_mascot_context ); ?>"
	aria-hidden="true"
>
	<!-- Speech Bubble (rendered left of character via flex row-reverse) -->
	<div class="skyy-bubble" id="skyy-bubble" aria-live="polite" role="status" hidden>
		<p class="skyy-bubble__text" id="skyy-bubble-text"></p>
		<div
			class="skyy-chips"
			id="skyy-chips"
			role="group"
			aria-label="<?php esc_attr_e( 'Reply options', 'skyyrose-flagship' ); ?>"
		></div>
	</div>

	<!-- Character — clicking replays greeting or dismisses bubble -->
	<button
		type="button"
		class="skyyrose-mascot__character"
		id="skyyrose-mascot-trigger"
		aria-label="<?php esc_attr_e( 'Talk to Skyy', 'skyyrose-flagship' ); ?>"
		aria-expanded="false"
	>
		<img
			src="<?php echo esc_url( $skyyrose_mascot_img ); ?>"
			alt="<?php esc_attr_e( 'Skyy, SkyyRose brand ambassador', 'skyyrose-flagship' ); ?>"
			class="skyyrose-mascot__image"
			width="220"
			height="auto"
			loading="eager"
			decoding="async"
		/>
	</button>

	<!-- Minimize — tiny × in top-right corner of character -->
	<button
		type="button"
		class="skyyrose-mascot__minimize"
		id="skyyrose-mascot-minimize"
		aria-label="<?php esc_attr_e( 'Dismiss Skyy', 'skyyrose-flagship' ); ?>"
	>&times;</button>
</div>

<!-- Recall Pill — shown at bottom-right when Skyy is minimized -->
<button
	type="button"
	class="skyyrose-mascot__recall"
	id="skyyrose-mascot-recall"
	aria-label="<?php esc_attr_e( 'Bring back Skyy', 'skyyrose-flagship' ); ?>"
	style="display:none"
>
	<img
		src="<?php echo esc_url( $skyyrose_mascot_img ); ?>"
		width="32"
		height="32"
		alt=""
		aria-hidden="true"
		loading="lazy"
		decoding="async"
	/>
	<span><?php esc_html_e( 'Skyy', 'skyyrose-flagship' ); ?></span>
</button>
