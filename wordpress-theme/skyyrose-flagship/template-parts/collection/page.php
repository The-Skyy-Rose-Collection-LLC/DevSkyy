<?php
/**
 * Collection Page — Unified Layout
 *
 * Shared template part for all collection pages. Receives the collection
 * slug via $args['slug'] and renders the full page from data returned by
 * skyyrose_get_collection_content().
 *
 * Handles kids-capsule differences: no hero bg image, h1 title instead
 * of logo, no 3D experience link, pre-order product URLs, product count.
 *
 * @package SkyyRose
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

$slug = isset( $args['slug'] ) ? sanitize_key( $args['slug'] ) : '';
$c    = skyyrose_get_collection_content( $slug );

if ( ! $c ) {
	// Hard-fail: log + emit hidden error marker. Silent return previously
	// masked a missing kids-capsule config — caught only after a structural
	// audit ran. data-skyyrose-error is a project-wide beacon picked up by
	// scripts/verify_live_structure.py to fail deploys on render regressions.
	error_log(
		sprintf(
			"[SkyyRose Collections] Missing content config for slug '%s' in %s. Check inc/collection-content.php.",
			$slug,
			__FILE__
		)
	);
	printf(
		'<div class="skyyrose-render-error" data-skyyrose-error="missing-collection-content" data-collection="%s" hidden></div>',
		esc_attr( $slug )
	);
	return;
}

/* ── Shared data ────────────────────────────────────────────────── */
$products    = skyyrose_get_collection_display_products( $slug );
$cross_nav   = skyyrose_get_cross_nav( $slug );
$svg_kses    = skyyrose_svg_kses();
$has_wc      = function_exists( 'wc_get_cart_url' );
$is_kids     = ( 'kids-capsule' === $slug );
$has_hero_bg = ! empty( $c['hero_bg'] );
$has_logo    = ! empty( $c['hero_logo'] );
$has_3d      = ! empty( $c['experience_url'] );

/* Kids Capsule uses pre-order URL for product links */
$preorder_url  = $is_kids ? home_url( '/pre-order/' ) : '';
$product_count = $is_kids ? count( $products ) : 0;

/* CTA shop link */
$cta_url = $has_wc ? wc_get_cart_url() : ( $is_kids ? $preorder_url : home_url( '/shop/' ) );
?>

<div class="col-page" data-collection="<?php echo esc_attr( $slug ); ?>">
	<div class="col-floating" aria-hidden="true"></div>

	<!-- ════ Hero ════ -->
	<section class="col-hero ambient-glow" data-scroll-fade>
		<?php if ( $has_hero_bg ) : ?>
			<div class="col-hero__bg parallax-ken-burns">
				<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . $c['hero_bg'] . '?v=' . SKYYROSE_VERSION ); ?>"
					alt="<?php echo esc_attr( $c['hero_bg_alt'] ); ?>"
					loading="eager" fetchpriority="high" decoding="async" width="1024" height="1024">
			</div>
		<?php endif; ?>
		<div class="col-hero__content col-reveal">
			<span class="col-hero__badge rv-blur-down"><?php echo esc_html( $c['hero_badge'] ); ?></span>
			<?php if ( $has_logo ) : ?>
				<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . $c['hero_logo'] . '?v=' . SKYYROSE_VERSION ); ?>"
					alt="<?php echo esc_attr( $c['hero_logo_alt'] ); ?>"
					class="col-hero__logo rv-clip-up" width="<?php echo esc_attr( $c['hero_logo_w'] ); ?>" height="<?php echo esc_attr( $c['hero_logo_h'] ); ?>" loading="eager">
			<?php else : ?>
				<h1 class="col-hero__title"><span><?php echo esc_html( $c['hero_title'] ); ?></span></h1>
			<?php endif; ?>
			<p class="col-hero__tagline rv-split-word"><?php echo esc_html( $c['hero_tagline'] ); ?></p>
			<p class="col-hero__subtitle rv-blur"><?php echo esc_html( $c['hero_subtitle'] ); ?></p>
			<div class="col-hero__cta-group">
				<a href="#shop" class="col-hero__cta col-hero__cta--primary btn-sweep btn-press"><?php esc_html_e( 'Shop the Collection', 'skyyrose' ); ?></a>
				<?php if ( $has_3d ) : ?>
					<a href="<?php echo esc_url( home_url( $c['experience_url'] ) ); ?>" class="col-hero__cta col-hero__cta--secondary btn-border-draw btn-press"><?php echo esc_html( $c['hero_3d_label'] ); ?></a>
				<?php endif; ?>
			</div>
		</div>
		<div class="col-hero__scroll" aria-hidden="true"><span><?php echo esc_html( $c['hero_scroll_text'] ); ?></span><span>&#x2193;</span></div>
	</section>

	<!-- ════ Marquee ════ -->
	<div class="col-marquee" aria-hidden="true">
		<div class="col-marquee__track">
			<?php for ( $i = 0; $i < 8; $i++ ) : ?>
				<span><?php echo esc_html( $c['marquee'][0] ); ?></span>
				<span><?php echo wp_kses( $c['marquee_icon'], $svg_kses ); ?></span>
				<span><?php echo esc_html( $c['marquee'][1] ); ?></span>
				<span><?php echo wp_kses( $c['marquee_icon'], $svg_kses ); ?></span>
			<?php endfor; ?>
		</div>
	</div>

	<!-- ════ Story ════ -->
	<section class="col-story rv-clip-up">
		<div class="col-story__grid">
			<div class="col-story__content">
				<span class="col-story__label"><?php echo esc_html( $c['story_label'] ); ?></span>
				<h2 class="col-story__title"><?php echo esc_html( $c['story_title'] ); ?></h2>
				<p class="col-story__text"><?php echo esc_html( $c['story_text_1'] ); ?></p>
				<blockquote class="col-story__quote"><?php echo esc_html( $c['story_quote'] ); ?></blockquote>
				<p class="col-story__text"><?php echo esc_html( $c['story_text_2'] ); ?></p>
			</div>
			<div class="col-story__visual">
				<span class="col-story__visual-text"><?php echo esc_html( $c['story_visual_text'] ); ?></span>
				<span class="col-story__visual-label"><?php echo esc_html( $c['story_visual_label'] ); ?></span>
			</div>
		</div>
	</section>

	<!-- ════ Divider + Quote ════ -->
	<div class="col-divider" aria-hidden="true"><span class="col-divider__icon"><?php echo wp_kses( $c['divider_icon'], $svg_kses ); ?></span></div>
	<div class="col-quote-block rv-blur">
		<blockquote class="col-quote-block__text"><?php echo esc_html( $c['quote_text'] ); ?></blockquote>
		<cite class="col-quote-block__cite">&mdash; <?php echo esc_html( $c['quote_cite'] ); ?></cite>
	</div>

	<!-- ════ Feature Cards ════ -->
	<section class="col-features rv-clip-left">
		<h2 class="col-features__heading"><?php echo esc_html( $c['features_heading'] ); ?></h2>
		<p class="col-features__subheading"><?php echo esc_html( $c['features_subheading'] ); ?></p>
		<div class="col-features__grid stagger-grid">
			<?php foreach ( $c['features'] as $feat ) : ?>
				<div class="col-features__card">
					<div class="col-features__icon" aria-hidden="true"><?php echo wp_kses( $feat['icon'], $svg_kses ); ?></div>
					<h3><?php echo esc_html( $feat['title'] ); ?></h3>
					<p><?php echo esc_html( $feat['text'] ); ?></p>
				</div>
			<?php endforeach; ?>
		</div>
	</section>

	<!-- ════ Product Grid ════ -->
	<?php
	// Build subheading: kids-capsule uses a dynamic piece count, others
	// use the static copy from skyyrose_get_collection_content().
	if ( $is_kids ) {
		$products_subheading = sprintf(
			/* translators: %d: product count */
			_n( '%d Piece', '%d Pieces', $product_count, 'skyyrose' ),
			$product_count
		) . ' · ' . __( 'Limited Run', 'skyyrose' );
	} else {
		$products_subheading = $c['products_subheading'] ?? '';
	}

	get_template_part(
		'template-parts/product-grid',
		null,
		array(
			'products'      => $products,
			'collection'    => $slug,
			'heading'       => __( 'The Collection', 'skyyrose' ),
			'subheading'    => $products_subheading,
			'section_id'    => 'shop',
			'section_class' => 'col-products',
			'reveal_class'  => 'rv-clip-up',
			'permalink'     => $is_kids ? $preorder_url : '',
		)
	);
	?>

	<!-- ════ CTA ════ -->
	<section class="col-cta rv-blur">
		<h2 class="col-cta__title"><?php echo esc_html( $c['cta_title'] ); ?></h2>
		<p class="col-cta__text"><?php echo esc_html( $c['cta_text'] ); ?></p>
		<a href="<?php echo esc_url( $cta_url ); ?>" class="col-cta__btn"><?php echo esc_html( $c['cta_btn'] ); ?></a>
	</section>

	<!-- ════ Cross-Collection Nav ════ -->
	<nav class="col-crossnav rv-clip-up" aria-label="<?php esc_attr_e( 'Other collections', 'skyyrose' ); ?>">
		<h3 class="col-crossnav__heading"><?php esc_html_e( 'Explore More Collections', 'skyyrose' ); ?></h3>
		<div class="col-crossnav__grid stagger-grid">
			<?php foreach ( $cross_nav as $nav ) : ?>
				<a href="<?php echo esc_url( home_url( '/' . $nav['slug'] . '/' ) ); ?>" class="col-crossnav__link <?php echo esc_attr( $nav['class'] ); ?>" aria-label="<?php echo esc_attr( sprintf( __( 'Explore the %s collection', 'skyyrose' ), $nav['name'] ) ); ?>">
					<h3><?php echo esc_html( $nav['name'] ); ?></h3>
					<p><?php echo esc_html( $nav['desc'] ); ?></p>
				</a>
			<?php endforeach; ?>
		</div>
	</nav>

	<!-- ════ Newsletter ════ -->
	<section class="col-newsletter rv-blur">
		<h2 class="col-newsletter__title"><?php esc_html_e( 'Join the Inner Circle', 'skyyrose' ); ?></h2>
		<p class="col-newsletter__text"><?php echo esc_html( $c['newsletter_text'] ); ?></p>
		<form class="col-newsletter__form" aria-label="<?php esc_attr_e( 'Newsletter signup', 'skyyrose' ); ?>">
			<label class="screen-reader-text" for="<?php echo esc_attr( $c['email_id'] ); ?>"><?php esc_html_e( 'Email address', 'skyyrose' ); ?></label>
			<input type="email" id="<?php echo esc_attr( $c['email_id'] ); ?>" class="col-newsletter__input" placeholder="<?php esc_attr_e( 'Enter your email', 'skyyrose' ); ?>" required>
			<button type="submit" class="col-newsletter__submit"><?php esc_html_e( 'Join', 'skyyrose' ); ?></button>
		</form>
	</section>

</div><!-- .col-page -->
