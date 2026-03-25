<?php
/**
 * Front Page: Brand Story
 *
 * 2-column layout with pull quote, brand stats, and optional image.
 *
 * @package SkyyRose_Flagship
 * @since   3.2.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$brand_stats = array(
	array(
		'number' => __( '2019', 'skyyrose-flagship' ),
		'label'  => __( 'Year Founded', 'skyyrose-flagship' ),
	),
	array(
		'number' => __( '28+', 'skyyrose-flagship' ),
		'label'  => __( 'Products Designed', 'skyyrose-flagship' ),
	),
	array(
		'number' => __( '3', 'skyyrose-flagship' ),
		'label'  => __( 'Collections', 'skyyrose-flagship' ),
	),
	array(
		'number' => __( '1', 'skyyrose-flagship' ),
		'label'  => __( 'Vision', 'skyyrose-flagship' ),
	),
);
?>

<section class="brand-story" aria-labelledby="brand-story-heading">
	<div class="brand-story__bg" aria-hidden="true"></div>

	<div class="brand-story__content">
		<div class="brand-story__text js-scroll-reveal">
			<span class="section-header__label">
				<?php esc_html_e( 'Our Story', 'skyyrose-flagship' ); ?>
			</span>
			<h2 class="brand-story__heading" id="brand-story-heading">
				<?php
				echo wp_kses(
					__( 'Born in Oakland,<br>Crafted with Love', 'skyyrose-flagship' ),
					array( 'br' => array() )
				);
				?>
			</h2>

			<blockquote class="brand-story__pullquote">
				<?php esc_html_e( 'We don\'t just make clothes. We make statements. Every stitch carries the weight of our story, and every piece invites you to write yours.', 'skyyrose-flagship' ); ?>
			</blockquote>

			<p>
				<?php esc_html_e( 'SkyyRose emerged from the vibrant streets of Oakland, where authenticity isn\'t just valued — it\'s essential. Founded with a vision to bridge the gap between street culture and luxury fashion, we create pieces that tell stories.', 'skyyrose-flagship' ); ?>
			</p>
			<p>
				<?php esc_html_e( 'The name "Love Hurts" carries deep meaning — it\'s our founder\'s family name, Hurts, woven into the fabric of every piece. This personal connection infuses each collection with genuine emotion and uncompromising quality.', 'skyyrose-flagship' ); ?>
			</p>

			<!-- Brand statistics -->
			<div class="brand-story__stats">
				<?php foreach ( $brand_stats as $bstat ) : ?>
					<div class="brand-story__stat">
						<span class="brand-story__stat-number">
							<?php echo esc_html( $bstat['number'] ); ?>
						</span>
						<span class="brand-story__stat-label">
							<?php echo esc_html( $bstat['label'] ); ?>
						</span>
					</div>
				<?php endforeach; ?>
			</div>

			<a href="<?php echo esc_url( home_url( '/about/' ) ); ?>" class="btn btn--outline">
				<?php esc_html_e( 'Learn More', 'skyyrose-flagship' ); ?>
			</a>
		</div>

		<div class="brand-story__visual js-scroll-reveal">
			<?php
			// Use a curated brand image if available via the customizer.
			$brand_story_image_id = get_theme_mod( 'skyyrose_brand_story_image', 0 );

			if ( $brand_story_image_id ) {
				echo wp_get_attachment_image(
					$brand_story_image_id,
					'large',
					false,
					array(
						'class'   => 'brand-story__image',
						'loading' => 'lazy',
						'alt'     => esc_attr__( 'SkyyRose brand story', 'skyyrose-flagship' ),
					)
				);
			}
			?>
		</div>
	</div>
</section>
