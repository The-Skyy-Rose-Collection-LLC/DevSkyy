<?php
/**
 * Collection — Founder pull quote (Corey Foster)
 *
 * Editorial pull quote anchored to the brand-DNA founder origin story.
 * Surfaces user-visible founder voice on a collection page (Black Rose,
 * Signature) whose register is the origin/heritage story.
 *
 * Quote + attribution are passed via $args (per-collection) and fall back to
 * the original Black Rose default so existing call sites render unchanged.
 * Set apart with hairline rules above and below (no boxes, no shadows).
 * Cinzel italic at fluid clamp(28px, 4vw, 44px). Reduced-motion safe via
 * the unified .col-reveal observer in premium-interactions.js.
 *
 * Conditional include from template-parts/collection/page.php; slug-gating
 * happens at the call site.
 *
 * @package SkyyRose
 * @since   1.5.4
 */

defined( 'ABSPATH' ) || exit;

// Per-collection quote via $args, with the original Black Rose default so a
// call with no $args (Black Rose) renders exactly as before.
$fq_text = ( isset( $args['quote_text'] ) && '' !== $args['quote_text'] )
	? (string) $args['quote_text']
	: __( 'If you asked me four years ago, I never would have thought I\'d be here. I had no drive, lost it all, a baby on the way, and was broke. But we knew we had to get it by any means necessary.', 'skyyrose' );
$fq_name = ( isset( $args['quote_name'] ) && '' !== $args['quote_name'] )
	? (string) $args['quote_name']
	: __( 'Corey Foster', 'skyyrose' );
$fq_role = ( isset( $args['quote_role'] ) && '' !== $args['quote_role'] )
	? (string) $args['quote_role']
	: __( 'Founder · Oakland', 'skyyrose' );
?>
<section class="col-founder-quote col-reveal" role="region" aria-label="<?php esc_attr_e( 'Founder note from Corey Foster', 'skyyrose' ); ?>">
	<div class="col-founder-quote__inner">
		<blockquote class="col-founder-quote__text"><?php echo esc_html( $fq_text ); ?></blockquote>
		<cite class="col-founder-quote__attr">
			<span class="col-founder-quote__name"><?php echo esc_html( $fq_name ); ?></span>
			<span class="col-founder-quote__role"><?php echo esc_html( $fq_role ); ?></span>
		</cite>
	</div>
</section>
