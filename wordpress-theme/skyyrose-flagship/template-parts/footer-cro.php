<?php
/**
 * Template Part: Footer CRO Sections
 *
 * Reviews, value props, FAQ, and scarcity banner displayed site-wide
 * above the newsletter bar in the footer.
 *
 * @package SkyyRose_Flagship
 * @since   7.0.0
 */

defined( 'ABSPATH' ) || exit;
?>

<!-- Scarcity Banner -->
<div class="ft-cro-banner rv-clip-up">
	<p><?php esc_html_e( 'Limited Edition. Individually Numbered. Never Restocked.', 'skyyrose' ); ?></p>
</div>

<!-- Customer Reviews -->
<section class="ft-cro-reviews rv-clip-up" aria-label="<?php esc_attr_e( 'Customer reviews', 'skyyrose' ); ?>">
	<div class="ft-cro__container">
		<h2 class="ft-cro__heading"><?php esc_html_e( 'What Customers Say', 'skyyrose' ); ?></h2>
		<div class="ft-cro-reviews__grid">
			<?php
			$ft_reviews = array(
				array( "The quality is insane. I've washed my hoodie 20+ times and it still looks brand new.", 'Marcus T., Oakland' ),
				array( 'The numbered tag makes it feel truly exclusive. Exceeded expectations.', 'Jade W., San Francisco' ),
				array( "This isn't just a brand, it's a movement. The craftsmanship is unmatched.", 'Devon L., Los Angeles' ),
			);
			foreach ( $ft_reviews as $r ) :
				?>
				<div class="ft-cro-reviews__card">
					<div class="ft-cro-reviews__stars" aria-label="<?php esc_attr_e( '5 out of 5 stars', 'skyyrose' ); ?>">
						<?php for ( $s = 0; $s < 5; $s++ ) : ?>
							<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
						<?php endfor; ?>
					</div>
					<blockquote><p><?php echo esc_html( $r[0] ); ?></p></blockquote>
					<cite><?php echo esc_html( '— ' . $r[1] ); ?></cite>
				</div>
			<?php endforeach; ?>
		</div>
	</div>
</section>

<!-- Value Props -->
<section class="ft-cro-craft rv-clip-up" aria-label="<?php esc_attr_e( 'Why SkyyRose', 'skyyrose' ); ?>">
	<div class="ft-cro__container">
		<h2 class="ft-cro__heading"><?php esc_html_e( 'Why SkyyRose', 'skyyrose' ); ?></h2>
		<p class="ft-cro__subheading"><?php esc_html_e( 'Every dollar goes into the product. No influencer budgets. No middlemen. Just quality you can feel.', 'skyyrose' ); ?></p>
		<div class="ft-cro-craft__grid">
			<?php
			$ft_craft = array(
				array( '380gsm', '380gsm French Terry', 'Premium heavyweight fabric. Most brands use 220gsm. We use nearly double.' ),
				array( '#', 'Numbered Authentication', 'Every piece is hand-numbered. You know exactly which one is yours.' ),
				array( '//', 'Made-to-Order', 'We produce what is ordered. No waste, no overstock. Made for you.' ),
				array( '////', 'Double-Stitched Seams', 'Reinforced at every stress point. Built to last years, not seasons.' ),
			);
			foreach ( $ft_craft as $c ) :
				?>
				<div class="ft-cro-craft__card">
					<span class="ft-cro-craft__icon" aria-hidden="true"><?php echo esc_html( $c[0] ); ?></span>
					<h3><?php echo esc_html( $c[1] ); ?></h3>
					<p><?php echo esc_html( $c[2] ); ?></p>
				</div>
			<?php endforeach; ?>
		</div>
	</div>
</section>

<!-- FAQ -->
<section class="ft-cro-faq rv-clip-up" id="faq" aria-label="<?php esc_attr_e( 'Frequently asked questions', 'skyyrose' ); ?>">
	<div class="ft-cro__container">
		<h2 class="ft-cro__heading"><?php esc_html_e( 'Frequently Asked', 'skyyrose' ); ?></h2>
		<div class="ft-cro-faq__list">
			<?php
			$ft_faq = array(
				array( __( 'How does the sizing run?', 'skyyrose' ), __( 'True to size, S through 3XL. Check the size guide on any product page for exact measurements.', 'skyyrose' ) ),
				array( __( 'Is this really limited edition?', 'skyyrose' ), __( 'Yes. Every style is produced in a numbered run of 80-250 pieces. Once sold out, never restocked or reprinted.', 'skyyrose' ) ),
				array( __( 'When do pre-orders ship?', 'skyyrose' ), __( 'Pre-orders ship Spring 2026. You will receive tracking via email. We update timelines on our social channels.', 'skyyrose' ) ),
				array( __( 'What is your return policy?', 'skyyrose' ), __( '30-day return and exchange on unworn items. Contact us and we will make it right.', 'skyyrose' ) ),
				array( __( 'How does payment work for pre-orders?', 'skyyrose' ), __( 'Full payment at checkout to secure your numbered piece. Cancel any time before shipping for a full refund.', 'skyyrose' ) ),
				array( __( 'How long does shipping take?', 'skyyrose' ), __( 'Orders ship within 5-7 business days. You receive a tracking number via email.', 'skyyrose' ) ),
			);
			foreach ( $ft_faq as $i => $item ) :
				?>
				<div class="ft-cro-faq__item">
					<button class="ft-cro-faq__question" type="button"
							aria-expanded="false"
							aria-controls="ft-faq-a-<?php echo esc_attr( $i ); ?>">
						<span><?php echo esc_html( $item[0] ); ?></span>
						<svg class="ft-cro-faq__icon" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" aria-hidden="true">
							<line x1="12" y1="5" x2="12" y2="19"></line>
							<line x1="5" y1="12" x2="19" y2="12"></line>
						</svg>
					</button>
					<div class="ft-cro-faq__answer" id="ft-faq-a-<?php echo esc_attr( $i ); ?>" role="region">
						<div class="ft-cro-faq__answer-inner"><?php echo wp_kses_post( $item[1] ); ?></div>
					</div>
				</div>
			<?php endforeach; ?>
		</div>
	</div>
</section>
<?php // FAQ accordion behavior lives in assets/js/footer-cro.js (enqueued globally via inc/enqueue.php). ?>
