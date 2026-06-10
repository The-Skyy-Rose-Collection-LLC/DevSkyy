<?php
/**
 * Landing Page — Unified Orchestrator
 *
 * Single orchestrator for all 4 collection landing pages.
 * Reads $args['slug'], fetches content via skyyrose_get_landing_content(),
 * and renders all 10 sections. Mirrors the collection page pattern exactly.
 *
 * Hard-fails with a data-skyyrose-error beacon when slug is unknown — picked
 * up by scripts/verify_live_structure.py to fail deploys on render regressions.
 *
 * @package SkyyRose
 * @since   6.6.0
 */

defined( 'ABSPATH' ) || exit;

$slug = isset( $args['slug'] ) ? sanitize_key( $args['slug'] ) : '';

if ( ! function_exists( 'skyyrose_get_landing_content' ) ) {
	error_log( '[SkyyRose Landing] skyyrose_get_landing_content() not defined — inc/landing-content.php not loaded.' );
	printf(
		'<div class="skyyrose-render-error" data-skyyrose-error="missing-landing-fn" hidden></div>'
	);
	return;
}

$c = skyyrose_get_landing_content( $slug );

if ( ! $c ) {
	error_log(
		sprintf(
			"[SkyyRose Landing] Missing content config for slug '%s' in %s. Check inc/landing-content.php.",
			$slug,
			__FILE__
		)
	);
	printf(
		'<div class="skyyrose-render-error" data-skyyrose-error="missing-landing-content" data-collection="%s" hidden></div>',
		esc_attr( $slug )
	);
	return;
}

/* ── Unpack sections ────────────────────────────────────────────── */
$hero      = $c['hero']      ?? array();
$stats     = $c['stats']     ?? array();
$story     = $c['story']     ?? array();
$parallax  = $c['parallax']  ?? '';
$products  = $c['products']  ?? array();
$editorial = $c['editorial'] ?? array();
$reviews   = $c['reviews']   ?? array();
$craft     = $c['craft']     ?? array();
$faq_data  = $c['faq']       ?? array();
$cta       = $c['cta']       ?? array();
?>

<main class="lp" id="lp-top" data-collection="<?php echo esc_attr( $slug ); ?>">

	<?php
	/* ── 1. Hero ────────────────────────────────────────────────── */
	if ( ! empty( $hero ) ) {
		get_template_part(
			'template-parts/landing/hero',
			null,
			array_merge(
				$hero,
				array( 'collection' => $slug )
			)
		);
	}
	?>

	<?php
	/* ── 2. Stats bar (honest brand facts — no fake press logos) ── */
	if ( ! empty( $stats ) ) :
	?>
	<section class="lp-stats" id="stats" aria-label="<?php esc_attr_e( 'Brand Facts', 'skyyrose' ); ?>">
		<div class="lp__container">
			<ul class="lp-stats__row" role="list">
				<?php foreach ( $stats as $i => $stat ) : ?>
					<li class="lp-stats__item lp-rv" data-delay="<?php echo esc_attr( min( $i + 1, 5 ) ); ?>">
						<span class="lp-stats__value"><?php echo esc_html( $stat['value'] ); ?></span>
						<span class="lp-stats__label"><?php echo esc_html( $stat['label'] ); ?></span>
					</li>
				<?php endforeach; ?>
			</ul>
		</div>
	</section>
	<?php endif; ?>

	<?php
	/* ── 3. Story — origin narrative + founder quote ─────────────── */
	if ( ! empty( $story ) ) :
	?>
	<section class="lp-story" id="story">
		<div class="lp__container">
			<div class="lp-story__prose lp-rv">
				<?php if ( ! empty( $story['label'] ) ) : ?>
					<span class="lp-story__label"><?php echo esc_html( $story['label'] ); ?></span>
				<?php endif; ?>

				<?php if ( ! empty( $story['title'] ) ) : ?>
					<h2 class="lp-story__title"><?php echo esc_html( $story['title'] ); ?></h2>
				<?php endif; ?>

				<?php if ( ! empty( $story['paragraphs'] ) ) : ?>
					<div class="lp-story__text">
						<?php foreach ( $story['paragraphs'] as $para ) : ?>
							<p><?php echo esc_html( $para ); ?></p>
						<?php endforeach; ?>
					</div>
				<?php endif; ?>

				<?php if ( ! empty( $story['quote']['text'] ) ) : ?>
					<blockquote class="lp-story__quote">
						<p><?php echo esc_html( $story['quote']['text'] ); ?></p>
						<?php if ( ! empty( $story['quote']['cite'] ) ) : ?>
							<cite><?php echo esc_html( $story['quote']['cite'] ); ?></cite>
						<?php endif; ?>
					</blockquote>
				<?php endif; ?>
			</div>
		</div>
	</section>
	<?php endif; ?>

	<?php
	/* ── 4. Parallax banner — single statement line ───────────────── */
	if ( $parallax ) :
	?>
	<section class="lp-parallax" aria-hidden="true">
		<p class="lp-parallax__text"><?php echo esc_html( $parallax ); ?></p>
	</section>
	<?php endif; ?>

	<?php
	/* ── 5. Product grid → holo cards ───────────────────────────── */
	if ( ! empty( $products['skus'] ) ) {
		get_template_part(
			'template-parts/landing/product-grid',
			null,
			array(
				'heading'    => $products['heading']    ?? __( 'The Collection', 'skyyrose' ),
				'subheading' => $products['subheading'] ?? '',
				'skus'       => $products['skus'],
				'collection' => $slug,
				'wear_count' => $products['wear_count'] ?? 0,
			)
		);
	}
	?>

	<?php
	/* ── 6. Editorial gallery — per-collection lookbook images ────── */
	if ( ! empty( $editorial['images'] ) ) {
		get_template_part(
			'template-parts/landing/editorial',
			null,
			array(
				'heading' => $editorial['heading'] ?? '',
				'images'  => $editorial['images'],
			)
		);
	}
	?>

	<?php
	/* ── 7. Reviews / testimonials ──────────────────────────────── */
	if ( ! empty( $reviews['items'] ) ) :
	?>
	<section class="lp-reviews" id="reviews">
		<div class="lp__container">
			<?php if ( ! empty( $reviews['heading'] ) ) : ?>
				<div class="lp-reviews__header lp-rv">
					<h2><?php echo esc_html( $reviews['heading'] ); ?></h2>
				</div>
			<?php endif; ?>

			<div class="lp-reviews__grid">
				<?php foreach ( $reviews['items'] as $i => $review ) : ?>
					<div class="lp-review-card lp-rv" data-delay="<?php echo esc_attr( min( $i + 1, 5 ) ); ?>">
						<div class="lp-review-card__stars" aria-label="<?php esc_attr_e( '5 stars', 'skyyrose' ); ?>" aria-hidden="true">
							&#9733;&#9733;&#9733;&#9733;&#9733;
						</div>
						<p class="lp-review-card__text"><?php echo esc_html( $review['text'] ); ?></p>
						<p class="lp-review-card__author"><?php echo esc_html( $review['author'] ); ?></p>
					</div>
				<?php endforeach; ?>
			</div>
		</div>
	</section>
	<?php endif; ?>

	<?php
	/* ── 8. Craft cards — why it costs what it costs ─────────────── */
	if ( ! empty( $craft['cards'] ) ) :
	?>
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
				<?php foreach ( $craft['cards'] as $i => $card ) : ?>
					<div class="lp-craft__card lp-rv" data-delay="<?php echo esc_attr( min( $i + 1, 5 ) ); ?>">
						<?php if ( ! empty( $card['icon'] ) ) : ?>
							<div class="lp-craft__icon" aria-hidden="true"><?php echo esc_html( $card['icon'] ); ?></div>
						<?php endif; ?>
						<?php if ( ! empty( $card['title'] ) ) : ?>
							<h3><?php echo esc_html( $card['title'] ); ?></h3>
						<?php endif; ?>
						<?php if ( ! empty( $card['desc'] ) ) : ?>
							<p><?php echo esc_html( $card['desc'] ); ?></p>
						<?php endif; ?>
					</div>
				<?php endforeach; ?>
			</div>
		</div>
	</section>
	<?php endif; ?>

	<?php
	/* ── 9. FAQ accordion ───────────────────────────────────────── */
	if ( ! empty( $faq_data['questions'] ) ) {
		get_template_part( 'template-parts/landing/faq', null, $faq_data );
	}
	?>

	<?php
	/* ── 10. Email capture — wired to Klaviyo AJAX ───────────────── */
	if ( ! empty( $cta['heading'] ) ) :
		$email_id  = $cta['email_id']    ?? 'lp-cta-email-' . esc_attr( $slug );
		$list_slug = $cta['list_slug']   ?? 'general';
	?>
	<section class="lp-cta" id="cta">
		<div class="lp__container">
			<h2 class="lp-cta__title lp-rv"><?php echo esc_html( $cta['heading'] ); ?></h2>

			<?php if ( ! empty( $cta['subtitle'] ) ) : ?>
				<p class="lp-cta__subtitle lp-rv" data-delay="1"><?php echo esc_html( $cta['subtitle'] ); ?></p>
			<?php endif; ?>

			<form class="lp-cta__form lp-rv"
				  data-delay="2"
				  data-list="<?php echo esc_attr( $list_slug ); ?>"
				  data-nonce="<?php echo esc_attr( wp_create_nonce( 'skyyrose-nonce' ) ); ?>"
				  novalidate>
				<label for="<?php echo esc_attr( $email_id ); ?>" class="screen-reader-text">
					<?php esc_html_e( 'Your email address', 'skyyrose' ); ?>
				</label>
				<input class="lp-cta__input"
					   type="email"
					   id="<?php echo esc_attr( $email_id ); ?>"
					   name="email"
					   placeholder="<?php esc_attr_e( 'Your email address', 'skyyrose' ); ?>"
					   required
					   autocomplete="email">
				<button class="lp-cta__submit" type="submit">
					<?php echo esc_html( $cta['button_text'] ?? __( 'Join', 'skyyrose' ) ); ?>
				</button>
			</form>

			<?php if ( ! empty( $cta['note'] ) ) : ?>
				<p class="lp-cta__note lp-rv" data-delay="3"><?php echo esc_html( $cta['note'] ); ?></p>
			<?php endif; ?>
		</div>
	</section>
	<?php endif; ?>

</main>
