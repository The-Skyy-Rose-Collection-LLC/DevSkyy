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

// Conversation context + walk-on side — shared resolution lives in
// inc/mascot-config.php so body_class, walkSide, and per-page tips all agree.
$skyy_context = skyyrose_get_skyy_context();
$skyy_side    = skyyrose_get_skyy_walk_side( $skyy_context );

// Recall pill: tiny avatar thumb for the minimised state.
$recall_thumb = $skyy_img_url ?: '';
?>

<?php if ( get_theme_mod( 'skyyrose_mascot_glb_url', '' ) ) : // skyy-3d.js is injected client-side by mascot-loader.js, never via wp_enqueue_script — gate the canvas on the same theme mod that gates the loader. ?>
<!-- Skyy 3D canvas — sits behind the speech bubble, driven by skyy-3d.js -->
<canvas
	id="skyy-3d-canvas"
	class="skyy-3d-canvas <?php echo 'left' === $skyy_side ? 'skyy-3d-canvas--left' : ''; ?>"
	width="220"
	height="340"
	aria-hidden="true"
	style="position:fixed;bottom:20px;z-index:9989;pointer-events:none;display:none;"
></canvas>
<?php endif; ?>

<!-- Skyy — Living Character Widget -->
<div
	id="skyyrose-mascot"
	class="skyyrose-mascot skyyrose-mascot--hidden"
	aria-hidden="true"
	aria-label="<?php esc_attr_e( 'Skyy, your SkyyRose style guide', 'skyyrose' ); ?>"
	data-context="<?php echo esc_attr( $skyy_context ); ?>"
	data-walk-side="<?php echo esc_attr( $skyy_side ); ?>"
	role="complementary"
>
	<!-- Speech bubble (rendered left of character via flex row-reverse) -->
	<div id="skyy-bubble" class="skyy-bubble" role="status" aria-live="polite" hidden>
		<p id="skyy-bubble-text" class="skyy-bubble__text"></p>
		<div id="skyy-chips" class="skyy-chips" role="group" aria-label="<?php esc_attr_e( 'Quick replies', 'skyyrose' ); ?>"></div>
		<button id="skyy-ask-trigger" class="skyy-ask-trigger" type="button" hidden>
			<?php esc_html_e( 'Ask a question', 'skyyrose' ); ?>
		</button>
	</div>

	<!-- Character button (click = open / dismiss bubble) -->
	<button
		id="skyyrose-mascot-trigger"
		class="skyyrose-mascot__character"
		type="button"
		aria-label="<?php esc_attr_e( 'Chat with Skyy', 'skyyrose' ); ?>"
		aria-expanded="false"
	>
		<?php if ( $skyy_img_url ) : ?>
			<img
				src="<?php echo esc_url( $skyy_img_url ); ?>"
				alt="<?php esc_attr_e( 'Skyy, SkyyRose brand mascot', 'skyyrose' ); ?>"
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

	</button>

	<!-- Minimize × button — must be OUTSIDE the trigger to avoid nested <button> (invalid HTML).
		Keyboard-reachable (no tabindex="-1"): ESC is a shortcut, not the only way to dismiss. -->
	<button
		id="skyyrose-mascot-minimize"
		class="skyyrose-mascot__minimize"
		type="button"
		aria-label="<?php esc_attr_e( 'Minimize Skyy', 'skyyrose' ); ?>"
	>&#215;</button>
</div><!-- #skyyrose-mascot -->

<!-- Ask Skyy — native <dialog> panel: focus trapped while open, ESC closes,
	focus restored to the trigger on close. Routine speech stays in the
	non-modal bubble above; this is the one deliberate, user-initiated
	"panel" interaction in the widget. -->
<dialog id="skyy-ask-dialog" class="skyy-ask-dialog" aria-labelledby="skyy-ask-dialog-title">
	<form id="skyy-ask-form" class="skyy-ask-form" method="dialog">
		<h2 id="skyy-ask-dialog-title" class="skyy-ask-dialog__title"><?php esc_html_e( 'Ask Skyy', 'skyyrose' ); ?></h2>
		<label class="skyy-ask-form__label" for="skyy-ask-input"><?php esc_html_e( 'Where to find something, sizing, shipping…', 'skyyrose' ); ?></label>
		<input
			type="text"
			id="skyy-ask-input"
			class="skyy-ask-form__input"
			autocomplete="off"
			placeholder="<?php esc_attr_e( 'Sizing, shipping, a collection…', 'skyyrose' ); ?>"
		/>
		<div class="skyy-ask-form__actions">
			<button type="button" id="skyy-ask-cancel" class="skyy-ask-form__cancel"><?php esc_html_e( 'Cancel', 'skyyrose' ); ?></button>
			<button type="submit" class="skyy-ask-form__submit"><?php esc_html_e( 'Ask', 'skyyrose' ); ?></button>
		</div>
	</form>
</dialog>

<!-- Recall pill — shown when minimised -->
<button
	id="skyyrose-mascot-recall"
	class="skyyrose-mascot__recall"
	type="button"
	style="display:none;"
	aria-hidden="true"
	aria-label="<?php esc_attr_e( 'Bring Skyy back', 'skyyrose' ); ?>"
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
	<span><?php esc_html_e( 'Skyy', 'skyyrose' ); ?></span>
</button>
