<?php
/**
 * Landing Page — FAQ Accordion
 *
 * Accordion-style FAQ section. JS in landing-pages.js handles toggle.
 *
 * Expected $args:
 *   'heading'   => string  Section heading ("Frequently Asked")
 *   'questions' => array   Array of ['q' => question, 'a' => answer]
 *
 * @package SkyyRose_Flagship
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

$heading   = $args['heading'] ?? 'Frequently Asked';
$questions = $args['questions'] ?? array();

if ( empty( $questions ) ) {
	return;
}
?>

<section class="lp-faq" id="faq">
	<div class="lp__container">
		<div class="lp-faq__header lp-rv">
			<h2><?php echo esc_html( $heading ); ?></h2>
		</div>

		<div class="lp-faq__list">
			<?php foreach ( $questions as $i => $item ) : ?>
				<div class="lp-faq__item lp-rv" data-delay="<?php echo esc_attr( min( $i + 1, 5 ) ); ?>">
					<button class="lp-faq__question" type="button"
							aria-expanded="false"
							aria-controls="lp-faq-a-<?php echo esc_attr( $i ); ?>">
						<span><?php echo esc_html( $item['q'] ); ?></span>
						<svg class="lp-faq__icon" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" aria-hidden="true">
							<line x1="12" y1="5" x2="12" y2="19"></line>
							<line x1="5" y1="12" x2="19" y2="12"></line>
						</svg>
					</button>
					<div class="lp-faq__answer" id="lp-faq-a-<?php echo esc_attr( $i ); ?>" role="region">
						<div class="lp-faq__answer-inner">
							<?php echo wp_kses_post( $item['a'] ); ?>
						</div>
					</div>
				</div>
			<?php endforeach; ?>
		</div>
	</div>
</section>
