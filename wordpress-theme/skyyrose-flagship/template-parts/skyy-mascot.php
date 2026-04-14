<?php
/**
 * Skyy — Living Character Widget
 *
 * Injects the Skyy mascot DOM that mascot.min.js drives.
 * Outputs a fixed-position character + speech bubble + choice chips.
 *
 * JS state machine: dormant → walking-in → greeting → idle ↔ speaking → exiting
 *
 * @package SkyyRose_Flagship
 * @since   5.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

// Resolve the canonical character image — prefer new canonical, fall back gracefully.
$canonical_path = SKYYROSE_DIR . '/assets/images/mascot/skyy-canonical.jpeg';
$reference_path = SKYYROSE_DIR . '/assets/images/mascot/skyyrose-mascot-reference.png';

if ( file_exists( $canonical_path ) ) {
	$skyy_img_url = SKYYROSE_ASSETS_URI . '/images/mascot/skyy-canonical.jpeg';
} elseif ( file_exists( $reference_path ) ) {
	$skyy_img_url = SKYYROSE_ASSETS_URI . '/images/mascot/skyyrose-mascot-reference.png';
} else {
	// No image available — widget still renders so JS loads cleanly.
	$skyy_img_url = '';
}

// Determine conversation context from current page/template.
$skyy_context = 'default';
if ( is_front_page() ) {
	$skyy_context = 'homepage';
} elseif ( is_page( 'pre-order' ) || is_page( 'preorder' ) ) {
	$skyy_context = 'preorder';
} elseif ( is_404() ) {
	$skyy_context = '404';
} else {
	$slug = get_queried_object() ? get_post_field( 'post_name', get_queried_object_id() ) : '';
	if ( str_contains( $slug, 'black-rose' ) )  $skyy_context = 'black-rose';
	elseif ( str_contains( $slug, 'love-hurts' ) ) $skyy_context = 'love-hurts';
	elseif ( str_contains( $slug, 'signature' ) )  $skyy_context = 'signature';
}

// Recall pill: tiny avatar thumb for the minimised state.
$recall_thumb = $skyy_img_url ?: '';
?>

<!-- Skyy 3D canvas — sits behind the speech bubble, driven by skyy-3d.js -->
<canvas
	id="skyy-3d-canvas"
	class="skyy-3d-canvas"
	width="220"
	height="340"
	aria-hidden="true"
	style="position:fixed;bottom:20px;right:20px;z-index:9989;pointer-events:none;display:none;"
></canvas>

<!-- Skyy — Living Character Widget -->
<div
	id="skyyrose-mascot"
	class="skyyrose-mascot skyyrose-mascot--hidden"
	aria-hidden="true"
	aria-label="<?php esc_attr_e( 'Skyy, your SkyyRose style guide', 'skyyrose-flagship' ); ?>"
	data-context="<?php echo esc_attr( $skyy_context ); ?>"
	role="complementary"
>
	<!-- Speech bubble (rendered left of character via flex row-reverse) -->
	<div id="skyy-bubble" class="skyy-bubble" role="status" aria-live="polite" hidden>
		<p id="skyy-bubble-text" class="skyy-bubble__text"></p>
		<div id="skyy-chips" class="skyy-chips" role="group" aria-label="<?php esc_attr_e( 'Quick replies', 'skyyrose-flagship' ); ?>"></div>
	</div>

	<!-- Character button (click = open / dismiss bubble) -->
	<button
		id="skyyrose-mascot-trigger"
		class="skyyrose-mascot__character"
		type="button"
		aria-label="<?php esc_attr_e( 'Chat with Skyy', 'skyyrose-flagship' ); ?>"
		aria-expanded="false"
	>
		<?php if ( $skyy_img_url ) : ?>
			<img
				src="<?php echo esc_url( $skyy_img_url ); ?>"
				alt="<?php esc_attr_e( 'Skyy, SkyyRose brand mascot — young girl in Love Hurts varsity set', 'skyyrose-flagship' ); ?>"
				class="skyyrose-mascot__image"
				width="220"
				height="auto"
				loading="eager"
				decoding="async"
			/>
		<?php else : ?>
			<!-- Fallback when image not yet deployed -->
			<div class="skyyrose-mascot__image-placeholder" aria-hidden="true">
				<span style="font-size:2rem;">🌹</span>
			</div>
		<?php endif; ?>

		<!-- Minimize × button (appears on idle/speaking) -->
		<button
			id="skyyrose-mascot-minimize"
			class="skyyrose-mascot__minimize"
			type="button"
			aria-label="<?php esc_attr_e( 'Minimize Skyy', 'skyyrose-flagship' ); ?>"
			tabindex="-1"
		>&#215;</button>
	</button>
</div><!-- #skyyrose-mascot -->

<!-- Recall pill — shown when minimised -->
<button
	id="skyyrose-mascot-recall"
	class="skyyrose-mascot__recall"
	type="button"
	style="display:none;"
	aria-hidden="true"
	aria-label="<?php esc_attr_e( 'Bring Skyy back', 'skyyrose-flagship' ); ?>"
>
	<?php if ( $recall_thumb ) : ?>
		<img
			src="<?php echo esc_url( $recall_thumb ); ?>"
			alt=""
			aria-hidden="true"
			width="32"
			height="32"
		/>
	<?php else : ?>
		<span aria-hidden="true" style="width:32px;height:32px;display:inline-flex;align-items:center;justify-content:center;font-size:1.2rem;">🌹</span>
	<?php endif; ?>
	<span><?php esc_html_e( 'Skyy', 'skyyrose-flagship' ); ?></span>
</button>
