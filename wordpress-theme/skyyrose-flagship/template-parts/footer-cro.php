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

/**
 * Print the Footer CRO stylesheet IN PLACE, before this part's markup.
 * A footer-timed wp_enqueue_style() defers the <link> to wp_footer — after
 * the markup — so the section first paints unstyled and re-lays-out when
 * the sheet lands (~0.49 CLS on short pages where the footer opens inside
 * the viewport: cart, wishlist). An in-body <link> blocks paint of the
 * content that follows it until applied, so the section renders styled on
 * first paint. wp_print_styles() is a no-op if the handle was already
 * printed (safe to combine with a future head enqueue).
 */
$skyyrose_fcro_dir  = trailingslashit( get_stylesheet_directory() ) . 'assets/css';
$skyyrose_fcro_uri  = trailingslashit( get_stylesheet_directory_uri() ) . 'assets/css';
$skyyrose_fcro_min  = ! ( defined( 'SCRIPT_DEBUG' ) && SCRIPT_DEBUG );
$skyyrose_fcro_file = $skyyrose_fcro_min && file_exists( $skyyrose_fcro_dir . '/footer-cro.min.css' )
	? 'footer-cro.min.css'
	: 'footer-cro.css';
if ( file_exists( $skyyrose_fcro_dir . '/' . $skyyrose_fcro_file ) ) {
	wp_register_style(
		'skyyrose-footer-cro',
		$skyyrose_fcro_uri . '/' . $skyyrose_fcro_file,
		array( 'skyyrose-design-tokens' ),
		defined( 'SKYYROSE_VERSION' ) ? SKYYROSE_VERSION : false
	);
	wp_print_styles( 'skyyrose-footer-cro' );
}
?>

<!-- Scarcity Banner -->
<div class="ft-cro-banner rv-clip-up">
	<p><?php esc_html_e( 'Limited Edition. Individually Numbered. Never Restocked.', 'skyyrose' ); ?></p>
</div>

<!-- Why SkyyRose — merged testimonials + value props (structural remediation WS4) -->
<section class="ft-cro-craft rv-clip-up" aria-label="<?php esc_attr_e( 'Why SkyyRose', 'skyyrose' ); ?>">
	<div class="ft-cro__container">
		<h2 class="ft-cro__heading"><?php esc_html_e( 'Why SkyyRose', 'skyyrose' ); ?></h2>
		<p class="ft-cro__subheading"><?php esc_html_e( 'Every dollar goes into the product. No influencer budgets. No middlemen. Just quality you can feel.', 'skyyrose' ); ?></p>
		<div class="ft-cro-reviews__grid stagger-grid">
			<?php
			$ft_reviews = array(
				array( "The quality is insane. I've washed my hoodie 20+ times and it still looks brand new.", 'Marcus T., Oakland' ),
				array( 'The numbered tag makes it feel like yours alone. Exceeded every expectation.', 'Jade W., Oakland' ),
				array( "This isn't just a brand, it's a movement. The craftsmanship is unmatched.", 'Devon L., Los Angeles' ),
			);
			foreach ( $ft_reviews as $r ) :
				?>
				<div class="ft-cro-reviews__card">
					<div class="ft-cro-reviews__stars" role="img" aria-label="<?php esc_attr_e( '5 out of 5 stars', 'skyyrose' ); ?>">
						<?php for ( $s = 0; $s < 5; $s++ ) : ?>
							<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
						<?php endfor; ?>
					</div>
					<blockquote><p><?php echo esc_html( $r[0] ); ?></p></blockquote>
					<cite><?php echo esc_html( '— ' . $r[1] ); ?></cite>
				</div>
			<?php endforeach; ?>
		</div>
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
			/*
			 * Three-question teaser (structural remediation WS4) — the full FAQ
			 * lives at /faq/ (FAQPage JSON-LD); this block links there below.
			 * The stale "ship Spring 2026" pre-order answer was removed, not
			 * updated — pre-order timing copy lives on /faq/ only (HG-3).
			 */
			$ft_faq = array(
				array( __( 'How does the sizing run?', 'skyyrose' ), __( 'True to size, S through 3XL. Check the size guide on any product page for exact measurements.', 'skyyrose' ) ),
				array( __( 'Is this really limited edition?', 'skyyrose' ), __( 'Yes. Every style is produced in a numbered run of 80-250 pieces. Once sold out, never restocked or reprinted.', 'skyyrose' ) ),
				array( __( 'What is your return policy?', 'skyyrose' ), __( '30-day return and exchange on unworn items. Contact us and we will make it right.', 'skyyrose' ) ),
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
		<p class="ft-cro-faq__all">
			<a href="<?php echo esc_url( home_url( '/faq/' ) ); ?>"><?php esc_html_e( 'View all questions on the FAQ page', 'skyyrose' ); ?> &rarr;</a>
		</p>
	</div>
</section>
<?php // FAQ accordion behavior lives in assets/js/footer-cro.js (enqueued globally via inc/enqueue.php). ?>
