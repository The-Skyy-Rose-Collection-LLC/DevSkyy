<?php
/**
 * Front Page: Testimonials
 *
 * 3 customer review cards with ratings and verified badges.
 *
 * @package SkyyRose_Flagship
 * @since   3.2.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$testimonials = array(
	array(
		'quote'    => __( 'The quality is insane. I\'ve bought from a lot of streetwear brands and nothing comes close to the weight and feel of the Black Rose Hoodie. This is real luxury.', 'skyyrose-flagship' ),
		'name'     => __( 'Marcus T.', 'skyyrose-flagship' ),
		'location' => __( 'Oakland, CA', 'skyyrose-flagship' ),
		'product'  => __( 'BLACK Rose Hoodie', 'skyyrose-flagship' ),
		'rating'   => 5,
		'verified' => true,
	),
	array(
		'quote'    => __( 'Wore The Fannie to a gallery opening and got stopped five times. People wanted to know the brand. SkyyRose is about to blow up — get in now.', 'skyyrose-flagship' ),
		'name'     => __( 'Jasmine R.', 'skyyrose-flagship' ),
		'location' => __( 'Los Angeles, CA', 'skyyrose-flagship' ),
		'product'  => __( 'The Fannie Pack', 'skyyrose-flagship' ),
		'rating'   => 5,
		'verified' => true,
	),
	array(
		'quote'    => __( 'The Bay Set is my go-to for everything. Airport fits, studio sessions, date nights. The rose gold tones hit different. Worth every penny.', 'skyyrose-flagship' ),
		'name'     => __( 'Devon K.', 'skyyrose-flagship' ),
		'location' => __( 'San Francisco, CA', 'skyyrose-flagship' ),
		'product'  => __( 'The Bay Set', 'skyyrose-flagship' ),
		'rating'   => 5,
		'verified' => true,
	),
);
?>

<section class="testimonials" aria-labelledby="testimonials-heading">
	<div class="testimonials__header section-header">
		<span class="section-header__label">
			<?php esc_html_e( 'Real Talk', 'skyyrose-flagship' ); ?>
		</span>
		<h2 class="section-header__title" id="testimonials-heading">
			<?php esc_html_e( 'What the Family Says', 'skyyrose-flagship' ); ?>
		</h2>
		<p class="section-header__subtitle">
			<?php esc_html_e( 'Don\'t take our word for it. Hear from the SkyyRose community.', 'skyyrose-flagship' ); ?>
		</p>
	</div>

	<div class="testimonials__grid">
		<?php foreach ( $testimonials as $testimonial ) : ?>
			<div class="testimonials__card js-scroll-reveal">
				<div class="testimonials__card-inner">
					<!-- Stars -->
					<div class="testimonials__stars" aria-label="<?php echo esc_attr( sprintf( __( 'Rated %d out of 5', 'skyyrose-flagship' ), $testimonial['rating'] ) ); ?>">
						<?php for ( $i = 0; $i < $testimonial['rating']; $i++ ) : ?>
							<svg class="testimonials__star" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
								<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
							</svg>
						<?php endfor; ?>
					</div>

					<!-- Quote -->
					<blockquote class="testimonials__quote">
						<?php echo esc_html( $testimonial['quote'] ); ?>
					</blockquote>

					<!-- Attribution -->
					<div class="testimonials__author">
						<div class="testimonials__avatar" aria-hidden="true">
							<?php echo esc_html( mb_substr( $testimonial['name'], 0, 1 ) ); ?>
						</div>
						<div class="testimonials__author-info">
							<span class="testimonials__name">
								<?php echo esc_html( $testimonial['name'] ); ?>
							</span>
							<span class="testimonials__location">
								<?php echo esc_html( $testimonial['location'] ); ?>
							</span>
						</div>
						<?php if ( $testimonial['verified'] ) : ?>
							<span class="testimonials__verified" title="<?php esc_attr_e( 'Verified Purchase', 'skyyrose-flagship' ); ?>">
								<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
									<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
									<polyline points="22 4 12 14.01 9 11.01" fill="none" stroke="currentColor" stroke-width="2"/>
								</svg>
								<?php esc_html_e( 'Verified', 'skyyrose-flagship' ); ?>
							</span>
						<?php endif; ?>
					</div>

					<!-- Product purchased -->
					<p class="testimonials__product">
						<?php
						/* translators: %s: product name */
						echo esc_html( sprintf( __( 'Purchased: %s', 'skyyrose-flagship' ), $testimonial['product'] ) );
						?>
					</p>
				</div>
			</div>
		<?php endforeach; ?>
	</div>
</section>
