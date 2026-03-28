<?php
/**
 * Template Name: Collection - Signature
 *
 * SIGNATURE collection — standalone page template.
 * Hero, origin story, craftsmanship, holo product grid,
 * quality promise, CTA banner.
 *
 * Gold (#D4AF37) accents on deep black.
 *
 * @package SkyyRose_Flagship
 * @since   5.0.0
 */

defined( 'ABSPATH' ) || exit;


/* ── Product data ──────────────────────────────────────────────────────────── */
$signature_products = array();

if ( function_exists( 'wc_get_products' ) ) {
	$signature_products = wc_get_products( array(
		'category' => array( 'signature' ),
		'limit'    => 20,
		'status'   => 'publish',
	) );
}

// Static fallback when WooCommerce is unavailable or returns no products.
if ( empty( $signature_products ) ) {
	$signature_products = array(
		array(
			'title'      => __( 'Signature Rose Hoodie', 'skyyrose-flagship' ),
			'price'      => '$185',
			'badge_text' => __( 'Iconic', 'skyyrose-flagship' ),
			'collection' => 'signature',
			'permalink'  => '#',
			'sku'        => 'sig-rose-hoodie',
			'category'   => 'tops',
		),
		array(
			'title'      => __( 'Script Logo Tee', 'skyyrose-flagship' ),
			'price'      => '$95',
			'badge_text' => __( 'Bestseller', 'skyyrose-flagship' ),
			'collection' => 'signature',
			'permalink'  => '#',
			'sku'        => 'sig-script-tee',
			'category'   => 'tops',
		),
		array(
			'title'      => __( 'Gold Standard Jacket', 'skyyrose-flagship' ),
			'price'      => '$425',
			'badge_text' => __( 'Limited', 'skyyrose-flagship' ),
			'collection' => 'signature',
			'permalink'  => '#',
			'sku'        => 'sig-gold-jacket',
			'category'   => 'outerwear',
		),
		array(
			'title'      => __( 'Heritage Crewneck', 'skyyrose-flagship' ),
			'price'      => '$145',
			'badge_text' => '',
			'collection' => 'signature',
			'permalink'  => '#',
			'sku'        => 'sig-heritage-crew',
			'category'   => 'tops',
		),
		array(
			'title'      => __( 'Foundation Joggers', 'skyyrose-flagship' ),
			'price'      => '$155',
			'badge_text' => __( 'New', 'skyyrose-flagship' ),
			'collection' => 'signature',
			'permalink'  => '#',
			'sku'        => 'sig-foundation-joggers',
			'category'   => 'bottoms',
		),
		array(
			'title'      => __( 'Crown Cap', 'skyyrose-flagship' ),
			'price'      => '$65',
			'badge_text' => '',
			'collection' => 'signature',
			'permalink'  => '#',
			'sku'        => 'sig-crown-cap',
			'category'   => 'accessories',
		),
	);
}

/* ── Craftsmanship features ────────────────────────────────────────────────── */
$craft_features = array(
	array(
		'icon'  => '&#x2726;',
		'title' => __( 'Premium Materials', 'skyyrose-flagship' ),
		'desc'  => __( 'Italian leathers, Japanese denim, Egyptian cotton', 'skyyrose-flagship' ),
	),
	array(
		'icon'  => '&#x2726;',
		'title' => __( 'Expert Construction', 'skyyrose-flagship' ),
		'desc'  => __( 'Hand-finished details by master tailors', 'skyyrose-flagship' ),
	),
	array(
		'icon'  => '&#x2726;',
		'title' => __( 'Timeless Design', 'skyyrose-flagship' ),
		'desc'  => __( 'Classic silhouettes that never date', 'skyyrose-flagship' ),
	),
	array(
		'icon'  => '&#x2726;',
		'title' => __( 'Limited Production', 'skyyrose-flagship' ),
		'desc'  => __( 'Small batches for exclusivity', 'skyyrose-flagship' ),
	),
);

/* ── Quality promise items ─────────────────────────────────────────────────── */
$quality_items = array(
	array(
		'icon'  => '&#x1F3C6;',
		'title' => __( 'Lifetime Warranty', 'skyyrose-flagship' ),
		'desc'  => __( 'Covers manufacturing defects for the life of the garment', 'skyyrose-flagship' ),
	),
	array(
		'icon'  => '&#x1F527;',
		'title' => __( 'Free Repairs', 'skyyrose-flagship' ),
		'desc'  => __( 'Complimentary alterations and repairs for the first year', 'skyyrose-flagship' ),
	),
	array(
		'icon'  => '&#x1F4E6;',
		'title' => __( 'Premium Packaging', 'skyyrose-flagship' ),
		'desc'  => __( 'Each piece arrives in our signature luxury presentation', 'skyyrose-flagship' ),
	),
	array(
		'icon'  => '&#x1F48E;',
		'title' => __( 'Authenticity Card', 'skyyrose-flagship' ),
		'desc'  => __( 'Numbered certificate of authenticity with each purchase', 'skyyrose-flagship' ),
	),
);

get_header();
?>

<div class="sig-art-deco"></div>

<!-- ════ Hero ════════════════════════════════════════════════════════════════ -->
<section class="sig-hero">
	<div class="sig-hero__content reveal">
		<span class="sig-hero__badge"><?php echo esc_html__( 'Where It All Began', 'skyyrose-flagship' ); ?></span>
		<h1 class="sig-hero__title gradient-text-animated"><?php echo esc_html__( 'SIGNATURE', 'skyyrose-flagship' ); ?></h1>
		<p class="sig-hero__tagline"><?php echo esc_html__( 'The origin. The main event. The birth of it all.', 'skyyrose-flagship' ); ?></p>
		<p class="sig-hero__subtitle"><?php echo esc_html__( 'This is what they know us for. The first rose ever pressed. The signature script logo worn around the world. The iconic pieces that built the crown. Every collection since has grown from this foundation.', 'skyyrose-flagship' ); ?></p>
		<div class="sig-hero__cta-group">
			<a href="#col-catalog" class="sig-hero__cta sig-hero__cta--primary"><?php echo esc_html__( 'Shop the Collection', 'skyyrose-flagship' ); ?></a>
			<a href="<?php echo esc_url( home_url( '/experience-signature/' ) ); ?>" class="sig-hero__cta sig-hero__cta--secondary"><?php echo esc_html__( 'View 3D Experience', 'skyyrose-flagship' ); ?></a>
		</div>
	</div>
	<div class="sig-hero__scroll">
		<span><?php echo esc_html__( 'Discover', 'skyyrose-flagship' ); ?></span>
		<span>&#x2193;</span>
	</div>
</section>

<!-- ════ Origin Story ═══════════════════════════════════════════════════════ -->
<section class="sig-origin reveal">
	<div class="sig-origin__grid">
		<div class="sig-origin__content">
			<span class="sig-origin__label"><?php echo esc_html__( 'Chapter One', 'skyyrose-flagship' ); ?></span>
			<h2 class="sig-origin__title"><?php echo esc_html__( 'The First Rose', 'skyyrose-flagship' ); ?></h2>
			<p class="sig-origin__text"><?php echo esc_html__( 'Before the collections, before the collaborations, before the world took notice, there was a single idea: luxury grows from concrete. The Signature collection is that seed. It carries the original rose motif, the hand-drawn script logo, and every foundational silhouette that defined SkyyRose from day one.', 'skyyrose-flagship' ); ?></p>
			<blockquote class="sig-origin__quote"><?php echo esc_html__( '"This is the crown. Everything we\'ve built starts right here, in these pieces. The first sketches, the first fabrics, the first time someone saw the logo and understood what we were building."', 'skyyrose-flagship' ); ?></blockquote>
			<p class="sig-origin__text"><?php echo esc_html__( 'These are not trend pieces. They are the architecture of a brand. Each garment carries the DNA that every future collection inherits. When you wear Signature, you wear the origin story.', 'skyyrose-flagship' ); ?></p>
		</div>
		<div class="sig-origin__visual">
			<span class="sig-origin__rose">&#x1F339;</span>
			<span class="sig-origin__visual-label"><?php echo esc_html__( 'Est. Oakland, CA', 'skyyrose-flagship' ); ?></span>
		</div>
	</div>
</section>

<!-- ════ Divider ═════════════════════════════════════════════════════════════ -->
<div class="sig-divider"><span>&#x2726;</span></div>

<!-- ════ Craftsmanship ══════════════════════════════════════════════════════ -->
<section class="sig-craft reveal">
	<div class="sig-craft__grid">
		<div class="sig-craft__content">
			<h2 class="sig-craft__title"><?php echo esc_html__( 'The Art of Craftsmanship', 'skyyrose-flagship' ); ?></h2>
			<p class="sig-craft__text"><?php echo esc_html__( 'Every SIGNATURE piece represents the pinnacle of luxury streetwear. We source only the finest materials from renowned mills and work with master craftspeople who share our obsession with perfection.', 'skyyrose-flagship' ); ?></p>
			<p class="sig-craft__text"><?php echo esc_html__( 'From the initial sketch to the final stitch, each garment undergoes rigorous quality checks to ensure it meets our exacting standards. This is clothing built to be cherished for generations.', 'skyyrose-flagship' ); ?></p>
			<div class="sig-craft__features">
				<?php foreach ( $craft_features as $feature ) : ?>
					<div class="sig-craft__feature">
						<span class="sig-craft__feature-icon"><?php echo wp_kses( $feature['icon'], array( 'svg' => array( 'viewBox' => true, 'fill' => true, 'stroke' => true, 'class' => true, 'aria-hidden' => true, 'width' => true, 'height' => true, 'xmlns' => true ), 'path' => array( 'd' => true, 'fill' => true, 'stroke' => true, 'stroke-width' => true, 'stroke-linecap' => true, 'stroke-linejoin' => true ), 'circle' => array( 'cx' => true, 'cy' => true, 'r' => true, 'fill' => true ), 'line' => array( 'x1' => true, 'y1' => true, 'x2' => true, 'y2' => true, 'stroke' => true, 'stroke-width' => true ), 'polyline' => array( 'points' => true, 'fill' => true, 'stroke' => true, 'stroke-width' => true ), 'rect' => array( 'x' => true, 'y' => true, 'width' => true, 'height' => true, 'rx' => true, 'ry' => true, 'fill' => true, 'stroke' => true ) ) ); ?></span>
						<div>
							<h4><?php echo esc_html( $feature['title'] ); ?></h4>
							<p><?php echo esc_html( $feature['desc'] ); ?></p>
						</div>
					</div>
				<?php endforeach; ?>
			</div>
		</div>
		<div class="sig-craft__image">&#x25C6;</div>
	</div>
</section>

<!-- ════ Holographic Product Grid ═══════════════════════════════════════════ -->
<section class="sig-products reveal" id="col-catalog">
	<div class="sig-products__header">
		<h2><?php echo esc_html__( 'The Collection', 'skyyrose-flagship' ); ?></h2>
		<p><?php echo esc_html__( 'The iconic pieces. Investment-grade luxury built on the original blueprint.', 'skyyrose-flagship' ); ?></p>
	</div>

	<div class="product-grid" data-collection="signature">
		<div class="product-grid__header">
			<h3 class="product-grid__title"><?php echo esc_html__( 'Signature Essentials', 'skyyrose-flagship' ); ?></h3>
			<p class="product-grid__subtitle"><?php echo esc_html__( 'The foundation of the SkyyRose wardrobe', 'skyyrose-flagship' ); ?></p>
		</div>

		<?php
		$index = 0;
		foreach ( $signature_products as $product_item ) :
			// Build args for the holo card template part.
			if ( $product_item instanceof WC_Product ) {
				$card_args = array(
					'product'    => $product_item,
					'collection' => 'signature',
					'index'      => $index,
				);
			} else {
				$card_args = array(
					'product'    => null,
					'title'      => $product_item['title'] ?? '',
					'price'      => $product_item['price'] ?? '',
					'badge_text' => $product_item['badge_text'] ?? '',
					'collection' => 'signature',
					'permalink'  => $product_item['permalink'] ?? '#',
					'sku'        => $product_item['sku'] ?? '',
					'index'      => $index,
				);
			}

			get_template_part( 'template-parts/product-card-holo', null, $card_args );
			$index++;
		endforeach;
		?>
	</div>
</section>

<!-- ════ Quality Promise ════════════════════════════════════════════════════ -->
<section class="sig-quality reveal">
	<h2 class="sig-quality__title"><?php echo esc_html__( 'Our Quality Promise', 'skyyrose-flagship' ); ?></h2>
	<p class="sig-quality__desc"><?php echo esc_html__( 'Every SIGNATURE piece is backed by our commitment to excellence. We stand behind every stitch, every seam, every detail.', 'skyyrose-flagship' ); ?></p>
	<div class="sig-quality__grid">
		<?php foreach ( $quality_items as $item ) : ?>
			<div class="sig-quality__item">
				<div class="sig-quality__icon"><?php echo wp_kses( $item['icon'], array( 'svg' => array( 'viewBox' => true, 'fill' => true, 'stroke' => true, 'class' => true, 'aria-hidden' => true, 'width' => true, 'height' => true, 'xmlns' => true ), 'path' => array( 'd' => true, 'fill' => true, 'stroke' => true, 'stroke-width' => true, 'stroke-linecap' => true, 'stroke-linejoin' => true ), 'circle' => array( 'cx' => true, 'cy' => true, 'r' => true, 'fill' => true ), 'line' => array( 'x1' => true, 'y1' => true, 'x2' => true, 'y2' => true, 'stroke' => true, 'stroke-width' => true ), 'polyline' => array( 'points' => true, 'fill' => true, 'stroke' => true, 'stroke-width' => true ), 'rect' => array( 'x' => true, 'y' => true, 'width' => true, 'height' => true, 'rx' => true, 'ry' => true, 'fill' => true, 'stroke' => true ) ) ); ?></div>
				<h3><?php echo esc_html( $item['title'] ); ?></h3>
				<p><?php echo esc_html( $item['desc'] ); ?></p>
			</div>
		<?php endforeach; ?>
	</div>
</section>

<!-- ════ CTA Banner ═════════════════════════════════════════════════════════ -->
<section class="sig-cta reveal">
	<h2 class="sig-cta__title"><?php echo esc_html__( 'Invest in Excellence', 'skyyrose-flagship' ); ?></h2>
	<p class="sig-cta__text"><?php echo esc_html__( 'Join the discerning few who understand that true luxury is an investment in craftsmanship, quality, and timeless style.', 'skyyrose-flagship' ); ?></p>
	<a href="<?php echo esc_url( function_exists( 'wc_get_cart_url' ) ? wc_get_cart_url() : '#' ); ?>" class="sig-cta__btn"><?php echo esc_html__( 'Shop Signature', 'skyyrose-flagship' ); ?></a>
</section>

<?php get_footer(); ?>
