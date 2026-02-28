<?php
/**
 * Template Name: Style DNA Quiz
 *
 * Interactive personality quiz that maps aesthetic preferences to SkyyRose
 * collections. Generates a "Style DNA" profile with percentage breakdown
 * and a canvas-rendered shareable card.
 *
 * 7 visual questions → score accumulation → DNA reveal with product recs.
 *
 * @package SkyyRose_Flagship
 * @since   3.10.0
 */

defined( 'ABSPATH' ) || exit;

get_header();

// Grab products for recommendations.
$skyyrose_quiz_products = array();
if ( function_exists( 'skyyrose_get_collection_products' ) ) {
	foreach ( array( 'signature', 'black-rose', 'love-hurts' ) as $col ) {
		$items = skyyrose_get_collection_products( $col );
		foreach ( $items as $p ) {
			if ( ! empty( $p['published'] ) ) {
				$skyyrose_quiz_products[] = array(
					'sku'        => $p['sku'],
					'name'       => $p['name'],
					'collection' => $col,
					'price'      => skyyrose_format_price( $p ),
					'image'      => skyyrose_product_image_uri( ! empty( $p['front_model_image'] ) ? $p['front_model_image'] : $p['image'] ),
					'url'        => skyyrose_product_url( $p['sku'] ),
				);
			}
		}
	}
}
?>

<main id="primary" class="site-main" role="main" tabindex="-1">
<div class="style-quiz" data-products="<?php echo esc_attr( wp_json_encode( $skyyrose_quiz_products ) ); ?>">

	<!-- ====== Intro Screen ====== -->
	<section class="quiz-intro quiz-screen active" id="quiz-intro" aria-label="<?php esc_attr_e( 'Style DNA Quiz introduction', 'skyyrose-flagship' ); ?>">
		<div class="quiz-intro__content">
			<span class="quiz-intro__eyebrow"><?php esc_html_e( 'Discover Your', 'skyyrose-flagship' ); ?></span>
			<h1 class="quiz-intro__title"><?php esc_html_e( 'Style DNA', 'skyyrose-flagship' ); ?></h1>
			<p class="quiz-intro__desc">
				<?php esc_html_e( 'Seven questions. Three collections. One unique profile. Discover which SkyyRose collections match your personality and get personalized product recommendations.', 'skyyrose-flagship' ); ?>
			</p>
			<button class="quiz-start-btn" id="quiz-start">
				<?php esc_html_e( 'Begin the Quiz', 'skyyrose-flagship' ); ?>
			</button>
			<p class="quiz-intro__time"><?php esc_html_e( '2 minutes \u2022 No sign-up required', 'skyyrose-flagship' ); ?></p>
		</div>
	</section>

	<!-- ====== Questions Container ====== -->
	<section class="quiz-questions quiz-screen" id="quiz-questions"
	         aria-label="<?php esc_attr_e( 'Quiz questions', 'skyyrose-flagship' ); ?>">

		<!-- Progress Bar -->
		<div class="quiz-progress" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="7">
			<div class="quiz-progress__bar"></div>
			<span class="quiz-progress__label">1 / 7</span>
		</div>

		<!-- Questions are injected by JS -->
		<div class="quiz-question-container" id="quiz-question-container"></div>

	</section>

	<!-- ====== Results Screen ====== -->
	<section class="quiz-results quiz-screen" id="quiz-results"
	         aria-label="<?php esc_attr_e( 'Your Style DNA results', 'skyyrose-flagship' ); ?>">

		<h2 class="quiz-results__eyebrow"><?php esc_html_e( 'Your Style DNA', 'skyyrose-flagship' ); ?></h2>

		<!-- DNA Visualization -->
		<div class="quiz-dna-viz" id="quiz-dna-viz">
			<div class="quiz-dna-ring" id="quiz-dna-ring"></div>
			<div class="quiz-dna-labels" id="quiz-dna-labels"></div>
		</div>

		<!-- Personality Summary -->
		<p class="quiz-results__summary" id="quiz-results-summary"></p>

		<!-- Product Recommendations -->
		<h3 class="quiz-results__recs-heading"><?php esc_html_e( 'Your Picks', 'skyyrose-flagship' ); ?></h3>
		<div class="quiz-recs" id="quiz-recs"></div>

		<!-- Shareable Card -->
		<div class="quiz-share" id="quiz-share">
			<canvas id="quiz-share-canvas" width="600" height="400" style="display:none;"></canvas>
			<img class="quiz-share-preview" id="quiz-share-preview" alt="<?php esc_attr_e( 'Your SkyyRose Style DNA card', 'skyyrose-flagship' ); ?>" />
			<div class="quiz-share-actions">
				<button class="quiz-share-btn" id="quiz-share-btn">
					<?php esc_html_e( 'Share My DNA', 'skyyrose-flagship' ); ?>
				</button>
				<button class="quiz-share-btn quiz-share-btn--secondary" id="quiz-download-btn">
					<?php esc_html_e( 'Save Image', 'skyyrose-flagship' ); ?>
				</button>
			</div>
		</div>

		<!-- Retake -->
		<button class="quiz-retake" id="quiz-retake">
			<?php esc_html_e( 'Retake Quiz', 'skyyrose-flagship' ); ?>
		</button>

	</section>

</div><!-- .style-quiz -->
</main>

<?php get_footer(); ?>
