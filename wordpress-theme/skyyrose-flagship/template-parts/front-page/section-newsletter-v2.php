<?php
/**
 * Template Part: Newsletter Section (Homepage V2)
 *
 * @package SkyyRose_Flagship
 * @since   4.1.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
?>
<!-- ═══ NEWSLETTER ═══ -->
<section class="newsletter" id="community" aria-label="<?php esc_attr_e( 'Newsletter', 'skyyrose-flagship' ); ?>">
	<div class="nl-inner">
		<p class="nl-eyebrow rv"><?php esc_html_e( 'Join the Movement', 'skyyrose-flagship' ); ?></p>
		<h2 class="nl-title rv rv-d1"><?php esc_html_e( 'For The Real Ones', 'skyyrose-flagship' ); ?></h2>
		<p class="nl-desc rv rv-d2"><?php esc_html_e( 'Early access to drops. Behind-the-scenes from Oakland. Stories that matter. No spam, just substance.', 'skyyrose-flagship' ); ?></p>
		<div class="nl-form rv rv-d3">
			<input
				type="email"
				class="nl-input"
				placeholder="<?php esc_attr_e( 'Your email address', 'skyyrose-flagship' ); ?>"
				id="nlEmail"
				aria-label="<?php esc_attr_e( 'Email address', 'skyyrose-flagship' ); ?>"
				required
			/>
			<button type="button" class="nl-submit"><?php esc_html_e( 'Join', 'skyyrose-flagship' ); ?></button>
		</div>
		<p class="nl-note rv rv-d4"><?php echo esc_html( 'Free to join · Unsubscribe anytime · Oakland love only' ); ?></p>
	</div>
</section>
