<?php
/**
 * Shared Landing Page Partial — renders all 10 sections from landing data.
 *
 * Consumed by template-landing-{collection}.php files. Each landing template
 * is now a 16-line stub that resolves its data via skyyrose_get_landing_data()
 * and delegates to this partial.
 *
 * Sections rendered (in order):
 *   1. Hero          (delegates to template-parts/landing/hero.php)
 *   2. Press bar
 *   3. Story
 *   4. Parallax banner
 *   5. Product grid  (delegates to template-parts/landing/product-grid.php)
 *   6. Editorial gallery
 *   7. Reviews
 *   8. Craft
 *   9. FAQ           (delegates to template-parts/landing/faq.php)
 *  10. Email CTA
 *
 * Required $args keys:
 *   - 'collection' (string)  — slug used for the [data-collection] attribute
 *   - 'data' (array)         — full landing data array (from skyyrose_get_landing_data)
 *
 * @package SkyyRose
 * @since   7.1.0
 *
 * phpcs:disable WordPress.Files.FileName.NotHyphenatedLowercase
 */

defined( 'ABSPATH' ) || exit;

/** @var array<string, mixed> $args */
$collection = isset( $args['collection'] ) ? sanitize_html_class( $args['collection'] ) : '';
$data       = isset( $args['data'] ) && is_array( $args['data'] ) ? $args['data'] : array();

if ( empty( $data ) || empty( $collection ) ) {
	return;
}

$story     = $data['story'] ?? array();
$reviews   = $data['reviews'] ?? array();
$craft     = $data['craft'] ?? array();
$editorial = $data['editorial'] ?? array();
$cta       = $data['cta'] ?? array();
?>

<div class="lp" data-collection="<?php echo esc_attr( $collection ); ?>">

	<?php
	/* ───── 1. Hero ───── */
	if ( ! empty( $data['hero'] ) ) {
		get_template_part(
			'template-parts/landing/hero',
			null,
			array_merge( array( 'collection' => $collection ), $data['hero'] )
		);
	}
	?>

	<?php /* ───── 2. Press Bar ───── */ ?>
	<?php if ( ! empty( $data['press'] ) ) : ?>
	<div class="lp-press lp-rv" aria-label="Featured in">
		<div class="lp__container">
			<div class="lp-press__row">
				<?php foreach ( $data['press'] as $name ) : ?>
					<span class="lp-press__name"><?php echo esc_html( $name ); ?></span>
				<?php endforeach; ?>
			</div>
		</div>
	</div>
	<?php endif; ?>

	<?php /* ───── 3. Story ───── */ ?>
	<?php if ( ! empty( $story ) ) : ?>
	<section class="lp-story" id="story">
		<div class="lp__container">
			<div class="lp-story__grid">
				<div class="lp-story__text lp-rv">
					<?php if ( ! empty( $story['label'] ) ) : ?>
						<span class="lp-story__label"><?php echo esc_html( $story['label'] ); ?></span>
					<?php endif; ?>
					<?php if ( ! empty( $story['title'] ) ) : ?>
						<h2 class="lp-story__title"><?php echo esc_html( $story['title'] ); ?></h2>
					<?php endif; ?>
					<?php foreach ( ( $story['paragraphs'] ?? array() ) as $para ) : ?>
						<p><?php echo esc_html( $para ); ?></p>
					<?php endforeach; ?>
					<?php if ( ! empty( $story['quote'] ) ) : ?>
						<blockquote class="lp-story__quote">
							<p><?php echo esc_html( $story['quote'] ); ?></p>
							<?php if ( ! empty( $story['cite'] ) ) : ?>
								<cite><?php echo esc_html( $story['cite'] ); ?></cite>
							<?php endif; ?>
						</blockquote>
					<?php endif; ?>
				</div>
				<div class="lp-story__image lp-rv" data-delay="2" aria-hidden="true"></div>
			</div>
		</div>
	</section>
	<?php endif; ?>

	<?php /* ───── 4. Parallax Banner ───── */ ?>
	<?php if ( ! empty( $data['parallax'] ) ) : ?>
	<div class="lp-parallax lp-rv">
		<div class="lp__container">
			<p class="lp-parallax__text"><?php echo esc_html( $data['parallax'] ); ?></p>
		</div>
	</div>
	<?php endif; ?>

	<?php
	/* ───── 5. Product Grid ───── */
	if ( ! empty( $data['product_grid'] ) ) {
		get_template_part(
			'template-parts/landing/product-grid',
			null,
			$data['product_grid']
		);
	}
	?>

	<?php /* ───── 6. Editorial Gallery ───── */ ?>
	<?php if ( ! empty( $editorial['heading'] ) ) : ?>
	<section class="lp-editorial" id="editorial">
		<div class="lp__container">
			<div class="lp-editorial__header lp-rv">
				<h2><?php echo esc_html( $editorial['heading'] ); ?></h2>
			</div>

			<div class="lp-editorial__grid lp-editorial__grid--top">
				<?php for ( $i = 1; $i <= ( $editorial['top_count'] ?? 3 ); $i++ ) : ?>
					<div class="lp-editorial__item lp-rv" data-delay="<?php echo esc_attr( (string) $i ); ?>"></div>
				<?php endfor; ?>
			</div>

			<?php if ( ! empty( $editorial['bot_count'] ) ) : ?>
				<div class="lp-editorial__grid lp-editorial__grid--row2">
					<?php for ( $j = 1; $j <= $editorial['bot_count']; $j++ ) : ?>
						<div class="lp-editorial__item lp-rv" data-delay="<?php echo esc_attr( (string) $j ); ?>"></div>
					<?php endfor; ?>
				</div>
			<?php endif; ?>
		</div>
	</section>
	<?php endif; ?>

	<?php /* ───── 7. Reviews ───── */ ?>
	<?php if ( ! empty( $reviews['items'] ) ) : ?>
	<section class="lp-reviews" id="reviews">
		<div class="lp__container">
			<?php if ( ! empty( $reviews['heading'] ) ) : ?>
				<div class="lp-reviews__header lp-rv">
					<h2><?php echo esc_html( $reviews['heading'] ); ?></h2>
				</div>
			<?php endif; ?>

			<div class="lp-reviews__grid">
				<?php
				$rev_delay = 1;
				foreach ( $reviews['items'] as $review ) :
					?>
					<div class="lp-review-card lp-rv" data-delay="<?php echo esc_attr( (string) $rev_delay ); ?>">
						<div class="lp-review-card__stars" aria-label="5 out of 5 stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
						<p class="lp-review-card__text"><?php echo esc_html( $review['text'] ); ?></p>
						<cite class="lp-review-card__author">&mdash; <?php echo esc_html( $review['author'] ); ?></cite>
					</div>
					<?php
					++$rev_delay;
				endforeach;
				?>
			</div>
		</div>
	</section>
	<?php endif; ?>

	<?php /* ───── 8. Craft ───── */ ?>
	<?php if ( ! empty( $craft['cards'] ) ) : ?>
	<section class="lp-craft" id="craft">
		<div class="lp__container">
			<?php if ( ! empty( $craft['heading'] ) ) : ?>
				<div class="lp-craft__header lp-rv">
					<h2><?php echo esc_html( $craft['heading'] ); ?></h2>
					<?php if ( ! empty( $craft['subheading'] ) ) : ?>
						<p><?php echo esc_html( $craft['subheading'] ); ?></p>
					<?php endif; ?>
				</div>
			<?php endif; ?>

			<div class="lp-craft__grid">
				<?php
				$craft_delay = 1;
				foreach ( $craft['cards'] as $card ) :
					?>
					<div class="lp-craft__card lp-rv" data-delay="<?php echo esc_attr( (string) $craft_delay ); ?>">
						<span class="lp-craft__icon" aria-hidden="true"><?php echo esc_html( $card['icon'] ); ?></span>
						<h3><?php echo esc_html( $card['title'] ); ?></h3>
						<p><?php echo esc_html( $card['desc'] ); ?></p>
					</div>
					<?php
					++$craft_delay;
				endforeach;
				?>
			</div>
		</div>
	</section>
	<?php endif; ?>

	<?php
	/* ───── 9. FAQ ───── */
	if ( ! empty( $data['faq'] ) ) {
		get_template_part(
			'template-parts/landing/faq',
			null,
			$data['faq']
		);
	}
	?>

	<?php /* ───── 10. Email CTA ───── */ ?>
	<?php if ( ! empty( $cta['heading'] ) ) : ?>
	<section class="lp-cta" id="signup">
		<div class="lp__container">
			<h2 class="lp-cta__title lp-rv"><?php echo esc_html( $cta['heading'] ); ?></h2>
			<?php if ( ! empty( $cta['subtitle'] ) ) : ?>
				<p class="lp-cta__subtitle lp-rv" data-delay="1"><?php echo esc_html( $cta['subtitle'] ); ?></p>
			<?php endif; ?>
			<form class="lp-cta__form lp-rv" data-delay="2" action="#" method="post" aria-label="<?php echo esc_attr__( 'Newsletter signup', 'skyyrose' ); ?>">
				<label class="screen-reader-text" for="lp-cta-email-<?php echo esc_attr( $collection ); ?>">
					<?php esc_html_e( 'Email address', 'skyyrose' ); ?>
				</label>
				<input
					id="lp-cta-email-<?php echo esc_attr( $collection ); ?>"
					class="lp-cta__input"
					type="email"
					name="email"
					placeholder="<?php esc_attr_e( 'Enter your email', 'skyyrose' ); ?>"
					required
					autocomplete="email">
				<button type="submit" class="lp-cta__submit">
					<?php echo esc_html( $cta['submit_text'] ?? __( 'Join', 'skyyrose' ) ); ?>
				</button>
			</form>
			<?php if ( ! empty( $cta['note'] ) ) : ?>
				<p class="lp-cta__note lp-rv" data-delay="3"><?php echo esc_html( $cta['note'] ); ?></p>
			<?php endif; ?>
		</div>
	</section>
	<?php endif; ?>

</div><!-- /.lp -->
