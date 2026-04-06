<?php
/**
 * Template Name: Collection - Kids Capsule
 *
 * KIDS CAPSULE — luxury runs in the family. Rose-gold (#B76E79) on dark.
 * Uses unified collection layout (col-*) with data-collection="kids-capsule".
 * NOT pink, NOT playful — same dark luxury DNA as every SkyyRose collection.
 *
 * @package SkyyRose_Flagship
 * @since   6.1.0
 */

defined( 'ABSPATH' ) || exit;

/* ── Product data (catalog = source of truth, WC enriches) ───── */
$preorder_url = home_url( '/pre-order/' );
$products     = skyyrose_get_collection_display_products( 'kids-capsule' );

$product_count = count( $products );

/* ── Feature cards ────────────────────────────────────────────── */
$features = array(
	array( 'icon' => '&#x2726;', 'title' => __( 'Premium Materials', 'skyyrose-flagship' ), 'text' => __( 'Same uncompromising fabrics as the adult lines — premium cotton, reinforced stitching, luxury hand-feel.', 'skyyrose-flagship' ) ),
	array( 'icon' => '&#x2726;', 'title' => __( 'Built to Last', 'skyyrose-flagship' ), 'text' => __( 'Engineered for the energy of youth. Double-stitched seams, pre-shrunk fits, colorfast dyes that survive everything.', 'skyyrose-flagship' ) ),
	array( 'icon' => '&#x2726;', 'title' => __( 'Dark Luxury DNA', 'skyyrose-flagship' ), 'text' => __( 'No pastels. No cartoons. Real streetwear scaled down, not dumbed down. The same aesthetic the brand was built on.', 'skyyrose-flagship' ) ),
);

/* Cross-collection navigation — sourced from inc/collections-config.php */
$cross_nav = skyyrose_get_cross_nav( 'kids-capsule' );

$svg_kses = skyyrose_svg_kses();

get_header();
?>

<div class="col-page" data-collection="kids-capsule">
	<div class="col-floating" aria-hidden="true"></div>

	<!-- ════ Hero ════ -->
	<section class="col-hero ambient-glow" data-scroll-fade>
		<div class="col-hero__content col-reveal">
			<span class="col-hero__badge rv-blur-down"><?php esc_html_e( 'New Collection', 'skyyrose-flagship' ); ?></span>
			<h1 class="col-hero__title"><span><?php esc_html_e( 'KIDS CAPSULE', 'skyyrose-flagship' ); ?></span></h1>
			<p class="col-hero__tagline rv-split-word"><?php esc_html_e( 'Luxury runs in the family.', 'skyyrose-flagship' ); ?></p>
			<p class="col-hero__subtitle rv-blur"><?php esc_html_e( 'Premium streetwear for the next generation — powerful, elevated, and born into legacy. Because legacy is not inherited. It is worn.', 'skyyrose-flagship' ); ?></p>
			<div class="col-hero__cta-group">
				<a href="#shop" class="col-hero__cta col-hero__cta--primary btn-sweep btn-press"><?php esc_html_e( 'Shop the Collection', 'skyyrose-flagship' ); ?></a>
			</div>
		</div>
		<div class="col-hero__scroll" aria-hidden="true"><span><?php esc_html_e( 'Explore', 'skyyrose-flagship' ); ?></span><span>&#x2193;</span></div>
	</section>

	<!-- ════ Marquee ════ -->
	<div class="col-marquee" aria-hidden="true">
		<div class="col-marquee__track">
			<?php for ( $i = 0; $i < 8; $i++ ) : ?>
				<span><?php esc_html_e( 'Born Into Luxury', 'skyyrose-flagship' ); ?></span>
				<span>&#x2726;</span>
				<span><?php esc_html_e( 'Next Generation', 'skyyrose-flagship' ); ?></span>
				<span>&#x2726;</span>
			<?php endfor; ?>
		</div>
	</div>

	<!-- ════ Story ════ -->
	<section class="col-story rv-clip-up">
		<div class="col-story__grid">
			<div class="col-story__content">
				<span class="col-story__label"><?php esc_html_e( 'Her Name', 'skyyrose-flagship' ); ?></span>
				<h2 class="col-story__title"><?php esc_html_e( 'Named After My Daughter', 'skyyrose-flagship' ); ?></h2>
				<p class="col-story__text"><?php esc_html_e( 'The whole brand is named after her — Skyy Rose. My daughter. She was on the way when I had nothing. No drive, no money, no support. But that baby coming changed everything. I needed to build something she\'d be proud to carry. Kids Capsule is the promise made real — pieces I designed thinking about my daughter walking into a room and knowing she belongs there.', 'skyyrose-flagship' ); ?></p>
				<blockquote class="col-story__quote"><?php esc_html_e( '"No pastels. No cartoons. Skyy Rose doesn\'t wear that. She wears what her father built — premium, dark, elegant. Scaled down but never dumbed down."', 'skyyrose-flagship' ); ?></blockquote>
				<p class="col-story__text"><?php esc_html_e( 'Every kid deserves to feel like they belong at the table. Not the kids\' table — THE table. Kids Capsule is that seat.', 'skyyrose-flagship' ); ?></p>
			</div>
			<div class="col-story__visual">
				<span class="col-story__visual-text"><?php esc_html_e( 'KC', 'skyyrose-flagship' ); ?></span>
				<span class="col-story__visual-label"><?php esc_html_e( 'Kids Capsule', 'skyyrose-flagship' ); ?></span>
			</div>
		</div>
	</section>

	<!-- ════ Divider + Quote ════ -->
	<div class="col-divider" aria-hidden="true"><span class="col-divider__icon">&#x2726;</span></div>
	<div class="col-quote-block rv-blur">
		<blockquote class="col-quote-block__text"><?php esc_html_e( '"I built SkyyRose so my daughter would never have to wonder if she was enough. Every piece in Kids Capsule carries that — a father\'s promise that she can be anything, wear anything, own any room she walks into."', 'skyyrose-flagship' ); ?></blockquote>
		<cite class="col-quote-block__cite">&mdash; <?php esc_html_e( 'Corey Foster, Father & Founder', 'skyyrose-flagship' ); ?></cite>
	</div>

	<!-- ════ Feature Cards ════ -->
	<section class="col-features rv-clip-left">
		<h2 class="col-features__heading"><?php esc_html_e( 'Built Different', 'skyyrose-flagship' ); ?></h2>
		<p class="col-features__subheading"><?php esc_html_e( 'The same philosophy that built SkyyRose — uncompromising quality, dark luxury DNA, premium everything.', 'skyyrose-flagship' ); ?></p>
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
			<p>
				<?php
				printf(
					esc_html( _n( '%d Piece', '%d Pieces', $product_count, 'skyyrose-flagship' ) ),
					$product_count
				);
				echo ' &middot; ';
				esc_html_e( 'Limited Run', 'skyyrose-flagship' );
				?>
			</p>
		</div>
		<div class="product-grid stagger-grid" data-collection="kids-capsule">
			<?php
			$index = 0;
			foreach ( $products as $item ) :
				if ( $item instanceof WC_Product ) {
					$card_args = array( 'product' => $item, 'collection' => 'kids-capsule', 'index' => $index );
				} else {
					$card_args = array( 'product' => null, 'title' => $item['title'] ?? '', 'price' => $item['price'] ?? '', 'badge_text' => $item['badge_text'] ?? '', 'collection' => 'kids-capsule', 'permalink' => $preorder_url, 'sku' => $item['sku'] ?? '', 'index' => $index );
				}
				get_template_part( 'template-parts/product-card-holo', null, $card_args );
				$index++;
			endforeach;
			?>
		</div>
	</section>

	<!-- ════ CTA ════ -->
	<section class="col-cta rv-blur">
		<h2 class="col-cta__title"><?php esc_html_e( 'Their Turn Now', 'skyyrose-flagship' ); ?></h2>
		<p class="col-cta__text"><?php esc_html_e( 'We built this for Skyy Rose. For every kid who deserves to feel the same luxury their parents wear. Legacy isn\'t inherited — it\'s earned. But we can give them a head start.', 'skyyrose-flagship' ); ?></p>
		<a href="<?php echo esc_url( function_exists( 'wc_get_cart_url' ) ? wc_get_cart_url() : $preorder_url ); ?>" class="col-cta__btn"><?php esc_html_e( 'Shop Kids Capsule', 'skyyrose-flagship' ); ?></a>
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
		<p class="col-newsletter__text"><?php esc_html_e( 'Be first to know about new Kids Capsule drops and family exclusives.', 'skyyrose-flagship' ); ?></p>
		<form class="col-newsletter__form" aria-label="<?php esc_attr_e( 'Newsletter signup', 'skyyrose-flagship' ); ?>">
			<label class="screen-reader-text" for="kc-email"><?php esc_html_e( 'Email address', 'skyyrose-flagship' ); ?></label>
			<input type="email" id="kc-email" class="col-newsletter__input" placeholder="<?php esc_attr_e( 'Enter your email', 'skyyrose-flagship' ); ?>" required>
			<button type="submit" class="col-newsletter__submit"><?php esc_html_e( 'Join', 'skyyrose-flagship' ); ?></button>
		</form>
	</section>

</div><!-- .col-page -->

<?php get_footer(); ?>
