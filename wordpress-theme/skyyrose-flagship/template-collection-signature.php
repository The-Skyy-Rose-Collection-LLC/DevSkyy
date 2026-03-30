<?php
/**
 * Template Name: Collection - Signature
 *
 * SIGNATURE collection — the origin. Gold (#D4AF37) on deep black.
 * Uses unified collection layout (col-*) with data-collection="signature".
 *
 * @package SkyyRose_Flagship
 * @since   6.1.0
 */

defined( 'ABSPATH' ) || exit;

/* ── Product data ─────────────────────────────────────────────── */
$products = array();
if ( function_exists( 'wc_get_products' ) ) {
	$products = wc_get_products( array(
		'category' => array( 'signature' ),
		'limit'    => 20,
		'status'   => 'publish',
		'orderby'  => 'menu_order',
		'order'    => 'ASC',
	) );
}

if ( empty( $products ) ) {
	$products = skyyrose_map_collection_to_cards( 'signature' );
}

/* ── Feature cards ────────────────────────────────────────────── */
$features = array(
	array( 'icon' => '&#x2726;', 'title' => __( 'Premium Materials', 'skyyrose-flagship' ), 'text' => __( 'Italian leathers, Japanese denim, Egyptian cotton — sourced from the finest mills worldwide.', 'skyyrose-flagship' ) ),
	array( 'icon' => '&#x2726;', 'title' => __( 'Expert Construction', 'skyyrose-flagship' ), 'text' => __( 'Hand-finished details by master tailors who share our obsession with perfection.', 'skyyrose-flagship' ) ),
	array( 'icon' => '&#x2726;', 'title' => __( 'Timeless Design', 'skyyrose-flagship' ), 'text' => __( 'Classic silhouettes that never date. Investment pieces, not trend pieces.', 'skyyrose-flagship' ) ),
);

/* ── Cross-collection navigation ──────────────────────────────── */
$cross_nav = array(
	array( 'slug' => 'collection-black-rose', 'name' => __( 'Black Rose', 'skyyrose-flagship' ), 'desc' => __( 'Dark Elegance', 'skyyrose-flagship' ), 'class' => 'col-crossnav__link--black-rose' ),
	array( 'slug' => 'collection-love-hurts', 'name' => __( 'Love Hurts', 'skyyrose-flagship' ), 'desc' => __( 'Crimson Rebellion', 'skyyrose-flagship' ), 'class' => 'col-crossnav__link--love-hurts' ),
	array( 'slug' => 'collection-kids-capsule', 'name' => __( 'Kids Capsule', 'skyyrose-flagship' ), 'desc' => __( 'Next Generation', 'skyyrose-flagship' ), 'class' => 'col-crossnav__link--kids-capsule' ),
);

/* SVG whitelist for wp_kses */
$svg_kses = skyyrose_svg_kses();

get_header();
?>

<div class="col-page" data-collection="signature">
	<div class="col-floating" aria-hidden="true"></div>

	<!-- ════ Hero ════ -->
	<section class="col-hero ambient-glow" data-scroll-fade>
		<div class="col-hero__bg parallax-ken-burns">
			<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/branding/sr-collection-signature.webp?v=' . SKYYROSE_VERSION ); ?>"
			     alt="<?php esc_attr_e( 'Signature Collection — Oakland skyline', 'skyyrose-flagship' ); ?>"
			     loading="eager" fetchpriority="high" decoding="async" width="1024" height="1024">
		</div>
		<div class="col-hero__content col-reveal">
			<span class="col-hero__badge rv-blur-down"><?php esc_html_e( 'Where It All Began', 'skyyrose-flagship' ); ?></span>
			<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/branding/signature-logo-hero-transparent.png?v=' . SKYYROSE_VERSION ); ?>"
			     alt="<?php esc_attr_e( 'The SkyyRose Signature Collection', 'skyyrose-flagship' ); ?>"
			     class="col-hero__logo rv-clip-up" width="560" height="280" loading="eager">
			<p class="col-hero__tagline rv-split-word"><?php esc_html_e( 'The origin. The main event. The birth of it all.', 'skyyrose-flagship' ); ?></p>
			<p class="col-hero__subtitle rv-blur"><?php esc_html_e( 'This is what they know us for. The first rose ever pressed. The signature script logo worn around the world. Every collection since has grown from this foundation.', 'skyyrose-flagship' ); ?></p>
			<div class="col-hero__cta-group">
				<a href="#shop" class="col-hero__cta col-hero__cta--primary btn-sweep btn-press"><?php esc_html_e( 'Shop the Collection', 'skyyrose-flagship' ); ?></a>
				<a href="<?php echo esc_url( home_url( '/experience-signature/' ) ); ?>" class="col-hero__cta col-hero__cta--secondary btn-border-draw btn-press"><?php esc_html_e( 'View 3D Experience', 'skyyrose-flagship' ); ?></a>
			</div>
		</div>
		<div class="col-hero__scroll" aria-hidden="true"><span><?php esc_html_e( 'Discover', 'skyyrose-flagship' ); ?></span><span>&#x2193;</span></div>
	</section>

	<!-- ════ Marquee ════ -->
	<div class="col-marquee" aria-hidden="true">
		<div class="col-marquee__track">
			<?php for ( $i = 0; $i < 8; $i++ ) : ?>
				<span><?php esc_html_e( 'The Foundation', 'skyyrose-flagship' ); ?></span>
				<span>&#x2726;</span>
				<span><?php esc_html_e( 'Est. Oakland', 'skyyrose-flagship' ); ?></span>
				<span>&#x2726;</span>
			<?php endfor; ?>
		</div>
	</div>

	<!-- ════ Story ════ -->
	<section class="col-story rv-clip-up">
		<div class="col-story__grid">
			<div class="col-story__content">
				<span class="col-story__label"><?php esc_html_e( 'Chapter One', 'skyyrose-flagship' ); ?></span>
				<h2 class="col-story__title"><?php esc_html_e( 'The First Rose', 'skyyrose-flagship' ); ?></h2>
				<p class="col-story__text"><?php esc_html_e( 'Before the collections, before the collaborations, before the world took notice, there was a single idea: luxury grows from concrete. The Signature collection is that seed. It carries the original rose motif, the hand-drawn script logo, and every foundational silhouette that defined SkyyRose from day one.', 'skyyrose-flagship' ); ?></p>
				<blockquote class="col-story__quote"><?php esc_html_e( '"This is the crown. Everything we\'ve built starts right here, in these pieces. The first sketches, the first fabrics, the first time someone saw the logo and understood what we were building."', 'skyyrose-flagship' ); ?></blockquote>
				<p class="col-story__text"><?php esc_html_e( 'These are not trend pieces. They are the architecture of a brand. Each garment carries the DNA that every future collection inherits. When you wear Signature, you wear the origin story.', 'skyyrose-flagship' ); ?></p>
			</div>
			<div class="col-story__visual">
				<span class="col-story__visual-text"><?php esc_html_e( 'SIGNATURE', 'skyyrose-flagship' ); ?></span>
				<span class="col-story__visual-label"><?php esc_html_e( 'Est. Oakland, CA', 'skyyrose-flagship' ); ?></span>
			</div>
		</div>
	</section>

	<!-- ════ Divider + Quote ════ -->
	<div class="col-divider" aria-hidden="true"><span class="col-divider__icon">&#x2726;</span></div>
	<div class="col-quote-block rv-blur">
		<blockquote class="col-quote-block__text"><?php esc_html_e( '"The first rose ever pressed became the blueprint for everything. Signature is not a collection — it is the origin of the crown."', 'skyyrose-flagship' ); ?></blockquote>
		<cite class="col-quote-block__cite">&mdash; <?php esc_html_e( 'Corey Foster, Founder', 'skyyrose-flagship' ); ?></cite>
	</div>

	<!-- ════ Feature Cards ════ -->
	<section class="col-features rv-clip-left">
		<h2 class="col-features__heading"><?php esc_html_e( 'The Art of Craftsmanship', 'skyyrose-flagship' ); ?></h2>
		<p class="col-features__subheading"><?php esc_html_e( 'Every SIGNATURE piece represents the pinnacle of luxury streetwear — from initial sketch to final stitch.', 'skyyrose-flagship' ); ?></p>
		<div class="col-features__grid stagger-grid">
			<?php foreach ( $features as $feat ) : ?>
				<div class="col-features__card">
					<div class="col-features__icon" aria-hidden="true"><?php echo wp_kses( $feat['icon'], $svg_kses ); ?></div>
					<h3><?php echo esc_html( $feat['title'] ); ?></h3>
					<p><?php echo esc_html( $feat['text'] ); ?></p>
				</div>
			<?php endforeach; ?>
		</div>
	</section>

	<!-- ════ Product Grid ════ -->
	<section class="col-products rv-clip-up" id="shop">
		<div class="col-products__header">
			<h2><?php esc_html_e( 'The Collection', 'skyyrose-flagship' ); ?></h2>
			<p><?php esc_html_e( 'Investment-grade luxury built on the original blueprint.', 'skyyrose-flagship' ); ?></p>
		</div>
		<div class="product-grid stagger-grid" data-collection="signature">
			<?php
			$index = 0;
			foreach ( $products as $item ) :
				if ( $item instanceof WC_Product ) {
					$card_args = array( 'product' => $item, 'collection' => 'signature', 'index' => $index );
				} else {
					$card_args = array( 'product' => null, 'title' => $item['title'] ?? '', 'price' => $item['price'] ?? '', 'badge_text' => $item['badge_text'] ?? '', 'collection' => 'signature', 'permalink' => '#', 'sku' => $item['sku'] ?? '', 'index' => $index );
				}
				get_template_part( 'template-parts/product-card-holo', null, $card_args );
				$index++;
			endforeach;
			?>
		</div>
	</section>

	<!-- ════ CTA ════ -->
	<section class="col-cta rv-blur">
		<h2 class="col-cta__title"><?php esc_html_e( 'Invest in Excellence', 'skyyrose-flagship' ); ?></h2>
		<p class="col-cta__text"><?php esc_html_e( 'Join the discerning few who understand that true luxury is an investment in craftsmanship, quality, and timeless style.', 'skyyrose-flagship' ); ?></p>
		<a href="<?php echo esc_url( function_exists( 'wc_get_cart_url' ) ? wc_get_cart_url() : home_url( '/shop/' ) ); ?>" class="col-cta__btn"><?php esc_html_e( 'Shop Signature', 'skyyrose-flagship' ); ?></a>
	</section>

	<!-- ════ Cross-Collection Nav ════ -->
	<nav class="col-crossnav rv-clip-up" aria-label="<?php esc_attr_e( 'Other collections', 'skyyrose-flagship' ); ?>">
		<h3 class="col-crossnav__heading"><?php esc_html_e( 'Explore More Collections', 'skyyrose-flagship' ); ?></h3>
		<div class="col-crossnav__grid stagger-grid">
			<?php foreach ( $cross_nav as $nav ) : ?>
				<a href="<?php echo esc_url( home_url( '/' . $nav['slug'] . '/' ) ); ?>" class="col-crossnav__link <?php echo esc_attr( $nav['class'] ); ?>" aria-label="<?php echo esc_attr( sprintf( __( 'Explore the %s collection', 'skyyrose-flagship' ), $nav['name'] ) ); ?>">
					<h3><?php echo esc_html( $nav['name'] ); ?></h3>
					<p><?php echo esc_html( $nav['desc'] ); ?></p>
				</a>
			<?php endforeach; ?>
		</div>
	</nav>

	<!-- ════ Newsletter ════ -->
	<section class="col-newsletter rv-blur">
		<h2 class="col-newsletter__title"><?php esc_html_e( 'Join the Inner Circle', 'skyyrose-flagship' ); ?></h2>
		<p class="col-newsletter__text"><?php esc_html_e( 'Early access to new drops, exclusive content, and the stories behind each piece.', 'skyyrose-flagship' ); ?></p>
		<form class="col-newsletter__form" aria-label="<?php esc_attr_e( 'Newsletter signup', 'skyyrose-flagship' ); ?>">
			<label class="screen-reader-text" for="sig-email"><?php esc_html_e( 'Email address', 'skyyrose-flagship' ); ?></label>
			<input type="email" id="sig-email" class="col-newsletter__input" placeholder="<?php esc_attr_e( 'Enter your email', 'skyyrose-flagship' ); ?>" required>
			<button type="submit" class="col-newsletter__submit"><?php esc_html_e( 'Join', 'skyyrose-flagship' ); ?></button>
		</form>
	</section>

</div><!-- .col-page -->

<?php get_footer(); ?>
