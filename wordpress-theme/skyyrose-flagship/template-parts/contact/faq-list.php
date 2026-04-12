<?php
/**
 * Contact Page — FAQ Accordion Section
 *
 * Renders the FAQ accordion with accessible expand/collapse buttons.
 *
 * Expected variables (passed via $args from get_template_part):
 *   $args['faq_items'] — indexed array of arrays with 'question' and 'answer' keys.
 *
 * @package SkyyRose
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

$faq_items = isset( $args['faq_items'] ) ? $args['faq_items'] : array();

if ( empty( $faq_items ) ) {
	return;
}
?>

<section class="faq-section" aria-label="<?php esc_attr_e( 'Frequently Asked Questions', 'skyyrose' ); ?>">
	<div class="faq-section__container">
		<h2 class="faq-section__heading">
			<?php esc_html_e( 'Frequently Asked Questions', 'skyyrose' ); ?>
		</h2>
		<p class="faq-section__subheading">
			<?php esc_html_e( "Can't find what you're looking for? Send us a message above and we'll get back to you.", 'skyyrose' ); ?>
		</p>

		<div class="faq-accordion" role="list">
			<?php foreach ( $faq_items as $index => $faq ) : ?>
				<?php $faq_id = 'faq-answer-' . $index; ?>
				<div class="faq-item" role="listitem">
					<button
						class="faq-item__trigger"
						type="button"
						aria-expanded="false"
						aria-controls="<?php echo esc_attr( $faq_id ); ?>"
						id="faq-trigger-<?php echo esc_attr( $index ); ?>"
					>
						<span class="faq-item__question">
							<?php echo esc_html( $faq['question'] ); ?>
						</span>
						<span class="faq-item__icon" aria-hidden="true">
							<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
								<line x1="12" y1="5" x2="12" y2="19"/>
								<line x1="5" y1="12" x2="19" y2="12"/>
							</svg>
						</span>
					</button>
					<div
						class="faq-item__panel"
						id="<?php echo esc_attr( $faq_id ); ?>"
						role="region"
						aria-labelledby="faq-trigger-<?php echo esc_attr( $index ); ?>"
						hidden
					>
						<p class="faq-item__answer">
							<?php echo esc_html( $faq['answer'] ); ?>
						</p>
					</div>
				</div>
			<?php endforeach; ?>
		</div>
	</div>
</section>
