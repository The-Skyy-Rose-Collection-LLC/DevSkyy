<?php
/**
 * Collection — Founder pull quote (Corey Foster, BR)
 *
 * Editorial pull quote anchored to the brand-DNA founder origin story.
 * Surfaces user-visible founder voice on the Black Rose collection page.
 *
 * Set apart with hairline rules above and below (no boxes, no shadows).
 * Cinzel italic at fluid clamp(28px, 4vw, 44px). Reduced-motion safe via
 * the unified .col-reveal observer in premium-interactions.js.
 *
 * Conditional include from template-parts/collection/page.php; expected
 * to receive no $args — slug-gating happens at the call site.
 *
 * @package SkyyRose
 * @since   1.5.4
 */

defined( 'ABSPATH' ) || exit;
?>
<section class="col-founder-quote col-reveal" role="region" aria-label="<?php esc_attr_e( 'Founder note from Corey Foster', 'skyyrose' ); ?>">
	<div class="col-founder-quote__inner">
		<blockquote class="col-founder-quote__text">
			<?php
			// Verbatim from brand-DNA — preserved exactly so future audits can match.
			esc_html_e(
				'If you asked me four years ago, I never would have thought I\'d be here. I had no drive, lost it all, a baby on the way, and was broke. But we knew we had to get it by any means necessary.',
				'skyyrose'
			);
			?>
		</blockquote>
		<cite class="col-founder-quote__attr">
			<span class="col-founder-quote__name"><?php esc_html_e( 'Corey Foster', 'skyyrose' ); ?></span>
			<span class="col-founder-quote__role"><?php esc_html_e( 'Founder · Oakland', 'skyyrose' ); ?></span>
		</cite>
	</div>
</section>
